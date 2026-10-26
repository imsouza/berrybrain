---
id: sciref-polars-core-concepts
name: "Scientific Ref: Polars Core Concepts"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (polars): Polars Core Concepts"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "polars core concepts"
keywords:
  - "polars"
  - "core"
  - "concepts"
  - "specialized"
  - "scientific"
  - "reference"
---

# Polars Core Concepts

## Expressions

Expressions are the foundation of Polars' API. They are composable units that describe data transformations without executing them immediately.

### What are Expressions?

An expression describes a transformation on data. It only materializes (executes) within specific contexts:
- `select()` - Select and transform columns
- `with_columns()` - Add or modify columns
- `filter()` - Filter rows
- `group_by().agg()` - Aggregate data

### Expression Syntax

**Basic column reference:**
```python
pl.col("column_name")
```

**Computed expressions:**
```python
# Arithmetic
pl.col("height") * 2
pl.col("price") + pl.col("tax")

# With alias
(pl.col("weight") / (pl.col("height") ** 2)).alias("bmi")

# Method chaining
pl.col("name").str.to_uppercase().str.slice(0, 3)
```

### Expression Contexts

**Select context:**
```python
df.select(
    "name",  # Simple column name
    pl.col("age"),  # Expression
    (pl.col("age") * 12).alias("age_in_months")  # Computed expression
)
```

**With_columns context:**
```python
df.with_columns(
    age_doubled=pl.col("age") * 2,
    name_upper=pl.col("name").str.to_uppercase()
)
```

**Filter context:**
```python
df.filter(
    pl.col("age") > 25,
    pl.col("city").is_in(["NY", "LA", "SF"])
)
```

**Group_by context:**
```python
df.group_by("department").agg(
    pl.col("salary").mean(),
    pl.col("employee_id").count()
)
```

### Expression Expansion

Apply operations to multiple columns at once:

**All columns:**
```python
df.select(pl.all() * 2)
```

**Pattern matching:**
```python
import polars.selectors as cs

# All columns ending with "_value"
df.select(pl.col("^.*_value$") * 100)

# All numeric columns
df.select(cs.numeric() + 1)
```

**Exclude patterns:**
```python
df.select(pl.all().exclude("id", "name"))
```

### Expression Composition

Expressions can be stored and reused:

```python
# Define reusable expressions
age_expression = pl.col("age") * 12
name_expression = pl.col("name").str.to_uppercase()

# Use in multiple contexts
df.select(age_expression, name_expression)
df.with_columns(age_months=age_expression)
```

## Data Types

Polars has typed columns and Arrow interoperability. Schema inference and common-supertype
coercion occur; strict casts reject invalid or overflowing values unless `strict=False`.
Inspect `df.schema` or `lf.collect_schema()`; resolving a lazy schema may read metadata
or sample source data. Use explicit schemas for identifiers and measurement units.

### Core Data Types

**Numeric:**
- `Int8`, `Int16`, `Int32`, `Int64` - Signed integers
- `UInt8`, `UInt16`, `UInt32`, `UInt64` - Unsigned integers
- `Float32`, `Float64` - Floating point numbers

**Text:**
- `String` (`Utf8` is an alias) - UTF-8 encoded strings
- `Categorical` - Categorized strings (low cardinality)
- `Enum` - Fixed set of string values

**Temporal:**
- `Date` - Calendar date (no time)
- `Datetime` - Date and time with optional timezone
- `Time` - Time of day
- `Duration` - Time duration/difference

**Boolean:**
- `Boolean` - True/False values

**Nested:**
- `List` - Variable-length lists
- `Array` - Fixed-length arrays
- `Struct` - Nested record structures

**Other:**
- `Binary` - Binary data
- `Object` - Python objects (avoid in production)
- `Null` - Null type

### Type Casting

Convert between types explicitly:

```python
# Cast to different type
df.select(
    pl.col("age").cast(pl.Float64),
    pl.col("date_string").str.strptime(pl.Date, "%Y-%m-%d"),
    pl.col("id").cast(pl.String)
)
```

### Null Handling

Polars uses consistent null handling across all types:

**Check for nulls:**
```python
df.filter(pl.col("value").is_null())
df.filter(pl.col("value").is_not_null())
```

**Fill nulls:**
```python
pl.col("value").fill_null(0)
pl.col("value").fill_null(strategy="forward")
pl.col("value").fill_null(strategy="backward")
pl.col("value").fill_null(strategy="mean")
```

**Drop nulls:**
```python
df.drop_nulls()  # Drop any row with nulls
df.drop_nulls(subset=["col1", "col2"])  # Drop rows with nulls in specific columns
```

Null is distinct from floating-point NaN and infinity. `fill_null`, `drop_nulls`,
and `count` only address nulls; use `is_nan`, `is_finite`, and `fill_nan` for floats.
Do not replace missing measurements with zero without a scientific justification.

### Categorical Data

Use categorical types for string columns with low cardinality (repeated values):

```python
# Cast to categorical
df.with_columns(
    pl.col("category").cast(pl.Categorical)
)

# Benefits:
# - Reduced memory usage
# - Faster grouping and joining
# - Does not encode a scientific or ordinal order; use Enum for declared levels
```

## Lazy vs Eager Evaluation

Polars supports two execution modes: eager (DataFrame) and lazy (LazyFrame).

### Eager Evaluation (DataFrame)

Operations execute immediately:

```python
import polars as pl

# DataFrame operations execute right away
df = pl.read_csv("data.csv")  # Reads file immediately
result = df.filter(pl.col("age") > 25)  # Filters immediately
final = result.select("name", "age")  # Selects immediately
```

**When to use eager:**
- Small datasets that fit in memory
- Interactive exploration in notebooks
- Simple one-off operations
- Immediate feedback needed

### Lazy Evaluation (LazyFrame)

Operations build a query plan, optimized before execution:

```python
import polars as pl

# LazyFrame operations build a query plan
lf = pl.scan_csv("data.csv")  # Builds a plan; schema inference may read source data
lf2 = lf.filter(pl.col("age") > 25)  # Adds to plan
lf3 = lf2.select("name", "age")  # Adds to plan
df = lf3.collect()  # NOW executes optimized plan
```

**When to use lazy:**
- Large datasets
- Complex query pipelines
- Only need subset of data
- Performance is critical
- Streaming required

### Query Optimization

Polars automatically optimizes lazy queries:

**Predicate Pushdown:**
Filter operations pushed to data source when possible:
```python
# Applies the filter during scanning; CSV still has to parse the input
lf = pl.scan_csv("data.csv")
result = lf.filter(pl.col("age") > 25).collect()
```

**Projection Pushdown:**
Only read needed columns from data source:
```python
# Projects needed columns; CSV bytes still require scanning
lf = pl.scan_csv("data.csv")
result = lf.select("name", "age").collect()
```

**Query Plan Inspection:**
```python
# View the optimized query plan
lf = pl.scan_csv("data.csv")
result = lf.filter(pl.col("age") > 25).select("name", "age")
print(resul

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

