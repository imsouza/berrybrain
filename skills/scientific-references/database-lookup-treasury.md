---
id: sciref-database-lookup-treasury
name: "Scientific Ref: US Treasury Fiscal Data API Reference"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (database-lookup): US Treasury Fiscal Data API Reference"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "database lookup treasury"
  - "us treasury fiscal data api reference"
keywords:
  - "database"
  - "lookup"
  - "treasury"
  - "specialized"
  - "scientific"
  - "reference"
---

# US Treasury Fiscal Data API Reference

## Overview
The US Treasury's Fiscal Data API provides machine-readable access to federal financial data: national debt, treasury securities, interest rates, yield curves, revenue, spending, and more. Maintained by the Bureau of the Fiscal Service.

## Base URL
```
https://api.fiscaldata.treasury.gov/services/api/fiscal_service
```

## Authentication
**No API key required.** The API is fully open and public.

## Rate Limits
- **No formal rate limits published.**
- Reasonable use expected; no authentication or throttling documented.
- For bulk data, use pagination with large page sizes.

---

## Key Endpoints

### URL Pattern
All dataset endpoints follow:
```
GET /services/api/fiscal_service/{endpoint}?{parameters}
```

### Common Query Parameters (apply to all endpoints)
| Parameter | Type | Description |
|-----------|------|-------------|
| `fields` | string | Comma-separated list of fields to return |
| `filter` | string | Filter expression: `field:operator:value` (e.g., `record_date:gte:2024-01-01`) |
| `sort` | string | Sort fields: `field` (asc) or `-field` (desc); comma-separated |
| `page[number]` | int | Page number (default 1) |
| `page[size]` | int | Results per page (default 100, max 10000) |
| `format` | string | `json` (default), `csv`, or `xml` |

**Filter Operators:**
`eq` (equals), `lt`, `lte`, `gt`, `gte`, `in` (comma-separated values)

---

### 1. Average interest rates on Treasury securities

`GET /v2/accounting/od/avg_interest_rates` reports average interest rates on
outstanding securities. It is not the daily par yield curve. Exchange-rate
records at `/v1/accounting/od/rates_of_exchange` are also a different dataset.

Daily Treasury yield curves are provided by the separate
[Treasury XML feeds](https://home.treasury.gov/treasury-daily-interest-rate-xml-feed).
Select the par-yield dataset and year from that documentation; preserve maturity,
date and yield definition rather than substituting average debt interest rates.

**Example -- Average interest rates on Treasury securities:**
```
https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/avg_interest_rates?filter=record_date:gte:2024-01-01&sort=-record_date&page[size]=100
```

**Response:**
```json
{
  "data": [
    {
      "record_date": "2024-10-31",
      "security_type_desc": "Marketable",
      "security_desc": "Treasury Bills",
      "avg_interest_rate_amt": "5.223",
      "src_line_nbr": "1",
      "record_fiscal_year": "2025",
      "record_fiscal_quarter": "1",
      "record_calendar_year": "2024",
      "record_calendar_quarter": "4",
      "record_calendar_month": "10",
      "record_calendar_day": "31"
    }
  ],
  "meta": {
    "count": 100,
    "labels": { ... },
    "dataTypes": { ... },
    "dataFormats": { ... },
    "total-count": 1234,
    "total-pages": 13
  },
  "links": {
    "self": "&page%5Bnumber%5D=1&page%5Bsize%5D=100",
    "first": "&page%5Bnumber%5D=1&page%5Bsize%5D=100",
    "prev": null,
    "next": "&page%5Bnumber%5D=2&page%5Bsize%5D=100",
    "last": "&page%5Bnumber%5D=13&page%5Bsize%5D=100"
  }
}
```

---

### 2. Debt to the Penny (Daily National Debt)
```
GET /v2/accounting/od/debt_to_penny
```

**Example -- Debt since 2024:**
```
https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/debt_to_penny?filter=record_date:gte:2024-01-01&sort=-record_date&page[size]=10
```

**Key Fields:** `record_date`, `tot_pub_debt_out_amt`, `intragov_hold_amt`, `debt_held_public_amt`

---

### 3. Treasury Securities Auctions
```
GET /v1/accounting/od/auctions_query
```

**Example -- Recent T-Bill auctions:**
```
https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/od/auctions_query?filter=security_type:eq:Bill&sort=-auction_date&page[size]=10
```

**Key Fields:** `cusip`, `security_type`, `security_term`, `auction_date`, `issue_date`, `maturity_date`, `high_yield`, `high_discount_rate`, `bid_to_cover_ratio`, `total_accepted`

---

### 4. Monthly Treasury Statement (Outlays)
```
GET /v1/accounting/mts/mts_table_5
```

**Example -- Federal outlays:**
```
https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/mts/mts_table_5?filter=record_date:gte:2024-01-01&sort=-record_date&page[size]=50
```

---

### 5. Receipts by Source and Outlays by Function
```
GET /v1/accounting/mts/mts_table_9
```

**Example:**
```
https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/mts/mts_table_9?filter=record_date:gte:2024-01-01&sort=-record_date
```

---

### 6. Treasury Reporting Rates of Exchange
```
GET /v1/accounting/od/rates_of_exchange
```

**Example -- Exchange rates for a quarter:**
```
https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/od/rates_of_exchange?filter=record_date:eq:2024-09-30&page[size]=200
```

**Key Fields:** `country_currency_desc`, `exchange_rate`, `record_date`, `effective_date`

---

### 7. Interest Expense on the Debt
```
GET /v2/accounting/od/interest_expense
```

**Example:**
```
https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/interest_expense?filter=record_fiscal_year:eq:2024&sort=-record_date
```

---

### 8. Other datasets

Discover savings-bond and financial-statement endpoints in the current Fiscal
Data catalogue; their names do not imply interchangeable rate or value series.
Avoid undocumented guessed paths.

## Common Endpoint Paths

| Endpoint | Description |
|----------|-------------|
| `v2/accounting/od/debt_to_penny` | Daily total public debt outstanding |
| `v2/accounting/od/avg_interest_rates` | Average interest rates on Treasury securities |
| `v1/accounting/od/auctions_query` | Treasury securities auction results |
| `v1/accounting/od/rates_of_exchange` | Treasury reporting rates of exchange |
| `v2/accounting/od/interest_expense` | Interest expense on the public debt |
| `v1/accounting/mts/mts_table_5` | Outlays of the U.S. Government |
| `v1/accounting/mts/mts_table_9` | Summary of receipts by source and outlays by function |
| `v2/accounting/od/debt_outstanding` | Historical debt outstanding (annual) |

## Response Format
All JSON responses share the same envelope:
- `data`: Array of result objects
- `meta`: Contains `count`, `total-count`, `total-pages`, field labels and data types
- `links`: Pagination links (`self`, `first`, `prev`, `next`, `last`)

## Notes
- All monetary amounts are returned as strings to preserve precision.
- Confirm uni

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

