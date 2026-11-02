---
id: sciref-polars-transformations
name: "Scientific Ref: Polars Data Transformations"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (polars): Polars Data Transformations"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "polars transformations"
  - "polars data transformations"
keywords:
  - "polars"
  - "transformations"
  - "specialized"
  - "scientific"
  - "reference"
---

# Polars Data Transformations

Polars 1.44.2 patterns. Fragments require the named input columns; see
[review.md](review.md) for the bounded native checks and untested integrations.

## Joins

Joins combine data from multiple DataFrames based on common columns.

### Basic Join Types

**Inner Join (intersection):**
```python
# Keep only matching rows from both DataFrames
result = df1.join(df2, on="id", how="inner")
```

**Left Join (all left + matches from right):**
```python
# Keep all rows from left, add matching rows from right
result = df1.join(df2, on="id", how="left")
```

**Full Join (union):**
```python
# Keep all rows from both DataFrames
result = df1.join(df2, on="id", how="full")
```

**Cross Join (Cartesian product):**
```python
# Every row from left with every row from right
result = df1.join(df2, how="cross")
```

**Semi Join (filtered left):**
```python
# Keep only left rows that have a match in right
result = df1.join(df2, on="id", how="semi")
```

**Anti Join (non-matching left):**
```python
# Keep only left rows that DON'T have a match in right
result = df1.join(df2, on="id", how="anti")
```

### Join correctness

Default `validate="m:m"` does not check uniqueness. Use `validate="m:1"` for
a sample-to-metadata join or `"1:1"` for paired samples; duplicate keys otherwise
multiply observations. Audit unmatched keys with anti joins. The current docs
exclude validation from streaming support: validate keys independently before a
large streaming join, and test the selected engine.

Null keys do not match unless `nulls_equal=True` (formerly `join_nulls`). Full joins
retain both key columns by default; choose `coalesce=True` if merged keys are wanted.
Request `maintain_order="left"` or sort by explicit keys when order matters.

### Join Syntax Variations

**Single column join:**
```python
df1.join(df2, on="id")
```

**Multiple columns join:**
```python
df1.join(df2, on=["id", "date"])
```

**Different column names:**
```python
df1.join(df2, left_on="user_id", right_on="id")
```

**Multiple different columns:**
```python
df1.join(
    df2,
    left_on=["user_id", "date"],
    right_on=["id", "timestamp"]
)
```

### Suffix Handling

When both DataFrames have columns with the same name (other than join keys):

```python
# Add suffixes to distinguish columns
result = df1.join(df2, on="id", suffix="_right")

# Results in: value, value_right (if both had "value" column)
```

### Join Examples

**Example 1: Customer Orders**
```python
customers = pl.DataFrame({
    "customer_id": [1, 2, 3, 4],
    "name": ["Alice", "Bob", "Charlie", "David"]
})

orders = pl.DataFrame({
    "order_id": [101, 102, 103],
    "customer_id": [1, 2, 1],
    "amount": [100, 200, 150]
})

# Inner join - only customers with orders
result = customers.join(orders, on="customer_id", how="inner")

# Left join - all customers, even without orders
result = customers.join(orders, on="customer_id", how="left")
```

**Example 2: Time-series data**
```python
prices = pl.DataFrame({
    "date": ["2023-01-01", "2023-01-02", "2023-01-03"],
    "stock": ["AAPL", "AAPL", "AAPL"],
    "price": [150, 152, 151]
})

volumes = pl.DataFrame({
    "date": ["2023-01-01", "2023-01-02"],
    "stock": ["AAPL", "AAPL"],
    "volume": [1000000, 1100000]
})

result = prices.join(
    volumes,
    on=["date", "stock"],
    how="left"
)
```

### Asof Joins (Nearest Match)

For time-series data, join to nearest timestamp:

```python
# Join to nearest earlier timestamp
quotes = pl.DataFrame({
    "timestamp": [1.0, 2.0, 3.0, 4.0, 5.0],
    "stock": ["A", "A", "A", "A", "A"],
    "quote": [100, 101, 102, 103, 104]
})

trades = pl.DataFrame({
    "timestamp": [1.5, 3.5, 4.2],
    "stock": ["A", "A", "A"],
    "trade": [50, 75, 100]
})

result = trades.sort("stock", "timestamp").join_asof(
    quotes.sort("stock", "timestamp"),
    on="timestamp",
    by="stock",
    strategy="backward",  # or "forward", "nearest"
    tolerance=0.6,  # timestamp units; unmatched rows retain null quote
)
```

As-of keys must have matching dtypes and be sorted within each `by` group. Polars
cannot verify grouped sortedness automatically in every case. `nearest` may match
a future observation; choose direction and tolerance according to the study.

## Concatenation

Concatenation stacks DataFrames together.

### Vertical Concatenation (Stack Rows)

```python
df1 = pl.DataFrame({"a": [1, 2], "b": [3, 4]})
df2 = pl.DataFrame({"a": [5, 6], "b": [7, 8]})

# Stack rows
result = pl.concat([df1, df2], how="vertical")
# Result: 4 rows, same columns
```

**Handling mismatched schemas:**
```python
df1 = pl.DataFrame({"a": [1, 2], "b": [3, 4]})
df2 = pl.DataFrame({"a": [5, 6], "c": [7, 8]})

# Diagonal concat - fills missing columns with nulls
result = pl.concat([df1, df2], how="diagonal")
# Result: columns a, b, c (with nulls where not present)
```

### Horizontal Concatenation (Stack Columns)

```python
df1 = pl.DataFrame({"a": [1, 2, 3]})
df2 = pl.DataFrame({"b": [4, 5, 6]})

# Stack columns
result = pl.concat([df1, df2], how="horizontal_extend")
# Result: 3 rows, columns a and b
```

**Note:** Horizontal concat aligns by row position and pads shorter frames with nulls
with `how="horizontal_extend"`. In 1.44.2, `how="horizontal"` also pads but is
deprecated toward an equal-height contract; `strict` is transitional/deprecated.
Validate heights explicitly when needed; a keyed join is safer for sample alignment. `vertical` requires matching schemas; the `*_relaxed`
variants coerce to a common supertype, so inspect the result dtype.

#As-of keys must have matching dtypes and be sorted within each `by` group. Polars
cannot verify grouped sortedness automatically in every case. `nearest` may match
a future observation; choose direction and tolerance according to the study.

## Concatenation Options

```python
# Rechunk after concatenation (better performance for subsequent operations)
result = pl.concat([df1, df2], rechunk=True)

# Parallel subplans (applies to LazyFrames)
result = pl.concat([lf1, lf2], parallel=True)
```

### Use Cases

**Combining data from multiple sources:**
```python
# Read multiple files and concatenate
files = ["data_2023.csv", "data_2024.csv", "data_2025.csv"]
dfs = [pl.read_csv(f) for f in files]
combined = pl.concat(dfs, how="vertical")
```

**Adding computed columns:**
```python
base = pl.DataFrame({"value": [1, 2, 3]})
computed = pl.DataFrame({"doubled": [2, 4, 6]})
result = pl.concat([base, computed], how="horizontal_extend")
```

## Pivot

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

