---
id: sciref-anndata-concatenation
name: "Scientific Ref: Concatenating AnnData Objects"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (anndata): Concatenating AnnData Objects"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "anndata concatenation"
  - "concatenating anndata objects"
keywords:
  - "anndata"
  - "concatenation"
  - "specialized"
  - "scientific"
  - "reference"
  - "concatenating"
---

# Concatenating AnnData Objects

Combine multiple AnnData objects along either axis. Reviewed for AnnData 0.13.4. Match stable identifiers, species/genome build, units, and preprocessing before concatenating. Feature unions with sparse zero fill conflate unmeasured features with observed zeros; preserve a per-batch feature-presence record when that distinction matters.

## Basic Concatenation

### Concatenate along observations (stack cells/samples)
```python
import anndata as ad
import numpy as np

# Create multiple AnnData objects
adata1 = ad.AnnData(X=np.random.rand(100, 50))
adata2 = ad.AnnData(X=np.random.rand(150, 50))
adata3 = ad.AnnData(X=np.random.rand(200, 50))

# Concatenate along observations (axis=0, default)
adata_combined = ad.concat([adata1, adata2, adata3], axis=0, index_unique='-')

print(adata_combined.shape)  # (450, 50)
```

### Concatenate along variables (stack genes/features)
```python
# Create objects with same observations, different variables
adata1 = ad.AnnData(X=np.random.rand(100, 50))
adata2 = ad.AnnData(X=np.random.rand(100, 30))
adata3 = ad.AnnData(X=np.random.rand(100, 70))

# Concatenate along variables (axis=1)
adata_combined = ad.concat([adata1, adata2, adata3], axis=1)

print(adata_combined.shape)  # (100, 150)
```

## Join Types

### Inner join (intersection)
Keep only variables/observations present in all objects.

```python
import pandas as pd

# Create objects with different variables
adata1 = ad.AnnData(
    X=np.random.rand(100, 50),
    var=pd.DataFrame(index=[f'Gene_{i}' for i in range(50)])
)
adata2 = ad.AnnData(
    X=np.random.rand(150, 60),
    var=pd.DataFrame(index=[f'Gene_{i}' for i in range(10, 70)])
)

# Inner join: only genes 10-49 are kept (overlap)
adata_inner = ad.concat([adata1, adata2], join='inner')
print(adata_inner.n_vars)  # 40 genes (overlap)
```

### Outer join (union)
Keep all variables/observations, filling missing values.

```python
# Outer join: all genes are kept
adata_outer = ad.concat([adata1, adata2], join='outer')
print(adata_outer.n_vars)  # 70 genes (union)

# Missing values are filled with appropriate defaults:
# - 0 for sparse matrices
# - NaN for dense matrices
```

### Fill values for outer joins
```python
# Specify fill value for missing data
adata_filled = ad.concat([adata1, adata2], join='outer', fill_value=0)
```

## Tracking Data Sources

### Add batch labels
```python
# Label which object each observation came from
adata_combined = ad.concat(
    [adata1, adata2, adata3],
    label='batch',  # Column name for labels
    keys=['batch1', 'batch2', 'batch3']  # Labels for each object
)

print(adata_combined.obs['batch'].value_counts())
# batch1    100
# batch2    150
# batch3    200
```

### Automatic batch labels
```python
# If keys not provided, uses integer indices
adata_combined = ad.concat(
    [adata1, adata2, adata3],
    label='dataset'
)
# dataset column contains: 0, 1, 2
```

## Merge Strategies

Control how metadata from different objects is combined using the `merge` parameter.

### merge=None (default for either axis)
Exclude metadata on non-concatenation axis.

```python
# When concatenating observations, merge controls var-side annotations
adata1.var['gene_type'] = 'protein_coding'
adata2.var['gene_type'] = 'protein_coding'

# Variable index is kept; var annotation columns are dropped even if identical
adata_combined = ad.concat([adata1, adata2], merge=None)
```

### merge='same'
Keep metadata that is identical across all objects.

```python
adata1.var['chromosome'] = 'chr1'
adata2.var['chromosome'] = 'chr1'
adata1.var['type'] = 'protein_coding'
adata2.var['type'] = 'lncRNA'  # Different

# 'chromosome' is kept (same), 'type' is excluded (different)
adata_combined = ad.concat([adata1, adata2], merge='same')
```

### merge='unique'
Keep elements with one possible value across inputs after index alignment; this does not mean all entries within a column must be identical.

```python
adata1.var['gene_id'] = adata1.var_names
adata2.var['gene_id'] = adata2.var_names

# gene_id is kept (unique values for each key)
adata_combined = ad.concat([adata1, adata2], merge='unique')
```

### merge='first'
Take values from the first object containing each key.

```python
adata1.var['description'] = 'Desc1'
adata2.var['description'] = 'Desc2'

# Uses descriptions from adata1
adata_combined = ad.concat([adata1, adata2], merge='first')
```

### merge='only'
Keep metadata that appears in only one object.

```python
adata1.var['adata1_specific'] = 1
adata2.var['adata2_specific'] = 2

# Both metadata columns are kept
adata_combined = ad.concat([adata1, adata2], merge='only')
```

## Handling Index Conflicts

### Make indices unique
```python
import pandas as pd

# Create objects with overlapping observation names
adata1 = ad.AnnData(
    X=np.random.rand(3, 10),
    obs=pd.DataFrame(index=['cell_1', 'cell_2', 'cell_3'])
)
adata2 = ad.AnnData(
    X=np.random.rand(3, 10),
    obs=pd.DataFrame(index=['cell_1', 'cell_2', 'cell_3'])
)

# Make indices unique by appending batch keys
adata_combined = ad.concat(
    [adata1, adata2],
    label='batch',
    keys=['batch1', 'batch2'],
    index_unique='_'  # Separator for making indices unique
)

print(adata_combined.obs_names)
# ['cell_1_batch1', 'cell_2_batch1', 'cell_3_batch1',
#  'cell_1_batch2', 'cell_2_batch2', 'cell_3_batch2']
```

## Concatenating Layers

```python
# Objects with layers
adata1 = ad.AnnData(X=np.random.rand(100, 50))
adata1.layers['normalized'] = np.random.rand(100, 50)
adata1.layers['scaled'] = np.random.rand(100, 50)

adata2 = ad.AnnData(X=np.random.rand(150, 50))
adata2.layers['normalized'] = np.random.rand(150, 50)
adata2.layers['scaled'] = np.random.rand(150, 50)

# With join="inner", common layers are concatenated (outer joins union keys)
adata_combined = ad.concat([adata1, adata2])

print(adata_combined.layers.keys())
# Contains None (X), 'normalized', and 'scaled' in AnnData 0.13.4
```

## Concatenating Multi-dimensional Annotations

### obsm/varm
```python
# Objects with embeddings
adata1.obsm['X_pca'] = np.random.rand(100, 50)
adata2.obsm['X_pca'] = np.random.rand(150, 50)

# obsm is concatenated along observation axis
adata_combined = ad.concat([adata1, adata2])
print(adata_combined.obsm['X_pca'].shape)  # (250, 50)
```

### obsp/varp (pairwise annotations)
```python
from scipy.sparse import csr_matrix

# Pairwise matrices
adata1.obsp['connectivities'] = csr_matrix((100, 100))
adata2.obsp['connectivities'] = csr_matrix((150, 15

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

