---
id: sci-scientific-critical-thinking
name: "Scientific: scientific-critical-thinking"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Evaluates scientific claims and evidence quality. Applies to experimental design validity, biases and confounders, statistical interpretation, evidence grading frameworks (GRADE, Cochrane Risk of Bias), and teaching critical analysis. Supports evidence appraisal and identifying f"
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "scientific critical thinking"
  - "cientifico critica pensamento"
  - "scientific-critical-thinking"
keywords:
  - "scientific"
  - "critical"
  - "thinking"
  - "cientifico"
  - "critica"
  - "pensamento"
  - "evaluates"
  - "claims"
  - "evidence"
  - "quality"
  - "applies"
---

# Scientific Critical Thinking

## Overview

Critical thinking is a systematic process for evaluating scientific rigor. Assess methodology, experimental design, statistical validity, biases, confounding, and evidence quality using GRADE and Cochrane ROB frameworks. Apply this skill for critical analysis of scientific claims.

## When to Use This Skill

This skill should be used when:
- Evaluating research methodology and experimental design
- Assessing statistical validity and evidence quality
- Identifying biases and confounding in studies
- Reviewing scientific claims and conclusions
- Conducting systematic reviews or meta-analyses
- Applying GRADE or Cochrane risk of bias assessments
- Providing critical analysis of research papers

## Appraisal Workflow

1. **Fix the question and unit.** Record population, intervention/exposure, comparator,
   outcome, time point, effect measure, and target setting. Distinguish descriptive,
   predictive, and causal claims. Identify the independent experimental/sampling unit.
2. **Extract evidence before judging.** Locate the numerical result, uncertainty,
   denominators, protocol/registration, analysis plan, and relevant supplementary material.
   Keep missing reporting separate from evidence that a procedure was not performed.
3. **Assess design and analysis.** Check selection, confounding, measurement, attrition,
   multiplicity, dependence, and model assumptions. Good fit or optimizer convergence does
   not establish a uniquely identified parameter or a causal effect.
4. **Choose the right appraisal framework.** Reporting completeness, risk of bias, and
   certainty of a body of evidence answer different questions. Record the exact tool
   version and the result being assessed; do not turn checklist counts into a quality score.
5. **Synthesize with scope intact.** Examine independent replication, overlapping samples,
   missing evidence, and applicability. Apply GRADE per outcome/comparison when appropriate,
   with explicit domain reasons, rather than grading a whole paper by its design label.
6. **Write a traceable critique.** For each concern give the source location, observation,
   consequence for the claim, uncertainty, and a feasible remedy. Separate supported
   conclusions from assumptions and from clinical/policy recommendations.

Current framework versions, primary sources, and verification limits are in
[references/review_sources.md](references/review_sources.md). The examples in the references
are teaching examples, not empirical findings or validated patient-specific advice.

## Visual Aids (Optional)

Only add figures when the **user explicitly requests** a diagram (for example, a GRADE flowchart, bias decision tree, or evidence-quality framework).

**When figures help:**
- Critical thinking framework diagrams
- Bias identification decision trees
- Evidence quality assessment flowcharts
- GRADE or risk-of-bias evaluation frameworks

**How to create figures:**
- **Preferred:** Use the **scientific-schematics** skill for AI-generated diagrams from a natural-language description
- **Alternative:** Build figures in your usual tools (draw.io, PowerPoint, matplotlib, etc.)

Run from the repository root, with `OPENROUTER_API_KEY` set:

```bash
python skills/scientific-schematics/scripts/generate_schematic.py "Illustrative GRADE appraisal: define outcome and comparison, assess certainty domains with reasons; keep recommendation decisions separate" -o figures/grade_flowchart.png --doc-type report
```

This optional command's CLI was checked with `--help`; paid generation was not exercised
for this example. Follow that skill's current dependencies and review every generated label.

**Disclosure:** AI schematic generation sends your prompt to [OpenRouter](https://openrouter.ai/) (a third-party API). Do not include unpublished sensitive details unless that transmission is appropriate for your project.

---

## Core Capabilities

Seven capability areas, each with the questions to ask and what the answers imply, are in
[references/core_capabilities.md](references/core_capabilities.md):

1. **Methodology critique** — design, controls, confounding, and whether the method can
   answer the question asked.
2. **Bias detection** — selection, measurement, publication, and cognitive biases.
3. **Statistical analysis evaluation** — power, multiplicity, p-value misuse, effect sizes.
4. **Evidence quality assessment** — study hierarchy, replication, and strength of inference.
5. **Logical fallacy identification** — the fallacies that recur in scientific argument.
6. **Research design guidance** — how to strengthen a design before data collection.
7. **Claim evaluation** — separating what was shown from what is being asserted.

Per-topic detail is in [references/scientific_method.md](references/scientific_method.md),
[references/common_biases.md](references/common_biases.md),
[references/statistical_pitfalls.md](references/statistical_pitfalls.md),
[references/evidence_hierarchy.md](references/evidence_hierarchy.md),
[references/logical_fallacies.md](references/logical_fallacies.md), and
[references/experimental_design.md](references/experimental_design.md).

## Application Guidelines

### General Approach

1. **Be Constructive**
   - Identify strengths as well as weaknesses
   - Suggest improvements rather than just criticizing
   - Distinguish between fatal flaws and minor limitations
   - Recognize that all research has limitations

2. **Be Specific**
   - Point to specific instances (e.g., "Table 2 shows..." or "In the Methods section...")
   - Quote problematic statements
   - Provide concrete examples of issues
   - Reference specific principles or standards violated

3. **Be Proportionate**
   - Match criticism severity to issue importance
   - Distinguish between major threats to validity and minor concerns
   - Consider whether issues affect primary conclusions
   - Acknowledge uncertainty in your own assessments

4. **Apply Consistent Standards**
   - Use same criteria across all studies
   - Don't apply stricter standards to findings you dislike
   - Acknowledge your own potential biases
   - Base judgments on methodology, not results

5. **Consider Context**
   - Acknowledge practical and ethical constraints
   - Consider field-specific norms for effect sizes and methods
   - Recognize exploratory vs. confirmatory contexts
   - Account for resource limitations in evaluating studies

### Apply risk-of-bias tools to the right unit

Fo

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

