---
id: sciref-optimize-for-gpu-warp
name: "Scientific Ref: NVIDIA Warp Reference — GPU Simulation & Spatial Computing"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (optimize-for-gpu): NVIDIA Warp Reference — GPU Simulation & Spatial Computing"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "optimize gpu warp"
  - "nvidia warp reference — gpu simulation & spatial computing"
keywords:
  - "optimize"
  - "gpu"
  - "warp"
  - "specialized"
  - "scientific"
  - "reference"
  - "nvidia"
---

# NVIDIA Warp Reference — GPU Simulation & Spatial Computing

> Review: 2026-10-01. Code below is illustrative unless explicitly described as CPU-tested.
> GPU execution, performance, GDS, and multi-GPU behavior require validation on target hardware.

NVIDIA Warp is a Python framework for writing high-performance simulation and graphics code. It JIT-compiles Python functions decorated with `@wp.kernel` into efficient C++/CUDA code that runs on CPU or GPU. Warp is designed specifically for spatial computing — physics simulation, robotics, geometry processing, and differentiable programming — with rich built-in types (vectors, matrices, quaternions, transforms) and spatial primitives (meshes, volumes, hash grids, BVH).

Unlike Numba CUDA (which gives you raw thread/block control) or CuPy (which replaces NumPy ops), Warp provides a higher-level programming model with built-in support for differentiable simulation, spatial queries, and tile-based cooperative operations.

## Table of Contents

1. [Installation](#installation)
2. [When to Use Warp vs Other Libraries](#when-to-use-warp-vs-other-libraries)
3. [Kernels and Launch](#kernels-and-launch)
4. [Arrays](#arrays)
5. [Data Types](#data-types)
6. [Spatial Computing Primitives](#spatial-computing-primitives)
7. [Tile-Based Programming](#tile-based-programming)
8. [Differentiability](#differentiability)
9. [Streams, Events, and CUDA Graphs](#streams-events-and-cuda-graphs)
10. [Random Number Generation](#random-number-generation)
11. [Interoperability](#interoperability)
12. [Performance Optimization](#performance-optimization)
13. [Common Patterns](#common-patterns)
14. [Common Pitfalls](#common-pitfalls)

---

## Installation

```bash
uv add "warp-lang==1.17.*"              # PyPI wheels built with the CUDA 12.9 runtime
# uv add "warp-lang[examples]==1.17.*"  # Includes USD and example dependencies
```

Requires Python >= 3.10. Windows/Linux wheels support CPU or CUDA; the macOS Apple Silicon wheel is CPU-only, with no Metal backend. CUDA 12 wheels need an NVIDIA driver >=525. CUDA 13.0 builds (driver >= 580) are published on the project's GitHub Releases page rather than PyPI.

Verify installation:

```python
import warp as wp
wp.init()
# Prints device info, CUDA version, kernel cache location
```

---

## When to Use Warp vs Other Libraries

| Use Case | Best Choice | Why |
|----------|------------|-----|
| High-level rigid-body / robotics simulation | **Newton** | Maintained engine built on Warp; successor to removed `warp.sim` |
| Custom physics kernels (particles, cloth, fluids) | **Warp** | Spatial primitives, autodiff, and explicit kernels |
| Geometry processing (meshes, ray casting, SDFs) | **Warp** | Native mesh/volume/BVH types, spatial queries |
| Differentiable simulation for ML training | **Warp** | Automatic forward/backward AD, PyTorch/JAX integration |
| Robotics (kinematics, dynamics, control) | **Warp** | Transforms, quaternions, spatial vectors built-in |
| NumPy array math (FFT, linear algebra, sorting) | **CuPy** | Drop-in NumPy replacement, wraps cuBLAS/cuFFT |
| General custom CUDA kernels with explicit SIMT control | **Numba-CUDA-MLIR** or **Numba-CUDA** | Direct CUDA programming model and shared memory |
| Data wrangling / ETL on tabular data | **cuDF** | pandas API on GPU |
| ML training (sklearn-style) | **cuML** | scikit-learn API on GPU |

Warp and Numba both compile Python to CUDA, but serve different niches:
- **Warp** excels at simulation/spatial workloads with its rich type system (vec3, quat, transform, mesh, volume) and automatic differentiation
- **Numba** excels at raw CUDA programming where you need explicit thread/block control, shared memory management, and atomic operations on arbitrary data

Warp's former ready-made physics engine module `warp.sim` was removed in Warp 1.10. Use the
separate Newton library, built on Warp, for maintained high-level simulation APIs. Warp itself
remains the tool for writing custom kernels and domain primitives.

---

## Kernels and Launch

### Defining Kernels

```python
import warp as wp

@wp.kernel
def compute_forces(positions: wp.array(dtype=wp.vec3),
                   velocities: wp.array(dtype=wp.vec3),
                   forces: wp.array(dtype=wp.vec3),
                   dt: float):
    tid = wp.tid()

    pos = positions[tid]
    vel = velocities[tid]

    # Gravity
    force = wp.vec3(0.0, -9.81, 0.0)

    forces[tid] = force
```

### Launching Kernels

```python
# 1D launch
wp.launch(kernel=compute_forces,
          dim=num_particles,
          inputs=[positions, velocities, forces, 0.01],
          device="cuda")

# 2D launch (e.g., image processing)
wp.launch(kernel=compute_image, dim=(1024, 1024), inputs=[img], device="cuda")

# 3D launch
wp.launch(kernel=compute_field, dim=(nx, ny, nz), inputs=[field], device="cuda")
```

Inside 2D/3D kernels, retrieve indices with:

```python
i, j = wp.tid()       # 2D
i, j, k = wp.tid()    # 3D
```

### User Functions

```python
@wp.func
def spring_force(x0: wp.vec3, x1: wp.vec3, rest_length: float, stiffness: float):
    delta = x1 - x0
    length = wp.length(delta)
    if length <= 1.0e-8:
        return wp.vec3(0.0, 0.0, 0.0)  # Chosen degenerate-spring convention
    direction = delta / length
    return stiffness * (length - rest_length) * direction
```

Functions can be called from kernels, support overloading, and can return multiple values.

### User Structs

```python
@wp.struct
class Particle:
    pos: wp.vec3
    vel: wp.vec3
    mass: float
    active: int
```

---

## Arrays

Warp arrays are typed, device-aware containers (1D to 4D):

```python
# Allocate
positions = wp.zeros(n, dtype=wp.vec3, device="cuda")
grid = wp.empty(shape=(nx, ny, nz), dtype=float, device="cuda")

# From NumPy
import numpy as np
data = np.random.rand(1000, 3).astype(np.float32)
wp_data = wp.from_numpy(data, dtype=wp.vec3, device="cuda")

# Back to NumPy (synchronizes GPU automatically)
np_data = wp_data.numpy()

# Array math operators
c = 2.0 * a + b   # Element-wise, GPU-accelerated
c *= 10.0          # In-place
```

Type aliases for kernel signatures: `wp.array2d`, `wp.array3d`, `wp.array4d`.

---

## Data Types

### Scalars
`bool`, `int8`, `uint8`, `int16`, `uint16`, `int32` (alias: `int`), `uint32`, `int64`, `uint64`, `float16`, `float32` (alias: `float`), `float64`

### Vectors
`vec2`, `vec3`, `vec4` — float32 by default. Variants for every scalar type: `vec3f`, `vec3d`, `vec3h`, `vec3i`, etc.

```python
v = wp.vec3

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

