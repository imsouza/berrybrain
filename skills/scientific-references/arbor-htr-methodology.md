---
id: sciref-arbor-htr-methodology
name: "Scientific Ref: Hypothesis Tree Refinement (HTR) — methodology and evidence"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (arbor): Hypothesis Tree Refinement (HTR) — methodology and evidence"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "arbor htr methodology"
  - "hypothesis tree refinement (htr) — methodology and evidence"
keywords:
  - "arbor"
  - "htr"
  - "methodology"
  - "specialized"
  - "scientific"
  - "reference"
  - "hypothesis"
  - "tree"
---

# Hypothesis Tree Refinement (HTR) — methodology and evidence

Background reference for the `arbor` skill. Source: *Toward Generalist
Autonomous Research via Hypothesis-Tree Refinement* (Jin et al., 2026,
[arXiv:2606.11926](https://arxiv.org/abs/2606.11926);
[code](https://github.com/RUC-NLPIR/Arbor)). Reviewed against v1, the current
paper version on 2026-09-30. Read this when you want
the reasoning behind a design choice in the main loop.

## The problem: Autonomous Optimization (AO)

AO is the operational core of autonomous research. An agent starts from an
initial artifact and a research objective, then improves the artifact through
experimental feedback **without step-level human supervision**. Formally a task
is a tuple `P = (M_0, O, E_dev, E_test)`:

- `M_0` — mutable initial material (usually a codebase + its data).
- `O` — objective: what "better" means, as a metric direction over the
  artifact's output.
- `E_dev` — development evaluator the agent may use freely during search.
- `E_test` — held-out test evaluator. Same objective, different evidence.

The goal is to return `M* = argmax over candidates of S_test(M')`, subject to
the constraint that hypotheses and implementation decisions are made **without
using `E_test` as an exploration oracle**. A candidate that exploits dev-split
idiosyncrasies may raise `S_dev` but is not a successful AO solution unless the
gain also transfers to `S_test`.

Why this is hard: feedback is delayed, experiments are expensive, and failed
attempts contain information that should guide later search. If an agent treats
each trial as an independent local attempt, it loses the structure of the
research process — what was tried, what evidence came back, how each result
reshapes the space of future hypotheses.

## The three design requirements

HTR is built to satisfy three requirements that ordinary agentic tool use does
not:

1. **Branching with coherence.** Multiple competing hypotheses can be plausible
   at once, so exploration must branch — but unrestricted branching degenerates
   into an unstructured log. The frontier must keep competing directions
   organized, comparable, and actionable.
2. **Global strategy with local execution.** Strategic decisions depend on
   evidence across the whole run; implementing one hypothesis is short-horizon
   code editing. Separate the two so low-level traces don't obscure the global
   state, and outcomes stay attributable to the hypotheses that produced them.
3. **Exploration with held-out admission.** Dev feedback guides search;
   artifact-level progress is admitted only when it transfers beyond that
   feedback. The system must distinguish exploratory dev improvement from
   verified test improvement.

## The hypothesis tree as research state

A rooted tree `T = (V, E)`. Each node is a research unit `n = <h_n, iota_n, mu_n>`:

- **Hypothesis `h_n`** — a verifiable/falsifiable claim about how changing the
  material improves the objective. Granularity tracks depth: nodes near the root
  are broad directions; deeper nodes are concrete interventions an executor can
  implement and evaluate. This organizes exploration as progressive refinement
  rather than a flat sequence of independent trials.
- **Insight `iota_n`** — the reusable interpretation of evidence. For an
  executed leaf: what was tried, what happened, and *why* the result supports,
  weakens, or constrains the hypothesis. For an internal node: an abstraction
  over its children's insights — the current understanding of that direction.
  It is **not** an execution transcript; it is compact semantic memory for later
  ideation and selection.
- **Metadata `mu_n`** — connects the semantic hypothesis to executable evidence:
  node status, dev score, factual result, implementation reference (git branch
  or commit), optional background. The material itself is **not** duplicated in
  the tree — only references to external artifact states produced in isolated
  worktrees. This keeps the state compact while every hypothesis stays grounded
  in a verifiable implementation.

Internal nodes hold abstract directions and accumulated lessons; leaves hold
candidate interventions to dispatch. After a leaf executes, its score, result,
artifact ref, and insight are written back, and the insight is propagated upward
along the path to the root. Through this abstraction, local outcomes become
direction-level lessons and eventually a compact global understanding.

The tree therefore plays three roles at once: a **search frontier** (which
directions are active/validated/pruned), a **long-term memory** (reusable
evidence from successes *and* failures), and an **auditable record** (each
artifact change linked to the hypothesis and evidence that motivated it).

## The coordinator–executor split

- A persistent **coordinator** owns the shared tree and decides where to expand,
  which evidence to trust, what to prune, and when to merge. It sees the whole
  frontier but does not perform every low-level implementation step.
- Short-lived **executors** are invoked to test one hypothesis each. An executor
  gets `h_n`, relevant ancestor insights, and the current best artifact; it
  creates an isolated git worktree, implements the minimal change `h_n` requires,
  evaluates on `E_dev`, repairs its own broken/inactive code, and returns
  structured evidence.

The boundary is the point: exploratory code changes stay isolated until they
pass the merge gate, and the tree records only decision-relevant evidence
(scores, factual outcomes, artifact refs, distilled insights) rather than a raw
log of tool calls. This is how transient execution traces become persistent
research state.

### Executors are hypothesis-bound (and why)

An executor's local loop may involve many edits and reruns, but it stays bound
to the assigned hypothesis: `h_n` is fixed. If an executor were allowed to
change the hypothesis when the metric stalls, the returned score would no longer
be evidence about the assigned node, and ancestor insights built from it would
become impossible to interpret. Keeping executors hypothesis-bound preserves the
semantic meaning of every tree update while still allowing local engineering
flexibility.

## The six-step cycle (Algorithm 1, HTR)

Each coordinator cycle is a controlled mutation of the tree through a narrow
interface:

1. **Observe** — re-ground in a structured projection of the tree (frontier,
   root/global insights, ancestor insights, current best). Makes the tr

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

