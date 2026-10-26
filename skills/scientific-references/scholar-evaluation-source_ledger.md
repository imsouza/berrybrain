---
id: sciref-scholar-evaluation-source-ledger
name: "Scientific Ref: Dated Source Ledger"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (scholar-evaluation): Dated Source Ledger"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "scholar evaluation source ledger"
  - "dated source ledger"
keywords:
  - "scholar"
  - "evaluation"
  - "source"
  - "ledger"
  - "specialized"
  - "scientific"
  - "reference"
  - "dated"
---

# Dated Source Ledger

Refreshed on **2026-10-01** against the current official pages, source PDFs,
and ScholarEval project record below. This updates the 2026-07-23 review.
Policy-source verification and local synthetic-tool tests are distinct: no
researcher profiles, bibliometric datasets, authenticated services, external
model pipeline, or private work were evaluated.

The bundled workflow is local JSON/CSV only. It contains no scholarly-database,
author-identity, citation-count, authentication, pagination, or rate-limit API
contract. The shared collection citation's arXiv request is a metadata lookup,
not an evaluation service. Do not graft provider endpoints into this rubric.

## Responsible research assessment

### San Francisco Declaration on Research Assessment (DORA)

- **Primary source:** [Read the Declaration](https://sfdora.org/read/)
- **Origin:** developed in 2012; official page rechecked 2026-10-01.
- **Verified points:** assess work on its own merits; do not use journal-based
  measures as surrogates for an article or a person's contribution; state
  criteria explicitly; consider data, software, and other outputs; use
  qualitative evidence; make metric methods transparent and account for field
  and output-type variation.
- **Use here:** categorical ban on scored prestige proxies and a requirement
  for explicit criteria, diverse evidence, and traceability.

### DORA quantitative-indicator guidance

- **Primary source:** [Guidance on the responsible use of quantitative
  indicators](https://sfdora.org/resource/guidance-on-the-responsible-use-of-quantitative-indicators-in-research-assessment/)
- **Document:** [official PDF](https://sfdora.org/wp-content/uploads/2024/05/DORA_indicators_guidance.pdf)
- **Release:** 2024; official resource page accessible in 2026.
- **Verified points:** no indicator captures research quality in one number;
  uses should be clear, transparent, specific, contextual, and fair. The
  guidance addresses journal measures, citation counts, the h-index,
  field-normalized indicators, and altmetrics; it warns about reductive,
  aggregate, composite, lagging, field, career-stage, and bias effects.
- **Use here:** quantitative indicators are excluded from rubric scores. If
  mentioned descriptively outside the tools, their purpose, data, coverage,
  time window, field normalization, uncertainty, bias, and non-quality meaning
  must be explicit.

### Leiden Manifesto

- **Primary source:** Hicks, Wouters, Waltman, de Rijcke, and Rafols,
  [“Bibliometrics: The Leiden Manifesto for research
  metrics”](https://doi.org/10.1038/520429a), *Nature* 520, 429–431.
- **Published:** 2015-04-22. Publisher metadata remains current. The publisher
  full text was access-limited during this refresh; principles were checked
  against the [author-linked Spanish translation](https://www.leidenmanifesto.org/uploads/4/1/6/0/41603901/manifiesto_cast.pdf)
  hosted by the official manifesto site.
- **Verified points:** quantitative evaluation should support qualitative
  expert assessment; measure against missions; protect locally relevant
  research; account for field variation; keep data and analysis open and
  verifiable; allow those evaluated to verify data; account for career age and database differences;
  avoid false precision; recognize gaming and system effects; review indicators
  regularly.
- **Use here:** contextualization, inspectability, uncertainty, fairness review,
  and periodic revision.

### Agreement on Reforming Research Assessment / CoARA

- **Primary record:** [Agreement on Reforming Research
  Assessment](https://doi.org/10.5281/zenodo.13480728), version 1.
- **Published:** 2022-07-20; Zenodo record modified 2024-08-29.
- **Current official overview:** [CoARA Agreement](https://www.coara.org/agreement/the-agreement-full-text/)
- **Verified points:** recognize diverse outputs, practices, activities, roles,
  and careers; base assessment primarily on qualitative judgment with peer
  review central; use quantitative indicators responsibly; abandon
  inappropriate uses of journal- and publication-based measures, especially
  Journal Impact Factor and h-index; publish criteria; train assessors; review
  and evaluate criteria, tools, and processes.
- **Use here:** qualitative-first process, rubric provenance, rater training,
  monitoring, and no metric shortcut.

### Hong Kong Principles

- **Primary article:** Moher et al. (2020), [“The Hong Kong Principles for
  assessing researchers: Fostering research
  integrity”](https://doi.org/10.1371/journal.pbio.3000737), *PLOS Biology*
  18(7):e3000737.
- **Published:** 2020-07-16.
- **Official implementation page:** [World Conferences on Research Integrity
  Foundation](https://www.wcrif.org/guidance/hong-kong-principles)
- **Verified points:** assess responsible practices, value complete reporting,
  reward open research, acknowledge diverse research activity, and recognize
  essential work such as review and mentoring.
- **Use here:** integrity, reporting, appropriate openness, and diverse
  contribution evidence. The principles do not supply validated score weights.

### The Metric Tide and its commissioned revisit

- **Primary public-sector source:** Research England/UKRI, [*The Metric
  Tide*](https://www.ukri.org/publications/review-of-metrics-in-research-assessment-and-management/).
- **Published:** 2015-07-06.
- **Revisit:** Curry, Gadd, and Wilsdon, [*Harnessing the Metric
  Tide*](https://rori.figshare.com/articles/report/Harnessing_the_Metric_Tide/21701624),
  version 2 (DOI 10.6084/m9.figshare.21701624).
- **Posted:** 2022-12-12; commissioned by the joint UK higher-education funding
  bodies for the Future Research Assessment Programme.
- **Verified points:** the revisit recommends putting principles into practice,
  evaluating with those evaluated, avoiding all-metric approaches, using data
  for public benefit, and rethinking rankings.
- **Status limitation:** *Harnessing the Metric Tide* describes itself as an
  independent input to deliberations, not the eventual policy conclusion.
- **Use here:** stakeholder participation, no all-metric process, and explicit
  scrutiny of rankings and system effects.

### Current UKRI guidance

- **Primary policy:** [UKRI funding assessment and decision-making policy and
  principles](https://www.ukri.org/publications/ukri-principles-of-assessment-and-decision-making/uk-research-and-innovation-ukri-funding-assessment-and-decision-making-policy-and-princ

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

