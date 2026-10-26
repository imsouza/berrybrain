---
id: sci-hypothesis-generation
name: "Scientific: hypothesis-generation"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Formulates evidence-bounded scientific questions, candidate hypotheses, rival explanations, causal or associational claims, discriminating predictions, measurements, and preregistration-ready analysis plans. Used when turning observations or preliminary findings into transparent,"
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "hypothesis generation"
  - "hipotese generation"
  - "hypothesis-generation"
keywords:
  - "hypothesis"
  - "generation"
  - "hipotese"
  - "formulates"
  - "evidence"
  - "bounded"
  - "scientific"
  - "questions"
  - "candidate"
---

# Scientific Hypothesis Generation

Turn an observation into a transparent set of candidate explanations and tests. A hypothesis is a proposal to be challenged, not a finding, fact, diagnosis, or recommendation.

## Non-negotiable boundaries

Before using unpublished, sensitive, controlled, personal, proprietary, export-controlled, or security-relevant material:

1. Confirm authorization and the applicable institutional, funder, publisher, data-use, privacy, and AI policies.
2. Keep the material local unless an authorized human explicitly approves a named external destination and data scope.
3. Minimize inputs. Do not place sensitive or unpublished data in web searches or external AI systems without authorization.
4. Stop at the appropriate human, animal, biosafety, dual-use, data-governance, or regulatory gate.

Never:

- present a hypothesis, mechanism, causal effect, citation, or apparent pattern as established evidence;
- claim novelty because a quick search found nothing;
- infer causation from association, temporal order alone, predictive accuracy, or model output;
- supply patient-specific diagnosis, treatment, dose, prognosis, or other clinical advice;
- provide harmful experimental optimization or operational detail for pathogens, toxins, weapons, evasion, or other misuse;
- bypass IRB/REC, IACUC, IBC, biosafety, dual-use, privacy, legal, or regulatory review;
- fabricate sources, identifiers, search coverage, data, results, approvals, or preregistration;
- automatically score, rank, select, accept, or reject scientific hypotheses.

If a request crosses a safety gate, produce only a high-level risk/oversight note and route it to the qualified local authority. Do not continue with operational detail.

## Keep the objects distinct

| Object | Meaning |
|---|---|
| **Observation** | What was measured, noticed, or reported, with provenance and uncertainty |
| **Research question** | The answerable question that defines scope |
| **Hypothesis** | A candidate explanatory or relational proposition |
| **Mechanism** | The proposed process connecting conditions to an outcome |
| **Causal estimand** | The precisely defined causal contrast to estimate |
| **Prediction** | An observable implication derived before checking the target result |
| **Alternative explanation** | A rival account, including bias or non-causal explanations |
| **Null hypothesis** | A specified no-effect/no-difference model used by an analysis |
| **Negative control** | A control expected not to operate through the proposed mechanism |
| **Operationalization** | How a construct becomes a variable, measurement, intervention, or category |
| **Analysis plan** | Prespecified transformations, models, contrasts, uncertainty, and decision rules |
| **Evidence** | Observations or sources that bear on a claim; never the claim itself |

Do not collapse these labels. A mechanistic story is not a prediction; a prediction is not evidence; rejection of one null does not prove a mechanism; support for one candidate does not eliminate unconsidered rivals.

## Workflow

### 1. Run the scope and safety gate

Record:

- accountable human owner and intended use;
- data sensitivity, authorization, retention, and permitted processing;
- affected people, animals, ecosystems, communities, or security interests;
- required ethics, feasibility, biosafety, dual-use, and regulatory reviews;
- unresolved blocks and domain expertise needed.

No script approval is an ethics, safety, regulatory, or scientific approval.

### 2. Freeze the observation

Write the observation before interpretation:

- measurement or source;
- population, system, place, and time;
- unit of observation and unit of analysis;
- uncertainty, missingness, exclusions, and preprocessing;
- whether the pattern was expected, exploratory, or selected after viewing results.

Use “reported,” “observed,” or “associated,” not causal language, unless a causal design and estimand justify it.

### 3. Frame the research question

Choose a framework only when it fits:

- **PICO/PICOT** for intervention/effectiveness questions: population, intervention, comparator, outcome, and optionally time.
- **PECO** for exposure questions.
- **Population–index test–reference standard–target condition** for diagnostic accuracy.
- **Population–prognostic factor–outcome–time** for prognosis.
- A domain-specific construct–context–outcome frame for qualitative, descriptive, mechanistic, or theoretical work.

PICO is not a universal template. Define stakeholders, context, boundaries, feasibility, and what answer would change knowledge or practice. FINER is a question-refinement mnemonic—Feasible, Interesting, Novel, Ethical, Relevant—not a scoring system. Treat “Novel” as unresolved until a documented, fit-for-purpose search and expert review support it.

### 4. Establish a dated evidence boundary

Search before making literature-dependent statements. Prefer primary research, official policies, primary methods papers, current reporting guidelines, and systematic reviews used for orientation.

Record:

- search date and cutoff;
- databases/indexes, queries, filters, and screening boundary;
- included and excluded source types;
- sources supporting, challenging, or contextualizing each claim;
- known access, language, database, and time limitations.

A search can establish what was searched, not universal absence. Say “not located within the documented search boundary,” never “no prior work exists.” Use `assets/search_boundary_template.json`, `assets/evidence_ledger_template.csv`, and `references/literature_search_strategies.md`.

### 5. Generate rivals before choosing tests

Create multiple candidates from genuinely different explanatory classes when plausible:

- proposed mechanism;
- measurement or processing artifact;
- confounding or common cause;
- selection or attrition;
- conditioning on a collider;
- reverse causation;
- temporal, contextual, or boundary-condition differences;
- stochastic variation;
- competing mechanisms at another scale.

Generate an initial rival set independently before AI-assisted expansion to reduce anchoring and homogenization. Do not force a fixed number or false symmetry. Keep every candidate labeled `candidate`.

Platt’s strong-inference pattern motivates alternative hypotheses and crucial tests, but failed alternatives do not make the survivor true. Unknown alternatives, auxiliary assumptions, measurement error, and mixed mechanisms remain possible.

### 6. De

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

