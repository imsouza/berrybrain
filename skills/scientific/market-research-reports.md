---
id: sci-market-research-reports
name: "Scientific: market-research-reports"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Builds evidence-traceable market research reports and assumption-driven market sizing or forecast scenarios. Use for market definition, industry and customer evidence, competitive landscapes, TAM/SAM/SOM reconciliation, forecast sensitivity, and auditable report scaffolds."
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "market research reports"
  - "market pesquisa reports"
  - "market-research-reports"
keywords:
  - "market"
  - "research"
  - "reports"
  - "pesquisa"
  - "builds"
  - "evidence"
  - "traceable"
---

# Market Research Reports

## Purpose

Create decision-focused market reports whose claims, calculations, assumptions,
and uncertainties can be audited. Match depth and format to the question and
evidence. There is no required length, chapter count, visual count, or output
format.

Do not:

- imitate or imply affiliation with a consulting, analyst, or research brand;
- invent citations, quotes, market shares, or paid-market figures;
- present TAM/SAM/SOM or a forecast as one certain truth;
- treat a framework, chart, or fluent narrative as evidence;
- provide investment, legal, antitrust, tax, accounting, or regulatory advice.

## Operating principles

1. **Define before sizing.** Fix product, customer, geography, channel, period,
   measure, unit, denominator, currency/base year, and taxonomy.
2. **Map every claim.** Every factual or quantitative claim has a claim ID and
   exact source IDs.
3. **Separate statement types.** Distinguish facts, estimates, calculations,
   forecasts, opinions, and recommendations.
4. **Prefer primary evidence.** Use official statistics, regulator records,
   filed company disclosures, and transparent original studies before
   secondary synthesis.
5. **Preserve uncertainty.** Retain source conflicts, revisions, scenario
   ranges, sensitivity, and limitations.
6. **Keep methods reproducible.** Use local structured inputs and deterministic
   calculations when practical.
7. **Collect lawfully and ethically.** No deception, PII disclosure, access
   circumvention, confidential material, or trade-secret acquisition.

## Workflow

### 1. Establish the research contract

Clarify:

- decision, audience, deadline, and materiality threshold;
- formal market definition and adjacent exclusions;
- buyer, payer, user, transaction, and value-chain level;
- geography and treatment of imports, exports, and channels;
- historical period, forecast period, and retrieval cutoff;
- revenue/expenditure, gross output/value added, units, capacity, users, or
  another measure;
- stock/flow, gross/net, taxes, and denominator;
- currency, base year, and nominal/real/current/constant basis;
- industry and product classification with version;
- permitted data sources, primary research, confidentiality, and output format.

Ask a focused question when a missing choice would materially change the
denominator or result. Otherwise state a provisional scope and proceed.

Use `references/report_structure_guide.md` for modular report design.

### 2. Build the evidence plan

Route each question to the source closest to the underlying event:

1. primary law, regulator decision, official filing, or official statistic;
2. original company filing or attributable first-party disclosure;
3. transparent survey/study with inspectable methods;
4. institutional or peer-reviewed research using identifiable primary data;
5. industry association data with disclosed coverage;
6. reputable secondary synthesis;
7. lawfully accessed paid estimate with inspectable scope and method;
8. news/commentary for leads or attributable events.

For company data, prefer the official filing system in the relevant
jurisdiction. For industry, labor, prices, population, trade, and national
accounts, prefer the responsible national statistical agency or central bank.
For cross-country work, use harmonized World Bank, IMF, OECD, or Eurostat data
only after checking definitions and original-source lineage.

Read `references/official_data_sources.md` before using public APIs. API rules
and limits are a dated snapshot: verify current official terms before automated
or high-volume retrieval. Never put an API key in a report or bundled script.

### 3. Create the source ledger

Assign stable IDs (`S-001`, `S-002`, ...). Record:

- title, publisher, URL/persistent ID, source type;
- publication date and retrieval date;
- original producer when accessed through an aggregator;
- geography, covered population, period, and vintage;
- currency, base year, price basis, measure type, unit, and denominator;
- taxonomy and version;
- preliminary/revised/final/current status;
- method, sample, imputation, suppression, and limitations;
- license/terms and lawful local snapshot path.

Use `assets/source_ledger_template.csv` and validate it:

```bash
python3 scripts/validate_evidence_ledger.py data/source_ledger.csv
```

If publication date is unavailable, record `not-stated`; do not guess.

### 4. Maintain a claims ledger

Assign IDs (`C-001`, ...). Keep the exact claim text, statement type, source
IDs, report location, as-of date, geography, currency/base, measure/unit,
taxonomy, revision status, confidence, calculation ID, and assumption IDs.

Rules:

- one end-of-paragraph citation does not support unrelated sentences;
- split compound claims that rely on different evidence;
- a calculation cites its inputs, not a source that never published the result;
- an aggregator and its original source are not independent corroboration;
- an interview theme is not population prevalence;
- absence of public feature evidence means `unknown`, not `no`.

Audit mappings:

```bash
python3 scripts/audit_claim_citations.py \
  data/claims.csv data/source_ledger.csv
```

See `references/evidence_model.md`.

### 5. Size the market as scenarios

#### Measurement guardrails

Give every component a disjoint `coverage_key` and one shared
`denominator_id`. Do not add:

- manufacturer revenue to distributor or end-customer spend;
- production, imports, and sales without trade/inventory reconciliation;
- parent and subsidiary revenue;
- bundles and their included components;
- gross output and value added;
- installed-base stock and annual transaction flow;
- overlapping customer or geographic segments.

Use product classifications and supply-use logic when industry codes are too
broad. Preserve an unknown/residual category instead of forcing totals.

#### Top-down and bottom-up

Compute independently:

```text
TAM_top = sum(disjoint in-scope component values)

TAM_bottom =
  sum(customer_count
      * addressable_fraction
      * annual_quantity_per_customer
      * price_per_unit)
```

Then apply scenario-specific serviceability and capture assumptions:

```text
SAM_s = TAM * serviceable_fraction_s
SOM_s = SAM_s * obtainable_share_s
```

Use at least two genuinely different scenarios; a downside/base/upside set is
usually useful. State horizon, constraints, evidence, and assumptions. SOM is
not a guaranteed revenue forecast.

Run the deterministic calculato

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

