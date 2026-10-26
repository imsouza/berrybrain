---
id: sciref-networkx-io
name: "Scientific Ref: NetworkX Input/Output"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (networkx): NetworkX Input/Output"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "networkx"
  - "networkx input/output"
keywords:
  - "networkx"
  - "specialized"
  - "scientific"
  - "reference"
---

# NetworkX Input/Output

API patterns assume `import networkx as nx`, suitable input files and the optional packages named below. See [review.md](review.md) for tested round trips. Preserve a separate node table, graph class, node-ID schema, units and attribute schema; compare them after every conversion. Edge tables alone omit isolated nodes.

## Reading Graphs from Files

### Adjacency List Format
```python
# Read adjacency list (simple text format)
G = nx.read_adjlist('graph.adjlist')

# With node type conversion
G = nx.read_adjlist('graph.adjlist', nodetype=int)

# For directed graphs
G = nx.read_adjlist('graph.adjlist', create_using=nx.DiGraph())

# Write adjacency list
nx.write_adjlist(G, 'graph.adjlist')
```

Example adjacency list format:
```
# node neighbors
0 1 2
1 0 3 4
2 0 3
3 1 2 4
4 1 3
```

### Edge List Format
```python
# Read edge list
G = nx.read_edgelist('graph.edgelist')

# With node types and edge data
G = nx.read_edgelist('graph.edgelist',
                     nodetype=int,
                     data=(('weight', float),))

# Read weighted edge list
G = nx.read_weighted_edgelist('weighted.edgelist')

# Write edge list
nx.write_edgelist(G, 'graph.edgelist')

# Write weighted edge list
nx.write_weighted_edgelist(G, 'weighted.edgelist')
```

Example edge list format:
```
# source target
0 1
1 2
2 3
3 0
```

Example weighted edge list:
```
# source target weight
0 1 0.5
1 2 1.0
2 3 0.75
```

### GML (Graph Modelling Language)
```python
# Read GML (supported GML attributes; default label="label")
G = nx.read_gml('graph.gml')

# Write GML
nx.write_gml(G, 'graph.gml')
```

GML is a text format, not XML. It supports a constrained attribute/type schema; reserved keys such as `id`/`label` have structural meanings. It is not an arbitrary Python-object round trip.

### GraphML Format
```python
# Read GraphML (XML-based format)
G = nx.read_graphml('graph.graphml')

# Write GraphML
nx.write_graphml(G, 'graph.graphml')

# With specific encoding
nx.write_graphml(G, 'graph.graphml', encoding='utf-8')
```

GraphML supports scalar strings, booleans and numeric attributes, not arbitrary lists/dicts/arrays/None. Node IDs are strings on read unless `node_type=` is specified. Use `force_multigraph=True` and an explicit `edge_key_type` to preserve a multigraph class with no parallel edges. GraphML defaults stay in `G.graph`; they are not filled into every node/edge. Mixed directed/undirected graphs and hyperedges are unsupported.

### GEXF (Graph Exchange XML Format)
```python
# Read GEXF
G = nx.read_gexf('graph.gexf')

# Write GEXF
nx.write_gexf(G, 'graph.gexf')
```

GEXF has reserved attribute names and requires compatible attribute types across nodes/edges; mixed types can raise. Validate dynamic attributes separately. GraphML/GEXF readers use XML parsers: only parse trusted files or sanitize XML before this workflow.

### Pajek Format
```python
# Read Pajek .net files
G = nx.read_pajek('graph.net')

# Write Pajek format
nx.write_pajek(G, 'graph.net')
```

### LEDA Format
```python
# Read LEDA format (read-only; NetworkX has no LEDA writer)
G = nx.read_leda('graph.leda')
```

## Working with Pandas

### From Pandas DataFrame
```python
import pandas as pd

# Create graph from edge list DataFrame
df = pd.DataFrame({
    'source': [1, 2, 3, 4],
    'target': [2, 3, 4, 1],
    'weight': [0.5, 1.0, 0.75, 0.25]
})

# Create graph
G = nx.from_pandas_edgelist(df,
                            source='source',
                            target='target',
                            edge_attr='weight')

# With multiple edge attributes: columns must actually exist
df["color"] = "blue"
df["type"] = "interaction"
G = nx.from_pandas_edgelist(df,
                            source='source',
                            target='target',
                            edge_attr=['weight', 'color', 'type'])

# Create directed graph
G = nx.from_pandas_edgelist(df,
                            source='source',
                            target='target',
                            edge_attr='weight',
                            create_using=nx.DiGraph())
```

Specify `create_using=nx.MultiDiGraph()` and `edge_key="edge_id"` when repeated directed observations are separate edges. Simple graphs overwrite duplicate edge attributes; they do not sum them. Import the node table with `add_nodes_from` to retain isolates and node attributes. Check ID dtypes and missing IDs before conversion, especially mixed numeric tables.

### To Pandas DataFrame
```python
# Convert graph to edge list DataFrame
df = nx.to_pandas_edgelist(G)

# Rename endpoint columns (this does not select edge attributes)
df = nx.to_pandas_edgelist(G, source='node1', target='node2')
```

### Adjacency Matrix with Pandas
```python
# Create DataFrame from adjacency matrix
df = nx.to_pandas_adjacency(G, dtype=float)

# Create graph from adjacency DataFrame
G = nx.from_pandas_adjacency(df)

# For directed graphs
G = nx.from_pandas_adjacency(df, create_using=nx.DiGraph())
```

## NumPy and SciPy Integration

### Adjacency Matrix
```python
import numpy as np

# Simple directed weighted fixture, including a zero-cost edge and an isolate
G = nx.DiGraph()
G.add_nodes_from(["A", "B", "isolate"])
G.add_edge("A", "B", weight=0.0)
nodelist = list(G)
A = nx.to_numpy_array(G, nodelist=nodelist, dtype=float, nonedge=np.nan)
# NetworkX 3.7 supports nonedge= on import too
H = nx.from_numpy_array(
    A, nodelist=nodelist, create_using=nx.DiGraph, nonedge=np.nan
)
assert H.has_edge("A", "B") and H["A"]["B"]["weight"] == 0.0
assert set(nx.isolates(H)) == {"isolate"}
```

Dense arrays default to zero meaning **no edge**; a different `nonedge` sentinel is needed for genuine zero-weight edges. `dtype=int` truncates fractional weights. Matrices omit most attributes and aggregate parallel weights (sum by default); integer entries become edge counts only with a multigraph plus `parallel_edges=True`. For directed graphs, row i / column j represents i -> j.

### Sparse Matrix (SciPy)
```python
from scipy import sparse

# Preserve ordering and directedness explicitly
nodelist = list(G)
A = nx.to_scipy_sparse_array(G, nodelist=nodelist, format="csr")
H = nx.from_scipy_sparse_array(A, create_using=type(G))
H = nx.relabel_nodes(H, dict(enumerate(nodelist)))
# Explicitly stored zeros become edges. Call A.eliminate_zeros() only
# when those entries really mean absent edges, not zero-weight edges.
```

## JSON Format

### Node-Link Format
```python
import json

# To node-link fo

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

