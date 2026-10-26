---
id: sciref-networkx-generators
name: "Scientific Ref: NetworkX Graph Generators"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (networkx): NetworkX Graph Generators"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "networkx generators"
  - "networkx graph generators"
keywords:
  - "networkx"
  - "generators"
  - "specialized"
  - "scientific"
  - "reference"
  - "graph"
---

# NetworkX Graph Generators

API patterns assume `import networkx as nx`. A generated model is a hypothesis about a graph, not evidence that observed data follow that model. Preserve direction, loops, multiplicity, size, degree constraints and seed/version provenance when constructing null ensembles. See [review.md](review.md).

## Classic Graphs

### Complete Graphs
```python
# Complete graph (all nodes connected to all others)
G = nx.complete_graph(n=10)

# Complete bipartite graph
G = nx.complete_bipartite_graph(n1=5, n2=7)

# Complete multipartite graph
G = nx.complete_multipartite_graph(3, 4, 5)  # Three partitions
```

### Cycle and Path Graphs
```python
# Cycle graph (nodes arranged in circle)
G = nx.cycle_graph(n=20)

# Path graph (linear chain)
G = nx.path_graph(n=15)

# Circular ladder graph
G = nx.circular_ladder_graph(n=10)
```

### Regular Graphs
```python
# Empty graph (no edges)
G = nx.empty_graph(n=10)

# Null graph (no nodes)
G = nx.null_graph()

# Star graph (one central node connected to all others)
G = nx.star_graph(n=19)  # Creates 20-node star

# Wheel graph (cycle with central hub)
G = nx.wheel_graph(n=10)
```

### Special Named Graphs
```python
# Bull graph
G = nx.bull_graph()

# Chvatal graph
G = nx.chvatal_graph()

# Cubical graph
G = nx.cubical_graph()

# Diamond graph
G = nx.diamond_graph()

# Dodecahedral graph
G = nx.dodecahedral_graph()

# Heawood graph
G = nx.heawood_graph()

# House graph
G = nx.house_graph()

# Petersen graph
G = nx.petersen_graph()

# Karate club graph (classic social network)
G = nx.karate_club_graph()
```

## Random Graphs

### Erdős-Rényi Graphs
```python
# G(n, p) model: n nodes, edge probability p
G = nx.erdos_renyi_graph(n=100, p=0.1, seed=42)

# G(n, m) model: n nodes, exactly m edges
G = nx.gnm_random_graph(n=100, m=500, seed=42)

# Fast version (for large sparse graphs)
G = nx.fast_gnp_random_graph(n=10000, p=0.0001, seed=42)
```

### Watts-Strogatz Small-World
```python
# Small-world network with rewiring
# n nodes, k nearest neighbors, rewiring probability p
G = nx.watts_strogatz_graph(n=100, k=6, p=0.1, seed=42)

# Returns a connected sample or raises after tries attempts
G = nx.connected_watts_strogatz_graph(n=100, k=6, p=0.1, tries=100, seed=42)
```

### Barabási-Albert Preferential Attachment
```python
# Preferential-attachment model; finite samples do not establish a power law
# n nodes, m edges to attach from new node
G = nx.barabasi_albert_graph(n=100, m=3, seed=42)

# Extended version with parameters
G = nx.extended_barabasi_albert_graph(n=100, m=3, p=0.5, q=0.2, seed=42)
```

### Power Law Degree Sequence
```python
# Power law cluster graph
G = nx.powerlaw_cluster_graph(n=100, m=3, p=0.1, seed=42)

# Random power law tree
G = nx.random_powerlaw_tree(n=100, gamma=3, seed=42, tries=1000)
```

### Configuration Model
```python
# Graph with specified degree sequence
degree_sequence = [3, 3, 2, 2, 2, 2]  # Even sum required
G = nx.configuration_model(degree_sequence, seed=42)
assert [G.degree(i) for i in range(len(degree_sequence))] == degree_sequence

# Optional simplification changes the degree sequence and null model
H = nx.Graph(G)
H.remove_edges_from(list(nx.selfloop_edges(H)))
```

The configuration model is a stub-matching **multigraph** with possible self-loops. Removing loops/parallel edges does not preserve the specified degrees. `havel_hakimi_graph` gives one simple realization of a graphical sequence, not a uniform random sample. Degree-preserving swaps need adequate mixing and convergence checks; neither a single sample nor a fixed seed establishes null-model validity.

### Random Geometric Graphs
```python
# Nodes in unit square, edges if distance < radius
G = nx.random_geometric_graph(n=100, radius=0.2, seed=42)

# With positions
pos = nx.get_node_attributes(G, 'pos')
```

### Random Regular Graphs
```python
# Every node has exactly d neighbors
G = nx.random_regular_graph(d=3, n=100, seed=42)
```

### Stochastic Block Model
```python
# Community structure model
sizes = [50, 50, 50]  # Three communities
probs = [[0.25, 0.05, 0.02],  # Within and between community probabilities
         [0.05, 0.35, 0.07],
         [0.02, 0.07, 0.40]]
G = nx.stochastic_block_model(sizes, probs, seed=42)
```

## Lattice and Grid Graphs

### Grid Graphs
```python
# 2D grid
G = nx.grid_2d_graph(m=5, n=7)  # 5x7 grid

# 3D grid
G = nx.grid_graph(dim=[5, 7, 3])  # 5x7x3 grid

# Hexagonal lattice
G = nx.hexagonal_lattice_graph(m=5, n=7)

# Triangular lattice
G = nx.triangular_lattice_graph(m=5, n=7)
```

### Hypercube
```python
# n-dimensional hypercube
G = nx.hypercube_graph(n=4)
```

## Tree Graphs

### Random Trees
```python
# Random labeled tree with n nodes, sampled uniformly over labeled trees
# (nx.random_tree was removed in NetworkX 3.4)
G = nx.random_labeled_tree(100, seed=42)

# Sample uniformly over isomorphism classes instead
G = nx.random_unlabeled_tree(100, seed=42)

# Rooted variant is still an undirected Graph, with G.graph["root"]
G = nx.random_labeled_rooted_tree(100, seed=42)

# Prefix tree (tries)
G = nx.prefix_tree([[0, 1, 2], [0, 1, 3], [0, 4]])
```

### Balanced Trees
```python
# Balanced r-ary tree of height h
G = nx.balanced_tree(r=2, h=5)  # Binary tree, height 5

# Full r-ary tree with n nodes
G = nx.full_rary_tree(r=3, n=100)  # Ternary tree
```

### Barbell and Lollipop Graphs
```python
# Two complete graphs connected by path
G = nx.barbell_graph(m1=5, m2=3)  # Two K_5 graphs with 3-node path

# Complete graph connected to path
G = nx.lollipop_graph(m=7, n=5)  # K_7 with 5-node path
```

## Social Network Models

### Karate Club
```python
# Zachary's karate club (classic social network)
G = nx.karate_club_graph()
```

### Davis Southern Women
```python
# Bipartite social network
G = nx.davis_southern_women_graph()
```

### Florentine Families
```python
# Historical marriage network (this generator does not add business ties)
G = nx.florentine_families_graph()
```

### Les Misérables
```python
# Character co-occurrence network
G = nx.les_miserables_graph()
```

## Directed Graph Generators

### Random Directed Graphs
```python
# Directed Erdős-Rényi
G = nx.gnp_random_graph(n=100, p=0.1, directed=True, seed=42)

# Directed MultiDiGraph; parallel edges and self-loops can occur
G = nx.scale_free_graph(n=100, seed=42)
```

### DAG (Directed Acyclic Graph)
```python
# Ordered random DAG; this is not uniform over all DAGs
R = nx.gnp_random_graph(n=20, p=0.2, directed=True, seed=42)
G = nx.DiGraph()
G

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

