---
id: sci-dask
name: "Scientific: dask"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Scales pandas, NumPy, and custom Python research workflows beyond memory or across clusters with Dask. Covers DataFrames, Arrays, Bags, Futures, chunking, schedulers, and distributed diagnostics. Use for partitioned file processing, scientific array computation, or parallel tasks"
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "dask"
keywords:
  - "dask"
  - "scales"
  - "pandas"
  - "numpy"
  - "custom"
  - "python"
  - "research"
---

# Dask

## Overview

Dask is a Python library for parallel and distributed computing that enables three critical capabilities:
- **Larger-than-memory execution** on single machines for data exceeding available RAM
- **Parallel processing** for improved computational speed across multiple cores
- **Distributed computation** supporting terabyte-scale datasets across multiple machines

Capacity depends on partition sizes, intermediate data, concurrency, storage, and available memory.

**Reviewed release:** dask/distributed **2026.8.0** (September 30, 2026 review). Docs: [docs.dask.org](https://docs.dask.org/en/stable/). Since **2025.1.0**, the expression-based DataFrame API with query planning is the only implementation — do not install `dask-expr` separately or set `dataframe.query-planning: False`.

## Quick Start

### Installation

```bash
uv pip install "dask[array,dataframe]==2026.8.0"
```

For a typical pandas/NumPy workflow with the distributed scheduler and dashboard:

```bash
uv pip install "dask[complete]==2026.8.0"
```

Remote object storage (requires provider credentials for private data):

```bash
uv pip install s3fs    # s3:// paths
uv pip install gcsfs   # gs:// paths
```

Requires **Python 3.10+**, pandas 2+, PyArrow 16+. Zarr, HDF5, SciPy, Xarray, Dask-ML, and cluster deployment packages are separate optional dependencies. See [review and validation](references/review.md) for tested versions, source links, and limits. File paths and undefined application functions below are illustrative. Put process scheduler/`Client()` execution in a `main()` guarded by `if __name__ == "__main__":` in scripts; close clients and clusters afterward.

## When to Use This Skill

This skill should be used when:
- Process datasets that exceed available RAM
- Scale pandas or NumPy operations to larger datasets
- Parallelize computations for performance improvements
- Process multiple files efficiently (CSVs, Parquet, JSON, text logs)
- Build custom parallel workflows with task dependencies
- Distribute workloads across multiple cores or machines

## Core Capabilities

Dask provides five main components, each suited to different use cases:

### 1. DataFrames - Parallel Pandas Operations

**Purpose**: Scale pandas operations to larger datasets through parallel processing.

**When to Use**:
- Tabular data exceeds available RAM
- Need to process multiple CSV/Parquet files together
- Pandas operations are slow and need parallelization
- Scaling from pandas prototype to production

**Reference Documentation**: For comprehensive guidance on Dask DataFrames, refer to `references/dataframes.md` which includes:
- Reading data (single files, multiple files, glob patterns)
- Common operations (filtering, groupby, joins, aggregations)
- Custom operations with `map_partitions`
- Performance optimization tips
- Common patterns (ETL, time series, multi-file processing)

**Quick Example**:
```python
import dask.dataframe as dd

# Read multiple files as single DataFrame
ddf = dd.read_csv('data/2024-*.csv')

# Operations are lazy until compute()
filtered = ddf[ddf['value'] > 100]
result = filtered.groupby('category')['value'].mean().compute()
```

**Key Points**:
- Operations are lazy (build task graph) until `.compute()` called
- Use `map_partitions` for efficient custom operations
- Convert to DataFrame early when working with structured data from other sources

### 2. Arrays - Parallel NumPy Operations

**Purpose**: Extend NumPy capabilities to datasets larger than memory using blocked algorithms.

**When to Use**:
- Arrays exceed available RAM
- NumPy operations need parallelization
- Working with scientific datasets (HDF5, Zarr, NetCDF)
- Need parallel linear algebra or array operations

**Reference Documentation**: For comprehensive guidance on Dask Arrays, refer to `references/arrays.md` which includes:
- Creating arrays (from NumPy, random, from disk)
- Chunking strategies and optimization
- Common operations (arithmetic, reductions, linear algebra)
- Custom operations with `map_blocks`
- Integration with HDF5, Zarr, and XArray

**Quick Example**:
```python
import dask.array as da

# Small executable example; size chunks from uncompressed memory before scaling
x = da.random.default_rng(42).random((1000, 1000), chunks=(250, 250))

# Operations are lazy
y = x + 100
z = y.mean(axis=0)

# Compute result
result = z.compute()
```

**Key Points**:
- Chunk size is critical (aim for ~100 MiB per chunk, adjusted to memory and operation)
- Operations work on chunks in parallel
- Rechunk data when needed for efficient operations
- Use `map_blocks` for operations not available in Dask

### 3. Bags - Parallel Processing of Unstructured Data

**Purpose**: Process unstructured or semi-structured data (text, JSON, logs) with functional operations.

**When to Use**:
- Processing text files, logs, or JSON records
- Data cleaning and ETL before structured analysis
- Working with Python objects that don't fit array/dataframe formats
- Need memory-efficient streaming processing

**Reference Documentation**: For comprehensive guidance on Dask Bags, refer to `references/bags.md` which includes:
- Reading text and JSON files
- Functional operations (map, filter, fold, groupby)
- Converting to DataFrames
- Common patterns (log analysis, JSON processing, text processing)
- Performance considerations

**Quick Example**:
```python
import dask.bag as db
import json

# Read and parse JSON files
bag = db.read_text('logs/*.json').map(json.loads)

# Filter and transform
valid = bag.filter(lambda x: x['status'] == 'valid')
processed = valid.map(lambda x: {'id': x['id'], 'value': x['value']})

# Convert to DataFrame for analysis
ddf = processed.to_dataframe(meta={'id': 'int64', 'value': 'float64'})
```

**Key Points**:
- Use for initial data cleaning, then convert to DataFrame/Array
- Use `foldby` instead of `groupby` for better performance
- Operations are streaming and memory-efficient
- Convert to structured formats (DataFrame) for complex operations

### 4. Futures - Task-Based Parallelization

**Purpose**: Build custom parallel workflows with fine-grained control over task execution and dependencies.

**When to Use**:
- Building dynamic, evolving workflows
- Need immediate task execution (not lazy)
- Computations depend on runtime conditions
- Implementing custom parallel algorithms
- Need stateful computations

**Reference Documentation**: For comprehensive guidance on Dask Futures, refer to `references/futures.md` which inclu

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

