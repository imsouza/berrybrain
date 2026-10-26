---
id: sciref-aeon-clustering
name: "Scientific Ref: Time Series Clustering"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (aeon): Time Series Clustering"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "aeon clustering"
  - "time series clustering"
keywords:
  - "aeon"
  - "clustering"
  - "specialized"
  - "scientific"
  - "reference"
  - "time"
  - "series"
---

# Time Series Clustering

Aeon provides clustering algorithms adapted for temporal data with specialized distance metrics and averaging methods.

## Partitioning Algorithms

Standard k-means/k-medoids adapted for time series:

- `TimeSeriesKMeans` - K-means with temporal distance metrics (DTW, Euclidean, etc.)
- `TimeSeriesKMedoids` - Uses actual time series as cluster centers
- `KShape` - Shape-based clustering algorithm
- `TimeSeriesKernelKMeans` - Kernel-based variant for nonlinear patterns

**Use when**: Known number of clusters, spherical cluster shapes expected.

## Large Dataset Methods

Efficient clustering for large collections:

- `TimeSeriesCLARA` - Clustering Large Applications with sampling
- `TimeSeriesCLARANS` - Randomized search variant of CLARA

**Use when**: Dataset too large for standard k-medoids, need scalability.

## Elastic Distance Clustering

Specialized for alignment-based similarity:

- `KASBA` - K-means with stochastic subgradient elastic barycenter averaging
- `ElasticSOM` - Self-organizing map using elastic distances

**Use when**: Time series have temporal shifts or warping.

## Spectral Methods

Scale- and shift-invariant centroid clustering:

- `KSpectralCentroid` - K-Spectral Centroid clustering using shape-based alignment

**Use when**: Series shape matters despite differences in scale and temporal shift.

## Deep Learning Clustering

Neural network-based clustering with auto-encoders:

- `AEFCNClusterer` - Fully convolutional auto-encoder
- `AEResNetClusterer` - Residual network auto-encoder
- `AEDCNNClusterer` - Dilated CNN auto-encoder
- `AEDRNNClusterer` - Dilated RNN auto-encoder
- `AEBiGRUClusterer` - Bidirectional GRU auto-encoder
- `AEAttentionBiGRUClusterer` - Attention-enhanced BiGRU auto-encoder

**Use when**: Large datasets, need learned representations, or complex patterns.

## Feature-Based Clustering

Transform to feature space before clustering:

- `Catch22Clusterer` - Clusters on 22 canonical features
- `SummaryClusterer` - Uses summary statistics
- `TSFreshClusterer` - Automated tsfresh features

**Use when**: Raw time series not informative, need interpretable features.

## Composition

Build custom clustering pipelines:

- `ClustererPipeline` - Chain transformers with clusterers

## Averaging Methods

Compute cluster centers for time series:

- `mean_average` - Arithmetic mean
- `ba_average` - Barycentric averaging with DTW
- `kasba_average` - Stochastic subgradient elastic barycenter averaging
- `shift_invariant_average` - General shift-invariant method

**Use when**: Need representative cluster centers for visualization or initialization.

## Quick Start

```python
from aeon.clustering import TimeSeriesKMeans
from aeon.datasets import load_classification

# Load data (using classification data for clustering)
X_train, _ = load_classification("GunPoint", split="train")

# Cluster time series
clusterer = TimeSeriesKMeans(
    n_clusters=3,
    distance="dtw",  # Use DTW distance
    averaging_method="ba"  # Barycentric averaging
)
labels = clusterer.fit_predict(X_train)
centers = clusterer.cluster_centers_
```

## Algorithm Selection

- **Speed priority**: TimeSeriesKMeans with Euclidean distance
- **Temporal alignment**: KASBA, TimeSeriesKMeans with DTW
- **Large datasets**: TimeSeriesCLARA, TimeSeriesCLARANS
- **Complex patterns**: Deep learning clusterers
- **Interpretability**: Catch22Clusterer, SummaryClusterer
- **Scale/shift invariant shapes**: KSpectralCentroid

## Distance Metrics

Compatible distance metrics include:
- Euclidean, Manhattan, Minkowski (lock-step)
- DTW, DDTW, WDTW (elastic with alignment)
- ERP, EDR, LCSS (edit-based)
- MSM, TWE (specialized elastic)

## Evaluation

For elastic distances, compute a pairwise matrix and pass it to sklearn `silhouette_score(..., metric="precomputed")`. Davies-Bouldin and Calinski-Harabasz expect Euclidean feature vectors; do not pass a DTW matrix as features. With known class labels, `aeon.benchmarking.metrics.clustering.clustering_accuracy_score` optimally matches cluster IDs to class IDs.

For Euclidean k-means set `distance="euclidean", averaging_method="mean"` explicitly. Elastic barycenter averaging supports only its documented distance subset; a distance callable alone does not guarantee a compatible averaging method. `TimeSeriesAgglomerative` (new in 1.6) supports fit-time labels but does not predict unseen cases; inspect `capability:predict` for clusterers.

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

