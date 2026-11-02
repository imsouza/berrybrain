---
id: sciref-latchbio-integration-registry
name: "Scientific Ref: Latch Registry SDK"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (latchbio-integration): Latch Registry SDK"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "latchbio integration registry"
  - "latch registry sdk"
keywords:
  - "latchbio"
  - "integration"
  - "registry"
  - "specialized"
  - "scientific"
  - "reference"
  - "latch"
---

# Latch Registry SDK

The current Registry API is object- and transaction-based. Older examples that
call `Project.create`, `Table.create`, `Record.create`, `Record.list`,
`record.update`, or `record.delete` do not match the current SDK.

This reference targets `latch==2.77.1`.

## Object Model

```text
Account (workspace)
└── Project
    └── Table
        └── Record
```

Current classes:

```python
from latch.account import Account
from latch.registry.project import Project
from latch.registry.record import Record
from latch.registry.table import Table
```

Objects are identified by numeric-string IDs. Display names are not globally
unique and must not be used as stable identifiers.

## Read Projects and Tables

```python
from latch.account import Account

account = Account.current()

for project in account.list_registry_projects():
    print(project.id, project.get_display_name())

    for table in project.list_tables():
        print("  ", table.id, table.get_display_name())
```

Most getters lazily call `load()` and cache the result. Use `load()` explicitly
when another process may have changed an object and fresh state is required.

Permissions are evaluated in the active CLI workspace or the workspace running
the task.

## Read Records

`Table.list_records()` is paginated and yields dictionaries keyed by record ID:

```python
from latch.registry.table import Table

table = Table(id="12345")

for page in table.list_records(page_size=100):
    for record_id, record in page.items():
        print(
            record_id,
            record.get_name(),
            record.get_values(),
            record.get_creation_time(),
            record.get_last_updated(),
        )
```

`page_size` must be positive. The SDK uses limit/offset pagination and sorts by
record ID; concurrent edits can change the result set between pages. Export a
quiescent table when a consistent scientific snapshot is required.

Record names are unique only within their table. Use `record.id` when a global
identifier is required.

To load one known record:

```python
from latch.registry.record import Record

record = Record(id="67890")
values = record.get_values()
table_id = record.get_table_id()
```

## DataFrames

`Table.get_dataframe()` requires the pandas extra:

```bash
uv pip install "latch[pandas]==2.77.1"
```

```python
frame = Table(id="12345").get_dataframe()
```

Use `list_records()` when streaming or dependency minimization matters.

## Transactional Updates

Updates are queued in a context manager and committed atomically when the
context exits successfully.

### Create a project

```python
from latch.account import Account

account = Account.current()
with account.update() as update:
    update.upsert_registry_project("RNA-seq Studies")
```

Despite the method name, creating projects and tables is not idempotent: two
calls with the same display name create two objects.

### Create a table

```python
from latch.registry.project import Project

project = Project(id="123")
with project.update() as update:
    update.upsert_table("Samples")
```

### Add columns and records

```python
from latch.registry.table import Table
from latch.types import LatchFile

table = Table(id="456")

with table.update() as update:
    update.upsert_column("condition", str, required=True)
    update.upsert_column("replicate", int)
    update.upsert_column("reads", LatchFile)

with table.update() as update:
    update.upsert_record(
        "sample-001",
        condition="treated",
        replicate=1,
        reads=LatchFile("latch:///inputs/sample-001.fastq.gz"),
    )
```

`upsert_record` takes the record name followed by column values as keyword
arguments. Unknown columns raise an error.

Supported column types include strings, integers, floats, dates, datetimes,
Booleans, `LatchFile`, `LatchDir`, enums, linked records, and selected list
forms. Check `TableUpdate.upsert_column` in the installed SDK before using a
less common nested type.

`TableUpdate.upsert_record` accepts `LPath` values in SDK 2.67.22 and later:

```python
from latch.ldata.path import LPath

with table.update() as update:
    update.upsert_record(
        "sample-002",
        reads=LPath("latch:///inputs/sample-002.fastq.gz"),
    )
```

### Delete

Deletion is queued through the corresponding updater:

```python
with table.update() as update:
    update.delete_record("sample-001")

with project.update() as update:
    update.delete_table("456")

with account.update() as update:
    update.delete_registry_project("123")
```

Record deletion takes a record **name**. Table and project deletion take IDs.
Confirm destructive operations and the active workspace first.

## Registry Samplesheets in Workflow Forms

`SamplesheetItem` preserves the source Registry record when a user imports rows
into a workflow form.

```python
from dataclasses import dataclass

from latch import small_task, workflow
from latch.registry.table import Table
from latch.types import LatchFile
from latch.types.metadata import (
    LatchAuthor,
    LatchMetadata,
    LatchParameter,
)
from latch.types.samplesheet_item import SamplesheetItem


@dataclass
class SampleRow:
    sample_name: str
    reads: LatchFile
    qc_status: str


metadata = LatchMetadata(
    display_name="Registry-aware QC",
    author=LatchAuthor(name="Workflow Team"),
    parameters={
        "samples": LatchParameter(
            display_name="Samples",
            samplesheet=True,
        )
    },
)


@small_task
def process_samples(samples: list[SamplesheetItem[SampleRow]]) -> int:
    updated = 0

    for item in samples:
        if item.record is None:
            continue

        table = Table(id=item.record.get_table_id())
        with table.update() as update:
            update.upsert_record(
                item.record.get_name(),
                qc_status="complete",
            )
        updated += 1

    return updated


@workflow(metadata)
def registry_qc(samples: list[SamplesheetItem[SampleRow]]) -> int:
    return process_samples(samples=samples)
```

Important behavior:

- `item.data` is the typed dataclass value.
- `item.record` is a `Record` when imported from Registry.
- `item.record` is `None` for a manually entered row.
- Dataclass fields should match Registry column keys where possible.
- The target table must already contain columns written by the task.
- Restrict selectable tables with `LatchParameter.allowed_tables` when the
  workflow should not accept arbitrary Registry sche

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

