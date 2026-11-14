"""
ASTRATERRA backend API.

Run (from astraterra-kit/backend, with the venv active):
    uvicorn main:app --reload --port 8000
Then open http://localhost:8000/docs to try the endpoint in the browser.

The response follows docs/api-contract.sample.json (v0.3).
REAL parts (computed from NASA data + SoilGrids): field, soil, climate.monthly, climate.yearly,
    climate.frost, bare_field_calendar, and each rotation's replay + water_stress + water score.
PLACEHOLDER parts (copied from the sample contract until built): trends,
    year_types, risk_zones, the other scores, explanation text.
Each placeholder is listed in the response under "_placeholders"
"""

import copy
import json
from pathlib import Path
from typing import Optional

from fastapi import FastAPI
from pydantic import BaseModel

from crops import MAIN_CROP_KC, year_kc
from features import monthly_by_year, monthly_normals, frost_dates
from nasa_power import get_daily
from soil import get_soil, apply_overrides, water_per_metre
from water_balance import simulate_rotation

app = FastAPI(title="ASTRATERRA API")

# Iowa demo farm, used when the frontend does not send a location yet.
DEFAULT_LAT, DEFAULT_LON = 42.03, -93.62

# The sample contract: used for the parts that are not built yet.
CONTRACT = json.loads(
    (Path(__file__).resolve().parent.parent / "docs" / "api-contract.sample.json").read_text(encoding="utf-8")
)
SAMPLE = CONTRACT["response"]


# ---------- 1. What the frontend sends ----------
# pydantic checks the incoming JSON for us: wrong types give a clear error.
# Everything is optional so the frontend can send a partial request.
class AnalyzeRequest(BaseModel):
    lat: Optional[float] = None
    lon: Optional[float] = None
    field_name: Optional[str] = None
    name: Optional[str] = None
    current_rotation: list[str] = ["corn", "soybean"]
    priorities: dict[str, float] = {}
    constraints: dict[str, bool] = {}
    soil_overrides: dict[str, Optional[float]] = {}


# ---------- 2. Rotation templates ----------
# Each alternative is built from the farmer's current rotation.
# Robajr's templates will replace these.
def build_rotations(current):
    def steps(crops, cover=None):
        return [{"main_crop": c, "cover_crop": cover} for c in crops]

    return [
        {"id": "current", "name": " / ".join(c.title() for c in current) + " (current)",
         "is_current": True, "requires": [], "steps": steps(current)},
        {"id": "alt_cover", "name": " / ".join(c.title() for c in current) + " + cereal rye cover",
         "is_current": False, "requires": [], "steps": steps(current, "cereal_rye")},
        {"id": "alt_small_grain", "name": " / ".join(c.title() for c in current) + " / Winter wheat + red clover",
         "is_current": False, "requires": [],
         "steps": steps(current) + [{"main_crop": "wheat_winter", "cover_crop": "red_clover"}]},
        {"id": "alt_perennial", "name": " / ".join(c.title() for c in current) + " / 2 years alfalfa",
         "is_current": False, "requires": ["hay_equipment"],
         "steps": steps(current) + steps(["alfalfa", "alfalfa"])},
    ]


# ---------- 3. The endpoint ----------
@app.post("/api/analyze")
def analyze(req: AnalyzeRequest):
    lat = req.lat if req.lat is not None else DEFAULT_LAT
    lon = req.lon if req.lon is not None else DEFAULT_LON
    field_name = req.field_name or req.name or "Your field"

    # Unknown crops would crash the model, so keep only the ones we have data for.
    current = [c for c in req.current_rotation if c in MAIN_CROP_KC] or ["corn", "soybean"]

    # --- Real NASA data ---
    daily = get_daily(lat, lon)
    monthly = monthly_by_year(daily)
    normals = monthly_normals(monthly).reset_index()
    years =sorted(monthly.index.get_level_values("year").unique())

    response = copy.deepcopy(SAMPLE)   # start from the sample, then overwrite real parts
    response["_placeholders"] = [
        "climate.trends", "climate.year_types", "climate.yearly[].year_type",
        "risk_zones", "rotations[].scores (except water and bare_months)",
        "rotations[].why/evidence/benefits/data_gaps/risks_for_local_review",
    ]

    response["field"] = {
        "name": field_name, "lat": lat, "lon": lon,
        "elevation_m": None,  # comes with the elevation (risk map) step
        "data_years": [int(years[0]), int(years[-1])],
    }
    response["climate"]["frost"] = frost_dates(daily)

    # --- Soil: SoilGrids, then the farmer's own numbers on top ---
    soil_values, soil_source = apply_overrides(get_soil(lat, lon), req.soil_overrides)
    per_metre = water_per_metre(soil_values["clay_pct"], soil_values["sand_pct"], soil_values["organic_carbon_pct"])
    response["soil"] = {**soil_values, "water_per_metre_mm": per_metre, "source": soil_source}


    # climate.monthly: the typical year
    response["climate"]["monthly"] = [
        {
            "month": int(r.month),
            "rain_mm": round(float(r.rain_mm), 1),
            "et0_mm": round(float(r.et0_mm), 1),
            "water_balance_mm": round(float(r.water_balance_mm), 1),
            "tmax_c": round(float(r.tmax_c), 1),
            "tmin_c": round(float(r.tmin_c), 1),
            "heat_days": round(float(r.heat_days), 1),
            "heavy_rain_days": round(float(r.heavy_rain_days), 1),
            "soil_moisture_root": round(float(r.soil_moisture_root), 2),
        }
        for r in normals.itertuples()
    ]

    # climate.yearly: summer (Jun-Aug) numbers for each year
    summer = monthly[monthly.index.get_level_values("month").isin([6, 7, 8])]
    by_year = summer.groupby("year").agg(
        summer_rain_mm=("rain_mm", "sum"),
        summer_tmax_c=("tmax_c", "mean"),
        heat_days=("heat_days", "sum"),
        summer_soil_moisture_root=("soil_moisture_root", "mean"),
    )
    response["climate"]["yearly"] = [
        {
            "year": int(year),
            "summer_rain_mm": round(float(r.summer_rain_mm), 1),
            "summer_tmax_c": round(float(r.summer_tmax_c), 1),
            "heat_days": int(r.heat_days),
            "summer_soil_moisture_root": round(float(r.summer_soil_moisture_root), 2),
            "year_type": None,  # Brandon's clustering fills this in
        }
        for year, r in by_year.iterrows()
    ]

    # Heavy-rain risk per month: rank months by heavy-rain days, top 4 = high, next 4 = medium.
    ranked = normals.sort_values("heavy_rain_days", ascending=False)["month"].tolist()
    rain_risk = {m: ("high" if i < 4 else "medium" if i < 8 else "low") for i, m in enumerate(ranked)}

    # Bare-field calendar for the CURRENT rotation (first year), from the crop calendar.
    _, bare_now = year_kc(current[0])
    response["bare_field_calendar"] = {
        "source": "Crop calendar + NASA POWER heavy-rain days (MODIS NDVI check coming)",
        "months": [
            {"month": m, "bare": m in bare_now, "ndvi_median": None, "heavy_rain_risk": rain_risk[m]}
            for m in range(1, 13)
        ],
    }

    # --- Rotations: real replay through every past year ---
    samples_by_id = {r["id"]: r for r in SAMPLE["rotations"]}
    rotations_out = []
    for rot in build_rotations(current):
        replay = simulate_rotation(monthly, rot["steps"], per_metre)
        bad_years = [r for r in replay if r["outcome"] != "ok"]
        avg_stress = sum(r["water_stress_pct"] for r in replay) / len(replay)

        # Bare months averaged over the rotation's years
        bare_counts = [len(year_kc(s["main_crop"], s["cover_crop"])[1]) for s in rot["steps"]]
        avg_bare = sum(bare_counts) / len(bare_counts)

        sample = copy.deepcopy(samples_by_id.get(rot["id"], SAMPLE["rotations"][0]))
        scores = sample["scores"]
        scores["water"] = round(max(0.0, 1 - avg_stress / 30), 2)   # 0% avg stress -> 1.0, 30%+ -> 0
        scores["bare_months"] = round(1 - avg_bare / 12, 2)         # 0 bare months -> 1.0

        rotations_out.append({
            **sample,
            "id": rot["id"],
            "name": rot["name"],
            "is_current": rot["is_current"],
            "requires": rot["requires"],
            "sequence": [s["main_crop"] + (f" + {s['cover_crop']}" if s["cover_crop"] else "") for s in rot["steps"]],
            "scores": scores,
            "water_stress": {
                **sample["water_stress"],          # keeps worst_month (placeholder)
                "years_with_stress": len(bad_years),
                "years_total": len(replay),
                "worst_year": max(replay, key=lambda r: r["water_stress_pct"])["year"],
            },
            "replay": replay,
        })

    response["rotations"] = rotations_out
    return response


@app.get("/api/health")
def health():
    """Quick check that the server is running."""
    return {"status": "ok"}
