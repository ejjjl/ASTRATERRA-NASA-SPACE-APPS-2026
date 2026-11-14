import pandas as pd
import numpy as np
pd.set_option("display.width", 200)
from nasa_power import get_daily

"""
Each month:
  soil water = last month's soil water + rain − (ET₀ × Kc of the crop growing now)
  if soil water > what the soil can hold → the extra drains away (bucket overflows)
  if soil water < 50% of what the soil can hold → the crop is STRESSED that month

"""

HEAT_DAY_C = 32  #max temp anything above -> heat stress day
HEAVY_RAIN_MM = 25 #daily rain anything above -> heavy rain day

def add_et0(df):
    """Add daily ET0 (mm/day) using the Hargreaves formula (FAO-56, eq. 52)."""
    df = df.copy()
    temp_range = (df["temp_max_c"] - df["temp_min_c"]).clip(lower=0)
    df["et0_mm"] = (
        0.0023 * 0.408 * df["toa_solar_mj"]
        * (df["temp_mean_c"] + 17.8)
        * np.sqrt(temp_range)
    ).clip(lower=0)
    return df

def monthly_by_year(df):
    """Daily data, one row per (year,month)"""
    df = df.copy()
    df = add_et0(df)
    df["year"] = df.index.year
    df["month"] = df.index.month
    df["is_heat_day"] = df["temp_max_c"] > HEAT_DAY_C
    df["is_heavy_rain_day"] = df["rain_mm"] > HEAVY_RAIN_MM

    return df.groupby(["year", "month"]).agg(
        et0_mm=("et0_mm", "sum"),
        rain_mm=("rain_mm", "sum"),
        tmax_c=("temp_max_c", "mean"),
        tmin_c=("temp_min_c", "mean"),
        heat_days=("is_heat_day", "sum"),
        heavy_rain_days=("is_heavy_rain_day", "sum"),
        soil_moisture_root=("soil_moisture_root", "mean"),
    )

def monthly_normals(monthly):
    """One row per (year,month) 12 rows per year"""
    normals = monthly.groupby("month").mean()
    normals["water_balance_mm"] = normals["rain_mm"] - normals["et0_mm"]
    return normals.round(2)

if __name__ == "__main__":
    df = get_daily(42.03, -93.62)
    monthly = monthly_by_year(df)
    print(monthly_normals(monthly))
