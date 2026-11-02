---
id: sciref-anndata-data-structure
name: "Scientific Ref: AnnData Object Structure"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (anndata): AnnData Object Structure"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "anndata structure"
  - "anndata object structure"
keywords:
  - "anndata"
  - "structure"
  - "specialized"
  - "scientific"
  - "reference"
  - "object"
---

# AnnData Object Structure

The AnnData object stores a data matrix with associated annotations, providing a flexible framework for managing experimental data and metadata.

## Core Components

### X (Data Matrix)
The primary data matrix has shape `(n_obs, n_vars)` (observations by variables). It may be `None` for metadata-only objects. Record whether values are counts, normalized expression, residuals, or another measurement; names alone do not establish units.

```python
import anndata as ad
import numpy as np

# Create with dense array
adata = ad.AnnData(X=np.random.rand(100, 2000))

# Create with sparse matrix (recommended for large, sparse data)
from scipy.sparse import csr_matrix
sparse_data = csr_matrix(np.random.default_rng(42).binomial(1, 0.01, (100, 2000)))
adata = ad.AnnData(X=sparse_data)
```

Access data:
```python
# Full matrix (caution with large datasets)
full_data = adata.X

# Single observation
obs_data = adata.X[0, :]

# Single variable across all observations
var_data = adata.X[:, 0]
```

### obs (Observation Annotations)
DataFrame storing metadata about observations (rows). Each row corresponds to one observation in X.

```python
import pandas as pd

# Create AnnData with observation metadata
obs_df = pd.DataFrame({
    'cell_type': ['T cell', 'B cell', 'Monocyte'],
    'treatment': ['control', 'treated', 'control'],
    'timepoint': [0, 24, 24]
}, index=['cell_1', 'cell_2', 'cell_3'])

adata = ad.AnnData(X=np.random.rand(3, 100), obs=obs_df)

# Access observation metadata
print(adata.obs['cell_type'])
print(adata.obs.loc['cell_1'])
```

### var (Variable Annotations)
DataFrame storing metadata about variables (columns). Each row corresponds to one variable in X.

```python
# Create AnnData with variable metadata
var_df = pd.DataFrame({
    'gene_name': ['ACTB', 'GAPDH', 'TP53'],
    'chromosome': ['7', '12', '17'],
    'highly_variable': [True, False, True]
}, index=['ENSG00001', 'ENSG00002', 'ENSG00003'])

adata = ad.AnnData(X=np.random.rand(100, 3), var=var_df)

# Access variable metadata
print(adata.var['gene_name'])
print(adata.var.loc['ENSG00001'])
```

### layers (Alternative Data Representations)
Mapping of same-shape matrices. In **AnnData 0.13.4**, `layers[None]` aliases `X` and iteration includes this special key. Named layers remain strings; handle `None` explicitly in code that exports or enumerates layers. On disk, native formats still store X under the top-level `X` key.

```python
# Derive each representation from the SAME synthetic count matrix.
counts = np.random.default_rng(42).poisson(1, (100, 2000)).astype('float32')
adata = ad.AnnData(X=counts)
adata.layers['raw_counts'] = adata.X.copy()
totals = adata.X.sum(axis=1, keepdims=True)
adata.layers['normalized'] = adata.X / np.where(totals == 0, 1, totals)
std = adata.X.std(axis=0)
adata.layers['scaled'] = (adata.X - adata.X.mean(axis=0)) / np.where(std == 0, 1, std)

# Access layers
raw_data = adata.layers['raw_counts']
normalized_data = adata.layers['normalized']
named_layers = {key: value for key, value in adata.layers.items() if key is not None}
assert adata.layers[None] is adata.X
```

Common layer uses:
- `raw_counts`: Original count data before normalization
- `normalized`: Log-normalized or TPM values
- `scaled`: Z-scored values for analysis
- `imputed`: Data after imputation

### obsm (Multi-dimensional Observation Annotations)
Dictionary storing multi-dimensional arrays aligned to observations.

```python
# Store PCA coordinates and UMAP embeddings
adata.obsm['X_pca'] = np.random.rand(100, 50)  # 50 principal components
adata.obsm['X_umap'] = np.random.rand(100, 2)  # 2D UMAP coordinates
adata.obsm['X_tsne'] = np.random.rand(100, 2)  # 2D t-SNE coordinates

# Access embeddings
pca_coords = adata.obsm['X_pca']
umap_coords = adata.obsm['X_umap']
```

Common obsm uses:
- `X_pca`: Principal component coordinates
- `X_umap`: UMAP embedding coordinates
- `X_tsne`: t-SNE embedding coordinates
- `X_diffmap`: Diffusion map coordinates
- `protein_expression`: Protein abundance measurements (CITE-seq)

### varm (Multi-dimensional Variable Annotations)
Dictionary storing multi-dimensional arrays aligned to variables.

```python
# Store PCA loadings
adata.varm['PCs'] = np.random.rand(2000, 50)  # Loadings for 50 components
adata.varm['gene_modules'] = np.random.rand(2000, 10)  # Gene module scores

# Access loadings
pc_loadings = adata.varm['PCs']
```

Common varm uses:
- `PCs`: Principal component loadings
- `gene_modules`: Gene co-expression module assignments

### obsp (Pairwise Observation Relationships)
Mapping of dense or sparse arrays whose first two dimensions are `(n_obs, n_obs)`.

```python
from scipy.sparse import csr_matrix

# Store k-nearest neighbor graph
n_obs = 100
knn_graph = csr_matrix(np.random.rand(n_obs, n_obs) > 0.95)
adata.obsp['connectivities'] = knn_graph
adata.obsp['distances'] = csr_matrix(np.random.rand(n_obs, n_obs))

# Access graphs
knn_connections = adata.obsp['connectivities']
distances = adata.obsp['distances']
```

Common obsp uses:
- `connectivities`: Cell-cell neighborhood graph
- `distances`: Pairwise distances between cells

### varp (Pairwise Variable Relationships)
Mapping of dense or sparse arrays whose first two dimensions are `(n_vars, n_vars)`.

```python
# Store gene-gene correlation matrix
n_vars = 2000
gene_corr = csr_matrix(np.random.rand(n_vars, n_vars) > 0.99)
adata.varp['correlations'] = gene_corr

# Access correlations
gene_correlations = adata.varp['correlations']
```

### uns (Unstructured Annotations)
Mapping for unstructured metadata. In-memory Python objects are not all serializable; native output requires supported AnnData encodings. Avoid slashes in keys and validate by reopening the saved file.

```python
# Store analysis parameters and results
adata.uns['experiment_date'] = '2025-11-03'
adata.uns['pca'] = {
    'variance_ratio': [0.15, 0.10, 0.08],
    'params': {'n_comps': 50}
}
adata.uns['neighbors'] = {
    'params': {'n_neighbors': 15, 'method': 'umap'},
    'connectivities_key': 'connectivities'
}

# Access unstructured data
exp_date = adata.uns['experiment_date']
pca_params = adata.uns['pca']['params']
```

Common uns uses:
- Analysis parameters and settings
- Color palettes for plotting
- Cluster information
- Tool-specific metadata

### raw (Original Data Snapshot)
Optional snapshot of the current `X`, `var`, and `varm`; it is not a full backup and is not automatically raw counts. Observation slicing subsets `.raw`, while var

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

