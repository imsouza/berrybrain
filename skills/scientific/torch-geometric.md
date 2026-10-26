---
id: sci-torch-geometric
name: "Scientific: torch-geometric"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Supports PyTorch Geometric (PyG) graph neural networks — node/link/graph classification, message passing (GCN, GAT, GraphSAGE, GIN), heterogeneous graphs, neighbor sampling, and custom datasets. Use when working with torch_geometric, not for general NetworkX analytics or non-grap"
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "torch geometric"
  - "torch-geometric"
keywords:
  - "torch"
  - "geometric"
  - "supports"
  - "pytorch"
  - "graph"
  - "neural"
  - "networks"
---

# PyTorch Geometric (PyG)

PyG is the standard library for Graph Neural Networks built on PyTorch. It provides data structures for graphs, 60+ GNN layer implementations, scalable mini-batch training, and support for heterogeneous graphs.

## Installation

Reviewed released **torch-geometric 2.8.0.post1** (2026-10-01); CPU examples tested with **Python 3.13 / PyTorch 2.14.1**. Rolling `latest` docs identify 2.9.0; check the installed release before adopting new APIs. PyG 2.8 requires PyTorch 2.9+; its original release table covers 2.9–2.12. Our 2.14.1 core tests do not establish every extension/backend combination.

```bash
# Install the PyTorch build for your platform from https://pytorch.org/get-started/locally/
uv pip install torch==2.14.1
uv pip install torch-geometric==2.8.0.post1
python -c "import torch, torch_geometric; print(torch.__version__, torch.version.cuda, torch_geometric.__version__)"
```

Basic tensor-based layers need no extensions. Neighbor sampling requires `pyg-lib` or `torch-sparse`; spatial k-NN operators require `pyg-lib` in 2.8. `torch-cluster` and `torch-spline-conv` are deprecated and ignored. Inspect the [wheel index](https://data.pyg.org/whl/) for your exact Python/OS/Torch/CUDA tuple. Never install wheels for a different Torch release merely because core imports succeed. The tested macOS ARM CPU extension is below; choose a different matching wheel for other platforms, and verify its operators:

```bash
uv pip install --only-binary=:all: "pyg-lib==0.9.0+pt214" \
  -f https://data.pyg.org/whl/torch-2.14.0+cpu.html
```

Conda packages are no longer provided for Torch >2.5. See [installation](https://pytorch-geometric.readthedocs.io/en/latest/install/installation.html) and [2.8 release changes](https://github.com/pyg-team/pytorch_geometric/releases/tag/2.8.0). Optional sampling/GPU/distributed/download examples below are illustrative unless covered by the CPU checks in [review notes](references/review.md).

## Core Concepts

### Graph Data: `Data` and `HeteroData`

A graph lives in a `Data` object. The key attributes:

```python
from torch_geometric.data import Data

data = Data(
    x=node_features,          # [num_nodes, num_node_features]
    edge_index=edge_index,     # [2, num_edges] — COO format, dtype=torch.long
    edge_attr=edge_features,   # [num_edges, num_edge_features]
    y=labels,                  # node-level [num_nodes, *] or graph-level [1, *]
    pos=positions,             # [num_nodes, num_dimensions] (for point clouds/spatial)
)
```

**`edge_index` format is critical**: it's a `[2, num_edges]` tensor where `edge_index[0]` = source nodes, `edge_index[1]` = target nodes. It is NOT a list of tuples. If you have edge pairs as rows, transpose and call `.contiguous()`:

```python
# If edges are [[src1, dst1], [src2, dst2], ...] — transpose first:
edge_index = edge_pairs.t().contiguous()
```

For undirected graphs, include both directions: edge (0,1) needs both `[0,1]` and `[1,0]` in edge_index.

If node features are absent, set `data.num_nodes` explicitly from the node table. Inferring it from `edge_index.max() + 1` misses isolated nodes, which can corrupt batching offsets and outputs. Check `data.validate(raise_on_error=True)` after construction, including an edge-free or isolated-node case.

For heterogeneous graphs, use `HeteroData` — see the Heterogeneous Graphs section below.

### Datasets

PyG bundles many standard datasets that auto-download and preprocess:

```python
from torch_geometric.datasets import Planetoid, TUDataset

# Single-graph node classification (Cora, Citeseer, Pubmed)
dataset = Planetoid(root='./data/Cora', name='Cora', split='public')
data = dataset[0]  # single graph with train/val/test masks

# Multi-graph classification (ENZYMES, MUTAG, IMDB-BINARY, etc.)
dataset = TUDataset(root='./data/TU', name='ENZYMES')
# dataset[0], dataset[1], ... are individual graphs
```

Common datasets by task:
- **Node classification**: Planetoid (Cora/Citeseer/Pubmed), OGB (ogbn-arxiv, ogbn-products, ogbn-mag)
- **Graph classification**: TUDataset (MUTAG, ENZYMES, PROTEINS, IMDB-BINARY), OGB (ogbg-molhiv)
- **Link prediction**: OGB (ogbl-collab, ogbl-citation2)
- **Molecular**: QM7b, QM9, MoleculeNet
- **Point cloud/mesh**: ShapeNet, ModelNet(name="10" or "40"), FAUST (manual download)

Dataset classes manage provider downloads; they are not API search endpoints. Preserve the dataset version, split and preprocessing. OGB benchmarks use the separate `ogb` package/evaluator; do not replace their official split with a random split. See [review notes](references/review.md) for verified download locations and unexecuted large datasets.

### Transforms

Transforms preprocess or augment graph data, analogous to torchvision transforms:

```python
import torch_geometric.transforms as T
from torch_geometric.datasets import ShapeNet

# Common transforms
T.NormalizeFeatures()    # Shift by minimum, then divide row sum (clamped >=1)
T.ToUndirected()         # Add reverse edges to make graph undirected
T.AddSelfLoops()         # Add self-loop edges
T.KNNGraph(k=6)          # Build k-NN graph from positions; requires pyg-lib
T.RandomJitter(0.01)     # Random noise augmentation on positions
T.Compose([...])         # Chain multiple transforms

# Apply as pre_transform (once, saved to disk) or transform (every access)
dataset = ShapeNet(root='./data', pre_transform=T.KNNGraph(k=6),
                   transform=T.RandomJitter(0.01))
```

`ToUndirected` may merge/reduce duplicate edge attributes (default sum); confirm weight/label semantics before applying it. Adding self-loops can also duplicate existing loops. Do not make directed or temporal relations undirected without a scientific reason.

## Building GNN Models

### Quick Start: Using Built-in Layers

The fastest way to build a GNN — stack conv layers from `torch_geometric.nn`:

```python
import torch
import torch.nn.functional as F
from torch_geometric.nn import GCNConv

class GCN(torch.nn.Module):
    def __init__(self, in_channels, hidden_channels, out_channels):
        super().__init__()
        self.conv1 = GCNConv(in_channels, hidden_channels)
        self.conv2 = GCNConv(hidden_channels, out_channels)

    def forward(self, x, edge_index):
        x = self.conv1(x, edge_index).relu()
        x = F.dropout(x, p=0.5, training=self.training)
        x = self.conv2(x, edge_index)
        return x
```

`GCNConv`, `SAGEConv` and attention layers return embeddings; add the intended nonlineari

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

