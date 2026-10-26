---
id: sciref-arbor-report-template
name: "Scientific Ref: Final report template"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (arbor): Final report template"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "arbor report template"
  - "arbor relatorio template"
  - "final report template"
keywords:
  - "arbor"
  - "report"
  - "template"
  - "relatorio"
  - "specialized"
  - "scientific"
  - "reference"
  - "final"
---

# Final report template

Produce this when the run ends (budget spent, frontier exhausted, or progress
stalled). The point is an honest, auditable account — not a victory lap. Keep it
concise and grounded in the tree.

```markdown
# Arbor run report: [objective]

## Result
- **Best artifact**: [git branch/ref of M_best, e.g. `arbor/best`]
- **Gate score**: [score of M_best] vs. initial [score of M_0] → delta [Δ]
- **Final untouched evaluation**: [score/protocol, or explicitly not performed]
- **Evidence**: [commit, evaluator/data versions, seeds, repetitions, raw logs]
- **How to check it out**: `git checkout [ref]`
- One-line summary of the change that won.

## What was tried (audit trail)
[Paste `python "$ARBOR_TREE" status` — the tree shows every direction,
which were pruned, which merged, with dev/test scores.]

## How understanding evolved
2-4 bullets tracing the main hypothesis shifts: which early nodes tested broad
mechanisms, what they confirmed or ruled out, and how that reshaped later
hypotheses. The story should explain *why* the final design looks the way it
does — i.e. the constraints the run discovered.

## Dev vs. test (overfitting check)
- Nodes that improved **dev**: [count]
- Nodes that passed the **test merge gate**: [count]
- Comment on the gap: were there high-dev / low-test candidates? What did
  rejecting them tell you? How many gate queries were made, and was the
  same holdout reused for selection? An honest gap here is more trustworthy than a clean
  "everything worked".

## Open directions
What you'd explore with more budget, and any direction that seemed to need a
new high-level formulation rather than further refinement (HTR's known weak
spot — flag it for the human).
```

Always leave `M_best` as a real, runnable artifact on a named git branch.

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

