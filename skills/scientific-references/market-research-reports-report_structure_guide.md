---
id: sciref-market-research-reports-report-structure-guide
name: "Scientific Ref: Market Research Report Structure"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (market-research-reports): Market Research Report Structure"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "market research reports report structure guide"
  - "market pesquisa reports relatorio structure guide"
  - "market research report structure"
keywords:
  - "market"
  - "research"
  - "reports"
  - "report"
  - "structure"
  - "guide"
  - "pesquisa"
  - "relatorio"
  - "specialized"
  - "scientific"
  - "reference"
---

# Market Research Report Structure

Match the report to the decision and available evidence. There is no required
page count, chapter count, figure count, or output format. Omit irrelevant
modules and expand methods/limitations when uncertainty is high.

## Front matter

### Title and scope

Include:

- market and geography;
- historical and forecast periods;
- retrieval cutoff;
- report version and classification;
- sponsor, author, and material conflicts;
- explicit statement that the report is not investment, legal, or financial
  advice.

Do not use logos, layouts, or wording that imply affiliation with another firm.

### Executive synopsis

Write last. It should stand alone and contain:

1. decision context;
2. formal market boundary in one sentence;
3. highest-confidence findings with claim IDs;
4. top-down and bottom-up scenario range;
5. forecast scenario range and principal sensitivity;
6. material conflicts and limitations;
7. implications or options clearly labeled as judgment.

Never introduce a metric in the synopsis that is absent from the evidence and
claims ledgers.

## 1. Scope and definitions

Define:

- product/service inclusion and exclusion;
- customer, payer, user, and transaction;
- value-chain level;
- geography, imports/exports, and channels;
- time basis and as-of date;
- measure, unit, and denominator;
- stock/flow and gross/net treatment;
- currency, base year, and nominal/real basis;
- industry and product classifications with versions;
- adjacent markets that are excluded.

Explain alternate plausible definitions and why one was selected. An industry
classification is not automatically a product market or an antitrust market.

## 2. Evidence and methods

Describe:

- source hierarchy and search cutoff;
- original data producers and aggregator lineage;
- exact claim-source mapping;
- archived snapshots and revision handling;
- extraction, cleaning, joins, conversions, and calculations;
- source conflicts and reconciliation rules;
- confidence labels;
- primary-research methods and privacy controls;
- missing evidence and analysis deviations.

Summarize the source ledger by source type and revision status. Do not inflate
source count by counting mirrors or derivative articles as independent.

## 3. Market size

### Top-down

Show:

- control total and definition;
- disjoint components and coverage keys;
- in-scope fractions;
- channel/tax/trade adjustments;
- source IDs and limitations;
- resulting TAM scenarios.

### Bottom-up

Show:

- population or installed base;
- customer segments;
- annual units or transactions;
- price/spend assumptions;
- addressable fractions;
- source and assumption IDs;
- resulting TAM scenarios.

### SAM and SOM

For each scenario, state:

- serviceability filters;
- capture-share assumptions;
- time horizon;
- capacity, channel, sales-cycle, retention, and competition constraints;
- source evidence and analyst assumptions.

Present TAM/SAM/SOM as conditional scenarios. Do not select one estimate merely
because it is the midpoint.

### Reconciliation and sensitivity

Report:

- absolute and percentage gap between methods;
- definition, denominator, and coverage-key comparison;
- corrections for double counting;
- remaining unexplained difference;
- sensitivity to major counts, price, penetration, serviceability, and capture;
- switching values that change a decision.

## 4. Demand and customer evidence

Separate:

- official/administrative or transactional evidence;
- published survey evidence;
- original survey evidence;
- interview/focus-group themes;
- analyst interpretation.

For survey claims, include population, frame, sample method, mode, dates,
unweighted sample, weighting, response/participation, wording, precision, and
limitations. For interviews, include recruitment, consent, roles, mode, dates,
coding, divergent views, and limits to generalization.

## 5. Market dynamics

For each driver or inhibitor:

- state the mechanism;
- identify observed evidence versus assumption;
- quantify only with a defensible calculation;
- define time horizon and leading indicators;
- include disconfirming evidence;
- state how it changes a scenario input.

Frameworks such as PESTLE or SWOT may organize questions but are not evidence.
Use them only when useful, and do not force a fixed number of factors or scores.

## 6. Competitive landscape

### Scope

Define the product and geographic basis from the customer perspective. Consider
substitutability, non-price dimensions, channels, imports, digital/multi-sided
features, innovation, and dynamic change where relevant.

### Competitor set

State inclusion rules. Distinguish:

- current direct competitors;
- adjacent/substitute providers;
- potential entrants;
- channel partners or suppliers;
- unknown/private participants.

### Feature and positioning evidence

Use the validated matrix with product edition, geography, date, status, and
source IDs. Publish scoring rules for any positioning map. Use `unknown` when
evidence is absent.

### Shares and concentration

State numerator and denominator, metric, period, coverage, residual share, and
alternate definitions. Treat HHI/CRn as descriptive screens. Do not make legal
antitrust conclusions.

## 7. Forecast scenarios

### Historical basis

Show series IDs, units, frequency, seasonal adjustment, revisions, taxonomy
breaks, transformations, and vintage.

### Scenario design

For each named scenario, document:

- annual rate path or driver equations;
- demand, price, supply, regulation, competition, and capacity assumptions;
- evidence and assumption IDs;
- constraints and internal consistency;
- conditions that would make the scenario obsolete.

Do not assign probabilities without a defensible probabilistic model. Do not
call scenario bounds confidence or prediction intervals.

### Sensitivity

Report endpoints under stated input shifts, rank influential assumptions, and
identify decision thresholds. If interactions matter, add coherent combined
scenarios rather than relying only on one-way sensitivity.

## 8. Regulation and policy

Use primary regulator and legal sources. Record:

- jurisdiction and authority;
- instrument or docket identifier;
- publication, adoption, and effective dates;
- enacted/proposed/stayed/repealed status;
- affected products and entities;
- evidence-backed market mechanism;
- uncertainty and need for legal review.

Do not present a policy proposal as effective law or compliance interpretation
as legal advice

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

