---
id: sciref-dask-dataframes
name: "Scientific Ref: Dask DataFrames"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (dask): Dask DataFrames"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "dask dataframes"
keywords:
  - "dask"
  - "dataframes"
  - "specialized"
  - "scientific"
  - "reference"
---

# Dask DataFrames

Reviewed with Dask/distributed 2026.8.0. File paths, deployment settings, and undefined application functions are illustrative; executed local checks and current official sources are in [review.md](review.md).

## Overview

Dask DataFrames enable parallel processing of large tabular data by distributing work across multiple pandas DataFrames. As described in the documentation, "Dask DataFrames are a collection of many pandas DataFrames" with a supported subset of the pandas API; global operations can require shuffles or be unavailable.

Since **dask 2025.1.0**, the expression-based implementation with logical query planning is the only DataFrame backend. Import from `dask.dataframe` only — avoid legacy submodule paths. DataFrame I/O requires **PyArrow 16+** (dask 2026.1.2+).

## Core Concept

A Dask DataFrame is divided into multiple pandas DataFrames (partitions) along the index:
- Each partition is a regular pandas DataFrame
- Operations are applied to each partition in parallel
- Results are combined automatically

## Key Capabilities

### Scale
- Capacity is workload-dependent; budget partition, shuffle, and result memory
- Handle datasets exceeding available RAM

### Compatibility
- Implements most of the pandas API
- Easy transition from pandas code
- Works with familiar operations

## When to Use Dask DataFrames

**Use Dask When**:
- Dataset exceeds available RAM
- Computations require significant time and pandas optimization hasn't helped
- Need to scale from prototype (pandas) to production (larger data)
- Working with multiple files that should be processed together

**Stick with Pandas When**:
- Data fits comfortably in memory
- Computations complete in subseconds
- Simple operations without custom `.apply()` functions
- Iterative development and exploration

## Reading Data

Dask mirrors pandas reading syntax with added support for multiple files:

### Single File
```python
import dask.dataframe as dd

# Read single file
ddf = dd.read_csv('data.csv')
ddf = dd.read_parquet('data.parquet')
```

### Multiple Files
```python
# Read multiple files using glob patterns
ddf = dd.read_csv('data/*.csv')
ddf = dd.read_parquet('data/year=*/month=*/day=*.parquet')

# Remote Parquet (requires s3fs: uv pip install s3fs)
ddf = dd.read_parquet('s3://mybucket/data/*.parquet', storage_options={'anon': False})
```

### Optimizations
```python
# Specify columns to read (reduces memory)
ddf = dd.read_parquet('data.parquet', columns=['col1', 'col2'])

# Control partitioning
ddf = dd.read_csv('data.csv', blocksize='64MB')  # About 64 MB of source bytes, not in-memory pandas size
```

## Common Operations

Most transformations build lazy graphs. Reads may sample metadata; `head`, index-division discovery, `persist`, and writes can also execute work.

### Filtering
```python
# Same as pandas
filtered = ddf[ddf['column'] > 100]
filtered = ddf.query('column > 100')
```

### Column Operations
```python
# Add columns
ddf['new_column'] = ddf['col1'] + ddf['col2']

# Select columns
subset = ddf[['col1', 'col2', 'col3']]

# Drop columns
ddf = ddf.drop(columns=['unnecessary_col'])
```

### Aggregations
```python
# Standard aggregations work as expected
mean = ddf['column'].mean().compute()
sum_total = ddf['column'].sum().compute()
counts = ddf['category'].value_counts().compute()
```

### GroupBy
```python
# GroupBy operations (may require shuffle)
grouped = ddf.groupby('category')['value'].mean().compute()

# Multiple aggregations
agg_result = ddf.groupby('category').agg({
    'value': ['mean', 'sum', 'count'],
    'amount': 'sum'
}).compute()
```

### Joins and Merges
```python
# Merge DataFrames
merged = dd.merge(ddf1, ddf2, on='key', how='left')

# Join on index
joined = ddf1.join(ddf2, on='key')
```

### Sorting
```python
# Sorting (expensive operation, requires data movement)
sorted_ddf = ddf.sort_values('column')
result = sorted_ddf.compute()
```

## Custom Operations

### Apply Functions

**To Partitions (Efficient)**:
```python
# Apply function to entire partitions
def custom_partition_function(partition_df):
    # partition_df is a pandas DataFrame
    return partition_df.assign(new_col=partition_df['col1'] * 2)

ddf = ddf.map_partitions(custom_partition_function)
```

**To Rows (Less Efficient)**:
```python
# Python row calls execute within each partition; prefer vectorized operations
ddf['result'] = ddf.apply(lambda row: custom_function(row), axis=1, meta=('result', 'float'))
```

**Note**: Use vectorized pandas code inside `map_partitions` when possible. Merely moving the same row loop into a partition function does not remove its Python overhead.

### Meta Parameter

When Dask can't infer output structure, specify the `meta` parameter:
```python
# For apply operations
ddf['new'] = ddf.apply(func, axis=1, meta=('new', 'float64'))

# For map_partitions
import pandas as pd
ddf = ddf.map_partitions(func, meta=pd.DataFrame({
    'col1': pd.Series(dtype='float64'),
    'col2': pd.Series(dtype='int64')
}))
```

## Lazy Evaluation and Computation

### Lazy Operations
```python
# These operations are lazy (instant, no computation)
filtered = ddf[ddf['value'] > 100]
aggregated = filtered.groupby('category')[['value']].mean()
final = aggregated[aggregated['value'] < 500]

# Nothing has computed yet
```

### Triggering Computation
```python
# Compute single result
result = final.compute()

# Compute multiple results efficiently
result1, result2, result3 = dask.compute(
    operation1,
    operation2,
    operation3
)
```

### Persist in Memory

Persist only a reusable intermediate that fits worker memory, after projection/filtering. It blocks downstream optimizer pushdown through that boundary.
```python
# Keep results in distributed memory for reuse
ddf_cached = ddf.persist()

# Now multiple operations on ddf_cached won't recompute
result1 = ddf_cached['value'].mean().compute()
result2 = ddf_cached['value'].sum().compute()
```

## Index Management

### Setting Index
```python
# Shuffle unsorted input into sorted index partitions
ddf = ddf.set_index('timestamp')
# sorted=True asserts the column is ALREADY globally sorted across partitions.
# It does not sort input. Use it only after verifying ordering and divisions.
```

### Index Properties
- Sorted index enables efficient filtering and joins
- Index determines partitioning
- Some operations perform better with appropriate index

## Writing Results

### To Files
```python
# Write to multiple files (one per partition)
ddf.to_par

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

