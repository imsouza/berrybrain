---
id: sciref-dask-arrays
name: "Scientific Ref: Dask Arrays"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (dask): Dask Arrays"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "dask arrays"
keywords:
  - "dask"
  - "arrays"
  - "specialized"
  - "scientific"
  - "reference"
---

# Dask Arrays

Reviewed with Dask/distributed 2026.8.0. File paths, deployment settings, and undefined application functions are illustrative; executed local checks and current official sources are in [review.md](review.md).

## Overview

Dask Array implements NumPy's ndarray interface using blocked algorithms. It coordinates many NumPy arrays arranged into a grid to enable computation on datasets larger than available memory, utilizing parallelism across multiple cores.

## Core Concept

A Dask Array is divided into chunks (blocks):
- Each chunk is a regular NumPy array
- Operations are applied to each chunk in parallel
- Results are combined automatically
- Enables out-of-core computation (data larger than RAM)

## Key Capabilities

### What Dask Arrays Support

**Mathematical Operations**:
- Arithmetic operations (+, -, *, /)
- Scalar functions (exponentials, logarithms, trigonometric)
- Element-wise operations

**Reductions**:
- `sum()`, `mean()`, `std()`, `var()`
- Reductions along specified axes
- `min()`, `max()`, `argmin()`, `argmax()`

**Linear Algebra**:
- Tensor contractions
- Dot products and matrix multiplication
- Some decompositions (SVD, QR)

**Data Manipulation**:
- Transposition
- Slicing (standard and fancy indexing)
- Reshaping
- Concatenation and stacking

**Array Protocols**:
- Universal functions (ufuncs)
- NumPy protocols for interoperability

## When to Use Dask Arrays

**Use Dask Arrays When**:
- Arrays exceed available RAM
- Computation can be parallelized across chunks
- Working with NumPy-style numerical operations
- Need to scale NumPy code to larger datasets

**Stick with NumPy When**:
- Arrays fit comfortably in memory
- Operations require global views of data
- Using specialized functions not available in Dask
- Performance is adequate with NumPy alone

## Important Limitations

Dask Arrays intentionally don't implement certain NumPy features:

**Not Implemented**:
- Most `np.linalg` functions (only basic operations available)
- Operations difficult to parallelize (like full sorting)
- Memory-inefficient operations (converting to lists, iterating via loops)
- Many specialized functions (driven by community needs)

**Workarounds**: `map_blocks` is appropriate only when each block can be processed independently. A block FFT is not a global FFT; neighborhood filters need overlap; global reductions need a valid combine step.

## Creating Dask Arrays

### From NumPy Arrays
```python
import dask.array as da
import numpy as np

# Create from NumPy array with specified chunks
x = np.arange(10000)
dx = da.from_array(x, chunks=1000)  # Creates 10 chunks of 1000 elements each
```

### Random Arrays
```python
# Create random array with specified chunks
x = da.random.random((10000, 10000), chunks=(1000, 1000))

# Other random functions
x = da.random.normal(10, 0.1, size=(10000, 10000), chunks=(1000, 1000))
```

### Zeros, Ones, and Empty
```python
# Create arrays filled with constants
zeros = da.zeros((10000, 10000), chunks=(1000, 1000))
ones = da.ones((10000, 10000), chunks=(1000, 1000))
empty = da.empty((10000, 10000), chunks=(1000, 1000))
```

### From Functions
```python
import dask
import dask.array as da
import numpy as np

def create_block(i, j):
    # Deterministic small synthetic block
    return np.full((4, 5), i * 10 + j, dtype='float64')

blocks = [[da.from_delayed(dask.delayed(create_block)(i, j),
                           shape=(4, 5), dtype='float64')
           for j in range(3)] for i in range(2)]
x = da.block(blocks)  # (8, 15); from_delayed accepts ONE delayed value
```

### From Disk
```python
# Load from HDF5
import h5py
with h5py.File('myfile.hdf5', mode='r') as f:
    x = da.from_array(f['/data'], chunks=(1000, 1000))
    mean = x.mean().compute(scheduler='threads')  # While handle is open
# h5py handles cannot be pickled for process/distributed workers.
# For those schedulers, open files inside worker tasks and return concrete chunks.

# Load from Zarr
import zarr
z = zarr.open('myfile.zarr', mode='r')
x = da.from_array(z, chunks=(1000, 1000))
```

## Common Operations

### Arithmetic Operations
```python
import dask.array as da

x = da.random.random((10000, 10000), chunks=(1000, 1000))
y = da.random.random((10000, 10000), chunks=(1000, 1000))

# Element-wise operations (lazy)
z = x + y
z = x * y
z = da.exp(x)
z = da.log(y)

# Compute result
result = z.compute()
```

### Reductions
```python
# Reductions along axes
total = x.sum().compute()
mean = x.mean().compute()
std = x.std().compute()

# Reduction along specific axis
row_means = x.mean(axis=1).compute()
col_sums = x.sum(axis=0).compute()
```

### Slicing and Indexing
```python
# Standard slicing (returns Dask Array)
subset = x[1000:5000, 2000:8000]

# Fancy indexing
indices = [0, 5, 10, 15]
selected = x[indices, :]

# Boolean indexing
mask = x > 0.5
filtered = x[mask]
```

### Matrix Operations
```python
# Matrix multiplication
A = da.random.random((10000, 5000), chunks=(1000, 1000))
B = da.random.random((5000, 8000), chunks=(1000, 1000))
C = da.matmul(A, B)
result = C.compute()

# Dot product
dot_product = da.dot(A, B)

# Transpose
AT = A.T
```

### Linear Algebra
```python
# Exact SVD/QR need a single column of chunks here.
# Check that a full-width block and decomposition workspaces fit memory.
import dask
A = da.random.default_rng(42).random((40, 6), chunks=(10, 6))
U, s, Vt = da.linalg.svd(A)
U_computed, s_computed, Vt_computed = dask.compute(U, s, Vt)

# QR decomposition
Q, R = da.linalg.qr(A)
Q_computed, R_computed = dask.compute(Q, R)

# Note: Only some linalg operations are available
```

### Reshaping and Manipulation
```python
# Reshape
x = da.random.random((10000, 10000), chunks=(1000, 1000))
reshaped = x.reshape(5000, 20000)

# Transpose
transposed = x.T

# Concatenate
x1 = da.random.random((5000, 10000), chunks=(1000, 1000))
x2 = da.random.random((5000, 10000), chunks=(1000, 1000))
combined = da.concatenate([x1, x2], axis=0)

# Stack
stacked = da.stack([x1, x2], axis=0)
```

## Chunking Strategy

Chunking is critical for Dask Array performance.

### Chunk Size Guidelines

**Good Chunk Sizes**:
- Measure uncompressed bytes (`prod(chunk_shape) * dtype.itemsize`)
- Start around 100 MiB for substantial arrays, then measure task duration and peak memory
- Budget concurrent input, output, and temporary buffers; align chunks with storage

**Example Calculation**:
```python
# For float64 data (8 bytes per element)
# Target 100 MB chunks: 100 MB / 8 bytes = 12.5M elements



*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

