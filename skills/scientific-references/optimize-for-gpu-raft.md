---
id: sciref-optimize-for-gpu-raft
name: "Scientific Ref: RAFT (pylibraft) Reference"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (optimize-for-gpu): RAFT (pylibraft) Reference"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "optimize gpu raft"
  - "raft (pylibraft) reference"
keywords:
  - "optimize"
  - "gpu"
  - "raft"
  - "specialized"
  - "scientific"
  - "reference"
  - "pylibraft"
---

# RAFT (pylibraft) Reference

> Review: 2026-10-01. Code below is illustrative unless explicitly described as CPU-tested.
> GPU execution, performance, GDS, and multi-GPU behavior require validation on target hardware.

RAFT (Reusable Accelerated Functions and Tools) is a RAPIDS library of GPU-accelerated building blocks for machine learning and information retrieval. It provides low-level primitives — sparse eigensolvers, device memory management, random graph generation, and multi-GPU communication — that higher-level libraries like cuML and cuGraph are built on. Use `pylibraft` directly when you need these primitives without the overhead of a full ML framework.

> **Full documentation:** https://docs.nvidia.com/raft/26.08/
> **Note:** Vector search and clustering algorithms have been migrated to [cuVS](https://github.com/rapidsai/cuvs). Use cuVS for nearest neighbor search, not RAFT.

## Table of Contents

1. [Installation and Setup](#installation-and-setup)
2. [Core Concepts](#core-concepts)
3. [Device Memory Management](#device-memory-management)
4. [Sparse Eigenvalue Problems](#sparse-eigenvalue-problems)
5. [Random Graph Generation](#random-graph-generation)
6. [Multi-Node Multi-GPU with raft-dask](#multi-node-multi-gpu-with-raft-dask)
7. [Interoperability](#interoperability)
8. [Performance Tips](#performance-tips)
9. [Common Pitfalls](#common-pitfalls)

---

## Installation and Setup

Use `uv add` in standalone examples; follow the user's existing project package manager when one
is already configured.

```bash
# pylibraft (core library)
uv add --extra-index-url=https://pypi.nvidia.com "pylibraft-cu12==26.8.*"   # For CUDA 12.x
uv add --extra-index-url=https://pypi.nvidia.com "pylibraft-cu13==26.8.*"   # For CUDA 13.x

# raft-dask (multi-node multi-GPU support, optional)
uv add --extra-index-url=https://pypi.nvidia.com "raft-dask-cu12==26.8.*"   # For CUDA 12.x
uv add --extra-index-url=https://pypi.nvidia.com "raft-dask-cu13==26.8.*"   # For CUDA 13.x
```

pylibraft and raft-dask wheels (including the companion `libraft` wheel) are also published directly to PyPI, so the extra index is optional.

Verify:
```python
import pylibraft
from pylibraft.common import DeviceResources
handle = DeviceResources()
handle.sync()
print("pylibraft is working")
```

---

## Core Concepts

### DeviceResources (CUDA Resource Handle)

`DeviceResources` manages expensive CUDA resources (streams, stream pools, library handles for cuBLAS/cuSOLVER). Create one and reuse it across multiple RAFT calls to avoid repeated allocation overhead.

```python
from pylibraft.common import DeviceResources, Stream

# Default stream
handle = DeviceResources()

# Custom stream
stream = Stream()
handle = DeviceResources(stream)

# With a CuPy stream
import cupy
cupy_stream = cupy.cuda.Stream()
handle = DeviceResources(stream=cupy_stream.ptr)

# Always sync before reading results
handle.sync()
```

RAFT functions are asynchronous by default — they return immediately and work continues on the GPU. You must call `handle.sync()` before accessing output data on the CPU. If you don't pass a `handle`, RAFT allocates temporary resources internally and synchronizes before returning (convenient but slower for repeated calls).

### Stream

A thin wrapper around `cudaStream_t` for ordering GPU operations:

```python
from pylibraft.common import Stream

stream = Stream()
stream.sync()                  # Synchronize all work on this stream
ptr = stream.get_ptr()         # Get the raw cudaStream_t pointer (uintptr_t)
```

---

## Device Memory Management

### device_ndarray

`device_ndarray` is RAFT's lightweight GPU array type. It implements `__cuda_array_interface__`, making it interoperable with CuPy, Numba, PyTorch, and other GPU libraries.

```python
from pylibraft.common import device_ndarray
import numpy as np

# Allocate empty GPU array
gpu_arr = device_ndarray.empty((1000, 50), dtype=np.float32)

# From a NumPy array (copies data to GPU)
cpu_data = np.random.rand(1000, 50).astype(np.float32)
gpu_arr = device_ndarray(cpu_data)

# Back to NumPy (copies data to CPU)
result = gpu_arr.copy_to_host()

# Properties
print(gpu_arr.shape)          # (1000, 50)
print(gpu_arr.dtype)          # float32
print(gpu_arr.c_contiguous)   # True (row-major)
print(gpu_arr.f_contiguous)   # False
```

### Configuring Output Types

You can configure all RAFT compute APIs to return CuPy arrays or PyTorch tensors instead of `device_ndarray`:

```python
import pylibraft.config

pylibraft.config.set_output_as("cupy")    # All APIs return cupy arrays
pylibraft.config.set_output_as("torch")   # All APIs return torch tensors

# Custom conversion
pylibraft.config.set_output_as(lambda arr: arr.copy_to_host())  # Return numpy
```

---

## Sparse Eigenvalue Problems

### eigsh — Sparse Symmetric Eigenvalue Decomposition

GPU-accelerated Lanczos method for finding eigenvalues/eigenvectors of large sparse symmetric matrices. A narrower interface than SciPy: the 26.08 implementation accepts real float32/float64 CSR values and int32/int64 indices. It does not implement SciPy generalized/shift-invert parameters such as M or sigma.

```python
import cupy as cp
import cupyx.scipy.sparse as sp
from pylibraft.sparse.linalg import eigsh
from pylibraft.common import DeviceResources

# Create a sparse symmetric matrix (CSR format)
n = 10000
density = 0.01
A = sp.random(n, n, density=density, dtype=cp.float32, format='csr')
A = A + A.T  # Make symmetric

# Find 6 largest eigenvalues
handle = DeviceResources()
eigenvalues, eigenvectors = eigsh(A, k=6, which='LM', handle=handle)
handle.sync()

print(f"Eigenvalues shape: {eigenvalues.shape}")      # (6,)
print(f"Eigenvectors shape: {eigenvectors.shape}")     # (10000, 6)
```

**Parameters:**
- `A` — Sparse symmetric CSR matrix (`cupyx.scipy.sparse.csr_matrix`)
- `k` — Number of eigenvalues to compute (default: 6). Must be `1 <= k < n`
- `which` — Which eigenvalues:
  - `'LM'`: largest in magnitude (default)
  - `'LA'`: largest algebraic
  - `'SA'`: smallest algebraic
  - `'SM'`: smallest in magnitude
- `v0` — Starting vector (optional, random if None)
- `ncv` — Number of Lanczos vectors. Must be `k + 1 < ncv < n`
- `maxiter` — Maximum iterations
- `tol` — Convergence tolerance (0 = machine precision)
- `seed` — Random seed for reproducibility
- `handle` — Optional `DeviceResources` handle

**When to use:** Spectral methods (spectral clustering, graph partitioning, PageRank-like computations), dimensionality reduct

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

