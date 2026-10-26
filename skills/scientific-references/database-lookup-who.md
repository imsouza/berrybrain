---
id: sciref-database-lookup-who
name: "Scientific Ref: WHO Global Health Observatory (GHO) API Reference"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (database-lookup): WHO Global Health Observatory (GHO) API Reference"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "database lookup"
  - "who global health observatory (gho) api reference"
keywords:
  - "database"
  - "lookup"
  - "specialized"
  - "scientific"
  - "reference"
  - "global"
---

# WHO Global Health Observatory (GHO) API Reference

## Overview
The WHO Global Health Observatory (GHO) OData API provides access to health statistics for 194 WHO member states. It covers over 2000 indicators including life expectancy, disease burden, mortality, immunization coverage, health workforce, air pollution, water/sanitation, and the Sustainable Development Goal (SDG) health indicators.

## Base URL
```
https://ghoapi.azureedge.net/api
```

## Authentication
**No API key required.** The API is fully open and free.

## Rate Limits
- No formal rate limits documented.
- The API is served via Azure CDN and handles moderate loads well.
- Be respectful with automated requests; 1-2 per second recommended.

---

## Key Endpoints

The API follows the OData v4 protocol. Standard OData query parameters work: `$filter`, `$select`, `$orderby`, `$top`, `$skip`, `$count`.

### 1. List All Indicators

```
GET /Indicator
```

**Example:**
```
https://ghoapi.azureedge.net/api/Indicator
```

**Response:**
```json
{
  "@odata.context": "...",
  "value": [
    {
      "IndicatorCode": "WHOSIS_000001",
      "IndicatorName": "Life expectancy at birth (years)",
      "Language": "EN"
    },
    {
      "IndicatorCode": "WHOSIS_000002",
      "IndicatorName": "Healthy life expectancy (HALE) at birth (years)",
      "Language": "EN"
    },
    {
      "IndicatorCode": "WHS4_100",
      "IndicatorName": "Measles (MCV1) immunization coverage among 1-year-olds (%)",
      "Language": "EN"
    }
  ]
}
```

### 2. Get Data for a Specific Indicator

```
GET /{IndicatorCode}
```

**Example (life expectancy at birth):**
```
https://ghoapi.azureedge.net/api/WHOSIS_000001
```

**Response:**
```json
{
  "@odata.context": "...",
  "value": [
    {
      "Id": 12345,
      "IndicatorCode": "WHOSIS_000001",
      "SpatialDim": "USA",
      "SpatialDimType": "COUNTRY",
      "TimeDim": 2019,
      "TimeDimType": "YEAR",
      "Dim1": "SEX_BTSX",
      "Dim1Type": "SEX",
      "Dim2": null,
      "Dim2Type": null,
      "Dim3": null,
      "Dim3Type": null,
      "DataSourceDim": null,
      "Value": "78.5",
      "NumericValue": 78.5,
      "Low": 78.2,
      "High": 78.8,
      "Comments": "",
      "Date": "2024-01-15T00:00:00+00:00",
      "TimeDimensionValue": "2019",
      "TimeDimensionBegin": "2019-01-01T00:00:00+00:00",
      "TimeDimensionEnd": "2019-12-31T00:00:00+00:00"
    }
  ]
}
```

### 3. Filter by Country

Use OData `$filter` to restrict results by country (SpatialDim).

**Example (life expectancy for USA only):**
```
https://ghoapi.azureedge.net/api/WHOSIS_000001?$filter=SpatialDim eq 'USA'
```

**Example (life expectancy for multiple countries):**
```
https://ghoapi.azureedge.net/api/WHOSIS_000001?$filter=SpatialDim eq 'USA' or SpatialDim eq 'GBR' or SpatialDim eq 'JPN'
```

### 4. Filter by Year

**Example (life expectancy in 2019):**
```
https://ghoapi.azureedge.net/api/WHOSIS_000001?$filter=TimeDim eq 2019
```

**Example (life expectancy for USA since 2015):**
```
https://ghoapi.azureedge.net/api/WHOSIS_000001?$filter=SpatialDim eq 'USA' and TimeDim ge 2015
```

### 5. Filter by Sex/Dimension

**Example (life expectancy, both sexes, USA, 2015+):**
```
https://ghoapi.azureedge.net/api/WHOSIS_000001?$filter=SpatialDim eq 'USA' and TimeDim ge 2015 and Dim1 eq 'SEX_BTSX'
```

Dim1 sex values: `SEX_BTSX` (both sexes), `SEX_MLE` (male), `SEX_FMLE` (female).

### 6. Pagination and Limiting

**Example (first 10 results):**
```
https://ghoapi.azureedge.net/api/WHOSIS_000001?$top=10
```

**Example (skip first 100, get next 50):**
```
https://ghoapi.azureedge.net/api/WHOSIS_000001?$top=50&$skip=100
```

### 7. Select Specific Fields

```
https://ghoapi.azureedge.net/api/WHOSIS_000001?$filter=SpatialDim eq 'USA'&$select=SpatialDim,TimeDim,NumericValue,Dim1
```

### 8. Order Results

```
https://ghoapi.azureedge.net/api/WHOSIS_000001?$filter=SpatialDim eq 'USA'&$orderby=TimeDim desc
```

### 9. List Dimension Values

```
GET /DIMENSION/{DimensionType}/DimensionValues
```

**Example (list all countries):**
```
https://ghoapi.azureedge.net/api/DIMENSION/COUNTRY/DimensionValues
```

**Example (list all regions):**
```
https://ghoapi.azureedge.net/api/DIMENSION/REGION/DimensionValues
```

**Example (list sex dimension values):**
```
https://ghoapi.azureedge.net/api/DIMENSION/SEX/DimensionValues
```

---

## Common Indicator Codes

### Life Expectancy & Mortality
| Code | Description |
|------|-------------|
| `WHOSIS_000001` | Life expectancy at birth (years) |
| `WHOSIS_000002` | Healthy life expectancy (HALE) at birth (years) |
| `WHOSIS_000004` | Neonatal mortality rate (per 1000 live births) |
| `MDG_0000000001` | Infant mortality rate (per 1000 live births) |
| `MDG_0000000007` | Under-five mortality rate (per 1000 live births) |
| `MORT_MATERNALNUM` | Number of maternal deaths |
| `MDG_0000000026` | Maternal mortality ratio (per 100000 live births) |
| `NCDMORT3070` | Probability of dying from NCDs between ages 30-70 |
| `LIFE_0000000029` | Adult mortality rate (probability of dying 15-60) |

### Communicable Diseases
| Code | Description |
|------|-------------|
| `WHS3_49` | HIV prevalence (% of population ages 15-49) |
| `MDG_0000000029` | Tuberculosis incidence (per 100,000) |
| `MALARIA_EST_INCIDENCE` | Malaria incidence (per 1000 population at risk) |
| `WHS3_62` | New HIV infections (per 1000 uninfected population) |

### Immunization
| Code | Description |
|------|-------------|
| `WHS4_100` | Measles (MCV1) immunization (% of 1-year-olds) |
| `WHS4_117` | DTP3 immunization (% of 1-year-olds) |
| `WHS4_129` | Hepatitis B (HepB3) immunization (%) |
| `WHS4_543` | Polio (Pol3) immunization (% of 1-year-olds) |

### Non-Communicable Diseases & Risk Factors
| Code | Description |
|------|-------------|
| `NCD_BMI_30A` | Prevalence of obesity (BMI >= 30), age-standardized |
| `NCD_HYP_PREVALENCE_A` | Prevalence of raised blood pressure |
| `NCD_GLUC_04` | Prevalence of diabetes (% of population) |
| `M_Est_smk_curr_std` | Prevalence of current tobacco smoking |
| `SA_0000001462` | Total alcohol per capita consumption (litres) |

### Health Systems
| Code | Description |
|------|-------------|
| `HWF_0001` | Medical doctors (per 10,000 population) |
| `HWF_0006` | Nursing and midwifery personnel (per 10,000) |
| `WHS7_104` | Hospital beds (per 10,000 population) |
| `GHED_CHE_pc_US_SHA2011` | Current health expenditure per capita (USD) |
| `UHC_INDEX_REPORTED` | UHC service coverage index |

##

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

