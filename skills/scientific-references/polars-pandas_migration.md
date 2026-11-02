---
id: sciref-polars-pandas-migration
name: "Scientific Ref: Pandas to Polars Migration Guide"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (polars): Pandas to Polars Migration Guide"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "polars pandas migration"
  - "pandas to polars migration guide"
keywords:
  - "polars"
  - "pandas"
  - "migration"
  - "specialized"
  - "scientific"
  - "reference"
---

# Pandas to Polars Migration Guide

Migration patterns reviewed with Polars 1.44.2 and pandas 3.0.6. Fragments require
matching input columns; see [review.md](review.md) for tested behavior and limits.

## Core Conceptual Differences

### 1. No Index System

**Pandas:** Uses row-based indexing system
```python
df.loc[0, "column"]
df.iloc[0:5]
df.set_index("id")
```

**Polars:** Uses integer positions only
```python
df[0, "column"]  # Row position, column name
df[0:5]  # Row slice
# Preserve former index labels as explicit columns; group_by is an aggregation
```

### 2. Memory Format

Both systems store data by column. pandas supports NumPy-backed and extension
arrays, including Arrow; Polars uses columnar typed buffers with Arrow interchange.
Performance, memory, and zero-copy behavior depend on types, chunking, and workload;
benchmark the actual conversion and query.

### 3. Parallelization

**Pandas:** Parallel behavior depends on the operation and backend
**Polars:** Parallel by default using Rust's concurrency

### 4. Lazy Evaluation

**Pandas:** Only eager evaluation
**Polars:** Both eager (DataFrame) and lazy (LazyFrame) with query optimization

### 5. Type Strictness

**Pandas:** Allows silent type conversions
**Polars:** Typed columns with inference and common-supertype coercion; validate dtypes

**Example:**
```python
# pandas may infer float here; nullable Int64/Arrow dtypes can preserve integers
pd_df["int_col"] = [1, 2, None, 4]  # dtype: float64

# Polars: Keeps as integer with null
pl_df = pl.DataFrame({"int_col": [1, 2, None, 4]})  # dtype: Int64
```

## Operation Mappings

### Data Selection

| Operation | Pandas | Polars |
|-----------|--------|--------|
| Select column | `df["col"]` or `df.col` | `df.select("col")` or `df["col"]` |
| Select multiple | `df[["a", "b"]]` | `df.select("a", "b")` |
| Select by position | `df.iloc[:, 0:3]` | `df.select(pl.col(df.columns[0:3]))` |
| Select by condition | `df[df["age"] > 25]` | `df.filter(pl.col("age") > 25)` |

### Data Filtering

| Operation | Pandas | Polars |
|-----------|--------|--------|
| Single condition | `df[df["age"] > 25]` | `df.filter(pl.col("age") > 25)` |
| Multiple conditions | `df[(df["age"] > 25) & (df["city"] == "NY")]` | `df.filter(pl.col("age") > 25, pl.col("city") == "NY")` |
| Query method | `df.query("age > 25")` | `df.filter(pl.col("age") > 25)` |
| isin | `df[df["city"].isin(["NY", "LA"])]` | `df.filter(pl.col("city").is_in(["NY", "LA"]))` |
| isna (float) | `df[df["value"].isna()]` | `df.filter(pl.col("value").is_null() | pl.col("value").is_nan())` |
| notna (float) | `df[df["value"].notna()]` | `df.filter(pl.col("value").is_not_null() & pl.col("value").is_not_nan())` |

### Adding/Modifying Columns

| Operation | Pandas | Polars |
|-----------|--------|--------|
| Add column | `df["new"] = df["old"] * 2` | `df.with_columns(new=pl.col("old") * 2)` |
| Multiple columns | `df.assign(a=..., b=...)` | `df.with_columns(a=..., b=...)` |
| Conditional column | `np.where(condition, a, b)` | `pl.when(condition).then(a).otherwise(b)` |

**Important difference - Parallel execution:**

```python
# Pandas: Sequential (lambda sees previous results)
df.assign(
    a=lambda df_: df_.value * 10,
    b=lambda df_: df_.value * 100
)

# Polars: Parallel (all computed together)
df.with_columns(
    a=pl.col("value") * 10,
    b=pl.col("value") * 100
)
```

### Grouping and Aggregation

| Operation | Pandas | Polars |
|-----------|--------|--------|
| Group by | `df.groupby("col")` | `df.group_by("col")` |
| Agg single | `df.groupby("col")["val"].mean()` | `df.group_by("col").agg(pl.col("val").mean())` |
| Agg multiple | `df.groupby("col").agg({"val": ["mean", "sum"]})` | `df.group_by("col").agg(pl.col("val").mean().alias("mean"), pl.col("val").sum().alias("sum"))` |
| Size | `df.groupby("col").size()` | `df.group_by("col").agg(pl.len())` |
| Count | `df.groupby("col").count()` | `df.group_by("col").agg(pl.exclude("col").count())` |

### Window Functions

| Operation | Pandas | Polars |
|-----------|--------|--------|
| Transform | `df.groupby("col").transform("mean")` | `df.with_columns(pl.col("val").mean().over("col"))` |
| Rank | `df.groupby("col")["val"].rank()` | `df.with_columns(pl.col("val").rank().over("col"))` |
| Shift | `df.groupby("col")["val"].shift(1)` | `df.with_columns(pl.col("val").shift(1).over("col"))` |
| Cumsum | `df.groupby("col")["val"].cumsum()` | `df.with_columns(pl.col("val").cum_sum().over("col"))` |

### Joins

| Operation | Pandas | Polars |
|-----------|--------|--------|
| Inner join | `df1.merge(df2, on="id")` | `df1.join(df2, on="id", how="inner")` |
| Left join | `df1.merge(df2, on="id", how="left")` | `df1.join(df2, on="id", how="left")` |
| Different keys | `df1.merge(df2, left_on="a", right_on="b")` | `df1.join(df2, left_on="a", right_on="b")` |

### Concatenation

| Operation | Pandas | Polars |
|-----------|--------|--------|
| Vertical | `pd.concat([df1, df2], axis=0)` | `pl.concat([df1, df2], how="vertical")` |
| Horizontal | `pd.concat([df1, df2], axis=1)` | `pl.concat([df1, df2], how="horizontal_extend")` |

### Sorting

| Operation | Pandas | Polars |
|-----------|--------|--------|
| Sort by column | `df.sort_values("col")` | `df.sort("col")` |
| Descending | `df.sort_values("col", ascending=False)` | `df.sort("col", descending=True)` |
| Multiple columns | `df.sort_values(["a", "b"])` | `df.sort("a", "b")` |

### Reshaping

| Operation | Pandas | Polars |
|-----------|--------|--------|
| Pivot | `df.pivot(index="a", columns="b", values="c")` | `df.pivot(on="b", values="c", index="a")` |
| Melt | `df.melt(id_vars="id")` | `df.unpivot(index="id")` |

### I/O Operations

| Operation | Pandas | Polars |
|-----------|--------|--------|
| Read CSV | `pd.read_csv("file.csv")` | `pl.read_csv("file.csv")` or `pl.scan_csv("file.csv")` |
| Write CSV | `df.to_csv("file.csv")` | `df.write_csv("file.csv")` |
| Read Parquet | `pd.read_parquet("file.parquet")` | `pl.read_parquet("file.parquet")` |
| Write Parquet | `df.to_parquet("file.parquet")` | `df.write_parquet("file.parquet")` |
| Read Excel | `pd.read_excel("file.xlsx")` | `pl.read_excel("file.xlsx")` |

### String Operations

| Operation | Pandas | Polars |
|-----------|--------|--------|
| Upper | `df["col"].str.upper()` | `df.select(pl.col("col").str.to_uppercase())` |
| Lower | `df["col"].str.lower()` | `df.select(pl.col("col").str.to_lowercase())` |
| Contains | `df["col"].str.contains("pattern")` | `df.filter(pl.col("c

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

