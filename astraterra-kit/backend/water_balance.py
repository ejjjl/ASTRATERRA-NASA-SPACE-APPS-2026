from crops import year_kc
from crops import MAIN_CROP_KC

STRESS_LINE = 0.5   # FAO-56: crop is stressed below 50% of available soil water


def simulate_year(months, kc, capacity_mm, water_mm):
    """
    Run the bucket for one year.
      months:      12 rows of monthly data for one year (needs rain_mm, et0_mm)
      kc:          12 Kc values (Jan..Dec)
      capacity_mm: how much water the soil can hold for the roots
      water_mm:    water in the bucket at the start of the year
    Returns (water left at the end of the year, list of 12 monthly results)
    """
    threshold = capacity_mm * STRESS_LINE
    results = []

    for i in range(12):
        rain = months["rain_mm"].iloc[i]
        et0 = months["et0_mm"].iloc[i]

        water_mm = water_mm + rain                 # 1. rain fills the bucket
        demand = et0 * kc[i]                       # 2. what the crop wants to drink

        # 3 + 4. how much it actually gets
        if water_mm >= threshold:
            actual = demand                            # above the line: no stress
        else:
            actual = demand * (water_mm / threshold)   # below: gets less, the emptier the less

        actual = min(actual, water_mm)                 # can't drink more than is in the bucket

        water_mm = water_mm - actual                # 5a. take out what was drunk
        water_mm = min(water_mm, capacity_mm)      # 5b. overflow drains away
        water_mm = max(water_mm, 0)                # can't go below empty

        stress_pct = ((demand - actual) / demand) * 100 if demand > 0 else 0                      # share of demand NOT met, 0 to 100
        results.append({"month": i + 1, "demand_mm": demand, "actual_mm": actual, "stress_pct": stress_pct})

    return water_mm, results

OK_BELOW = 15      # season stress below 15%  -> "ok"
FAIL_FROM = 35     # season stress 35% or more -> "fail" (in between = "stress")


def simulate_rotation(monthly, sequence, capacity_mm):
    """
    Run a rotation through every past year, carrying soil water from year to year.
      monthly:  output of features.monthly_by_year (one row per year+month)
      sequence: one dict per rotation year, e.g.
                [{"main_crop": "corn", "cover_crop": "cereal_rye"},
                 {"main_crop": "soybean", "cover_crop": None}]
    Returns the replay: one dict per year.
    """
    years = sorted(monthly.index.get_level_values("year").unique())
    water_mm = capacity_mm          # assume the soil starts full
    replay = []

    for n, year in enumerate(years):
        step = sequence[n% len(sequence)]            # which rotation year is this? (corn, soybean, corn, ...)
        kc, bare_months = year_kc(step["main_crop"], step["cover_crop"])

        water_mm, results = simulate_year(monthly.loc[year], kc, capacity_mm, water_mm)

        # Season stress: only count months when the MAIN crop is growing
        growing = [r for r in results if MAIN_CROP_KC[step["main_crop"]][r["month"] - 1] > 0]
        demand = sum(r["demand_mm"] for r in growing)
        actual = sum(r["actual_mm"] for r in growing)
        stress_pct = round(100 * (demand - actual) / demand) if demand > 0 else 0

        if stress_pct < OK_BELOW:
            outcome = "ok"
        elif stress_pct < FAIL_FROM:
            outcome = "stress"
        else:
            outcome = "fail"

        replay.append({
            "year": int(year),
            "crop": step["main_crop"],
            "outcome": outcome,
            "water_stress_pct": stress_pct,
        })

    return replay
if __name__ == "__main__":
    from nasa_power import get_daily
    from features import monthly_by_year

    monthly = monthly_by_year(get_daily(42.03, -93.62))
    corn_soy = [{"main_crop": "corn", "cover_crop": None},
                {"main_crop": "soybean", "cover_crop": None}]
    for r in simulate_rotation(monthly, corn_soy, 170):
        print(r)