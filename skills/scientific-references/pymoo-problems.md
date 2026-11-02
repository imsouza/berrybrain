---
id: sciref-pymoo-problems
name: "Scientific Ref: Pymoo Test Problems Reference"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (pymoo): Pymoo Test Problems Reference"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "pymoo problems"
  - "pymoo test problems reference"
keywords:
  - "pymoo"
  - "problems"
  - "specialized"
  - "scientific"
  - "reference"
  - "test"
---

# Pymoo Test Problems Reference

Reference for pymoo 0.6.2 benchmark problems. Dimensions below are defaults unless specified. Custom parameter choices can change the benchmark. The built-in Sphere is sum((x - 0.5)**2) on [0, 1], not sum(x**2) about the origin.

## Single-Objective Test Problems

### Ackley Function
**Characteristics:**
- Highly multimodal
- Many local optima
- Tests algorithm's ability to escape local minima
- Continuous variables

### Griewank Function
**Characteristics:**
- Multimodal with regularly distributed local minima
- Product term introduces interdependencies between variables
- Global minimum at origin

### Rastrigin Function
**Characteristics:**
- Highly multimodal with regularly spaced local minima
- Challenging for gradient-based methods
- Tests global search capability

### Rosenbrock Function
**Characteristics:**
- Unimodal but narrow valley to global optimum
- Tests algorithm's convergence in difficult landscape
- Classic benchmark for continuous optimization

### Zakharov Function
**Characteristics:**
- Unimodal
- Single global minimum
- Tests basic convergence capability

## Multi-Objective Test Problems (2-3 objectives)

### ZDT Test Suite
**Purpose:** Standard benchmark for bi-objective optimization
**Construction:** f₂(x) = g(x) · h(f₁(x), g(x)) where g(x) = 1 at Pareto-optimal solutions

#### ZDT1
- **Variables:** 30 continuous
- **Bounds:** [0, 1]
- **Pareto front:** Convex
- **Purpose:** Basic convergence and diversity test

#### ZDT2
- **Variables:** 30 continuous
- **Bounds:** [0, 1]
- **Pareto front:** Non-convex (concave)
- **Purpose:** Tests handling of non-convex fronts

#### ZDT3
- **Variables:** 30 continuous
- **Bounds:** [0, 1]
- **Pareto front:** Disconnected (5 separate regions)
- **Purpose:** Tests diversity maintenance across discontinuous front

#### ZDT4
- **Variables:** 10 continuous (x₁ ∈ [0,1], x₂₋₁₀ ∈ [-5,5])
- **Pareto front:** Convex
- **Difficulty:** 21⁹ local Pareto fronts
- **Purpose:** Tests global search with many local optima

#### ZDT5
- **Variables:** 80 Boolean entries in pymoo by default (11 bitstring groups)
- **Encoding:** x₁ uses 30 bits, x₂₋₁₁ use 5 bits each
- **Pareto front:** Convex
- **Purpose:** Tests discrete optimization and deceptive landscapes

#### ZDT6
- **Variables:** 10 continuous
- **Bounds:** [0, 1]
- **Pareto front:** Non-convex with non-uniform density
- **Purpose:** Tests handling of biased solution distributions

**Usage:**
```python
from pymoo.problems.multi import ZDT1, ZDT2, ZDT3, ZDT4, ZDT5, ZDT6
problem = ZDT1()  # or ZDT2(), ZDT3(), etc.
```

### BNH (Binh and Korn)
**Characteristics:**
- 2 objectives
- 2 variables
- Constrained problem
- Tests constraint handling in multi-objective context

### OSY (Osyczka and Kundu)
**Characteristics:**
- 2 objectives
- 6 variables
- Multiple constraints
- Real-world inspired

### TNK (Tanaka)
**Characteristics:**
- 2 objectives
- 2 variables
- Disconnected feasible region
- Tests handling of disjoint search spaces

### Truss2D
**Characteristics:**
- Structural engineering problem
- Bi-objective (weight vs displacement)
- Practical application test

### Welded Beam
**Characteristics:**
- Engineering design problem
- Multiple constraints
- Practical optimization scenario

### Omni-test
**Characteristics:**
- Configurable test problem
- Various difficulty levels
- Systematic testing

### SYM-PART
**Characteristics:**
- Symmetric problem structure
- Tests specific algorithmic behaviors

## Many-Objective Test Problems (4+ objectives)

### DTLZ Test Suite
**Purpose:** Scalable many-objective benchmarks
**Objectives:** Configurable (typically 3-15)
**Variables:** Scalable

#### DTLZ1
- **Pareto front:** Linear (hyperplane)
- **Difficulty:** 11^k - 1 local Pareto fronts
- **Purpose:** Tests convergence with many local optima

#### DTLZ2
- **Pareto front:** Spherical (concave)
- **Difficulty:** Straightforward convergence
- **Purpose:** Basic many-objective diversity test

#### DTLZ3
- **Pareto front:** Spherical
- **Difficulty:** Multimodal distance term shared with DTLZ1
- **Purpose:** Combines DTLZ1's multimodality with DTLZ2's geometry

#### DTLZ4
- **Pareto front:** Spherical with biased density
- **Difficulty:** Non-uniform solution distribution
- **Purpose:** Tests diversity maintenance with bias

#### DTLZ5
- **Pareto front:** Degenerate; the standard three-objective case is a curve
- **Purpose:** Tests handling of degenerate fronts

#### DTLZ6
- **Pareto front:** Degenerate; inspect the selected objective count
- **Difficulty:** Harder convergence than DTLZ5
- **Purpose:** Challenging degenerate front

#### DTLZ7
- **Pareto front:** Disconnected regions
- **Difficulty:** 2^(M-1) disconnected regions
- **Purpose:** Tests diversity across disconnected fronts

**Usage:**
```python
from pymoo.problems.many import DTLZ1, DTLZ2
problem = DTLZ1(n_var=7, n_obj=3)  # 7 variables, 3 objectives
```

### WFG Test Suite
**Purpose:** Walking Fish Group scalable benchmarks
**Features:** More complex than DTLZ, various front shapes and difficulties

**Variants:** WFG1-WFG9 with different characteristics
- Non-separable
- Deceptive
- Multimodal
- Biased
- Scaled fronts

## Constrained Multi-Objective Problems

### MW Test Suite
**Purpose:** Multi-objective problems with various constraint types
**Features:** Different constraint difficulty levels

### DAS-CMOP
**Purpose:** Difficulty-adjustable and scalable constrained multi-objective problems
**Features:** Tunable constraint difficulty

### MODAct
**Purpose:** Multi-objective optimization with active constraints
**Features:** Realistic constraint scenarios

## Dynamic Multi-Objective Problems

### DF Test Suite
**Purpose:** CEC2018 Competition dynamic multi-objective benchmarks
**Features:**
- Time-varying objectives
- Changing Pareto fronts
- Tests algorithm adaptability

**Variants:** DF1-DF14 with different dynamics

## Custom Problem Definition

Define custom problems by extending base classes:

```python
from pymoo.core.problem import ElementwiseProblem
import numpy as np

class MyProblem(ElementwiseProblem):
    def __init__(self):
        super().__init__(
            n_var=2,           # number of variables
            n_obj=2,           # number of objectives
            n_ieq_constr=0,    # inequality constraints
            n_eq_constr=0,     # equality constraints
            xl=np.array([0, 0]),   # lower bounds
            xu=np.array([1, 1])    # upper bounds
        )

    def _evaluate(

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

