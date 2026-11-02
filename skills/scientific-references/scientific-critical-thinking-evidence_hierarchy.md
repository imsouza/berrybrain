---
id: sciref-scientific-critical-thinking-evidence-hierarchy
name: "Scientific Ref: Evidence Hierarchy and Quality Assessment"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (scientific-critical-thinking): Evidence Hierarchy and Quality Assessment"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "scientific critical thinking evidence hierarchy"
  - "cientifico critica pensamento evidence hierarchy"
  - "evidence hierarchy and quality assessment"
keywords:
  - "scientific"
  - "critical"
  - "thinking"
  - "evidence"
  - "hierarchy"
  - "cientifico"
  - "critica"
  - "pensamento"
  - "specialized"
  - "reference"
---

# Evidence Hierarchy and Quality Assessment

## Traditional Evidence Hierarchy (Medical/Clinical)

This is a teaching shorthand for some intervention questions, not a universal ranking.
Choose designs for the question: prevalence, prognosis, diagnostic accuracy, harms, and
mechanisms have different evidence needs. A review synthesizes its underlying studies;
meta-analysis alone does not increase certainty. Reporting quality, risk of bias,
applicability, and certainty must be assessed separately. Current sources are recorded in
[review_sources.md](review_sources.md).

### Level 1: Systematic Reviews and Meta-Analyses
**Description:** Comprehensive synthesis of all available evidence on a question.

**Strengths:**
- Combines multiple studies for greater power
- Reduces impact of single-study anomalies
- Can identify patterns across studies
- May quantify a pooled effect if studies and estimands can meaningfully be combined

**Weaknesses:**
- Quality depends on included studies ("garbage in, garbage out")
- Publication bias can distort findings
- Heterogeneity may make pooling inappropriate
- Can mask important differences between studies

**Critical evaluation:**
- Was search comprehensive (multiple databases, grey literature)?
- Were inclusion criteria appropriate and prespecified?
- Was study quality assessed?
- Was heterogeneity explored?
- Were missing studies/results sought in registries and protocols? If funnel-plot methods
  were appropriate, were alternative explanations for asymmetry considered? Fail-safe N
  is not a reliable assessment of missing-evidence bias.
- Were appropriate statistical methods used?

### Level 2: Randomized Controlled Trials (RCTs)
**Description:** Experimental studies with random assignment to conditions.

**Strengths:**
- Strong design for estimating intervention effects when implemented and analysed appropriately
- Balances prognostic factors in expectation, not necessarily in each realized sample
- Minimizes selection bias
- Enables causal inference

**Weaknesses:**
- May not be ethical or feasible
- Artificial settings may limit generalizability
- Often short-term with selected populations
- Expensive and time-consuming

**Critical evaluation:**
- Was randomization adequate (sequence generation, allocation concealment)?
- Was blinding implemented (participants, providers, assessors)?
- Was sample size adequate (power analysis)?
- Was intention-to-treat analysis used?
- Was attrition rate acceptable and balanced?
- Are results generalizable?

### Level 3: Cohort Studies
**Description:** Observational studies following groups over time.

**Types:**
- **Prospective:** Follow forward from exposure to outcome
- **Retrospective:** Look backward at existing data

**Strengths:**
- Can study multiple outcomes
- Establishes temporal sequence
- Can calculate incidence and relative risk
- More feasible than RCTs for many questions

**Weaknesses:**
- Susceptible to confounding
- Selection bias possible
- Attrition can bias results
- Causal interpretation requires explicit identification assumptions and sensitivity analysis

**Critical evaluation:**
- Were cohorts comparable at baseline?
- Was exposure measured reliably?
- Was follow-up adequate and complete?
- Were potential confounders measured and controlled?
- Was outcome assessment blinded to exposure?

### Level 4: Case-Control Studies
**Description:** Compare people with outcome (cases) to those without (controls), looking back at exposures.

**Strengths:**
- Efficient for rare outcomes
- Relatively quick and inexpensive
- Can study multiple exposures
- Useful for generating hypotheses

**Weaknesses:**
- Usually cannot estimate absolute incidence from sampled case/control counts alone
- Susceptible to recall bias
- Selection of controls is challenging
- Causal interpretation depends on the sampling design and control of relevant biases

**Critical evaluation:**
- Were cases and controls defined clearly?
- Were controls appropriate (same source population)?
- Was matching appropriate?
- How was exposure ascertained (records vs. recall)?
- Were potential confounders controlled?
- Could recall bias explain findings?

### Level 5: Cross-Sectional Studies
**Description:** Snapshot observation at single point in time.

**Strengths:**
- Quick and inexpensive
- Can assess prevalence
- Useful for hypothesis generation
- Can study multiple outcomes and exposures

**Weaknesses:**
- Cannot establish temporal sequence
- Cannot determine causation
- Prevalence-incidence bias
- Survival bias

**Critical evaluation:**
- Was sample representative?
- Were measures validated?
- Could reverse causation explain findings?
- Are confounders acknowledged?

### Level 6: Case Series and Case Reports
**Description:** Description of observations in clinical practice.

**Strengths:**
- Can identify new diseases or effects
- Hypothesis-generating
- Details rare phenomena
- Quick to report

**Weaknesses:**
- No control group
- Descriptive uncertainty may be estimable; uncontrolled counts do not identify a comparative effect
- Highly susceptible to bias
- Cannot establish causation or frequency

**Use:** Primarily for hypothesis generation and clinical description.

### Level 7: Expert Opinion
**Description:** Statements by recognized authorities.

**Strengths:**
- Synthesizes experience
- Useful when no research available
- May integrate multiple sources

**Weaknesses:**
- Subjective and potentially biased
- May not reflect current evidence
- Appeal to authority fallacy risk
- Individual expertise varies

**Use:** Lowest level of evidence; should be supported by data when possible.

## Nuances and Limitations of Traditional Hierarchy

### When Lower-Level Evidence Can Be Strong
1. **Well-designed observational studies** with:
   - Large effects that plausible bias cannot explain (size alone does not establish this)
   - Dose-response relationships
   - Consistent findings across contexts
   - Biological plausibility
   - Explicitly justified confounding and selection assumptions, with sensitivity analyses

2. **Multiple converging lines of evidence** from different study types

3. **Natural experiments** approximating randomization

### When Higher-Level Evidence Can Be Weak
1. **Poor-quality RCTs** with:
   - Inadequate randomization
   - High attrition
   - No blinding when feasible
   - Design, conduct, or reporting problems associated with sponsor influence

2. **Biased meta-analyses**:
   - Publication bias
   - Selective i

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

