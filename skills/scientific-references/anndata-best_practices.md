---
id: sciref-anndata-best-practices
name: "Scientific Ref: Best Practices"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (anndata): Best Practices"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "anndata best practices"
  - "best practices"
keywords:
  - "anndata"
  - "best"
  - "practices"
  - "specialized"
  - "scientific"
  - "reference"
---

# Best Practices

Guidelines reviewed for AnnData 0.13.4. User-file paths and application-specific `process`/`analyze` functions are illustrative. Small synthetic tests verify the data-structure and native-I/O contracts; they do not validate biological analysis.

## Memory Management

### Use sparse matrices for sparse data
```python
import numpy as np
from scipy.sparse import csr_matrix, csc_matrix
import anndata as ad

# Check data sparsity
data = np.random.rand(1000, 2000)
sparsity = 1 - np.count_nonzero(data) / data.size
print(f"Sparsity: {sparsity:.2%}")

# Convert to sparse if >50% zeros (anndata 0.12+ requires csr or csc)
if sparsity > 0.5:
    adata = ad.AnnData(X=csr_matrix(data))
else:
    adata = ad.AnnData(X=data)

# Measure actual memory: data.nbytes versus CSR data/indices/indptr.nbytes.
# Density, dtype, index width, and temporary arrays determine savings.
```

### Convert strings to categoricals
```python
# Inefficient: string columns use lots of memory
adata.obs['cell_type'] = ['Type_A', 'Type_B', 'Type_C'] * 333 + ['Type_A']

# Efficient: convert to categorical
adata.obs['cell_type'] = adata.obs['cell_type'].astype('category')

# Convert all string columns
adata.strings_to_categoricals()

# Check obs.memory_usage(deep=True); savings depend on category cardinality.
```

### Use backed mode for large datasets
```python
# Don't load entire dataset into memory
adata = ad.read_h5ad('large_dataset.h5ad', backed='r')

# Work with metadata
filtered = adata[adata.obs['quality'] > 0.8]

# Load only filtered subset
adata_subset = filtered.to_memory()

# Benefits: Work with datasets larger than RAM
```

## Views vs Copies

### Understanding views
```python
# Subsetting creates a view by default
subset = adata[0:100, :]
print(subset.is_view)  # True

# Views defer subset copies. In 0.13, .X also uses copy-on-write.
# Modification can allocate a full subset copy; make ownership explicit.

# Check if object is a view
if adata.is_view:
    adata = adata.copy()  # Make independent
```

### When to use views
```python
# Good: Read-only operations on subsets
mean_expr = adata[adata.obs['cell_type'] == 'T cell'].X.mean()

# Good: Temporary analysis
temp_subset = adata[:100, :]
result = analyze(temp_subset.X)
```

### When to use copies
```python
# Create independent copy for modifications
adata_filtered = adata[keep_cells, :].copy()

# Safe to modify without affecting original
adata_filtered.obs['new_column'] = values

# Always copy when:
# - Storing subset for later use
# - Modifying subset data
# - Passing to function that modifies data
```

## Data Storage Best Practices

### Choose the right format

**H5AD (HDF5) - Default choice**
```python
adata.write_h5ad('data.h5ad', compression='gzip')
```
- Fast random access
- Supports backed mode
- Good compression
- Best for: Most use cases

**Zarr - Cloud and parallel access**
```python
import anndata

# AnnData 0.13.4 defaults to Zarr v3 with automatic sharding.
adata.write_zarr('data.zarr', chunks=(100, 100))
```
- Excellent for cloud storage (S3, GCS)
- Supports parallel I/O and default Zarr v3 sharding in 0.13.4
- Good compression
- Best for: Large datasets, cloud workflows, parallel processing

**CSV - Interoperability**
```python
adata.write_csvs('output_dir/', skip_data=False)
```
- Human readable
- Interoperable tabular export; loses parts of AnnData and may densify X
- Large file sizes, slow
- Best for: Sharing with non-Python tools, small datasets

### Optimize file size
```python
# Before saving, optimize:

# 1. Convert to sparse if appropriate
from scipy.sparse import csr_matrix, issparse
if not issparse(adata.X):
    density = np.count_nonzero(adata.X) / adata.X.size
    if density < 0.5:
        adata.X = csr_matrix(adata.X)

# 2. Convert strings to categoricals
adata.strings_to_categoricals()

# 3. Use compression
adata.write_h5ad('data.h5ad', compression='gzip', compression_opts=9)

# Compare actual sizes and read/write times; there is no universal reduction factor.
```

## Backed Mode Strategies

### Read-only analysis
```python
# Open in read-only backed mode
adata = ad.read_h5ad('data.h5ad', backed='r')

# Perform filtering without loading data
high_quality = adata[adata.obs['quality_score'] > 0.8]

# Load only filtered data
adata_filtered = high_quality.to_memory()
```

### Read-write modifications
```python
# Open in read-write backed mode
adata = ad.read_h5ad('data.h5ad', backed='r+')

# Dense HDF5 X supports in-place writes; backed sparse X does not in 0.13.
import h5py
if isinstance(adata.X, h5py.Dataset):
    adata.X[0, 0] = 0

# Metadata changes are not persisted from backed mode; load and write a new file
adata_memory = adata.to_memory()
adata_memory.obs['new_annotation'] = values
adata.file.close()
adata_memory.write_h5ad('data_with_annotations.h5ad')
```

### Chunked processing
```python
# Process large dataset in chunks
adata = ad.read_h5ad('huge_dataset.h5ad', backed='r')

results = []
chunk_size = 1000

for i in range(0, adata.n_obs, chunk_size):
    chunk = adata[i:i+chunk_size, :].to_memory()
    result = process(chunk)
    results.append(result)

final_result = combine(results)
```

## Performance Optimization

### Subsetting performance
```python
# Boolean mask: clear and aligned to obs
mask = np.array(adata.obs['quality'] > 0.5)
subset = adata[mask, :]

# A boolean Series is also supported; it does not inherently create a view chain
subset = adata[adata.obs['quality'] > 0.5, :]

# Integer positions: useful when already available; benchmark actual workloads
indices = np.where(adata.obs['quality'] > 0.5)[0]
subset = adata[indices, :]
```

### Avoid repeated subsetting
```python
# Inefficient: Multiple subset operations
for cell_type in ['A', 'B', 'C']:
    subset = adata[adata.obs['cell_type'] == cell_type]
    process(subset)

# Alternative: reuse groups when several operations need the same grouping
groups = adata.obs.groupby('cell_type', observed=True).groups
for cell_type, indices in groups.items():
    subset = adata[indices, :]
    process(subset)
```

### Use chunked operations for large matrices
```python
# Process X in chunks
for chunk, start, stop in adata.chunked_X(chunk_size=1000):
    result = compute(chunk)

# More memory efficient than loading full X
```

## Working with Raw Data

### Store raw before filtering
```python
# Original data with all genes
adata = ad.AnnData(X=counts)

# Store raw before filtering
adata.raw = adata.copy()

# Filter to highly variable genes
adata = adata[:

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

