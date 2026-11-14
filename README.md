# ASTRATERRA
Decision-support tool (NASA Space Apps 2026, "Field Shift"). A farmer picks a field, sets priorities, and compares their current crop rotation with 3+ alternatives, using NASA data.

Start here: read AGENTS.md, then docs/BUILD_PLAN.md.

Run the frontend:
    cd frontend
    npm install
    npm run dev

Repo map:
- frontend/ : React + Vite + Leaflet. Feature modules in frontend/src/features/
- docs/ : api-contract.sample.json (source of truth), BUILD_PLAN.md, FEATURES.md, TOOLS_LOG.md
- data/crops/ : crop database (template only so far)
- .cursor/rules/ : agent rules
