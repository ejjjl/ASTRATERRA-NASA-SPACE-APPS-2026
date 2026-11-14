import pandas as pd
from nasa_power import get_daily

HEAT_DAY_C = 32  #max temp anything above -> heat stress day
HEAVY_RAIN_MM = 25 #daily rain anything above -> heavy rain day

def monthly_by_year(df):
    """Daily data, one row per (year,month)"""
    df = df.copy()
    df["year"] = df.index.year
    df["month"] = df.index.month
    df["is_heat_day"] = df["temp_max_c"] > HEAT_DAY_C
    df["is_heavy_rain_day"] = df["rain_mm"] > HEAVY_RAIN_MM

    return df.groupby(["year", "month"]).agg(
        rain_mm=("rain_mm", "sum"),
        tmax_c=("temp_max_c", "mean"),
        tmin_c=("temp_min_c", "mean"),
        heat_days=("is_heat_day", "sum"),
        heavy_rain_days=("is_heavy_rain_day", "sum"),
        soil_moisture_root=("soil_moisture_root", "mean"),
    )

def monthly_normals(monthly):
    """One row per (year,month) 12 rows per year"""
    return monthly.groupby("month").mean().round(2)

if __name__ == "__main__":
    df = get_daily(42.03, -93.62)
    monthly = monthly_by_year(df)
    print(monthly_normals(monthly))
