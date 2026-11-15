"""
The rotations we compare: the farmer's current one +  templates (data/rotations/templates.json).

A template describes a rotation in BLOCKS; the replay needs ONE ENTRY PER YEAR:
    template steps:  [{"use_current": true}, {"main_crop": "alfalfa", "cover_crop": null, "years": 2}]
    farmer grows:    ["corn", "soybean"]
    expanded:        [{"main_crop": "corn",    "cover_crop": None},
                      {"main_crop": "soybean", "cover_crop": None},
                      {"main_crop": "alfalfa", "cover_crop": None},
                      {"main_crop": "alfalfa", "cover_crop": None}]
"""

import json
from pathlib import Path

from crops import MAIN_CROP_KC

TEMPLATES_PATH = Path(__file__).resolve().parent.parent / "data" / "rotations" / "templates.json"


def load_templates():
    return json.loads(TEMPLATES_PATH.read_text(encoding="utf-8"))["templates"]


def nice_name(crops):
    """["corn", "wheat_winter"] -> "Corn / Wheat Winter" """
    return " / ".join(c.replace("_", " ").title() for c in crops)


def expand_steps(template_steps, current):
    """
    Turn a template's blocks into one step per rotation year.
      {"use_current": true, "cover_crop": "cereal_rye"}  -> one step per crop in `current`,
                                                             each with that cover crop (None if not given)
      {"main_crop": "alfalfa", "cover_crop": None, "years": 2} -> that crop, repeated `years` times
    Returns a list of {"main_crop": ..., "cover_crop": ...}
    """
    steps = []
    for block in template_steps:
        if block.get("use_current"):
            for crop in current:
                steps.append({
                    "main_crop": crop,
                    "cover_crop": block.get("cover_crop")
                })
        else:
            years = block.get("years", 1)

            for _ in range(years):
                steps.append({
                    "main_crop": block["main_crop"],
                    "cover_crop": block.get("cover_crop")
                })        
            pass
    return steps


def build_rotations(current):
    """Current rotation first, then every template whose crops our water model knows."""
    rotations = [{
        "id": "current", "name": nice_name(current) + " (current)", "is_current": True,
        "requires": [], "steps": [{"main_crop": c, "cover_crop": None} for c in current], "template": None,
    }]
    for t in load_templates():
        steps = expand_steps(t["steps"], current)
        if any(s["main_crop"] not in MAIN_CROP_KC for s in steps):
            continue                                   # a crop without water data (e.g. oats): can't replay it
        rotations.append({
            "id": t["id"],
            "name": t["name"].replace("{current}", nice_name(current)),
            "is_current": False,
            "requires": t.get("requires", []),
            "steps": steps,
            "template": t,                             
        })
    return rotations


if __name__ == "__main__":
    for rot in build_rotations(["corn", "soybean"]):
        print(f"{rot['id']:16} {rot['name']:42}", [s["main_crop"] + (f"+{s['cover_crop']}" if s["cover_crop"] else "") for s in rot["steps"]])
