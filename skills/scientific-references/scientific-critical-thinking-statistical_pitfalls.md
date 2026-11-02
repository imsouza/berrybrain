---
id: sciref-scientific-critical-thinking-statistical-pitfalls
name: "Scientific Ref: Common Statistical Pitfalls"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (scientific-critical-thinking): Common Statistical Pitfalls"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "scientific critical thinking statistical pitfalls"
  - "cientifico critica pensamento estatistica pitfalls"
  - "common statistical pitfalls"
keywords:
  - "scientific"
  - "critical"
  - "thinking"
  - "statistical"
  - "pitfalls"
  - "cientifico"
  - "critica"
  - "pensamento"
  - "estatistica"
  - "specialized"
  - "reference"
---

# Common Statistical Pitfalls

Use the estimand, sampling design, and assumptions to judge an analysis; the examples
below are illustrative. Primary guidance is linked in [review_sources.md](review_sources.md).

## P-Value Misinterpretations

### Pitfall 1: P-Value = Probability Hypothesis is True
**Misconception:** p = .05 means 5% chance the null hypothesis is true.

**Reality:** A p-value is a tail probability for the specified test statistic under the
null and the rest of the statistical model, including the sampling/analysis procedure.
It is not a posterior probability that a hypothesis is true.

**Correct interpretation:** "Under this null model and analysis procedure, a test statistic
at least this extreme has probability .05." Selection or unaccounted optional stopping
can invalidate this calibration.

### Pitfall 2: Non-Significant = No Effect
**Misconception:** p > .05 proves there's no effect.

**Reality:** Absence of evidence ≠ evidence of absence. Non-significant results may indicate:
- Insufficient statistical power
- True effect too small to detect
- High variability
- Small sample size

**Better approach:**
- Report confidence intervals
- Compare the interval with effects of practical importance; do not calculate power
  from the observed effect to explain this result
- Consider equivalence testing with scientifically justified, prespecified bounds

### Pitfall 3: Significant = Important
**Misconception:** Statistical significance means practical importance.

**Reality:** With large samples, effects too small to matter for the decision can become
"significant." Judge magnitude against a justified practical threshold.

**Better approach:**
- Report effect sizes
- Consider practical significance
- Use confidence intervals

### Pitfall 4: P = .049 vs. P = .051
**Misconception:** These are meaningfully different because one crosses the .05 threshold.

**Reality:** These represent nearly identical evidence. The .05 threshold is arbitrary.

**Better approach:**
- Interpret p-values continuously as model-compatibility summaries, not stand-alone evidence scores
- Report exact p-values
- Consider context and prior evidence

### Pitfall 5: One-Tailed Tests Without Justification
**Misconception:** One-tailed tests are free extra power.

**Reality:** A one-sided test addresses a directional hypothesis; the opposite direction
need not be impossible. Choosing the tail after seeing data invalidates the nominal error rate.

**When appropriate:** Prespecify a directional decision and error criterion (for example,
a justified non-inferiority margin). Still report estimates, uncertainty, and possible harm.

## Multiple Comparisons Problems

### Pitfall 6: Multiple Testing Without Correction
**Problem:** For 20 independent tests of true nulls at alpha .05, the probability of at
least one false rejection is `1 - 0.95**20 = 0.6415` (about 64%). Dependence changes this value.

**Examples:**
- Testing many outcomes
- Testing many subgroups
- Conducting multiple interim analyses
- Testing at multiple time points

**Solutions:**
- Bonferroni correction (divide α by number of tests)
- False Discovery Rate (FDR) control
- Prespecify primary outcome
- Treat exploratory analyses as hypothesis-generating

Define the hypothesis family and error target first. FWER limits the probability of any
false rejection; FDR limits the expected false-discovery proportion (zero when there are
no discoveries). Neither is the probability that a particular discovery is false. A named
primary outcome does not resolve multiplicity across doses, time points, interim looks,
subgroups, or data-selected analysis choices.

### Pitfall 7: Subgroup Analysis Fishing
**Problem:** Testing many subgroups until finding significance.

**Why problematic:**
- Inflates false positive rate
- Often reported without disclosure
- A significant result in women and a non-significant result in men does not establish
  a difference between groups; estimate and test the interaction directly

**Solutions:**
- Prespecify subgroups
- Use interaction tests, not separate tests
- Require replication
- Correct for multiple comparisons

### Pitfall 8: Outcome Switching
**Problem:** Analyzing many outcomes, reporting only significant ones.

**Detection signs:**
- Secondary outcomes emphasized
- Incomplete outcome reporting
- Discrepancy between registration and publication

**Solutions:**
- Preregister all outcomes
- Report all planned outcomes
- Distinguish primary from secondary

## Sample Size and Power Issues

### Pitfall 9: Underpowered Studies
**Problem:** Small samples have low probability of detecting true effects.

**Consequences:**
- High false negative rate
- Among selected significant findings, the false-discovery fraction depends on power,
  prior prevalence of real effects, bias, and multiplicity; low power alone does not
  increase a correctly calibrated test's Type I error above its alpha
- Overestimated effect sizes (when significant)

**Solutions:**
- Conduct a priori power analysis
- Justify power or precision targets for the decision; 80-90% are conventions, not guarantees
- Use a meaningful effect and plausible variance; assess uncertainty in small pilot estimates

### Pitfall 10: Post-Hoc Power Analysis
**Problem:** Calculating "observed power" using the observed effect and the same test is
circular and uninformative. This does not prohibit design sensitivity calculations at an
independently justified effect size.

**Why useless:**
- Non-significant results always have low "post-hoc power"
- It recapitulates the p-value without new information

**Better approach:**
- Calculate confidence intervals
- Plan replication with adequate sample
- Conduct prospective power analysis for future studies

### Pitfall 11: Small Sample Fallacy
**Problem:** Trusting results from very small samples.

**Issues:**
- High sampling variability
- Outliers have large influence
- Distributional approximations may be unreliable; small n alone is not an assumption violation
- Confidence intervals very wide

**Guidelines:**
- There is no universal n = 30 validity threshold; count independent units and inspect precision
- Check assumptions carefully
- Choose methods for the estimand and design; non-parametric methods also have assumptions
- Replicate findings

## Effect Size Misunderstandings

### Pitfall 12: Ignoring Effect Size
**Problem:** Focusing only on significance, not magnitude.

**Why problematic:**
- Significance ≠ importance
- Can't compa

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

