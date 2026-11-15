import pandas as pd
import numpy as np
pd.set_option("display.width", 200)
from nasa_power import get_daily


HEAT_DAY_C = 32  #max temp anything above -> heat stress day
HEAVY_RAIN_MM = 25 #daily rain anything above -> heavy rain day

# Growing degree days (GDD): "heat units" a crop collects each day, which drive how fast it grows.
# Standard US corn method (86/50 F): cap Tmax at 30 C, floor Tmin at 10 C, base 10 C.
GDD_BASE_C = 10
GDD_CAP_C = 30


def add_gdd(df):
    """Add daily growing degree days."""
    df = df.copy()
    tmax = df["temp_max_c"].clip(lower=GDD_BASE_C, upper=GDD_CAP_C)
    tmin = df["temp_min_c"].clip(lower=GDD_BASE_C, upper=GDD_CAP_C)
    df["gdd"] = (tmax + tmin) / 2 - GDD_BASE_C
    return df

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
    df = add_gdd(df)
    df["year"] = df.index.year
    df["month"] = df.index.month
    df["is_heat_day"] = df["temp_max_c"] > HEAT_DAY_C
    df["is_heavy_rain_day"] = df["rain_mm"] > HEAVY_RAIN_MM

    return df.groupby(["year", "month"]).agg(
        solar_mj = ("solar_mj", "mean"),
        et0_mm=("et0_mm", "sum"),
        rain_mm=("rain_mm", "sum"),
        tmax_c=("temp_max_c", "mean"),
        tmin_c=("temp_min_c", "mean"),
        heat_days=("is_heat_day", "sum"),
        heavy_rain_days=("is_heavy_rain_day", "sum"),
        soil_moisture_root=("soil_moisture_root", "mean"),
        gdd=("gdd", "sum"),
    )

def monthly_normals(monthly):
    """One row per (year,month) 12 rows per year"""
    normals = monthly.groupby("month").mean()
    normals["water_balance_mm"] = normals["rain_mm"] - normals["et0_mm"]
    return normals.round(2)
FROST_C = 0          # min temp at or below this = frost
MID_YEAR_DOY = 182   # July 1: splits spring frosts from fall frosts


def frost_dates(df):
    """Typical last spring frost and first fall frost, as day of year (median over all years)."""
    df = df.copy()
    df["year"] = df.index.year
    df["doy"] = df.index.day_of_year

    frosts = df[df["temp_min_c"] <= FROST_C]                             # keep only the frost days

    spring = frosts[frosts["doy"] < MID_YEAR_DOY]
    fall = frosts[frosts["doy"] >= MID_YEAR_DOY]

    last_spring = spring.groupby("year")["doy"].max()  # per year: the LATEST spring frost
    first_fall = fall.groupby("year")["doy"].min()     # per year: the EARLIEST fall frost

    # Some places never freeze (tropics). Then there is no frost date: return None.
    spring_doy = int(last_spring.median()) if not last_spring.empty else None
    fall_doy = int(first_fall.median()) if not first_fall.empty else None
    # No spring frost -> season starts Jan 1; no fall frost -> it runs to Dec 31.
    frost_free = (fall_doy or 366) - (spring_doy or 1)
    return {
        "last_spring_median_doy": spring_doy,
        "first_fall_median_doy": fall_doy,
        "frost_free_days": frost_free,
    }


if __name__ == "__main__":
    df = get_daily(42.03, -93.62)
    monthly = monthly_by_year(df)
    print(monthly_normals(monthly))
    print(frost_dates(df))
