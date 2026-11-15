"""
Placeholder crop water data until Roket's crop database (data/crops/crops.csv) is ready.

Kc (crop coefficient) = how much water a crop uses compared with ET0 (reference grass).
    crop water use (mm) = ET0 (mm) x Kc
Kc is low when the plant is small, about 1.0-1.2 when it fully covers the ground,
and drops again as it ripens.

Values: FAO-56 Table 12 (Kc ini / mid / end), spread over calendar months for a
US Midwest (Iowa) planting calendar. Approximate, so mark as PLACEHOLDER in the evidence.
Source: https://www.fao.org/4/x0490e/x0490e0b.htm#tabulated%20kc%20values
"""

# Kc for each calendar month, Jan..Dec. 0 = this crop is not in the field that month.
MAIN_CROP_KC = {
    #             J    F    M    A    M     J     J     A     S     O    N    D
    "corn":     [0,   0,   0,   0,   0.3,  0.7,  1.2,  1.15, 0.7,  0,   0,   0],    # plant May, harvest Oct
    "soybean":  [0,   0,   0,   0,   0.2,  0.5,  1.0,  1.15, 0.6,  0,   0,   0],    # plant mid-May, harvest Oct
    "wheat_winter": [0.3, 0.3, 0.6, 1.0, 1.15, 1.0, 0.3, 0,  0,    0.4, 0.4, 0.3],  # plant Oct, harvest early Jul
    "alfalfa":  [0.3, 0.3, 0.5, 0.9, 0.95, 0.95, 0.95, 0.95, 0.9, 0.6, 0.4, 0.3],  # perennial, cut several times
}

# Cover crops grow in the gap months (fall to spring) when no main crop is in the field.
COVER_CROP_KC = {
    #               J    F    M    A    M  J  J  A  S  O    N    D
    "cereal_rye": [0.3, 0.3, 0.6, 0.9, 0, 0, 0, 0, 0, 0.4, 0.4, 0.3],  # terminated before corn planting
    "red_clover": [0.3, 0.3, 0.6, 0.9, 0, 0, 0, 0, 0, 0.4, 0.4, 0.3],
}

# Bare soil still loses some water by evaporation from the surface.
BARE_SOIL_KC = 0.25

# Root depth (m): how deep a crop can pull water from. Deeper roots = bigger "bucket".
ROOT_DEPTH_M = {
    "corn": 1.0,
    "soybean": 0.8,
    "wheat_winter": 1.0,
    "alfalfa": 1.5,
}


# ---- Real values from Robajr's crop database (data/crops/crops.csv) replace the placeholders ----
# Where the CSV has a complete FAO-56 curve or a root depth, it wins. Blank cells keep the
# placeholder above and are listed in CROP_DATA_GAPS so the app can say so.
from crop_data import load_crops

CROP_DB, CROP_DATA_GAPS = load_crops()
KC_SOURCE = {crop: "placeholder" for crop in MAIN_CROP_KC}   # where each crop's curve came from

for crop_id, info in CROP_DB.items():
    if info["kc_monthly"] and crop_id not in COVER_CROP_KC:
        MAIN_CROP_KC[crop_id] = info["kc_monthly"]
        KC_SOURCE[crop_id] = "crops.csv (FAO-56)"
    if info["root_depth_m"]:
        ROOT_DEPTH_M[crop_id] = info["root_depth_m"]


def year_kc(main_crop, cover_crop=None):
    """
    Return 12 Kc values (Jan..Dec) for one rotation year.
    Months with no main crop use the cover crop if there is one, else bare soil.
    Also returns which months are bare (no crop cover at all).
    """
    main = MAIN_CROP_KC[main_crop]
    cover = COVER_CROP_KC.get(cover_crop, [0] * 12)

    kc = []
    bare_months = []
    for month_index in range(12):
        if main[month_index] > 0:
            kc.append(main[month_index])
        elif cover[month_index] > 0:
            kc.append(cover[month_index])
        else:
            kc.append(BARE_SOIL_KC)
            bare_months.append(month_index + 1)   # store as 1..12
    return kc, bare_months


if __name__ == "__main__":
    kc, bare = year_kc("corn")
    print("Corn alone:          ", kc, "bare months:", bare)
    kc, bare = year_kc("corn", "cereal_rye")
    print("Corn + cereal rye:   ", kc, "bare months:", bare)
