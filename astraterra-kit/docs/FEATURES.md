# Feature modules

Each feature is a folder in `frontend/src/features/<name>/` with an `index.jsx` that default-exports:

```js
export default { id: "unique-id", title: "Shown heading", order: 50, Component: MyFeature };
```

The registry auto-loads it. No edits to `App.jsx`.

## Rules
1. Read data with `useApp()`. Never import another feature.
2. If you need new data, add it to `docs/api-contract.sample.json` in the same PR.
3. Handle missing data (render an "empty" message, never crash).
4. Each feature is wrapped in an error boundary. A crash hides only that feature.
5. Hide an unfinished feature by adding its id to `frontend/src/features.config.js`.

## Current features
| id | order | Owner | Reads from contract | Status |
|---|---|---|---|---|
| field-map | 10 | Alex | `field`, `risk_zones` | working on mock |
| bare-calendar | 15 | Alex | `bare_field_calendar` | working on mock |
| rotation-compare | 20 | Alex | `rotations`, priorities, constraints | working on mock |

## Planned (claim one in Discord)
| id | Reads | Notes |
|---|---|---|
| soil-questionnaire | `soil` | Auto-fill default, optional home tests |
| farm-journal | localStorage | Rules-based failure clues |
| climate-trends | `climate.trends`, `climate.year_types` | Plain-language trend cards |
| what-if-sliders | request: temp/rain deltas | Nice-to-have |
| crop-guide | crop database | Nice-to-have |

## Scoring note
Sliders re-rank rotations in the browser via `src/core/scoring.js`. The backend remains the source of
truth for the scores themselves. Keep the criteria groups in sync with `backend/rotations/scoring.py`.
