---
id: sciref-umap-learn-api-reference
name: "Scientific Ref: UMAP API Reference"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (umap-learn): UMAP API Reference"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "umap learn api reference"
  - "umap api reference"
keywords:
  - "umap"
  - "learn"
  - "api"
  - "reference"
  - "specialized"
  - "scientific"
---

# UMAP API Reference

Reference checked 2026-10-01 for **umap-learn 0.5.12** (Python >=3.9; `scikit-learn>=1.6`). The [hosted API guide](https://umap-learn.readthedocs.io/en/latest/api.html) still identifies 0.5.8; use the [released implementation](https://github.com/lmcinnes/umap/blob/release-0.5.12/umap/umap_.py) for exact signatures and return contracts. All calculations run locally; the package has no service endpoint, authentication, or pagination requirement. Examples assume finite numeric arrays with stable sample/feature ordering. Core synthetic checks used native Numba JIT; TensorFlow examples are illustrative and source-checked only.

## UMAP Class

`umap.UMAP(n_neighbors=15, n_components=2, metric='euclidean', metric_kwds=None, output_metric='euclidean', output_metric_kwds=None, n_epochs=None, learning_rate=1.0, init='spectral', min_dist=0.1, spread=1.0, low_memory=True, n_jobs=-1, set_op_mix_ratio=1.0, local_connectivity=1.0, repulsion_strength=1.0, negative_sample_rate=5, transform_queue_size=4.0, a=None, b=None, random_state=None, angular_rp_forest=False, target_n_neighbors=-1, target_metric='categorical', target_metric_kwds=None, target_weight=0.5, transform_seed=42, transform_mode='embedding', force_approximation_algorithm=False, verbose=False, tqdm_kwds=None, unique=False, densmap=False, dens_lambda=2.0, dens_frac=0.3, dens_var_shift=0.1, output_dens=False, disconnection_distance=None, precomputed_knn=(None, None, None))`

Find low-dimensional embedding that approximates the underlying manifold of the data.

### Core Parameters

#### n_neighbors (int, default: 15)
Size of the local neighborhood used for manifold approximation. Larger values result in more global views of the manifold, while smaller values preserve more local structure. Generally in the range 2 to 100.

**Tuning guidance:**
- Use 2-5 for very local structure
- Use 10-20 for balanced local/global structure (typical)
- Use 50-200 for emphasizing global structure

#### n_components (int, default: 2)
Dimension of the embedding space. Unlike t-SNE, UMAP scales well with increasing embedding dimensions.

**Common values:**
- 2-3: Visualization
- 5-10: Clustering preprocessing
- 10-100: Feature engineering for downstream ML

#### metric (str or callable, default: 'euclidean')
Distance metric to use. Accepts:
- Recognized names in UMAP/PyNNDescent; not every SciPy or scikit-learn metric is accepted, and sparse support differs from dense support
- `"precomputed"`: distances, not similarities; see the recipe below
- Custom Numba-compatible callables returning a distance; return `(distance, gradient)` to enable inverse transformation

**Common metrics:**
- `'euclidean'`: Standard Euclidean distance (default)
- `'manhattan'`: L1 distance
- `'cosine'`: Cosine distance (good for text/document vectors)
- `'correlation'`: Correlation distance
- `'hamming'`: Hamming distance (for binary data)
- `'jaccard'`: Jaccard distance (for binary/set data)
- `'dice'`: Dice distance
- `'canberra'`: Canberra distance
- `'braycurtis'`: Bray-Curtis distance
- `'chebyshev'`: Chebyshev distance
- `'minkowski'`: Minkowski distance (specify p with metric_kwds)
- `'precomputed'`: Use precomputed distance matrix

#### output_metric (str or callable, default: 'euclidean')
Distance metric for the embedding space. Most workflows should keep the Euclidean default; advanced workflows can use a supported output metric with `output_metric_kwds`.

#### min_dist (float, default: 0.1)
A parameter of the fitted low-dimensional attraction curve, not a hard pairwise-distance bound. Smaller values favor clumpier embeddings. Require `0 <= min_dist <= spread`.

**Tuning guidance:**
- Use 0.0 for clustering applications
- Use 0.1-0.3 for visualization (balanced)
- Use 0.5-0.99 for loose structure preservation

#### spread (float, default: 1.0)
Effective scale of embedded points. Combined with `min_dist` to control clumped vs. spread-out embeddings. Determines how spread out the clusters are in the embedding space.

### Training Parameters

#### n_epochs (int, list of int, or None; default: None)
Optimization epochs. With `None`, standard UMAP uses 500 epochs up to 10,000 samples and 200 above that; densMAP adds 200. A list requests intermediate embeddings in `embedding_list_`, while `embedding_` is the final result.

**Manual tuning:**
- Smaller datasets may need 500+ epochs
- Larger datasets may converge with 200 epochs
- More epochs increase cost; scientific validity still requires external checks

#### learning_rate (float, default: 1.0)
Initial learning rate for the SGD optimizer. Higher values lead to faster convergence but may overshoot optimal solutions.

#### init (str or np.ndarray, default: 'spectral')
Initialization method for the embedding:
- `'spectral'`: Spectral initialization (default)
- `'random'`: Random initialization
- `'pca'`: Initialize with PCA (TruncatedSVD for sparse input)
- `'tswspectral'`: Truncated-SVD warm start for spectral initialization
- numpy array: Custom initialization (shape: (n_samples, n_components))

### Advanced Structural Parameters

#### local_connectivity (float, default: 1.0)
Number of nearest neighbors assumed to be locally connected. Higher values give more connected manifolds.

#### set_op_mix_ratio (float, default: 1.0)
Interpolation between union and intersection when constructing fuzzy set unions. Value of 1.0 uses pure union, 0.0 uses pure intersection.

#### repulsion_strength (float, default: 1.0)
Weighting applied to negative samples in low-dimensional embedding optimization. Higher values push embedded points further apart.

#### negative_sample_rate (int, default: 5)
Number of negative samples to select per positive sample. Higher values lead to greater repulsion between points and more spread-out embeddings but increase computational cost.

### Supervised Learning Parameters

#### target_n_neighbors (int, default: -1)
Number of nearest neighbors to use when constructing target simplicial set. If -1, uses n_neighbors value.

#### target_metric (str or callable, default: 'categorical')
Distance metric for target values (labels):
- `'categorical'`: For classification tasks
- A supported continuous metric such as `"l2"` for regression targets; `-1` is not a generic missing-value marker

#### target_weight (float, default: 0.5)
Weight applied to target information vs. data structure. Range 0.0 to 1.0:
- Lower values emphasize the feature graph; higher values emphasize target agreement
- 0.5 is th

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

