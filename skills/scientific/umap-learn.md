---
id: sci-umap-learn
name: "Scientific: umap-learn"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Applies UMAP-learn to nonlinear dimensionality reduction, 2D/3D embeddings, clustering preprocessing, supervised or semi-supervised UMAP, DensMAP, AlignedUMAP, and Parametric UMAP workflows."
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "umap learn"
  - "umap-learn"
keywords:
  - "umap"
  - "learn"
  - "applies"
  - "nonlinear"
  - "dimensionality"
  - "reduction"
---

# UMAP-Learn

## Overview

UMAP (Uniform Manifold Approximation and Projection) is a dimensionality reduction technique for visualization and general non-linear dimensionality reduction. Apply this skill for fast, scalable embeddings that approximate neighborhood structure, supervised learning, and clustering preprocessing.

Before interpreting an embedding, check finite coordinates, neighborhood retention, sensitivity to seeds/parameters, and domain evidence in the original space. UMAP axes, island areas, and gaps between clusters have no calibrated physical or probabilistic meaning. Keep predictive test data outside preprocessing and embedding fits.

## Quick Start

### Installation

Verified on 2026-10-01: **umap-learn 0.5.12** is the current stable release (April 2026). Requires Python 3.9+ and depends on `scikit-learn>=1.6`, `numba`, `pynndescent`, `numpy`, and `scipy`. Pin to a verified release:

```bash
uv pip install umap-learn==0.5.12
```

### Basic Usage

UMAP uses the scikit-learn estimator interface, but its geometry and supervised behavior differ from PCA and t-SNE. Core examples were exercised on small synthetic data with Python 3.13, scikit-learn 1.9.1, NumPy 2.5.3, and Numba 0.68.0. Parametric examples are source-checked illustrations, not executed TensorFlow tests. In snippets below, `data` is a finite samples-by-features array and labels must follow the same row order.

```python
import umap
from sklearn.preprocessing import StandardScaler

# Scale continuous features when their units should carry equal weight
scaled_data = StandardScaler().fit_transform(data)

# Method 1: Single step (fit and transform)
embedding = umap.UMAP(random_state=42, n_jobs=1).fit_transform(scaled_data)

# Method 2: Separate steps (for reusing trained model)
reducer = umap.UMAP(random_state=42)
reducer.fit(scaled_data)
embedding = reducer.embedding_  # Access the trained embedding
```

**Preprocessing requirement:** Match preprocessing to the metric. For numeric Euclidean-style metrics, decide whether scaling is scientifically appropriate; it changes the feature weighting. Fit preprocessing on training data only for predictive work. Use `StandardScaler(with_mean=False)` for sparse matrices to avoid densifying them. For cosine, binary, precomputed-distance, or mixed-feature workflows, choose preprocessing that matches the metric instead of blindly standardizing every column.

### Typical Workflow

```python
import umap
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler

# 1. Preprocess data
scaler = StandardScaler()
scaled_data = scaler.fit_transform(raw_data)

# 2. Create and fit UMAP
reducer = umap.UMAP(
    n_neighbors=15,
    min_dist=0.1,
    n_components=2,
    metric='euclidean',
    random_state=42
)
embedding = reducer.fit_transform(scaled_data)

# 3. Visualize
plt.scatter(embedding[:, 0], embedding[:, 1], c=labels, cmap='Spectral', s=5)
plt.colorbar()
plt.title('UMAP Embedding')
plt.show()
```

## Parameter Tuning Guide

UMAP has four primary parameters that control the embedding behavior. Understanding these is crucial for effective usage.

### n_neighbors (default: 15)

**Purpose:** Balances local versus global structure in the embedding.

**How it works:** Controls the size of the local neighborhood UMAP examines when learning manifold structure.

**Effects by value:**
- **Low values (2-5):** Emphasizes fine local detail but may fragment data into disconnected components
- **Medium values (15-20):** Balanced view of both local structure and global relationships (recommended starting point)
- **High values (50-200):** Prioritizes broad topological structure at the expense of fine-grained details

**Recommendation:** Start with 15, keep it below the number of fitted samples, and compare several values. Larger neighborhoods do not make inter-cluster distances quantitatively reliable.

### min_dist (default: 0.1)

**Purpose:** Controls how tightly points cluster in the low-dimensional space.

**How it works:** Adjusts the attraction curve and typical packing in the embedding; it is not a hard lower bound on pairwise distances. Require `0 <= min_dist <= spread`.

**Effects by value:**
- **Low values (0.0-0.1):** Creates clumped embeddings useful for clustering; reveals fine topological details
- **High values (0.5-0.99):** Encourages looser packing; does not certify preservation of global distances

**Recommendation:** Use 0.0 for clustering applications, 0.1-0.3 for visualization, 0.5+ for loose structure.

### n_components (default: 2)

**Purpose:** Determines the dimensionality of the embedded output space.

**Key feature:** Unlike t-SNE, UMAP scales well in the embedding dimension, enabling use beyond visualization.

**Common uses:**
- **2-3 dimensions:** Visualization
- **5-10 dimensions:** Clustering preprocessing (may retain more useful structure than 2D; does not guarantee density preservation)
- **10-50 dimensions:** Feature engineering for downstream ML models

**Recommendation:** Use 2 for visualization, 5-10 for clustering, higher for ML pipelines.

### metric (default: 'euclidean')

**Purpose:** Specifies how distance is calculated between input data points.

**Supported metrics:**
- **Minkowski variants:** euclidean, manhattan, chebyshev
- **Spatial metrics:** canberra, braycurtis, haversine
- **Correlation metrics:** cosine, correlation (good for text/document embeddings)
- **Binary data metrics:** hamming, jaccard, dice, russellrao, kulsinski, rogerstanimoto, sokalmichener, sokalsneath, yule
- **Custom metrics:** User-defined distance functions via Numba

**Recommendation:** Use euclidean for numeric data, cosine for text/document vectors, hamming for binary data.

### Parameter Tuning Example

```python
# For visualization with emphasis on local structure
umap.UMAP(n_neighbors=15, min_dist=0.1, n_components=2, metric='euclidean')

# For clustering preprocessing
umap.UMAP(n_neighbors=30, min_dist=0.0, n_components=10, metric='euclidean')

# For document embeddings
umap.UMAP(n_neighbors=15, min_dist=0.1, n_components=2, metric='cosine')

# For emphasizing broader neighborhoods
umap.UMAP(n_neighbors=100, min_dist=0.5, n_components=2, metric='euclidean')
```

## Supervised and Semi-Supervised Dimension Reduction

UMAP supports incorporating label information to guide the embedding process, encouraging class separation while retaining parts of the feature-neighborhood graph.

### Supervised UMAP

Pass target labels via the `y` parameter

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

