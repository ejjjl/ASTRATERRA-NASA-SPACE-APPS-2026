"""
What has this field really grown? USDA Cropland Data Layer (CDL) via CropScape.

CDL is a 30 m map of the US: every pixel gets a crop type every year (from Landsat/Sentinel
satellite images + farmer surveys). We read the pixel under the pin for each year, then
look for the repeating pattern (corn, soy, corn, soy... = a 2-year rotation).

CropScape API: https://nassgeodata.gmu.edu/CropScape/  (free, no key, US only)
"""

import json
import math
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

CDL_URL = "https://nassgeodata.gmu.edu/axis2/services/CDLService/GetCDLValue"
CACHE_DIR = Path(__file__).resolve().parent.parent / "data" / "cache"
FIRST_YEAR, LAST_YEAR = 2008, 2025      # CDL covers the whole US from 2008

# CDL code -> our crop id (only crops our water model knows)
CDL_TO_CROP = {1: "corn", 4: "sorghum", 5: "soybean", 24: "wheat_winter", 26: "wheat_winter", 36: "alfalfa"}
# Codes that mean "this is not a farm field"
NOT_CROPLAND = {111, 112, 121, 122, 123, 124, 131, 141, 142, 143, 190, 195}  # water, towns, forest, wetland


def to_albers(lat, lon):
    """
    lat/lon -> US Albers Equal Area (EPSG:5070), the flat map CDL is stored in (metres).
    Formulas from Snyder (1987) "Map Projections: A Working Manual", USGS, p. 101-102.
    Map settings: standard parallels 29.5 and 45.5 N, origin 23 N 96 W, GRS80 ellipsoid.
    """
    a, e2 = 6378137.0, 0.00669438002290       # Earth radius (m) and flattening (squared eccentricity)
    e = math.sqrt(e2)

    def q(phi):
        s = math.sin(phi)
        return (1 - e2) * (s / (1 - e2 * s * s) - (1 / (2 * e)) * math.log((1 - e * s) / (1 + e * s)))

    def m(phi):
        s = math.sin(phi)
        return math.cos(phi) / math.sqrt(1 - e2 * s * s)

    phi1, phi2, phi0, lon0 = map(math.radians, (29.5, 45.5, 23.0, -96.0))
    n = (m(phi1) ** 2 - m(phi2) ** 2) / (q(phi2) - q(phi1))
    C = m(phi1) ** 2 + n * q(phi1)
    rho = a * math.sqrt(C - n * q(math.radians(lat))) / n
    rho0 = a * math.sqrt(C - n * q(phi0)) / n
    theta = n * (math.radians(lon) - lon0)
    return rho * math.sin(theta), rho0 - rho * math.cos(theta)


def _one_year(year, x, y):
    """Ask CropScape for one year. Returns {"year", "code", "name"} or None."""
    try:
        resp = requests.get(CDL_URL, params={"year": year, "x": x, "y": y}, timeout=15)
        resp.raise_for_status()
        text = resp.text                       # looks like: {x: ..., value: 5, category: "Soybeans", ...}
        code = int(text.split("value:")[1].split(",")[0])
        name = text.split('category: "')[1].split('"')[0]
        return {"year": year, "code": code, "name": name}
    except (requests.RequestException, IndexError, ValueError):
        return None


def crop_history(lat, lon):
    """One entry per year 2008-2025 (cached). Empty list outside the US or if the server is down."""
    cache = CACHE_DIR / f"cdl_{lat:.4f}_{lon:.4f}.json"
    if cache.exists():
        history = json.loads(cache.read_text())
        for r in history:                        # re-map, so crops added later (e.g. sorghum) apply to old caches
            r["crop"] = CDL_TO_CROP.get(r["code"])
        return history

    x, y = to_albers(lat, lon)
    years = range(FIRST_YEAR, LAST_YEAR + 1)
    # 18 small requests: send them at the same time instead of one after another
    with ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(lambda yr: _one_year(yr, x, y), years))

    history = [r for r in results if r is not None]
    for r in history:
        r["crop"] = CDL_TO_CROP.get(r["code"])   # None = a crop/land type our model doesn't have
    if len(history) >= len(years) - 2:           # only cache a (nearly) complete answer
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(history))
    return history


def detect_rotation(history, start_year, recent=8):
    """
    Find the shortest repeating crop pattern in the last `recent` years.
    Returns (rotation list or None, how well it matches 0-1).
    The list is lined up with start_year (the first replay year), so the replay puts
    corn in the same years the farmer really grew corn.
    """
    recent_years = [h for h in history if h["crop"]][-recent:]
    if len(recent_years) < 4:
        return None, 0.0

    for period in (1, 2, 3, 4):
        # For each position in the cycle, the crop seen most often there
        pattern = {}
        for pos in range(period):
            crops = [h["crop"] for h in recent_years if (h["year"] - start_year) % period == pos]
            if crops:
                pattern[pos] = max(set(crops), key=crops.count)
        if len(pattern) < period:
            continue
        if period > 1 and len(set(pattern.values())) == 1:
            continue                             # ["corn", "corn"] is not a 2-year rotation
        matches = sum(1 for h in recent_years if pattern[(h["year"] - start_year) % period] == h["crop"])
        fit = matches / len(recent_years)
        if fit >= 0.75 and (period > 1 or fit == 1):   # one crop every year must be exact
            return [pattern[pos] for pos in range(period)], round(fit, 2)
    return None, 0.0


def is_cropland(history):
    """False if the pin is on a town, lake or forest in most recent years."""
    recent = history[-5:]
    if not recent:
        return None                              # unknown (outside US / no data)
    return sum(1 for h in recent if h["code"] in NOT_CROPLAND) < len(recent) / 2


if __name__ == "__main__":
    import sys
    lat, lon = (float(sys.argv[1]), float(sys.argv[2])) if len(sys.argv) > 2 else (42.03, -93.62)
    print("Albers:", [round(v) for v in to_albers(lat, lon)])
    hist = crop_history(lat, lon)
    print(" ".join(f"{h['year']}:{h['crop'] or h['name']}" for h in hist))
    print("Cropland:", is_cropland(hist), "| Rotation:", detect_rotation(hist, 2005))
