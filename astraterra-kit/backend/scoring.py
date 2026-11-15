"""
Rotation scores, 0-1 (higher = better). Deterministic rules, no AI.
Each function returns (score, evidence) so every number shown to the farmer can be traced.

The frontend (frontend/src/core/scoring.js) groups these into the priority sliders:
  water | soil_health = erosion, bare_months, nitrogen, organic_matter, pest_break | profit | forage

Crop traits below are PLACEHOLDERS until Robajr's data/crops/crops.csv is loaded
(columns plant_family, nitrogen_fixing, organic_matter_value, forage_value).
"""

from crops import year_kc

# ---- Crop traits (placeholder, from the crop template + common agronomy) ----
PLANT_FAMILY = {"corn": "Poaceae", "soybean": "Fabaceae", "wheat_winter": "Poaceae", "alfalfa": "Fabaceae"}
FIXES_NITROGEN = {"corn": False, "soybean": True, "wheat_winter": False, "alfalfa": True,
                  "red_clover": True, "cereal_rye": False}
# How much each crop builds soil organic matter in one year (roots + residue left behind), 0-1.
# Perennials keep roots in the ground all year; soybean leaves little residue.
ORGANIC_MATTER_VALUE = {"corn": 0.4, "soybean": 0.15, "wheat_winter": 0.5, "alfalfa": 1.0}
COVER_CROP_OM_BONUS = 0.3
# Forage produced in one year (hay / grazing), 0-1.
FORAGE_VALUE = {"corn": 0.0, "soybean": 0.0, "wheat_winter": 0.1, "alfalfa": 1.0,
                "red_clover": 0.3, "cereal_rye": 0.2}

# Heavy-rain weight of a bare month: bare soil in a stormy month erodes most.
RAIN_WEIGHT = {"high": 1.0, "medium": 0.5, "low": 0.2}
WORST_EXPOSURE = 4 * 1.0 + 4 * 0.5 + 4 * 0.2     # bare all 12 months
SLOPE_HIGH_PCT = 9                               # same "high" class as terrain.py


def _ev(claim, value, unit, source):
    return {"claim": claim, "value": value, "unit": unit, "source": source}


def water_score(replay):
    """Average water stress over all replayed years. 0% -> 1.0, 30%+ -> 0."""
    avg = sum(r["water_stress_pct"] for r in replay) / len(replay)
    bad = sum(1 for r in replay if r["outcome"] != "ok")
    return round(max(0.0, 1 - avg / 30), 2), [
        _ev("Years with water stress", f"{bad} of {len(replay)}", "years", "NASA POWER + FAO-56 water balance"),
        _ev("Average crop water shortfall", round(avg, 1), "%", "NASA POWER + FAO-56 water balance"),
    ]


def bare_months_score(steps):
    """Months per year with nothing growing. 0 -> 1.0, 12 -> 0."""
    avg = sum(len(year_kc(s["main_crop"], s["cover_crop"])[1]) for s in steps) / len(steps)
    return round(1 - avg / 12, 2), [_ev("Bare months", round(avg, 1), "months/year", "Crop calendar")]


def erosion_score(steps, rain_risk, field_slope_pct):
    """
    Erosion protection. Bare months are weighted by how stormy they are here
    (NASA POWER heavy-rain days), then scaled by the field's slope (NASA SRTM):
    a flat field erodes about half as much, a 9%+ slope about 1.5x as much.
    """
    exposure = 0.0
    for s in steps:
        _, bare = year_kc(s["main_crop"], s["cover_crop"])
        exposure += sum(RAIN_WEIGHT[rain_risk[m]] for m in bare)
    exposure /= len(steps)
    slope_mult = 0.5 + min(field_slope_pct or 0, 1.5 * SLOPE_HIGH_PCT) / SLOPE_HIGH_PCT
    stormy_bare = sum(1 for s in steps for m in year_kc(s["main_crop"], s["cover_crop"])[1]
                      if rain_risk[m] == "high") / len(steps)
    score = max(0.0, 1 - exposure / WORST_EXPOSURE * slope_mult)
    return round(score, 2), [
        _ev("Bare months in heavy-rain season", round(stormy_bare, 1), "months/year", "Crop calendar + NASA POWER"),
        _ev("Field slope", field_slope_pct, "%", "NASA SRTM"),
    ]


def nitrogen_score(steps):
    """Legumes add nitrogen: main-crop legume year = 1 point, legume cover = 0.5. Corn every year -> 0.2."""
    points = sum((1.0 if FIXES_NITROGEN.get(s["main_crop"]) else 0.0)
                 + (0.5 if FIXES_NITROGEN.get(s["cover_crop"]) else 0.0) for s in steps)
    share = min(points / len(steps), 1.0)
    legume_years = sum(1 for s in steps if FIXES_NITROGEN.get(s["main_crop"]))
    return round(0.2 + 0.8 * share, 2), [
        _ev("Years with a nitrogen-fixing main crop", f"{legume_years} of {len(steps)}", "years", "Crop database"),
    ]


def pest_break_score(steps):
    """
    Pests and diseases build up when the same crop / plant family repeats.
    More different crops and families = more broken pest cycles. One crop every year -> 0.1.
    """
    crops = {s["main_crop"] for s in steps}
    families = {PLANT_FAMILY[c] for c in crops}
    score = min(1.0, 0.1 + 0.25 * (len(crops) - 1) + 0.25 * (len(families) - 1))
    return round(score, 2), [
        _ev("Different main crops", len(crops), "crops", "Rotation"),
        _ev("Different plant families", len(families), "families", "Crop database"),
    ]


def organic_matter_score(steps):
    """Average yearly organic-matter value of the crops (+ bonus for a cover crop)."""
    per_year = [min(1.0, ORGANIC_MATTER_VALUE[s["main_crop"]] + (COVER_CROP_OM_BONUS if s["cover_crop"] else 0))
                for s in steps]
    perennial_years = sum(1 for s in steps if s["main_crop"] == "alfalfa")
    return round(sum(per_year) / len(per_year), 2), [
        _ev("Years with a perennial or cover crop",
            f"{sum(1 for s in steps if s['cover_crop'] or s['main_crop'] == 'alfalfa')} of {len(steps)}", "years",
            "Rotation"),
    ] + ([_ev("Perennial (alfalfa) years", perennial_years, "years", "Rotation")] if perennial_years else [])


def forage_score(steps):
    """Share of the rotation that produces hay or grazing."""
    per_year = [min(1.0, FORAGE_VALUE[s["main_crop"]] + FORAGE_VALUE.get(s["cover_crop"], 0)) for s in steps]
    return round(sum(per_year) / len(per_year), 2), []


def score_rotation(steps, replay, rain_risk, field_slope_pct):
    """All scores + all evidence for one rotation. Profit stays a placeholder until prices are in."""
    scores, evidence = {}, []
    for name, (score, ev) in {
        "water": water_score(replay),
        "bare_months": bare_months_score(steps),
        "erosion": erosion_score(steps, rain_risk, field_slope_pct),
        "nitrogen": nitrogen_score(steps),
        "organic_matter": organic_matter_score(steps),
        "pest_break": pest_break_score(steps),
        "forage": forage_score(steps),
    }.items():
        scores[name] = score
        evidence += ev
    for i, e in enumerate(evidence, 1):
        e["id"] = f"e{i}"
    return scores, evidence
