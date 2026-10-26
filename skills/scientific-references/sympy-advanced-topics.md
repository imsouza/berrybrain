---
id: sciref-sympy-advanced-topics
name: "Scientific Ref: SymPy Advanced Topics"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (sympy): SymPy Advanced Topics"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "sympy advanced topics"
keywords:
  - "sympy"
  - "advanced"
  - "topics"
  - "specialized"
  - "scientific"
  - "reference"
---

# SymPy Advanced Topics

Examples in this reference are ordered session fragments: run earlier imports and
setup first. Tested with SymPy 1.14.0; exceptions are explicitly marked illustrative.

This document covers SymPy's advanced mathematical capabilities including geometry, number theory, combinatorics, logic and sets, statistics, polynomials, and special functions.

## Geometry

### 2D Geometry

```python
from sympy.geometry import Point, Line, Circle, Triangle, Polygon

# Points
p1 = Point(0, 0)
p2 = Point(1, 1)
p3 = Point(1, 0)

# Distance between points
dist = p1.distance(p2)

# Lines
line = Line(p1, p2)
line_from_eq = Line(Point(0, 0), slope=2)

# Line properties
line.slope       # Slope
line.equation()  # Equation of line
line.length      # oo (infinite for lines)

# Line segment
from sympy.geometry import Segment
seg = Segment(p1, p2)
seg.length       # Finite length
seg.midpoint     # Midpoint

# Intersection
line2 = Line(Point(0, 1), Point(1, 0))
intersection = line.intersection(line2)  # [Point(1/2, 1/2)]

# Circles
circle = Circle(Point(0, 0), 5)  # Center, radius
circle.area           # 25*pi
circle.circumference  # 10*pi

# Triangles
tri = Triangle(p1, p2, p3)
tri.area       # Area
tri.perimeter  # Perimeter
tri.angles     # Dictionary of angles
tri.vertices   # Tuple of vertices

# Polygons
poly = Polygon(Point(0, 0), Point(1, 0), Point(1, 1), Point(0, 1))
poly.area
poly.perimeter
poly.vertices
```

### Geometric Queries

```python
# Check if point is on line/curve
from sympy import Rational
point = Point(Rational(1, 2), Rational(1, 2))
line.contains(point)

# Check if parallel/perpendicular
line1 = Line(Point(0, 0), Point(1, 1))
line2 = Line(Point(0, 1), Point(1, 2))
line1.is_parallel(line2)  # True
line1.is_perpendicular(line2)  # False

# Tangent lines
from sympy.geometry import Circle, Point
circle = Circle(Point(0, 0), 5)
point = Point(5, 0)
tangents = circle.tangent_lines(point)
```

### 3D Geometry

```python
from sympy.geometry import Point3D, Line3D, Plane

# 3D Points
p1 = Point3D(0, 0, 0)
p2 = Point3D(1, 1, 1)
p3 = Point3D(1, 0, 0)

# 3D Lines
line = Line3D(p1, p2)

# Planes
plane = Plane(p1, p2, p3)  # From 3 points
plane = Plane(Point3D(0, 0, 0), normal_vector=(1, 0, 0))  # From point and normal

# Plane equation
plane.equation()

# Distance from point to plane
point = Point3D(2, 3, 4)
dist = plane.distance(point)

# Intersection of plane and line
intersection = plane.intersection(line)
```

### Curves and Ellipses

```python
from sympy.geometry import Ellipse, Curve
from sympy import sin, cos, pi

# Ellipse
ellipse = Ellipse(Point(0, 0), hradius=3, vradius=2)
ellipse.area          # 6*pi
ellipse.eccentricity  # Eccentricity

# Parametric curves
from sympy.abc import t
curve = Curve((cos(t), sin(t)), (t, 0, 2*pi))  # Circle
```

## Number Theory

### Prime Numbers

```python
from sympy.ntheory import isprime, primerange, prime, nextprime, prevprime

# Check if prime
isprime(7)    # True
isprime(10)   # False
# Results are definitive below 2**64; larger inputs use a probable-prime test.

# Generate primes in range
list(primerange(10, 50))  # [11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47]

# nth prime
prime(10)     # 29 (10th prime)

# Next and previous primes
nextprime(10)  # 11
prevprime(10)  # 7
```

### Prime Factorization

```python
from sympy import factorint, primefactors, divisors

# Prime factorization
factorint(60)  # {2: 2, 3: 1, 5: 1} means 2^2 * 3^1 * 5^1

# List of prime factors
primefactors(60)  # [2, 3, 5]

# All divisors
divisors(60)  # [1, 2, 3, 4, 5, 6, 10, 12, 15, 20, 30, 60]
```

### GCD and LCM

```python
from sympy import gcd, lcm, igcd, ilcm

# Greatest common divisor
gcd(60, 48)   # 12
igcd(60, 48)  # 12 (integer version)

# Least common multiple
lcm(60, 48)   # 240
ilcm(60, 48)  # 240 (integer version)

# Multiple arguments
igcd(60, 48, 36)  # 12; gcd accepts two expressions or a sequence
```

### Modular Arithmetic

```python
from sympy import mod_inverse, totient
from sympy.ntheory import is_primitive_root

# Modular inverse (find x such that a*x ≡ 1 (mod m))
mod_inverse(3, 7)  # 5 (because 3*5 = 15 ≡ 1 (mod 7))

# Euler's totient function
totient(10)  # 4 (numbers less than 10 coprime to 10: 1,3,7,9)

# Primitive roots
is_primitive_root(2, 5)  # True
```

### Diophantine Equations

```python
from sympy.solvers.diophantine import diophantine
from sympy.abc import x, y, z

# Linear Diophantine: ax + by = c
diophantine(3*x + 4*y - 5)  # {(4*t_0 - 5, -3*t_0 + 5)}

# Quadratic forms
diophantine(x**2 + y**2 - 25)  # Pythagorean-type equations

# More complex equations
diophantine(x**2 - 4*x*y + 8*y**2 - 3*x + 7*y - 5)
```

### Continued Fractions

```python
from sympy import nsimplify, continued_fraction_iterator
from sympy import Rational, pi

# Convert to continued fraction
cf = continued_fraction_iterator(Rational(415, 93))
list(cf)  # [4, 2, 6, 7]

# Approximate irrational numbers
cf_pi = continued_fraction_iterator(pi.evalf(20))
```

## Combinatorics

### Permutations and Combinations

```python
from sympy import factorial, binomial, factorial2
from sympy.functions.combinatorial.numbers import nC, nP

# Factorial
factorial(5)  # 120

# Binomial coefficient (n choose k)
binomial(5, 2)  # 10

# Permutations nPk = n!/(n-k)!
nP(5, 2)  # 20

# Combinations nCk = n!/(k!(n-k)!)
nC(5, 2)  # 10

# Double factorial n!!
factorial2(5)  # 15 (5*3*1)
factorial2(6)  # 48 (6*4*2)
```

### Permutation Objects

```python
from sympy.combinatorics import Permutation

# Create permutation (cycle notation)
p = Permutation([1, 2, 0, 3])  # Sends 0->1, 1->2, 2->0, 3->3
p = Permutation(0, 1, 2, size=4)    # Cycle notation: (0 1 2)(3)

# Permutation operations
p.order()       # Order of permutation
p.is_even       # True if even permutation
p.inversions()  # Number of inversions

# Compose permutations
q = Permutation([2, 0, 1, 3])
r = p * q       # Composition: (p*q)(i) == q(p(i))
```

### Partitions

```python
from sympy.utilities.iterables import partitions
from sympy.functions.combinatorial.numbers import partition

# Number of integer partitions
partition(5)  # 7 (5, 4+1, 3+2, 3+1+1, 2+2+1, 2+1+1+1, 1+1+1+1+1)

# Generate all partitions
list(partitions(4))
# {4: 1}, {3: 1, 1: 1}, {2: 2}, {2: 1, 1: 2}, {1: 4}
```

### Catalan and Fibonacci Numbers

```python
from sympy import catalan, fibonacci, lucas

# Catalan numbers
catalan(5)  # 42

# Fibonacci numbers
fibonacci(10)  # 55
lucas(10)      # 123 (Lucas numbers)
```

### Group Theory

```python


*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

