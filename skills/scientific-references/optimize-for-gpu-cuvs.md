---
id: sciref-optimize-for-gpu-cuvs
name: "Scientific Ref: cuVS Reference"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (optimize-for-gpu): cuVS Reference"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "optimize gpu cuvs"
  - "cuvs reference"
keywords:
  - "optimize"
  - "gpu"
  - "cuvs"
  - "specialized"
  - "scientific"
  - "reference"
---

# cuVS Reference

> Review: 2026-10-01. Code below is illustrative unless explicitly described as CPU-tested.
> GPU execution, performance, GDS, and multi-GPU behavior require validation on target hardware.

cuVS is NVIDIA's GPU-accelerated library for exact and approximate nearest-neighbor search, part
of the RAPIDS ecosystem. It provides CAGRA, IVF-Flat, IVF-PQ, brute-force, and CPU-serving
interoperability. Compare equal metrics and exactness requirements, validate ANN recall, and
benchmark build, search, transfer, and serialization costs separately.

> **Full documentation:** https://docs.nvidia.com/cuvs/home
> **Reviewed release source:** https://github.com/rapidsai/cuvs/tree/v26.08.00/python/cuvs/cuvs

## Table of Contents

1. [Installation and Setup](#installation-and-setup)
2. [When to Use cuVS](#when-to-use-cuvs)
3. [Index Selection Guide](#index-selection-guide)
4. [CAGRA — Graph-Based Index](#cagra)
5. [IVF-Flat — Inverted File Index](#ivf-flat)
6. [IVF-PQ — Compressed Inverted File Index](#ivf-pq)
7. [Brute Force — Exact Search](#brute-force)
8. [HNSW — CPU Search from GPU Index](#hnsw)
9. [Distance Metrics](#distance-metrics)
10. [Filtering](#filtering)
11. [Multi-GPU](#multi-gpu)
12. [Memory and Performance](#memory-and-performance)
13. [Interoperability](#interoperability)
14. [Common Patterns](#common-patterns)

---

## Installation and Setup

Use `uv add` in standalone examples; follow the user's existing project package manager when one
is already configured.

```bash
uv add --extra-index-url=https://pypi.nvidia.com "cuvs-cu12==26.8.*"   # For CUDA 12.x
uv add --extra-index-url=https://pypi.nvidia.com "cuvs-cu13==26.8.*"   # For CUDA 13.x
```

cuVS wheels (including the companion `libcuvs` wheel) are also published directly to PyPI, so the extra index is optional — but the official cuVS docs still show it and it does no harm.

**Platform:** Linux and WSL2 only (no native macOS or Windows).
**Requires:** NVIDIA GPU with CUDA 12.x or 13.x support, Python 3.11+, CuPy recommended for GPU arrays.

Verify:
```python
from cuvs.neighbors import cagra
import cupy as cp

dataset = cp.random.rand(1000, 128, dtype=cp.float32)
index = cagra.build(cagra.IndexParams(), dataset)
print("cuVS working — built CAGRA index")
```

---

## When to Use cuVS

cuVS is the right tool when the user needs:
- **Nearest neighbor search** on high-dimensional vectors (embeddings)
- **Similarity search** for RAG, recommender systems, image/text/audio retrieval
- **k-NN graph construction** for clustering or visualization pipelines
- **Vector database backends** — cuVS powers search in Milvus, Lucene, Kinetica, and Faiss GPU
- **Replacing Faiss, Annoy, ScaNN, or sklearn NearestNeighbors** with GPU acceleration

cuVS is NOT the right tool for:
- General machine learning (use cuML instead)
- Small or low-dimensional datasets where build, transfer, or launch overhead dominates in a
  representative benchmark
- CPU-only environments with no GPU available

---

## Index Selection Guide

| Index | Best For | Build Speed | Search Speed | Memory | Accuracy |
|-------|----------|-------------|--------------|--------|----------|
| **CAGRA** | Strong first ANN candidate | Fast | Fast | Medium | Tunable |
| **IVF-Flat** | High-recall ANN without vector compression | Medium | Fast | High (stores full vectors) | Tunable |
| **IVF-PQ** | Large datasets that don't fit in GPU memory | Medium | Fast | Low (compressed) | Good |
| **Brute Force** | Small datasets or ground truth | N/A | Slow at scale | High | Exact |
| **HNSW** | CPU-side serving from GPU-built index | Slow | Fast (CPU) | Medium | High |

Benchmark CAGRA as the first ANN candidate, then compare IVF-PQ when memory is tight and IVF-Flat
when avoiding vector compression matters. Use brute force for exact search and recall ground truth.
Choose build and search parameters from measured latency, throughput, memory, and recall targets.

---

## CAGRA

CAGRA (CUDA Accelerated Graph-based) is a graph-based ANN index optimized for GPU. Treat it as a strong ANN candidate and compare recall, memory, and end-to-end latency.

### Build

```python
import cupy as cp
from cuvs.neighbors import cagra

n_samples = 1_000_000
n_features = 128
dataset = cp.random.rand(n_samples, n_features, dtype=cp.float32)

# Default parameters work well for most cases
index_params = cagra.IndexParams(
    metric="sqeuclidean",             # "sqeuclidean", "inner_product", "cosine"
    intermediate_graph_degree=128,     # Higher = better quality, slower build
    graph_degree=64,                   # Final graph degree (lower = less memory)
    build_algo="ivf_pq",              # "ivf_pq", "nn_descent", "iterative_cagra_search", or "ace"
)

index = cagra.build(index_params, dataset)
```

### Search

```python
from cuvs.common import Resources

queries = cp.random.rand(1000, n_features, dtype=cp.float32)

search_params = cagra.SearchParams(
    itopk_size=64,       # Intermediate top-k (higher = more accurate, slower)
    search_width=1,      # Starting nodes per iteration
    max_iterations=0,    # 0 = auto
    algo="auto",         # "auto", "single_cta", "multi_cta", "multi_kernel"
)

resources = Resources()
distances, neighbors = cagra.search(
    search_params, index, queries, k=10, resources=resources
)
resources.sync()

# distances: shape (1000, 10) — squared Euclidean distances
# neighbors: shape (1000, 10) — indices into original dataset
```

### Save / Load

Persist the exact cuVS release, dtype, metric and dataset identity alongside the index.
Serialized formats are experimental and not guaranteed portable across releases.

```python
cagra.save("my_index.cagra", index)
loaded_index = cagra.load("my_index.cagra")
```

### Extend

```python
new_data = cp.random.rand(10_000, n_features, dtype=cp.float32)
extended_index = cagra.extend(cagra.ExtendParams(), index, new_data)
```

### With Compression (for large datasets)

```python
from cuvs.neighbors.cagra import CompressionParams

index_params = cagra.IndexParams(
    compression=CompressionParams(
        pq_bits=8,
        pq_dim=64,
    )
)
index = cagra.build(index_params, dataset)
```

---

## IVF-Flat

IVF-Flat partitions the dataset into clusters (inverted file) and stores full vectors. Higher accuracy than IVF-PQ but uses more memory.

### Build

```python
from cuvs.neighbors import ivf_flat

build_params = ivf_flat.IndexParams(
    n_lists=1024,                    # Number of clusters (sqrt(n_samples) is a good start)
  

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

