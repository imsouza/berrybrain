---
id: sciref-database-lookup-usgs
name: "Scientific Ref: USGS API Reference (Earthquake Hazards + Water Services)"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (database-lookup): USGS API Reference (Earthquake Hazards + Water Services)"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "database lookup usgs"
  - "usgs api reference (earthquake hazards + water services)"
keywords:
  - "database"
  - "lookup"
  - "usgs"
  - "specialized"
  - "scientific"
  - "reference"
---

# USGS API Reference (Earthquake Hazards + Water Services)

## Part A: Earthquake Hazards Program

### Water Services migration

USGS announces that WaterServices will be decommissioned in early 2027. The NWIS
examples below target the legacy service. For new water-data applications, use
https://api.waterdata.usgs.gov and its documented collections; do not translate
NWIS query parameters mechanically. Earthquake APIs have a separate lifecycle.
Source: https://waterservices.usgs.gov/

## Base URL
```
https://earthquake.usgs.gov/fdsnws/event/1
```

### Authentication
**None required.** Fully public, no API key needed.

### Rate Limits
- No documented per-user rate limit, but USGS asks users to limit automated queries to avoid overloading the service.
- Requests returning very large result sets (>20,000 events) will be rejected. Use pagination or narrow your query.

### Key Endpoints

#### 1. Query Earthquakes
```
GET /query
```
Returns earthquake events matching search criteria. This is the primary endpoint.

**Parameters:**
| Parameter     | Type   | Required | Default    | Description |
|--------------|--------|----------|------------|-------------|
| `format`     | string | No       | `quakeml`  | `geojson`, `csv`, `quakeml`, `text`, `kml`. Use `geojson` for JSON. |
| `starttime`  | string | No       | (now - 30d)| ISO8601 date, e.g. `2024-01-01`. |
| `endtime`    | string | No       | (now)      | ISO8601 date. |
| `minmagnitude`| float | No       | -          | Minimum magnitude (e.g. `4.5`). |
| `maxmagnitude`| float | No       | -          | Maximum magnitude. |
| `mindepth`   | float  | No       | -          | Minimum depth in km. |
| `maxdepth`   | float  | No       | -          | Maximum depth in km. |
| `latitude`   | float  | No       | -          | Center latitude for circle search (-90 to 90). |
| `longitude`  | float  | No       | -          | Center longitude for circle search (-180 to 180). |
| `maxradiuskm`| float  | No       | -          | Max radius in km (with lat/lon). |
| `minlatitude`| float  | No       | -          | Bounding box south edge. |
| `maxlatitude`| float  | No       | -          | Bounding box north edge. |
| `minlongitude`| float | No       | -          | Bounding box west edge. |
| `maxlongitude`| float | No       | -          | Bounding box east edge. |
| `limit`      | int    | No       | -          | Max events returned (max 20000). |
| `offset`     | int    | No       | 1          | Pagination offset (1-based). |
| `orderby`    | string | No       | `time`     | `time`, `time-asc`, `magnitude`, `magnitude-asc`. |
| `alertlevel` | string | No       | -          | PAGER alert: `green`, `yellow`, `orange`, `red`. |
| `eventtype`  | string | No       | -          | e.g. `earthquake`, `quarry blast`. |

**Example -- significant earthquakes in a region:**
```
https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime=2024-01-01&endtime=2024-12-31&minmagnitude=5.0&minlatitude=30&maxlatitude=45&minlongitude=-125&maxlongitude=-110&orderby=magnitude
```

**GeoJSON Response:**
```json
{
  "type": "FeatureCollection",
  "metadata": {
    "generated": 1700000000000,
    "url": "https://earthquake.usgs.gov/fdsnws/event/1/query?...",
    "title": "USGS Earthquakes",
    "status": 200,
    "api": "1.14.1",
    "count": 42
  },
  "features": [
    {
      "type": "Feature",
      "properties": {
        "mag": 6.2,
        "place": "15 km NNE of Ridgecrest, CA",
        "time": 1700000000000,
        "updated": 1700100000000,
        "tz": null,
        "url": "https://earthquake.usgs.gov/earthquakes/eventpage/ci00000001",
        "detail": "https://earthquake.usgs.gov/fdsnws/event/1/query?eventid=ci00000001&format=geojson",
        "felt": 1500,
        "cdi": 7.1,
        "mmi": 6.5,
        "alert": "yellow",
        "status": "reviewed",
        "tsunami": 0,
        "sig": 800,
        "net": "ci",
        "code": "00000001",
        "type": "earthquake",
        "title": "M 6.2 - 15 km NNE of Ridgecrest, CA"
      },
      "geometry": {
        "type": "Point",
        "coordinates": [-117.5, 35.8, 10.5]
      },
      "id": "ci00000001"
    }
  ]
}
```
Note: `geometry.coordinates` is `[longitude, latitude, depth_km]`.

#### 2. Event Detail
```
GET /query?eventid={EVENTID}&format=geojson
```
Returns detailed info for a single event, including moment tensor, focal mechanism, and nearby cities.

#### 3. Event Count
```
GET /count
```
Same parameters as `/query`, returns just the count of matching events. Useful for checking result size before querying.

**Example:**
```
https://earthquake.usgs.gov/fdsnws/event/1/count?starttime=2024-01-01&endtime=2024-12-31&minmagnitude=4.5
```

#### 4. Real-Time Feeds (no parameters)
Pre-built GeoJSON feeds updated every minute/5 min/15 min/hour:
```
https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/significant_month.geojson
https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_week.geojson
https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_day.geojson
https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson
```
Pattern: `{significance}_{timeperiod}.geojson` where significance is `significant`, `4.5`, `2.5`, `1.0`, `all` and timeperiod is `hour`, `day`, `week`, `month`.

---

## Part B: Water Services

### Base URL
```
https://waterservices.usgs.gov/nwis
```

### Authentication
**None required.** Fully public, no API key needed.

### Rate Limits
- No strict per-user limit, but USGS recommends limiting automated requests. Large queries may time out.

### Key Endpoints

#### 1. Instantaneous Values (Real-Time Data)
```
GET /iv/
```
Returns the most recent sensor readings (typically 15-minute intervals).

**Parameters:**
| Parameter       | Type   | Required | Default | Description |
|----------------|--------|----------|---------|-------------|
| `format`       | string | No       | `wml`   | `json`, `xml`, `wml,1.1`, `wml,2.0`, `rdb`. Use `json` for JSON. |
| `sites`        | string | Cond.    | -       | Comma-separated USGS site numbers (e.g. `01646500`). |
| `stateCd`      | string | Cond.    | -       | 2-letter state code (e.g. `NY`). |
| `huc`          | string | Cond.    | -       | Hydrologic Unit Code(s). |
| `bBox`         | string | Cond.    | -       | Bounding box: `west,south,east,north` (decimal degrees). |
| `countyCd`     | string | Cond.    | -       | 5-digit FIPS county code(s). |
| `parameterCd`  | string | No       | `00060` | Parameter

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

