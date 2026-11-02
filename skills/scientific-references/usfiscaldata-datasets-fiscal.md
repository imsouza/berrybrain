---
id: sciref-usfiscaldata-datasets-fiscal
name: "Scientific Ref: Fiscal Statement Datasets — U.S. Treasury Fiscal Data"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (usfiscaldata): Fiscal Statement Datasets — U.S. Treasury Fiscal Data"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "usfiscaldata datasets fiscal"
  - "fiscal statement datasets — u.s. treasury fiscal data"
keywords:
  - "usfiscaldata"
  - "datasets"
  - "fiscal"
  - "specialized"
  - "scientific"
  - "reference"
  - "statement"
---

# Fiscal Statement Datasets — U.S. Treasury Fiscal Data

## Daily Treasury Statement (DTS)

The DTS dataset has **9 data tables**, all under `/v1/accounting/dts/`. Updated daily (business days).

**Date Range:** October 2005 to present

### DTS Tables

| Table | Endpoint | Description |
|-------|----------|-------------|
| Operating Cash Balance | `/v1/accounting/dts/operating_cash_balance` | Treasury General Account balance |
| Deposits & Withdrawals | `/v1/accounting/dts/deposits_withdrawals_operating_cash` | Changes to TGA |
| Public Debt Transactions | `/v1/accounting/dts/public_debt_transactions` | Issues and redemptions of securities |
| Adjustment of Public Debt | `/v1/accounting/dts/adjustment_public_debt_transactions_cash_basis` | Cash basis adjustments |
| Debt Subject to Limit | `/v1/accounting/dts/debt_subject_to_limit` | Debt vs. statutory limit |
| Inter-Agency Tax Transfers | `/v1/accounting/dts/inter_agency_tax_transfers` | Intra-government tax transfers |
| Federal Tax Deposits | `/v1/accounting/dts/federal_tax_deposits` | Tax deposit activity |
| Short-Term Cash Investments | `/v1/accounting/dts/short_term_cash_investments` | Cash investment activity |
| Income Tax Refunds Issued | `/v1/accounting/dts/income_tax_refunds_issued` | Tax refund issuances |

### Common DTS Fields

| Field | Type | Description |
|-------|------|-------------|
| `record_date` | DATE | Business date |
| `account_type` | STRING | Account/balance type |
| `open_today_bal` | CURRENCY0 | Opening balance |
| `open_month_bal` | CURRENCY0 | Opening month balance |
| `open_fiscal_year_bal` | CURRENCY0 | Opening fiscal year balance |
| `close_today_bal` | CURRENCY0 | Closing balance |
| `transaction_today_amt` | CURRENCY0 | Today's transaction amount |
| `transaction_mtd_amt` | CURRENCY0 | Month-to-date amount |
| `transaction_fytd_amt` | CURRENCY0 | Fiscal year-to-date amount |

Since April 18, 2022, `close_today_bal` is null. Select
`account_type:eq:Treasury General Account (TGA) Closing Balance` and read
`open_today_bal` for the closing balance (millions of USD). The similarly named
opening-balance row is a different observation. See [examples.md](examples.md).

Table II has category hierarchies; preserve `account_type`, `transaction_type`,
`transaction_catg` and `transaction_catg_desc` before selecting totals. Use the
explicit Table I total deposit/withdrawal rows for a daily cash-flow summary.
Do not add cumulative `transaction_mtd_amt`/`transaction_fytd_amt` across dates.

Federal Tax Deposits is historical; the current reporting structure uses
Inter-Agency Tax Transfers and Table II. Short-Term Cash Investments is
historical and was removed from the published report in February 2023.

---

## Monthly Treasury Statement (MTS)

The MTS dataset has **18 data tables**, all under `/v1/accounting/mts/`. Updated monthly.

**Date Range:** October 1980 to present

### MTS Tables

| Endpoint | Description |
|----------|-------------|
| `/v1/accounting/mts/mts_table_1` | Summary of receipts, outlays, and deficit/surplus |
| `/v1/accounting/mts/mts_table_2` | Summary of budget and off-budget results |
| `/v1/accounting/mts/mts_table_3` | Summary of receipts and outlays |
| `/v1/accounting/mts/mts_table_4` | Receipts of the U.S. Government |
| `/v1/accounting/mts/mts_table_5` | Outlays of the U.S. Government |
| `/v1/accounting/mts/mts_table_5m` | Receipts offset against outlays |
| `/v1/accounting/mts/mts_table_6` | Means of financing the deficit or disposition of surplus |
| `/v1/accounting/mts/mts_table_6a` | Analysis of change in excess of liabilities |
| `/v1/accounting/mts/mts_table_6b` | Securities issued under special financing authorities |
| `/v1/accounting/mts/mts_table_6c` | Federal agency borrowing via Treasury securities |
| `/v1/accounting/mts/mts_table_6d` | Investments of federal accounts in federal securities |
| `/v1/accounting/mts/mts_table_6e` | Guaranteed and direct loan financing, net activity |
| `/v1/accounting/mts/mts_table_7` | Receipts and outlays by month |
| `/v1/accounting/mts/mts_table_8` | Trust fund impact on budget results and holdings |
| `/v1/accounting/mts/mts_table_9` | Summary of receipts by source and outlays by function |
| `/v1/accounting/mts/mts_table_9_outlays_functions_subfunctions` | Outlays by function and subfunction |
| `/v1/accounting/mts/mts_distributed_offsetting_receipts` | Distributed offsetting receipts |
| `/v1/accounting/mts/mts_receipts_outlays_deficit_surplus` | Receipts, outlays, and deficit/surplus |

### MTS field and unit differences

| Table | Amount fields | Interpretation |
|-------|---------------|----------------|
| Table 1 | `current_month_gross_rcpt_amt`, `current_month_gross_outly_amt`, `current_month_dfct_sur_amt` | Dollar amounts; each publication includes multiple months, fiscal years and YTD rows |
| Table 9 | `current_month_rcpt_outly_amt`, `current_fytd_rcpt_outly_amt`, `prior_fytd_rcpt_outly_amt` | Dollar amounts by receipt source/outlay function |
| Monthly summary | `amt_category`, `mil_amt` | One category per reporting month; amount in millions of USD |

`record_date` dates the publication, not necessarily the month described by a
Table 1 row. For a simple monthly budget series use
`mts_receipts_outlays_deficit_surplus` as shown in [examples.md](examples.md).
Deficit is positive and surplus negative in its `Deficit/Surplus (-)` category.

Tables have totals, subtotals and structural rows with null values. Reconcile
`parent_id`/`classification_id` within each publication before aggregating;
classification IDs change between publications. Do not filter Table 1 for
"Total Receipts": its receipt and outlay values are columns on month/YTD rows.
Table 9 line 120 is the documented total-receipts example; inspect its label and
hierarchy and use `current_month_rcpt_outly_amt`.

The dataset's generic notes describe published reports in millions, but live
Table 1/9 API amounts are dollar-scale while `mil_amt` explicitly represents
millions. Validate each field against the matching report; never apply one
scaling factor to all MTS endpoints. API coverage starts at different dates by
table; the dataset-wide 1980 start is not every table's first API observation.

---

## U.S. Government Revenue Collections

**Endpoint:** `/v2/revenue/rcm`  
**Frequency:** Daily  
**Date Range:** October 2004 to present

Daily tax and non-tax revenue collections.

---

## Financial Report of the U.S. Government

**Endpoint:** (8 tables)  
**Frequency

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

