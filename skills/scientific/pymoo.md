---
id: sci-pymoo
name: "Scientific: pymoo"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Solves and validates single-, multi-, and many-objective optimization with pymoo, including NSGA-II, NSGA-III, MOEA/D, constraints, Pareto approximations, reference directions, and ZDT/DTLZ benchmarks for engineering and research problems."
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "pymoo"
keywords:
  - "pymoo"
  - "solves"
  - "validates"
  - "single"
  - "multi"
  - "many"
  - "objective"
---

# Pymoo - Multi-Objective Optimization in Python

## Overview

Pymoo is a comprehensive Python framework for optimization with emphasis on multi-objective problems. Solve single and multi-objective optimization using state-of-the-art algorithms (NSGA-II/III, MOEA/D, SPEA2), benchmark problems (ZDT, DTLZ), customizable genetic operators, and multi-criteria decision making methods. Excels at finding trade-off solutions (Pareto fronts) for problems with conflicting objectives. Targets stable **pymoo 0.6.2**, reviewed 2026-10-01 against current official docs and native toy runs.

## Installation

```bash
uv pip install "pymoo==0.6.2"
```

For reproducible environments, pin a version: `uv pip install "pymoo==0.6.2"`.

**Dependencies:** The released 0.6.2 wheel requires NumPy, SciPy, moocore, autograd, cma, matplotlib, alive_progress, and Deprecated. NumPy 2.x is supported. The current installation prose describes some dependencies as optional; the released package metadata governs installation. Joblib, Optuna and dill are separate dependencies for the corresponding recipes.

**Documentation:** https://pymoo.org/ — LLM-friendly index: https://pymoo.org/llms.txt

## When to Use This Skill

This skill should be used when:
- Solving optimization problems with one or multiple objectives
- Finding Pareto-optimal solutions and analyzing trade-offs
- Implementing evolutionary algorithms (GA, DE, PSO, NSGA-II/III)
- Working with constrained optimization problems
- Benchmarking algorithms on standard test problems (ZDT, DTLZ, WFG)
- Customizing genetic operators (crossover, mutation, selection)
- Visualizing high-dimensional optimization results
- Making decisions from multiple competing solutions
- Handling binary, discrete, continuous, or mixed-variable problems

## Core Concepts

### The Unified Interface

Pymoo uses a consistent `minimize()` function for all optimization tasks:

```python
from pymoo.optimize import minimize

result = minimize(
    problem,        # What to optimize
    algorithm,      # How to optimize
    termination,    # When to stop
    seed=1,
    verbose=True
)
```

**Result object contains:**
- `result.X`: Decision variables of optimal solution(s)
- `result.F`: Objective values of optimal solution(s)
- `result.G`: Raw inequality values (`g(x) <= 0` is feasible)
- `result.H`: Raw equality residuals
- `result.CV`: Aggregated constraint violation under the configured tolerances
- `result.algorithm`: Final algorithm state; history is retained when requested

**Check feasibility before plotting or selecting:** If no feasible solution was found, `result.X` and `result.F` can be `None`. With `return_least_infeasible=True`, a returned candidate can still violate constraints; report its `CV` and residuals instead of calling it feasible. Re-evaluate chosen candidates against the original physical constraints after any normalization or repair. See the [result contract](https://pymoo.org/interface/result.html).

### Problem Definition Styles

Pymoo supports three problem definition styles:

- **`Problem`**: Vectorized — `_evaluate` receives a batch of solutions (matrix)
- **`ElementwiseProblem`**: One solution per call — recommended for custom problems and parallel evaluation
- **`FunctionalProblem`**: Define objectives and constraints as separate functions without subclassing

### Problem Types

**Single-objective:** One objective to minimize; negate a maximization objective and record the conversion
**Multi-objective:** 2-3 conflicting objectives → Pareto front
**Many-objective:** 4+ objectives → High-dimensional Pareto front
**Constrained:** Objectives + inequality/equality constraints
**Mixed-variable:** Continuous, integer, binary, and categorical variables in one problem
**Dynamic:** Time-varying objectives or constraints

## Quick Start Workflows

Nine workflows and context-dependent adaptation snippets are in
[references/quick_start_workflows.md](references/quick_start_workflows.md):

| # | Workflow | Use when |
| --- | --- | --- |
| 1 | Single-objective optimization | one objective, GA or DE |
| 2 | Multi-objective (2-3 objectives) | NSGA-II and a Pareto front |
| 3 | Many-objective (4+ objectives) | NSGA-III or reference-direction methods |
| 4 | Custom problem definition | subclassing `Problem` / `ElementwiseProblem` |
| 5 | Constraint handling | inequality and equality constraints |
| 6 | Decision making from a Pareto front | scalarization and MCDM selection |
| 7 | Visualization | scatter, PCP, radviz, and heatmap views |
| 8 | Parallel evaluation | threads or joblib for expensive objectives |
| 9 | Mixed-variable optimization | integer, binary, and categorical variables |

## Algorithm Selection Guide

### Single-Objective Problems

| Algorithm | Best For | Key Features |
|-----------|----------|--------------|
| **GA** | General-purpose | Flexible, customizable operators |
| **DE** | Continuous optimization | Good global search |
| **PSO** | Smooth landscapes | Fast convergence |
| **CMA-ES** | Difficult/noisy problems | Self-adapting |

### Multi-Objective Problems (2-3 objectives)

| Algorithm | Best For | Key Features |
|-----------|----------|--------------|
| **NSGA-II** | Standard benchmark | Fast, reliable, well-tested |
| **SPEA2** | Strength/density survival | Strength-based fitness, truncation for diversity |
| **R-NSGA-II** | Preference regions | Reference point guidance |
| **MOEA/D** | Decomposable problems | Scalarization approach |

### Many-Objective Problems (4+ objectives)

| Algorithm | Best For | Key Features |
|-----------|----------|--------------|
| **NSGA-III** | 4-15 objectives | Reference direction-based |
| **RVEA** | Adaptive search | Reference vector evolution |
| **AGE-MOEA** | Complex landscapes | Adaptive geometry |

### Constrained Problems

| Approach | Algorithm | When to Use |
|----------|-----------|-------------|
| Feasibility-first | NSGA-II, GA and compatible algorithms | Feasible candidates available |
| Specialized | SRES, ISRES | Heavy constraints |
| Penalty | GA + penalty | Algorithm compatibility |

Algorithm choices are starting points, not performance guarantees. Pymoo MOEA/D does not support constraints directly.

**See:** `references/algorithms.md` for algorithm parameters and restrictions

## Benchmark Problems

### Quick problem access:
```python
from pymoo.problems import get_problem

# Single-objective
problem = get_problem("rastrigin", n_var=10)
problem = get_problem("rosenbrock", n_var=10)

# Multi-objectiv

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

