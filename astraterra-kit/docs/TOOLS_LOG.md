# Tools & Resources Log

Required for submission. Add a row whenever you use a new tool, dataset, or AI assistant.

## AI / dev tools
| Tool | Used by | Used for |
|---|---|---|
| Cursor IDE | Alex | Coding, refactors, agent rules (`.cursor/rules/`) |
| Claude (Anthropic) | Alex, Elaa | Planning, code aid, debugging, documentation drafts, planning |
| GitHub | Team | Repo, PRs, issues |

## Datasets & APIs
| Source | Provider | What we use it for | Notes |
|---|---|---|---|
| NASA POWER (agriculture community) | NASA | Daily temperature, rainfall, solar radiation, humidity, root-zone soil wetness 2005-2025: ET0, water bucket, frost dates, replay | Soil wetness is MERRA-2 model output. Cached per location |
| MODIS NDVI (ORNL DAAC) | NASA | Vegetation greenness, bare-field detection | 250 m, 16-day |
| SRTM 30 m via OpenTopoData | NASA (data), OpenTopoData (API) | Field elevation, slope (erosion zones), low spots (frost pockets) | 81 points in 1 call per field, cached. Public API limits respected: max 100 points/call, 1 call/sec, 1000 calls/day |
| SoilGrids 2.0 REST API | ISRIC | Clay, sand, organic carbon, pH (0-100 cm average) | Not NASA; farmer can override. CC-BY 4.0, credited in app + README. Fair-use API, cached so each field is queried once |
| FAOSTAT | FAO | Country crop and price context | Stretch goal |
| FAO-56 / FAO-33 | FAO | Hargreaves ET0 (eq. 52), crop coefficients Kc (Table 12), 50% stress line | Methodology |
| Saxton & Rawls (2006), SSSAJ 70:1569 | Published paper | Soil texture -> plant-available water per metre | Methodology |
| USDA soil survey slope classes | USDA NRCS | Erosion levels: 5% medium, 9% high | Methodology |

## Libraries
| Package | Used for |
|---|---|
| FastAPI + uvicorn + pydantic | Backend API |
| requests | Calling NASA POWER, SoilGrids, OpenTopoData |
| pandas, numpy | Daily -> monthly climate, water bucket, slope grid |
| scikit-learn, pymannkendall | Year-type clustering, climate trends (Brandon) |

## Data use terms we follow
Non-government sources are allowed if we follow each site's data-use rules:
- **SoilGrids (ISRIC):** CC-BY 4.0, attribution "Soil data: SoilGrids 2.0, ISRIC World Soil Information".
- **OpenTopoData:** public API fair-use limits above; results cached.
- **OpenStreetMap tiles (map background):** attribution shown on the map; light demo use only.
- **NASA POWER / SRTM:** NASA open data; cite "NASA POWER Project" and "NASA SRTM".

## Future work (not implemented)
SMAP, GRACE-FO, ECOSTRESS, GPM, TEMPO. Require Earthdata login or heavy file processing.
