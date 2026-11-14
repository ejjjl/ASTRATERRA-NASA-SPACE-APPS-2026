from crops import year_kc

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

