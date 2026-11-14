# ASTRATERRA Build Plan (read before coding)

## What we are building
A web app where a farmer picks a field on a map, sets priorities (water, soil health, profit, forage) and constraints (irrigation, hay equipment), and sees the current rotation compared with 3+ alternatives. Each rotation explains: why, evidence, benefits, data gaps, risks for local review. It supports farmer judgment and never replaces it.

## How the pieces connect
Browser (frontend/) -> POST /api/analyze -> backend (backend/, FastAPI, Python) -> JSON matching docs/api-contract.sample.json -> frontend feature modules each render one slice of that JSON.
Until the backend exists, the frontend reads frontend/public/sample.json (USE_MOCK = true in frontend/src/api.js). frontend/public/sample.json must always be an exact copy of docs/api-contract.sample.json.

## What exists today
- frontend/ works on mock data: features field-map, bare-calendar, rotation-compare.
- docs/api-contract.sample.json (v0.2, a proposal; the backend owner may replace it).
- data/crops/crops.template.csv (header plus 8 crop ids, mostly empty).
## What does NOT exist yet
backend/, data/cache/, data/crops/crops.csv, backend scoring code. Rules mention these as future targets. Never assume they exist. Create them only when a step below says so.

## Rules for every step
1. Do one step at a time. Small commits.
2. Run the step's Verify command. If it fails, fix it before moving on.
3. docs/api-contract.sample.json is the source of truth. If code and contract disagree, ask the user.
4. Scores come from deterministic code. Never from an LLM.
5. Every claim shown to a farmer needs an entry in the response "evidence" array.
6. Do not add dependencies without saying why.

## Steps (owner in brackets)
Step 1 [Elaa] Contract freeze. Agree the final JSON shape. 
