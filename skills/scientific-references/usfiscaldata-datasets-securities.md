---
id: sciref-usfiscaldata-datasets-securities
name: "Scientific Ref: Securities & Savings Bonds Datasets — U.S. Treasury Fiscal Data"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (usfiscaldata): Securities & Savings Bonds Datasets — U.S. Treasury Fiscal Data"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "usfiscaldata datasets securities"
  - "securities & savings bonds datasets — u.s. treasury fiscal data"
keywords:
  - "usfiscaldata"
  - "datasets"
  - "securities"
  - "specialized"
  - "scientific"
  - "reference"
  - "savings"
---

# Securities & Savings Bonds Datasets — U.S. Treasury Fiscal Data

## Treasury Securities Auctions Data

**Endpoint:** `/v1/accounting/od/auctions_query`  
**Frequency:** As Needed  
**Date Range:** November 1979 to present

Historical data on Treasury securities auctions including bills, notes, bonds, TIPS, and FRNs.

**Key fields:**
| Field | Type | Description |
|-------|------|-------------|
| `record_date` | DATE | Publication date; do not use as auction date |
| `auction_date` | DATE | Date auction was held |
| `security_type` | STRING | Basic security type; inspect `inflation_index_security` and `floating_rate` flags for TIPS/FRNs |
| `security_term` | STRING | e.g., "4-Week", "2-Year", "10-Year" |
| `cusip` | STRING | CUSIP identifier |
| `offering_amt` | CURRENCY0 | Amount offered |
| `high_yield` | NUMBER | High accepted yield (notes/bonds/TIPS; bills use `high_discnt_rate`) |
| `int_rate` | NUMBER | Coupon/interest rate of the security |
| `bid_to_cover_ratio` | NUMBER | Bid-to-cover ratio |
| `total_accepted` | NUMBER | Total accepted amount (USD) |
| `indirect_bidder_accepted` | NUMBER | Indirect bidder amount accepted (USD) |
| `issue_date` | DATE | Issue/settlement date |
| `maturity_date` | DATE | Maturity date |

```python
# Get recent 10-year Treasury note auctions
resp = requests.get(
    "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/od/auctions_query",
    params={
        "filter": "security_type:eq:Note,original_security_term:eq:10-Year,inflation_index_security:eq:No,floating_rate:eq:No",
        "sort": "-auction_date",
        "page[size]": 10
    },
    timeout=30,
)
resp.raise_for_status()
df = pd.DataFrame(resp.json()["data"])

# Get all auctions in 2024
resp = requests.get(
    "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/od/auctions_query",
    params={
        "filter": "auction_date:gte:2024-01-01,auction_date:lte:2024-12-31",
        "sort": "-auction_date",
        "page[size]": 10000
    },
    timeout=30,
)
resp.raise_for_status()
assert resp.json()["meta"]["total-pages"] <= 1, "Use fetch_all for more pages"
```

## Treasury Securities Upcoming Auctions

**Endpoint:** `/v1/accounting/od/upcoming_auctions`  
**Frequency:** As Needed  
**Date Range:** March 2024 to present

Schedule data can include historical rows. Filter `auction_date:gte:<today>` for future auction dates, or `issue_date` for settlement timing. Do not assume an unfiltered response contains only upcoming events.

**Key fields:**
| Field | Type | Description |
|-------|------|-------------|
| `auction_date` | DATE | Scheduled auction date |
| `security_type` | STRING | Security type |
| `security_term` | STRING | Maturity term |
| `offering_amt` | CURRENCY0 | Announced offering amount |

```python
# Get upcoming auctions
from datetime import date
resp = requests.get(
    "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/od/upcoming_auctions",
    params={"filter": f"auction_date:gte:{date.today().isoformat()}", "sort": "auction_date", "page[size]": 1000},
    timeout=30,
)
resp.raise_for_status()
assert resp.json()["meta"]["total-pages"] <= 1, "Use fetch_all for more pages"
upcoming = pd.DataFrame(resp.json()["data"])
if upcoming.empty:
    print("No upcoming rows returned for the requested date range")
else:
    print(upcoming[["auction_date", "security_type", "security_term", "offering_amt"]])
```

## Record-Setting Treasury Securities Auction Data

**Frequency:** As Needed

Tracks auction records (largest, highest rate, lowest rate, etc.) for each security type and term.

## Treasury Securities Buybacks

**Frequency:** As Needed (2 data tables)  
**Date Range:** March 2000 to present

Data on Treasury's secondary market buyback (repurchase) operations. Active since the program's relaunch in 2024.

| Table | Endpoint | Description |
|-------|----------|-------------|
| Buybacks Operations | `/v1/accounting/od/buybacks_operations` | Announcements and results per operation |
| Security Details | `/v1/accounting/od/buybacks_security_details` | Security details per operation |

```python
# Recent buyback operations
resp = requests.get(
    "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/od/buybacks_operations",
    params={"sort": "-operation_date", "page[size]": 10},
    timeout=30,
)
resp.raise_for_status()
df = pd.DataFrame(resp.json()["data"])
print(df[["operation_date", "settlement_date"]].head())
```

---

## I Bonds Interest Rates

**Endpoint:** `/v1/accounting/od/i_bonds_interest_rates`  
**Frequency:** Semi-Annual (May and November)  
**Date Range:** September 1998 to present

Composite interest rates for Series I Savings Bonds, including fixed rate and inflation rate components.

**Key fields:**
| Field | Type | Description |
|-------|------|-------------|
| `issue_year_month` | STRING | Bond issue month (`YYYY-MM`); fixes the bond vintage |
| `earning_period_start` | DATE | Start of published earning period |
| `earning_period_end` | DATE | End of published earning period |
| `fixed_rate` | PERCENTAGE | Fixed rate component |
| `semi_annual_inflation_rate` | PERCENTAGE | Semi-annual CPI-U inflation rate |
| `combined_rate` | PERCENTAGE | Combined composite rate |

Do not take the first row sorted only by earning period: many issue-month
vintages share that period and have different fixed rates. Filter
`issue_year_month` for the bond, and choose the earning period appropriate to the
reporting date. The first period may be shorter than six months. The current
rate for newly issued bonds is not the rate for every outstanding I Bond.
See [examples.md](examples.md) for a query that names its issue vintage.

## U.S. Treasury Savings Bonds: Issues, Redemptions & Maturities

Three data tables under `/v1/accounting/od/`:

| Table | Endpoint | Description |
|-------|----------|-------------|
| Issues, Redemptions & Maturities | `/v1/accounting/od/savings_bonds_report` | Paper-bond counts by series |
| Matured Unredeemed Debt | `/v1/accounting/od/savings_bonds_mud` | Matured unredeemed debt |
| Piece Information by Series | `/v1/accounting/od/savings_bonds_pcs` | Piece information by series |

**Frequency:** Monthly  
**Date Range:** September 1998 to present

The `savings_bonds_report` table counts paper bonds by series; its fields are not dollar amounts. Its API coverage starts in January 2019; the other tables have different start dates. These counts sh

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

