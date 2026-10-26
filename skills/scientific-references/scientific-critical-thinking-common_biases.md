---
id: sciref-scientific-critical-thinking-common-biases
name: "Scientific Ref: Common Biases in Scientific Research"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (scientific-critical-thinking): Common Biases in Scientific Research"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "scientific critical thinking common biases"
  - "cientifico critica pensamento common biases"
  - "common biases in scientific research"
keywords:
  - "scientific"
  - "critical"
  - "thinking"
  - "common"
  - "biases"
  - "cientifico"
  - "critica"
  - "pensamento"
  - "specialized"
  - "reference"
---

# Common Biases in Scientific Research

These are prompts to examine mechanisms, not evidence of misconduct. Connect a concern
to the particular result and its likely consequences; use the matching formal tool when
needed. Sources and current tool scopes are in [review_sources.md](review_sources.md).

## Cognitive Biases Affecting Researchers

### 1. Confirmation Bias
**Description:** Tendency to search for, interpret, and recall information that confirms preexisting beliefs.

**Manifestations:**
- Designing studies that can only support the hypothesis
- Interpreting ambiguous results as supportive
- Remembering hits and forgetting misses
- Selectively citing literature that agrees

**Mitigation:**
- Preregister hypotheses and analysis plans
- Actively seek disconfirming evidence
- Use blinded data analysis
- Consider alternative hypotheses

### 2. Hindsight Bias (I-Knew-It-All-Along Effect)
**Description:** After an event, people perceive it as having been more predictable than it actually was.

**Manifestations:**
- HARKing (Hypothesizing After Results are Known)
- Claiming predictions that weren't made
- Underestimating surprise at results

**Mitigation:**
- Document predictions before data collection
- Preregister studies
- Distinguish exploratory from confirmatory analyses

### 3. Publication Bias (File Drawer Problem)
**Description:** Positive/significant results are more likely to be published than negative/null results.

**Manifestations:**
- Literature appears to support effects that don't exist
- Overestimation of effect sizes
- Inability to estimate true effects from published literature

**Mitigation:**
- Publish null results
- Use preregistration and registered reports
- Conduct systematic reviews with grey literature
- When appropriate, examine funnel asymmetry as a small-study-effects diagnostic;
  asymmetry does not uniquely diagnose publication bias

### 4. Anchoring Bias
**Description:** Over-reliance on the first piece of information encountered.

**Manifestations:**
- Initial hypotheses unduly influence interpretation
- First studies in a field set expectations
- Pilot data biases main study interpretation

**Mitigation:**
- Consider multiple initial hypotheses
- Evaluate evidence independently
- Use structured decision-making

### 5. Availability Heuristic
**Description:** Overestimating likelihood of events based on how easily examples come to mind.

**Manifestations:**
- Overemphasizing recent or dramatic findings
- Neglecting base rates
- Anecdotal evidence overshadowing statistics

**Mitigation:**
- Consult systematic reviews, not memorable papers
- Consider base rates explicitly
- Use statistical thinking, not intuition

### 6. Bandwagon Effect
**Description:** Adopting beliefs because many others hold them.

**Manifestations:**
- Following research trends without critical evaluation
- Citing widely-cited papers without reading
- Accepting "textbook knowledge" uncritically

**Mitigation:**
- Evaluate evidence independently
- Read original sources
- Question assumptions

### 7. Belief Perseverance
**Description:** Maintaining beliefs even after evidence disproving them.

**Manifestations:**
- Defending theories despite contradictory evidence
- Finding ad hoc explanations for discrepant results
- Dismissing replication failures

**Mitigation:**
- Explicitly consider what evidence would change your mind
- Update beliefs based on evidence
- Distinguish between theories and ego

### 8. Outcome Bias
**Description:** Judging decisions based on outcomes rather than the quality of the decision at the time.

**Manifestations:**
- Valuing lucky guesses over sound methodology
- Dismissing good studies with null results
- Rewarding sensational findings over rigorous methods

**Mitigation:**
- Evaluate methodology independently of results
- Value rigor and transparency
- Recognize role of chance

## Experimental and Methodological Biases

### 9. Selection Bias
**Description:** Selection can impair representativeness or create biased exposure-outcome
associations by conditioning on participation, survival, or another common effect. These
are related but distinct problems; a nonrepresentative sample is not automatically biased
for every within-sample contrast.

**Types:**
- **Sampling bias:** Non-random sample
- **Attrition bias:** Systematic dropout
- **Volunteer bias:** Self-selected participants differ
- **Berkson's bias:** Conditioning on hospitalization influenced by both exposure and
  disease can create an association (collider bias)
- **Survivorship bias:** Only examining "survivors"

**Detection:**
- Compare characteristics of participants vs. target population
- Analyze dropout patterns
- Consider who is missing from the sample

**Mitigation:**
- Random sampling
- Track and analyze non-responders
- Use strategies to minimize dropout
- Report participant flow diagrams

### 10. Observer Bias (Detection Bias)
**Description:** Researchers' expectations influence observations or measurements.

**Manifestations:**
- Measuring outcomes differently across groups
- Interpreting ambiguous results based on group assignment
- Unconsciously cueing participants

**Mitigation:**
- Blinding of observers/assessors
- Objective, automated measurements
- Standardized protocols
- Inter-rater reliability checks

### 11. Performance Bias
**Description:** Systematic differences in care provided to comparison groups.

**Manifestations:**
- Treating experimental group differently
- Providing additional attention to one group
- Differential adherence to protocols

**Mitigation:**
- Standardize all procedures
- Blind participants and providers
- Use placebo controls
- Monitor protocol adherence

### 12. Measurement Bias (Information Bias)
**Description:** Systematic errors in how variables are measured.

**Types:**
- **Recall bias:** Systematic differences in accuracy of recall
- **Social desirability bias:** Responding in socially acceptable ways
- **Interviewer bias:** Interviewer's characteristics affect responses
- **Instrument bias:** Measurement tools systematically err

**Mitigation:**
- Use validated, objective measures
- Standardize data collection
- Blind participants to hypotheses
- Verify self-reports with objective data

### 13. Confounding Bias
**Description:** Effect of extraneous variable mixed with the variable of interest.

**Examples:**
- Age confounding relationship between exercise and health
- Socioeconomic status confounding education and outcomes
- Indication bi

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

