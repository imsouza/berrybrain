---
id: sciref-anndata-manipulation
name: "Scientific Ref: Data Manipulation"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (anndata): Data Manipulation"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "anndata manipulation"
  - "data manipulation"
keywords:
  - "anndata"
  - "manipulation"
  - "specialized"
  - "scientific"
  - "reference"
---

# Data Manipulation

Operations for transforming, subsetting, and manipulating AnnData objects.

## Subsetting

### By indices
```python
import anndata as ad
import numpy as np

adata = ad.AnnData(X=np.random.rand(1000, 2000))

# Integer indices
subset = adata[0:100, 0:500]  # First 100 obs, first 500 vars

# List of indices
obs_indices = [0, 10, 20, 30, 40]
var_indices = [0, 1, 2, 3, 4]
subset = adata[obs_indices, var_indices]

# Single observation or variable
single_obs = adata[0, :]
single_var = adata[:, 0]
```

### By names
```python
import pandas as pd

# Create with named indices
obs_names = [f'cell_{i}' for i in range(1000)]
var_names = [f'gene_{i}' for i in range(2000)]
adata = ad.AnnData(
    X=np.random.rand(1000, 2000),
    obs=pd.DataFrame(index=obs_names),
    var=pd.DataFrame(index=var_names)
)

# Subset by observation names
subset = adata[['cell_0', 'cell_1', 'cell_2'], :]

# Subset by variable names
subset = adata[:, ['gene_0', 'gene_10', 'gene_20']]

# Both axes
subset = adata[['cell_0', 'cell_1'], ['gene_0', 'gene_1']]
```

### By boolean masks
```python
# Create boolean masks
high_count_obs = np.random.rand(1000) > 0.5
high_var_genes = np.random.rand(2000) > 0.7

# Subset using masks
subset = adata[high_count_obs, :]
subset = adata[:, high_var_genes]
subset = adata[high_count_obs, high_var_genes]
```

### By metadata conditions
```python
# Add metadata
adata.obs['cell_type'] = np.random.choice(['A', 'B', 'C'], 1000)
adata.obs['quality_score'] = np.random.rand(1000)
adata.var['highly_variable'] = np.random.rand(2000) > 0.8

# Filter by cell type
t_cells = adata[adata.obs['cell_type'] == 'A']

# Filter by multiple conditions
high_quality_a_cells = adata[
    (adata.obs['cell_type'] == 'A') &
    (adata.obs['quality_score'] > 0.7)
]

# Filter by variable metadata
hv_genes = adata[:, adata.var['highly_variable']]

# Complex conditions
filtered = adata[
    (adata.obs['quality_score'] > 0.5) &
    (adata.obs['cell_type'].isin(['A', 'B'])),
    adata.var['highly_variable']
]
```

## Transposition

```python
# Transpose AnnData object (swap observations and variables)
adata_T = adata.copy().T

# Shape changes
print(adata.shape)    # (1000, 2000)
print(adata_T.shape)  # (2000, 1000)

# obs and var are swapped
print(adata.obs.head())   # Observation metadata
print(adata_T.var.head()) # Same data, now as variable metadata

# Transposition drops .raw and is unsupported directly on views/backed arrays.
# Materialize backed data with .to_memory() first if it fits.
# Useful when data is in opposite orientation
# Common with some file formats where genes are rows
```

## Copying

### Full copy
```python
# Create independent copy
adata_copy = adata.copy()

# Modifications to copy don't affect original
adata_copy.obs['new_column'] = 1
print('new_column' in adata.obs.columns)  # False
```

### View
```python
# View (subset arrays are accessed lazily; writes can materialize a copy)
adata_view = adata[0:100, :]

# Check if object is a view
print(adata_view.is_view)  # True

# Convert view to independent copy
adata_independent = adata_view.copy()
print(adata_independent.is_view)  # False
```

## Renaming

### Rename observations and variables
```python
# Rename all observations
adata.obs_names = [f'new_cell_{i}' for i in range(adata.n_obs)]

# Rename all variables
adata.var_names = [f'new_gene_{i}' for i in range(adata.n_vars)]

# Make names unique (add suffix to duplicates)
adata.obs_names_make_unique()
adata.var_names_make_unique()
```

### Rename categories
```python
# Create categorical column
adata.obs['cell_type'] = pd.Categorical(['A', 'B', 'C'] * 333 + ['A'])

# Rename categories
adata.rename_categories('cell_type', ['Type_A', 'Type_B', 'Type_C'])

# Mapping input is unsupported by AnnData.rename_categories; preserve category order.
rename = {'Type_A': 'T_cell', 'Type_B': 'B_cell', 'Type_C': 'Monocyte'}
adata.rename_categories(
    'cell_type', [rename.get(c, c) for c in adata.obs['cell_type'].cat.categories]
)
```

## Type Conversions

### Strings to categoricals
```python
# Convert string columns to categorical (more memory efficient)
adata.obs['cell_type'] = ['TypeA', 'TypeB'] * 500
adata.obs['tissue'] = ['brain', 'liver'] * 500

# Convert all string columns to categorical
adata.strings_to_categoricals()

print(adata.obs['cell_type'].dtype)  # category
print(adata.obs['tissue'].dtype)     # category
```

### Sparse to dense and vice versa
```python
from scipy.sparse import csr_matrix, issparse

# Dense to sparse
if not issparse(adata.X):
    adata.X = csr_matrix(adata.X)

# Sparse to dense
if issparse(adata.X):
    adata.X = adata.X.toarray()

# Convert layer
adata.layers['normalized'] = csr_matrix(adata.layers['normalized'])
```

## Chunked Operations

Process large datasets in chunks:

```python
# Iterate through data in chunks
chunk_size = 100
for chunk, start, stop in adata.chunked_X(chunk_size):
    # Process chunk
    result = process_chunk(chunk)
```

## Extracting Vectors

### Get observation vectors
```python
# Get observation metadata as array
cell_types = adata.obs_vector('cell_type')

# Get gene expression across observations
actb_expression = adata.obs_vector('ACTB')  # If ACTB in var_names
```

### Get variable vectors
```python
# Get variable metadata as array
gene_names = adata.var_vector('gene_name')
```

## Adding/Modifying Data

### Add observations
```python
# Create new observations
new_obs = ad.AnnData(X=np.random.rand(100, adata.n_vars))
new_obs.var_names = adata.var_names

# Concatenate with existing
adata_extended = ad.concat([adata, new_obs], axis=0)
```

### Add variables
```python
# Create new variables
new_vars = ad.AnnData(X=np.random.rand(adata.n_obs, 100))
new_vars.obs_names = adata.obs_names

# Concatenate with existing
adata_extended = ad.concat([adata, new_vars], axis=1)
```

### Add metadata columns
```python
# Add observation annotation
adata.obs['new_score'] = np.random.rand(adata.n_obs)

# Add variable annotation
adata.var['new_label'] = ['label'] * adata.n_vars

# Add from external data
external_data = pd.read_csv('metadata.csv', index_col=0)
adata.obs['external_info'] = external_data.loc[adata.obs_names, 'column']
```

### Add layers
```python
# Add new layer
adata.layers['raw_counts'] = np.random.randint(0, 100, adata.shape)
adata.layers['log_transformed'] = np.log1p(adata.X)

# Replace layer
adata.layers['normalized'] = new_normalized_data
```

### Add embeddings
```python
# Add PCA
adata.obsm['X_pca'] = np.random.rand(adata.n

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

