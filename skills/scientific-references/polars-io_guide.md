---
id: sciref-polars-io-guide
name: "Scientific Ref: Polars Data I/O Guide"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (polars): Polars Data I/O Guide"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "polars guide"
  - "polars data i/o guide"
keywords:
  - "polars"
  - "guide"
  - "specialized"
  - "scientific"
  - "reference"
---

# Polars Data I/O Guide

Polars 1.44.2 I/O patterns. Local CSV, Parquet, JSON, IPC, Excel, SQLite, and
Arrow/pandas/NumPy conversions are covered by bounded native tests. Cloud providers,
BigQuery, ConnectorX/ADBC, and remote databases below are illustrative, documentation-
verified integrations, not authenticated end-to-end checks. See [review.md](review.md).
Fragments require the named files and schemas. All writes use user-chosen outputs.

## CSV Files

### Reading CSV

**Eager mode (loads into memory):**
```python
import polars as pl

# Basic read
df = pl.read_csv("data.csv")

# With options
df = pl.read_csv(
    "data.csv",
    separator=",",
    has_header=True,
    columns=["col1", "col2"],  # Select specific columns
    n_rows=1000,  # Parser limit; multithreading may exceed it; head(1000) caps output
    skip_rows=10,  # Skip records before parsing the header; respects CSV quoting
    schema_overrides={"col1": pl.Int64, "col2": pl.String},  # Specify types
    null_values=["NA", "null", ""],  # Define null values
    encoding="utf-8",
    ignore_errors=False
)
```

**Lazy mode (builds a plan; metadata/inference can read the source):**
```python
# Scan CSV (builds query plan)
lf = pl.scan_csv("data.csv")

# Apply operations
result = lf.filter(pl.col("age") > 25).select("name", "age")

# Execute and load
df = result.collect()
```

### Writing CSV

```python
# Basic write
df.write_csv("output.csv")

# With options
df.write_csv(
    "output.csv",
    separator=",",
    include_header=True,
    null_value="",  # How to represent nulls
    quote_char='"',
    line_terminator="\n"
)
```

### Multiple CSV Files

**Read multiple files:**
```python
# Read all CSVs in directory
lf = pl.scan_csv("data/*.csv")

# Read specific files
lf = pl.scan_csv(["file1.csv", "file2.csv", "file3.csv"])
```

## Parquet Files

Parquet is the recommended format for performance and compression.

### Reading Parquet

**Eager:**
```python
df = pl.read_parquet("data.parquet")

# With options
df = pl.read_parquet(
    "data.parquet",
    columns=["col1", "col2"],  # Select specific columns
    n_rows=1000,  # Read first N rows
    parallel="auto"  # Control parallelization
)
```

**Lazy (recommended):**
```python
lf = pl.scan_parquet("data.parquet")

# Automatic predicate and projection pushdown
result = lf.filter(pl.col("age") > 25).select("name", "age").collect()
```

### Writing Parquet

```python
# Basic write
df.write_parquet("output.parquet")

# With compression
df.write_parquet(
    "output.parquet",
    compression="snappy",  # Options: "snappy", "gzip", "brotli", "lz4", "zstd"
    statistics=True,  # Write statistics (enables predicate pushdown)
    use_pyarrow=False  # Use native writer; benchmark for the workload
)
```

### Partitioned Parquet (Hive-style)

**Write partitioned:**
```python
# Write with partitioning
df.write_parquet(
    "output_dir",
    partition_by=["year", "month"]  # Creates directory structure
)
# Creates year=.../month=... partitions; filenames and zero-padding are not fixed
```

**Read partitioned:**
```python
lf = pl.scan_parquet("output_dir/**/*.parquet", hive_partitioning=True)

# Explicitly parse Hive keys when scanning a glob; validate their inferred types
result = lf.filter(pl.col("year") == 2023).collect()
```

## JSON Files

### Reading JSON

**NDJSON (newline-delimited JSON) - recommended:**
```python
df = pl.read_ndjson("data.ndjson")

# Lazy
lf = pl.scan_ndjson("data.ndjson")
```

**Standard JSON:**
```python
df = pl.read_json("data.json")

# From JSON string
from io import StringIO
df = pl.read_json(StringIO('[{"col1": 1, "col2": "a"}, {"col1": 2, "col2": "b"}]'))
```

### Writing JSON

```python
# Write NDJSON
df.write_ndjson("output.ndjson")

# Write standard JSON
df.write_json("output.json")

# write_json emits row-oriented JSON; pretty/row_oriented are not current arguments.
# To serialize a column dictionary explicitly:
import json
from pathlib import Path
Path("columns.json").write_text(json.dumps(df.to_dict(as_series=False)), encoding="utf-8")
```

## Excel Files

### Reading Excel

```python
# Read first sheet
df = pl.read_excel("data.xlsx")

# Specific sheet
df = pl.read_excel("data.xlsx", sheet_name="Sheet1")
# Sheet IDs are 1-based; 0 returns a dictionary containing every sheet.
df = pl.read_excel("data.xlsx", sheet_id=1)
sheets = pl.read_excel("data.xlsx", sheet_id=0)

# With options
df = pl.read_excel(
    "data.xlsx",
    sheet_name="Sheet1",
    columns=["sample_id", "value"],  # Header names or zero-based positions
    engine="calamine",
    read_options={"n_rows": 100, "skip_rows": 5},  # fastexcel options, after header
    has_header=True
)
```

### Writing Excel

```python
# Write to Excel
df.write_excel("output.xlsx")

# Multiple sheets: reading uses fastexcel by default, writing uses xlsxwriter.
import xlsxwriter
with xlsxwriter.Workbook("output.xlsx") as writer:
    df1.write_excel(workbook=writer, worksheet="Sheet1")
    df2.write_excel(workbook=writer, worksheet="Sheet2")
```

## Database Connectivity

### Read from Database

```python
import polars as pl

# A connection/cursor, not a URI keyword. Bind values through the driver.
import sqlite3
with sqlite3.connect("study.sqlite") as connection:
    df = pl.read_database(
        "SELECT * FROM observations WHERE value > ?",
        connection=connection,
        execute_options={"parameters": [25]},
    )

# URI route: requires connectorx (default) or ADBC plus a suitable driver.
import os
df = pl.read_database_uri(
    "SELECT * FROM observations WHERE value > 25",
    uri=os.environ["STUDY_DATABASE_URI"],
    engine="connectorx",
)
```

### Write to Database

```python
# Using SQLAlchemy
from sqlalchemy import create_engine

engine = create_engine("sqlite:///study.sqlite")

# Choose the table-existence policy explicitly.
df.write_database(
    "table_name",
    connection=engine,
    if_table_exists="fail",  # Explicitly choose "append" or "replace" only if intended
)
```

### Common Database Connectors

**PostgreSQL:**
```python
uri = os.environ["STUDY_POSTGRES_URI"]  # postgresql:// URI supplied by deployment
df = pl.read_database_uri("SELECT * FROM table", uri=uri)
```

**MySQL:**
```python
uri = os.environ["STUDY_MYSQL_URI"]  # mysql:// URI supplied by deployment
df = pl.read_database_uri("SELECT * FROM table", uri=uri)
```

**SQLite:**
```python
uri = "sqlite:///path/to/database.db"
df = pl.read_database_uri("SELECT * FROM table", uri=uri)
```

For large database results, `re

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

