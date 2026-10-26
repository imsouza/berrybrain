---
id: sciref-networkx-visualization
name: "Scientific Ref: NetworkX Graph Visualization"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (networkx): NetworkX Graph Visualization"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "networkx visualization"
  - "networkx graph visualization"
keywords:
  - "networkx"
  - "visualization"
  - "specialized"
  - "scientific"
  - "reference"
  - "graph"
---

# NetworkX Graph Visualization

API patterns assume suitable graphs and imports; examples use simple graphs unless stated. Geometric layout distance is not an observed physical or statistical distance. See [review.md](review.md) for executed rendering checks and optional integration limits.

## Basic Drawing with Matplotlib

### Simple Visualization
```python
import networkx as nx
import matplotlib.pyplot as plt

# Create and draw graph
G = nx.karate_club_graph()
nx.draw(G)
plt.show()

# Save to file
nx.draw(G)
plt.savefig('graph.png', dpi=300, bbox_inches='tight')
plt.close()
```

NetworkX 3.5 added `nx.display(G)`, a newer declarative drawing API that reads visualization attributes (color, size, position) stored directly on nodes and edges. `nx.draw` and the `draw_networkx_*` functions below remain fully supported.

### Drawing with Labels
```python
# Draw with node labels
nx.draw(G, with_labels=True)
plt.show()

# Custom labels
labels = {i: f"Node {i}" for i in G.nodes()}
nx.draw(G, labels=labels, with_labels=True)
plt.show()
```

## Layout Algorithms

### Spring Layout (Force-Directed)
```python
# Fruchterman-Reingold force-directed algorithm
pos = nx.spring_layout(G, seed=42)
nx.draw(G, pos=pos, with_labels=True)
plt.show()

# With parameters
pos = nx.spring_layout(G, k=0.5, iterations=50, seed=42)
```

`spring_layout(method="auto")` uses force below 500 nodes and energy otherwise. Energy uses absolute edge weights and component gravity; force can behave differently on signed graphs. Set `method`, `weight` and `seed` when comparing layouts. Large weights attract nodes more strongly, unlike shortest-path costs.

### Circular Layout
```python
# Arrange nodes in circle
pos = nx.circular_layout(G)
nx.draw(G, pos=pos, with_labels=True)
plt.show()
```

### Random Layout
```python
# Random positioning
pos = nx.random_layout(G, seed=42)
nx.draw(G, pos=pos, with_labels=True)
plt.show()
```

### Shell Layout
```python
# Concentric circles
pos = nx.shell_layout(G)
nx.draw(G, pos=pos, with_labels=True)
plt.show()

# With custom shells
shells = [[0, 1, 2], [3, 4, 5, 6], [7, 8, 9]]
pos = nx.shell_layout(G, nlist=shells)
```

### Spectral Layout
```python
# Use eigenvectors of graph Laplacian
pos = nx.spectral_layout(G)
nx.draw(G, pos=pos, with_labels=True)
plt.show()
```

### Kamada-Kawai Layout
```python
# Energy-based layout
pos = nx.kamada_kawai_layout(G)
nx.draw(G, pos=pos, with_labels=True)
plt.show()
```

### Planar Layout
```python
# For planar graphs only
if nx.is_planar(G):
    pos = nx.planar_layout(G)
    nx.draw(G, pos=pos, with_labels=True)
    plt.show()
```

### Tree Layouts
```python
# For tree graphs
if nx.is_tree(G):
    # Requires pygraphviz (verify its Graphviz runtime availability)
    pos = nx.nx_agraph.graphviz_layout(G, prog='dot')
    nx.draw(G, pos=pos, with_labels=True)
    plt.show()
```

## Customizing Node Appearance

### Node Colors
```python
# Single color
nx.draw(G, node_color='red')

# Different colors per node
node_colors = ['red' if G.degree(n) > 5 else 'blue' for n in G.nodes()]
nx.draw(G, node_color=node_colors)

# Color by attribute
pos = nx.spring_layout(G, seed=42)
colors = [G.degree(n) for n in G]
fig, ax = plt.subplots()
nx.draw_networkx_edges(G, pos, ax=ax)
artist = nx.draw_networkx_nodes(G, pos, node_color=colors, cmap="viridis", ax=ax)
fig.colorbar(artist, ax=ax, label="Degree")
plt.show()
```

### Node Sizes
```python
# Size by degree
node_sizes = [100 * G.degree(n) for n in G.nodes()]
nx.draw(G, node_size=node_sizes)

# Size by centrality
centrality = nx.degree_centrality(G)
node_sizes = [3000 * centrality[n] for n in G.nodes()]
nx.draw(G, node_size=node_sizes)
```

### Node Shapes
```python
# Draw nodes separately with different shapes
pos = nx.spring_layout(G)

# Circle nodes
nx.draw_networkx_nodes(G, pos, nodelist=[0, 1, 2],
                       node_shape='o', node_color='red')

# Square nodes
nx.draw_networkx_nodes(G, pos, nodelist=[3, 4, 5],
                       node_shape='s', node_color='blue')

nx.draw_networkx_edges(G, pos)
nx.draw_networkx_labels(G, pos)
plt.show()
```

### Node Borders
```python
nx.draw(G, pos=pos,
        node_color='lightblue',
        edgecolors='black',  # Node border color
        linewidths=2)        # Node border width
plt.show()
```

## Customizing Edge Appearance

### Edge Colors
```python
# Single color
nx.draw(G, edge_color='gray')

# Different colors per edge
edge_colors = ['red' if G[u][v].get('weight', 1) > 0.5 else 'blue'
               for u, v in G.edges()]
nx.draw(G, edge_color=edge_colors)

# Color by weight
edges = G.edges()
weights = [G[u][v].get('weight', 1) for u, v in edges]
nx.draw(G, edge_color=weights, edge_cmap=plt.cm.Reds)
```

### Edge Widths
```python
# Width by weight
edge_widths = [3 * G[u][v].get('weight', 1) for u, v in G.edges()]
nx.draw(G, width=edge_widths)

# Width by betweenness
edge_betweenness = nx.edge_betweenness_centrality(G)
edge_widths = [5 * edge_betweenness[(u, v)] for u, v in G.edges()]
nx.draw(G, width=edge_widths)
```

### Edge Styles
```python
# Dashed edges
nx.draw(G, style='dashed')

# Different styles per edge
pos = nx.spring_layout(G)
strong_edges = [(u, v) for u, v in G.edges() if G[u][v].get('weight', 0) > 0.5]
weak_edges = [(u, v) for u, v in G.edges() if G[u][v].get('weight', 0) <= 0.5]

nx.draw_networkx_nodes(G, pos)
nx.draw_networkx_edges(G, pos, edgelist=strong_edges, style='solid', width=2)
nx.draw_networkx_edges(G, pos, edgelist=weak_edges, style='dashed', width=1)
plt.show()
```

### Directed Graphs (Arrows)
```python
# Draw directed graph with arrows
G_directed = nx.DiGraph([(1, 2), (2, 3), (3, 1)])
pos = nx.spring_layout(G_directed)

nx.draw(G_directed, pos=pos, with_labels=True,
        arrows=True,
        arrowsize=20,
        arrowstyle='->',
        connectionstyle='arc3,rad=0.1')
plt.show()
```

## Labels and Annotations

### Node Labels
```python
pos = nx.spring_layout(G)

# Custom labels
labels = {n: f"N{n}" for n in G.nodes()}
nx.draw_networkx_labels(G, pos, labels=labels, font_size=12, font_color='white')

# Font customization
nx.draw_networkx_labels(G, pos,
                       font_size=10,
                       font_family='serif',
                       font_weight='bold')
```

### Edge Labels
```python
pos = nx.spring_layout(G)
nx.draw_networkx_nodes(G, pos)
nx.draw_networkx_edges(G, pos)

# Edge labels from attributes
edge_labels = nx.get_edge_attributes(G, 'weight')
nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

