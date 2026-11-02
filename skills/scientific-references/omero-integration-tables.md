---
id: sciref-omero-integration-tables
name: "Scientific Ref: OMERO.tables"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (omero-integration): OMERO.tables"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "omero integration tables"
  - "omero.tables"
keywords:
  - "omero"
  - "integration"
  - "tables"
  - "specialized"
  - "scientific"
  - "reference"
---

# OMERO.tables

OMERO.tables stores columnar analysis data as an `OriginalFile` backed by an
HDF table. Treat table reads as data exports and table creation/update as
server writes.

## Compatibility and Scope

The current stable OMERO.tables definition is part of `omero-blitz` 5.8.5 in
the OMERO.server 5.6.18 documentation. OMERO.server 5.6.12 specifically
required OMERO.py 5.19.4 for the Tables service to start correctly, which
illustrates why client/server pairing matters.

Before using tables:

- confirm the server's tested OMERO.py version;
- confirm the Tables service is active;
- select one group and one table/attached object;
- cap columns and rows;
- plan handle closure even after read/query failure.

## Column Types

Current scalar columns:

- `FileColumn`, `ImageColumn`, `RoiColumn`, `WellColumn`, `PlateColumn`
- `BoolColumn`
- `LongColumn` (signed 64-bit)
- `DoubleColumn` (64-bit)
- `StringColumn(name, description, size, values)`

Current fixed-width array columns include:

- `FloatArrayColumn(name, description, size, values)`
- `DoubleArrayColumn(name, description, size, values)`
- `LongArrayColumn(name, description, size, values)`

Upstream still labels array columns experimental. The array `size` argument
is required. Older examples that omit it are stale.
All columns added in one operation must contain the same number of rows.
Column names are unique; names beginning with double underscore are reserved.

The service performs limited validation of string and array lengths. Validate
every value against the initialized schema before writing.

## Read-Only Table Inspection

Start from one explicit `OriginalFile` ID, not a filename search:

```python
original_file_id = 123
max_rows = 100
max_columns = 20

original = conn.getObject("OriginalFile", original_file_id)
if original is None:
    raise LookupError("Table OriginalFile unavailable")

resources = conn.c.sf.sharedResources(conn.SERVICE_OPTS)
table = resources.openTable(original._obj, conn.SERVICE_OPTS)
try:
    headers = list(table.getHeaders())
    if len(headers) > max_columns:
        raise ValueError("Table has more columns than approved")

    row_count = table.getNumberOfRows()
    stop = min(row_count, max_rows)
    column_indices = list(range(len(headers)))
    data = table.read(column_indices, 0, stop) if stop > 0 else None

    print(
        {
            "original_file_id": original_file_id,
            "total_rows": row_count,
            "returned_rows": stop,
            "truncated": row_count > stop,
            "columns": [column.name for column in headers],
        }
    )
finally:
    table.close()
```

`read(colNumbers, start, stop)` uses a stop-exclusive row range, except the
current docs note that `start=0, stop=0` returns the first row. Avoid that edge
case: do not call `read` when the approved row count is zero.

Other current read methods:

- `readCoordinates(rowNumbers)`: complete rows at explicit indices
- `slice(colNumbers, rowNumbers)`: selected columns and rows
- `getWhereList(condition, variables, start, stop, step)`: matching row
  indices, which can then be passed to `readCoordinates`

An empty column or row selection in `slice` may mean “all,” so never use empty
lists as a safety limit.

## Paged Read

Read consecutive chunks instead of every row:

```python
def iter_table_pages(table, column_indices, *, limit=1000, page_size=100):
    if not 1 <= limit <= 10_000:
        raise ValueError("limit out of range")
    if not 1 <= page_size <= min(limit, 500):
        raise ValueError("page_size out of range")

    total = min(table.getNumberOfRows(), limit)
    start = 0
    while start < total:
        stop = min(start + page_size, total)
        yield table.read(column_indices, start, stop)
        start = stop
```

Do not accumulate all pages unless the total cap and memory cost were reviewed.
Large string/array columns can make a small row count expensive.

## Fixed Queries and Bound Variables

OMERO.tables uses PyTables condition syntax. Keep the condition code fixed and
bind user values:

```python
from omero.rtypes import rlong

row_count = table.getNumberOfRows()
max_rows_considered = min(row_count, 1000)
matches = []
if max_rows_considered > 0:
    matches = list(table.getWhereList(
        condition="(Image > minimum_id)",
        variables={"minimum_id": rlong(100)},
        start=0,
        stop=max_rows_considered,
        step=0,
    )[:100])
data = table.readCoordinates(matches) if matches else None
```

Never concatenate user text into a condition. Validate column names against
`getHeaders()` and map requested operations to a fixed allowlist.

The documented condition language includes logical, comparison, arithmetic,
and selected mathematical operations. Treat it as a query language, not as
arbitrary Python. Do not use Python `eval()` or `exec()` around it.

## Creating a Table

Creation is a write. Use a unique, caller-reviewed name and one selected
repository:

```python
from omero.grid import DoubleColumn, ImageColumn, StringColumn

columns = [
    ImageColumn("Image", "Source image", []),
    DoubleColumn("MeanIntensity", "Mean raw value", []),
    StringColumn("Status", "Review status", 32, []),
]

resources = conn.c.sf.sharedResources(conn.SERVICE_OPTS)
repositories = resources.repositories(conn.SERVICE_OPTS).descriptions
if not repositories:
    raise RuntimeError("No table repository is available")

repository_id = repositories[0].getId().getValue()
table = resources.newTable(
    repository_id, "analysis-v2-explicit-name", conn.SERVICE_OPTS,
)
try:
    table.initialize(columns)
    table.addData(
        [
            ImageColumn("Image", "Source image", [101, 102]),
            DoubleColumn("MeanIntensity", "Mean raw value", [12.5, 14.0]),
            StringColumn("Status", "Review status", 32, ["reviewed", "reviewed"]),
        ]
    )
    table_file_id = table.getOriginalFile().getId().getValue()
finally:
    table.close()
```

Before execution:

- verify repository selection with the administrator;
- validate every referenced object ID in the same intended group;
- validate all row counts, numeric ranges, strings, and array sizes;
- cap rows per `addData` batch;
- decide recovery if initialization succeeds but data upload fails.

## Linking a Table

The table `OriginalFile` becomes discoverable through a `FileAnnotation` and an
object-annotation link:

```python
from omero.model import (
    DatasetAnnotationLinkI,
    DatasetI,
    FileAnnotationI,
   

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

