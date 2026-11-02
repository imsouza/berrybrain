---
id: sciref-scientific-critical-thinking-core-capabilities
name: "Scientific Ref: Core Capabilities"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (scientific-critical-thinking): Core Capabilities"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "scientific critical thinking core capabilities"
  - "cientifico critica pensamento core capabilities"
  - "core capabilities"
keywords:
  - "scientific"
  - "critical"
  - "thinking"
  - "core"
  - "capabilities"
  - "cientifico"
  - "critica"
  - "pensamento"
  - "specialized"
  - "reference"
---

# Core Capabilities

The seven capability areas in full: methodology critique, bias detection, statistical
analysis evaluation, evidence quality assessment, logical fallacy identification,
research design guidance, and claim evaluation — each with the questions to ask and what
the answers imply.

Use [review_sources.md](review_sources.md) for current framework versions and primary
sources. Keep missing reporting, risk of bias, applicability, and certainty distinct.

## Core Capabilities

### 1. Methodology Critique

Evaluate research methodology for rigor, validity, and potential flaws.

**Apply when:**
- Reviewing research papers
- Assessing experimental designs
- Evaluating study protocols
- Planning new research

**Evaluation framework:**

1. **Study Design Assessment**
   - Is the design appropriate for the research question?
   - Can the design support causal claims being made?
   - Are comparison groups appropriate and adequate?
   - Consider whether experimental, quasi-experimental, or observational design is justified

2. **Validity Analysis**
   - **Internal validity:** Can we trust the causal inference?
     - Check randomization quality
     - Evaluate confounding control
     - Assess selection bias
     - Review attrition/dropout patterns
   - **External validity:** Do results generalize?
     - Evaluate sample representativeness
     - Consider ecological validity of setting
     - Assess whether conditions match target application
   - **Construct validity:** Do measures capture intended constructs?
     - Review measurement validation
     - Check operational definitions
     - Assess whether measures are direct or proxy
   - **Statistical conclusion validity:** Are statistical inferences sound?
     - Verify adequate power/sample size
     - Check assumption compliance
     - Evaluate test appropriateness

3. **Control and Blinding**
   - Was randomization properly implemented (sequence generation, allocation concealment)?
   - Was blinding feasible and implemented (participants, providers, assessors)?
   - Are control conditions appropriate (placebo, active control, no treatment)?
   - Could performance or detection bias affect results?

4. **Measurement Quality**
   - Are instruments validated and reliable?
   - Are measures objective when possible, or subjective with acknowledged limitations?
   - Is outcome assessment standardized?
   - Are multiple measures used to triangulate findings?

**Reference:** See `references/scientific_method.md` for detailed principles and `references/experimental_design.md` for comprehensive design checklist.

### 2. Bias Detection

Identify and evaluate potential sources of bias that could distort findings.

**Apply when:**
- Reviewing published research
- Designing new studies
- Interpreting conflicting evidence
- Assessing research quality

**Systematic bias review:**

1. **Cognitive Biases (Researcher)**
   - **Confirmation bias:** Are only supporting findings highlighted?
   - **HARKing:** Were hypotheses stated a priori or formed after seeing results?
   - **Publication bias:** Are negative results missing from literature?
   - **Cherry-picking:** Is evidence selectively reported?
   - Check for preregistration and analysis plan transparency

2. **Selection Biases**
   - **Sampling bias:** Is sample representative of target population?
   - **Volunteer bias:** Do participants self-select in systematic ways?
   - **Attrition bias:** Is dropout differential between groups?
   - **Survivorship bias:** Are only "survivors" visible in sample?
   - Examine participant flow diagrams and compare baseline characteristics

3. **Measurement Biases**
   - **Observer bias:** Could expectations influence observations?
   - **Recall bias:** Are retrospective reports systematically inaccurate?
   - **Social desirability:** Are responses biased toward acceptability?
   - **Instrument bias:** Do measurement tools systematically err?
   - Evaluate blinding, validation, and measurement objectivity

4. **Analysis Biases**
   - **P-hacking:** Were multiple analyses conducted until significance emerged?
   - **Outcome switching:** Were non-significant outcomes replaced with significant ones?
   - **Selective reporting:** Are all planned analyses reported?
   - **Subgroup fishing:** Were subgroup analyses conducted without correction?
   - Check for study registration and compare to published outcomes

5. **Confounding**
   - What variables could affect both exposure and outcome?
   - Were confounders measured and controlled (statistically or by design)?
   - Could unmeasured confounding explain findings?
   - Are there plausible alternative explanations?

**Reference:** See `references/common_biases.md` for comprehensive bias taxonomy with detection and mitigation strategies.

### 3. Statistical Analysis Evaluation

Critically assess statistical methods, interpretation, and reporting.

**Apply when:**
- Reviewing quantitative research
- Evaluating data-driven claims
- Assessing clinical trial results
- Reviewing meta-analyses

**Statistical review checklist:**

1. **Sample Size and Power**
   - Was a priori power analysis conducted?
   - Is sample adequate for detecting meaningful effects?
   - Is the study underpowered (common problem)?
   - Do significant results from small samples raise flags for inflated effect sizes?

2. **Statistical Tests**
   - Are tests appropriate for data type and distribution?
   - Were test assumptions checked and met?
   - Are parametric tests justified, or should non-parametric alternatives be used?
   - Is the analysis matched to study design (e.g., paired vs. independent)?
   - Is n the number of independent units rather than technical replicates or time points?

3. **Multiple Comparisons**
   - Were multiple hypotheses tested?
   - Was correction applied (Bonferroni, FDR, other)?
   - Are primary outcomes distinguished from secondary/exploratory?
   - Could findings be false positives from multiple testing?

4. **P-Value Interpretation**
   - Are p-values interpreted as test-statistic tail probabilities under the null model
     and analysis procedure, rather than hypothesis probabilities?
   - Is non-significance incorrectly interpreted as "no effect"?
   - Is statistical significance conflated with practical importance?
   - Are exact p-values reported, or only "p < .05"?
   - Is there suspicious clustering just below .05?

5. **Effect Sizes and Confidence Intervals**
   - Are effect sizes reported alongside

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

