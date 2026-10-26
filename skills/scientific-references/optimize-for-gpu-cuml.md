---
id: sciref-optimize-for-gpu-cuml
name: "Scientific Ref: cuML Reference"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (optimize-for-gpu): cuML Reference"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "optimize gpu cuml"
  - "cuml reference"
keywords:
  - "optimize"
  - "gpu"
  - "cuml"
  - "specialized"
  - "scientific"
  - "reference"
---

# cuML Reference

> Review: 2026-10-01. Code below is illustrative unless explicitly described as CPU-tested.
> GPU execution, performance, GDS, and multi-GPU behavior require validation on target hardware.

cuML is NVIDIA's GPU-accelerated machine learning library within the RAPIDS ecosystem. It
provides scikit-learn-compatible APIs for classification, regression, clustering, dimensionality
reduction, preprocessing, and model selection. Performance depends on algorithm, shape, dtype,
fallback behavior, and transfer cost; benchmark the complete pipeline on representative data.

> **Full documentation:** https://docs.nvidia.com/cuml/26.08/

## Table of Contents

1. [Installation and Setup](#installation-and-setup)
2. [Two Usage Modes](#two-usage-modes)
3. [cuml.accel Accelerator Mode](#cumlaccel-accelerator-mode)
4. [Direct cuML API](#direct-cuml-api)
5. [Algorithm Catalog](#algorithm-catalog)
6. [Input/Output Type Handling](#inputoutput-type-handling)
7. [Preprocessing](#preprocessing)
8. [Feature Extraction](#feature-extraction)
9. [Model Selection and Tuning](#model-selection-and-tuning)
10. [Forest Inference Library (FIL)](#forest-inference-library)
11. [Multi-GPU with Dask](#multi-gpu-with-dask)
12. [Model Serialization](#model-serialization)
13. [Memory Management](#memory-management)
14. [Performance Optimization](#performance-optimization)
15. [Interoperability](#interoperability)
16. [Key Differences from sklearn](#key-differences-from-sklearn)
17. [Common Migration Patterns](#common-migration-patterns)

---

## Installation and Setup

Use `uv add` in standalone examples; follow the user's existing project package manager when one
is already configured.

```bash
uv add "cuml-cu12==26.8.*"    # For CUDA 12.x
uv add "cuml-cu13==26.8.*"    # For CUDA 13.x
```

cuML wheels are published directly to PyPI (since RAPIDS 25.10) — the `--extra-index-url=https://pypi.nvidia.com` extra index is no longer required.

**Platform:** Linux and WSL2 only (no native macOS or Windows).
**Requires:** Python >= 3.11, scikit-learn >= 1.6, NVIDIA GPU with CUDA 12.x or 13.x support.

Verify:
```python
import cuml
print(cuml.__version__)

from cuml.datasets import make_blobs
X, y = make_blobs(n_samples=1000, n_features=10)
print(f"Generated {X.shape[0]} samples on GPU")
```

---

## Two Usage Modes

### 1. cuml.accel (Zero-Code-Change)
Transparently intercepts sklearn, umap-learn, and hdbscan calls and routes them to GPU. Falls back to CPU for unsupported operations. Best for: quick acceleration of existing sklearn code, mixed codebases, prototyping.

### 2. Direct cuML API
Replace `from sklearn` with `from cuml`. Maximum performance, explicit control over GPU execution. Best for: production pipelines, maximum performance, new GPU-first code.

---

## cuml.accel Accelerator Mode

The fastest path from sklearn to GPU — no code changes required. Similar to `cudf.pandas` for pandas.

### Activation

```python
# Jupyter/IPython (MUST be the first cell, before any sklearn import)
%load_ext cuml.accel

import sklearn  # Now GPU-accelerated
from sklearn.cluster import KMeans  # Runs on GPU transparently
```

```bash
# Command line
python -m cuml.accel script.py
python -m cuml.accel -v script.py     # With info logging
python -m cuml.accel -vv script.py    # With debug logging
```

```python
# Programmatic (call BEFORE importing sklearn)
import cuml
cuml.accel.install()

from sklearn.cluster import KMeans  # Now GPU-accelerated
```

```bash
# Environment variable
CUML_ACCEL_ENABLED=1 python script.py
```

### How It Works

- Intercepts sklearn/umap-learn/hdbscan imports and replaces estimators with GPU versions.
- If an operation isn't supported on GPU, it silently falls back to CPU sklearn.
- Uses managed memory by default — host RAM augments GPU VRAM.
- Models pickled under cuml.accel load as standard sklearn objects in non-GPU environments.
- Accelerates 30+ algorithms across sklearn, umap-learn, and hdbscan. Recent releases (26.04-26.06) expanded coverage to preprocessing estimators (StandardScaler, MinMaxScaler, MaxAbsScaler, PolynomialFeatures, LabelEncoder) and SpectralClustering.
- 26.08 requires scikit-learn >=1.6; specific accelerated preprocessors require >=1.8. Check the [26.08 compatibility page](https://docs.nvidia.com/cuml/26.08/cuml-accel/compatibility/) for method and parameter restrictions.

### Known Fallback Triggers (Runs on CPU Instead)

- Sparse input data (most algorithms)
- Callable parameters (e.g., callable `init` for KMeans)
- Certain parameter values: `n_components="mle"` for PCA, `positive=True` for linear models, warm starts
- Unsupported distance metrics for neighbors algorithms
- Multi-output targets for Random Forest
- String/object dtypes — must pre-encode with LabelEncoder first

### Numerical Precision

GPU estimators can use different algorithms, solvers, tree-split approximations, defaults, and random streams. Differences can exceed roundoff. Compare held-out quality, prediction agreement, class/feature order and calibration; use sign/subspace-aware checks for decompositions. A matching seed does not imply matching models.

---

## Direct cuML API

The API follows fit/predict/transform conventions, but signatures, defaults and supported inputs differ. Consult the chosen estimator before replacing imports.

```python
from cuml.cluster import DBSCAN
from cuml.datasets import make_blobs

# Create data directly on GPU
X, y = make_blobs(n_samples=100_000, centers=5, n_features=10, random_state=42)

# Fit — runs on GPU
model = DBSCAN(eps=1.0, min_samples=5)
model.fit(X)
print(model.labels_)
```

```python
from cuml import LinearRegression
from cuml.datasets import make_regression
from cuml.model_selection import train_test_split

X, y = make_regression(n_samples=100_000, n_features=50, noise=0.1)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

model = LinearRegression()
model.fit(X_train, y_train)
predictions = model.predict(X_test)
score = model.score(X_test, y_test)
print(f"R2 score: {score:.4f}")
```

---

## Algorithm Catalog

### Clustering

| cuML | sklearn Equivalent | Multi-GPU |
|------|-------------------|-----------|
| `cuml.KMeans` | `sklearn.cluster.KMeans` | Yes |
| `cuml.DBSCAN` | `sklearn.cluster.DBSCAN` | Yes |
| `cuml.AgglomerativeClustering` | `sklearn.cluster.AgglomerativeClustering` | No |
| `cuml.cluster.hdbscan.HDBSCAN` | `hdbscan.HDBSCAN` | No |
| `cuml.cluster.SpectralClustering` | `sklearn.cluster.SpectralClustering` |

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

