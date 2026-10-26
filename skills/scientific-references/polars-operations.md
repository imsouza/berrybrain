---
id: sciref-polars-operations
name: "Scientific Ref: Polars Operations Reference"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (polars): Polars Operations Reference"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "polars operations"
  - "polars operations reference"
keywords:
  - "polars"
  - "operations"
  - "specialized"
  - "scientific"
  - "reference"
---

# Polars Operations Reference

Polars 1.44.2 operation patterns. Fragments assume `import polars as pl` and a
DataFrame with the named columns; they are illustrative unless instantiated in the
local recipe tests described in [review.md](review.md).

## Selection Operations

### Select Columns

**Basic selection:**
```python
# Select specific columns
df.select("name", "age", "city")

# Using expressions
df.select(pl.col("name"), pl.col("age"))
```

**Pattern-based selection:**
```python
import polars.selectors as cs

# All columns starting with "sales_"
df.select(pl.col("^sales_.*$"))

# All numeric columns
df.select(cs.numeric())

# All columns except specific ones
df.select(pl.all().exclude("id", "timestamp"))
```

**Computed columns:**
```python
df.select(
    "name",
    (pl.col("age") * 12).alias("age_in_months"),
    (pl.col("salary") * 1.1).alias("salary_after_raise")
)
```

### With Columns (Add/Modify)

Add new columns or modify existing ones while preserving all other columns:

```python
# Add new columns
df.with_columns(
    age_doubled=pl.col("age") * 2,
    full_name=pl.col("first_name") + " " + pl.col("last_name")
)

# Modify existing columns
df.with_columns(
    pl.col("name").str.to_uppercase().alias("name"),
    pl.col("salary").cast(pl.Float64).alias("salary")
)

# Multiple operations in parallel need distinct output names.
df.with_columns(
    (pl.col("value") * 10).alias("value_times_10"),
    (pl.col("value") * 100).alias("value_times_100"),
    (pl.col("value") * 1000).alias("value_times_1000"),
)
```

## Filtering Operations

### Basic Filtering

```python
# Single condition
df.filter(pl.col("age") > 25)

# Multiple conditions (AND)
df.filter(
    pl.col("age") > 25,
    pl.col("city") == "NY"
)

# OR conditions
df.filter(
    (pl.col("age") > 30) | (pl.col("salary") > 100000)
)

# NOT condition
df.filter(~pl.col("active"))
df.filter(pl.col("city") != "NY")
```

### Advanced Filtering

**String operations:**
```python
# Contains substring
df.filter(pl.col("name").str.contains("John"))

# Starts with
df.filter(pl.col("email").str.starts_with("admin"))

# Regex match
df.filter(pl.col("phone").str.contains(r"^\d{3}-\d{3}-\d{4}$"))
```

**Membership checks:**
```python
# In list
df.filter(pl.col("city").is_in(["NY", "LA", "SF"]))

# Not in list
df.filter(~pl.col("status").is_in(["inactive", "deleted"]))
```

**Range filters:**
```python
# Between values
df.filter(pl.col("age").is_between(25, 35))

# Date range
df.filter(
    pl.col("date") >= pl.date(2023, 1, 1),
    pl.col("date") <= pl.date(2023, 12, 31)
)
```

**Null filtering:**
```python
# Filter out nulls
df.filter(pl.col("value").is_not_null())

# Keep only nulls
df.filter(pl.col("value").is_null())
```

## Grouping and Aggregation

### Basic Group By

```python
# Group by single column
df.group_by("department").agg(
    pl.col("salary").mean().alias("avg_salary"),
    pl.len().alias("employee_count")
)

# Group by multiple columns
df.group_by("department", "location").agg(
    pl.col("salary").sum()
)

# Maintain order
df.group_by("category", maintain_order=True).agg(
    pl.col("value").sum()
)
```

### Aggregation Functions

**Count and length:**
```python
df.group_by("category").agg(
    pl.len().alias("count"),
    pl.col("id").count().alias("non_null_count"),
    pl.col("id").n_unique().alias("unique_count")
)
```

**Statistical aggregations:**
```python
df.group_by("group").agg(
    pl.col("value").sum().alias("total"),
    pl.col("value").mean().alias("average"),
    pl.col("value").median().alias("median"),
    pl.col("value").std().alias("std_dev"),
    pl.col("value").var().alias("variance"),
    pl.col("value").min().alias("minimum"),
    pl.col("value").max().alias("maximum"),
    pl.col("value").quantile(0.95).alias("p95")
)
```

**First and last:**
```python
df.group_by("user_id").agg(
    pl.col("timestamp").first().alias("first_seen"),
    pl.col("timestamp").last().alias("last_seen"),
    pl.col("event").first().alias("first_event")
)
```

**List aggregation:**
```python
# Collect values into lists
df.group_by("category").agg(
    pl.col("item").alias("all_items")  # Creates list column
)
```

`count()` excludes nulls, whereas `pl.len()` includes them and `n_unique()` counts
null as one distinct value. NaN is a float value, not a null. `std`/`var` default to
`ddof=1`; `quantile` defaults to nearest interpolation. Declare those conventions.
`first`/`last` follow row order, not chronological extrema: sort first or use min/max.

### Conditional Aggregations

Filter within aggregations:

```python
df.group_by("department").agg(
    # Count high earners
    (pl.col("salary") > 100000).sum().alias("high_earners"),

    # Average of filtered values
    pl.col("salary").filter(pl.col("bonus") > 0).mean().alias("avg_with_bonus"),

    # Conditional sum
    pl.when(pl.col("active"))
      .then(pl.col("sales"))
      .otherwise(0)
      .sum()
      .alias("active_sales")
)
```

### Multiple Aggregations

Combine multiple aggregations efficiently:

```python
df.group_by("store_id").agg(
    pl.col("transaction_id").count().alias("num_transactions"),
    pl.col("amount").sum().alias("total_sales"),
    pl.col("amount").mean().alias("avg_transaction"),
    pl.col("customer_id").n_unique().alias("unique_customers"),
    pl.col("amount").max().alias("largest_transaction"),
    pl.col("timestamp").min().alias("first_transaction_date"),
    pl.col("timestamp").max().alias("last_transaction_date")
)
```

## Window Functions

Window functions apply aggregations while preserving the original row count.

### Basic Window Operations

**Group statistics:**
```python
# Add group mean to each row
df.with_columns(
    avg_age_by_dept=pl.col("age").mean().over("department")
)

# Multiple group columns
df.with_columns(
    group_avg=pl.col("value").mean().over("category", "region")
)
```

**Ranking:**
```python
df.with_columns(
    # Rank within groups
    rank=pl.col("score").rank().over("team"),

    # Dense rank (no gaps)
    dense_rank=pl.col("score").rank(method="dense").over("team"),

    # Row number
    row_num=pl.col("timestamp").rank(method="ordinal").over("user_id")
)
```

### Window Mapping Strategies

**group_to_rows (default):**
Preserves original row order:
```python
df.with_columns(
    group_mean=pl.col("value").mean().over("category", mapping_strategy="group_to_rows")
)
```

**explode:**
Produces one scalar mean per group here; use `select` because row count changes:
```python
df.select(
    gr

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

