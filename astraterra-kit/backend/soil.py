"""
Soil for a field: what it is made of, and how much water it can hold for roots.

1. get_soil(lat, lon)  -> clay %, sand %, organic carbon %, pH from SoilGrids (ISRIC, 250 m maps),
                          averaged over the top 1 m (where the roots are).
2. apply_overrides()   -> the farmer's own numbers (lab test) replace SoilGrids values.
3. water_per_metre()   -> plant-available water (mm per metre of soil), from texture
                          (Saxton & Rawls 2006 equations).
4. bucket_mm()         -> bucket size for one crop = water per metre x crop root depth.

SoilGrids: https://www.isric.org/explore/soilgrids  (REST API, no key needed)
"""

import json
from pathlib import Path

import requests

from crops import ROOT_DEPTH_M

SOILGRIDS_URL = "https://rest.isric.org/soilgrids/v2.0/properties/query"
CACHE_DIR = Path(__file__).resolve().parent.parent / "data" / "cache"

# Depth layers down to 1 m, and how thick each one is (cm), for a weighted average.
DEPTHS = {"0-5cm": 5, "5-15cm": 10, "15-30cm": 15, "30-60cm": 30, "60-100cm": 40}

# SoilGrids name -> (our name, divide by this to get our unit)
#   clay/sand come in g/kg (/10 -> %), soc in dg/kg (/100 -> %), pH as pH*10 (/10)
PROPERTIES = {
    "clay": ("clay_pct", 10),
    "sand": ("sand_pct", 10),
    "soc": ("organic_carbon_pct", 100),
    "phh2o": ("ph", 10),
}

# Used when SoilGrids has no data (towns, water, server down): a typical loam.
DEFAULT_SOIL = {"clay_pct": 20.0, "sand_pct": 40.0, "organic_carbon_pct": 1.5, "ph": 6.5}

# SoilGrids masks out towns and water. If the exact point is empty, look ~3 km around it.
NEARBY_STEPS = [(0, 0), (0.03, 0), (-0.03, 0), (0, 0.03), (0, -0.03)]


def _query(lat, lon):
    """One SoilGrids call. Returns {our_name: value over the top 1 m} or None if no data."""
    params = {
        "lat": lat, "lon": lon, "value": "mean",
        "property": list(PROPERTIES), "depth": list(DEPTHS),
    }
    resp = requests.get(SOILGRIDS_URL, params=params, timeout=60)
    resp.raise_for_status()

    soil = {}
    for layer in resp.json()["properties"]["layers"]:
        our_name, divide_by = PROPERTIES[layer["name"]]
        total, thickness = 0.0, 0
        for d in layer["depths"]:
            value = d["values"]["mean"]
            if value is not None:
                total += value * DEPTHS[d["label"]]
                thickness += DEPTHS[d["label"]]
        if thickness == 0:
            return None                      # empty point (town, lake...)
        soil[our_name] = round(total / thickness / divide_by, 2)
    return soil


def get_soil(lat, lon):
    """Soil for a point (cached). Always returns a dict with a 'found_at' note."""
    cache = CACHE_DIR / f"soil_{lat:.2f}_{lon:.2f}.json"
    if cache.exists():
        return json.loads(cache.read_text())

    for dlat, dlon in NEARBY_STEPS:
        try:
            soil = _query(lat + dlat, lon + dlon)
        except requests.RequestException:
            break                            # server down: use the default, don't cache
        if soil:
            soil["found_at"] = "exact point" if (dlat, dlon) == (0, 0) else "nearest farmland (~3 km)"
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            cache.write_text(json.dumps(soil))
            return soil

    return {**DEFAULT_SOIL, "found_at": "default (no SoilGrids data)"}


def apply_overrides(soil, overrides):
    """Farmer's numbers win. Returns (soil values, source of each value)."""
    found_default = soil.get("found_at", "").startswith("default")
    values, source = {}, {}
    for key in DEFAULT_SOIL:
        if overrides.get(key) is not None:
            values[key], source[key] = float(overrides[key]), "farmer_override"
        else:
            values[key], source[key] = soil[key], ("default" if found_default else "SoilGrids")
    return values, source


def water_per_metre(clay_pct, sand_pct, organic_carbon_pct):
    """
    Plant-available water (mm per metre of soil) = field capacity - wilting point.
    Saxton & Rawls (2006), Soil Sci. Soc. Am. J. 70:1569, equations 1 and 2.
      field capacity = water left after the soil drains (held at 33 kPa)
      wilting point  = water held so tightly roots can't get it (1500 kPa)
    Clay holds lots of water but grips it tightly; sand holds little. Loams are best.
    """
    S, C = sand_pct / 100, clay_pct / 100          # fractions 0-1
    OM = min(organic_carbon_pct * 1.724, 8)        # organic matter % (carbon x 1.724), valid up to 8%

    wp_t = -0.024*S + 0.487*C + 0.006*OM + 0.005*S*OM - 0.013*C*OM + 0.068*S*C + 0.031
    wilting = wp_t + (0.14 * wp_t - 0.02)

    fc_t = -0.251*S + 0.195*C + 0.011*OM + 0.006*S*OM - 0.027*C*OM + 0.452*S*C + 0.299
    field_cap = fc_t + (1.283 * fc_t**2 - 0.374 * fc_t - 0.015)

    return round(max(field_cap - wilting, 0.03) * 1000)   # m3/m3 -> mm per metre


def bucket_mm(per_metre_mm, crop):
    """Bucket size for one crop: deeper roots reach more water."""
    return per_metre_mm * ROOT_DEPTH_M[crop]


if __name__ == "__main__":
    soil = get_soil(42.03, -93.62)
    print("SoilGrids:", soil)
    values, source = apply_overrides(soil, {"ph": 6.2})
    print("With farmer pH:", values, source)
    per_m = water_per_metre(values["clay_pct"], values["sand_pct"], values["organic_carbon_pct"])
    print("Water per metre:", per_m, "mm")
    for crop in ROOT_DEPTH_M:
        print(f"  {crop:13} bucket = {bucket_mm(per_m, crop):.0f} mm")
    print("Sandy soil check:", water_per_metre(5, 85, 0.5), "mm/m  (should be much lower)")
