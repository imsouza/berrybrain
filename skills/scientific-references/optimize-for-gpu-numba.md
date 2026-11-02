---
id: sciref-optimize-for-gpu-numba
name: "Scientific Ref: Numba CUDA Reference"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (optimize-for-gpu): Numba CUDA Reference"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "optimize gpu numba"
  - "numba cuda reference"
keywords:
  - "optimize"
  - "gpu"
  - "numba"
  - "specialized"
  - "scientific"
  - "reference"
  - "cuda"
---

# Numba CUDA Reference

> Review: 2026-10-01. Code below is illustrative unless explicitly described as CPU-tested.
> GPU execution, performance, GDS, and multi-GPU behavior require validation on target hardware.

The established Numba-CUDA target compiles Python into CUDA kernels with explicit control over
threads, blocks, shared memory, and synchronization. It is now in maintenance mode. For new kernel
projects, evaluate Numba-CUDA-MLIR first; use this reference for existing `numba.cuda` code,
compatibility work, or features not yet available in the MLIR implementation.

> **Full documentation:** https://nvidia.github.io/numba-cuda/
> **New-development path:** https://nvidia.github.io/numba-cuda-mlir/

## Table of Contents

1. [Installation and Setup](#installation-and-setup)
2. [Core Concepts: Kernels, Threads, Blocks, Grids](#core-concepts)
3. [Writing CUDA Kernels](#writing-cuda-kernels)
4. [Thread Positioning](#thread-positioning)
5. [Memory Management](#memory-management)
6. [Shared Memory](#shared-memory)
7. [Device Functions](#device-functions)
8. [Atomic Operations](#atomic-operations)
9. [GPU Ufuncs: @vectorize and @guvectorize](#gpu-ufuncs)
10. [GPU Reductions](#gpu-reductions)
11. [Streams and Async Operations](#streams)
12. [Random Number Generation](#random-number-generation)
13. [Cooperative Groups](#cooperative-groups)
14. [Common Patterns for Scientific Computing](#common-patterns)
15. [Performance Optimization](#performance-optimization)
16. [Debugging](#debugging)
17. [Interoperability](#interoperability)
18. [Common Pitfalls](#common-pitfalls)

---

## Installation and Setup

Use `uv add` in standalone examples; follow the user's existing project package manager when one
is already configured.

```bash
uv add "numba-cuda[cu12]==0.30.*"    # For CUDA 12.x (pulls in numba and CUDA components)
uv add "numba-cuda[cu13]==0.30.*"    # For CUDA 13.x
```

The NVIDIA `numba-cuda` package is the out-of-tree implementation of the established
`numba.cuda` target (Numba's built-in target is deprecated). It keeps the `numba.cuda` namespace
and depends on `numba`, so a single install command suffices. NVIDIA limits this implementation to
security and critical fixes through the CUDA 13 lifetime; new feature development targets the
separate `numba-cuda-mlir` package. Follow its migration guide before choosing a compiler for new
code because feature coverage continues to evolve.

**Requirements:** CUDA Toolkit 12 or 13. GPU with Compute Capability >= 5.0 (Maxwell or newer) on CUDA 12, or >= 7.5 (Turing or newer) on CUDA 13.

```python
from numba import cuda

# Verify GPU is available
print(cuda.is_available())   # True if CUDA works
cuda.detect()                # Prints GPU details
```

---

## Core Concepts

CUDA organizes parallel execution in a hierarchy:

```
Grid (of blocks) → Blocks (of threads) → Threads
```

- **Thread**: The smallest unit of execution. Each runs your kernel function.
- **Block**: A group of threads that can share fast on-chip memory and synchronize with each other. Max 1024 threads per block.
- **Grid**: The collection of all blocks for a kernel launch.

A **kernel** is a function that runs on the GPU, launched from the CPU. A **device function** runs on the GPU but is called from other GPU code (not from CPU).

---

## Writing CUDA Kernels

### The @cuda.jit Decorator

```python
from numba import cuda

@cuda.jit
def my_kernel(input_array, output_array):
    i = cuda.grid(1)                    # Get this thread's global index
    if i < input_array.size:            # Bounds check — ALWAYS do this
        output_array[i] = input_array[i] * 2.0
```

**Key parameters for @cuda.jit:**

| Parameter | Purpose |
|-----------|---------|
| `device=True` | Makes this a device function (callable from GPU only, can return values) |
| `fastmath=True` | Enables fast math (fast sqrt, division, FMA, trig/exp/log approximations on float32). Use when IEEE-754 strictness isn't required |
| `max_registers=N` | Limits registers per thread to increase occupancy |
| `cache=True` | Caches compiled kernel to disk |
| `debug=True` | Enables exception checking (slow — for debugging only, pair with `opt=False`) |
| `lineinfo=True` | Source line info for profiling without full debug overhead |

### Launching Kernels

```python
import numpy as np
from numba import cuda

data = np.random.rand(1_000_000).astype(np.float32)
out = np.zeros_like(data)

# Transfer to GPU
d_data = cuda.to_device(data)
d_out = cuda.device_array_like(out)

# Calculate launch configuration
threads_per_block = 256
blocks_per_grid = (data.size + threads_per_block - 1) // threads_per_block

# Launch
my_kernel[blocks_per_grid, threads_per_block](d_data, d_out)

# Get results back
result = d_out.copy_to_host()
```

**Launch syntax:** `kernel[grid_dim, block_dim, stream, dynamic_shared_mem_bytes](...args)`

The 3rd and 4th parameters are optional (stream and dynamic shared memory size in bytes).

### 2D Launch Configuration

```python
@cuda.jit
def kernel_2d(matrix, output):
    x, y = cuda.grid(2)
    if x < matrix.shape[0] and y < matrix.shape[1]:
        output[x, y] = matrix[x, y] * 2.0

threads = (16, 16)
blocks = (
    (matrix.shape[0] + threads[0] - 1) // threads[0],
    (matrix.shape[1] + threads[1] - 1) // threads[1],
)
kernel_2d[blocks, threads](d_matrix, d_output)
```

### Convenience: .forall() for 1D

```python
# Automatically computes grid dimensions for 1D
my_kernel.forall(len(data))(d_data, d_out)
```

### Critical Rules for Kernels

1. **Kernels CANNOT return values.** All output must be written to arrays passed as arguments.
2. **Always check array bounds.** If grid_size > array_size, out-of-bounds threads corrupt memory silently.
3. **Kernel launches are asynchronous.** Use `cuda.synchronize()` before reading results on the CPU.

---

## Thread Positioning

### Intrinsics

| Intrinsic | Description |
|-----------|-------------|
| `cuda.threadIdx.x/y/z` | Thread index within its block |
| `cuda.blockIdx.x/y/z` | Block index within the grid |
| `cuda.blockDim.x/y/z` | Threads per block |
| `cuda.gridDim.x/y/z` | Blocks in the grid |
| `cuda.grid(ndim)` | Absolute position in entire grid (1D → int, 2D/3D → tuple) |
| `cuda.gridsize(ndim)` | Total number of threads in entire grid |

### Grid-Stride Loop Pattern

For processing data larger than the grid, use a grid-stride loop. This decouples grid size from problem size and is essential for reusing RNG states.

```python
@cuda.jit
def process_larg

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

