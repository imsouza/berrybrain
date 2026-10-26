---
id: sciref-torch-geometric-link-prediction
name: "Scientific Ref: Link Prediction — Full Reference"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (torch-geometric): Link Prediction — Full Reference"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "torch geometric link prediction"
  - "link prediction — full reference"
keywords:
  - "torch"
  - "geometric"
  - "link"
  - "prediction"
  - "specialized"
  - "scientific"
  - "reference"
---

# Link Prediction — Full Reference

Link prediction is the task of predicting missing or future edges in a graph. Common applications: social network friend suggestion, knowledge graph completion, drug-target interaction.

## Edge Splitting

Use `RandomLinkSplit` to split edges into train/val/test while maintaining graph structure:

```python
import torch_geometric.transforms as T

transform = T.RandomLinkSplit(
    num_val=0.1,              # 10% of edges for validation
    num_test=0.1,             # 10% of edges for test
    is_undirected=True,       # Set True for undirected graphs
    add_negative_train_samples=True,   # Fixed negatives, excluded from known positives
    disjoint_train_ratio=0.2, # Supervision positives excluded from train messages
    neg_sampling_ratio=1.0,   # 1 negative per positive edge
)
train_data, val_data, test_data = transform(data)
```

For an unlabeled binary graph, each split has `edge_label_index` of shape `[2, E_label]` and `edge_label` of shape `[E_label]` (`1` observed, `0` sampled absent). This example uses fixed negatives generated against the original graph. `disjoint_train_ratio=0.2` reserves part of the training positives for supervision; the remainder supplies training messages.

`edge_index` differs by split: training uses its message subset, validation uses **all training positives**, and test uses **training plus validation positives**. The last behavior is PyG's default evaluation protocol, not a universal no-leakage guarantee. If validation edges would be unavailable at prediction time, explicitly use a train-only message graph for both evaluations. Never use test positives for training or checkpoint selection. For temporal prediction, construct time-respecting splits instead of this random transform.

An undirected input must have both edge directions; `is_undirected=True` keeps positive reverse pairs together but returns one orientation per positive label. Bipartite relations need paired `edge_types`/`rev_edge_types` instead. If there are too few nonedges, the realized negative ratio shrinks: verify both label classes before AUC. Existing categorical edge labels are shifted to reserve zero for negatives; binary BCE here assumes no such labels. Continuous ratings are regression targets, not valid `RandomLinkSplit` class labels.

## Encoder-Decoder Pattern

The standard approach:
1. **Encode** — use a GNN to produce node embeddings from the message-passing edges
2. **Decode** — score candidate edges using the node embeddings

```python
import torch
import torch.nn.functional as F
from torch_geometric.nn import GCNConv

class LinkEncoder(torch.nn.Module):
    def __init__(self, in_channels, hidden_channels, out_channels):
        super().__init__()
        self.conv1 = GCNConv(in_channels, hidden_channels)
        self.conv2 = GCNConv(hidden_channels, out_channels)

    def forward(self, x, edge_index):
        x = self.conv1(x, edge_index).relu()
        x = self.conv2(x, edge_index)
        return x

def decode(z, edge_label_index):
    """Dot-product decoder: score = z_src . z_dst for each edge."""
    src, dst = edge_label_index
    return (z[src] * z[dst]).sum(dim=1)
```

## Full-Batch Training Loop

```python
model = LinkEncoder(data.num_features, 128, 64)
optimizer = torch.optim.Adam(model.parameters(), lr=0.01)

def train(train_data):
    model.train()
    optimizer.zero_grad()
    z = model(train_data.x, train_data.edge_index)
    edge_label_index = train_data.edge_label_index
    edge_label = train_data.edge_label.to(device=z.device, dtype=z.dtype)

    # Decode and compute loss
    pred = decode(z, edge_label_index)
    loss = F.binary_cross_entropy_with_logits(pred, edge_label)
    loss.backward()
    optimizer.step()
    return loss.item()

@torch.no_grad()
def test(data_split):
    model.eval()
    z = model(data_split.x, data_split.edge_index)
    pred = decode(z, data_split.edge_label_index).sigmoid()
    # Report the candidate/negative distribution alongside ranking metrics.
    from sklearn.metrics import roc_auc_score
    return roc_auc_score(data_split.edge_label.cpu(), pred.cpu())
```

## Graph Autoencoders (GAE / VGAE)

PyG provides `GAE` and `VGAE` for graph reconstruction/link prediction. Separate positive and negative **edge columns**, not the source and destination rows:

```python
from torch_geometric.nn import GAE, VGAE, GCNConv

class Encoder(torch.nn.Module):
    def __init__(self, in_channels, out_channels):
        super().__init__()
        self.conv1 = GCNConv(in_channels, 2 * out_channels)
        self.conv2 = GCNConv(2 * out_channels, out_channels)
        # For VGAE, also define conv_mu and conv_logstd

    def forward(self, x, edge_index):
        x = self.conv1(x, edge_index).relu()
        return self.conv2(x, edge_index)

# GAE wraps the encoder with reconstruction and evaluation helpers
model = GAE(Encoder(data.num_features, 64))
optimizer = torch.optim.Adam(model.parameters(), lr=0.01)

def train():
    model.train()
    optimizer.zero_grad()
    z = model.encode(train_data.x, train_data.edge_index)
    pos = train_data.edge_label_index[:, train_data.edge_label == 1]
    neg = train_data.edge_label_index[:, train_data.edge_label == 0]
    loss = model.recon_loss(z, pos, neg)
    # For VGAE, add KL divergence:
    # loss = loss + (1 / data.num_nodes) * model.kl_loss()
    loss.backward()
    optimizer.step()
    return loss.item()

@torch.no_grad()
def test(data_split):
    model.eval()
    z = model.encode(data_split.x, data_split.edge_index)
    pos = data_split.edge_label_index[:, data_split.edge_label == 1]
    neg = data_split.edge_label_index[:, data_split.edge_label == 0]
    return model.test(z, pos, neg)  # (ROC-AUC, average precision); each index is [2,E]
```

Do not call `recon_loss` on mixed positive/negative labels as if all were edges. Its default negative sampler only knows the supplied positives; pass explicit negatives under your chosen evaluation protocol. For VGAE, the encoder must return `mu` and `logstd` instead of a single embedding. Use the VGAE-specific encoder pattern:

```python
class VariationalEncoder(torch.nn.Module):
    def __init__(self, in_channels, out_channels):
        super().__init__()
        self.conv1 = GCNConv(in_channels, 2 * out_channels)
        self.conv_mu = GCNConv(2 * out_channels, out_channels)
        self.conv_logstd = GCNConv(2 * out_channels, out_channels)

    def forward(self, x, edge_index):
        x = self.conv1(x, edge_index).rel

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

