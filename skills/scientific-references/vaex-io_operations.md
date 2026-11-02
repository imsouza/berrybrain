---
id: sciref-vaex-io-operations
name: "Scientific Ref: File I/O and remote data"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (vaex): File I/O and remote data"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "vaex operations"
  - "file i/o and remote data"
keywords:
  - "vaex"
  - "operations"
  - "specialized"
  - "scientific"
  - "reference"
  - "file"
  - "remote"
---

# File I/O and remote data

Targets core 4.19.0 / HDF5 0.15.0. [Official I/O guide](https://vaex.io/docs/guides/io.html)
and released readers/writers define these contracts.

## Local format round trips

This small fixture uses a temporary directory. Real exports overwrite existing paths
by default: choose a new destination, verify it, then manage replacement explicitly.

```python
from pathlib import Path
from tempfile import TemporaryDirectory
import csv
import numpy as np
import pyarrow as pa
import pyarrow.csv as pacsv
import vaex

workspace = TemporaryDirectory()
root = Path(workspace.name)
df = vaex.from_arrays(id=np.array(['001', '002', '003']), x=np.array([1., 2., 3.]))
df['twice'] = 2 * df.x
paths = {ext: root / ('data.' + ext) for ext in ['hdf5', 'arrow', 'feather', 'parquet', 'csv']}
df.export_hdf5(str(paths['hdf5']), chunk_size=2)
df.export_arrow(str(paths['arrow']), chunk_size=2)  # Arrow IPC stream by default
df.export_feather(str(paths['feather']), compression='lz4')
df.export_parquet(str(paths['parquet']), compression='snappy', chunk_size=2)
df.export_csv(str(paths['csv']), index=False, chunk_size=2)
for ext in ['hdf5', 'arrow', 'feather', 'parquet']:
    reopened = vaex.open(str(paths[ext]))
    assert reopened.id.tolist() == ['001', '002', '003']
    assert reopened.twice.tolist() == [2., 4., 6.]
# Arrow stream and Arrow file readers differ:
with pa.input_stream(str(paths['arrow'])) as source:
    table = pa.ipc.open_stream(source).read_all()  # this small fixture fits in RAM
assert table.num_rows == 3
```

HDF5 means the Vaex tabular layout, not arbitrary HDF5. `export_hdf5` has no
`compression=` keyword. `mode='a'` appends a **different group**, not rows to the same
table. Do not implement incremental row export by repeatedly writing `/table` in append
mode. For compression use a tested Parquet/Feather format and verify type/null fidelity.
Nested Arrow structures and multidimensional columns have format-specific limits;
round-trip a representative fixture before a full conversion.

`export_arrow` defaults to a stream (`as_stream=True`); request `as_stream=False`
when an Arrow IPC file is required. `export_feather` uses its own Feather writer and
can materialize a table; do not assume its memory profile matches chunked Arrow export.
Compressed buffers cannot provide the same memory-map behavior as uncompressed columns.

## CSV types, chunking and conversion

```python
# Check raw column names before a CSV parser silently renames duplicates.
with paths['csv'].open(newline='', encoding='utf-8') as handle:
    headers = next(csv.reader(handle))
assert len(headers) == len(set(headers))
options = pacsv.ConvertOptions(column_types={'id': pa.string(), 'x': pa.float64(), 'twice': pa.float64()})
lazy = vaex.from_csv_arrow(str(paths['csv']), lazy=True, convert_options=options,
                           chunk_size='1MiB')
assert lazy.id.tolist() == ['001', '002', '003']
# pandas-backed reader is eager unless chunk_size or conversion is requested.
eager = vaex.from_csv(str(paths['csv']), dtype={'id': str})
assert eager.id.tolist() == ['001', '002', '003']
part_paths = []
for index, chunk in enumerate(vaex.from_csv(str(paths['csv']), chunk_size=2, dtype={'id': str})):
    chunk['offset'] = chunk.x + 10
    path = root / f'part-{index:04d}.hdf5'
    chunk.export_hdf5(str(path))
    part_paths.append(str(path))
combined = vaex.open_many(part_paths)
assert combined.offset.tolist() == [11., 12., 13.]
converted = vaex.from_csv(str(paths['csv']), convert=str(root / 'converted.hdf5'),
                          chunk_size=2, dtype={'id': str})
assert converted.id.tolist() == ['001', '002', '003']
```

Use `vaex.from_csv(..., chunk_size=...)` for the iterator; there is no public
`from_csv_chunked` function. `from_csv(..., convert=...)` writes intermediate parts
and a combined file, so budget temporary disk space as well as the final output.
Lazy CSV does schema/index work and does not support compressed CSV files in this
release. `convert_options` is the correct parameter for Arrow column type hints.
Inspect null spellings, delimiter, quoting, encoding and units. The metadata cache and
conversion-reuse logic are conveniences, not content-addressed provenance: record source
checksums and use a fresh destination when inputs change.

For SQL, use a bounded pandas/SQLAlchemy chunk iterator and export each chunk to a
separate file, then `vaex.open_many`. Collecting all chunks in a list retains all data
in RAM. SQL import/export is not a native Vaex database endpoint; parameter binding,
transactions and schema belong to the chosen database client. Never interpolate user
values into SQL or put passwords in examples/logs.

## State is separate from data

```python
state_path = root / 'expressions.json'
df.state_write(str(state_path))
fresh = vaex.from_arrays(id=np.array(['001', '002', '003']), x=np.array([1., 2., 3.]))
fresh.state_load(str(state_path), set_filter=False, trusted=True)
assert fresh.twice.tolist() == [2., 4., 6.]
workspace.cleanup()
```

A state file stores definitions, variables, selections and serialized functions; it is
not a data backup. Loading it can alter filters/columns and execute deserialized Python
objects. Use only trusted state plus matching schema/units/software versions.
`set_filter=False` prevents importing the training filter; validate target row count
and identities after transfer. Models appear only after their prediction transform is
attached to the saved DataFrame. See [ML](machine_learning.md).

## Remote/cloud I/O: source-verified, not service-tested

Core has native S3 handling through PyArrow with an s3fs fallback and GCS handling
through gcsfs. `fs_options` keys are backend-specific; an explicit `fs` object and
`fs_options` should not be combined. Remote reads may create a local file cache.
Examples below are illustrative and require an accessible object plus credentials
configured outside the code. They were checked against source, not run against accounts.

```python
s3 = vaex.open('s3://example-bucket/measurements.parquet',
               fs_options={'profile': 'research', 'region': 'us-east-1'})
gcs = vaex.open('gs://example-bucket/measurements.parquet',
                fs_options={'project': 'research-project'})
```

Do not assume installing `adlfs` makes an `az://` URI understood by every Vaex reader.
For another backend, configure its filesystem and verify a representative read with
`fs=` using that backend's current documentation. Native HD

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

