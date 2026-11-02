---
id: sciref-hypothesis-generation-experimental-design-patterns
name: "Scientific Ref: Design Patterns for Discriminating Tests"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (hypothesis-generation): Design Patterns for Discriminating Tests"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "hypothesis generation experimental design patterns"
  - "hipotese generation experimental design patterns"
  - "design patterns for discriminating tests"
keywords:
  - "hypothesis"
  - "generation"
  - "experimental"
  - "design"
  - "patterns"
  - "hipotese"
  - "specialized"
  - "scientific"
  - "reference"
---

# Design Patterns for Discriminating Tests

## Design starts from the prediction

For each test, link:

`candidate → mechanism → prediction → observable → operationalization → design → analysis → interpretation`

Choose the design that can distinguish candidates under realistic uncertainty. Do not select a design merely because it is familiar or available.

## NIH-aligned rigor questions

Where applicable, address:

- rigor of the prior research forming the scientific premise;
- unbiased and well-controlled design;
- relevant biological variables such as sex, age, weight, or health condition;
- authentication and validity of key biological/chemical resources;
- transparent methods, analysis, interpretation, and reporting.

Apply only the elements relevant to the science and explain omissions.

## Core design record

Every design should state:

- study system and target population;
- experimental/observational unit and analysis unit;
- sampling frame and recruitment/selection;
- interventions/exposures and comparator versions;
- allocation, randomization, concealment, and masking;
- outcomes, timing, measurement IDs, and quality control;
- positive, negative, vehicle/sham, procedural, or reference controls as applicable;
- inclusion, exclusion, attrition, and stopping;
- sample-size, precision, or information rationale;
- analysis IDs and estimands;
- safety, ethics, feasibility, data, and regulatory gates;
- replication, transport, and external-validation plan.

## Experimental designs

### Randomized intervention

Useful for causal contrasts when intervention, allocation, and ethics permit.

Check:

- allocation sequence and concealment;
- intervention versions, adherence, contamination, and co-interventions;
- masking of participants, providers, outcome assessors, and analysts where feasible;
- primary estimand and intercurrent events;
- intention-to-treat or other analysis population aligned to the estimand;
- harms, stopping, missing outcomes, and protocol deviations.

Randomization does not solve measurement bias, nonadherence, post-randomization selection, interference, or poor external validity.

### Factorial design

Useful for multiple interventions and interactions.

Check:

- scientific meaning and scale of interaction;
- power/precision for interactions, not only main effects;
- compatibility and safety of combined conditions;
- multiplicity and hierarchy;
- whether sparse combinations undermine interpretation.

### Within-unit or crossover design

Useful when effects are reversible and carryover can be controlled.

Check:

- period and sequence effects;
- washout rationale;
- time trends and learning;
- missing periods;
- whether the condition is stable and intervention reversible.

### Perturbation and rescue

Useful for mechanistic candidates when ethically and technically appropriate.

Check:

- perturbation specificity and off-target effects;
- manipulation check;
- rescue interpretation and overexpression artifacts;
- temporal order;
- orthogonal perturbations and measurements;
- relevant negative and positive controls.

A rescue can still be explained by compensatory or non-specific effects.

### Time-course

Useful when candidates predict different ordering or dynamics.

Check:

- sampling times justified by expected process;
- independent versus repeated units;
- baseline and pre-trend;
- measurement stability across time;
- multiple looks and timepoint multiplicity;
- lag, feedback, and reverse causation.

## Observational designs

### Cross-sectional

Can estimate prevalence and associations at a defined time. It usually cannot establish temporal direction. Explicitly consider selection, reverse causation, survival/prevalence bias, and common-method measurement.

### Cohort/longitudinal

Can establish measured temporal ordering and incidence. It does not eliminate confounding.

Check:

- time zero and eligibility;
- exposure updates and time-varying confounding;
- loss to follow-up and informative censoring;
- competing events;
- immortal-time and delayed-entry risks;
- outcome ascertainment changes.

### Case-control

Efficient for some rare outcomes.

Check:

- source population and control sampling;
- matching implications;
- exposure measurement and recall;
- selection mechanisms;
- correct effect measure and sampling analysis.

### Natural/quasi-experimental

Can strengthen causal identification when an assignment mechanism or discontinuity is credible.

Check:

- assignment mechanism and manipulation;
- continuity, parallel trends, exclusion, or instrument assumptions as applicable;
- anticipation and spillovers;
- bandwidth/window choices;
- placebo/negative-control tests;
- sensitivity to specification and clustering.

The design label alone does not establish identification.

## Computational and theoretical designs

### Simulation

Use to test implications of assumptions, estimator behavior, or model dynamics.

Record:

- data-generating process and parameter ranges;
- rationale for scenarios;
- seeds and software versions;
- performance targets and uncertainty;
- failure cases and sensitivity;
- separation between simulated truth and empirical validity.

Simulation can show consequences within a model, not that the model describes nature.

### Predictive model evaluation

Separate prediction from causation.

Check:

- target population, outcome, time origin, and horizon;
- leakage and preprocessing;
- train/tune/test independence;
- calibration and discrimination;
- uncertainty and subgroup performance;
- temporal/geographic/external validation;
- dataset shift and update policy.

### Secondary-data analysis

Record provenance, data-generating process, inclusion, missingness, transformations, version, and prior analysis exposure. Avoid using the same data to generate and confirm a hypothesis without transparent separation or independent validation.

## Controls

### Positive control

A condition expected to produce a known response. It checks whether the system and measurement can detect a relevant effect.

### Procedural control

Matches handling, timing, delivery, or processing without the target active component.

### Negative control

Should not operate through the target mechanism but should share relevant bias pathways. State assumptions and failure interpretation.

### Null comparator

A comparator representing no intervention or no difference may be useful, but it is not equivalent to a negative control and may not isolate placebo, hand

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

