---
id: sciref-optimize-for-gpu-cupy
name: "Scientific Ref: CuPy Reference"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (optimize-for-gpu): CuPy Reference"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "optimize gpu cupy"
  - "cupy reference"
keywords:
  - "optimize"
  - "gpu"
  - "cupy"
  - "specialized"
  - "scientific"
  - "reference"
---

# CuPy Reference

> Review: 2026-10-01. Code below is illustrative unless explicitly described as CPU-tested.
> GPU execution, performance, GDS, and multi-GPU behavior require validation on target hardware.

CuPy is a NumPy/SciPy-compatible array library for GPU-accelerated computing. It wraps NVIDIA's optimized libraries (cuBLAS, cuFFT, cuSOLVER, cuSPARSE, cuRAND) so standard array operations are already highly tuned. Most NumPy code works by simply changing the import.

> **Full documentation:** https://docs.cupy.dev/en/stable/

## Table of Contents

1. [Installation and Setup](#installation-and-setup)
2. [The Drop-In Replacement Pattern](#the-drop-in-replacement-pattern)
3. [Core API: cupy.ndarray](#core-api)
4. [Supported Operations](#supported-operations)
5. [Custom Kernels](#custom-kernels)
6. [Kernel Fusion](#kernel-fusion)
7. [Memory Management](#memory-management)
8. [Streams and Async Operations](#streams-and-async-operations)
9. [Multi-GPU](#multi-gpu)
10. [Performance Optimization](#performance-optimization)
11. [Interoperability](#interoperability)
12. [Key Differences from NumPy](#key-differences-from-numpy)
13. [Common Pitfalls](#common-pitfalls)
14. [Environment Variables](#environment-variables)

---

## Installation and Setup

Use `uv add` in standalone examples; follow the user's existing project package manager when one
is already configured.

```bash
uv add "cupy-cuda12x==14.2.*"    # For CUDA 12.x
uv add "cupy-cuda13x==14.2.*"    # For CUDA 13.x
```

CuPy 14.2 requires CUDA >= 12.0, Python >= 3.10, and NumPy >= 2.0 (it follows NumPy 2 type-promotion rules, NEP 50), and supports free-threaded Python. The `[ctk]` extra (e.g. `cupy-cuda13x[ctk]`) pulls the required CUDA runtime components from PyPI, so only the NVIDIA driver needs to be pre-installed.

Verify:
```python
import cupy as cp
print(cp.cuda.runtime.getDeviceCount())  # >= 1 means GPU is available
print(cp.show_config())                  # Full environment info
```

---

## The Drop-In Replacement Pattern

The fastest way to GPU-accelerate NumPy code: change the import.

```python
# Before (CPU)
import numpy as np
a = np.random.rand(10_000_000)
b = np.fft.fft(a)
c = np.sort(b.real)

# After (GPU)
import cupy as cp
a = cp.random.rand(10_000_000)
b = cp.fft.fft(a)
c = cp.sort(b.real)
```

### Data Transfer Between CPU and GPU

```python
# NumPy → CuPy (CPU → GPU)
gpu_array = cp.asarray(numpy_array)     # Zero-copy if already on current device
gpu_array = cp.array(numpy_array)       # Always copies

# CuPy → NumPy (GPU → CPU)
cpu_array = cp.asnumpy(gpu_array)       # Copy to CPU
cpu_array = gpu_array.get()             # Same thing
```

### Writing CPU/GPU Agnostic Code

```python
def normalize(x):
    xp = cp.get_array_module(x)  # Returns cupy or numpy depending on input
    return x / xp.linalg.norm(x)

# Works with both NumPy and CuPy arrays
normalize(numpy_array)   # Runs on CPU
normalize(cupy_array)    # Runs on GPU
```

CuPy arrays implement `__array_ufunc__` and `__array_function__`, so NumPy functions can dispatch to CuPy automatically when given CuPy arrays (NumPy >= 1.17).

---

## Core API

`cupy.ndarray` mirrors `numpy.ndarray` — same attributes (`shape`, `dtype`, `ndim`, `size`, `strides`, `T`), plus `device` (which GPU the array lives on).

**Important:** `cupy.ndarray` and `numpy.ndarray` are NOT implicitly convertible. Every conversion incurs a host-device data transfer.

### Array Creation

```python
cp.empty((1000, 1000), dtype=cp.float32)
cp.zeros((1000,), dtype=cp.float64)
cp.ones((512, 512), dtype=cp.float32)
cp.full((100,), fill_value=3.14, dtype=cp.float32)
cp.arange(0, 100, 0.1)
cp.linspace(0, 1, 1000)
cp.eye(100)
cp.random.rand(1000, 1000)                    # Uniform [0, 1)
cp.random.randn(1000, 1000)                   # Standard normal
cp.random.default_rng(42).normal(0, 1, 1000)  # Generator API
```

Many CuPy random methods accept `dtype`; check each method. NumPy Generator.random also supports float32/float64. Choose precision from the numerical contract.

---

## Supported Operations

CuPy implements most of NumPy and large parts of SciPy. All are GPU-accelerated.

### Array Math and Element-wise Operations
`sin`, `cos`, `tan`, `exp`, `log`, `log2`, `log10`, `sqrt`, `square`, `abs`, `power`, `add`, `subtract`, `multiply`, `divide`, `mod`, `clip`, `sign`, `ceil`, `floor`, `round`, `maximum`, `minimum`

### Reductions
`sum`, `prod`, `mean`, `std`, `var`, `min`, `max`, `argmin`, `argmax`, `cumsum`, `cumprod`, `any`, `all`, `nansum`, `nanmean`, `nanstd`, `nanvar`

### Linear Algebra (`cupy.linalg` — powered by cuBLAS/cuSOLVER)
`dot`, `matmul`, `@` operator, `tensordot`, `einsum`, `inner`, `outer`, `cholesky`, `qr`, `svd`, `eig`, `eigh`, `eigvalsh`, `norm`, `solve`, `inv`, `pinv`, `lstsq`, `det`, `slogdet`, `matrix_rank`, `matrix_power`

### FFT (`cupy.fft` — powered by cuFFT)
`fft`, `ifft`, `fft2`, `ifft2`, `fftn`, `ifftn`, `rfft`, `irfft`, `rfft2`, `irfft2`, `rfftn`, `irfftn`, `fftfreq`, `rfftfreq`, `fftshift`, `ifftshift`

### Sorting and Searching
`sort`, `argsort`, `partition`, `argpartition`, `argmin`, `argmax`, `where`, `nonzero`, `unique`, `searchsorted`

### Array Manipulation
`reshape`, `ravel`, `flatten`, `transpose`, `swapaxes`, `concatenate`, `stack`, `vstack`, `hstack`, `dstack`, `split`, `hsplit`, `vsplit`, `tile`, `repeat`, `pad`, `flip`, `fliplr`, `flipud`, `roll`, `rot90`, `broadcast_to`, `expand_dims`, `squeeze`

### Sparse Matrices (`cupyx.scipy.sparse`)
CSR, CSC, COO formats. Matrix-vector multiply, matrix-matrix multiply, conversions between formats. Powered by cuSPARSE. CuPy v14 adds support for large sparse matrices with 64-bit dimensions and nonzero counts.

### Signal Processing (`cupyx.scipy.signal`)
Convolution, correlation, filtering, window functions.

### Special Functions (`cupyx.scipy.special`)
Bessel functions, error functions, gamma functions, and more.

### Statistics
`mean`, `median`, `std`, `var`, `percentile`, `quantile`, `corrcoef`, `cov`, `histogram`, `bincount`, `digitize`

---

## Custom Kernels

When built-in operations aren't enough, CuPy offers several ways to write custom GPU code, ordered from simplest to most powerful.

### ElementwiseKernel — Custom Element-wise Operations

CuPy handles indexing and broadcasting automatically. You just write the per-element logic in C++.

```python
squared_diff = cp.ElementwiseKernel(
    'float32 x, float32 y',   # Input params
    'float32 z',               # Output params
    'z = (x - y) * 

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

