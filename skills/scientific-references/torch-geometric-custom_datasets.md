---
id: sciref-torch-geometric-custom-datasets
name: "Scientific Ref: Custom graph datasets"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (torch-geometric): Custom graph datasets"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "torch geometric custom datasets"
  - "custom graph datasets"
keywords:
  - "torch"
  - "geometric"
  - "custom"
  - "datasets"
  - "specialized"
  - "scientific"
  - "reference"
---

# Custom graph datasets

Use explicit node IDs, tensor dtypes and label shapes. `Data.validate()` checks graph structure but cannot detect a feature row attached to the wrong biological entity. Preserve the original ID-to-row mapping and test it separately. Fit feature encoders on the training data when the evaluation protocol requires an inductive split.

## InMemoryDataset

This local example reads a list of tensor dictionaries from `root/raw/graphs.pt`; it performs no download. Each dictionary can contain `x`, `edge_index`, `y`, and an integer `num_nodes`. Create that file yourself from reviewed raw data before instantiating the class. Only load trusted artifacts, even when using restricted deserialization.

```python
import torch
from torch_geometric.data import Data, InMemoryDataset

class MyDataset(InMemoryDataset):
    def __init__(self, root, transform=None, pre_transform=None, pre_filter=None,
                 force_reload=False):
        super().__init__(root, transform, pre_transform, pre_filter,
                         force_reload=force_reload)
        self.load(self.processed_paths[0])

    @property
    def raw_file_names(self):
        return ['graphs.pt']

    @property
    def processed_file_names(self):
        return ['data.pt']

    def process(self):
        records = torch.load(self.raw_paths[0], weights_only=True, map_location='cpu')
        graphs = []
        for record in records:
            graph = Data.from_dict(record)
            graph.validate(raise_on_error=True)
            if self.pre_filter is not None and not self.pre_filter(graph):
                continue
            if self.pre_transform is not None:
                graph = self.pre_transform(graph)
            graph.validate(raise_on_error=True)
            graphs.append(graph)
        if not graphs:
            raise ValueError('No graphs remain after filtering')
        self.save(graphs, self.processed_paths[0])
```

`process()` is cached by `processed_file_names`; `transform` runs on access, `pre_transform` only during processing. Use a versioned cache or `force_reload=True` when raw files, feature vocabulary or preprocessing changes. `InMemoryDataset.save/load` is the current paired API; saved PyG objects are not interchangeable with an arbitrary tensor-only `torch.load` payload.

## Disk-backed Dataset

This example has one tensor dictionary per `raw/graph_*.pt`; graphs are loaded and processed one at a time. A manifest indexes only the graphs retained by `pre_filter`, avoiding gaps and a false hardcoded length. Save tensor dictionaries so current `torch.load(weights_only=True)` can read them without loading a pickled `Data` class.

```python
import json
from pathlib import Path
import torch
from torch_geometric.data import Data, Dataset

class LargeDataset(Dataset):
    def __init__(self, root, transform=None, pre_transform=None, pre_filter=None,
                 force_reload=False):
        super().__init__(root, transform, pre_transform, pre_filter,
                         force_reload=force_reload)
        self.files = json.loads(Path(self.processed_paths[0]).read_text())
        if any(not (Path(self.processed_dir) / name).is_file() for name in self.files):
            raise FileNotFoundError('Processed graph missing; rebuild this cache')

    @property
    def raw_file_names(self):
        names = sorted(p.name for p in Path(self.raw_dir).glob('graph_*.pt'))
        if not names:
            raise FileNotFoundError('Put tensor dictionaries in raw/graph_*.pt')
        return names

    @property
    def processed_file_names(self):
        return ['index.json']

    def process(self):
        files = []
        for raw_path in self.raw_paths:
            graph = Data.from_dict(torch.load(raw_path, weights_only=True,
                                              map_location='cpu'))
            graph.validate(raise_on_error=True)
            if self.pre_filter is not None and not self.pre_filter(graph):
                continue
            if self.pre_transform is not None:
                graph = self.pre_transform(graph)
            graph.validate(raise_on_error=True)
            name = f'data_{len(files)}.pt'
            torch.save(graph.to_dict(), Path(self.processed_dir) / name)
            files.append(name)
        Path(self.processed_paths[0]).write_text(json.dumps(files))

    def len(self):
        return len(self.files)

    def get(self, idx):
        record = torch.load(Path(self.processed_dir) / self.files[idx],
                            weights_only=True, map_location='cpu')
        return Data.from_dict(record)
```

`get()` returns an untransformed graph; public `dataset[idx]` applies `transform`. This is a local single-writer cache example, not a concurrent or transactional database. Rebuild/version the cache when source files change.

## CSV node/edge alignment

Use a node table with unique, non-null IDs for feature-bearing nodes. A repeated interaction table can supply a featureless node universe only after explicit deduplication. Preserve string identifiers and leading zeros through `dtype=` when needed.

```python
import pandas as pd
import torch

def load_node_csv(path, index_col, encoders=None, dtype=None):
    df = pd.read_csv(path, index_col=index_col, dtype=dtype)
    if df.index.hasnans or not df.index.is_unique:
        raise ValueError('Node IDs must be unique and non-null')
    mapping = {node_id: i for i, node_id in enumerate(df.index)}
    x = None
    if encoders:
        columns = [encoder(df[col]) for col, encoder in encoders.items()]
        if any(t.ndim != 2 or t.size(0) != len(df) for t in columns):
            raise ValueError('Every encoder must return [num_nodes, features]')
        x = torch.cat(columns, dim=-1)
    return x, mapping

def load_edge_csv(path, src_index_col, src_mapping, dst_index_col, dst_mapping,
                  encoders=None, dtype=None):
    df = pd.read_csv(path, dtype=dtype)
    src = df[src_index_col].map(src_mapping)
    dst = df[dst_index_col].map(dst_mapping)
    if src.isna().any() or dst.isna().any():
        raise ValueError('Unknown or null edge endpoint')
    edge_index = torch.tensor([src.tolist(), dst.tolist()], dtype=torch.long)
    edge_attr = None
    if encoders:
        columns = [encoder(df[col]) for col, encoder in encoders.items()]
        if any(t.ndim != 2 or t.size(0) != len(df) for t in columns):
            raise ValueError('Every encoder must return [num_edges, features]')
        edge

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

