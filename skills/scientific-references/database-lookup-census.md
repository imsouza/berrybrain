---
id: sciref-database-lookup-census
name: "Scientific Ref: US Census Bureau API Reference"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (database-lookup): US Census Bureau API Reference"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "database lookup census"
  - "us census bureau api reference"
keywords:
  - "database"
  - "lookup"
  - "census"
  - "specialized"
  - "scientific"
  - "reference"
---

# US Census Bureau API Reference

## Overview
The US Census Bureau API provides access to hundreds of datasets including the American Community Survey (ACS), Decennial Census, Economic Census, Population Estimates, and more. It is the primary source for US demographic, social, economic, and housing data.

## Base URL
```
https://api.census.gov/data
```

## Authentication
- **API key optional for up to 500 queries per IP per day; required above that allowance (free).** Register at https://api.census.gov/data/key_signup.html
- Pass as query parameter: `&key=YOUR_KEY`
- Requests without a key are throttled to ~500/day. With a key, limits are much higher.

## Rate Limits
- Without key: approximately 500 requests per day.
- Use a key when exceeding the anonymous 500-query daily allowance; do not infer an unlimited service guarantee.
- No formal per-minute rate limit documented; keep automated requests to a few per second.

---

## Key Datasets and URL Patterns

The general URL pattern is:
```
https://api.census.gov/data/{year}/{dataset}?get={variables}&for={geography}&key=YOUR_KEY
```

### Major Dataset Paths

| Dataset | Path Segment | Description |
|---------|-------------|-------------|
| ACS 5-Year Detailed Tables | `acs/acs5` | 5-year estimates, most geographies (2009-present) |
| ACS 1-Year Detailed Tables | `acs/acs1` | 1-year estimates, areas 65k+ pop (2005-present) |
| ACS 5-Year Subject Tables | `acs/acs5/subject` | Precomputed subject tables |
| ACS 5-Year Data Profiles | `acs/acs5/profile` | Social/economic/housing profiles |
| Decennial Census (2020) | `dec/dhc` | Demographic and Housing Characteristics |
| Decennial Census (2020 PL) | `dec/pl` | Redistricting data (PL 94-171) |
| Decennial Census (2010) | `dec/sf1` | Summary File 1 |
| Population Estimates | `pep/population` | Annual population estimates |
| Economic Census | `ecnbasic` | Economic Census (2017, 2022) |
| County Business Patterns | `cbp` | Business establishment counts |
| Annual Business Survey | `abscs` | Business characteristics |

---

## Key Endpoints

### 1. ACS 5-Year Estimates (Most Common)

```
GET /data/{year}/acs/acs5?get={variables}&for={geography}&key=YOUR_KEY
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `get`     | Yes      | Comma-separated variable names (e.g., `NAME,B01001_001E`) |
| `for`     | Yes      | Target geography (e.g., `state:*`, `county:*`, `tract:*`) |
| `in`      | Sometimes | Parent geography for sub-state levels |
| `key`     | For higher volume | Your API key |

**Example (total population for all states, 2022 ACS 5-year):**
```
https://api.census.gov/data/2022/acs/acs5?get=NAME,B01001_001E&for=state:*&key=YOUR_KEY
```

**Example (median household income for all counties in California):**
```
https://api.census.gov/data/2022/acs/acs5?get=NAME,B19013_001E&for=county:*&in=state:06&key=YOUR_KEY
```

**Example (population by race for a specific tract):**
```
https://api.census.gov/data/2022/acs/acs5?get=NAME,B02001_001E,B02001_002E,B02001_003E&for=tract:000100&in=state:06&in=county:075&key=YOUR_KEY
```

**Response (JSON array of arrays, first row is headers):**
```json
[
  ["NAME", "B01001_001E", "state"],
  ["Alabama", "5024279", "01"],
  ["Alaska", "733391", "02"],
  ["Arizona", "7151502", "04"]
]
```

### 2. ACS 1-Year Estimates

```
GET /data/{year}/acs/acs1?get={variables}&for={geography}&key=YOUR_KEY
```
Same parameters as ACS 5-year. Only available for geographies with 65,000+ population.

**Example (poverty rate for all states):**
```
https://api.census.gov/data/2022/acs/acs1?get=NAME,B17001_001E,B17001_002E&for=state:*&key=YOUR_KEY
```

### 3. ACS Data Profiles

```
GET /data/{year}/acs/acs5/profile?get={variables}&for={geography}&key=YOUR_KEY
```
Uses `DP` prefix variables with precomputed percentages.

**Example (educational attainment profile):**
```
https://api.census.gov/data/2022/acs/acs5/profile?get=NAME,DP02_0068PE&for=state:*&key=YOUR_KEY
```

### 4. Decennial Census 2020

```
GET /data/2020/dec/dhc?get={variables}&for={geography}&key=YOUR_KEY
```

**Example (total population by state, 2020 Census):**
```
https://api.census.gov/data/2020/dec/dhc?get=NAME,P1_001N&for=state:*&key=YOUR_KEY
```

### 5. Decennial Census 2010

```
GET /data/2010/dec/sf1?get={variables}&for={geography}&key=YOUR_KEY
```

**Example:**
```
https://api.census.gov/data/2010/dec/sf1?get=NAME,P001001&for=state:*&key=YOUR_KEY
```

### 6. Discover Available Variables

```
GET /data/{year}/{dataset}/variables.json
```

**Example:**
```
https://api.census.gov/data/2022/acs/acs5/variables.json
```
Returns a large JSON object listing all available variables with labels and concepts.

### 7. Discover Available Geographies

```
GET /data/{year}/{dataset}/geography.json
```

**Example:**
```
https://api.census.gov/data/2022/acs/acs5/geography.json
```

### 8. List Available Datasets

```
GET /data.json
```

Returns all available datasets with their titles, years, and API endpoints.

---

## Geography Syntax

| Level | `for` syntax | `in` requirement |
|-------|-------------|-----------------|
| Nation | `us:1` or `us:*` | None |
| State | `state:06` or `state:*` | None |
| County | `county:075` or `county:*` | `in=state:06` (optional for all) |
| County Subdivision | `county subdivision:*` | `in=state:XX&in=county:YYY` |
| Census Tract | `tract:*` | `in=state:XX&in=county:YYY` |
| Block Group | `block group:*` | `in=state:XX&in=county:YYY&in=tract:ZZZZZZ` |
| Place (city) | `place:*` | `in=state:XX` |
| Metro Area (CBSA) | `metropolitan statistical area/micropolitan statistical area:*` | None |
| ZIP Code Tab Area | `zip code tabulation area:*` | None |

State FIPS codes: `01`=AL, `02`=AK, `04`=AZ, `05`=AR, `06`=CA, `08`=CO, `09`=CT, `10`=DE, `11`=DC, `12`=FL, `13`=GA, `15`=HI, `16`=ID, `17`=IL, `18`=IN, `19`=IA, `20`=KS, `21`=KY, `22`=LA, `23`=ME, `24`=MD, `25`=MA, `26`=MI, `27`=MN, `28`=MS, `29`=MO, `30`=MT, `31`=NE, `32`=NV, `33`=NH, `34`=NJ, `35`=NM, `36`=NY, `37`=NC, `38`=ND, `39`=OH, `40`=OK, `41`=OR, `42`=PA, `44`=RI, `45`=SC, `46`=SD, `47`=TN, `48`=TX, `49`=UT, `50`=VT, `51`=VA, `53`=WA, `54`=WV, `55`=WI, `56`=WY

---

## Common Variable Codes

### ACS Detailed Tables (B-tables)
| Variable | Description |
|----------|-------------|
| `B01001_001E` | Total population |
| `B01002_001E` | Median age |
| `B02001_001E` | Total (race) |
| `B02001_002E` | White alone |
| `B02001_003E` | Black or African American alone |
| `B03001_003E` | Hispanic or Latin

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

