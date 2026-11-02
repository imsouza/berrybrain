---
id: sciref-scientific-critical-thinking-experimental-design
name: "Scientific Ref: Experimental Design Checklist"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (scientific-critical-thinking): Experimental Design Checklist"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "scientific critical thinking experimental design"
  - "cientifico critica pensamento experimental design"
  - "experimental design checklist"
keywords:
  - "scientific"
  - "critical"
  - "thinking"
  - "experimental"
  - "design"
  - "cientifico"
  - "critica"
  - "pensamento"
  - "specialized"
  - "reference"
---

# Experimental Design Checklist

Apply items to the actual design rather than treating checked boxes as a quality score.
Framework versions and primary guidance: [review_sources.md](review_sources.md).

## Research Question Formulation

### Is the Question Well-Formed?
- [ ] **Specific:** Clearly defined variables and relationships
- [ ] **Answerable:** Can be addressed with available methods
- [ ] **Relevant:** Addresses a gap in knowledge or practical need
- [ ] **Feasible:** Resources, time, and ethical considerations allow it
- [ ] **Falsifiable:** Can be proven wrong if incorrect

### Have You Reviewed the Literature?
- [ ] Identified what's already known
- [ ] Found gaps or contradictions to address
- [ ] Learned from methodological successes and failures
- [ ] Identified appropriate outcome measures
- [ ] Determined typical effect sizes in the field

## Hypothesis Development

### Is Your Hypothesis Testable?
- [ ] Makes specific, quantifiable predictions
- [ ] Variables are operationally defined
- [ ] Specifies direction/nature of expected relationships
- [ ] Can be falsified by potential observations

### Types of Hypotheses
- [ ] **Null hypothesis (H₀):** Explicit value or range, including any non-inferiority margin
- [ ] **Alternative hypothesis (H₁):** Explicit competing value, range, or direction
- [ ] **Directional vs. non-directional:** One-tailed vs. two-tailed tests

## Study Design Selection

### What Type of Study is Appropriate?

**Experimental (Intervention) Studies:**
- [ ] **Randomized Controlled Trial (RCT):** Strong intervention-effect design when conduct
  and analysis preserve its identifying assumptions
- [ ] **Quasi-experimental:** Non-random assignment but manipulation
- [ ] **Within-subjects:** Same participants in all conditions
- [ ] **Between-subjects:** Different participants per condition
- [ ] **Factorial:** Multiple independent variables
- [ ] **Crossover:** Participants receive multiple interventions sequentially

**Observational Studies:**
- [ ] **Cohort:** Follow groups over time
- [ ] **Case-control:** Compare those with/without outcome
- [ ] **Cross-sectional:** Snapshot at one time point
- [ ] **Ecological:** Population-level data

**Consider:**
- [ ] Can you randomly assign participants?
- [ ] Can you manipulate the independent variable?
- [ ] Is the outcome rare (favor case-control) or common?
- [ ] Do you need to establish temporal sequence?
- [ ] What's feasible given ethical, practical constraints?

## Variables

### Independent Variables (Manipulated/Predictor)
- [ ] Clearly defined and operationalized
- [ ] Appropriate levels/categories chosen
- [ ] Manipulation is sufficient to test hypothesis
- [ ] Manipulation check planned (if applicable)

### Dependent Variables (Outcome/Response)
- [ ] Directly measures the construct of interest
- [ ] Validated and reliable measurement
- [ ] Sensitive enough to detect expected effects
- [ ] Appropriate for statistical analysis planned
- [ ] Primary outcome clearly designated

### Control Variables
- [ ] **Confounding variables identified:**
  - Variables that affect both IV and DV
  - Alternative explanations for findings
- [ ] **Strategy for control:**
  - Randomization
  - Matching
  - Stratification
  - Statistical adjustment
  - Restriction (inclusion/exclusion criteria)
  - Avoid conditioning on mediators/colliders unless required by the target estimand

### Extraneous Variables
- [ ] Potential sources of noise identified
- [ ] Standardized procedures to minimize
- [ ] Environmental factors controlled
- [ ] Time of day, setting, equipment standardized

## Sampling

### Population Definition
- [ ] **Target population:** Who you want to generalize to
- [ ] **Accessible population:** Who you can actually sample from
- [ ] **Sample:** Who actually participates
- [ ] Difference between these documented

### Sampling Method
- [ ] **Probability sampling (preferred for generalizability):**
  - Simple random sampling
  - Stratified sampling
  - Cluster sampling
  - Systematic sampling
- [ ] **Non-probability sampling (common but limits generalizability):**
  - Convenience sampling
  - Purposive sampling
  - Snowball sampling
  - Quota sampling

### Sample Size
- [ ] Experimental/sampling unit and independent replicate count stated (animal, donor,
  litter, cage, site, culture, etc.); repeated measurements do not increase independent n
- [ ] **A priori power analysis conducted**
  - Scientifically meaningful effect and plausible variability, with sensitivity analysis
  - Justified power or precision target (.80/.90 are conventions, not universal requirements)
  - Significance level (typically .05)
  - Statistical test to be used
- [ ] Accounts for expected attrition/dropout
- [ ] Accounts for clustering, repeated measures, and planned multiplicity
- [ ] Sufficient for planned subgroup analyses
- [ ] Practical constraints acknowledged

### Inclusion/Exclusion Criteria
- [ ] Clearly defined and justified
- [ ] Not overly restrictive (limits generalizability)
- [ ] Based on theoretical or practical considerations
- [ ] Ethical considerations addressed
- [ ] Documented and applied consistently

## Blinding and Randomization

### Randomization
- [ ] **What is randomized:**
  - Participant assignment to conditions
  - Order of conditions (within-subjects)
  - Stimuli/items presented
- [ ] **Method of randomization:**
  - Computer-generated random numbers
  - Random number tables
  - Coin flips (for very small studies)
- [ ] **Allocation concealment:**
  - Sequence generated before recruitment
  - Allocation hidden until after enrollment
  - Secure centralized allocation, or sequentially numbered opaque sealed envelopes
    with safeguards preventing anticipation or tampering
- [ ] **Stratified randomization:**
  - Balance important variables across groups
  - Block randomization to ensure equal group sizes
- [ ] **Check randomization:**
  - Audit sequence generation and concealment; describe baseline characteristics
  - Do not use baseline significance tests as proof of successful/failed randomization

### Blinding
- [ ] Name who was blinded (participants, providers, assessors, analysts), to what, and
  how; single/double/triple-blind labels have inconsistent meanings
- [ ] **Blinding feasibility:**
  - Is true blinding possible?
  - Placebo/sham controls needed?
  - Identical appearance of interventions?
- [ ] **Blinding check:**
  - Document unblinding and its likely effect on this outcome
  - Ass

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

