---
id: sciref-torch-geometric-heterogeneous
name: "Scientific Ref: Heterogeneous Graph Learning — Full Reference"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (torch-geometric): Heterogeneous Graph Learning — Full Reference"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "torch geometric heterogeneous"
  - "heterogeneous graph learning — full reference"
keywords:
  - "torch"
  - "geometric"
  - "heterogeneous"
  - "specialized"
  - "scientific"
  - "reference"
---

# Heterogeneous Graph Learning — Full Reference

## Creating HeteroData

```python
from torch_geometric.data import HeteroData

data = HeteroData()

# Node features — keyed by node type string
data['paper'].x = ...       # [num_papers, num_features_paper]
data['author'].x = ...      # [num_authors, num_features_author]
data['institution'].x = ... # [num_institutions, num_features_institution]

# Edge indices — keyed by (source_type, edge_type, dest_type) triplet
data['paper', 'cites', 'paper'].edge_index = ...              # [2, num_edges]
data['author', 'writes', 'paper'].edge_index = ...            # [2, num_edges]
data['author', 'affiliated_with', 'institution'].edge_index = ... # [2, num_edges]

# Edge features (optional)
data['paper', 'cites', 'paper'].edge_attr = ...  # [num_edges, num_edge_features]

# Additional node attributes
data['paper'].y = ...           # labels
data['paper'].train_mask = ...  # boolean mask
```

### Accessing data

```python
# Single store access
data['paper']                          # NodeStore for papers
data['paper', 'cites', 'paper']       # EdgeStore for cites edges
data['paper', 'paper']                 # Shorthand if edge type is unambiguous
data['cites']                          # Shorthand if edge type name is unique

# Dict access for model input
data.x_dict                            # {'paper': tensor, 'author': tensor, ...}
data.edge_index_dict                   # {('paper','cites','paper'): tensor, ...}
data.edge_attr_dict

# Metadata
node_types, edge_types = data.metadata()

# Modify
data['paper'].year = ...               # Add new attribute
del data['field_of_study']             # Delete node type
del data['has_topic']                  # Delete edge type

# Convert
data.to('cuda:0')                      # Transfer to GPU
data.to_homogeneous()                  # Convert to typed homogeneous graph
```

### Transforms on HeteroData

```python
import torch_geometric.transforms as T

data = T.ToUndirected()(data)       # Add reverse edge types
data = T.AddSelfLoops()(data)       # Add self-loops for same-type edges
data = T.NormalizeFeatures()(data)  # Normalize features across all types
```

`ToUndirected()` is important — it creates reverse edge types (e.g., `('paper', 'rev_writes', 'author')`) so messages flow in both directions.

## Building Heterogeneous GNN Models

### Option 1: Auto-convert with `to_hetero()`

Write a standard homogeneous GNN, then convert:

```python
import torch
from torch_geometric.nn import SAGEConv, to_hetero
import torch_geometric.transforms as T
from torch_geometric.datasets import OGB_MAG

# Illustrative large download; preserve the OGB split and embedding provenance.
dataset = OGB_MAG(root='./data', preprocess='metapath2vec', transform=T.ToUndirected())
data = dataset[0]

class GNN(torch.nn.Module):
    def __init__(self, hidden_channels, out_channels):
        super().__init__()
        # Use (-1, -1) for lazy init with bipartite support
        self.conv1 = SAGEConv((-1, -1), hidden_channels)
        self.conv2 = SAGEConv((-1, -1), out_channels)

    def forward(self, x, edge_index):
        x = self.conv1(x, edge_index).relu()
        x = self.conv2(x, edge_index)
        return x

model = GNN(64, dataset.num_classes)
model = to_hetero(model, data.metadata(), aggr='sum')

# Initialize lazy modules
with torch.no_grad():
    out = model(data.x_dict, data.edge_index_dict)
```

With skip-connections (important for attention-based models):

```python
from torch_geometric.nn import GATConv, Linear, to_hetero

class GAT(torch.nn.Module):
    def __init__(self, hidden_channels, out_channels):
        super().__init__()
        self.conv1 = GATConv((-1, -1), hidden_channels, add_self_loops=False)
        self.lin1 = Linear(-1, hidden_channels)
        self.conv2 = GATConv((-1, -1), out_channels, add_self_loops=False)
        self.lin2 = Linear(-1, out_channels)

    def forward(self, x, edge_index):
        # Skip connection replaces self-loops for bipartite message passing
        x = self.conv1(x, edge_index) + self.lin1(x)
        x = x.relu()
        x = self.conv2(x, edge_index) + self.lin2(x)
        return x

model = GAT(64, dataset.num_classes)
model = to_hetero(model, data.metadata(), aggr='sum')
```

### Option 2: HeteroConv wrapper (different conv per edge type)

```python
from torch_geometric.nn import HeteroConv, GCNConv, SAGEConv, GATConv, Linear

class HeteroGNN(torch.nn.Module):
    def __init__(self, hidden_channels, out_channels, num_layers):
        super().__init__()

        self.convs = torch.nn.ModuleList()
        for _ in range(num_layers):
            conv = HeteroConv({
                ('paper', 'cites', 'paper'): GCNConv(-1, hidden_channels),
                ('author', 'writes', 'paper'): SAGEConv((-1, -1), hidden_channels),
                ('paper', 'rev_writes', 'author'): GATConv((-1, -1), hidden_channels,
                                                            add_self_loops=False),
            }, aggr='sum')
            self.convs.append(conv)

        self.lin = Linear(hidden_channels, out_channels)

    def forward(self, x_dict, edge_index_dict):
        for conv in self.convs:
            x_dict = conv(x_dict, edge_index_dict)
            x_dict = {key: x.relu() for key, x in x_dict.items()}
        return self.lin(x_dict['paper'])

model = HeteroGNN(64, dataset.num_classes, num_layers=2)
with torch.no_grad():
    out = model(data.x_dict, data.edge_index_dict)
```

### Option 3: HGTConv (native heterogeneous operator)

```python
from torch_geometric.nn import HGTConv, Linear

class HGT(torch.nn.Module):
    def __init__(self, hidden_channels, out_channels, num_heads, num_layers):
        super().__init__()

        self.lin_dict = torch.nn.ModuleDict()
        for node_type in data.node_types:
            self.lin_dict[node_type] = Linear(-1, hidden_channels)

        self.convs = torch.nn.ModuleList()
        for _ in range(num_layers):
            conv = HGTConv(hidden_channels, hidden_channels, data.metadata(),
                           heads=num_heads)
            self.convs.append(conv)

        self.lin = Linear(hidden_channels, out_channels)

    def forward(self, x_dict, edge_index_dict):
        x_dict = {key: self.lin_dict[key](x).relu()
                  for key, x in x_dict.items()}
        for conv in self.convs:
            x_dict = conv(x_dict, edge_index_dict)
        return self.lin(x_dict['paper'])
```

`HGTConv` uses `heads=`, not `num_heads=` or `g

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

