---
id: sciref-optimize-for-gpu-cugraph
name: "Scientific Ref: cuGraph Reference"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (optimize-for-gpu): cuGraph Reference"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "optimize gpu cugraph"
  - "cugraph reference"
keywords:
  - "optimize"
  - "gpu"
  - "cugraph"
  - "specialized"
  - "scientific"
  - "reference"
---

# cuGraph Reference

> Review: 2026-10-01. Code below is illustrative unless explicitly described as CPU-tested.
> GPU execution, performance, GDS, and multi-GPU behavior require validation on target hardware.

cuGraph is NVIDIA's GPU-accelerated graph analytics library within the RAPIDS ecosystem. It
supports both a direct Python API and an **nx-cugraph** NetworkX backend. Performance depends on
algorithm, graph topology and size, graph-construction cost, fallback behavior, and GPU hardware,
so benchmark the complete workload instead of promising a fixed speedup.

> **Full documentation:** https://docs.nvidia.com/cugraph/26.08/
> **Version target:** 26.08
> **Repository:** https://github.com/rapidsai/cugraph

## Table of Contents

1. [Installation and Setup](#installation-and-setup)
2. [Two Usage Modes](#two-usage-modes)
3. [nx-cugraph: Zero-Code-Change NetworkX Backend](#nx-cugraph-zero-code-change-networkx-backend)
4. [Direct cuGraph API](#direct-cugraph-api)
5. [Graph Creation and Data Loading](#graph-creation-and-data-loading)
6. [Supported Graph Types](#supported-graph-types)
7. [Algorithm Catalog](#algorithm-catalog)
8. [Multi-GPU Support with Dask](#multi-gpu-support-with-dask)
9. [GNN Support (cugraph-pyg and WholeGraph)](#gnn-support)
10. [Performance Characteristics and Benchmarks](#performance-characteristics-and-benchmarks)
11. [Memory Management](#memory-management)
12. [Interoperability](#interoperability)
13. [Known Limitations vs NetworkX](#known-limitations-vs-networkx)
14. [Common Migration Patterns](#common-migration-patterns)

---

## Installation and Setup

Use `uv add` in standalone examples; follow the user's existing project package manager when one
is already configured.

```bash
uv add --extra-index-url=https://pypi.nvidia.com "cugraph-cu12==26.8.*"    # Core cuGraph for CUDA 12.x
uv add --extra-index-url=https://pypi.nvidia.com "nx-cugraph-cu12==26.8.*" # NetworkX backend
# For CUDA 13.x, use the -cu13 packages: cugraph-cu13, nx-cugraph-cu13
```

26.08 cuGraph and nx-cugraph wheels are published on PyPI. The NVIDIA index is optional for these current packages; historical releases may still use stub distributions.

**Platform:** Linux and WSL2 only (no native macOS or Windows).
**Requires:** Python >= 3.11, NVIDIA GPU with CUDA 12.x or 13.x support, NetworkX >= 3.2 (>= 3.5 recommended for optimal nx-cugraph).

Verify:
```python
import cugraph
print(cugraph.__version__)

# Quick test with built-in dataset
from cugraph.datasets import karate
G = karate.get_graph()
result = cugraph.degree_centrality(G)
print(result.head())
```

---

## Two Usage Modes

### Mode 1: nx-cugraph Backend (Zero Code Change)
Accelerate existing NetworkX code by setting one environment variable. No code changes required.

```bash
NX_CUGRAPH_AUTOCONFIG=True python my_networkx_script.py
```

### Mode 2: Direct cuGraph API
Use cuGraph's native API for maximum control, working directly with cuDF DataFrames and cuGraph graph objects.

```python
import cugraph
import cudf

edges = cudf.DataFrame({
    "src": [0, 1, 2, 0],
    "dst": [1, 2, 3, 3],
    "weight": [1.0, 2.0, 1.5, 3.0]
})
G = cugraph.Graph()
G.from_cudf_edgelist(edges, source="src", destination="dst", edge_attr="weight")
result = cugraph.pagerank(G)
```

**When to use which:**
- **nx-cugraph**: Existing NetworkX codebases, rapid prototyping, when you want zero migration effort
- **Direct API**: Maximum performance, multi-GPU workflows, integration with cuDF/cuML pipelines, GNN training

---

## nx-cugraph: Zero-Code-Change NetworkX Backend

nx-cugraph is a NetworkX backend that transparently redirects supported algorithm calls to GPU-accelerated cuGraph implementations.

### How It Works

NetworkX >= 3.2 has a backend dispatch system. When nx-cugraph is installed and enabled, NetworkX automatically redirects supported function calls to GPU implementations. Unsupported calls fall back to default NetworkX.

### Three Ways to Enable

**1. Environment Variable (recommended for zero code change):**
```bash
export NX_CUGRAPH_AUTOCONFIG=True
python my_script.py
# OR inline:
NX_CUGRAPH_AUTOCONFIG=True python my_script.py
```

**2. Keyword Argument (explicit per-call):**
```python
import networkx as nx
result = nx.betweenness_centrality(G, k=10, backend="cugraph")
```

**3. Type-Based Dispatch (explicit graph conversion):**
```python
import networkx as nx
import nx_cugraph as nxcg

G_nx = nx.karate_club_graph()
G_gpu = nxcg.from_networkx(G_nx)  # Convert once, reuse for multiple algorithms
result = nx.pagerank(G_gpu)       # Automatically dispatched to GPU
```

Since 26.04, GPU-backed graphs can also be constructed directly, e.g. `nx.Graph(backend="cugraph")`.

### Supported Algorithms in nx-cugraph

**Centrality:**
- `betweenness_centrality`, `edge_betweenness_centrality`
- `degree_centrality`, `in_degree_centrality`, `out_degree_centrality`
- `eigenvector_centrality`, `katz_centrality`

**Community:**
- `louvain_communities`, `leiden_communities`

**Components:**
- `connected_components`, `is_connected`, `number_connected_components`
- `node_connected_component`
- `weakly_connected_components`, `is_weakly_connected`, `number_weakly_connected_components`

**Clustering:**
- `average_clustering`, `clustering`, `transitivity`, `triangles`

**Core:**
- `core_number`, `k_truss`

**Link Analysis:**
- `pagerank`, `hits`

**Link Prediction:**
- `jaccard_coefficient`

**Shortest Paths (23+ functions):**
- `shortest_path`, `shortest_path_length`
- `has_path`, `all_pairs_shortest_path`, `all_pairs_shortest_path_length`
- `dijkstra_path`, `dijkstra_path_length`, `all_pairs_dijkstra`, `all_pairs_dijkstra_path_length`
- `bellman_ford_path`, `bellman_ford_path_length`, `all_pairs_bellman_ford_path_length`
- `single_source_shortest_path`, `single_source_shortest_path_length`
- `single_source_dijkstra`, `single_source_dijkstra_path`, `single_source_dijkstra_path_length`
- `single_source_bellman_ford`, `single_source_bellman_ford_path`, `single_source_bellman_ford_path_length`
- `single_target_shortest_path_length`

**Traversal:**
- `bfs_edges`, `bfs_layers`, `bfs_predecessors`, `bfs_successors`, `bfs_tree`
- `generic_bfs_edges`, `descendants_at_distance`

**DAG:**
- `ancestors`, `descendants`

**Bipartite:**
- `betweenness_centrality` (bipartite), `biadjacency_matrix`
- `complete_bipartite_graph`, `from_biadjacency_matrix`

**Tree:**
- `is_arborescence`, `is_branching`, `is_forest`, `is_tree`

**Operators:**
- `complement`, `reverse`

**Reciprocit

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

