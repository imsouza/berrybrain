---
id: sciref-pymoo-quick-start-workflows
name: "Scientific Ref: Quick start workflows (pymoo 0.6.2)"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (pymoo): Quick start workflows (pymoo 0.6.2)"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "pymoo quick start workflows"
  - "quick start workflows (pymoo 0.6.2)"
keywords:
  - "pymoo"
  - "quick"
  - "start"
  - "workflows"
  - "specialized"
  - "scientific"
  - "reference"
---

# Quick start workflows (pymoo 0.6.2)

These bounded examples illustrate API use; short runs do not establish convergence.
All objectives are minimized, so negate a maximization objective explicitly.
For headless execution use `MPLBACKEND=Agg`. Full recipes live in the linked
references; copied snippets need their displayed imports and prerequisite objects.

## 1. Single-objective optimization

```python
from pymoo.algorithms.soo.nonconvex.ga import GA
from pymoo.problems import get_problem
from pymoo.optimize import minimize

problem = get_problem("sphere", n_var=5)  # minimum at x = 0.5
result = minimize(problem, GA(pop_size=40), ("n_gen", 25), seed=1)
assert result.F is not None
print(result.X, result.F, result.algorithm.evaluator.n_eval)
```

Start with a declared evaluation budget and known-value checks of the objective.
Choose GA/DE/PSO according to model structure and compare multiple seeds.

## 2. Multi-objective optimization

```python
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.problems import get_problem
from pymoo.optimize import minimize
from pymoo.visualization.scatter import Scatter

problem = get_problem("zdt1", n_var=5)
result = minimize(problem, NSGA2(pop_size=40), ("n_gen", 40), seed=1)
plot = Scatter(legend=True)
plot.add(result.F, label="Approximation")
plot.add(problem.pareto_front(), label="Analytic front", alpha=0.3)
plot.save("zdt1.png", dpi=150)
```

ZDT1's analytic front satisfies `f2 = 1 - sqrt(f1)`, not a straight line.
Nondominance within the returned set does not certify convergence to that curve.

## 3. Many-objective optimization

```python
from pymoo.algorithms.moo.nsga3 import NSGA3
from pymoo.problems import get_problem
from pymoo.optimize import minimize
from pymoo.util.ref_dirs import get_reference_directions

problem = get_problem("dtlz2", n_obj=5)
ref_dirs = get_reference_directions("das-dennis", 5, n_partitions=3)
assert ref_dirs.shape == (35, 5)
result = minimize(problem, NSGA3(ref_dirs=ref_dirs), ("n_gen", 30), seed=1)
```

The population defaults to the number of directions. At five objectives,
12 partitions would produce 1820 directions; budget this combinatorial growth
before choosing a lattice. Directions guide diversity, not feasibility or
convergence. See [algorithms.md](algorithms.md).

## 4. Custom problem definition

```python
import numpy as np
from pymoo.core.problem import ElementwiseProblem

class MyProblem(ElementwiseProblem):
    def __init__(self):
        super().__init__(n_var=2, n_obj=2, xl=np.zeros(2), xu=np.full(2, 5.0))

    def _evaluate(self, x, out, *args, **kwargs):
        out["F"] = [np.sum(x**2), np.sum((x - 1)**2)]

problem = MyProblem()
np.testing.assert_allclose(problem.evaluate(np.array([[0, 0], [1, 1]])), [[0, 2], [2, 0]])
```

Use `Problem` for vectorized evaluation (one output row per input candidate),
`ElementwiseProblem` for individual simulations, or
`pymoo.problems.functional.FunctionalProblem` for callable objectives. Pass numeric decision vectors as NumPy arrays; elementwise callbacks can receive
plain lists unchanged if you supply lists. Check shapes and signs analytically
before optimizing.

## 5. Constraint handling

```python
import numpy as np
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.optimize import minimize
from pymoo.problems import get_problem

problem = get_problem("bnh")
result = minimize(problem, NSGA2(pop_size=40), ("n_gen", 20), seed=1)
if result.F is None:
    raise RuntimeError("No feasible solution was found")
feasible = result.opt.get("FEAS").ravel()
F, G = problem.evaluate(result.X, return_values_of=["F", "G"])
assert np.all(G[feasible] <= 0)
```

Declare `n_ieq_constr`/`n_eq_constr`; return inequalities `G <= 0` and equality
residuals `H = 0`. Equality feasibility uses a tolerance. Wrapping constraints as
objectives or penalties removes the solver's original constraint checks; recheck
physical residuals before selection. See [constraints_mcdm.md](constraints_mcdm.md)
for tested definitions and the single-objective limit of the penalty wrapper.

## 6. Select from a candidate front

```python
import numpy as np
from pymoo.mcdm.pseudo_weights import PseudoWeights
from pymoo.problems import get_problem

# An analytic front is used here to isolate preference selection from convergence.
F = get_problem("zdt1").pareto_front()
weights = np.array([0.3, 0.7])
assert np.isfinite(F).all() and np.all(np.ptp(F, axis=0) > 0)
selected = PseudoWeights(weights).do(F)
print(selected, F[selected])
```

PseudoWeights normalizes distances from estimated worst values internally and
matches a weight vector; it is not weighted-sum minimization. For optimizer output
validate feasibility, finite values, aligned X/F rows, nondominance, and varying
columns first. A single candidate needs no ranking. The bundled decision-making
script performs these checks. See [constraints_mcdm.md](constraints_mcdm.md) for ASF,
HV/IGD, scale choices, and preference sensitivity.

## 7. Visualize trade-offs

For two/three objectives use `Scatter`; for many objectives use `PCP` with common
bounds. `Heatmap` displays objective values by candidate, not solution density.
`Petal` requires bounds. The complete runnable plotting recipes are in
[visualization.md](visualization.md). Plot only feasible candidates unless
infeasible points are deliberately distinguished and labeled.

## 8. Parallel evaluation

Pass `elementwise_runner=StarmapParallelization(pool.starmap)` to an
`ElementwiseProblem`, or use `JoblibParallelization(n_jobs=2, backend="threading")`.
Keep pool lifetime inside a context manager; a process runner additionally needs
importable workers and a `__main__` guard. See [parallelization.md](parallelization.md)
for the executed deterministic thread recipes and stochastic-seed limitations.

## 9. Mixed-variable optimization

```python
from pymoo.core.problem import ElementwiseProblem
from pymoo.core.variable import Real, Integer, Choice, Binary
from pymoo.core.mixed import MixedVariableGA
from pymoo.optimize import minimize

class MixedProblem(ElementwiseProblem):
    def __init__(self, **kwargs):
        variables = {"b": Binary(), "x": Choice(options=["nothing", "multiply"]),
                     "y": Integer(bounds=(0, 2)), "z": Real(bounds=(0, 5))}
        super().__init__(vars=variables, n_obj=1, **kwargs)

    def _evaluate(self, X, out, *args, **kwargs):
        value = X["z"] + X["y"]
        if X["b"]:
            value *= 100
        if X["x"] == "multiply":
            value *= 10
 

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

