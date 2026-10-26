---
id: sciref-scientific-writing-source-ledger
name: "Scientific Ref: Source Ledger"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (scientific-writing): Source Ledger"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "scientific writing source ledger"
  - "cientifico writing source ledger"
  - "source ledger"
keywords:
  - "scientific"
  - "writing"
  - "source"
  - "ledger"
  - "cientifico"
  - "specialized"
  - "reference"
---

# Source Ledger

Current review date: **2026-10-01** (initial research: 2026-07-24)

Method: current official-page reads plus `parallel-cli extract` (600-second maximum
cache age, no stale fallback), restricted to
official guideline organizations, standards bodies, government sites, and original
statement publications. No search-result artifacts are bundled. Re-check every source
and the target journal immediately before submission because policies can change.

Source IDs in this ledger ground factual statements in the skill. They are not evidence
IDs for a user's manuscript.

## Publication ethics, authorship, and AI

### SW-S01 — ICMJE Recommendations

- Organization: International Committee of Medical Journal Editors
- Version: Updated January 2026
- URL: https://www.icmje.org/icmje-recommendations.pdf
- Used for: authorship criteria, human accountability, AI disclosure, reference
  verification, confidentiality, peer review, reporting guidelines, corrections, and
  data-access expectations.

### SW-S02 — ICMJE January 2026 update notice

- Organization: ICMJE
- Date: January 2026
- URL: https://www.icmje.org/news-and-editorials/updated_recommendations_jan2026.html
- Used for: confirmation that the 2026 update added expanded AI guidance and author
  access-to-data guidance.

### SW-S03 — COPE position on authorship and AI tools

- Organization: Committee on Publication Ethics
- Formal position last reviewed: 2023; current page rechecked 2026-10-01
- URL: https://publicationethics.org/guidance/cope-position/authorship-and-ai-tools
- Used for: AI cannot be an author; authors disclose use and remain responsible.

### SW-S04 — COPE Code of Conduct status

- Organization: COPE
- Version history: current version published 2026-07-21
- URL: https://publicationethics.org/membership/code-of-conduct
- Used for: published Code of Conduct for Members, replacing the retired Core
  Practices, with a 12-month implementation transition from first publication.

### SW-S05 — COPE history of Code and Core Practices

- Organization: COPE
- URL: https://publicationethics.org/about/what-we-do/our-story/history-code-conduct
- Used for: Core Practices retired in 2024; new Code published July 2026 alongside
  Core Principles (2026). Archived practices are not current membership standards.

## Reporting guidelines

### SW-S06 — EQUATOR reporting-guideline library

- Organization: EQUATOR Network
- URL: https://www.equator-network.org/reporting-guidelines/
- Used for: study-type discovery, extensions, translations, and current official links.

### SW-S07 — Joint SPIRIT–CONSORT resource

- Organization: SPIRIT–CONSORT
- Version: CONSORT 2025 and SPIRIT 2025
- URL: https://www.consort-spirit.org/
- Used for: current statements, editable checklists, expanded checklists, flow or
  timeline diagrams, and explanation-and-elaboration resources.

### SW-S08 — CONSORT 2025 statement

- Original statement publication: BMJ
- Date: 2025
- URL: https://www.bmj.com/content/389/bmj-2024-081123
- Used for: current randomized-trial reporting statement and scope.

### SW-S09 — SPIRIT 2025 statement

- Original statement publication: JAMA
- Date: 2025-04-28
- URL: https://jamanetwork.com/journals/jama/fullarticle/2833408
- Used for: current randomized-trial protocol reporting statement and scope.

### SW-S10 — PRISMA 2020

- Organization: PRISMA
- URL: https://www.prisma-statement.org/prisma-2020
- Checklist URL: https://www.prisma-statement.org/prisma-2020-checklist
- Used for: systematic review and meta-analysis reporting.

### SW-S11 — STROBE checklists

- Organization: STROBE Initiative
- Version: original 2007 statement; current official checklist page
- URL: https://www.strobe-statement.org/checklists/
- Used for: cohort, case-control, and cross-sectional study reporting.

### SW-S12 — STARD

- Organization: UK EQUATOR Centre
- Version shown by source: STARD 2015 v1.1
- URL: https://resources.equator-network.org/reporting-guidelines/stard
- Used for: diagnostic-accuracy reporting and the explicit distinction between
  reporting completeness and appraisal of study quality.

### SW-S13 — STARD-AI

- Original consensus statement publication: Nature Medicine
- Date: 2025-09-15; author correction dated 2026-07-13 adds a consortium member
- Correction: https://www.nature.com/articles/s41591-026-04570-9
- URL: https://www.nature.com/articles/s41591-025-03953-8
- Used for: diagnostic-accuracy studies evaluating AI systems.

### SW-S14 — TRIPOD+AI and TRIPOD-LLM

- Organization: TRIPOD
- Versions: TRIPOD+AI 2024; TRIPOD-LLM 2025
- URL: https://www.tripod-statement.org/
- EQUATOR record: https://www.equator-network.org/reporting-guidelines/tripod-statement
- Used for: prediction-model studies using regression or machine learning and the LLM
  extension. The official site states that TRIPOD+AI replaces TRIPOD 2015.

### SW-S15 — CARE

- Organization: CARE
- Version: 2013
- URL: https://www.care-statement.org/checklist
- Used for: case-report reporting and consent-sensitive coverage.

### SW-S16 — ARRIVE 2.0

- Organization: NC3Rs ARRIVE
- Date: 2020
- URL: https://arriveguidelines.org/arrive-guidelines
- Author checklists: https://arriveguidelines.org/resources/author-checklists
- Used for: in vivo animal research, Essential 10, and Recommended Set.

### SW-S17 — SQUIRE 2.0

- Organization: SQUIRE
- Date: 2015
- URL: https://www.squire-statement.org/index.cfm?fuseaction=page.viewPage&pageID=471&nodeID=1
- Used for: healthcare quality-improvement reporting.

### SW-S18 — CHEERS 2022

- Organization: ISPOR
- Date: 2022
- URL: https://www.ispor.org/heor-resources/good-practices/article/consolidated-health-economic-evaluation-reporting-standards-2022-cheers-2022-statement-updated-reporting-guidance-for-health-economic-evaluations
- EQUATOR record: https://www.equator-network.org/reporting-guidelines/cheers/
- Used for: health economic evaluation reporting.

### SW-S31 — CONSORT-AI extension

- Organization: EQUATOR Network record for the CONSORT-AI Working Group
- Date: 2020; EQUATOR record updated 2026-04-04
- URL: https://www.equator-network.org/reporting-guidelines/consort-artificial-intelligence/
- Used for: trial reports evaluating interventions with an AI component.

### SW-S32 — SPIRIT-AI extension

- Organization: EQUATOR Network record for the SPIRIT-AI Working Group
- Date: 2020; EQUATOR record updated 2025-05-30
- URL: https://www.equator-network.org/reporting-guidelines/spirit-artificial-intelligence/
- Used for: pro

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

