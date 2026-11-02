---
id: sciref-database-lookup-bls
name: "Scientific Ref: Bureau of Labor Statistics (BLS) Public Data API"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (database-lookup): Bureau of Labor Statistics (BLS) Public Data API"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "database lookup bls"
  - "bureau of labor statistics (bls) public data api"
keywords:
  - "database"
  - "lookup"
  - "bls"
  - "specialized"
  - "scientific"
  - "reference"
  - "bureau"
---

# Bureau of Labor Statistics (BLS) Public Data API

## Base URL

```
https://api.bls.gov/publicAPI/v2
```

Version 1 (no key): `https://api.bls.gov/publicAPI/v1`

## Authentication

**API key optional but strongly recommended.** Register at https://data.bls.gov/registrationEngine/

- **V1 (no key):** Limited to 25 requests/day, 10-year date range, 25 series per query.
- **V2 (with key):** 500 requests/day, 20-year date range, 50 series per query, plus catalog data and calculations.

## Key Endpoints

### 1. Get Series Data (POST -- primary method)
```
POST /timeseries/data/
```
Content-Type: `application/json`

**Request body:**
```json
{
  "seriesid": ["CUUR0000SA0", "LNS14000000"],
  "startyear": "2020",
  "endyear": "2024",
  "registrationkey": "YOUR_KEY",
  "catalog": true,
  "calculations": true,
  "annualaverage": true,
  "aspects": true
}
```

| Field            | Required | V1  | V2  | Description                                          |
|------------------|----------|-----|-----|------------------------------------------------------|
| seriesid         | Yes      | Yes | Yes | Array of series IDs (max 25 v1 / 50 v2)            |
| startyear        | No       | Yes | Yes | 4-digit start year                                  |
| endyear          | No       | Yes | Yes | 4-digit end year                                    |
| registrationkey  | No       | No  | Yes | API key (required for v2 features)                  |
| catalog          | No       | No  | Yes | `true` to include series metadata                   |
| calculations     | No       | No  | Yes | `true` to include net/pct changes                   |
| annualaverage    | No       | No  | Yes | `true` to include annual averages                   |
| aspects          | No       | No  | Yes | `true` to include footnotes and aspects             |

### 2. Get Single Series Data (GET -- convenience)
```
GET /timeseries/data/{seriesID}
```
Example:
```
https://api.bls.gov/publicAPI/v2/timeseries/data/CUUR0000SA0?registrationkey=YOUR_KEY&startyear=2022&endyear=2024
```

### 3. Latest Data (GET -- no date range)
```
GET /timeseries/data/{seriesID}
```
Without startyear/endyear, returns the most recent 3 years.

Example:
```
https://api.bls.gov/publicAPI/v2/timeseries/data/LNS14000000?registrationkey=YOUR_KEY
```

## Common Series IDs

### Consumer Price Index (CPI)
| Series ID       | Description                                       |
|-----------------|---------------------------------------------------|
| CUUR0000SA0     | CPI-U All Items, US City Avg, Not Seasonally Adj  |
| CUSR0000SA0     | CPI-U All Items, US City Avg, Seasonally Adj      |
| CUUR0000SAF1    | CPI-U Food, US City Avg                           |
| CUUR0000SETB01  | CPI-U Gasoline (all types)                        |
| CUUR0000SAH1    | CPI-U Shelter                                     |
| CUUR0000SAM     | CPI-U Medical Care                                |

CPI series ID structure: `CU` + `U/S` (unadj/adj) + `R/S` (revision) + area code + item code

### Employment / Unemployment (Current Population Survey)
| Series ID       | Description                                       |
|-----------------|---------------------------------------------------|
| LNS14000000     | Unemployment Rate (seasonally adjusted)            |
| LNS11000000     | Civilian Labor Force Level                         |
| LNS12000000     | Employment Level                                   |
| LNS13000000     | Unemployment Level                                 |
| LNS14000006     | Unemployment Rate - Black or African American      |
| LNS14000009     | Unemployment Rate - Hispanic or Latino             |

### Employment (Current Employment Statistics / Nonfarm Payrolls)
| Series ID       | Description                                       |
|-----------------|---------------------------------------------------|
| CES0000000001   | Total Nonfarm Employment (seasonally adj)          |
| CES0500000003   | Average Hourly Earnings, Total Private             |
| CES0500000002   | Average Weekly Hours, Total Private                |

### Producer Price Index (PPI)
| Series ID       | Description                                       |
|-----------------|---------------------------------------------------|
| WPSFD4          | PPI Final Demand                                  |
| WPUFD49104      | PPI Final Demand less Foods & Energy              |

### Employment Cost Index (ECI)
| Series ID       | Description                                       |
|-----------------|---------------------------------------------------|
| CIU1010000000000A | ECI Total Compensation, All Civilians           |

### Occupational Employment & Wage Statistics (OEWS)
| Series ID Pattern | Description                                     |
|-------------------|-------------------------------------------------|
| OEUM003342000000011-0000 | Example: specific occupation/area combo  |

OEWS series IDs are complex. Use the BLS Series ID finder: https://data.bls.gov/cgi-bin/srgate

## Series ID Structure

BLS series IDs encode survey, seasonal adjustment, area, industry, and item information. Key survey prefixes:

| Prefix | Survey                                          |
|--------|------------------------------------------------|
| CU     | Consumer Price Index                            |
| LN     | Current Population Survey (Labor Force)         |
| CE     | Current Employment Statistics                   |
| WP     | Producer Price Index                            |
| CI     | Employment Cost Index / National Compensation   |
| OE     | Occupational Employment & Wage Statistics       |
| LA     | Local Area Unemployment Statistics              |
| SM     | State and Metro Area Employment (CES)           |
| JT     | Job Openings and Labor Turnover (JOLTS)         |

## Response Format

### Standard response
```json
{
  "status": "REQUEST_SUCCEEDED",
  "responseTime": 85,
  "message": [],
  "Results": {
    "series": [
      {
        "seriesID": "CUUR0000SA0",
        "catalog": {
          "series_title": "All items in U.S. city average, all urban consumers, not seasonally adjusted",
          "series_id": "CUUR0000SA0",
          "seasonality": "Not Seasonally Adjusted",
          "survey_name": "Consumer Price Index - All Urban Consumers",
          "survey_abbreviation": "CU",
          "measure_data_type": "All items",
          "area": "U.S. city average",
          "item": "All items"
        },


*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

