---
id: sciref-optimize-for-gpu-decision-framework
name: "Scientific Ref: Decision Framework: Which Library to Use"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (optimize-for-gpu): Decision Framework: Which Library to Use"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "optimize gpu decision framework"
  - "decision framework: which library to use"
keywords:
  - "optimize"
  - "gpu"
  - "decision"
  - "framework"
  - "specialized"
  - "scientific"
  - "reference"
---

# Decision Framework: Which Library to Use

Each RAPIDS/GPU library, the CPU library it replaces, what it is good at, and when it is
the wrong choice — CuPy, Numba CUDA, Warp, cuDF, cuML, cuGraph, KvikIO, cuxfilter, cuCIM,
cuVS, cuSpatial, and RAFT — plus guidance on combining them.

Choose the right tool based on what the user's code actually does. Read the appropriate reference file(s) before writing any GPU code.

First decide whether a port is justified: establish an end-to-end baseline, estimate peak device
memory including temporaries, and identify transfer and fallback boundaries. Prefer an accelerator
or backend mode before a native rewrite, and prefer a maintained library operation before a custom
kernel. Validate output semantics and use synchronized GPU timing on representative data.

### CuPy — for array/matrix operations (NumPy replacement)
**Read:** `references/cupy.md`

Use CuPy when the user's code is primarily:
- NumPy array operations (element-wise math, linear algebra, FFT, sorting, reductions)
- SciPy operations (sparse matrices, signal processing, image filtering, special functions)
- Compatible chains of numeric NumPy calls — check CuPy coverage and semantics before porting

CuPy wraps NVIDIA's optimized libraries (cuBLAS, cuFFT, cuSOLVER, cuSPARSE, cuRAND) so standard operations are already tuned. Many numeric operations have matching names; unsupported dtypes, argument differences, and transfer boundaries still need review.

**Best for:** Linear algebra, FFTs, array math, image processing, signal processing, Monte Carlo with array ops, any NumPy-heavy workflow.

### Numba-CUDA-MLIR / Numba-CUDA — for custom GPU kernels
**Read:** `references/numba.md`

Use this path when the user needs:
- Custom algorithms that don't map to standard array operations
- Fine-grained control over GPU threads, blocks, and shared memory
- Reduction operations with custom logic
- Stencil computations or neighbor-dependent calculations
- Anything requiring the CUDA programming model directly

For new projects, evaluate **Numba-CUDA-MLIR**, where NVIDIA is doing new feature development.
Use the established `numba-cuda` package for existing `numba.cuda` code, compatibility, or features
not yet available in the MLIR implementation; it is in maintenance mode through the CUDA 13
lifetime. Do not invest in custom kernels until profiling rules out CuPy or another tuned library.

**Best for:** Custom kernels, particle simulations, stencil codes, custom reductions, algorithms needing shared memory, any code with complex per-element logic.

### Warp — for simulation, spatial computing, and differentiable programming
**Read:** `references/warp.md`

Use Warp when the user's code is primarily:
- Physics simulation (particles, cloth, fluids, rigid bodies, DEM, SPH)
- Geometry processing (mesh operations, ray casting, signed distance fields, marching cubes)
- Robotics (kinematics, dynamics, control with transforms and quaternions)
- Differentiable simulation for ML training (integrates with PyTorch/JAX autograd)
- Any Python simulation loop that needs to be JIT-compiled to GPU
- Spatial computing with meshes, volumes (NanoVDB), hash grids, or BVH queries

Warp JIT-compiles `@wp.kernel` Python functions to CUDA, with built-in types for spatial computing
(vec3, mat33, quat, transform) and primitives for geometry queries (Mesh, Volume, HashGrid, BVH).
Warp can generate adjoint kernels for differentiable programs. The higher-level `warp.sim` module
was removed in Warp 1.10; use the separate **Newton** engine for maintained high-level rigid-body,
robotics, and simulation-environment APIs, and use Warp for custom kernels and domain primitives.

**Best for:** Physics simulation, mesh ray casting, particle systems, differentiable rendering, robotics kinematics, SDF operations, any workload combining spatial data structures with GPU compute.

**Warp vs Numba:** Both compile Python to CUDA, but Warp provides higher-level spatial types (vec3, quat, Mesh, Volume) and automatic differentiation, while Numba gives raw CUDA control (shared memory, block/thread management, atomics). Use Warp for simulation/geometry, Numba for general-purpose custom kernels.

### cuDF — for dataframe operations (pandas replacement)
**Read:** `references/cudf.md`

Use cuDF when the user's code is primarily:
- pandas DataFrame operations (filtering, groupby, joins, aggregations)
- CSV/Parquet/JSON reading and processing
- ETL pipelines or data wrangling on large datasets
- Any pandas-heavy workflow on datasets that fit in GPU memory

cuDF's `cudf.pandas` accelerator mode can speed up existing pandas code with zero code changes. For maximum performance, use the native cuDF API.

**Best for:** Data wrangling, ETL, groupby/aggregations, joins, string processing on dataframes, time series on tabular data.

### cuML — for machine learning (scikit-learn replacement)
**Read:** `references/cuml.md`

Use cuML when the user's code is primarily:
- scikit-learn estimators (classification, regression, clustering, dimensionality reduction)
- ML preprocessing (scaling, encoding, imputation, feature extraction)
- Hyperparameter tuning or cross-validation
- Tree model inference (XGBoost, LightGBM, sklearn Random Forest via FIL)
- UMAP, t-SNE, HDBSCAN, or KNN on large datasets

Start with cuML's `cuml.accel` accelerator mode when compatibility permits. Move to the native
cuML API for unsupported estimators, explicit output control, or a measured performance reason.
Benchmark the user's estimator, dimensions, and end-to-end pipeline rather than relying on headline
speedup ranges.

**Best for:** Classification, regression, clustering, dimensionality reduction, preprocessing pipelines, model inference, any scikit-learn-heavy workflow.

### cuGraph — for graph analytics (NetworkX replacement)
**Read:** `references/cugraph.md`

Use cuGraph when the user's code is primarily:
- NetworkX graph algorithms (centrality, community detection, shortest paths, PageRank)
- Graph construction and analysis on large networks
- Social network analysis, knowledge graphs, or recommendation systems
- Supported graph algorithms with enough repeated work to amortize conversion

Start with the `nx-cugraph` backend and inspect fallback behavior. Move to the native cuGraph API
with cuDF edge lists for unsupported operations or a measured performance reason. Include graph
construction and host-device conversion in end-to-end benchmarks.

**Best for:** PageRank, betweenness ce

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

