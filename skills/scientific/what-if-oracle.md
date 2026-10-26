---
id: sci-what-if-oracle
name: "Scientific: what-if-oracle"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Supports structured what-if scenario analysis for research planning, experimental contingencies, and scientific project decisions. Explores favorable, reference, adverse, wild-card, contrarian, and second-order scenarios with explicit assumptions, evidence, and decision triggers."
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "oracle"
  - "what-if-oracle"
keywords:
  - "oracle"
  - "supports"
  - "structured"
  - "scenario"
  - "analysis"
  - "research"
  - "planning"
---

# What-If Oracle — Research Scenario Planning

Explore a bounded set of possible futures before committing research resources. The output is a scenario comparison, an evidence ledger, and a contingency plan. It does not cover the full possibility space or establish that a narrated mechanism will occur.

The six branch prompts and **0·IF·1** mnemonic come from the upstream What-If framework. Treat the mnemonic as a framing aid: a potential change (**0**), a stated condition (**IF**), and a resulting scenario (**1**). It is not a scientific law or a computational model.

The author's [What-If Paradigm](https://doi.org/10.5281/zenodo.18736841) and [Unified Theory of Digital Consciousness](https://doi.org/10.5281/zenodo.18807387) are catalogued by Zenodo as preprints. Their deposit and DOI establish provenance, not forecasting accuracy or empirical validation of this workflow.

## When to use

Use for questions such as:

- What if sample attrition is higher than planned?
- What if a method fails to transfer to a new instrument, cohort, or site?
- What if a key reagent, dataset, or measurement becomes unavailable?
- Which research option remains feasible under competing hypotheses or resource constraints?

Keep the analysis attached to a scientific decision. This is not a general business, personal advice, or software architecture skill. If the question requires an intervention effect, a power calculation, or a numerical simulation, identify the required design/model and evidence; do not manufacture those results with scenario prose.

No package, API endpoint, credential, or network connection is required for the qualitative workflow. Verify current external facts when they matter, or label the analysis as based only on supplied material. For research-specific prompts and a worked example, see [references/scenario-templates.md](references/scenario-templates.md).

## Phase 1 — Frame the question and evidence

Write one operational question containing:

- **Decision and comparator:** what can be changed, and what happens under the current plan?
- **Perturbation:** the main variable, magnitude, units, and any coupled changes. Do not assume other variables remain fixed when the mechanism links them.
- **Horizon and system:** population, site, protocol, and time window to which the answer applies.
- **Outcome and constraints:** measurable success/failure criteria, budget, capacity, and irreversible consequences.
- **Baseline:** observations and their dates, separated from assumptions and desired targets.

For example: "If the usable-sample fraction is 60% rather than the planned 80%, can a batch of 100 samples deliver 80 usable samples this month, and which contingency should we prepare?" Both fractions may be planning assumptions until supported by data.

Use the user's supplied framing when sufficient. State reasonable working assumptions and proceed; ask for a missing fact only when it materially changes the analysis.

Maintain a short evidence ledger: claim, source or data version/date, relevant population/protocol, uncertainty, and status (**observed**, **model-derived**, or **assumed**). Record conflicting evidence. An LLM-generated rationale is not an additional observation or an independent expert assessment.

## Phase 2 — Explore scenario branches

Select distinct scenarios suited to the question, usually four to six. A short screening can use favorable, reference, and adverse scenarios. The labels below are exploration lenses, not mutually exclusive outcomes or a probability distribution.

| Lens | What to examine | Scientific boundary |
| --- | --- | --- |
| **Ω Favorable (best case)** | Favorable conditions within justified bounds | Not a proven upper limit; specify whose outcome improves |
| **α Reference case** | A stated baseline or central set of assumptions | Call it "likely" only if comparative evidence supports that ranking |
| **Δ Adverse (worst case)** | Plausible failures, including dependent failures | Not a proven lower limit or the worst imaginable outcome |
| **Ψ Wild card** | A concrete disruption outside the main assumptions | Do not claim to enumerate unknowable events or assign a rarity from the label |
| **Φ Contrarian** | An alternative to a dominant hypothesis | Evaluate supporting and disconfirming evidence; disagreement alone is not support |
| **∞ Second order** | Downstream effects, delays, feedback, or changed behavior | Can occur within any other scenario; mark untested mechanisms as hypotheses |

Retain important shared drivers and correlations across branches. Avoid implausible combinations created by independently toggling quantities that share a cause. Use descriptive scenario names in the final output so favorable/adverse labels do not substitute for evaluation.

## Phase 3 — Analyze and challenge each branch

Use a compact record:

```text
Scenario: [name and lens]
Condition and horizon: [operational definition]
Assumptions: [including dependencies and boundary conditions]
Evidence: [source/data version, supporting and conflicting observations]
Mechanism: [conditional narrative; identify untested causal links]
Consequences: [outcomes, units, range, and relevant time points]
Likelihood: [not estimated, or justified estimate with method and uncertainty]
Evidence confidence: [reasoned assessment, separate from event likelihood]
Discriminating observation: [what would weaken this scenario or favor another]
Trigger and response: [observable measure, threshold, review time, owner, action]
Residual risk: [what this response does not resolve]
```

For quantitative claims, show inputs, units, method, assumptions, and whether the calculation was executed. Distinguish variation in future outcomes from uncertainty in the inputs or model. Sensitivity checks should vary decision-critical assumptions, including plausible joint changes, and identify where the preferred action changes.

For causal claims, specify the intervention, comparator, population, outcome, and horizon. An observational association or a changed prediction is not by itself an intervention effect. State the identification assumptions and supporting design; for observational adjustment these include consistency, exchangeability, and positivity. A scenario can motivate a controlled pilot or measurement, but cannot replace that evidence. See the author's maintained [Causal Inference: What If](https://miguelhernan.org/whatifbook), especially Chapters 1–3, for this distinction.

## Phase 4 — Co

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

