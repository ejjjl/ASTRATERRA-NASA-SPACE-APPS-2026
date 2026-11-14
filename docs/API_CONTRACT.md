# ASTRATERRA API contract (draft v0.1)

This is the format the backend sends and the frontend reads. Until the real backend is ready,
the frontend builds against the example files in `backend/sample_responses/`.

**Rule:** if you want to change a field name or shape, tell the whole team first and update this file.

Conventions:
- Base URL (local): `http://localhost:8000`
- All requests and responses are JSON.
- Months are numbers 1–12. Years are numbers (e.g. `2012`).
- Units are in the field name: `_mm`, `_c` (°C), `_pct` (%), `_m`, `_ha`.
- Coordinates: `lat`, `lon` in decimal degrees. Polygons are `[[lon, lat], ...]` (GeoJSON order).
- Every number shown to a farmer should have a source. `sources` lists them.

---

## 1. `POST /field/analyze`

Everything about the field itself: climate, trends, year types, soil and the risk map.

**Request**
```json
{
  "lat": 42.03,
  "lon": -93.63,
  "polygon": [[-93.635, 42.026], [-93.625, 42.026], [-93.625, 42.034], [-93.635, 42.034]]
}
```
`polygon` is optional. Without it, the backend can use a ~500 m square around the point.

**Response:** see `backend/sample_responses/field_analyze.json`

| Key | What it is | Used on screen |
|---|---|---|
| `field` | Location, area, elevation | Header |
| `period` | Years of data used (e.g. 2005–2025) | Footnotes |
| `climate.monthly` | 12 rows: rain, evaporation demand (ET0), water balance, temps, heat days, heavy-rain days, soil moisture | Field analysis charts |
| `climate.frost` | Typical last spring / first fall frost, frost-free days | Field analysis |
| `climate.heavy_rain_months` | Months with the most heavy-rain days | Bare-field calendar |
| `climate.yearly` | One row per year, with its year type | Year strip / scatter |
| `trends` | Change per decade + a ready-to-show sentence | Trend cards |
| `year_types` | Groups of similar years (hot/dry, normal, wet/cool) | Year types panel |
| `soil` | Auto-filled soil values; `source` says where each came from | Soil questionnaire |
| `risk_map` | Grid of cells with slope/erosion risk and frost pockets | Field risk map |
| `sources` | Data sources cited | Footnotes |

---

## 2. `POST /rotations/compare`

Replays the current rotation and the alternatives through every past year and scores them.

**Request**
```json
{
  "lat": 42.03,
  "lon": -93.63,
  "soil": { "clay_pct": 28, "sand_pct": 30, "organic_carbon_pct": 2.4, "ph": 6.4 },
  "current_rotation": ["corn", "soybean"],
  "priorities": { "water": 0.8, "soil_health": 0.6, "profit": 0.7, "erosion": 0.5 },
  "constraints": { "irrigation": false, "hay_equipment": false }
}
```
- `soil`: whatever the farmer confirmed or corrected. Missing keys or `null` = "I don't know" (backend uses SoilGrids).
- `current_rotation`: crop ids in order, one per year (ids from `GET /crops`).
- `priorities`: 0 to 1 slider values.
- `constraints`: options that don't fit are removed.

**Response:** see `backend/sample_responses/rotations_compare.json`

Each item in `rotations`:

| Key | What it is |
|---|---|
| `id`, `name`, `is_current` | `is_current: true` for the farmer's rotation (always included) |
| `sequence` | One entry per rotation year: main crop + optional cover crop |
| `scores` | 0–100 per category + `overall` (weighted by the farmer's priorities) |
| `replay` | One entry per past year: `ok` / `stress` / `fail` + water stress % |
| `replay_summary` | Ready-to-show sentence, e.g. "Water stress in 4 of 21 years" |
| `bare_months` | Months with no crop cover (compare to `heavy_rain_months`) |
| `explanation.why` | Why this rotation was suggested |
| `explanation.evidence` | Claims with the number and source behind each |
| `explanation.benefits` | Benefits |
| `explanation.data_gaps` | What we don't know |
| `explanation.risks_for_local_review` | What a local expert should check |

---

## 3. `POST /journal/clues`

The Farm Journal is stored in the browser (localStorage). The frontend sends the entries and gets clues back; nothing is stored on the server.

**Request**
```json
{
  "soil": { "ph": 7.6 },
  "entries": [
    { "year": 2023, "crop": "blueberry", "variety": "Duke", "outcome": "failed", "notes": "Yellow leaves" },
    { "year": 2024, "crop": "potato", "variety": "", "outcome": "failed", "notes": "" },
    { "year": 2024, "crop": "corn", "variety": "Pioneer P1197", "outcome": "good", "notes": "" }
  ]
}
```
`outcome`: `good` | `ok` | `failed`

**Response:** see `backend/sample_responses/journal_clues.json`

---

## 4. `GET /crops`

The crop list, for dropdowns and the Crop Guide. See `backend/sample_responses/crops.json`.
