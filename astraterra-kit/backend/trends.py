"""
Climate trends for a field: is it getting hotter, drier, frost-free longer?

For each yearly value (one number per year, 2005-2025) we run two standard tests:
  Mann-Kendall test: is there a real upward/downward trend, or just random ups and downs?
                     It compares every year with every later year and counts ups vs downs.
                     p-value < 0.05 -> "probably a real trend".
  Sen's slope:       HOW FAST it changes: the median of the slopes between all pairs of years.
                     Using the median means one extreme year (like 2012) cannot fake a trend.
Package: pymannkendall (original_test).

21 years is short for climate, so many results will honestly be "no clear trend".
"""

import pandas as pd
import pymannkendall as mk

SIGNIFICANT_P = 0.05


def yearly_table(daily, monthly):
    """One row per year with the values we test."""
    summer = monthly[monthly.index.get_level_values("month").isin([6, 7, 8])].groupby("year")
    season = monthly[monthly.index.get_level_values("month").isin([5, 6, 7, 8, 9])].groupby("year")
    july = monthly[monthly.index.get_level_values("month") == 7].groupby("year")

    table = pd.DataFrame({
        "summer_tmax_c": summer["tmax_c"].mean(),
        "summer_rain_mm": summer["rain_mm"].sum(),
        "annual_rain_mm": monthly.groupby("year")["rain_mm"].sum(),
        "summer_heat_days": summer["heat_days"].sum(),
        "summer_soil_moisture": summer["soil_moisture_root"].mean(),
        "season_gdd": season["gdd"].sum(),
        "july_water_balance_mm": july["rain_mm"].sum() - july["et0_mm"].sum(),
    })

    # Frost per year (frost = daily minimum at or below 0 C), split at July 1 like features.frost_dates
    frost = daily[daily["temp_min_c"] <= 0]
    doy, year = frost.index.day_of_year, frost.index.year
    last_spring = pd.Series(doy[doy < 182], index=year[doy < 182]).groupby(level=0).max()
    first_fall = pd.Series(doy[doy >= 182], index=year[doy >= 182]).groupby(level=0).min()
    if len(last_spring) and len(first_fall):
        table["last_spring_frost_doy"] = last_spring
        table["frost_free_days"] = first_fall - last_spring
    return table


# variable -> (unit per decade, how to say "it went up", how to say "it went down", label for "no trend")
DESCRIBE = {
    "summer_tmax_c": ("C/decade", "Summer highs are rising about {v} C per decade",
                      "Summer highs are falling about {v} C per decade", "summer highs"),
    "summer_rain_mm": ("mm/decade", "Summer rain is increasing about {v} mm per decade",
                       "Summer rain is decreasing about {v} mm per decade", "summer rain"),
    "annual_rain_mm": ("mm/decade", "Yearly rain is increasing about {v} mm per decade",
                       "Yearly rain is decreasing about {v} mm per decade", "yearly rain"),
    "summer_heat_days": ("days/decade", "Summer heat days (above 32 C) are increasing about {v} per decade",
                         "Summer heat days (above 32 C) are decreasing about {v} per decade", "summer heat days"),
    "summer_soil_moisture": ("fraction/decade", "Summer root-zone soil is getting wetter",
                             "Summer root-zone soil is getting drier", "summer soil moisture"),
    "season_gdd": ("C-days/decade", "Growing-season heat (GDD) is increasing about {v} C-days per decade",
                   "Growing-season heat (GDD) is decreasing about {v} C-days per decade", "growing-season heat"),
    "july_water_balance_mm": ("mm/decade", "July's rain minus water demand is improving about {v} mm per decade",
                              "July is getting drier: rain minus water demand falls about {v} mm per decade",
                              "July's water balance"),
    "last_spring_frost_doy": ("days/decade", "The last spring frost is coming about {v} days later per decade",
                              "The last spring frost is coming about {v} days earlier per decade", "the last spring frost date"),
    "frost_free_days": ("days/decade", "The frost-free season is lengthening about {v} days per decade",
                        "The frost-free season is shortening about {v} days per decade", "the frost-free season length"),
}


def climate_trends(daily, monthly):
    """List of trends in the contract format, significant ones first."""
    table = yearly_table(daily, monthly)
    first, last = int(table.index.min()), int(table.index.max())
    trends = []
    for variable, (unit, up, down, label) in DESCRIBE.items():
        if variable not in table:
            continue
        values = table[variable].dropna()
        if len(values) < 10:
            continue
        result = mk.original_test(values.to_numpy())
        per_decade = result.slope * 10                     # Sen's slope is per year -> per decade
        significant = result.p < SIGNIFICANT_P
        shown = round(abs(per_decade), 3 if variable == "summer_soil_moisture" else 1)
        if significant:
            sentence = (up if per_decade > 0 else down).format(v=shown) + f" ({first}-{last})."
        else:
            sentence = f"No clear trend in {label} over {first}-{last}; year-to-year variation is larger than any change."
        trends.append({
            "variable": variable,
            "change_per_decade": round(float(per_decade), 3),
            "unit": unit,
            "p_value": round(float(result.p), 3),
            "significant": bool(significant),
            "plain_language": sentence,
        })
    trends.sort(key=lambda t: (not t["significant"], t["p_value"]))
    return trends


if __name__ == "__main__":
    import sys
    from features import monthly_by_year
    from nasa_power import get_daily
    lat, lon = (float(sys.argv[1]), float(sys.argv[2])) if len(sys.argv) > 2 else (43.70767, -90.93877)
    daily = get_daily(lat, lon)
    for t in climate_trends(daily, monthly_by_year(daily)):
        flag = "SIGNIFICANT" if t["significant"] else "           "
        print(f"{flag} p={t['p_value']:<6} {t['change_per_decade']:>9} {t['unit']:<16} {t['plain_language']}")
