FIRST read README.md and docs/BUILD_PLAN.md. Work on one step at a time and do not create files the plan says do not exist yet.
# ASTRATERRA: Agent Context (read first)

Decision-support tool for NASA Space Apps 2026 "Field Shift". Helps farmers compare crop rotations
(current + 3 or more alternatives) using NASA data plus local soil info and farmer priorities.
It SUPPORTS farmer judgment; it never replaces it.

## Hard constraints
- 2-day hackathon. Prefer the simplest thing that works end to end. No new dependencies without a reason.
- Scores are computed by deterministic rules/formulas. An LLM may reword explanations, NEVER decides scores.
- Every claim shown to a farmer must trace to a real number in the API response (`evidence` array).
- Be honest about data: NASA POWER soil wetness is MERRA-2 model output, not direct satellite observation.
- Every rotation needs: why, evidence, benefits, gaps, risks_for_local_review.

## Stack (update once decided)
- Backend: Python (FastAPI), pandas, scikit-learn (k-means on yearly features)
- Frontend: React + Vite + Leaflet (CONFIRMED). Lives in `frontend/`. Reads `/sample.json` until the backend is up; flip `USE_MOCK` in `frontend/src/api.js`.
- Data: NASA POWER, MODIS NDVI (ORNL DAAC), SRTM via OpenTopoData, SoilGrids, FAOSTAT (stretch)

## Workflow
- Contract: `docs/api-contract.sample.json` is the source of truth. Change it via PR, announce in Discord.
- Branches: `feat/<area>-<name>`. Small PRs, merge to `main` often. Never push broken code to `main`.
- Cache demo-farm API responses in `data/cache/` so the demo never depends on live APIs.
- Log every AI tool/dataset used in `docs/TOOLS_LOG.md` (required for submission).

## Demo farms
1. Iowa corn/soy  2. Kansas wheat  3. One dry-region farm (TBD)
