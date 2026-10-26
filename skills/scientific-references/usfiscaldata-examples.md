---
id: sciref-usfiscaldata-examples
name: "Scientific Ref: Code Examples — U.S. Treasury Fiscal Data"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (usfiscaldata): Code Examples — U.S. Treasury Fiscal Data"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "usfiscaldata examples"
  - "code examples — u.s. treasury fiscal data"
keywords:
  - "usfiscaldata"
  - "examples"
  - "specialized"
  - "scientific"
  - "reference"
  - "code"
---

# Code Examples — U.S. Treasury Fiscal Data

Python queries and transformations below were exercised against the public API on
2026-09-30. First define `fetch_all()` from [parameters.md](parameters.md), then run
the setup. Historic dates are fixed examples, not claims about the current year.

## Setup

```python
from datetime import date
from decimal import Decimal
import requests
import pandas as pd

BASE_URL = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service"

def fetch(endpoint, **params):
    """Fetch one page; callers requesting a complete result use fetch_all."""
    allowed = {"fields", "filter", "sort", "format", "page[size]", "page[number]"}
    if set(params) - allowed:
        raise ValueError(f"Unknown query parameters: {set(params) - allowed}")
    resp = requests.get(BASE_URL + endpoint, params=params, timeout=30)
    resp.raise_for_status()
    result = resp.json()
    if "error" in result:
        raise ValueError(result)
    return result
```

## National Debt Tracker

```python
result = fetch("/v2/accounting/od/debt_to_penny",
               sort="-record_date", **{"page[size]": 1})
d = result["data"][0]
debt = Decimal(d["tot_pub_debt_out_amt"])
print(f"National debt as of {d['record_date']}: ${debt:,.2f}")

# Complete fixed-period series; cents remain in raw strings if needed.
df = fetch_all("/v2/accounting/od/debt_to_penny", {
    "filter": "record_date:gte:2024-01-01,record_date:lte:2024-12-31",
    "sort": "record_date", "page[size]": 100,
})
df["date"] = pd.to_datetime(df["record_date"])
df["debt_trillion"] = pd.to_numeric(df["tot_pub_debt_out_amt"]) / 1e12
print(df[["date", "debt_trillion"]].tail())
```

## Treasury Reporting Exchange Rates

```python
endpoint = "/v1/accounting/od/rates_of_exchange"
quarter = fetch(endpoint, sort="-record_date", **{"page[size]": 1})["data"][0]["record_date"]
rates = fetch_all(endpoint, {
    "filter": f"record_date:eq:{quarter}",
    "sort": "country_currency_desc,effective_date,src_line_nbr",
    "page[size]": 100,
})
rates["exchange_rate"] = pd.to_numeric(rates["exchange_rate"])
# Preserve amendments as separate rows; pick the applicable reporting period first.
rates["usd_1000_in_foreign_currency"] = 1000 * rates["exchange_rate"]
print(rates[["country_currency_desc", "record_date", "effective_date",
             "exchange_rate", "usd_1000_in_foreign_currency"]].head())
```

These are foreign-currency units per USD. Divide a foreign amount by its applicable
rate to obtain USD. Amendments have later `effective_date` values; quarterly PDF
reports omit amendments, so do not collapse rows without the official period rules.

## Treasury Securities Auction Analysis

```python
# Nominal fixed-rate 10-year notes. auction_date dates the event.
result = fetch("/v1/accounting/od/auctions_query",
    filter="security_type:eq:Note,original_security_term:eq:10-Year,inflation_index_security:eq:No,floating_rate:eq:No",
    sort="-auction_date,cusip", **{"page[size]": 20})
auctions = pd.DataFrame(result["data"])
for col in ["high_yield", "bid_to_cover_ratio", "total_accepted", "indirect_bidder_accepted"]:
    auctions[col] = pd.to_numeric(auctions[col].replace("null", None), errors="coerce")
auctions["indirect_pct_of_total"] = (
    100 * auctions["indirect_bidder_accepted"] / auctions["total_accepted"].where(auctions["total_accepted"] > 0)
)
print(auctions[["auction_date", "cusip", "security_term", "reopening",
                "high_yield", "indirect_pct_of_total"]].head())
```

`original_security_term` includes reopened securities whose remaining
`security_term` is shorter. Name the denominator when reporting bidder shares;
`total_accepted` is not the same as competitive awards. Missing yields can mean an
auction has been announced but results are unavailable. Auction yields observed on
different dates do not form a same-date yield curve; do not inner-join 2-year and
10-year auctions on publication dates and label the difference a market spread.

## Daily Treasury Statement

```python
endpoint = "/v1/accounting/dts/operating_cash_balance"
closing = fetch(endpoint,
    filter="account_type:eq:Treasury General Account (TGA) Closing Balance",
    sort="-record_date", **{"page[size]": 5})
for row in closing["data"]:
    print(row["record_date"], Decimal(row["open_today_bal"]), "million USD, closing TGA")

# Named totals avoid adding category detail to summary rows.
cash = fetch_all(endpoint, {
    "filter": "record_date:gte:2024-01-01,record_date:lte:2024-01-31",
    "sort": "record_date,src_line_nbr",
})
cash = cash[cash["account_type"].isin([
    "Total TGA Deposits (Table II)", "Total TGA Withdrawals (Table II) (-)",
])].copy()
cash["million_usd"] = pd.to_numeric(cash["open_today_bal"])
print(cash.pivot(index="record_date", columns="account_type", values="million_usd"))
```

Since April 18, 2022, `close_today_bal` is null. The closing-balance account row
stores its value in `open_today_bal`. Earlier layouts need separate handling.
DTS cash movements include financing and differ from MTS budget receipts/outlays.

## Monthly Budget Summary

```python
budget = fetch_all("/v1/accounting/mts/mts_receipts_outlays_deficit_surplus", {
    "filter": "record_fiscal_year:eq:2024",
    "sort": "record_date,src_line_nbr",
})
budget = budget[budget["amt_category"].isin(["Receipts", "Outlays", "Deficit/Surplus (-)"])].copy()
budget["million_usd"] = pd.to_numeric(budget["mil_amt"])
monthly = budget.pivot(index="record_date", columns="amt_category", values="million_usd")
assert len(monthly) == 12, "Fiscal year is incomplete"
# Published values are rounded to millions; allow rounding differences.
residual = monthly["Outlays"] - monthly["Receipts"] - monthly["Deficit/Surplus (-)"]
if (residual.abs() > 1).any():
    print("[WARN] Reconcile source revisions/footnotes before using these months:")
    print(residual[residual.abs() > 1])
print(monthly)
```

The live FY2024 extract on the review date had a March 2024 reconciliation
residual of -270 million USD, beyond rounding. This example exposes that source
discrepancy; it does not treat the series as reconciled or overwrite the published
values. Check the matching report/revisions before drawing budget conclusions.

This summary has explicit million-dollar units. Tables 1 and 9 have different
fields and dollar-scale API values; Table 1 repeats prior months and fiscal-year
sections in each publication. Never add all Table 1 rows to obtain monthly totals.

## Average Treasury and I Bond Rates

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

