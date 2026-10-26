---
id: sciref-sympy-core-capabilities
name: "Scientific Ref: SymPy Core Capabilities"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (sympy): SymPy Core Capabilities"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "sympy core capabilities"
keywords:
  - "sympy"
  - "core"
  - "capabilities"
  - "specialized"
  - "scientific"
  - "reference"
---

# SymPy Core Capabilities

Examples in this reference are ordered session fragments: run earlier imports and
setup first. Tested with SymPy 1.14.0; exceptions are explicitly marked illustrative.

This document covers SymPy's fundamental operations: symbolic computation basics, algebra, calculus, simplification, and equation solving.

## Creating Symbols and Basic Operations

### Symbol Creation

**Single symbols:**
```python
from sympy import symbols, Symbol
x = Symbol('x')
# or more commonly:
x, y, z = symbols('x y z')
```

**With assumptions:**
```python
xp = symbols('xp', positive=True)
n = symbols('n', integer=True)
# Keep x generic; symbols with the same name and different assumptions differ.
```

Common assumptions: `real`, `positive`, `negative`, `integer`, `rational`, `prime`, `even`, `odd`, `complex`

### Basic Arithmetic

SymPy supports standard Python operators for symbolic expressions:
- Addition: `x + y`
- Subtraction: `x - y`
- Multiplication: `x * y`
- Division: `x / y`
- Exponentiation: `x**y`

**Important gotcha:** Use `sympy.Rational()` or `S()` for exact rational numbers:
```python
from sympy import Rational, S
expr = Rational(1, 2) * x  # Correct: exact 1/2
expr = S(1)/2 * x          # Correct: exact 1/2
expr = 0.5 * x             # Creates floating-point approximation
```

### Substitution and Evaluation

**Substitute values:**
```python
expr = x**2 + 2*x + 1
expr.subs(x, 3)  # Returns 16
expr.subs({x: 2, y: 3})  # Multiple substitutions
```

**Numerical evaluation:**
```python
from sympy import pi, sqrt
expr = sqrt(8)
expr.evalf()      # 2.82842712474619
expr.evalf(20)    # 2.8284271247461900976 (20 digits)
pi.evalf(100)     # 100 digits of pi
```

`evalf(n)` requests precision; it cannot recreate digits missing from an input
float. For high-precision decimal input use `Float("0.1", 50)` or exact
`Rational("0.1")`. `nsimplify` guesses exact forms; a guess is not a proof.

## Simplification

SymPy provides multiple simplification functions, each with different strategies:

### General Simplification

```python
from sympy import simplify, expand, factor, collect, cancel, trigsimp, sin, cos

# General simplification (tries multiple methods)
simplify(sin(x)**2 + cos(x)**2)  # Returns 1

# Expand products and powers
expand((x + 1)**3)  # x**3 + 3*x**2 + 3*x + 1

# Factor polynomials
factor(x**3 - x**2 + x - 1)  # (x - 1)*(x**2 + 1)

# Collect terms by variable
collect(x*y + x - 3 + 2*x**2 - z*x**2 + x**3, x)

# Cancel common factors in rational expressions
cancel((x**2 + 2*x + 1)/(x**2 + x))  # (x + 1)/x
```

Cancelling factors preserves equality away from excluded denominator zeros; keep
those restrictions from the original problem. `simplify` is heuristic. A symbolic
`.equals()` or assumption predicate can return `None`, meaning undecided.

### Trigonometric Simplification

```python
from sympy import sin, cos, tan, trigsimp, expand_trig

# Simplify trig expressions
trigsimp(sin(x)**2 + cos(x)**2)  # 1
trigsimp(sin(x)/cos(x))          # tan(x)

# Expand trig functions
expand_trig(sin(x + y))  # sin(x)*cos(y) + sin(y)*cos(x)
```

### Power and Logarithm Simplification

```python
from sympy import powsimp, powdenest, log, expand_log, logcombine
a, b = symbols("a b")
p, q = symbols("p q", positive=True)

# Simplify powers
powsimp(x**a * x**b)  # x**(a + b)

# Expand logarithms
expand_log(log(p*q))  # log(p) + log(q); positive arguments justify the identity

# Combine logarithms
logcombine(log(p) + log(q))  # log(p*q)
# Generic complex x, y do not justify these logarithm identities.
```

## Calculus

### Derivatives

```python
from sympy import diff, Derivative

# First derivative
diff(x**2, x)  # 2*x

# Higher derivatives
diff(x**4, x, x, x)  # 24*x (third derivative)
diff(x**4, x, 3)     # 24*x (same as above)

# Partial derivatives
diff(x**2*y**3, x, y)  # 6*x*y**2

# Unevaluated derivative (for display)
d = Derivative(x**2, x)
d.doit()  # Evaluates to 2*x
```

### Integrals

**Indefinite integrals:**
```python
from sympy import integrate, exp, sin

integrate(x**2, x)           # x**3/3
integrate(exp(x)*sin(x), x)  # exp(x)*sin(x)/2 - exp(x)*cos(x)/2
integrate(1/x, x)            # log(x)
```

**Note:** SymPy does not include the constant of integration. Add `+ C` manually if needed.

**Definite integrals:**
```python
from sympy import oo, pi, exp, sin

integrate(x**2, (x, 0, 1))    # 1/3
integrate(exp(-x), (x, 0, oo)) # 1
integrate(sin(x), (x, 0, pi))  # 2
```

**Multiple integrals:**
```python
integrate(x*y, (y, 0, x), (x, 0, 1))  # 1/8; inner integral comes first
```

An unevaluated `Integral` means SymPy did not produce a closed form. Parameter
conditions, convergence and singularities must still be checked. Nested limits
are applied left to right, from inner to outer.

**Numerical integration (when symbolic fails):**
```python
integrate(x**x, (x, 0, 1)).evalf()  # 0.783430510712134
```

### Limits

```python
from sympy import limit, oo, sin

# Basic limits
limit(sin(x)/x, x, 0)  # 1
limit(1/x, x, oo)      # 0

# One-sided limits
limit(1/x, x, 0, '+')  # oo
limit(1/x, x, 0, '-')  # -oo

# Use limit() for singularities (not subs())
limit((x**2 - 1)/(x - 1), x, 1)  # 2
```

**Important:** Use `limit()` instead of `subs()` at singularities because infinity objects don't reliably track growth rates.

### Series Expansion

```python
from sympy import series, sin, exp, cos

# Taylor series expansion
expr = sin(x)
expr.series(x, 0, 6)  # x - x**3/6 + x**5/120 + O(x**6)

# Expansion around a point
exp(x).series(x, 1, 4)  # Expands around x=1

# Remove O() term
series(exp(x), x, 0, 4).removeO()  # 1 + x + x**2/2 + x**3/6
```

### Finite Differences (Numerical Derivatives)

```python
from sympy import Function, differentiate_finite
f = Function('f')

# Approximate derivative using finite differences
differentiate_finite(f(x), x)
f(x).diff(x).as_finite_difference()
```

## Equation Solving

### Algebraic Equations - solveset

**Primary function:** `solveset(equation, variable, domain)`

```python
from sympy import solveset, Eq, S

# Basic solving (assumes equation = 0)
solveset(x**2 - 1, x)  # {-1, 1}
solveset(x**2 + 1, x)  # {-I, I} (complex solutions)

# Using explicit equation
solveset(Eq(x**2, 4), x)  # {-2, 2}

# Specify domain
solveset(x**2 - 1, x, domain=S.Reals)  # {-1, 1}
solveset(x**2 + 1, x, domain=S.Reals)  # EmptySet (no real solutions)
```

**Return types:** Sets such as `FiniteSet`, `ImageSet`, `Union`, `EmptySet`, or
`ConditionSet`. `ConditionSet` is u

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

