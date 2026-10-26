---
id: sciref-scikit-learn-unsupervised-learning
name: "Scientific Ref: Unsupervised Learning Reference"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (scikit-learn): Unsupervised Learning Reference"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "scikit learn unsupervised learning"
  - "unsupervised learning reference"
keywords:
  - "scikit"
  - "learn"
  - "unsupervised"
  - "learning"
  - "specialized"
  - "scientific"
  - "reference"
---

# Unsupervised Learning Reference

Targets scikit-learn 1.9.1. Snippets with caller-supplied data/columns are illustrative; fit all learned preprocessing inside the training folds when estimating predictive performance.

## Overview

Unsupervised learning discovers patterns in unlabeled data through clustering, dimensionality reduction, and density estimation.

## Clustering

### K-Means

**KMeans (`sklearn.cluster.KMeans`)**
- Partition-based clustering into K clusters
- Key parameters:
  - `n_clusters`: Number of clusters to form
  - `init`: Initialization method ('k-means++', 'random')
  - `n_init`: Number of initializations (default='auto'; one run with k-means++, ten with random init). Set an integer explicitly for repeatable search effort
  - `max_iter`: Maximum iterations
- Use when: Know number of clusters, spherical cluster shapes
- Fast and scalable
- Example:
```python
from sklearn.cluster import KMeans

model = KMeans(n_clusters=3, init='k-means++', n_init=10, random_state=42)
labels = model.fit_predict(X)
centers = model.cluster_centers_

# Inertia (sum of squared distances to nearest center)
print(f"Inertia: {model.inertia_}")
```

**MiniBatchKMeans**
- Faster K-Means using mini-batches
- Use when: Large datasets, need faster training
- Slightly less accurate than K-Means
- Example:
```python
from sklearn.cluster import MiniBatchKMeans

model = MiniBatchKMeans(n_clusters=3, batch_size=100, random_state=42)
labels = model.fit_predict(X)
```

### Density-Based Clustering

**DBSCAN (`sklearn.cluster.DBSCAN`)**
- Density-Based Spatial Clustering
- Key parameters:
  - `eps`: Maximum distance between two samples to be neighbors
  - `min_samples`: Minimum samples in neighborhood to form core point
  - `metric`: Distance metric
- Use when: Arbitrary cluster shapes, presence of noise/outliers
- Automatically determines number of clusters
- Labels noise points as -1
- Example:
```python
from sklearn.cluster import DBSCAN

model = DBSCAN(eps=0.5, min_samples=5, metric='euclidean')
labels = model.fit_predict(X)

# Number of clusters (excluding noise)
n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
n_noise = list(labels).count(-1)
print(f"Clusters: {n_clusters}, Noise points: {n_noise}")
```

**HDBSCAN (`sklearn.cluster.HDBSCAN`)**
- Hierarchical DBSCAN with adaptive epsilon (added in scikit-learn 1.3)
- Handles varying density; performance and semantics still depend on data and parameters
- scikit-learn includes the point itself in `min_samples`; the contrib `hdbscan` package does not. Do not transfer that parameter unchanged between implementations
- Key parameter: `min_cluster_size`
- Use when: Varying density clusters
- Example:
```python
from sklearn.cluster import HDBSCAN

model = HDBSCAN(min_cluster_size=10, min_samples=5)
labels = model.fit_predict(X)
```

**OPTICS (`sklearn.cluster.OPTICS`)**
- Ordering points to identify clustering structure
- Similar to DBSCAN but doesn't require eps parameter
- Key parameters: `min_samples`, `max_eps`
- Use when: Varying density, exploratory analysis
- Example:
```python
from sklearn.cluster import OPTICS

model = OPTICS(min_samples=5, max_eps=0.5)
labels = model.fit_predict(X)
```

### Hierarchical Clustering

**AgglomerativeClustering**
- Bottom-up hierarchical clustering
- Key parameters:
  - `n_clusters`: Number of clusters (or use `distance_threshold`)
  - `linkage`: 'ward', 'complete', 'average', 'single'
  - `metric`: Distance metric
- Use when: Need dendrogram, hierarchical structure important
- Example:
```python
from sklearn.cluster import AgglomerativeClustering

model = AgglomerativeClustering(n_clusters=3, linkage='ward')
labels = model.fit_predict(X)

# Create dendrogram using scipy
from scipy.cluster.hierarchy import dendrogram, linkage
Z = linkage(X, method='ward')
dendrogram(Z)
```

### Other Clustering Methods

**MeanShift**
- Finds clusters by shifting points toward mode of density
- Automatically determines number of clusters
- Key parameter: `bandwidth`
- Use when: Don't know number of clusters, arbitrary shapes
- Example:
```python
from sklearn.cluster import MeanShift, estimate_bandwidth

# Estimate bandwidth
bandwidth = estimate_bandwidth(X, quantile=0.2, n_samples=500)
model = MeanShift(bandwidth=bandwidth)
labels = model.fit_predict(X)
```

**SpectralClustering**
- Uses graph-based approach with eigenvalues
- Key parameters: `n_clusters`, `affinity` ('rbf', 'nearest_neighbors')
- Use when: Non-convex clusters, graph structure
- Example:
```python
from sklearn.cluster import SpectralClustering

model = SpectralClustering(n_clusters=3, affinity='rbf', random_state=42)
labels = model.fit_predict(X)
```

**AffinityPropagation**
- Finds exemplars by message passing
- Automatically determines number of clusters
- Key parameters: `damping`, `preference`
- Use when: Don't know number of clusters
- Example:
```python
from sklearn.cluster import AffinityPropagation

model = AffinityPropagation(damping=0.9, random_state=42)
labels = model.fit_predict(X)
n_clusters = len(model.cluster_centers_indices_)
```

**BIRCH**
- Balanced Iterative Reducing and Clustering using Hierarchies
- Memory efficient for large datasets
- Key parameters: `n_clusters`, `threshold`, `branching_factor`
- Use when: Very large datasets
- Example:
```python
from sklearn.cluster import Birch

model = Birch(n_clusters=3, threshold=0.5)
labels = model.fit_predict(X)
```

### Clustering Evaluation

**Metrics when ground truth is known:**
```python
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score
from sklearn.metrics import adjusted_mutual_info_score, fowlkes_mallows_score

# Compare predicted labels with true labels
ari = adjusted_rand_score(y_true, y_pred)
nmi = normalized_mutual_info_score(y_true, y_pred)
ami = adjusted_mutual_info_score(y_true, y_pred)
fmi = fowlkes_mallows_score(y_true, y_pred)
```

**Metrics without ground truth:**
These require `2 <= n_labels < n_samples`. Noise label `-1` is otherwise treated as an ordinary cluster: explicitly decide whether to exclude noise and report retained coverage. Scores on different subsets are not directly comparable, and these Euclidean indices favor compact/convex clusters.
```python
from sklearn.metrics import silhouette_score, calinski_harabasz_score
from sklearn.metrics import davies_bouldin_score

# Silhouette: [-1, 1], higher is better
silhouette = silhouette_score(X, labels)

# Calinski-Harabasz: higher is better
ch_score = calinski_harabasz_score(X, l

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

