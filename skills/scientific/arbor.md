---
id: sci-arbor
name: "Scientific: arbor"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Applies Arbor Hypothesis Tree Refinement to research artifacts with repeatable evaluators, including model training, agent harnesses, data synthesis and benchmark optimization. Uses persistent hypotheses, isolated experiments, evidence propagation and held-out candidate compariso"
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "arbor"
keywords:
  - "arbor"
  - "applies"
  - "hypothesis"
  - "tree"
  - "refinement"
  - "research"
---

# Arbor — Autonomous Optimization via Hypothesis Tree Refinement

## Overview

This skill runs an **Autonomous Optimization (AO)** loop: starting from an existing artifact and a measurable objective, improve it through many rounds of experiment and evaluation — without step-by-step human supervision, while checking for overfitting to the development signal. It's the right tool when the bottleneck isn't writing one good change, but *organizing dozens of trials* so that lessons accumulate instead of evaporating.

It implements **Hypothesis Tree Refinement (HTR)** from *Arbor* (Jin et al., 2026). The key idea: keep the research state in a persistent **hypothesis tree** rather than in conversation history. Each node binds a hypothesis, the distilled insight it produced, and a pointer to the artifact version that realizes it. You play the long-lived **coordinator** that owns this tree and decides where to search; short-lived **executor** subagents test one hypothesis each in isolated git worktrees and report back. A **held-out merge gate** admits a change only when it improves on a *test* evaluator executors do not optimize against. This is what turns trial-and-error into cumulative, auditable research.

Use the `scripts/tree.py` state manager for all the bookkeeping (creating nodes, writing evidence, propagating insights, pruning, the merge gate, the Observe projection). It records scores and decisions; it does **not** run evaluators, create worktrees, verify Git refs, or merge Git branches. Only the coordinator writes shared state, serially; executors return evidence. The helper has no multi-writer locking. Its JSON schema is separate from upstream Arbor checkpoints.

## When to use this skill

Reach for Arbor when the task is **iterative improvement of a concrete artifact under an evaluator**:
- Model training: optimizer/architecture/recipe changes to lower loss or hit a target in fewer steps.
- Harness/agent engineering: raising pass rate or accuracy of an agent loop, search harness, or tool-use scaffold.
- Data synthesis: improving a generation/filtering pipeline judged by downstream model behavior.
- Benchmark optimization: MLE-bench / Kaggle-style "improve the submission" tasks.
- Prompt/system optimization where you can score outputs automatically.

The distinguishing signals: there's an **artifact you can modify**, an **objective**, a way to **score** candidates, and you expect to run **many experiments**. If the user only wants a single fix or a one-shot answer, this is overkill — just do the work directly. If they want open-ended ideation with no evaluator, use `hypothesis-generation` or `scientific-brainstorming` instead.

## The AO setup — pin this down first

Before any experiments, establish the task tuple `(M_0, O, E_dev, E_test)`. Record the resolved setup, using the user's existing instructions; clarify only missing decisions:

- **M_0 — initial material**: the artifact to improve (a repo, a script, a config, a prompt). Make sure it's under git and currently runs.
- **O — objective**: the natural-language goal and the metric *direction* (maximize accuracy? minimize loss/steps?).
- **E_dev — development evaluator**: a command you can run freely during search to score a candidate. Fast, repeatable.
- **E_test — held-out test evaluator**: a *separate* evaluation protocol (held-out examples or predeclared independent seeds) used only at the merge gate. It must not be used as a search oracle — that's the whole point.

Freeze the evaluator, dataset split, and metric before search, and record their
versions with each score. Repeated merge decisions on the same held-out set can
still adapt the search to that set; a fresh worktree prevents file contamination,
not statistical leakage. Keep a final untouched evaluation set for the final claim,
or disclose that the reported result was selected using repeated gate feedback.

If the user hasn't given you a clean dev/test split, **construct one and say so**. The dev/test separation is the mechanism that catches overfitting: a candidate that wins on dev but not on test isn't a success, it's a warning that you're exploiting the feedback signal. A larger run on the same examples is not an independent holdout. If no defensible holdout exists, label results as development-only.

Set `ARBOR_TREE` to the absolute path of this skill's `scripts/tree.py`, then work from the experiment project directory. The following commands illustrate one run; evaluator commands, scores and refs must be replaced with actual measured evidence. Initialize the run:

```bash
python "$ARBOR_TREE" init \
  --objective "Improve BrowseComp answer accuracy on the search harness" \
  --dev-eval "python eval.py --split dev --n 50" \
  --test-eval "python eval.py --split test --n 300" \
  --material "." --metric-direction max --branching 3 --max-depth 2 --budget 12
```

Evaluate `M_0` on the fixed gate protocol before search and record its commit and score:

```bash
python "$ARBOR_TREE" baseline --test-score 45.33 --branch-ref "baseline-commit"
```

The coordinator is responsible for freezing protocols and evaluating the baseline; these are procedural steps, not automated checks. The baseline command only records evidence supplied by the coordinator, once. `merge` refuses an unscored baseline and non-finite scores. Existing runs with no incumbent need this step; start a new run if the baseline/evaluator changes. Keep raw evaluator output, seeds, split IDs and evaluator version alongside `.arbor/`.

`--branching` is how many sibling hypotheses you propose per parent; `--max-depth 2` keeps directions at depth 1 and concrete interventions at depth 2 (the paper's default); `--budget` is the number of coordinator cycles. Start small (10–20 cycles). These helper settings are advisory: branching is recorded, depth overruns warn, and the cycle counter can exceed the budget. The coordinator must enforce the agreed stopping limits.

## The coordinator loop

You run repeated cycles of six steps. This is the heart of HTR; do not collapse it into ad-hoc editing. Run `python "$ARBOR_TREE" cycle` once per cycle to track the budget.

### 1. Observe
Begin every cycle by re-grounding in the tree, not in your memory of the conversation:

```bash
python "$ARBOR_TREE" observe
```

This prints the objective, global insights, the active frontier (selectable hypotheses), executed nodes with their evidence, pruned lessons (negative constraints), and the current best artifact. Treating the t

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

