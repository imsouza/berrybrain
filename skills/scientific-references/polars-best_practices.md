---
id: sciref-polars-best-practices
name: "Scientific Ref: Polars Best Practices and Performance Guide"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (polars): Polars Best Practices and Performance Guide"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "polars best practices"
  - "polars best practices and performance guide"
keywords:
  - "polars"
  - "best"
  - "practices"
  - "specialized"
  - "scientific"
  - "reference"
---

# Polars Best Practices and Performance Guide

Polars 1.44.2 patterns. Fragments use illustrative inputs; native regression coverage
and official sources are recorded in [review.md](review.md).

## Performance Optimization

### 1. Use Lazy Evaluation

**Always prefer lazy mode for large datasets:**

```python
# Bad: Eager mode loads everything immediately
df = pl.read_csv("large_file.csv")
result = df.filter(pl.col("age") > 25).select("name", "age")

# Good: Lazy mode optimizes before execution
lf = pl.scan_csv("large_file.csv")
result = lf.filter(pl.col("age") > 25).select("name", "age").collect()
```

**Benefits of lazy evaluation:**
- Predicate pushdown (filter at source)
- Projection pushdown (read only needed columns)
- Query optimization
- Parallel execution planning

### 2. Filter and Select Early

Let the optimizer push down predicates and projections where semantics permit.
The following query selects groups whose **mean** exceeds 100:

```python
# Filter the group means, preserving every observation within a selected group
result = (
    lf.group_by("category")
    .agg(pl.col("value").mean())
    .join(other, on="category")
    .filter(pl.col("value") > 100)
    .select("category", "value")
)

# Projection can move earlier while retaining all columns needed downstream.
result = (
    lf.select("category", "value")
    .group_by("category")
    .agg(pl.col("value").mean())
    .filter(pl.col("value") > 100)
    .join(other.select("category", "other_col"), on="category")
    .select("category", "value")
)
```
Filtering `value > 100` before the mean changes which observations contribute.
Likewise, moving filters across an outer join can change which rows survive.

### 3. Avoid Python Functions

Stay within the expression API to maintain parallelization:

```python
# Python element UDF adds overhead and can inhibit optimization
df = df.with_columns(
    result=pl.col("value").map_elements(lambda x: float(x) * 2, return_dtype=pl.Float64)
)

# Good: Use native expressions (parallelized)
df = df.with_columns(result=pl.col("value") * 2)
```

**When you must use custom functions:**
```python
# If truly needed, be explicit
df = df.with_columns(
    result=pl.col("value").map_elements(
        custom_function,
        return_dtype=pl.Float64,
        skip_nulls=True  # Optimize null handling
    )
)
```

### 4. Use Streaming for Very Large Data

Use streaming to reduce intermediate memory; it is not a memory cap.
`collect(engine="streaming")` still returns one in-memory DataFrame. High-cardinality
groups, joins, or unsupported operations may need large state or fall back to the
in-memory engine. Inspect the plan and measure actual peak RSS on representative data:

```python
# Streaming mode processes data in chunks
lf = pl.scan_parquet("very_large.parquet")
result = lf.filter(pl.col("value") > 100).collect(engine="streaming")

# Or use sink for direct streaming writes
lf.filter(pl.col("value") > 100).sink_parquet("output.parquet")
```

### 5. Optimize Data Types

Choose appropriate data types to reduce memory and improve performance:

```python
# Bad: Default types may be wasteful
df = pl.read_csv("data.csv")

# Good: Specify optimal types
df = pl.read_csv(
    "data.csv",
    schema_overrides={
        "id": pl.UInt32,  # Instead of Int64 if values fit
        "category": pl.Categorical,  # For low-cardinality strings
        "date": pl.Date,  # Instead of String
        "small_int": pl.Int16,  # Instead of Int64
    }
)
```

**Type optimization guidelines:**
- Use smallest integer type that fits your data
- Benchmark `Categorical` for repeated strings; use `Enum` for a fixed, ordered domain
- Use `Date` instead of `Datetime` when time isn't needed
- Use `Boolean` instead of integers for binary flags

### 6. Parallel Operations

Structure code to maximize parallelization:

```python
# Independent expressions share an input context.
df = df.with_columns(
    doubled=pl.col("value") * 2,
    squared=pl.col("value") ** 2,
)
# A dependent expression needs the new schema from the preceding context.
df = df.with_columns(plus_one=pl.col("doubled") + 1)
```

A `.pipe()` call simply invokes a Python helper. Helpers that return native
LazyFrame plans preserve optimization and parallel execution. A helper that
collects or loops over rows can lose those benefits. Eager chaining with and
without intermediate variable names has the same execution semantics.

### 7. Rechunk After Concatenation

```python
# Concatenation can fragment data
combined = pl.concat([df1, df2, df3])

# Rechunk for better performance in subsequent operations
combined = pl.concat([df1, df2, df3], rechunk=True)
```

## Expression Patterns

### Conditional Logic

**Simple conditions:**
```python
df.with_columns(
    status=pl.when(pl.col("age") >= 18)
        .then(pl.lit("adult"))
        .otherwise(pl.lit("minor"))
)
```

**Multiple conditions:**
```python
df.with_columns(
    grade=pl.when(pl.col("score") >= 90)
        .then(pl.lit("A"))
        .when(pl.col("score") >= 80)
        .then(pl.lit("B"))
        .when(pl.col("score") >= 70)
        .then(pl.lit("C"))
        .when(pl.col("score") >= 60)
        .then(pl.lit("D"))
        .otherwise(pl.lit("F"))
)
```

**Complex conditions:**
```python
df.with_columns(
    category=pl.when(
        (pl.col("revenue") > 1000000) & (pl.col("customers") > 100)
    )
    .then(pl.lit("enterprise"))
    .when(
        (pl.col("revenue") > 100000) | (pl.col("customers") > 50)
    )
    .then(pl.lit("business"))
    .otherwise(pl.lit("starter"))
)
```

### Null Handling

**Check for nulls:**
```python
df.filter(pl.col("value").is_null())
df.filter(pl.col("value").is_not_null())
```

**Fill nulls:**
```python
# Constant value
df.with_columns(pl.col("value").fill_null(0))

# Forward fill
df.with_columns(pl.col("value").fill_null(strategy="forward"))

# Backward fill
df.with_columns(pl.col("value").fill_null(strategy="backward"))

# Mean
df.with_columns(pl.col("value").fill_null(strategy="mean"))

# Per-group fill
df.with_columns(
    pl.col("value").fill_null(pl.col("value").mean()).over("group")
)
```

**Coalesce (first non-null):**
```python
df.with_columns(
    combined=pl.coalesce(["col1", "col2", "col3"])
)
```

### Column Selection Patterns

**By name:**
```python
df.select("col1", "col2", "col3")
```

**By pattern:**
```python
# Regex
df.select(pl.col("^sales_.*$"))

# Starts with
df.select(pl.col("^sales.*$"))

# Ends with
df.select(pl.col("^.*_total$"))

# Contains
df.se

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

