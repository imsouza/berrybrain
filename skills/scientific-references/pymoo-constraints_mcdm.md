---
id: sciref-pymoo-constraints-mcdm
name: "Scientific Ref: Constraints and decision making (pymoo 0.6.2)"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (pymoo): Constraints and decision making (pymoo 0.6.2)"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "pymoo constraints mcdm"
  - "constraints and decision making (pymoo 0.6.2)"
keywords:
  - "pymoo"
  - "constraints"
  - "mcdm"
  - "specialized"
  - "scientific"
  - "reference"
  - "decision"
---

# Constraints and decision making (pymoo 0.6.2)

## Encode and test the original constraints

All objectives are minimized. Negate a maximization objective and keep that sign
conversion with the result. Inequalities use `G <= 0`; equalities use `H = 0`.
`n_ieq_constr` and `n_eq_constr` declare the separate counts.

```python
import numpy as np
from pymoo.core.problem import ElementwiseProblem

class ConstrainedProblem(ElementwiseProblem):
    def __init__(self):
        super().__init__(n_var=2, n_obj=2, n_ieq_constr=2, n_eq_constr=1,
                         xl=np.zeros(2), xu=np.full(2, 5.0))

    def _evaluate(self, x, out, *args, **kwargs):
        out["F"] = [np.sum(x**2), np.sum((x - 1)**2)]
        # x0 + x1 >= 5; x0**2 + x1**2 <= 25
        out["G"] = [5 - x[0] - x[1], np.sum(x**2) - 25]
        out["H"] = [x[0] - 2*x[1]]

problem = ConstrainedProblem()
F, G, H = problem.evaluate(np.array([[4.0, 2.0], [0.0, 0.0]]),
                           return_values_of=["F", "G", "H"])
assert np.all(G[0] <= 0) and H[0, 0] == 0
assert G[1, 0] > 0
```

For vectorized `Problem`, return arrays of shape `(n_candidates, n_obj)`,
`(n_candidates, n_ieq_constr)`, and `(n_candidates, n_eq_constr)`. For
`ElementwiseProblem`, return one vector of each kind per candidate.

The default individual configuration has inequality tolerance 0, equality
residual tolerance `1e-4`, and `cv_eps=0`. Thus exact floating-point equality is
not the solver's feasibility test. Normalize constraint residuals by documented
positive physical scales before aggregating them: otherwise a large-unit
constraint can dominate violation rankings. Scaling also changes the physical
meaning of an equality tolerance. Re-evaluate original units at the final design.

## Choose a supported handling method

- `NSGA2` uses feasibility-first comparisons and constrained survival. This is
  common, not universal: pymoo's `MOEAD` rejects constrained problems.
- `SRES` and `ISRES` provide stochastic ranking for single-objective constraints.
- `ConstraintsAsObjective(problem)` removes solver constraints and **prepends**
  CV to `F`: `[CV, f1, ...]`. Its default `append=True` adds an objective;
  `append=False` optimizes only CV. Infeasible trade-offs may remain in the result.
- `ConstraintsAsPenalty(problem, penalty=...)` is demonstrated here only for
  single-objective problems. In 0.6.2 its implementation reshapes CV to `F.shape`
  and fails for ordinary multi-objective arrays. Penalties require unit/scale
  choices and do not guarantee feasibility.
- A `Repair._do(problem, X, **kwargs)` returns repaired decision vectors. Clipping
  to box bounds repairs only those bounds; it does not repair arbitrary `G/H`.
- `AdaptiveEpsilonConstraintHandling(algorithm, perc_eps_until=0.5)` is the
  epsilon wrapper in `pymoo.constraints.eps`; temporary tolerance relaxation is
  not a license to report a final infeasible design as feasible.

When calling a wrapper directly, use `return_values_of=["F", "G", "H"]` and
`return_as_dictionary=True`, then retrieve `["F"]`. Its implementation deletes both
constraint keys: omitted keys or requesting a returned G/H tuple can raise
`KeyError`. The normal optimizer evaluator uses the dictionary path. These snippets
assume an existing problem of the indicated objective count:

```python
from pymoo.constraints.as_obj import ConstraintsAsObjective
problem_with_cv = ConstraintsAsObjective(problem)
transformed = problem_with_cv.evaluate(np.array([[4.0, 2.0]]),
    return_values_of=["F", "G", "H"], return_as_dictionary=True)["F"]
# Recompute problem.evaluate(X, return_values_of=["F", "G", "H"])
# on any candidate selected from problem_with_cv before reporting feasibility.
```

A run without a feasible optimum normally returns `result.F is None` and
`result.X is None`. `return_least_infeasible=True` returns a diagnostic candidate,
not a feasible solution. The transformed wrappers remove constraints, so their
reported CV cannot certify the original problem. For ordinary unwrapped MOO
results use `result.opt.get("FEAS").ravel()` after the None check; single-objective
`X/F/CV` can be one-dimensional.

## Prepare candidates for decision making

Use a finite, feasible, nondominated candidate set and keep row alignment with
`X`. An optimizer's nondominated set is an approximation, not proof of the true
Pareto front. Do not silently turn failed evaluations into valid objective values.

Choose ideal/nadir bounds from scientific requirements or a common reference set.
Bounds estimated separately for each run can conceal scale and convergence
changes. For an individual candidate set:

```python
from pymoo.problems import get_problem
F = get_problem("zdt1").pareto_front()
ideal, nadir = F.min(axis=0), F.max(axis=0)
span = nadir - ideal
if not np.isfinite(F).all() or np.any(span <= 0):
    raise ValueError("Resolve nonfinite or constant objectives before normalization")
F_norm = (F - ideal) / span
```

A single feasible candidate needs no preference ranking. For constant objectives,
explicitly remove them and revise weights, or select a scientifically justified
fixed scale. Do not divide by zero or mask NaNs to obtain an arbitrary index.

## Pseudo-weights

`PseudoWeights` compares the desired weight vector with normalized distances from
the worst values. It minimizes L1 distance between pseudo-weight vectors; it does
**not** minimize a weighted sum. Pseudo-weights need not reproduce weighted-sum
solutions on nonconvex fronts, and increasing one weight does not guarantee a
monotone response on every finite candidate set.

```python
from pymoo.mcdm.pseudo_weights import PseudoWeights
weights = np.array([0.3, 0.7])  # nonnegative, finite, sum to one
selected, achieved = PseudoWeights(weights).do(F, return_pseudo_weights=True)
assert np.isclose(achieved[selected].sum(), 1.0)
selected_objectives = F[selected]
```

The bundled `scripts/decision_making_example.py` validates candidate/weight shapes,
feasibility, nondominance, and constant columns before selection. Its conservative
CV guard assumes the default final feasibility configuration; for custom
`cv_eps`, explicitly validate the original physical tolerances first.

## Scalarization and high trade-off points

For compromise programming, use a working decomposition such as `ASF`. The
0.6.2 `CompromiseProgramming` class is unfinished and does not return a usable
selection. ASF divides by its supplied weights: to make larger preference weights
penalize an objective more strongly, pas

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

