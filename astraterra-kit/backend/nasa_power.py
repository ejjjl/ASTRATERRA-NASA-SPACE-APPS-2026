"""
Fetch daily NASA POWER data for one point, with a cache on disk.

NASA POWER docs: https://power.larc.nasa.gov/docs/services/api/temporal/daily/

Usage:
    from nasa_power import get_daily
    df = get_daily(42.03, -93.62)      # pandas DataFrame, one row per day
"""

import json
from pathlib import Path

import pandas as pd
import requests

# The NASA POWER endpoint for daily data at a single point.
POWER_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"

# Which variables we ask for. Names are NASA POWER's own codes.
PARAMETERS = {
    "T2M": "temp_mean_c",            # air temperature at 2 m, daily mean (°C)
    "T2M_MAX": "temp_max_c",         # daily max (°C)
    "T2M_MIN": "temp_min_c",         # daily min (°C)
    "PRECTOTCORR": "rain_mm",        # rainfall, bias-corrected (mm/day)
    "GWETROOT": "soil_moisture_root",  # root-zone soil wetness, 0-1 (MERRA-2 model)
    "GWETTOP": "soil_moisture_top",    # topsoil wetness, 0-1 (MERRA-2 model)
    "ALLSKY_SFC_SW_DWN": "solar_mj",   # sunlight reaching the ground (MJ/m²/day)
    "TOA_SW_DWN": "toa_solar_mj",      # sunlight at top of atmosphere (needed for Hargreaves ET0)
    "RH2M": "humidity_pct",          # relative humidity at 2 m (%)
}

START_YEAR = 2005
END_YEAR = 2025

# Cache folder: astraterra-kit/data/cache/ (see AGENTS.md)
CACHE_DIR = Path(__file__).resolve().parent.parent / "data" / "cache"


def _cache_path(lat: float, lon: float) -> Path:
    # Round to 2 decimals (~1 km). NASA POWER's grid is ~50 km, so nearby
    # points give the same data anyway and can share one cache file.
    return CACHE_DIR / f"power_{lat:.2f}_{lon:.2f}_{START_YEAR}_{END_YEAR}.json"


def _download(lat: float, lon: float) -> dict:
    """Call the NASA POWER API and return the raw JSON."""
    params = {
        "parameters": ",".join(PARAMETERS),
        "community": "AG",           # agriculture community -> units suited to farming
        "latitude": lat,
        "longitude": lon,
        "start": f"{START_YEAR}0101",
        "end": f"{END_YEAR}1231",
        "format": "JSON",
    }
    response = requests.get(POWER_URL, params=params, timeout=120)
    response.raise_for_status()      # crash with a clear error if NASA returns an error
    return response.json()


def get_raw(lat: float, lon: float) -> dict:
    """Return raw NASA POWER JSON, from the cache if we already downloaded it."""
    path = _cache_path(lat, lon)
    if path.exists():
        return json.loads(path.read_text())

    data = _download(lat, lon)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data))
    return data


def get_daily(lat: float, lon: float) -> pd.DataFrame:
    """
    Return a DataFrame with one row per day and readable column names.

    The raw JSON looks like:
        {"properties": {"parameter": {"T2M": {"20050101": -5.2, ...}, ...}}}
    i.e. one dictionary per variable, keyed by date. pandas turns that
    straight into a table: variables become columns, dates become rows.
    """
    raw = get_raw(lat, lon)
    df = pd.DataFrame(raw["properties"]["parameter"])

    df = df.rename(columns=PARAMETERS)
    df.index = pd.to_datetime(df.index, format="%Y%m%d")
    df.index.name = "date"

    # NASA POWER uses -999 for "no data". Turn it into a real missing value (NaN)
    # so averages ignore it instead of being dragged down by -999.
    df = df.replace(-999, float("nan"))
    return df


if __name__ == "__main__":
    # Quick test: run `py nasa_power.py` from the backend folder.
    df = get_daily(42.03, -93.62)   # Iowa demo farm
    print(df.head())
    print(f"\n{len(df)} days, {df.index.min().date()} to {df.index.max().date()}")
    print("\nMissing values per column:")
    print(df.isna().sum())
