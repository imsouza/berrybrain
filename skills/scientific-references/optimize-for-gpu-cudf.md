---
id: sciref-optimize-for-gpu-cudf
name: "Scientific Ref: cuDF Reference"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (optimize-for-gpu): cuDF Reference"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "optimize gpu cudf"
  - "cudf reference"
keywords:
  - "optimize"
  - "gpu"
  - "cudf"
  - "specialized"
  - "scientific"
  - "reference"
---

# cuDF Reference

> Review: 2026-10-01. Code below is illustrative unless explicitly described as CPU-tested.
> GPU execution, performance, GDS, and multi-GPU behavior require validation on target hardware.

cuDF is a GPU DataFrame library that provides a pandas-like API for loading, joining, aggregating, filtering, and manipulating tabular data entirely on the GPU. It's part of the NVIDIA RAPIDS ecosystem and is built on the Apache Arrow columnar memory format.

> **Full documentation:** https://docs.nvidia.com/cudf/26.08/

## Table of Contents

1. [Installation and Setup](#installation-and-setup)
2. [Two Usage Modes](#two-usage-modes)
3. [cudf.pandas Accelerator Mode](#cudfpandas-accelerator-mode)
4. [Core API: DataFrame and Series](#core-api)
5. [IO Operations](#io-operations)
6. [GroupBy Operations](#groupby-operations)
7. [String Operations](#string-operations)
8. [User Defined Functions (UDFs)](#user-defined-functions)
9. [Missing Data Handling](#missing-data-handling)
10. [Data Types](#data-types)
11. [Memory Management](#memory-management)
12. [Interoperability](#interoperability)
13. [Multi-GPU with Dask-cuDF](#multi-gpu-with-dask-cudf)
14. [Performance Optimization](#performance-optimization)
15. [Key Differences from pandas](#key-differences-from-pandas)
16. [Common Migration Patterns](#common-migration-patterns)

---

## Installation and Setup

Use `uv add` in standalone examples; follow the user's existing project package manager when one
is already configured.

```bash
uv add "cudf-cu12==26.8.*"    # For CUDA 12.x
uv add "cudf-cu13==26.8.*"    # For CUDA 13.x
```

cuDF wheels are now published directly to PyPI — the `--extra-index-url=https://pypi.nvidia.com` extra index is no longer required. Requires Python 3.11-3.14; 26.08 targets pandas 3, CuPy 14, and NumPy 2.

Verify:
```python
import cudf
print(cudf.Series([1, 2, 3]))  # Should print a GPU series
```

---

## Two Usage Modes

cuDF offers two ways to accelerate pandas code:

### 1. cudf.pandas (Zero-Code-Change)
Drop-in replacement that automatically accelerates pandas. Falls back to CPU for unsupported operations. Best for: quick acceleration of existing code, mixed codebases, prototyping.

### 2. Direct cuDF API
Replace `import pandas` with `import cudf`. Maximum performance, no proxy overhead, but requires adapting code to cuDF's API (which has some behavioral differences from pandas). Best for: production pipelines, maximum performance, new GPU-first code.

---

## cudf.pandas Accelerator Mode

The fastest path from pandas to GPU — no code changes required.

### Activation

```python
# Jupyter/IPython (MUST be before any pandas import)
%load_ext cudf.pandas
import pandas as pd  # Now GPU-accelerated

# Command line
# python -m cudf.pandas your_script.py
# python -m cudf.pandas --profile your_script.py  # With profiling

# Programmatic
import cudf.pandas
cudf.pandas.install()
import pandas as pd  # Now GPU-accelerated
```

**Critical:** If pandas was already imported in the session, you must restart the kernel/process.

### How It Works

- `import pandas` returns a proxy module that wraps cuDF and pandas.
- Every operation is first attempted on GPU (cuDF). If it fails, it automatically falls back to CPU (pandas).
- Data transfers between GPU and CPU happen only when necessary.
- Uses managed memory by default — can process datasets larger than GPU memory.
- Validate the exact workload; aggregate upstream test pass rates do not establish API equivalence.

### Profiling GPU vs CPU Execution

```python
%%cudf.pandas.profile        # Shows GPU vs CPU operation breakdown per cell
%%cudf.pandas.line_profile   # Per-line GPU/CPU timing
```

### Accessing Underlying Objects

```python
proxy_df.as_gpu_object()  # Get the cuDF DataFrame directly
proxy_df.as_cpu_object()  # Get the pandas DataFrame directly
```

Note: automatic fallback stops working after you extract the underlying object.

### Compatible Third-Party Libraries
cuGraph, cuML, Hvplot, Holoview, Ibis, NumPy, Matplotlib, Plotly, PyTorch, Seaborn, Scikit-Learn, SciPy, TensorFlow, XGBoost.

**Not compatible:** Joblib. For distributed work, use Dask-cuDF instead.

### Limitations

- Join operations don't guarantee pandas' row ordering (for performance).
- Cannot use `import cudf` alongside cudf.pandas in the same session.
- Pickled objects are not interchangeable between regular pandas and cudf.pandas.
- Proxy arrays subclass `numpy.ndarray`, which can cause eager device-to-host transfers.
- To force CPU-only: set `CUDF_PANDAS_FALLBACK_MODE=1`.

---

## Core API

### Creating DataFrames and Series

```python
import cudf

# From dict
df = cudf.DataFrame({"a": [1, 2, 3], "b": [4.0, 5.0, 6.0], "c": ["x", "y", "z"]})

# From pandas
import pandas as pd
gdf = cudf.DataFrame.from_pandas(pd.DataFrame({"a": [1, 2, 3]}))
# or
gdf = cudf.DataFrame(pandas_df)

# Series
s = cudf.Series([1, 2, 3, None, 5])

# Back to pandas
pdf = gdf.to_pandas()
```

### Common Operations (Same as pandas)

```python
df.head(10)
df.tail(5)
df.describe()
df.info()
df.dtypes
df.columns
df.shape

# Selection
df["a"]                     # Column → Series
df[["a", "b"]]             # Multiple columns → DataFrame
df.loc[2:5, ["a", "b"]]   # Label-based indexing
df.iloc[0:3]               # Integer-based indexing

# Filtering
df[df["a"] > 2]
df.query("a > 2 and b < 6")  # Supports @var for local variables

# Sorting
df.sort_values("a", ascending=False)
df.sort_index()

# Missing data
df.fillna(0)
df.dropna()
df.isna()

# Aggregations
df["a"].sum()
df["a"].mean()
df["a"].std()
df["a"].value_counts()

# Transforms
df["a"].clip(lower=1, upper=5)
df["a"].apply(lambda x: x * 2)  # JIT-compiled

# Combining
cudf.concat([df1, df2])
df1.merge(df2, on="key")
df1.merge(df2, on="key", how="left")  # left, right, inner, outer

# Arrow interop (host/device transfer boundary)
arrow_table = df.to_arrow()
df = cudf.DataFrame.from_arrow(arrow_table)
```

---

## IO Operations

GPU-accelerated file reading and writing — often dramatically faster than pandas for large files.

### Parquet (Recommended for Performance)

```python
# Read
df = cudf.read_parquet("data.parquet")
df = cudf.read_parquet("data.parquet", columns=["a", "b"])  # Read only specific columns

# Write
df.to_parquet("output.parquet")

# Metadata inspection (without loading data)
cudf.io.parquet.read_parquet_metadata("data.parquet")

# Incremental writing
writer = cudf.io.parquet.ParquetDatasetWriter("output_dir/", partition_cols=["year"])
writer

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

