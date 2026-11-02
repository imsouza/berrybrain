---
id: sci-sympy
name: "Scientific: sympy"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Performs exact symbolic mathematics with SymPy for algebra, calculus, equation solving, symbolic linear algebra, physics, and lambdify or LaTeX code generation. Use when a task needs symbolic results, explicit assumptions, or exact arithmetic; use NumPy or SciPy for purely numeri"
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "sympy"
keywords:
  - "sympy"
  - "performs"
  - "exact"
  - "symbolic"
  - "mathematics"
  - "algebra"
---

# SymPy - Symbolic Mathematics in Python

## Overview

SymPy is a Python library for symbolic mathematics that enables exact computation using mathematical symbols rather than numerical approximations. This skill provides comprehensive guidance for performing symbolic algebra, calculus, linear algebra, equation solving, physics calculations, and code generation using SymPy.

## Installation

Reviewed against current official documentation and executed with **SymPy 1.14.0**
on Python 3.13.3 (2026-10-01). Core SymPy requires **Python 3.9+**; the tested
NumPy 2.5.3 / SciPy 1.18.1 stack needs Python 3.12+. SymPy 1.14.0 requires
`mpmath>=1.1,<1.4`; use the compatible 1.3.0, not the newer 1.4.x release.
See [verification and official sources](references/review.md) for coverage.

```bash
# Install SymPy using uv
uv pip install "sympy==1.14.0"

# Optional: for lambdify and plotting examples
uv pip install numpy scipy matplotlib
```

Check your version:

```python
import sympy
print(sympy.__version__)
```

## When to Use This Skill

Use this skill when:
- Solving equations symbolically (algebraic, differential, systems of equations)
- Performing calculus operations (derivatives, integrals, limits, series)
- Manipulating and simplifying algebraic expressions
- Working with matrices and linear algebra symbolically
- Doing physics calculations (mechanics, quantum mechanics, vector analysis)
- Number theory computations (primes, factorization, modular arithmetic)
- Geometric calculations (2D/3D geometry, analytic geometry)
- Converting mathematical expressions to executable code (Python, C, Fortran)
- Generating LaTeX or other formatted mathematical output
- Needing exact mathematical results (e.g., `sqrt(2)` not `1.414...`)

## Core Capabilities

Seven capability areas are documented in
[references/core_capabilities.md](references/core_capabilities.md):

1. **Symbolic computation basics** — symbols, expressions, simplification, substitution.
2. **Calculus** — differentiation, integration, limits, series.
3. **Equation solving** — `solve`, `solveset`, linear and nonlinear systems, ODEs.
4. **Matrices and linear algebra** — see
   [references/matrices-linear-algebra.md](references/matrices-linear-algebra.md).
5. **Physics and mechanics** — see
   [references/physics-mechanics.md](references/physics-mechanics.md).
6. **Advanced mathematics** — see
   [references/advanced-topics.md](references/advanced-topics.md).
7. **Code generation and output** — see
   [references/code-generation-printing.md](references/code-generation-printing.md).

Deeper treatment of the first three is in
[references/core-capabilities.md](references/core-capabilities.md).

## Working with SymPy: Best Practices

### 1. Always Define Symbols First

```python
from sympy import symbols
x, y, z = symbols('x y z')
# Now x, y, z can be used in expressions
```

### 2. Use Assumptions for Better Simplification

```python
from sympy import symbols, sqrt
x = symbols('x', positive=True, real=True)
sqrt(x**2)  # Returns x (not Abs(x)) due to positive assumption
```

Common assumptions: `real`, `positive`, `negative`, `integer`, `rational`, `complex`, `even`, `odd`

### 3. Use Exact Arithmetic

```python
from sympy import Rational, S
# Correct (exact):
expr = Rational(1, 2) * x
expr = S(1)/2 * x

# Approximate (appropriate for measured/numerical inputs):
expr = 0.5 * x  # Creates approximate value
```

### 4. Numerical Evaluation When Needed

```python
from sympy import pi, sqrt
result = sqrt(8) + pi
result.evalf()    # 5.96371554103586
result.evalf(50)  # Request 50 decimal digits; cannot recover precision lost in inputs
```

### 5. Convert to NumPy for Performance

```python
from sympy import symbols, lambdify
import numpy as np
x = symbols("x")
expr = x**2 + 1
# Slow for many evaluations:
for x_val in range(1000):
    result = expr.subs(x, x_val).evalf()

# Fast:
f = lambdify(x, expr, 'numpy')
results = f(np.arange(1000))
```

### 6. Use Appropriate Solvers

- `solveset`: Algebraic equations (primary)
- `linsolve`: Linear systems
- `nonlinsolve`: Nonlinear systems
- `dsolve`: Differential equations
- `solve`: General purpose; supports some problems `solveset` does not

Declare the solution domain: `solveset` defaults to complex numbers, so use `domain=S.Reals` for real-only questions. A returned `ConditionSet` means an unresolved solution condition, not that no solutions exist; distinguish it from `EmptySet`. A numerical `nsolve` result is a local root found from a starting point, not proof that every root was found.

### 7. Preserve mathematical meaning and input trust

Use assumptions only when justified by the problem. An unconstrained symbol is
complex; `sqrt(x**2)` need not equal `x`, and logarithm/power identities depend on
branches. Assumption predicates can return `None` (unknown). Keep excluded
denominator zeros when cancelling factors, and verify candidate solutions in the
original expression and requested domain. `==` compares symbolic structure; use
`Eq` to build an equation and targeted simplification to verify an identity.

`parse_expr`, string `sympify`, and `lambdify` can execute code. Accept only trusted
expressions there. A regex, `local_dict`, or `evaluate=False` is not a security
boundary; untrusted input needs a separate allowlisted grammar that constructs
SymPy objects, plus resource limits. See the code-generation reference.

## Reference Files Structure

This skill uses modular reference files for different capabilities:

1. **`core-capabilities.md`**: Symbols, algebra, calculus, simplification, equation solving
   - Load when: Basic symbolic computation, calculus, or solving equations

2. **`matrices-linear-algebra.md`**: Matrix operations, eigenvalues, linear systems
   - Load when: Working with matrices or linear algebra problems

3. **`physics-mechanics.md`**: Classical mechanics, quantum mechanics, vectors, units
   - Load when: Physics calculations or mechanics problems

4. **`advanced-topics.md`**: Geometry, number theory, combinatorics, logic, statistics
   - Load when: Advanced mathematical topics beyond basic algebra and calculus

5. **`code-generation-printing.md`**: Lambdify, codegen, LaTeX output, printing
   - Load when: Converting expressions to code or generating formatted output

## Common Use Case Patterns

### Pattern 1: Solve and Verify

```python
from sympy import symbols, solve, simplify
x = symbols('x')

# Solve equation
equation = x**2 - 5*x + 6
solutions = solve(equation, x)  # [2, 

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

