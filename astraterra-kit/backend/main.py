"""
ASTRATERRA backend API.

Run (from astraterra-kit/backend, with the venv active):
    uvicorn main:app --reload --port 8000
Then open http://localhost:8000/docs to try the endpoint in the browser.

The response follows docs/api-contract.sample.json (v0.3).
REAL parts (computed from NASA POWER + NASA SRTM + SoilGrids): field, soil, risk_zones, climate.monthly, climate.yearly,
    climate.frost, bare_field_calendar, and each rotation's replay + water_stress + water score.
PLACEHOLDER parts (copied from the sample contract until built): trends,
    year_types, the other scores, explanation text.
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
from terrain import risk_zones
from cdl import crop_history, detect_rotation, is_cropland
from water_balance import simulate_rotation
from scoring import score_rotation

app = FastAPI(title="ASTRATERRA API")

# Demo farm (Driftless Area, near Bloomingdale, WI): hay until 2019, corn/soy since 2020,
# on hilly ground. Used when the frontend does not send a location.
DEFAULT_LAT, DEFAULT_LON = 43.70767, -90.93877

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
    current_rotation: Optional[list[str]] = None   # None/[] = not given: detect it from USDA CDL
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

    # --- Real NASA data ---
    daily = get_daily(lat, lon)
    monthly = monthly_by_year(daily)
    normals = monthly_normals(monthly).reset_index()
    years =sorted(monthly.index.get_level_values("year").unique())

    # --- What the field really grew (USDA CDL). Used when the farmer didn't tell us. ---
    history = crop_history(lat, lon)
    detected, fit = detect_rotation(history, int(years[0]))
    if req.current_rotation:                                       # the farmer told us
        wanted, rotation_source = req.current_rotation, "farmer"
    elif detected:
        wanted, rotation_source = detected, "USDA Cropland Data Layer"
    else:
        wanted, rotation_source = ["corn", "soybean"], "default"
    # Unknown crops would crash the model, so keep only the ones we have data for.
    current = [c for c in wanted if c in MAIN_CROP_KC] or ["corn", "soybean"]

    response = copy.deepcopy(SAMPLE)   # start from the sample, then overwrite real parts
    response["_placeholders"] = [
        "climate.trends", "climate.year_types", "climate.yearly[].year_type",
        "rotations[].scores.profit",
        "rotations[].why/evidence/benefits/data_gaps/risks_for_local_review",
    ]

    # --- Terrain: NASA SRTM elevation -> slope (erosion) + low spots (frost pockets) ---
    zones, elevation_m, terrain = risk_zones(lat, lon)
    response["risk_zones"] = zones

    response["field"] = {
        "name": field_name, "lat": lat, "lon": lon,
        "elevation_m": elevation_m,
        "data_years": [int(years[0]), int(years[-1])],
        "terrain": terrain,   # field slope, steepest slope, height range (m)
        "is_cropland": is_cropland(history),   # False = pin is on a town / lake / forest
        "crop_history": [{"year": h["year"], "crop": h["crop"], "name": h["name"]} for h in history],
        "detected_rotation": detected,
        "detected_rotation_fit": fit,          # share of recent years that match the pattern
        "rotation_used": current,
        "rotation_source": rotation_source,    # farmer | USDA Cropland Data Layer | default
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
            "solar_mj": round(float(r.solar_mj), 1),      # average daily sunshine energy (MJ/m2/day)
            "gdd": round(float(r.gdd)),                   # growing degree days this month (base 10 C)
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
    # Season GDD (May-Sep) per year: is there enough heat to ripen a crop?
    season = monthly[monthly.index.get_level_values("month").isin([5, 6, 7, 8, 9])]
    by_year["season_gdd"] = season.groupby("year")["gdd"].sum()
    # Soil moisture vs normal: + = wetter summer than the 21-year average, - = drier
    by_year["soil_moisture_vs_normal"] = by_year["summer_soil_moisture_root"] - by_year["summer_soil_moisture_root"].mean()
    response["climate"]["yearly"] = [
        {
            "year": int(year),
            "summer_rain_mm": round(float(r.summer_rain_mm), 1),
            "summer_tmax_c": round(float(r.summer_tmax_c), 1),
            "heat_days": int(r.heat_days),
            "summer_soil_moisture_root": round(float(r.summer_soil_moisture_root), 2),
            "soil_moisture_vs_normal": round(float(r.soil_moisture_vs_normal), 3),
            "season_gdd": round(float(r.season_gdd)),
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

        sample = copy.deepcopy(samples_by_id.get(rot["id"], SAMPLE["rotations"][0]))
        # Real scores + the evidence behind them (scoring.py). Profit: placeholder until prices are in.
        scores, evidence = score_rotation(rot["steps"], replay, rain_risk, terrain.get("field_slope_pct"))
        scores["profit"] = sample["scores"]["profit"]

        rotations_out.append({
            **sample,
            "id": rot["id"],
            "name": rot["name"],
            "is_current": rot["is_current"],
            "requires": rot["requires"],
            "sequence": [s["main_crop"] + (f" + {s['cover_crop']}" if s["cover_crop"] else "") for s in rot["steps"]],
            "scores": scores,
            "evidence": evidence,
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
