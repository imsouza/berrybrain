---
id: sciref-peer-review-reporting-standards
name: "Scientific Ref: Reporting Guidelines and Domain Metadata Standards"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (peer-review): Reporting Guidelines and Domain Metadata Standards"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "peer review reporting standards"
  - "peer revisao reporting standards"
  - "reporting guidelines and domain metadata standards"
keywords:
  - "peer"
  - "review"
  - "reporting"
  - "standards"
  - "revisao"
  - "specialized"
  - "scientific"
  - "reference"
---

# Reporting Guidelines and Domain Metadata Standards

Reviewed against primary or official sources on **2026-10-01**; source-specific access limitations are recorded in the ledger. The dated evidence record is `assets/source_ledger.csv`; the machine-readable selector catalog is `assets/reporting_guidelines.json`.

## What reporting guidelines do—and do not do

A reporting guideline identifies information that should be reported so readers can understand and appraise a study. It is not, by itself:

- A method for designing or conducting the study
- A risk-of-bias tool
- A statistical reanalysis
- A measure of truth, importance, novelty, or manuscript merit
- A publication recommendation

Checklist completion must never be converted automatically into a quality score. A fully reported study can have serious design problems; an incompletely reported study may be impossible to assess. Record missing information as a reporting gap, then separately assess any design, conduct, analysis, reproducibility, or ethics concern using appropriate evidence and expertise.

Use the guideline’s current statement together with its explanation and elaboration. Check applicable extensions and the target venue’s instructions. Do not copy checklist wording into a review when a specific, contextual comment is more useful.

## Selection workflow

1. Identify the **report kind**: results, protocol, abstract, or data release.
2. Identify the **study design**, not merely the topic or journal section.
3. Add cross-cutting features: AI intervention, diagnostic AI, routinely collected data, clustered design, qualitative interviews, and so on.
4. Select the current base guideline and applicable extensions.
5. Use the official checklist to record `reported`, `partly_reported`, `not_reported`, `not_applicable`, or `not_assessed`.
6. Explain `not_applicable`; do not treat it as a defect.
7. Keep reporting coverage separate from methodological appraisal.

Run:

```bash
python3 scripts/select_reporting_guidelines.py \
  assets/study_profile_template.json \
  --coverage assets/reporting_checklist_template.csv
```

The bundled catalog is a dated aid, not a live registry. Consult the [EQUATOR Network](https://www.equator-network.org/) and official guideline site when the study type is unclear or a newer extension may apply.

## Major current health-research guidelines

### Randomized trial results — CONSORT 2025

- Current statement: **CONSORT 2025**, published 14 April 2025
- Structure: 30 main checklist items and a participant flow diagram
- Supersedes: CONSORT 2010
- Use for: reports of randomized trials
- Review with: explanation and elaboration plus design/intervention extensions
- Important boundary: the statement explicitly says it is not a quality assessment instrument

Check registration, protocol and statistical analysis plan consistency, allocation, participant flow, outcomes and harms, effect estimates and uncertainty, protocol changes, data sharing, conflicts, and patient/public involvement where applicable.

Official sources: [CONSORT–SPIRIT](https://www.consort-spirit.org/) and the [CONSORT 2025 statement](https://www.bmj.com/content/389/bmj-2024-081123).

### Randomized trial protocols — SPIRIT 2025

- Current statement: **SPIRIT 2025**, published 28 April 2025
- Structure: 34 main checklist items and a participant timeline
- Supersedes: SPIRIT 2013
- Use for: randomized trial protocols

Compare the protocol with registration, statistical analysis plan, ethics records, amendments, and any completed-trial report. Explicitly stated non-applicability with rationale is not missing reporting.

Official sources: [CONSORT–SPIRIT](https://www.consort-spirit.org/) and the [SPIRIT 2025 statement](https://www.bmj.com/content/389/bmj-2024-081477).

### Systematic reviews — PRISMA 2020

- Current statement: **PRISMA 2020** (named 2020; published 2021)
- Structure: 27 main items, expanded checklist, abstract checklist, and flow diagrams
- Use for: completed systematic reviews, primarily reviews of intervention effects
- Protocols: use PRISMA-P
- Extensions: use the appropriate extension for scoping, diagnostic, individual-participant-data, network, equity, harms, or other specialized reviews

PRISMA explicitly does not assess review conduct or methodological quality. Use appropriate methods and risk-of-bias tools separately.

Official sources: [PRISMA 2020 resources](https://www.prisma-statement.org/prisma-2020) and the [primary statement](https://www.bmj.com/content/372/bmj.n71).

### Observational studies — STROBE

- Current base statement: **STROBE 2007**
- Structure: 22 main items with cohort, case-control, cross-sectional, and combined checklists
- Use for: reports of observational epidemiologic studies
- Extensions: examples include RECORD for routinely collected health data, STREGA for genetic association studies, STROBE-MR, and domain-specific extensions

STROBE helps identify whether selection, measurement, bias, confounding, missing data, sensitivity analyses, and generalizability are reported. It does not establish that those methods were adequate.

Official source: [STROBE](https://www.strobe-statement.org/).

### Diagnostic accuracy — STARD 2015

- Current base statement: **STARD 2015**
- Structure: 30 main items and a flow diagram
- Use for: studies estimating diagnostic accuracy against a reference standard

Separately assess risk of bias and applicability with a suitable tool such as the current QUADAS family when relevant. STARD’s official implementation guidance explicitly says not to use the reporting checklist as a design-quality tool.

Official source: [STARD 2015](https://www.equator-network.org/reporting-guidelines/stard/).

### AI-centered diagnostic accuracy — STARD-AI

- Current statement: **STARD-AI 2025**
- Published: 15 September 2025; an author correction was published 13 July 2026
- Structure: 40 items, including 18 new or modified items relative to STARD 2015
- Use for: AI-centered diagnostic accuracy studies, including suitable diagnostic classification tasks

Check dataset practices, index-test specification, evaluation, algorithmic bias and fairness, applicability, and generalizability. If the primary aim is development or evaluation of a multivariable prediction model, use TRIPOD+AI instead.

Official source: [STARD-AI](https://www.nature.com/articles/s41591-025-03953-8).

### Clinical prediction models — TRIPOD+AI

- Current statement: **TRIPOD+AI 2024**
- Structure: 27 main item

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

