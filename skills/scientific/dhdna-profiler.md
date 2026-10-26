---
id: sci-dhdna-profiler
name: "Scientific: dhdna-profiler"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Applies the DHDNA framework as an exploratory rubric for reasoning and writing patterns in supplied text. Used for explicit requests for DHDNA, cognitive-style reflection, a thinking-pattern profile, or comparisons of textual reasoning. Scores describe evidence in the sample, not"
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "dhdna profiler"
  - "dhdna-profiler"
keywords:
  - "dhdna"
  - "profiler"
  - "applies"
  - "framework"
  - "exploratory"
  - "rubric"
  - "reasoning"
---

# DHDNA Profiler — Text Pattern Annotation

An exploratory rubric for describing a supplied text using Digital Human DNA (DHDNA) terminology. Its cognitive-fingerprint language is a framework metaphor; it does not establish a unique, stable, or identifiable psychological signature.

Use this workflow for requested reflection on writing. It requires no package, credentials, API call, or MindBook account. It does not reproduce MindBook's scoring engine.

## Sources and scope

The [current publisher page](https://www.ahkstrategies.net/dhdna) names twelve public dimensions as a design vocabulary. The table below maps those names to the existing skill's annotation labels. The observation criteria and score anchors are local conventions, not an upstream validated scoring instrument.

The [DHDNA preprint](https://doi.org/10.5281/zenodo.18736629), *DHDNA: A Framework for Ethical Digital Identity as Inheritable Heritage* (February 23, 2026), states in section 6.3 that validation was limited to internal testing. The [IDNA v2 preprint](https://doi.org/10.5281/zenodo.18807387), *Toward a Unified Theory of Digital Consciousness* (February 27, 2026), proposes the tension pairs in section 4.3/Table 3 and the temporal-attractor model in section 2. Neither source establishes psychometric validity for this skill's annotations. A DOI, product demonstration, or journal submission is not evidence of such validity.

Describe observable reasoning and rhetorical choices. Genre, task, language proficiency, editing, collaboration, and AI assistance can change those choices. Do not infer intelligence, diagnosis, honesty, latent emotions, or a person's stable cognitive architecture from them.

## The 12 annotation dimensions

| # | Skill label | Current publisher label | Evidence to describe in the sample |
| --- | --- | --- | --- |
| 1 | Analytical Depth | Reasoning style | Explicit premises, alternatives, causal arguments, and checks of conclusions |
| 2 | Creative Range | Creative synthesis | Connections, analogies, alternative framings; novelty needs a stated comparison context |
| 3 | Emotional Processing | Emotional architecture | Expressed affect and consideration of others' feelings; not inferred internal emotion |
| 4 | Linguistic Precision | Linguistic signature | Defined terms, clear references, and controlled ambiguity; simple prose can be precise |
| 5 | Ethical Reasoning | Ethical reasoning | Explicit values, affected parties, tradeoffs, and consequences; not moral character |
| 6 | Strategic Thinking | Strategic cognition | Stated goals, constraints, contingencies, and action sequences |
| 7 | Memory Integration | Memory topology | Use of past events or precedents; not memory capacity or historical truth |
| 8 | Social Intelligence | Social intelligence | Audience adaptation and represented perspectives; not actual interpersonal ability |
| 9 | Domain Expertise | Domain expertise | Relevant technical explanations and qualified claims; jargon alone is insufficient, accuracy needs independent checking |
| 10 | Intuitive Reasoning | Intuitive processing | Explicit reliance on impressions or heuristics; missing reasoning alone is not intuition |
| 11 | Temporal Orientation | Temporal awareness | Stated time horizons and links between past, present, and future |
| 12 | Metacognition | Metacognition | Explicit uncertainty, assumptions, limitations, and revision of reasoning |

### The 6 proposed tension pairs

The IDNA preprint proposes these pairings. They are prompts for comparison, not established negative correlations or complementary scales. Rate both independently; both may be high, low, or N/A. Do not derive one score by subtracting the other from ten.

| Pair | Compare the sample's evidence for |
| --- | --- |
| 1 and 10 | Analytical Depth and Intuitive Reasoning |
| 3 and 6 | Emotional Processing and Strategic Thinking |
| 2 and 5 | Creative Range and Ethical Reasoning |
| 4 and 12 | Linguistic Precision and Metacognition |
| 7 and 11 | Memory Integration and Temporal Orientation |
| 8 and 9 | Social Intelligence and Domain Expertise |

## Workflow

### 1. Establish the sample

Use only the text designated for this request. Record a sample label, paragraph or line references, genre, purpose, language, and known editing context. Mark missing context unknown. Distinguish the author's assertions from quoted speech, fictional characters, and copied material; do not attribute all voices to the author.

If the user explicitly requests analysis of specified conversation turns, state that source scope and proceed. If the request leaves the source ambiguous, ask which text to use before expanding to earlier conversations or unrelated files.

### 2. Collect evidence

For each dimension, identify specific quotations and how they support the observation. Include contrary evidence where present. Distinguish lack of expression from lack of opportunity to express it. Do not manufacture quotations or use a fictional narrator as evidence about the writer's personality.

### 3. Annotate all twelve dimensions

Use qualitative observations by default. If numeric scoring is requested, use whole numbers on the local 1–10 rubric with these declared anchors:

- **1–3:** Relevant but limited or weakly developed expression in this sample.
- **4–7:** Explicit, developed expression with some supporting context.
- **8–10:** Sustained, elaborated expression across several relevant passages.
- **N/A:** No suitable evidence or no opportunity to assess; never impute zero or a midpoint.

Explain each numeric choice against the dimension's evidence criterion. These are ordinal judgments, not equal-interval measurements, percentiles, calibrated probabilities, or rankings of ability. Short samples may warrant only a few observations and many N/A entries. Do not force all scores or a dominant pattern.

Attach annotation confidence to each observation: HIGH for multiple unambiguous passages, MEDIUM for a clear but limited example, LOW for ambiguous evidence. Confidence concerns the textual interpretation, not a stable trait. If uncertainty prevents a defensible observation, use N/A instead of speculative scoring.

### 4. Synthesize the text pattern

Identify two or three most evidenced dimensions only when the sample supports them. Discuss the six proposed pairings only where both sides have evidence. A numeric gap, if requested, is a difference between local annotations; it does not identify inner conflict or predict behavio

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

