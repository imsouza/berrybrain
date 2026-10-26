---
id: sciref-anndata-io-operations
name: "Scientific Ref: Input/Output Operations"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (anndata): Input/Output Operations"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "anndata operations"
  - "input/output operations"
keywords:
  - "anndata"
  - "operations"
  - "specialized"
  - "scientific"
  - "reference"
---

# Input/Output Operations

Reviewed against AnnData 0.13.4. Native H5AD/Zarr and small text/Excel fixtures were exercised; remote stores and 10X biological inputs below are illustrative. Preserve identifiers, matrix units, transformations, and source checksums through conversion.

Since anndata 0.11, most `read_*` and `write_*` functions live in `anndata.io`. Top-level `read_h5ad` and `read_zarr` remain supported; use `anndata.io` for other readers rather than compatibility aliases.

```python
import anndata as ad
from anndata.io import read_csv, read_mtx, read_loom, read_elem, write_elem
```

Avoid deprecated I/O aliases such as `ad.read`; use `ad.read_h5ad` or `anndata.io.read_h5ad` explicitly.

## Native Formats

### H5AD (HDF5-based)
The recommended native format for AnnData objects, providing efficient storage and fast access.

#### Writing H5AD files
```python
import anndata as ad

# Write to file
adata.write_h5ad('data.h5ad')

# Write with compression
adata.write_h5ad('data.h5ad', compression='gzip')

# Write with specific compression level (0-9, higher = more compression)
adata.write_h5ad('data.h5ad', compression='gzip', compression_opts=9)
```

#### Reading H5AD files
```python
# Read entire file into memory
adata = ad.read_h5ad('data.h5ad')

# Read in backed mode (lazy loading for large files)
adata = ad.read_h5ad('data.h5ad', backed='r')  # Read-only
adata.file.close()
# Alternatively (do not leave a read-only handle open on this file):
adata = ad.read_h5ad('data.h5ad', backed='r+')  # In-place dense X updates only
adata.file.close()

# Backed mode keeps X on disk; obs/var and named layers can still load into RAM.
# 0.13 removed backed sparse item assignment, even with r+.
# Write a new file for obs/var/uns or sparse-X changes.
```

#### Backed mode operations
```python
# Open in backed mode
adata = ad.read_h5ad('large_dataset.h5ad', backed='r')

# Access metadata without loading X into memory
print(adata.obs.head())
print(adata.var.head())

# Subset operations create views
subset = adata[:100, :500]  # View, no data loaded

# Load specific data into memory
X_subset = subset.X[:]  # Now loads this subset

# Convert entire backed object to memory
adata_memory = adata.to_memory()
adata.file.close()
```

### Zarr

`read_zarr` is eager; use experimental `read_lazy` for lazy arrays and annotations.
AnnData 0.13 requires the Zarr >=3 Python package and writes sharded Zarr format 3
by default. Format 2 stores can still be read. Chunk shape and shard size have
different effects; benchmark representative row/column access instead of assuming
a universal setting.

#### Writing Zarr
```python
# Write to Zarr store
adata.write_zarr('data.zarr')

# Write with specific chunks (important for performance)
adata.write_zarr('data.zarr', chunks=(100, 100))
```

#### Reading Zarr
```python
# Read Zarr store
adata = ad.read_zarr('data.zarr')
```

#### Zarr v3 defaults (AnnData 0.13.4)
```python
adata.write_zarr('data.zarr', chunks=(1000, 1000), consolidate_metadata=True)
```

The deprecated `settings.zarr_write_format` is scheduled for removal in 0.14.
If a downstream reader requires format 2, verify that compatibility separately;
do not confuse the Zarr package version with the storage format.

#### Remote Zarr access
Use the requested dataset location, with its provider credentials and suitable fsspec adapter (`s3fs` for S3, `gcsfs` for GCS). The following placeholder stores are illustrative and were not contacted. These examples use Zarr 3 `FsspecStore`; credentials should come from provider configuration, not source code.

```python
from zarr.storage import FsspecStore
from anndata.experimental import read_lazy

store = FsspecStore.from_url('s3://bucket-name/data.zarr', read_only=True)
adata = read_lazy(store)  # Verify provider/store support on a small slice first
```

## Alternative Input Formats

### CSV/TSV
```python
from anndata.io import read_csv

# Read CSV (genes as columns, cells as rows)
adata = read_csv('data.csv')

# Read with custom delimiter
adata = read_csv('data.tsv', delimiter='\t')

# Specify that first column is row names
adata = read_csv('data.csv', first_column_names=True)
```

### Excel

Requires `openpyxl` for `.xlsx`; first column supplies row names and first row supplies feature names. Validate numeric matrix dtype after importing.
```python
from anndata.io import read_excel

# Read Excel file
adata = read_excel('data.xlsx', sheet=0)  # sheet is required

# Read specific sheet
adata = read_excel('data.xlsx', sheet='Sheet1')
```

### Matrix Market (MTX)
Common format for sparse matrices in genomics.

```python
from anndata.io import read_mtx

import pandas as pd

# read_mtx reads ONLY the matrix; it has no obs_names/var_names arguments.
# For this explicit feature-by-cell input, transpose to cells by features.
adata = read_mtx('matrix.mtx').T
features = pd.read_csv('features.tsv', sep='\t', header=None, dtype=str)
barcodes = pd.read_csv('barcodes.tsv', sep='\t', header=None, dtype=str)
assert adata.shape == (len(barcodes), len(features))
adata.obs_names = barcodes[0].to_numpy()
adata.var_names = features[0].to_numpy()  # Stable IDs; keep symbols separately
adata.var['gene_symbol'] = features[1].to_numpy()
assert adata.obs_names.is_unique and adata.var_names.is_unique
```

### 10X Genomics formats
10X readers are provided by **scanpy**, not anndata. After loading, the result is a standard `AnnData` object.

```python
import scanpy as sc

# Read 10X h5 format
adata = sc.read_10x_h5('filtered_feature_bc_matrix.h5')

# Read 10X MTX directory
adata = sc.read_10x_mtx('filtered_feature_bc_matrix/')

# Specify genome if multiple present
adata = sc.read_10x_h5('data.h5', genome='GRCh38')
```

### Loom input

Requires `loompy`; `read_loom` is deprecated in 0.13 (legacy import still passed
a synthetic test with loompy 3.0.8). Use the actual source layer and annotation names; defaults
`CellID`/`Gene` do not match every Loom file. The format is lossy relative to
AnnData (for example, it is not a full `uns`/`raw` archive).

```python
from anndata.io import read_loom

# Read Loom file
adata = read_loom('data.loom')

# Read with specific observation and variable annotations
adata = read_loom(
    'data.loom',
    obs_names='CellID',
    var_names='Gene'
)
```

### Text files
```python
from anndata.io import read_text

# Read generic text file
adata = read_text('data.txt', delimiter='\t')

# Read with custom parameters
adata = read_text(
    'data.txt',
    delimiter=',',
    

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

