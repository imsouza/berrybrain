---
id: sciref-peer-review-statistical-reproducibility
name: "Scientific Ref: Statistical, Methods, and Reproducibility Review"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (peer-review): Statistical, Methods, and Reproducibility Review"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "peer review statistical reproducibility"
  - "peer revisao estatistica reproducibility"
  - "statistical, methods, and reproducibility review"
keywords:
  - "peer"
  - "review"
  - "statistical"
  - "reproducibility"
  - "revisao"
  - "estatistica"
  - "specialized"
  - "scientific"
  - "reference"
---

# Statistical, Methods, and Reproducibility Review

This guide supports structured questions; it does not replace a statistician, methodologist, domain expert, or independent reanalysis. Sources reviewed on **2026-10-01**, with source-specific verification limits, are recorded in `assets/source_ledger.csv`.

## Evidence hierarchy for the review

Use, in order:

1. The stated research question and target population
2. Protocol, registration, analysis plan, and amendments
3. Reported design and data-generating process
4. Methods, code, tables, figures, supplements, and repository records
5. Applicable primary method or regulatory guidance
6. Current reporting guidance
7. Target venue policy

Do not reject a method merely because another method is more familiar. Explain the estimand, assumption, error, or interpretation at stake.

## Core review sequence

### 1. Define what is being estimated

Write down:

- Unit of inference
- Population
- Intervention, exposure, test, or predictors
- Comparator or reference condition
- Outcome and time horizon
- Target effect, association, accuracy, or predictive performance
- Intercurrent events, censoring, and missing observations where relevant

Then trace whether design, data collection, analysis, result, and claim target the same quantity.

For applicable clinical trials, ICH E9(R1) provides a framework for estimands and sensitivity analyses. It is not a universal rule for every study.

### 2. Reconstruct the design

Identify:

- Prospective, retrospective, cross-sectional, longitudinal, experimental, or observational structure
- Recruitment or sampling frame
- Experimental/observational unit
- Pairing, nesting, clustering, repeated measures, sites, batches, and time
- Allocation, concealment, blinding, matching, or weighting
- Primary and secondary outcomes
- Prespecified versus exploratory analyses

If the design cannot be reconstructed, first request missing reporting. Do not label the design invalid solely because details are absent.

### 3. Trace every denominator

Reconcile:

- Eligible, enrolled, assigned, treated/exposed, followed, measured, and analyzed units
- Outcome-specific denominators
- Exclusions before and after allocation or measurement
- Missing values and reasons
- Complete-case, imputed, weighted, or model-based analysis populations
- Figure, table, abstract, text, and supplement totals

Report the exact mismatch and locations; do not infer why counts differ.

### 4. Assess analysis–design alignment

Ask whether the method accounts for:

- Outcome scale and distribution
- Pairing and repeated measures
- Clustering and multilevel structure
- Unequal follow-up, censoring, or competing events
- Sampling weights or matched designs
- Baseline adjustment and prespecified covariates
- Multiplicity and outcome hierarchy
- Model tuning and validation
- Missingness assumptions

The name of a statistical test is not enough. The report should state inputs, model form, uncertainty method, software/version, and relevant diagnostics.

### 5. Assess estimates and interpretation

Prefer:

- Effect or performance estimates with units
- Compatible uncertainty intervals
- Absolute as well as relative quantities when decision-relevant
- Exact denominators and analysis sets
- Assumption and sensitivity context
- Clinical, biological, policy, or practical relevance distinct from statistical compatibility

The ASA’s six p-value principles include:

- A p-value is about incompatibility with a specified model, not the probability a hypothesis is true.
- Threshold crossing alone should not determine scientific conclusions.
- Transparent reporting of all relevant analyses is required.
- Statistical significance does not measure effect size or importance.
- A p-value alone is not a good measure of evidence.

SAMPL provides concise biomedical statistical reporting guidance. Apply it as reporting guidance, not a universal analysis recipe.

## Topic-specific checks

### Sample size and precision

Look for:

- Prospective calculation or precision rationale
- Target effect or interval width
- Variance, event rate, prevalence, or accuracy assumptions
- Type I error, power, sidedness, and multiplicity when applicable
- Design effect, clustering, attrition, noncompliance, and missingness
- Model complexity and effective sample size
- Simulation details for complex designs

Do not request observed/post hoc power as a remedy for an imprecise result. Examine the estimate and uncertainty.

### Randomized trials

Check:

- Allocation sequence and concealment
- Prespecified estimand and analysis population
- Protocol/registry/outcome consistency
- Baseline adjustment and stratification factors
- Intercurrent events, adherence, treatment switching, and missing data
- Harms and unintended effects
- Sensitivity and supplementary analyses
- Non-inferiority/equivalence margin and interpretation if relevant

Use CONSORT 2025 and SPIRIT 2025 for reporting. Use ICH E9/E9(R1) only when its scope and decision context fit.

### Observational causal analyses

Check:

- Causal question and target contrast
- Time zero, eligibility, treatment/exposure assignment, follow-up, and outcome timing
- Confounder rationale and measurement timing
- Positivity/overlap
- Exchangeability and consistency assumptions
- Missingness, censoring, selection, and measurement error
- Model specification and balance diagnostics
- Sensitivity to unmeasured confounding or alternative specifications

Avoid judging causal identification from adjusted versus unadjusted p-values.

### Diagnostic accuracy

Check:

- Intended use, setting, and participant spectrum
- Index test and reference standard
- Threshold prespecification
- Blinding and timing
- Indeterminate/missing results
- Verification and incorporation bias
- Two-by-two denominators and uncertainty
- External applicability

STARD/STARD-AI describe reporting; use an appropriate risk-of-bias framework separately.

### Prediction models

Check:

- Intended use, prediction time, outcome, and target population
- Data source and participant flow
- Predictor availability at intended use
- Missing-data and preprocessing leakage
- Sample size relative to outcome information and complexity
- Internal validation and optimism correction
- Independent evaluation and dataset shift
- Calibration, discrimination, decision utility, and uncertainty
- Hyperparameter tuning separated from evaluation
- Reproducible model specification and preprocessing
- Subgroup pe

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

