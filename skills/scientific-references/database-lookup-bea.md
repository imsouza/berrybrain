---
id: sciref-database-lookup-bea
name: "Scientific Ref: BEA (Bureau of Economic Analysis) API Reference"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (database-lookup): BEA (Bureau of Economic Analysis) API Reference"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "database lookup bea"
  - "bea (bureau of economic analysis) api reference"
keywords:
  - "database"
  - "lookup"
  - "bea"
  - "specialized"
  - "scientific"
  - "reference"
  - "bureau"
---

# BEA (Bureau of Economic Analysis) API Reference

## Overview
The Bureau of Economic Analysis API provides access to U.S. economic accounts data including GDP (national income and product accounts -- NIPA), personal income, international trade, industry accounts, and regional economic data. Structured as a single endpoint with dataset-specific parameters.

## Base URL
```
https://apps.bea.gov/api/data
```

## Authentication
- **API Key: REQUIRED.** Register at https://apps.bea.gov/API/signup/
- Pass as query parameter: `&UserID=YOUR_API_KEY`

## Rate Limits
- **100 requests per minute** per API key.
- **100 MB of data per minute** per API key.
- **30 errors per minute** -- exceeding triggers a temporary lockout.
- Daily and monthly limits are not formally published but BEA may throttle heavy use.

## Common Parameters (all requests)
| Parameter  | Type   | Required | Description |
|-----------|--------|----------|-------------|
| `UserID`  | string | Yes      | Your BEA API key. |
| `method`  | string | Yes      | API method (see below). |
| `ResultFormat` | string | No  | `JSON` (default) or `XML`. |

---

## Methods

### 1. GetDataSetList
Lists all available datasets.

#### `GET /api/data?method=GetDataSetList&UserID=YOUR_KEY&ResultFormat=JSON`

**Example:**
```
https://apps.bea.gov/api/data?method=GetDataSetList&UserID=YOUR_KEY&ResultFormat=JSON
```

**Response:**
```json
{
  "BEAAPI": {
    "Request": {
      "RequestParam": [
        {"ParameterName": "METHOD", "ParameterValue": "GETDATASETLIST"},
        {"ParameterName": "RESULTFORMAT", "ParameterValue": "JSON"}
      ]
    },
    "Results": {
      "Dataset": [
        {"DatasetName": "NIPA", "DatasetDescription": "Standard NIPA tables"},
        {"DatasetName": "NIUnderlyingDetail", "DatasetDescription": "National Income and Product Accounts Underlying Detail"},
        {"DatasetName": "MNE", "DatasetDescription": "Multinational Enterprises"},
        {"DatasetName": "FixedAssets", "DatasetDescription": "Fixed Assets"},
        {"DatasetName": "ITA", "DatasetDescription": "International Transactions"},
        {"DatasetName": "IIP", "DatasetDescription": "International Investment Position"},
        {"DatasetName": "GDPbyIndustry", "DatasetDescription": "GDP by Industry"},
        {"DatasetName": "Regional", "DatasetDescription": "Regional data"},
        {"DatasetName": "UnderlyingGDPbyIndustry", "DatasetDescription": "Underlying GDP by Industry"},
        {"DatasetName": "InputOutput", "DatasetDescription": "Input-Output Statistics"}
      ]
    }
  }
}
```

---

### 2. GetParameterList
Lists parameters for a specific dataset.

#### `GET /api/data?method=GetParameterList&DatasetName={dataset}&UserID=YOUR_KEY&ResultFormat=JSON`

**Example:**
```
https://apps.bea.gov/api/data?method=GetParameterList&DatasetName=NIPA&UserID=YOUR_KEY&ResultFormat=JSON
```

**Response:**
```json
{
  "BEAAPI": {
    "Results": {
      "Parameter": [
        {
          "ParameterName": "TableName",
          "ParameterDataType": "string",
          "ParameterDescription": "The standard NIPA table identifier",
          "ParameterIsRequiredFlag": "1",
          "ParameterDefaultValue": ""
        },
        {
          "ParameterName": "Frequency",
          "ParameterDataType": "string",
          "ParameterDescription": "A - Annual, Q - Quarterly, M - Monthly",
          "ParameterIsRequiredFlag": "1",
          "ParameterDefaultValue": ""
        },
        {
          "ParameterName": "Year",
          "ParameterDataType": "string",
          "ParameterDescription": "List of year(s) of data to retrieve",
          "ParameterIsRequiredFlag": "1",
          "ParameterDefaultValue": ""
        }
      ]
    }
  }
}
```

---

### 3. GetParameterValues
Lists valid values for a parameter.

#### `GET /api/data?method=GetParameterValues&DatasetName={dataset}&ParameterName={param}&UserID=YOUR_KEY&ResultFormat=JSON`

**Example (list NIPA tables):**
```
https://apps.bea.gov/api/data?method=GetParameterValues&DatasetName=NIPA&ParameterName=TableName&UserID=YOUR_KEY&ResultFormat=JSON
```

**Response (abbreviated):**
```json
{
  "BEAAPI": {
    "Results": {
      "ParamValue": [
        {"TableName": "T10101", "Description": "Table 1.1.1. Percent Change From Preceding Period in Real Gross Domestic Product"},
        {"TableName": "T10106", "Description": "Table 1.1.6. Real Gross Domestic Product, Chained Dollars"},
        {"TableName": "T10105", "Description": "Table 1.1.5. Gross Domestic Product"},
        {"TableName": "T20100", "Description": "Table 2.1. Personal Income and Its Disposition"},
        {"TableName": "T30100", "Description": "Table 3.1. Government Current Receipts and Expenditures"}
      ]
    }
  }
}
```

---

### 4. GetData
The main data retrieval method. Parameters vary by dataset.

#### `GET /api/data?method=GetData&DatasetName={dataset}&{params}&UserID=YOUR_KEY&ResultFormat=JSON`

---

## Dataset-Specific Parameters & Examples

### A. NIPA (National Income and Product Accounts)

**Parameters:**
| Parameter   | Type   | Required | Description |
|------------|--------|----------|-------------|
| `TableName`| string | Yes      | NIPA table identifier (e.g., `T10101`). |
| `Frequency`| string | Yes      | `A` (annual), `Q` (quarterly), `M` (monthly). |
| `Year`     | string | Yes      | Comma-separated years, or `ALL`/`X` for all years; prefer an explicit bounded range. |

**Example (Real GDP percent change, quarterly, 2022-2024):**
```
https://apps.bea.gov/api/data?method=GetData&DatasetName=NIPA&TableName=T10101&Frequency=Q&Year=2022,2023,2024&UserID=YOUR_KEY&ResultFormat=JSON
```

**Example (GDP levels, annual, all years):**
```
https://apps.bea.gov/api/data?method=GetData&DatasetName=NIPA&TableName=T10105&Frequency=A&Year=ALL&UserID=YOUR_KEY&ResultFormat=JSON
```

**Response:**
```json
{
  "BEAAPI": {
    "Request": { ... },
    "Results": {
      "Statistic": "NIPA Table",
      "UTCProductionTime": "2024-11-01T13:00:00.000",
      "Dimensions": [
        {"Name": "TableName", "DataType": "string", "IsValue": "0"},
        {"Name": "SeriesCode", "DataType": "string", "IsValue": "0"},
        {"Name": "LineNumber", "DataType": "numeric", "IsValue": "0"},
        {"Name": "LineDescription", "DataType": "string", "IsValue": "0"},
        {"Name": "TimePeriod", "DataType": "string", "IsValue": "0"},
        {"Name": "METRIC_NAME", "DataType": "string", "IsValue": "0"},
        {"Name": "CL_UNIT", "DataType": "string", "IsValue":

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

