---
id: sciref-hypothesis-generation-source-ledger
name: "Scientific Ref: Dated Source Ledger"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (hypothesis-generation): Dated Source Ledger"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "hypothesis generation source ledger"
  - "hipotese generation source ledger"
  - "dated source ledger"
keywords:
  - "hypothesis"
  - "generation"
  - "source"
  - "ledger"
  - "hipotese"
  - "specialized"
  - "scientific"
  - "reference"
  - "dated"
---

# Dated Source Ledger

Latest targeted refresh: **2026-10-01**. The original source review was **2026-07-23**; `verified_on` in the machine-readable ledger records which sources were rechecked. Historical rows keep their original dates rather than implying every full text was reopened.

Machine-readable ledger: `assets/source_ledger.csv`.

## Search boundary

The original review used `parallel-cli`; the October refresh used live official/primary web documentation and indexed primary-source text, focusing on policy replacements, current reporting and preregistration guidance, and Python input semantics. The combined search scope covers:

- NIH rigor, reproducibility, and the 2026 replication initiative;
- Cochrane PICO and the original well-built clinical-question article;
- FINER’s attributed historical source and current interpretation;
- Platt’s original strong-inference essay;
- COS/OSF preregistration and Registered Reports;
- SPIRIT 2025 and CONSORT 2025;
- causal questions, counterfactuals, estimands, and bias;
- negative controls, HARKing, multiplicity, reproducibility, and replication;
- NIST/UNESCO responsible AI and primary evidence on output homogenization;
- human, animal, biosafety, biosecurity, dual-use, data, and regulatory gates.

Searches prioritized official domains and primary publications. Full-text extraction or search excerpts were used to verify titles, dates, versions, and relevant passages. Some publisher/PMC pages returned bot challenges; SPIRIT/CONSORT checklist scope and negative-control guidance were checked against indexed primary-source content. This was a targeted skill refresh, not a systematic review, patent search, or proof of scientific novelty. Source review does not authenticate or submit a registration.

## Core methodology sources

### Question formulation

- `SRC-COCHRANE-PICO` — current Cochrane Handbook Chapter 2. PICO is used for intervention-effect review questions, with objectives defined in advance and stakeholder input where appropriate.
- `SRC-PICO-ORIGINAL` — Richardson et al., 1995, *The well-built clinical question*. Foundational four-part clinical-question article.
- `SRC-FINER-1988` — Hulley and Cummings, *Designing Clinical Research*, first edition metadata (1988). It is the earliest FINER-attributed source located in this refresh.
- `SRC-FINER-CURRENT` — Werner and Willis, 2023, current FINER interpretation.

**Historical limitation:** the available targeted search confirmed the 1988 book’s bibliographic metadata and later attribution but did not establish the exact first printed use or coinage of the FINER mnemonic. The skill therefore does not claim that provenance as proven.

### Multiple hypotheses and falsification

- `SRC-PLATT-1964` — John R. Platt, “Strong Inference,” *Science* 146:347–353, DOI `10.1126/science.146.3642.347`.
- `SRC-NEG-CONTROL` — Lipsitch, Tchetgen Tchetgen, and Cohen, 2010, negative controls for confounding and bias, DOI `10.1097/EDE.0b013e3181d61eeb`.
- `SRC-HARKING` — Kerr, 1998, HARKing, DOI `10.1207/s15327957pspr0203_4`.
- `SRC-ASA-PVALUE` — ASA statement: thresholds alone do not support scientific conclusions; p-values do not measure hypothesis truth or effect importance; full reporting is required.

### Rigor, reproducibility, and replication

- `SRC-NIH-RIGOR` — NIH guidance on scientific premise, rigorous design, relevant biological variables, authentication, and transparency.
- `SRC-NIH-REPLICATION` — NIH’s agency-wide replication and reproducibility initiative, current official page at the NIH beta site; the central hub can change as implementation continues.
- `SRC-NASEM-RR` — National Academies 2019 consensus report defining computational reproducibility and replicability with new data.
- `SRC-TOP` — original 2015 Transparency and Openness Promotion article, retained as historical background.
- `SRC-TOP-2025` — current COS TOP 2025 framework: distinct research practices, implementation levels, and independent verification; apply the adopting journal/funder's policy.
- `SRC-NIH-DMS` — NIH Data Management and Sharing Policy.

Open practices remain subject to consent, privacy, community governance, intellectual property, export control, and security restrictions.

## Preregistration and intervention trials

- `SRC-COS-PREREG` — preregistration separates planned from unplanned work; transparent exploration remains valuable.
- `SRC-OSF-REG` — current OSF registration/preregistration implementation guidance, including justified registration updates; attached files cannot be added or removed during an update. The local scaffold is not an OSF submission.
- `SRC-COS-RR` — Registered Reports and results-blind protocol review.
- `SRC-SPIRIT-2025` — current 34-item randomized-trial protocol guideline; supersedes SPIRIT 2013.
- `SRC-CONSORT-2025` — current 30-item randomized-trial result-reporting guideline, including open science, harms, outcomes, intervention details, and important changes.

SPIRIT and CONSORT are reporting guidelines, not design-quality, ethics, regulatory, or efficacy certifications.

## Causal inference and estimands

- `SRC-WHATIF` — Hernán and Robins, *Causal Inference: What If*. Use the author page's latest-version link; the authors state that online revisions may not be individually documented, so do not infer a fixed current revision from an older filename.
- `SRC-ICH-E9R1` — ICH E9(R1), defining the estimand as the precise treatment-effect target and aligning planning, design, analysis, sensitivity analysis, and interpretation.

These sources ground the distinctions among target causal contrast, estimator, and estimate, and the explicit treatment of confounding, selection, collider, measurement, and intervention-definition assumptions.

## Responsible AI

- `SRC-NIST-GENAI` — NIST AI 600-1, covering confabulation, privacy, harmful bias/homogenization, information integrity, dangerous recommendations, and human–AI configuration.
- `SRC-UNESCO-AI` — human rights, privacy, accountability, transparency, diversity, and human oversight.
- `SRC-DOSHI-HAUSER` — Doshi and Hauser, 2024, DOI `10.1126/sciadv.adn5290`. In the studied story-writing task, AI-assisted outputs were more similar to one another while some individual creativity measures improved.

The primary homogenization result is task-specific. The skill treats idea homogenization as a plausible risk, not a universal measured effect across scientific domains.

## Ethics and oversight

### Humans

- `SRC-HHS-COMMON-RULE

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

