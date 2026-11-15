"""
Validation: does our water model agree with what farmers really harvested?

Real data:  USDA NASS county yields (bushels/acre), Vernon County WI, 2005-2025
            downloaded from https://quickstats.nass.usda.gov -> data/validation/nass_vernon_wi_yields.csv
Model:      water stress % per year from our bucket replay (NASA POWER weather)

Method:
  1. Yields rise every year (better seeds, better farming), so a raw comparison would
     mostly show that trend. We fit a straight trend line and look at each year's
     difference from it: "2023 corn was 19% below the expected yield".
  2. We simulate corn every year and soybean every year (so every year has a value
     for each crop) and compare stress % with the yield difference.
  3. Spearman rank correlation: do high-stress years rank as low-yield years?
     -1 = perfect "more stress, less yield", 0 = no relation.

Run (from backend/):  python validate.py   -> prints results, writes data/validation/validation_vernon_wi.json
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd

from features import monthly_by_year
from nasa_power import get_daily
from soil import apply_overrides, get_soil, water_per_metre
from water_balance import simulate_rotation

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "validation"
NASS_CSV = DATA_DIR / "nass_vernon_wi_yields.csv"
OUT_JSON = DATA_DIR / "validation_vernon_wi.json"
LAT, LON = 43.70767, -90.93877          # demo farm, Vernon County WI
CROPS = {"CORN": "corn", "SOYBEANS": "soybean"}


def load_yields():
    """{crop_id: Series(year -> yield)}. Values like '(D)' (withheld by USDA) become missing."""
    df = pd.read_csv(NASS_CSV)
    df["yield"] = pd.to_numeric(df["Value"].astype(str).str.replace(",", ""), errors="coerce")
    return {crop_id: df[df["Commodity"] == nass].set_index("Year")["yield"].dropna().sort_index()
            for nass, crop_id in CROPS.items()}


def yield_anomaly_pct(yields):
    """% difference from a straight trend line (np.polyfit degree 1 = best straight line)."""
    years = yields.index.to_numpy(dtype=float)
    slope, intercept = np.polyfit(years, yields.to_numpy(), 1)
    expected = slope * years + intercept
    return pd.Series(100 * (yields.to_numpy() - expected) / expected, index=yields.index).round(1)


def model_stress(monthly, per_metre, crop):
    """Stress % for every year if this crop were grown every year."""
    replay = simulate_rotation(monthly, [{"main_crop": crop, "cover_crop": None}], per_metre)
    return pd.Series({r["year"]: r["water_stress_pct"] for r in replay})


def spearman(a, b):
    """Rank correlation without extra packages: rank both, then normal correlation."""
    return round(float(a.rank().corr(b.rank())), 2)


def run():
    monthly = monthly_by_year(get_daily(LAT, LON))
    soil, _ = apply_overrides(get_soil(LAT, LON), {})
    per_metre = water_per_metre(soil["clay_pct"], soil["sand_pct"], soil["organic_carbon_pct"])

    result = {"county": "Vernon County, WI", "source": "USDA NASS Quick Stats, county yields (bu/acre)", "crops": {}}
    for crop_id, yields in load_yields().items():
        anomaly = yield_anomaly_pct(yields)
        stress = model_stress(monthly, per_metre, crop_id)
        both = pd.DataFrame({"yield": yields, "yield_vs_trend_pct": anomaly, "model_stress_pct": stress}).dropna()

        worst_model = both["model_stress_pct"].nlargest(3).index.tolist()
        worst_real = both["yield_vs_trend_pct"].nsmallest(3).index.tolist()
        result["crops"][crop_id] = {
            "years_compared": len(both),
            "spearman_stress_vs_yield": spearman(both["model_stress_pct"], both["yield_vs_trend_pct"]),
            "model_worst_years": worst_model,
            "real_worst_years": worst_real,
            "worst_years_matching": sorted(set(worst_model) & set(worst_real)),
            "years": [{"year": int(y), "yield": float(r["yield"]), "yield_vs_trend_pct": float(r["yield_vs_trend_pct"]),
                       "model_stress_pct": int(r["model_stress_pct"])} for y, r in both.iterrows()],
        }
    return result


if __name__ == "__main__":
    res = run()
    for crop, r in res["crops"].items():
        print(f"\n== {crop.upper()}  ({r['years_compared']} years)  Spearman stress vs yield: {r['spearman_stress_vs_yield']}")
        print(f"   model worst years: {r['model_worst_years']}   real worst years: {r['real_worst_years']}   match: {r['worst_years_matching']}")
        for y in r["years"]:
            bar = "#" * (y["model_stress_pct"] // 3)
            print(f"   {y['year']}  yield {y['yield']:6}  vs trend {y['yield_vs_trend_pct']:+6.1f}%   model stress {y['model_stress_pct']:3}%  {bar}")
    OUT_JSON.write_text(json.dumps(res, indent=2))
    print("\nwritten", OUT_JSON.name)
