---
id: sci-usfiscaldata
name: "Scientific: usfiscaldata"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Queries the U.S. Treasury Fiscal Data REST API for federal financial data. No API key required. Use for national debt (Debt to the Penny), Daily Treasury Statements, Monthly Treasury Statements, Treasury securities auctions, interest rates, foreign exchange rates, savings bonds, "
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "usfiscaldata"
keywords:
  - "usfiscaldata"
  - "queries"
  - "treasury"
  - "fiscal"
  - "rest"
  - "federal"
  - "financial"
---

# U.S. Treasury Fiscal Data API

Free, open REST API from the U.S. Department of the Treasury for federal financial data. No API key or registration required.

**Base URL:** `https://api.fiscaldata.treasury.gov/services/api/fiscal_service`

Browse [the current dataset catalog](https://fiscaldata.treasury.gov/datasets/) via the dataset search. Verify endpoint paths on each dataset's API Quick Guide — paths change over time.

## Installation

```bash
uv pip install requests pandas
```

## Quick Start

```python
import requests
import pandas as pd

BASE_URL = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service"

# Get the current national debt (Debt to the Penny)
resp = requests.get(f"{BASE_URL}/v2/accounting/od/debt_to_penny", params={
    "sort": "-record_date",
    "page[size]": 1
}, timeout=30)
resp.raise_for_status()
data = resp.json()["data"][0]
print(f"Total public debt as of {data['record_date']}: ${float(data['tot_pub_debt_out_amt']):,.0f}")
```

```python
# Preview Treasury exchange-rate rows for recent quarters (first page only)
resp = requests.get(f"{BASE_URL}/v1/accounting/od/rates_of_exchange", params={
    "fields": "country_currency_desc,exchange_rate,record_date,effective_date",
    "filter": "record_date:gte:2024-01-01",
    "sort": "-record_date",
    "page[size]": 100
}, timeout=30)
resp.raise_for_status()
df = pd.DataFrame(resp.json()["data"])
```

## Authentication

None required. The API is fully open and free.

## Core Parameters

| Parameter | Example | Description |
|-----------|---------|-------------|
| `fields=` | `fields=record_date,tot_pub_debt_out_amt` | Select specific columns |
| `filter=` | `filter=record_date:gte:2024-01-01` | Filter records |
| `sort=` | `sort=-record_date` | Sort (prefix `-` for descending) |
| `format=` | `format=json` | Output format: `json`, `csv`, `xml` |
| `page[size]=` | `page[size]=100` | Records per page (default 100) |
| `page[number]=` | `page[number]=2` | Page index (starts at 1) |

**Filter operators:** `lt`, `lte`, `gt`, `gte`, `eq`, `in`

```python
# Multiple filters separated by comma
"filter=country_currency_desc:in:(Canada-Dollar,Mexico-Peso),record_date:gte:2024-01-01"
```

## Key Datasets & Endpoints

### Debt

| Dataset | Endpoint | Frequency |
|---------|----------|-----------|
| Debt to the Penny | `/v2/accounting/od/debt_to_penny` | Daily |
| Historical Debt Outstanding | `/v2/accounting/od/debt_outstanding` | Annual |
| Schedules of Federal Debt | `/v1/accounting/od/schedules_fed_debt` | Monthly |

### Daily & Monthly Statements

| Dataset | Endpoint | Frequency |
|---------|----------|-----------|
| DTS Operating Cash Balance | `/v1/accounting/dts/operating_cash_balance` | Daily |
| DTS Deposits & Withdrawals | `/v1/accounting/dts/deposits_withdrawals_operating_cash` | Daily |
| Monthly Treasury Statement (MTS) | `/v1/accounting/mts/mts_table_1` (18 tables — see [datasets-fiscal.md](references/datasets-fiscal.md)) | Monthly |

### Interest Rates & Exchange

| Dataset | Endpoint | Frequency |
|---------|----------|-----------|
| Average Interest Rates on Treasury Securities | `/v2/accounting/od/avg_interest_rates` | Monthly |
| Treasury Reporting Rates of Exchange | `/v1/accounting/od/rates_of_exchange` | Quarterly |
| Interest Expense on Public Debt | `/v2/accounting/od/interest_expense` | Monthly |

**Exchange-rate interpretation:** Treasury Reporting Rates are foreign-currency units per USD, so divide a foreign-currency amount by the rate to obtain USD (and multiply USD to obtain foreign currency). These are government reporting rates, not live trading quotes. Preserve both `record_date` and `effective_date`, and check amendments before applying a rate to a reporting period.

### Securities & Auctions

| Dataset | Endpoint | Frequency |
|---------|----------|-----------|
| Treasury Securities Auctions Data | `/v1/accounting/od/auctions_query` | As Needed |
| Treasury Securities Upcoming Auctions | `/v1/accounting/od/upcoming_auctions` | As Needed |
| Treasury Securities Buybacks | `/v1/accounting/od/buybacks_operations` | As Needed |

### Savings Bonds

| Dataset | Endpoint | Frequency |
|---------|----------|-----------|
| I Bonds Interest Rates | `/v1/accounting/od/i_bonds_interest_rates` | Semi-Annual |
| Savings Bonds Issues, Redemptions & Maturities | `/v1/accounting/od/savings_bonds_report` | Monthly |

## Response Structure

```json
{
  "data": [...],
  "meta": {
    "count": 100,
    "total-count": 3790,
    "total-pages": 38,
    "labels": {"field_name": "Human Readable Label"},
    "dataTypes": {"field_name": "STRING|NUMBER|DATE|CURRENCY"},
    "dataFormats": {"field_name": "String|10.2|YYYY-MM-DD"}
  },
  "links": {"self": "...", "first": "...", "prev": null, "next": "...", "last": "..."}
}
```

**Note:** Data-row values are returned as strings; metadata counts are JSON numbers. Convert as needed (e.g., `float()`, `pd.to_datetime()`). Null values appear as the string `"null"`.

## Common Patterns

### Load all pages into a DataFrame

Use the bounded `fetch_all()` helper in [parameters.md](references/parameters.md). For small result sets, a single request with `page[size]=10000` may suffice when `meta.total-pages` is 1.

```python
# Single-page fetch when total-pages == 1
params = {"sort": "-record_date", "page[size]": 10000}
resp = requests.get(f"{BASE_URL}/v2/accounting/od/debt_outstanding", params=params, timeout=30)
resp.raise_for_status()
result = resp.json()
if result["meta"]["total-pages"] > 1:
    raise ValueError("Use fetch_all() from parameters.md for multi-page results")
df = pd.DataFrame(result["data"])
```

### Aggregation (automatic sum)

Selecting fewer fields can aggregate non-unique rows. It can also sum balances or rates that should not be added, and combine statement totals with their components. Inspect the full row grain first:

```python
# Preview full DTS rows, preserving account and category dimensions
resp = requests.get(f"{BASE_URL}/v1/accounting/dts/deposits_withdrawals_operating_cash", params={
    "filter": "record_date:eq:2024-01-16", "page[size]": 1000
}, timeout=30)
resp.raise_for_status()
```

## Interpretation checks

- DTS amounts are in millions. Since April 18, 2022, find the `Treasury General Account (TGA) Closing Balance` row and read `open_today_bal`; `close_today_bal` is null.
- MTS tables have different amount fields and row hierarchies. The compact monthly summary uses `mil_amt` (millions); do not assign that scale to every MTS field.


*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

