---
id: sciref-sympy-physics-mechanics
name: "Scientific Ref: SymPy Physics and Mechanics"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (sympy): SymPy Physics and Mechanics"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "sympy physics mechanics"
  - "sympy physics and mechanics"
keywords:
  - "sympy"
  - "physics"
  - "mechanics"
  - "specialized"
  - "scientific"
  - "reference"
---

# SymPy Physics and Mechanics

Examples in this reference are ordered session fragments: run earlier imports and
setup first. Tested with SymPy 1.14.0; exceptions are explicitly marked illustrative.

This document covers SymPy's physics modules including classical mechanics, quantum mechanics, vector analysis, units, optics, continuum mechanics, and control systems.

## Vector Analysis

### Creating Reference Frames and Vectors

```python
from sympy.physics.vector import ReferenceFrame, dynamicsymbols

# Create reference frames
N = ReferenceFrame('N')  # Inertial frame
B = ReferenceFrame('B')  # Body frame

# Create vectors
v = 3*N.x + 4*N.y + 5*N.z

# Time-varying quantities
t = dynamicsymbols._t
x = dynamicsymbols('x')  # Function of time
v = x.diff(t) * N.x  # Velocity vector
```

### Vector Operations

```python
from sympy.physics.vector import dot, cross

v1 = 3*N.x + 4*N.y
v2 = 1*N.x + 2*N.y + 3*N.z

# Dot product
d = dot(v1, v2)

# Cross product
c = cross(v1, v2)

# Magnitude
mag = v1.magnitude()

# Normalize
v1_norm = v1.normalize()
```

### Frame Orientation

```python
# Rotate frame B relative to N
from sympy import symbols, cos, sin
theta = symbols('theta')

# Simple rotation about z-axis
B.orient(N, 'Axis', [theta, N.z])

# Direction cosine matrix (DCM)
dcm = N.dcm(B)

# Angular velocity of B in N
omega = B.ang_vel_in(N)
```

### Points and Kinematics

```python
from sympy.physics.vector import Point

# Create points
O = Point('O')  # Origin
P = Point('P')

# Set position
P.set_pos(O, 3*N.x + 4*N.y)

# Set velocity
P.set_vel(N, 5*N.x + 2*N.y)

# Get velocity of P in frame N
v = P.vel(N)

# Get acceleration
a = P.acc(N)
```

## Classical Mechanics

### Lagrangian Mechanics

```python
from sympy import symbols, Function, cos
from sympy.physics.mechanics import dynamicsymbols, LagrangesMethod

# Define generalized coordinates
q = dynamicsymbols('q')
qd = dynamicsymbols('q', 1)  # q dot (velocity)

# Define Lagrangian (L = T - V)
from sympy import Rational
m, g, l = symbols('m g l')
T = Rational(1, 2) * m * (l * qd)**2  # Kinetic energy
V = m * g * l * (1 - cos(q))           # Potential energy
L = T - V

# Apply Lagrange's method
LM = LagrangesMethod(L, [q])
LM.form_lagranges_equations()
eqs = LM.rhs()  # Right-hand side of equations of motion
```

### Kane's Method

```python
from sympy.physics.mechanics import KanesMethod, ReferenceFrame, Point, Particle
from sympy.physics.vector import dynamicsymbols

# Define system
N = ReferenceFrame('N')
q = dynamicsymbols('q')
u = dynamicsymbols('u')  # Generalized speed

# One-dimensional mass-spring oscillator; positive mass and stiffness
m, k = symbols('m k', positive=True)
O = Point('O')
O.set_vel(N, 0)
P = O.locatenew('P', q*N.x)
P.set_vel(N, u*N.x)
particle = Particle('particle', P, m)
kd = [u - q.diff()]
KM = KanesMethod(N, q_ind=[q], u_ind=[u], kd_eqs=kd)
KM.kanes_equations([particle], [(P, -k*q*N.x)])
```

### System Bodies and Inertias

```python
from sympy.physics.mechanics import RigidBody, inertia, Point, ReferenceFrame
from sympy import symbols

# Mass and inertia parameters
m = symbols('m')
Ixx, Iyy, Izz = symbols('I_xx I_yy I_zz')

# Create reference frame and mass center
A = ReferenceFrame('A')
P = Point('P')

# Define inertia dyadic
I = inertia(A, Ixx, Iyy, Izz)  # Dyadic; Inertia itself takes (dyadic, point)

# Create rigid body
body = RigidBody('Body', P, A, m, (I, P))
```

### Joints Framework

```python
from sympy.physics.mechanics import RigidBody, PinJoint, PrismaticJoint

# Create bodies
parent = RigidBody('P')
child = RigidBody('C')

# Create pin (revolute) joint
pin = PinJoint('pin', parent, child)

# Create prismatic (sliding) joint
slider_child = RigidBody('S')
slider = PrismaticJoint('slider', parent, slider_child, joint_axis=parent.frame.z)
```

### Linearization

```python
# Linearize equations of motion about an equilibrium
operating_point = {q: 0, u: 0}  # Equilibrium point
A_linear, B_linear, inputs = KM.linearize(A_and_B=True, op_point=operating_point)
# A_linear = Matrix([[0, 1], [-k/m, 0]]); no input in this example.
# Coordinate/speed partitions were supplied to KanesMethod, not linearize().
```

## Quantum Mechanics

### States and Operators

```python
from sympy.physics.quantum import Ket, Bra, Operator, Dagger

# Define states
psi = Ket('psi')
phi = Ket('phi')

# Bra states
bra_psi = Bra('psi')

# Operators
A = Operator('A')
B = Operator('B')

# Hermitian conjugate
A_dag = Dagger(A)

# Inner product
inner = bra_psi * psi
```

### Commutators and Anti-commutators

```python
from sympy.physics.quantum import Commutator, AntiCommutator

# Commutator [A, B] = AB - BA
comm = Commutator(A, B)
comm.doit()

# Anti-commutator {A, B} = AB + BA
anti = AntiCommutator(A, B)
anti.doit()
```

### Quantum Harmonic Oscillator

```python
from sympy.physics.quantum.sho1d import RaisingOp, LoweringOp, NumberOp, SHOKet
from sympy.physics.quantum import qapply

# Creation and annihilation operators
a_dag = RaisingOp('a')  # Creation operator
a = LoweringOp('a')      # Annihilation operator
N = NumberOp('N')        # Number operator

# Number states
n = symbols('n', integer=True, nonnegative=True)
state = SHOKet(n)
raised = qapply(a_dag * state)  # sqrt(n + 1)*|n + 1>
```

### Spin Systems

```python
from sympy.physics.quantum.spin import (
    JzKet, JxKet, JyKet,  # Spin states
    Jz, Jx, Jy,            # Spin operators
    J2                     # Total angular momentum squared
)

# Spin-1/2 state
from sympy import Rational
psi = JzKet(Rational(1, 2), Rational(1, 2))  # |1/2, 1/2⟩

# Apply operator
result = qapply(Jz * psi)  # hbar/2 times this spin-up state
```

### Quantum Gates

```python
from sympy.physics.quantum.gate import (
    H,      # Hadamard gate
    X, Y, Z,  # Pauli gates
    CNOT,    # Controlled-NOT
    SWAP     # Swap gate
)

# Apply gate to quantum state
from sympy.physics.quantum.qubit import Qubit
q = Qubit('01')
result = qapply(H(0) * q)  # Apply Hadamard; qubit 0 is the rightmost bit
```

### Quantum Algorithms

```python
from sympy.physics.quantum.grover import grover_iteration, OracleGate

# Grover's algorithm components available
# from sympy.physics.quantum.shor import <components>
# Shor's algorithm components available
```

## Units and Dimensions

### Working with Units

```python
from sympy.physics.units import (
    meter, kilogram, second,
    newton, joule, watt,
    convert_to
)

# Define quantities
distance = 5 * meter
mass = 10 * kilogram
time = 2 * second

# Calculate f

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

