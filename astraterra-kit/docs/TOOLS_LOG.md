# Tools & Resources Log

Required for submission. Add a row whenever you use a new tool, dataset, or AI assistant.

## AI / dev tools
| Tool | Used by | Used for |
|---|---|---|
| Cursor IDE | Alex | Coding, refactors, agent rules (`.cursor/rules/`) |
| Claude (Anthropic) | Alex, Elaa | Planning, code review, debugging, documentation drafts |
| GitHub | Team | Repo, PRs, issues |

## Datasets & APIs
| Source | Provider | What we use it for | Notes |
|---|---|---|---|
| NASA POWER (agriculture community) | NASA | Temperature, rainfall, evaporation, soil wetness, frost days, 1981-present | Soil wetness is MERRA-2 model output |
| MODIS NDVI (ORNL DAAC) | NASA | Vegetation greenness, bare-field detection | 250 m, 16-day |
| SRTM 30 m via OpenTopoData | NASA | Slope and low spots | 100 points/call, 1 call/sec |
| SoilGrids | ISRIC | Clay, sand, organic carbon, pH defaults | Not NASA; farmer can override |
| FAOSTAT | FAO | Country crop and price context | Stretch goal |
| FAO-56 / FAO-33 | FAO | Crop water-use formulas | Methodology |

## Libraries
Add Python/JS packages here as they are introduced.

## Future work (not implemented)
SMAP, GRACE-FO, ECOSTRESS, GPM, TEMPO. Require Earthdata login or heavy file processing.
