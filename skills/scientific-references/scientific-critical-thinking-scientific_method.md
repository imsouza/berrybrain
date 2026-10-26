---
id: sciref-scientific-critical-thinking-scientific-method
name: "Scientific Ref: Scientific Method Core Principles"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (scientific-critical-thinking): Scientific Method Core Principles"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "scientific critical thinking scientific method"
  - "cientifico critica pensamento cientifico method"
  - "scientific method core principles"
keywords:
  - "scientific"
  - "critical"
  - "thinking"
  - "method"
  - "cientifico"
  - "critica"
  - "pensamento"
  - "specialized"
  - "reference"
---

# Scientific Method Core Principles

Use these principles as appraisal prompts. They are not an algorithm that proves a claim
or substitutes for design-specific methods; see [review_sources.md](review_sources.md).

## Fundamental Principles

### 1. Empiricism
- Knowledge derives from observable, measurable evidence
- Claims must be testable through observation or experiment
- Subjective experience alone is insufficient for scientific conclusions

### 2. Falsifiability (Popper's Criterion)
- A hypothesis should expose itself to observations inconsistent with its predictions;
  statistical hypotheses require probabilistic evaluation, not one decisive contrary datum
- Unfalsifiable claims are not scientific (e.g., "invisible, undetectable forces")
- Good hypotheses make specific, testable predictions

### 3. Reproducibility and Replication
- Distinguish reproducing computations with the same data/code from testing findings
  in new independent data; report the terminology used in the field
- Describe methods, data provenance, code, and environments sufficiently for checking
- Single studies are rarely definitive; replication strengthens confidence

### 4. Parsimony (Occam's Razor)
- Prefer simpler explanations over complex ones when both fit the data
- Don't multiply entities unnecessarily
- Extraordinary claims require extraordinary evidence

### 5. Systematic Observation
- Use standardized, rigorous methods
- Control for confounding variables
- Minimize observer bias through blinding and protocols

## The Scientific Process

### 1. Question Formation
- Identify a specific, answerable question
- Ensure the question is within the scope of scientific inquiry
- Consider whether current methods can address the question

### 2. Literature Review
- Survey existing knowledge
- Identify gaps and contradictions
- Build on previous work rather than reinventing

### 3. Hypothesis Development
- State a clear, testable prediction
- Define variables operationally
- Specify the expected relationship between variables

### 4. Experimental Design
- Choose appropriate methodology
- Identify independent and dependent variables
- Control confounding variables
- Select appropriate sample size and population
- Plan statistical analyses in advance

### 5. Data Collection
- Follow protocols consistently
- Record all observations, including unexpected results
- Maintain detailed lab notebooks or data logs
- Use validated measurement instruments

### 6. Analysis
- Apply appropriate statistical methods
- Test assumptions of statistical tests
- Consider effect size, not just significance
- Look for alternative explanations

### 7. Interpretation
- Distinguish between correlation and causation
- Acknowledge limitations
- Consider alternative interpretations
- Avoid overgeneralizing beyond the data

### 8. Communication
- Report methods transparently
- Include negative results
- Acknowledge conflicts of interest
- Make data and code available when possible

## Critical Evaluation Criteria

### When Reviewing Scientific Work, Ask:

**Validity Questions:**
- Does the study measure what it claims to measure?
- Are the methods appropriate for the research question?
- Were controls adequate?
- Could confounding variables explain the results?

**Reliability Questions:**
- Are measurements consistent?
- Would the study produce similar results if repeated?
- Are inter-rater reliability and measurement precision reported?

**Generalizability Questions:**
- Is the sample representative of the target population?
- Are the conditions realistic or artificial?
- Do the results apply beyond the specific context?

**Statistical Questions:**
- Is the sample size adequate for the analysis?
- Are the statistical tests appropriate?
- Are effect sizes reported alongside p-values?
- Were multiple comparisons corrected?

**Logical Questions:**
- Do the conclusions follow from the data?
- Are alternative explanations considered?
- Are causal claims supported by the study design?
- Are limitations acknowledged?

## Red Flags in Scientific Claims

1. **Cherry-picking data** - Highlighting only supporting evidence
2. **Moving goalposts** - Changing predictions after seeing results
3. **Ad hoc hypotheses** - Adding explanations to rescue a failed prediction
4. **Appeal to authority** - "Expert X says" without evidence
5. **Anecdotal evidence** - Relying on personal stories over systematic data
6. **Correlation implies causation** - Confusing association with causality
7. **Post hoc rationalization** - Explaining results after the fact without prediction
8. **Ignoring base rates** - Not considering prior probability
9. **Confirmation bias** - Seeking only evidence that supports beliefs
10. **Publication bias** - Only positive results get published

## Standards for Causal Inference

### Bradford Hill Viewpoints (adapted)
These are considerations, not necessary-and-sufficient criteria or a points score.
Weak associations can be causal; strong ones can arise from bias, and specificity is
not required. Mechanistic plausibility changes with knowledge.

1. **Strength** - Assess association size against plausible bias explanations
2. **Consistency** - Repeated observations by different researchers
3. **Specificity** - Specific outcomes from specific causes
4. **Temporality** - Cause precedes effect (essential)
5. **Biological gradient** - Dose-response relationship
6. **Plausibility** - Coherent with existing knowledge
7. **Coherence** - Consistent with other evidence
8. **Experiment** - Experimental evidence supports causation
9. **Analogy** - Similar cause-effect relationships exist

### Appraising a Causal Estimate
- Define the intervention/exposure contrast, eligible population, time zero, follow-up,
  outcome, and effect measure; association, prediction, and causation are distinct targets.
- State assumptions that identify that target from the data: consistency, exchangeability,
  positivity, appropriate handling of selection/missingness, and interference when relevant.
- Use a causal diagram to reason about adjustment; confounders, mediators, and colliders
  have different roles. Do not select adjustment variables just by statistical significance.
- Randomization supports exchangeability at assignment; it does not guarantee balanced
  realized groups or remove later selection, non-adherence, measurement, or attrition bias.
- Observational designs may support causal inference under defended assumptions; acknowledge
  untestable assumption

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

