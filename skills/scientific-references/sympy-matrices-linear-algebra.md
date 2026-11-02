---
id: sciref-sympy-matrices-linear-algebra
name: "Scientific Ref: SymPy Matrices and Linear Algebra"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (sympy): SymPy Matrices and Linear Algebra"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "sympy matrices linear algebra"
  - "sympy matrices and linear algebra"
keywords:
  - "sympy"
  - "matrices"
  - "linear"
  - "algebra"
  - "specialized"
  - "scientific"
  - "reference"
---

# SymPy Matrices and Linear Algebra

Examples in this reference are ordered session fragments: run earlier imports and
setup first. Tested with SymPy 1.14.0; exceptions are explicitly marked illustrative.

This document covers SymPy's matrix operations, linear algebra capabilities, and solving systems of linear equations.

## Matrix Creation

### Basic Matrix Construction

```python
from sympy import Matrix, eye, zeros, ones, diag

# From list of rows
M = Matrix([[1, 2], [3, 4]])
M = Matrix([
    [1, 2, 3],
    [4, 5, 6]
])

# Column vector
v = Matrix([1, 2, 3])

# Row vector
v = Matrix([[1, 2, 3]])
```

### Special Matrices

```python
# Identity matrix
I = eye(3)  # 3x3 identity
# [[1, 0, 0],
#  [0, 1, 0],
#  [0, 0, 1]]

# Zero matrix
Z = zeros(2, 3)  # 2 rows, 3 columns of zeros

# Ones matrix
O = ones(3, 2)   # 3 rows, 2 columns of ones

# Diagonal matrix
D = diag(1, 2, 3)
# [[1, 0, 0],
#  [0, 2, 0],
#  [0, 0, 3]]

# Block diagonal
from sympy import BlockDiagMatrix
A = Matrix([[1, 2], [3, 4]])
B = Matrix([[5, 6], [7, 8]])
BD = BlockDiagMatrix(A, B)
```

## Matrix Properties and Access

### Shape and Dimensions

```python
M = Matrix([[1, 2, 3], [4, 5, 6]])

M.shape  # (2, 3) - returns tuple (rows, cols)
M.rows   # 2
M.cols   # 3
```

### Accessing Elements

```python
M = Matrix([[1, 2, 3], [4, 5, 6]])

# Single element
M[0, 0]  # 1 (zero-indexed)
M[1, 2]  # 6

# Row access
M[0, :]   # Matrix([[1, 2, 3]])
M.row(0)  # Same as above

# Column access
M[:, 1]   # Matrix([[2], [5]])
M.col(1)  # Same as above

# Slicing
M[0:2, 0:2]  # Top-left 2x2 submatrix
```

### Modification

```python
M = Matrix([[1, 2], [3, 4]])

# Insert row
M = M.row_insert(1, Matrix([[5, 6]]))
# [[1, 2],
#  [5, 6],
#  [3, 4]]

# Insert column
M = M.col_insert(1, Matrix([7, 8, 9]))

# Delete row
M.row_del(0)  # In-place; returns None

# Delete column
M.col_del(1)  # In-place; returns None
```

## Basic Matrix Operations

### Arithmetic Operations

```python
from sympy import Matrix

A = Matrix([[1, 2], [3, 4]])
B = Matrix([[5, 6], [7, 8]])

# Addition
C = A + B

# Subtraction
C = A - B

# Scalar multiplication
C = 2 * A

# Matrix multiplication
C = A * B

# Element-wise multiplication (Hadamard product)
C = A.multiply_elementwise(B)

# Power
C = A**2  # Same as A * A
C = A**3  # A * A * A
```

### Transpose and Conjugate

```python
M = Matrix([[1, 2], [3, 4]])

# Transpose
M.T
# [[1, 3],
#  [2, 4]]

# Conjugate (for complex matrices)
M.conjugate()

# Conjugate transpose (Hermitian transpose)
M.H  # Same as M.conjugate().T
```

### Inverse

```python
M = Matrix([[1, 2], [3, 4]])

# Inverse
M_inv = M**-1
M_inv = M.inv()

# Verify
M * M_inv  # Returns identity matrix

# Check if invertible
M.det().is_zero  # False here; None means undecided for symbolic parameters
```

## Advanced Linear Algebra

### Determinant

```python
M = Matrix([[1, 2], [3, 4]])
M.det()  # -2

# For symbolic matrices
from sympy import symbols
a, b, c, d = symbols('a b c d')
M = Matrix([[a, b], [c, d]])
M.det()  # a*d - b*c
```

### Trace

```python
M = Matrix([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
M.trace()  # 1 + 5 + 9 = 15
```

### Row Echelon Form

```python
M = Matrix([[1, 2, 3], [4, 5, 6], [7, 8, 9]])

# Reduced Row Echelon Form
rref_M, pivot_cols = M.rref()
# rref_M is the RREF matrix
# pivot_cols is tuple of pivot column indices
```

### Rank

```python
M = Matrix([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
M.rank()  # 2 (this matrix is rank-deficient)
```

### Nullspace and Column Space

```python
M = Matrix([[1, 2, 3], [4, 5, 6], [7, 8, 9]])

# Nullspace (kernel)
null = M.nullspace()
# Returns list of basis vectors for nullspace

# Column space
col = M.columnspace()
# Returns list of basis vectors for column space

# Row space
row = M.rowspace()
# Returns list of basis vectors for row space
```

### Orthogonalization

```python
# Gram-Schmidt orthogonalization
vectors = [Matrix([1, 2, 3]), Matrix([4, 5, 6])]
ortho = Matrix.orthogonalize(*vectors)

# With normalization
ortho_norm = Matrix.orthogonalize(*vectors, normalize=True)
```

## Eigenvalues and Eigenvectors

### Computing Eigenvalues

```python
M = Matrix([[1, 2], [2, 1]])

# Eigenvalues with multiplicities
eigenvals = M.eigenvals()
# Returns dict: {eigenvalue: multiplicity}
# Example: {3: 1, -1: 1}

# Just the eigenvalues as a list
eigs = list(M.eigenvals().keys())
```

### Computing Eigenvectors

```python
M = Matrix([[1, 2], [2, 1]])

# Eigenvectors with eigenvalues
eigenvects = M.eigenvects()
# Returns list of tuples: (eigenvalue, multiplicity, [eigenvectors])
# Example: [(3, 1, [Matrix([1, 1])]), (-1, 1, [Matrix([1, -1])])]

# Access individual eigenvectors
for eigenval, multiplicity, eigenvecs in M.eigenvects():
    print(f"Eigenvalue: {eigenval}")
    print(f"Eigenvectors: {eigenvecs}")
```

### Diagonalization

```python
M = Matrix([[1, 2], [2, 1]])

# Check if diagonalizable
M.is_diagonalizable()  # True or False

# Diagonalize (M = P*D*P^-1)
P, D = M.diagonalize()
# P: matrix of eigenvectors
# D: diagonal matrix of eigenvalues

# Verify
P * D * P**-1 == M  # True
```

### Characteristic Polynomial

```python
from sympy import symbols
lam = symbols('lambda')

M = Matrix([[1, 2], [2, 1]])
charpoly = M.charpoly(lam)
# Returns characteristic polynomial
```

### Jordan Normal Form

```python
M = Matrix([[2, 1, 0], [0, 2, 1], [0, 0, 2]])

# Jordan form (for non-diagonalizable matrices)
P, J = M.jordan_form()
# J is the Jordan normal form
# P is the transformation matrix
```

## Matrix Decompositions

### LU Decomposition

```python
M = Matrix([[1, 2, 3], [4, 5, 6], [7, 8, 10]])

# LU decomposition
L, U, perm = M.LUdecomposition()
# L: lower triangular
# U: upper triangular
# perm: row swaps; M.permuteFwd(perm) == L*U
```

### QR Decomposition

```python
M = Matrix([[1, 2], [3, 4], [5, 6]])

# QR decomposition
Q, R = M.QRdecomposition()
# Q: matrix with orthonormal columns (possibly rectangular); Q.H*Q == eye(Q.cols)
# R: upper triangular matrix
```

### Cholesky Decomposition

```python
# For positive definite symmetric matrices
M = Matrix([[4, 2], [2, 3]])

L = M.cholesky()
# L is lower triangular such that M = L*L.T
```

### Singular Value Decomposition (SVD)

```python
M = Matrix([[1, 0], [0, 2], [0, 0]])

# Condensed SVD: U and V have rank(M) columns
U, Sigma, V = M.singular_value_decomposition()
assert U * Sigma * V.H == M  # Conjugate transpose of V, unlike NumPy
# Numerical SVD is preferable for large floating-point matrices.
```

## Solving Linear Systems

### Using Matrix E

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

