# Screens (guided flow)

The app is a guided flow, not one long page. Screens, in order:

| screen id | What the farmer does | Features on it |
|---|---|---|
| `welcome` | Names the farm (saved in localStorage; "Welcome back, X" next visit) | built into `core/Flow.jsx` |
| `field` | Searches or clicks the map | `location-search`, `field-map` |
| `survey` | Soil (blank = "I don't know") and current crops | `farm-survey` |
| `goals` | Priorities sliders and equipment checkboxes | `goals` |
| `report` | Reads the result | `report-summary`, `climate-chart`, `bare-calendar`, `rotation-compare` |
| `journal` | Farm Journal tab (appears only if a feature uses it) | (Elaa's journal feature) |

## Putting your feature on a screen
Add `screen` to your feature's export:

```js
export default { id: "farm-journal", title: "Farm journal", order: 10, screen: "journal", Component: FarmJournal };
```

- No `screen` means the feature appears on the **report**.
- Inside a screen, features are sorted by `order` (lower first).
- A feature with `title: ""` shows no heading (the card just holds the content).
- To move the farmer to another screen, `const { go } = useFlow()` (from `core/flowContext.js`) then `go("goals")`.

## Shared state (`useApp()`)
`data` (backend response), `field` + `setField`, `priorities`, `constraints`, `survey` + `setSurvey`, `loading`, `slow`, `error`.

Request body sent to `POST /api/analyze`:
`{ lat, lon, name, priorities, constraints, soil_overrides: {clay_pct, sand_pct, organic_carbon_pct, ph}, current_rotation: [crop ids] }`.
A `null` soil value means the farmer answered "I don't know".

## Saved in the browser
`core/storage.js` saves `farmName`, last `screen`, map pin, priorities, equipment, and survey answers under the key `astraterra.v1`.
