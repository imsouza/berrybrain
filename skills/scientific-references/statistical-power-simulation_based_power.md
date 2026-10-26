---
id: sciref-statistical-power-simulation-based-power
name: "Scientific Ref: Simulation-Based (Monte Carlo) Power"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (statistical-power): Simulation-Based (Monte Carlo) Power"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "statistical power simulation power"
  - "estatistica power simulation power"
  - "simulation-based (monte carlo) power"
keywords:
  - "statistical"
  - "power"
  - "simulation"
  - "estatistica"
  - "specialized"
  - "scientific"
  - "reference"
---

# Simulation-Based (Monte Carlo) Power

Simulation estimates a specified analysis procedure under an assumed
data-generating process. It is useful when analytical methods omit important
design features; it is only as credible as those assumptions. Several GLM,
cluster, repeated-measures, and survival designs do have analytical approximations.
Use one when it matches the estimand and planned analysis; otherwise simulate.

## The recipe (always the same)

1. **Simulate** a dataset of size *n* from your assumed truth: the effect you want
   to detect, plus realistic structure (baseline rates, residual SD, cluster random
   effects, dropout, covariate distributions).
2. **Analyze** it with the *exact* model/test planned for the real study.
3. **Repeat** R times. Power = fraction of replicates where the test is significant.
   Use R ≥ 1,000; use 5,000–10,000 for a stable estimate near the 80% decision point.

Always report the **Monte Carlo confidence interval** on the estimate (the
`scripts/simulate_power.py` harness returns a Wilson interval). With R = 1,000 the
±2 SE width near p = 0.8 is roughly ±0.025, so don't over-interpret 0.81 vs 0.79.

## Using the harness

`scripts/simulate_power.py` gives you `simulate_power()` and `find_sample_size()`.
You supply a function `gen_and_test(n, rng) -> bool` that builds one dataset, runs
the analysis, and returns whether it was significant. The `rng` is a seeded
`numpy.random.Generator` so each replicate consumes fresh pseudorandom draws. Reproduction also requires
recording software versions; seeded generator streams need not be identical
across future NumPy versions.

```python
from simulate_power import (simulate_power, find_sample_size,
                            example_two_group_difference)

alpha = 0.05
# n is per group; use this as a runnable template and replace the generator/test.
gen_and_test = example_two_group_difference(effect=0.5, sd=1.0, alpha=alpha)
est = simulate_power(gen_and_test, n=64, n_sims=2000, alpha=alpha, seed=0)
print(est)

# A candidate, not a guarantee of globally minimal n under Monte Carlo noise.
n, est = find_sample_size(gen_and_test, target_power=0.80, n_sims=1000,
                          alpha=alpha, lo=40, hi=100, seed=0, verbose=False)
# Check neighboring sizes with more replicates and an independent seed.
checks = [simulate_power(gen_and_test, n=j, n_sims=5000,
                         alpha=alpha, seed=2026) for j in (n - 1, n, n + 1)]
```

The file ships four adaptable examples: two-group difference (a sanity check
against the closed-form t-test), logistic regression, a cluster-randomized trial
with an ICC, and a repeated-measures linear mixed model. Copy the closest one and
edit the data-generating block.

## When simulation is useful

| Design / analysis | Features to include | What to simulate |
|-------------------|----------------|------------------|
| Logistic / Poisson regression | Power depends on the full covariate distribution | Generate predictors, compute the linear predictor, draw the outcome, fit the GLM |
| Mixed-effects / repeated measures | Random effects + within-subject correlation | Draw subject/cluster random effects, then observations; fit `mixedlm` |
| Cluster-randomized trial | ICC inflates variance; clusters are the unit | Cluster random intercepts via ICC; fit the planned cluster-aware analysis; check small-cluster inference |
| Survival (Cox / log-rank) | Censoring and event-time distribution | Draw event and censoring times; fit `lifelines` CoxPH or run a log-rank test |
| Interaction terms | The target is the interaction contrast, not either main effect | Generate the factorial structure and the interaction effect; test that coefficient |
| Mediation | Product-of-coefficients null is non-normal | Simulate the path model; bootstrap or test the indirect effect |
| Non-standard / custom test | Analytical assumptions do not match the design | Whatever your analysis script does |

## Key correctness points

- **Analyze exactly as planned.** If the real analysis adjusts for covariates,
  include them in the simulation. If it uses a robust SE or a specific correction,
  apply it in `gen_and_test`. The whole value of simulation is fidelity to the plan.
- **Handle estimation failures explicitly.** The bundled examples check convergence,
  separation/Hessian failures, and finite p-values. They raise `SimulationFitError`
  for anticipated failures; the harness retains those runs in the denominator as
  non-rejections and reports `n_failures` plus `failure_reasons`. Unexpected
  exceptions propagate. Counting failures this way defines an unconditional
  operational rejection rate; it does not prove valid statistical inference.
  Frequent failures require revising the planned analysis/design, not silently
  dropping replicates. Warnings are summarized in `n_warned` and `warning_counts`;
  inspect their categories even when a fit reports convergence.
- **Watch Type I error too.** As a check, simulate under the *null* (effect = 0)
  and confirm the rejection rate ≈ α. If it's inflated (common with small-cluster
  mixed models or naive cluster SEs), your planned analysis is anticonservative and
  the power number is meaningless until you fix the analysis.
- **Separate search from confirmation.** A fixed seed makes results reproducible,
  but does not remove noise or make power monotone in n. Bisection is only a
  heuristic for a design with increasing power. Confirm the selected n and nearby
  feasible allocations with larger runs and fresh seeds. The ordinary Wilson CI
  at an adaptively selected n is not selection-adjusted. If discrete tests,
  allocation rounding, or failures cause nonmonotonicity, inspect a grid instead.
- **Keep alpha in the callback.** The harness validates its `alpha` argument but
  does not forward it or threshold p-values. The callback must return bool, and
  must use the same planned threshold/procedure; raw p-values raise `TypeError`.
- **Distinguish conditional assumptions.** Logistic `beta` is per raw predictor
  unit; `base_rate` is risk at x=0. `n` is total observations for that example,
  clusters per arm for the cluster example, and subjects for repeated measures.
  The mixed-model examples use REML random intercepts and asymptotic Wald tests;
  they do not implement small-sample df corrections or random slopes.

## Modeling realistic complications

- **Dropout.** Either simulate missingness directly (drop rows / occasions under
  the assumed mechanism

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

