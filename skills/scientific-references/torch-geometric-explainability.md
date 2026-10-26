---
id: sciref-torch-geometric-explainability
name: "Scientific Ref: GNN Explainability — Full Reference"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (torch-geometric): GNN Explainability — Full Reference"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "torch geometric explainability"
  - "gnn explainability — full reference"
keywords:
  - "torch"
  - "geometric"
  - "explainability"
  - "specialized"
  - "scientific"
  - "reference"
---

# GNN Explainability — Full Reference

PyG provides `torch_geometric.explain` for interpreting GNN predictions. The module includes a unified `Explainer` interface, several explanation algorithms, visualization, and evaluation metrics.

## The Explainer Interface

The `Explainer` class is the central entry point. Configure it with:
1. An explanation **algorithm** (GNNExplainer, PGExplainer, CaptumExplainer, etc.)
2. An **explanation type** (`"model"` — explain model predictions, or `"phenomenon"` — explain dataset patterns)
3. **Mask types** — which parts of the input to explain (nodes, edges, features)
4. **Post-processing** — how to threshold masks (top-k, hard, etc.)

```python
from torch_geometric.explain import Explainer, GNNExplainer

explainer = Explainer(
    model=model,
    algorithm=GNNExplainer(epochs=200),
    explanation_type='model',          # 'model' or 'phenomenon'
    node_mask_type='attributes',       # 'object', 'common_attributes', 'attributes', or None
    edge_mask_type='object',           # 'object' or None
    model_config=dict(
        mode='multiclass_classification',  # 'binary_classification', 'multiclass_classification', 'regression'
        task_level='node',                  # 'node', 'edge', 'graph'
        return_type='raw',                  # Raw logits; match the actual model output
    ),
)
```

**Mask types explained:**
- `'object'`: One value per node (`[N, 1]`) or per edge (`[E]`).
- `'attributes'`: One mask value per node and feature, shape `[N, F]`.
- `'common_attributes'`: One feature mask shared across all nodes, shape `[1, F]`.
- `None`: Don't generate this mask type

## Generating Explanations

### Node classification

```python
# Explain prediction for node at index 10
explanation = explainer(data.x, data.edge_index, index=10)

print(explanation.node_mask)   # [num_nodes, num_features] — importance per feature per node
print(explanation.edge_mask)   # [num_edges] — importance per edge
```

### Graph classification

```python
explainer = Explainer(
    model=model,
    algorithm=GNNExplainer(epochs=200),
    explanation_type='model',
    edge_mask_type='object',
    model_config=dict(
        mode='multiclass_classification',
        task_level='graph',
        return_type='raw',
    ),
)

explanation = explainer(data.x, data.edge_index, batch=data.batch, index=0)
```

Pass every additional argument required by the model (e.g. graph assignment `batch`, edge weights or supervision edges). For an individual unbatched graph, construct a zero-valued node-to-graph assignment if the model requires it.

## Visualization

```python
# Visualize which features are most important (bar chart)
explanation.visualize_feature_importance(path='feature_importance.png', top_k=10)
# Needs a node feature mask and matplotlib.

# Visualize the important subgraph
explanation.visualize_graph(path='graph.png', backend='networkx')
# Requires an edge mask plus matplotlib/networkx. path=None displays, not saves.
```

## Available Algorithms

### GNNExplainer

Learns soft masks via optimization. Works for node and graph-level tasks. The most widely used algorithm.

```python
from torch_geometric.explain import GNNExplainer

algorithm = GNNExplainer(epochs=200, lr=0.01)
```

### PGExplainer

A parametric (trained) explainer — learns a neural network that generates edge masks. Must be trained before use; generalization to new graphs still needs evaluation. Only supports edge masks (no node masks).

```python
from torch_geometric.explain import PGExplainer

explainer = Explainer(
    model=model,
    algorithm=PGExplainer(epochs=30, lr=0.003),
    explanation_type='phenomenon',     # PGExplainer explains phenomena
    edge_mask_type='object',
    model_config=dict(
        mode='regression',
        task_level='graph',
        return_type='raw',
    ),
    threshold_config=dict(threshold_type='topk', value=10),
)

# Keep the trained prediction model fixed in evaluation behavior.
model.eval()
# Train the explainer first, using only permitted training targets.
for epoch in range(30):
    for batch in loader:
        loss = explainer.algorithm.train(
            epoch, model, batch.x, batch.edge_index, target=batch.y, batch=batch.batch
        )

# Then explain
explanation = explainer(data.x, data.edge_index, target=data.y,
                        batch=data.batch, index=0)
```

`phenomenon` requires `target=` both during training and explanation. This graph-regression recipe assumes model output and `data.y` have the same shape (for example `[num_graphs, 1]`). Node PGExplainer training also requires a single `index` per call.

### CaptumExplainer

Wraps the [Captum](https://captum.ai/) library, giving access to gradient-based attribution methods. Works with both homogeneous and heterogeneous graphs.

```python
from torch_geometric.explain import CaptumExplainer

# Supports: 'IntegratedGradients', 'Saliency', 'Deconvolution',
#           'ShapleyValueSampling', 'GuidedBackprop', etc.
algorithm = CaptumExplainer('IntegratedGradients')
```

Requires `uv pip install captum==0.9.0` for the reviewed runtime. Avoid blindly installing the PyG `full` extra: its released metadata still pins older Captum.

### AttentionExplainer

Uses supported layers' captured attention coefficients as edge masks, with no explainer training. Support is operator-specific; the tested example uses `GATConv`. A layer having an attention mechanism (e.g. `TransformerConv`) does not alone establish hook compatibility. Attention weights are not causal evidence.

```python
from torch_geometric.explain import AttentionExplainer

algorithm = AttentionExplainer()
```

## Heterogeneous Graph Explanations

For heterogeneous models, compatible algorithms return `HeteroExplanation` with per-type masks. Wrap dict-returning models so the explainer gets one tensor for the node type being explained; `index` then refers to rows of that type:

```python
from torch_geometric.explain import Explainer, CaptumExplainer

class PaperOutput(torch.nn.Module):
    def __init__(self, model):
        super().__init__()
        self.model = model
    def forward(self, x_dict, edge_index_dict):
        return self.model(x_dict, edge_index_dict)['paper']

explainer = Explainer(
    model=PaperOutput(hetero_model),
    algorithm=CaptumExplainer('IntegratedGradients'),
    explanation_type='model',
    node_mask_type='attributes',
    edge_mask_type='object',
    model_config=dict(
        mode='multiclass_classification',
      

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

