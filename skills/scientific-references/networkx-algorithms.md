---
id: sciref-networkx-algorithms
name: "Scientific Ref: NetworkX Graph Algorithms"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (networkx): NetworkX Graph Algorithms"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "networkx algorithms"
  - "networkx graph algorithms"
keywords:
  - "networkx"
  - "algorithms"
  - "specialized"
  - "scientific"
  - "reference"
  - "graph"
---

# NetworkX Graph Algorithms

The snippets are API patterns using a supplied graph `G`; choose the required graph class before each section. Use finite numeric weights with explicit units. Missing weight attributes generally default to one. See [review.md](review.md) for release sources and executed examples.

## Shortest Paths

### Single Source Shortest Paths
```python
# Dijkstra: distance/cost weights must be nonnegative
path = nx.shortest_path(G, source=1, target=5, weight='weight')
length = nx.shortest_path_length(G, source=1, target=5, weight='weight')

# All shortest paths from source
paths = nx.single_source_shortest_path(G, source=1)
lengths = nx.single_source_shortest_path_length(G, source=1)

# Bellman-Ford handles negative edges, but not a reachable negative cycle
path = nx.bellman_ford_path(G, source=1, target=5, weight='weight')
```

### All Pairs Shortest Paths
```python
# All pairs (returns iterator)
for source, paths in nx.all_pairs_shortest_path(G):
    print(f"From {source}: {paths}")

# Floyd-Warshall weighted distances (all-pairs unweighted BFS is different)
lengths = dict(nx.floyd_warshall(G, weight="distance"))
```

### Specialized Shortest Path Algorithms
```python
# A* algorithm (with heuristic)
def heuristic(u, v):
    # Zero is admissible without a proven geometric lower bound
    return 0

path = nx.astar_path(G, source=1, target=5, heuristic=heuristic, weight='weight')

# Average shortest path length
avg_length = nx.average_shortest_path_length(G)
```

Average path length requires a connected undirected or strongly connected directed graph. For disconnected inputs, report component coverage and define whether component summaries are node- or pair-weighted; do not silently discard unreachable pairs.

## Connectivity

### Connected Components (Undirected)
```python
# Check if connected
is_connected = nx.is_connected(G)

# Number of components
num_components = nx.number_connected_components(G)

# Get all components (returns iterator of sets)
components = list(nx.connected_components(G))
largest_component = max(components, key=len, default=set())

# Get component containing specific node
component = nx.node_connected_component(G, n=1)
```

### Strong/Weak Connectivity (Directed)
```python
# Strong connectivity (mutually reachable)
is_strongly_connected = nx.is_strongly_connected(G)
strong_components = list(nx.strongly_connected_components(G))
largest_scc = max(strong_components, key=len, default=set())

# Weak connectivity (ignoring direction)
is_weakly_connected = nx.is_weakly_connected(G)
weak_components = list(nx.weakly_connected_components(G))

# Condensation (DAG of strongly connected components)
condensed = nx.condensation(G)
```

### Cuts and Connectivity
```python
# Minimum node/edge cut
min_node_cut = nx.minimum_node_cut(G, s=1, t=5)
min_edge_cut = nx.minimum_edge_cut(G, s=1, t=5)

# Node/edge connectivity
node_connectivity = nx.node_connectivity(G)
edge_connectivity = nx.edge_connectivity(G)
```

## Centrality Measures

### Degree Centrality
```python
# Fraction of nodes each node is connected to
degree_cent = nx.degree_centrality(G)

# For directed graphs
in_degree_cent = nx.in_degree_centrality(G)
out_degree_cent = nx.out_degree_centrality(G)
```

### Betweenness Centrality
```python
# Fraction of shortest paths passing through node
betweenness = nx.betweenness_centrality(G, weight='weight')

# Edge betweenness
edge_betweenness = nx.edge_betweenness_centrality(G, weight='weight')

# Approximate for large graphs
approx_betweenness = nx.betweenness_centrality(
    G, k=min(100, len(G)), weight="distance", seed=42
)  # Repeat seeds to assess approximation variability
```

Weighted betweenness interprets weights as distances and requires strictly positive values. Zero distances permit infinitely many equal-length paths; floating-point ties can alter counts. Document any justified scaling to integer costs.

### Closeness Centrality
```python
# Reciprocal of average shortest path length
closeness = nx.closeness_centrality(G)

# For disconnected graphs
closeness = nx.closeness_centrality(G, wf_improved=True)
```

On a directed graph, closeness uses distances **into** each node. For outward reach use `nx.closeness_centrality(G.reverse(copy=False), distance="distance")`. `wf_improved=True` scales for the reachable fraction; it does not make disconnected graphs connected.

### Eigenvector Centrality
```python
# Centrality based on connections to high-centrality nodes
eigenvector = nx.eigenvector_centrality(G, max_iter=1000)

# Katz centrality (variant with attenuation factor)
katz = nx.katz_centrality(G, alpha=0.1, beta=1.0)
```

Eigenvector/Katz weights represent connection strength, unlike shortest-path costs. Directed eigenvector centrality uses incoming links; disconnected/reducible graphs can give nonunique or zero scores. Katz requires `alpha < 1 / spectral_radius(A)`, so 0.1 is only illustrative. Catch `PowerIterationFailedConvergence`; raising `max_iter` alone does not establish a meaningful solution.

### PageRank
```python
# Google's PageRank algorithm
pagerank = nx.pagerank(G, alpha=0.85)

# Personalized PageRank
personalization = {node: 1.0 if node in [1, 2] else 0.0 for node in G}
if sum(personalization.values()) == 0:
    raise ValueError("Personalization must include a node present in G")
ppr = nx.pagerank(G, personalization=personalization)
```

PageRank uses outgoing transition strengths (nonnegative weights) and SciPy; it treats each undirected edge as two directed edges. Personalization must have positive total mass. Record `alpha`, weight, dangling-node handling and convergence tolerance.

## Clustering

### Clustering Coefficients
```python
# Clustering coefficient for each node
clustering = nx.clustering(G)

# Average clustering coefficient
avg_clustering = nx.average_clustering(G)

# Weighted clustering
weighted_clustering = nx.clustering(G, weight='weight')
```

### Transitivity
```python
# Overall clustering (ratio of triangles to triads)
transitivity = nx.transitivity(G)
```

### Triangles
```python
# Count triangles per node
triangles = nx.triangles(G)

# Total number of triangles
total_triangles = sum(triangles.values()) // 3
```

Clustering/triangles are not supported for multigraphs. `triangles` and transitivity examples here use simple undirected graphs; weighted clustering uses strength, not distance. State whether low-degree nodes count in an average (`count_zeros`).

## Community Detection

### Modularity-Based
```pyth

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

