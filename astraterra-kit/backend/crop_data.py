"""

The CSV describes each crop the FAO-56 way:
    planting window (MM-DD), Kc_ini / Kc_mid / Kc_end, and 4 stage lengths in days
    (initial, development, mid-season, late season).

Our bucket model works per CALENDAR MONTH, so we:
    1. pick a planting day (middle of the planting window),
    2. draw the daily Kc curve (FAO-56 Fig. 25: flat, rising, flat, falling),
    3. average it per month: 12 monthly Kc values (0 = crop not in the field).

Blank cells (cereal rye, oats, ...) are NOT treated as zero: those crops keep the
placeholder values in crops.py and are reported as data gaps.
"""

from datetime import date
from pathlib import Path

import pandas as pd

CSV_PATH = Path(__file__).resolve().parent.parent / "data" / "crops" / "crops.csv"

DAYS_IN_MONTH = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]   # model year: 365 days
MIN_DAYS_IN_FIELD = 15          # a month counts as "crop in field" if the crop is there >= half of it
REF_YEAR = 2021                 # any non-leap year, only used to turn MM-DD into a day of the year

KC_COLUMNS = ["planting_window_start", "planting_window_end", "kc_ini", "kc_mid", "kc_end",
              "stage_len_ini", "stage_len_dev", "stage_len_mid", "stage_len_late"]


def load_table():
    """The CSV as a DataFrame indexed by crop_id. Dates stay text ("04-15")."""
    return pd.read_csv(CSV_PATH, dtype={"planting_window_start": str, "planting_window_end": str}).set_index("crop_id")


def _day_of_year(mm_dd):
    month, day = (int(x) for x in mm_dd.split("-"))
    return date(REF_YEAR, month, day).timetuple().tm_yday


def planting_day(row):
    """Middle of the planting window, as day of year (1-365)."""
    start, end = _day_of_year(row["planting_window_start"]), _day_of_year(row["planting_window_end"])
    if end < start:              # window crosses New Year (not the case today, but safe)
        end += 365
    return ((start + end) // 2 - 1) % 365 + 1


def daily_kc(row):
    """
    Kc for each of the 365 days of the year (0 when the crop is not in the field).
    FAO-56 crop curve:  ini: flat at Kc_ini | dev: straight line up to Kc_mid
                        mid: flat at Kc_mid | late: straight line down to Kc_end
    A crop planted in autumn (winter wheat) wraps over New Year: day 366 -> day 1.
    """
    kc = [0.0] * 365
    l_ini, l_dev, l_mid, l_late = (int(row[c]) for c in ["stage_len_ini", "stage_len_dev", "stage_len_mid", "stage_len_late"])
    k_ini, k_mid, k_end = row["kc_ini"], row["kc_mid"], row["kc_end"]
    start = planting_day(row) - 1                        # 0-based index

    for d in range(l_ini + l_dev + l_mid + l_late):
        if d < l_ini:
            value = k_ini
        elif d < l_ini + l_dev:
            value = k_ini + (k_mid - k_ini) * (d - l_ini) / l_dev
        elif d < l_ini + l_dev + l_mid:
            value = k_mid
        else:
            value = k_mid + (k_end - k_mid) * (d - l_ini - l_dev - l_mid) / l_late
        kc[(start + d) % 365] = value
    return kc


def monthly_kc(row):
    """12 monthly Kc values from the daily curve. A month with fewer than 15 crop days counts as 0 (bare)."""
    days = daily_kc(row)
    result, first = [], 0
    for n in DAYS_IN_MONTH:
        in_field = [k for k in days[first:first + n] if k > 0]
        result.append(round(float(sum(in_field) / len(in_field)), 2) if len(in_field) >= MIN_DAYS_IN_FIELD else 0)
        first += n
    return result


def has_full_curve(row):
    """True if every value the Kc curve needs is filled in."""
    return all(pd.notna(row[c]) for c in KC_COLUMNS)


def load_crops():
    """
    Returns (crops, gaps):
      crops: {crop_id: {"kc_monthly": [12] or None, "root_depth_m": float or None,
                        "family", "fixes_nitrogen", "source_url", "notes"}}
      gaps:  [text] what is missing, so the app can report it honestly
    """
    table = load_table()
    crops, gaps = {}, []
    for crop_id, row in table.iterrows():
        perennial = "forage" in str(row["category"])     # alfalfa: CSV stages = one cutting cycle, not a season
        kc = monthly_kc(row) if has_full_curve(row) and not perennial else None
        root = float(row["rooting_depth_m"]) if pd.notna(row["rooting_depth_m"]) else None
        crops[crop_id] = {
            "kc_monthly": kc,
            "root_depth_m": root,
            "family": row["plant_family"],
            "fixes_nitrogen": str(row["nitrogen_fixing"]).strip().lower() == "yes",
            "source_url": row["source_url"] if pd.notna(row["source_url"]) else None,
            "notes": row["notes"] if pd.notna(row["notes"]) else None,
        }
        if kc is None:
            gaps.append({"crop": crop_id, "text": f"{row['common_name']}: monthly water-use curve uses placeholder values"
                        + (" (perennial: CSV stages describe one cutting cycle)" if perennial else " (FAO values not filled in)")})
        if root is None:
            gaps.append({"crop": crop_id, "text": f"{row['common_name']}: root depth not verified, placeholder used"})
    return crops, gaps


if __name__ == "__main__":
    from crops import MAIN_CROP_KC, ROOT_DEPTH_M
    crops, gaps = load_crops()
    months = "J    F    M    A    M    J    J    A    S    O    N    D"
    print(f"{'':22}{months}")
    for crop_id, c in crops.items():
        if c["kc_monthly"]:
            print(f"{crop_id + ' (CSV)':22}" + " ".join(f"{k:<4}" for k in c["kc_monthly"]),
                  f"  root {c['root_depth_m']} m  planted day {planting_day(load_table().loc[crop_id])}")
            if crop_id in MAIN_CROP_KC:
                print(f"{crop_id + ' (old)':22}" + " ".join(f"{k:<4}" for k in MAIN_CROP_KC[crop_id]),
                      f"  root {ROOT_DEPTH_M.get(crop_id)} m")
    print("\nData gaps:")
    for g in gaps:
        print(" -", g["text"])
