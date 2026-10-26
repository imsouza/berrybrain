---
id: sciref-usfiscaldata-api-basics
name: "Scientific Ref: API Basics — U.S. Treasury Fiscal Data"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (usfiscaldata): API Basics — U.S. Treasury Fiscal Data"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "usfiscaldata api basics"
  - "api basics — u.s. treasury fiscal data"
keywords:
  - "usfiscaldata"
  - "api"
  - "basics"
  - "specialized"
  - "scientific"
  - "reference"
  - "treasury"
---

# API Basics — U.S. Treasury Fiscal Data

## Overview

- RESTful API — accepts HTTP GET requests only
- Returns JSON by default (also CSV, XML)
- No API key, no authentication, no registration required
- Open data, free for commercial and non-commercial use
- Current versions: v1 and v2 (check each dataset's page for which version applies)

## URL Structure

```
BASE URL + ENDPOINT + PARAMETERS

Base URL:  https://api.fiscaldata.treasury.gov/services/api/fiscal_service
Endpoint:  /v2/accounting/od/debt_to_penny
Params:    ?fields=record_date,tot_pub_debt_out_amt&sort=-record_date&page[size]=5

Full URL:
https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/debt_to_penny?fields=record_date,tot_pub_debt_out_amt&sort=-record_date&page[size]=5
```

- Endpoint components use lowercase + underscores
- Endpoint names are singular

## API Versioning

- **v1**: Earlier datasets (DTS, MTS, some debt tables)
- **v2**: Newer or updated datasets (Debt to Penny, TROR, avg interest rates)
- Check the specific dataset page at `fiscaldata.treasury.gov/datasets/` to confirm the version

## Verifying Endpoint Paths

Endpoint paths change when datasets are restructured. Always confirm the current path on the dataset's **API Quick Guide** before querying.

Authoritative sources (in order):

1. Dataset detail page at `https://fiscaldata.treasury.gov/datasets/{slug}/`
2. Site implementation fallback (not a stable API contract): Gatsby page data: `https://fiscaldata.treasury.gov/page-data/datasets/{slug}/page-data.json` (look for `"endpoint"` fields)
3. [API endpoint table](https://fiscaldata.treasury.gov/api-documentation/#list-of-endpoints-table)

## Data Types

All data-row values in responses are **strings** (quoted), regardless of their logical type.

| Logical Type | dataTypes value | Example value | How to convert |
|---|---|---|---|
| String | `STRING` | `"Canada-Dollar"` | No conversion needed |
| Number | `NUMBER` | `"36123456789012.34"` | `Decimal(value)` for exact amounts; `float(value)` for plots |
| Date | `DATE` | `"2024-03-31"` | `pd.to_datetime(value)` |
| Currency | `CURRENCY` or precision variants (`CURRENCY0`, `CURRENCY3`, etc.) | `"1234567.89"` | `Decimal(value)` for exact amounts; `float(value)` for plots |
| Integer | `INTEGER` | `"42"` | `int(value)` |
| Percentage | `PERCENTAGE` | `"4.25"` | `Decimal(value)` for exact amounts; `float(value)` for plots |

**Null values** appear as the string `"null"` (not Python `None` or JSON `null`).

```python
# Safe numeric conversion handling nulls
def safe_float(val):
    return float(val) if val and val != "null" else None
```

## HTTP Methods

- **Only GET is supported**
- The documented data interface is read-only GET; do not assume a particular error code for unsupported methods.

## Reliability and caching

Use an explicit request timeout and check HTTP status before parsing JSON. No fixed
request quota is published in the reviewed guide. Respect `Retry-After` on HTTP 429
and use bounded retries for transient 5xx responses; do not retry invalid filters.
Save the query, retrieval timestamp, metadata and raw response for reproducibility.
Historical series can be revised, so cached results need an explicit retrieval date.

## Pagination Headers

Responses include pagination in two places:

- **`links` object** in the JSON body (`self`, `first`, `prev`, `next`, `last`)
- **`Link` HTTP header** with RFC 5988 relations (`rel="first"`, `rel="next"`, etc.)

JSON links may be `&page...` fragments, not complete URLs. Preserve the original endpoint, filters, fields and sort while changing the page number; do not replace the query with the fragment. See [response-format.md](response-format.md) for details.

## Data Registry

The [Fiscal Service Data Registry](https://fiscal.treasury.gov/data-registry/index.html) contains field definitions, authoritative sources, data types, and formats across federal government data.

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

