---
id: sciref-peer-review-common-issues
name: "Scientific Ref: Common Issues in Manuscript Review"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (peer-review): Common Issues in Manuscript Review"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "peer review common issues"
  - "peer revisao common issues"
  - "common issues in manuscript review"
keywords:
  - "peer"
  - "review"
  - "common"
  - "issues"
  - "revisao"
  - "specialized"
  - "scientific"
  - "reference"
---

# Common Issues in Manuscript Review

Use this reference as a prompt for inquiry, not a defect checklist. A possible issue becomes a review comment only when it is relevant to the study and supported by a manuscript location, supplied artifact, or applicable method principle.

Do not infer misconduct, poor quality, or manuscript merit from a missing reporting item. Separate:

- **Not reported:** the manuscript does not provide enough information to assess the point.
- **Potential design or analysis problem:** the reported method may not answer the stated question.
- **Demonstrated inconsistency:** two supplied artifacts or manuscript locations conflict.
- **Integrity concern:** credible evidence should be described neutrally and routed through the journal process, normally in confidential editor notes.

## Claim–evidence alignment

Check each central claim against the design, analysis, result, and uncertainty that support it.

Common mismatches:

- Causal wording from an observational or otherwise non-identifying design
- Mechanistic conclusions supported only by association or prediction
- Conclusions based on a secondary, exploratory, or post hoc outcome without labeling
- Directionally correct claims that overstate magnitude or precision
- Population, setting, intervention, comparator, outcome, or time-horizon extrapolation
- “No effect,” “equivalent,” or “safe” conclusions from imprecise or non-significant results
- Abstract or conclusion claims that omit material harms, uncertainty, subgroup caveats, or null findings
- Novelty claims that are broader than the search or cited literature supports

Constructive response:

1. Identify the claim and its location.
2. Identify the relevant result or missing evidence.
3. Explain the alignment problem.
4. Request a bounded remedy: narrow wording, add uncertainty, clarify exploratory status, provide the prespecified analysis, or justify the inference.

Use `scripts/validate_claim_evidence.py` for a local identifier-based matrix. Its report never echoes claim text.

## Study question, design, and units

### Question–design mismatch

Check whether the population, intervention or exposure, comparator, outcomes, timing, and target quantity align from objectives through interpretation. For trials, identify the estimand when relevant. For prediction, distinguish model development from performance evaluation. For diagnostic studies, distinguish diagnostic accuracy from clinical utility.

### Experimental or observational unit

Potential issues include:

- Technical replicates treated as independent biological units
- Multiple cells, images, lesions, eyes, visits, or samples per subject analyzed as independent
- Cluster assignment analyzed at the individual level without accounting for clustering
- Paired or repeated observations analyzed as unpaired
- Site, operator, batch, family, spatial, or temporal dependence ignored

Request a clear definition of the unit, nesting, repeated measures, and analysis that reflects dependence. Do not assume a mixed model is always the correct remedy; the model must match the design and question.

### Selection, allocation, and masking

Assess, as applicable:

- Sampling frame, recruitment, eligibility, and exclusions
- Sequence generation and allocation concealment
- Prospective stopping rules
- Blinding or masking of participants, personnel, outcome assessors, and analysts
- Consequences and mitigation when masking is infeasible
- Baseline measurement timing and post-allocation exclusions

Avoid treating baseline significance tests as proof of successful randomization. Focus on chance imbalance, clinically important imbalance, prespecified adjustment, and departures from the randomized comparison.

### Confounding and causal identification

For causal claims, ask:

- What target causal contrast is intended?
- Which assumptions connect the design and analysis to that contrast?
- Were confounders selected using subject-matter reasoning rather than outcome-driven screening?
- Could adjustment introduce collider or mediator bias?
- Are time-varying treatment, censoring, immortal time, or informative observation processes relevant?
- Are negative controls, sensitivity analyses, or alternative explanations appropriate?

Do not demand a specific causal method without showing why it fits the data-generating process.

## Sample size, precision, and replication

Avoid fixed heuristics such as “n < 30 is too small” or “three replicates are sufficient.” Adequacy depends on the target effect or precision, variability, design effect, event count, model complexity, multiplicity, attrition, and decision context.

Check:

- Prospective rationale for sample size or precision
- Inputs, assumptions, software or method, and allowance for attrition or clustering
- Whether the primary outcome and analysis match the calculation
- Event and outcome information relative to model complexity
- Effective sample size after dependence, missingness, weighting, or splitting
- Independent biological replication and validation where the claim requires it
- Precision of estimates, not only nominal power

Observed or post hoc power calculated from the observed effect generally adds little beyond the estimate and its interval. Request effect estimates and uncertainty rather than “achieved power.”

## Statistical analysis

### Analysis–design alignment

Check whether the analysis respects:

- Outcome scale and distribution
- Pairing, clustering, repeated measures, censoring, and competing events
- Sampling design, weights, matching, stratification, or blocking
- Outcome hierarchy and prespecified estimand
- Non-inferiority or equivalence margins and analysis populations
- Longitudinal timing and informative dropout

Do not prescribe “parametric” or “non-parametric” methods from sample size alone.

### Assumptions and diagnostics

The relevant assumptions depend on the estimand and model. A standalone normality test is not a universal gatekeeper and can be uninformative in very small or large samples. Look for design-aware diagnostics, residual behavior, influential observations, functional form, calibration, proportional hazards where applicable, and sensitivity to reasonable alternatives.

Comments should identify the assumption at risk and why it matters. “Check normality” without specifying the modeled quantity or consequence is not actionable.

### Effect estimates and uncertainty

Flag:

- Thresholded interpretation of p-values
- P-values

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

