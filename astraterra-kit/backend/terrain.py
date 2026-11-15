"""
Risk map for a field from NASA SRTM elevation (30 m), via the free OpenTopoData API.

1. get_elevation_grid(): a 9 x 9 grid of points ~100 m apart around the field (81 points = 1 API call).
2. slope_pct():          how steep each cell is. Steep + bare soil + heavy rain = erosion.
3. frost_pockets():      cells lower than their surroundings. Cold air is heavy and flows
                         downhill on still nights, so low spots freeze first.
4. risk_zones():         GeoJSON squares for the map (contract: kind, level, slope_pct).

OpenTopoData: https://www.opentopodata.org  (max 100 points per call, 1 call per second)
SRTM: NASA Shuttle Radar Topography Mission, https://www.earthdata.nasa.gov/data/instruments/srtm
"""

import json
import math
from pathlib import Path

import numpy as np
import requests

TOPO_URL = "https://api.opentopodata.org/v1/srtm30m"
CACHE_DIR = Path(__file__).resolve().parent.parent / "data" / "cache"

GRID_N = 9            # 9 x 9 cells, the field is in the centre cell
CELL_M = 100          # each cell ~100 m wide

# SRTM heights are only accurate to ~2 m, so tiny bumps are noise: we smooth first
# and only flag clear features.
# Erosion levels by slope (USDA soil survey classes): 0-5% nearly level to gentle,
# 5-9% moderately sloping, 9%+ strongly sloping.
EROSION_MEDIUM_PCT = 5
EROSION_HIGH_PCT = 9

# Frost pocket: at least this many metres below the average of the area around it (~250 m)
POCKET_MEDIUM_M = 2.0
POCKET_HIGH_M = 4.0
POCKET_MAX_SLOPE_PCT = 5   # cold air collects in flat-ish low spots, not on slopes


def _cell_size_deg(lat):
    """~100 m in degrees. A degree of longitude gets shorter away from the equator."""
    dlat = CELL_M / 111_320
    dlon = CELL_M / (111_320 * math.cos(math.radians(lat)))
    return dlat, dlon


def _grid_points(lat, lon):
    """Centres of the 9 x 9 cells, row 0 = north. Returns a list of rows of (lat, lon)."""
    dlat, dlon = _cell_size_deg(lat)
    half = GRID_N // 2
    return [[(lat + (half - r) * dlat, lon + (c - half) * dlon) for c in range(GRID_N)] for r in range(GRID_N)]


def get_elevation_grid(lat, lon):
    """9 x 9 numpy array of elevations (m), cached. None if the API is down."""
    cache = CACHE_DIR / f"terrain_{lat:.4f}_{lon:.4f}.json"
    if cache.exists():
        return np.array(json.loads(cache.read_text()))

    points = [p for row in _grid_points(lat, lon) for p in row]
    locations = "|".join(f"{p_lat:.6f},{p_lon:.6f}" for p_lat, p_lon in points)
    try:
        resp = requests.post(TOPO_URL, data={"locations": locations}, timeout=20)
        resp.raise_for_status()
        elevations = [r["elevation"] for r in resp.json()["results"]]
    except (requests.RequestException, KeyError, ValueError):
        return None
    if any(e is None for e in elevations):      # e.g. over the sea
        return None

    grid = np.array(elevations, dtype=float).reshape(GRID_N, GRID_N)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(grid.tolist()))
    return grid


def _local_mean(grid, radius, skip_centre=False):
    """Average of the (2*radius+1) x (2*radius+1) window around each cell."""
    padded = np.pad(grid, radius, mode="edge")   # repeat the border so edge cells have neighbours
    size = 2 * radius + 1
    out = np.zeros_like(grid)
    for r in range(GRID_N):
        for c in range(GRID_N):
            window = padded[r:r + size, c:c + size]
            if skip_centre:
                out[r, c] = (window.sum() - grid[r, c]) / (size * size - 1)
            else:
                out[r, c] = window.mean()
    return out


def smooth(grid):
    """Average each cell with its 8 neighbours: removes the ~2 m SRTM noise."""
    return _local_mean(grid, 1)


def slope_pct(grid):
    """
    Slope of each cell in %: metres of drop per 100 m of distance.
    np.gradient gives the change in height per cell going north-south and east-west;
    the steepest direction combines both (Pythagoras).
    """
    d_ns, d_ew = np.gradient(grid, CELL_M)      # metres of height per metre of distance
    return np.sqrt(d_ns**2 + d_ew**2) * 100


def frost_pockets(grid):
    """How many metres each cell sits below the area around it (5 x 5 cells, ~250 m each way).
    Positive = low spot."""
    return _local_mean(grid, 2, skip_centre=True) - grid


def _square(cell_lat, cell_lon, dlat, dlon):
    """GeoJSON polygon for one cell. GeoJSON order is [lon, lat] and the ring must close."""
    s, n = cell_lat - dlat / 2, cell_lat + dlat / 2
    w, e = cell_lon - dlon / 2, cell_lon + dlon / 2
    return {"type": "Polygon", "coordinates": [[[w, n], [e, n], [e, s], [w, s], [w, n]]]}


def risk_zones(lat, lon):
    """
    Returns (GeoJSON FeatureCollection, field elevation in m or None, summary dict).
    Only medium/high cells are drawn, so the map shows the problem spots, not 81 green squares.
    """
    empty = {"type": "FeatureCollection", "features": []}
    grid = get_elevation_grid(lat, lon)
    if grid is None:
        return empty, None, {"source": "unavailable"}

    smoothed = smooth(grid)
    slopes = slope_pct(smoothed)
    pockets = frost_pockets(smoothed)
    dlat, dlon = _cell_size_deg(lat)
    points = _grid_points(lat, lon)

    features = []
    for r in range(GRID_N):
        for c in range(GRID_N):
            s, depth = float(slopes[r, c]), float(pockets[r, c])
            p_lat, p_lon = points[r][c]

            if s >= EROSION_MEDIUM_PCT:
                level = "high" if s >= EROSION_HIGH_PCT else "medium"
                features.append({"type": "Feature",
                                 "properties": {"kind": "erosion", "level": level, "slope_pct": round(s, 1)},
                                 "geometry": _square(p_lat, p_lon, dlat, dlon)})

            if depth >= POCKET_MEDIUM_M and s < POCKET_MAX_SLOPE_PCT:
                level = "high" if depth >= POCKET_HIGH_M else "medium"
                features.append({"type": "Feature",
                                 "properties": {"kind": "frost_pocket", "level": level, "slope_pct": round(s, 1),
                                                "below_surroundings_m": round(depth, 1)},
                                 "geometry": _square(p_lat, p_lon, dlat, dlon)})

    half = GRID_N // 2
    summary = {
        "source": "NASA SRTM 30 m via OpenTopoData",
        "field_slope_pct": round(float(slopes[half, half]), 1),
        "max_slope_pct": round(float(slopes.max()), 1),
        "relief_m": round(float(grid.max() - grid.min()), 1),
    }
    return {"type": "FeatureCollection", "features": features}, round(float(grid[half, half])), summary


if __name__ == "__main__":
    import sys
    lat, lon = (float(sys.argv[1]), float(sys.argv[2])) if len(sys.argv) > 2 else (42.03, -93.62)
    zones, elevation, summary = risk_zones(lat, lon)
    print("Field elevation:", elevation, "m")
    print("Summary:", summary)
    for f in zones["features"]:
        print(" ", f["properties"])
