"""
Turns numbers into  sentences. No Every sentence
is built from numbers the model already computed, so every claim can be traced.

    rotation_facts()  the key numbers of one rotation (bare months, stress years, ...)
    fit_breakdown()   "what 71 means": the weighted average behind the fit score
    field_facts()     how an alternative compares with the CURRENT rotation on this field
    summary()         one sentence per card, key numbers inline
    confidence()      high / medium: does it rely on placeholder crop data?
    recommendation()  the best fit for the farmer's priorities + the 3 biggest reasons
"""

from crops import CROP_DATA_GAPS, year_kc
from scoring import FIXES_NITROGEN, PLANT_FAMILY
from water_balance import worst_month

MONTH_NAMES = ["January", "February", "March", "April", "May", "June", "July",
               "August", "September", "October", "November", "December"]

# Same groups and weights as the frontend (frontend/src/core/scoring.js), so numbers match.
CRITERIA_GROUPS = {
    "water": ["water"],
    "soil_health": ["erosion", "bare_months", "nitrogen", "organic_matter", "pest_break"],
    "profit": ["profit"],
    "forage": ["forage"],
}
GROUP_LABELS = {"water": "Saving water", "soil_health": "Soil health", "profit": "Profit", "forage": "Forage value"}
DEFAULT_PRIORITIES = {"water": 0.3, "soil_health": 0.4, "profit": 0.2, "forage": 0.1}
PLACEHOLDER_SCORES = {"profit"}     # still sample values until crop prices are in crops.csv

# Readable names for each score, used in the "reasons" sentences.
SCORE_LABELS = {
    "water": "water reliability", "bare_months": "soil cover", "erosion": "erosion protection",
    "nitrogen": "nitrogen supply", "organic_matter": "organic matter", "pest_break": "pest-cycle breaks",
    "profit": "profit", "forage": "forage value",
}


# 1. The key numbers of one rotation 
def rotation_facts(steps, replay, rain_risk):
    """Plain numbers about one rotation, averaged over its rotation years."""
    n = len(steps)
    bare = [year_kc(s["main_crop"], s["cover_crop"])[1] for s in steps]   # bare months per rotation year
    crops = {s["main_crop"] for s in steps}
    worst = max(replay, key=lambda r: r["water_stress_pct"])
    return {
        "bare_months": round(sum(len(b) for b in bare) / n, 1),
        "stormy_bare_months": round(sum(1 for b in bare for m in b if rain_risk[m] == "high") / n, 1),
        "legume_years": sum(1 for s in steps if FIXES_NITROGEN.get(s["main_crop"])),
        "rotation_years": n,
        "crops": len(crops),
        "families": len({PLANT_FAMILY.get(c) for c in crops}),
        "stress_years": sum(1 for r in replay if r["outcome"] != "ok"),
        "fail_years": sum(1 for r in replay if r["outcome"] == "fail"),
        "replay_years": len(replay),
        "worst_year": worst["year"],
        "worst_pct": worst["water_stress_pct"],
        "worst_month": worst_month(replay),
    }


#  2. "What 71 means" 
def fit_breakdown(scores, priorities=None):
    """
    The fit score is a weighted average, like a school grade where some subjects count more.
    For each slider group: average its scores, multiply by the slider weight, add up, divide by total weight.
    Returns {"fit": 0-1, "parts": [{group, label, score, weight_pct, points}]} where the
    parts' points add up to the fit.
    """
    priorities = {**DEFAULT_PRIORITIES, **(priorities or {})}
    used = []
    for group, keys in CRITERIA_GROUPS.items():
        values = [scores[k] for k in keys if scores.get(k) is not None]
        weight = priorities.get(group, 0)
        if weight and values:
            used.append((group, sum(values) / len(values), weight))
    total_weight = sum(w for _, _, w in used)
    if not total_weight:
        return {"fit": 0.0, "parts": []}
    parts = [{
        "group": g,
        "label": GROUP_LABELS[g],
        "score": round(s, 2),
        "weight_pct": round(100 * w / total_weight),          # share of the farmer's priorities
        "points": round(s * w / total_weight, 3),             # how much this group adds to the fit
    } for g, s, w in used]
    return {"fit": round(sum(s * w for _, s, w in used) / total_weight, 2), "parts": parts}


#  3. Compared with the current rotation, on this field 
def field_facts(facts, current, slope_pct):
    """
    Field-specific comparisons with numbers, both better AND worse (honest trade-offs).
    Only lines where something actually changes are returned.
    """
    lines = []
    if facts["bare_months"] != current["bare_months"]:
        lines.append(f"Bare soil: {facts['bare_months']:g} months per year, compared with "
                     f"{current['bare_months']:g} in your current rotation (crop calendar).")
    if facts["stormy_bare_months"] != current["stormy_bare_months"]:
        lines.append(f"Bare months in this field's heavy-rain season: {facts['stormy_bare_months']:g} per year, "
                     f"compared with {current['stormy_bare_months']:g}"
                     + (f", on a {slope_pct:g}% slope (NASA SRTM)." if slope_pct else " (NASA POWER)."))
    if facts["legume_years"] / facts["rotation_years"] != current["legume_years"] / current["rotation_years"]:
        lines.append(f"Nitrogen-fixing crop in {facts['legume_years']} of {facts['rotation_years']} years, "
                     f"compared with {current['legume_years']} of {current['rotation_years']}.")
    if (facts["crops"], facts["families"]) != (current["crops"], current["families"]):
        lines.append(f"{facts['crops']} different crops from {facts['families']} plant families, "
                     f"compared with {current['crops']} from {current['families']}: more breaks in pest cycles."
                     if facts["crops"] > current["crops"] else
                     f"{facts['crops']} different crops, compared with {current['crops']}.")
    if facts["stress_years"] != current["stress_years"]:
        better = facts["stress_years"] < current["stress_years"]
        lines.append(f"Water stress in {facts['stress_years']} of {facts['replay_years']} past years, compared with "
                     f"{current['stress_years']} ({'fewer' if better else 'more'}; NASA POWER 2005-2025 replay).")
    return lines


#  4. One sentence per card 
def summary(facts, is_current):
    """Professional, plain sentence with the key numbers inline."""
    stress = (f"water stress in {facts['stress_years']} of {facts['replay_years']} years "
              f"(worst: {facts['worst_year']}, {facts['worst_pct']}% of crop water need not met)"
              if facts["stress_years"] else f"no water-stress years out of {facts['replay_years']}")
    cover = ("keeps the soil covered all year" if facts["bare_months"] == 0
             else f"leaves the soil bare about {facts['bare_months']:g} months per year")
    start = "Replayed through 2005-2025, your current rotation had " if is_current else "Replayed through 2005-2025, this rotation had "
    vulnerable = (f" The crop is most often short of water in {MONTH_NAMES[facts['worst_month'] - 1]}."
                  if facts.get("worst_month") else "")
    return f"{start}{stress}. It {cover}.{vulnerable}"


#  5. Confidence 
def confidence(steps):
    """'high' if every crop uses sourced crop-database values, 'medium' if any uses placeholders."""
    crops = {s["main_crop"] for s in steps} | {s["cover_crop"] for s in steps if s["cover_crop"]}
    return "medium" if any(g["crop"] in crops for g in CROP_DATA_GAPS) else "high"


#  6. The recommendation 
def recommendation(rotations, priorities, constraints):
    """
    Best fit among the rotations the farmer can actually do (requires met), and why.
    Reasons = the 3 scores where the winner beats the current rotation the most.
    """
    constraints = constraints or {}
    current = next(r for r in rotations if r["is_current"])
    possible = [r for r in rotations if all(constraints.get(req) for req in r["requires"])]
    best = max(possible, key=lambda r: r["fit"]["fit"])

    if best["is_current"]:
        return {
            "rotation_id": best["id"],
            "headline": "Your current rotation fits your priorities best.",
            "reasons": ["None of the alternatives scored higher with your current priority settings; "
                        "the cards below show the trade-offs of each one."],
        }

    # Placeholder scores (not computed from real data yet) never become a reason or trade-off.
    gains = sorted(((best["scores"][k] - current["scores"][k], k) for k in best["scores"]
                    if k not in PLACEHOLDER_SCORES
                    and best["scores"].get(k) is not None and current["scores"].get(k) is not None), reverse=True)
    reasons = [f"Higher {SCORE_LABELS[k]}: {round(100 * best['scores'][k])} vs {round(100 * current['scores'][k])} "
               f"for your current rotation." for gain, k in gains[:3] if gain > 0]
    losses = [f"Lower {SCORE_LABELS[k]}: {round(100 * best['scores'][k])} vs {round(100 * current['scores'][k])}."
              for gain, k in gains if gain < -0.05]
    return {
        "rotation_id": best["id"],
        "headline": f"Best fit for your priorities: {best['name']} "
                    f"(fit {round(100 * best['fit']['fit'])} vs {round(100 * current['fit']['fit'])} for your current rotation).",
        "reasons": reasons,
        "trade_offs": losses,
    }
