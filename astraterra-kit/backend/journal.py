"""
Farm Journal clues: simple rules, not machine learning.
One farm has 5-20 records, far too few to train a model on, and rules explain themselves.

The farmer logs entries:  {"year": 2023, "crop": "soybean", "outcome": "failed" | "so_so" | "good" | None, "notes": "..."}
(outcome None = a USDA satellite record without the farmer's verdict: used only to know what grew when)

Each rule looks for a pattern and returns a clue:
  {"kind", "title", "text", "evidence": [{claim, value, source}]}

Rules:
  1. ph_mismatch     failed crops prefer a pH this soil does not have        (crops.csv + SoilGrids/farmer)
  2. dry_years       failures fall in the driest summers on record here     (NASA POWER)
  3. same_family     repeated failures within one plant family               (crops.csv)
  4. same_crop_twice a crop failed right after itself                         (journal + USDA history)
  5. what_works      crops that did well more than once                       (journal)
Every clue ends with "check" wording: the tool suggests causes, the farmer and local experts decide.
"""

from crops import CROP_DB

BAD = {"failed", "so_so"}          # outcomes that count as "did not go well"


def _name(crop):
    return CROP_DB.get(crop, {}).get("name") or crop.replace("_", " ").title()


def _ph_range(lo, hi):
    """(6.5, None) -> 'pH 6.5 or higher', (6.0, 6.5) -> 'pH 6.0-6.5'"""
    if lo and hi:
        return f"pH {lo:g}-{hi:g}"
    return f"pH {lo:g} or higher" if lo else f"pH up to {hi:g}"


def _and(items):
    """['a', 'b', 'c'] -> 'a, b and c'"""
    items = [str(i) for i in items]
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " and " + items[-1]


# ---------- Rule 1: pH ----------
def ph_mismatch(entries, soil_ph, ph_source):
    """Failed crops whose preferred pH range does not include this soil's pH."""
    if soil_ph is None:
        return []
    out_of_range = {}
    for e in entries:
        info = CROP_DB.get(e["crop"], {})
        lo, hi = info.get("ph_min"), info.get("ph_max")
        if e.get("outcome") == "failed" and (lo or hi):
            if (lo and soil_ph < lo) or (hi and soil_ph > hi):
                out_of_range[e["crop"]] = (lo, hi)
    if not out_of_range:
        return []
    crops = list(out_of_range)
    too_acid = any(lo and soil_ph < lo for lo, hi in out_of_range.values())
    ranges = _and([f"{_name(c)} prefers {_ph_range(lo, hi)}" for c, (lo, hi) in out_of_range.items()])
    soil_ph = round(soil_ph, 1)
    return [{
        "kind": "ph_mismatch",
        "title": "Soil pH may not suit these crops",
        "text": f"{_and([_name(c) for c in crops])} failed. {ranges}, but this soil's pH is about {soil_ph:g}. "
                + ("Soil that is too acidic can hold back these crops; a soil test would show whether lime could help."
                   if too_acid else "Soil that is too alkaline can hold back these crops; a soil test would confirm it."),
        "evidence": [{"claim": "Soil pH", "value": soil_ph, "source": ph_source},
                     *[{"claim": f"{_name(c)} preferred pH", "value": _ph_range(lo, hi), "source": "Crop database"}
                       for c, (lo, hi) in out_of_range.items()]],
    }]


# ---------- Rule 2: dry years ----------
def dry_year_failures(entries, dry_years):
    """Poor results in the years NASA data shows as the driest summers here."""
    hits = sorted({e["year"] for e in entries if e.get("outcome") in BAD and e["year"] in dry_years})
    if not hits:
        return []
    return [{
        "kind": "dry_years",
        "title": "Your poor years match the driest summers",
        "text": f"Your poor results in {_and(hits)} fall in {'one of the driest summers' if len(hits) == 1 else 'the driest summers'} "
                f"recorded here since 2005. Weather, rather than management, may explain much of the loss. "
                f"Rotations with lower summer water demand or deeper roots are worth comparing in the report.",
        "evidence": [{"claim": "Driest summers (root-zone soil moisture)", "value": _and(sorted(dry_years)),
                      "source": "NASA POWER 2005-2025"}],
    }]


# ---------- Rule 3: same plant family ----------
def same_family_failures(entries):
    """Two or more failures (different years) of crops from the same plant family."""
    by_family = {}
    for e in entries:
        if e.get("outcome") == "failed":
            family = CROP_DB.get(e["crop"], {}).get("family")
            if family:
                by_family.setdefault(family, []).append(e)
    clues = []
    for family, failed in by_family.items():
        years = sorted({e["year"] for e in failed})
        if len(years) >= 2:
            crops = sorted({_name(e["crop"]) for e in failed})
            clues.append({
                "kind": "same_family",
                "title": f"Repeated failures in one plant family ({family})",
                "text": f"{_and(crops)} failed in {_and(years)}; {'they belong' if len(crops) > 1 else 'it belongs'} to the same "
                        f"plant family, {family}. Crops from one family share many pests and diseases, which can build up "
                        f"in the soil. Rotating to a different family for a year or two is worth discussing with a local agronomist.",
                "evidence": [{"claim": "Plant family", "value": family, "source": "Crop database"}],
            })
    return clues


# ---------- Rule 4: same crop two years running ----------
def same_crop_twice(entries):
    """A crop failed in a year right after the same crop grew there."""
    grown = {}
    for e in entries:                      # what grew each year (farmer entries win over USDA records)
        if e["year"] not in grown or e.get("outcome") is not None:
            grown[e["year"]] = e["crop"]
    hits = sorted({e["year"] for e in entries
                   if e.get("outcome") == "failed" and grown.get(e["year"] - 1) == e["crop"]})
    if not hits:
        return []
    crop = grown[hits[0]]
    return [{
        "kind": "same_crop_twice",
        "title": "Failure after the same crop two years in a row",
        "text": f"{_name(crop)} failed in {_and(hits)} after being grown in the same field the year before. "
                f"Growing a crop after itself lets its pests and diseases carry over; a rotation break usually helps.",
        "evidence": [{"claim": "Same crop in consecutive years", "value": _and([f"{y - 1}-{y}" for y in hits]),
                      "source": "Your journal + USDA Cropland Data Layer"}],
    }]


# ---------- Rule 5: what works ----------
def what_works(entries):
    good = {}
    for e in entries:
        if e.get("outcome") == "good":
            good.setdefault(e["crop"], set()).add(e["year"])
    return [{
        "kind": "what_works",
        "title": f"{_name(crop)} has done well here",
        "text": f"{_name(crop)} did well in {_and(sorted(years))}. Keeping it in the rotation builds on what already works on this field.",
        "evidence": [{"claim": "Good years", "value": len(years), "source": "Your journal"}],
    } for crop, years in good.items() if len(years) >= 2]


def journal_clues(entries, soil_ph, ph_source, dry_years):
    """All clues, most important first. Fewer than 2 farmer verdicts -> a friendly 'keep logging' note."""
    verdicts = [e for e in entries if e.get("outcome")]
    clues = (ph_mismatch(entries, soil_ph, ph_source) + dry_year_failures(entries, dry_years)
             + same_family_failures(entries) + same_crop_twice(entries) + what_works(entries))
    if not clues and len(verdicts) < 2:
        clues = [{"kind": "keep_logging", "title": "Keep logging your seasons",
                  "text": "Add how each season went. With a few entries the journal starts looking for patterns, "
                          "such as soil pH, dry summers or crops that follow themselves.", "evidence": []}]
    return clues
