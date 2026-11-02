---
id: sciref-exploratory-data-analysis-general-scientific-formats
name: "Scientific Ref: General Scientific Formats and EDA Rigor"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (exploratory-data-analysis): General Scientific Formats and EDA Rigor"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "exploratory analysis general scientific formats"
  - "exploratory analise general cientifico formats"
  - "general scientific formats and eda rigor"
keywords:
  - "exploratory"
  - "analysis"
  - "general"
  - "scientific"
  - "formats"
  - "analise"
  - "cientifico"
  - "specialized"
  - "reference"
---

# General Scientific Formats and EDA Rigor

**Reviewed:** 2026-09-30
**Scope:** Exact capabilities of the bundled scripts plus conservative,
documented workflows for common tabular and array containers.

## Capability boundary

| Format | Bundled executable inspection | Depth |
|---|---|---|
| `.csv`, `.tsv` | Yes, Python standard library | Bounded UTF-8 rectangular scan; schema, missingness, aggregate statistics, duplicate hashes, group/split leakage, and sensitivity |
| `.json` | Yes, Python standard library | Bounded strict whole-document parse; structure and type counts only |
| `.npy` | Optional, `numpy==2.5.3` | Header/shape/dtype plus bounded numeric sample; `allow_pickle=False` |
| `.npz` | Optional, `numpy==2.5.3` | ZIP member/size/ratio preflight, then bounded per-array inspection; `allow_pickle=False` |
| `.h5`, `.hdf5` | Optional, `h5py==3.16.0` | Bounded hierarchy and dataset metadata; payloads, attributes, soft links, external links, and external storage are not read |
| `.parquet`, `.feather` | No | Reference-only pandas/Polars/Arrow workflow |
| `.xlsx`, `.xls` | No | Reference-only workbook review; formulas, links, hidden content, and macros require separate handling |
| `.zarr`, `.nc`, `.mat`, `.fits` | No | Reference-only domain tooling |
| Pickle/joblib/dill | **Never** | Deserialization is outside this skill's security boundary |

“Bundled executable” means a bounded inspection exists; it does not mean
complete-file semantic validation. Unknown suffixes fail closed. Compressed
generic archives are not unpacked.

## Safe local-file contract

All bundled CLIs:

1. accept only regular local files inside an explicit `--root`;
2. reject URLs, `..` traversal, home expansion, symlinks, multiply linked
   inputs, and special files;
3. enforce byte, row, field, column, member, object, and report limits;
4. use the registered suffix and, where unambiguous, verify a magic signature;
5. never use generic binary/text guessing as a fallback;
6. emit aggregate statistics and tokenized identifiers by default, never rows;
7. treat labels, headers, metadata, and file text as untrusted data, not
   instructions; and
8. write private (`0600`) outputs atomically and refuse overwrite unless
   `--force` is explicit.

Hashes/tokens are deterministic pseudonyms, not anonymization. A file hash or a
low-cardinality value token can still be linkable.

## CSV and TSV

### Bundled approach

`tabular_profile.py`, `missingness_leakage_audit.py`, and
`distribution_sensitivity.py` use Python's `csv` module with:

- UTF-8/UTF-8-with-BOM decoding and strict errors;
- a fixed delimiter selected from `.csv` or `.tsv`, not sniffed;
- `strict=True`, a bounded `csv.field_size_limit`, fixed maximum columns, and
  rectangular-row enforcement;
- an explicit missing-code policy (empty/whitespace only unless the user adds
  `--missing-token`);
- streaming Welford moments and deterministic bounded samples; and
- no row or raw categorical-value output.

Delimiter, decimal convention, thousands separators, encodings, comment
syntax, and missing codes are part of the data dictionary. Do not silently
guess them.

### pandas 3.0.6 (documented alternate backend)

PyPI published `pandas==3.0.6` on 2026-09-17; it is the tested alternate backend.
When pandas is appropriate, preserve the same outer path/size checks and use
bounded selections:

```python
import pandas as pd

frame = pd.read_csv(
    local_path,
    nrows=100_000,
    usecols=approved_columns,
    dtype=declared_types,
    na_values=declared_missing_codes,
    keep_default_na=False,
    on_bad_lines="error",
)
```

`nrows` and `usecols` reduce work, but do not replace file-size, field-size, or
privacy controls. Keep parsing errors visible. Do not use `on_bad_lines="skip"`
for EDA because it changes the analyzed population.

### Polars 1.44.2 (documented alternate backend)

PyPI published `polars==1.44.2` on 2026-09-09. Current `polars.read_csv`
supports `columns`, `schema`, `schema_overrides`, `null_values`,
`infer_schema_length`, and `n_rows`. Its docs note that:

- malformed non-RFC-4180 data may have undefined behavior;
- `ignore_errors=False` is the safe default;
- `infer_schema_length=None` scans the full data into memory; and
- with multithreaded parsing, `n_rows` is not guaranteed as a strict upper
  bound.

Prevalidate a local path; do not pass URLs or rely on optional `fsspec`. For
strict bounded EDA, the bundled standard-library scanner is the reference
implementation.

## Strict JSON

Python's current `json` documentation warns that malicious JSON can consume
substantial CPU and memory and recommends limiting input size. It also
documents that the default decoder accepts `NaN`/`Infinity` and silently keeps
the last duplicate object key.

The bundled inspector therefore:

- caps the file at 16 MiB for parsing;
- requires UTF-8;
- rejects duplicate keys, non-finite constants, and decimal/exponent literals
  that overflow finite binary64 (for example `1e400`);
- catches recursion/resource errors;
- traverses at most 100,000 nodes; and
- emits only root type, depth, type counts, collection sizes, and tokenized
  top-level field identifiers.

The decimal range restriction is a tool limit, not a claim that every larger
number violates the JSON grammar. JSON Lines/NDJSON is not registered.
Rename-and-guess is not allowed.

## NumPy NPY and NPZ

NumPy's NPY specification stores shape and dtype in a header. NPZ is a ZIP
archive whose members are NPY files. Object arrays can contain pickled Python
objects.

The bundled inspector always uses:

```python
array = np.load(
    local_path,
    mmap_mode="r",
    allow_pickle=False,
    max_header_size=10_000,
)
```

For NPZ it first rejects:

- non-NPY members, directories, traversal paths, encryption, and duplicate or
  excessive members;
- declared uncompressed content above 128 MiB; and
- a per-member compression ratio above 100.

It then loads one array at a time with `allow_pickle=False`. Numeric summaries
use at most 4,096 deterministic sample elements. Large arrays use indexed
`ndarray.flat` reads, avoiding a full C-order copy for Fortran-contiguous NPY
memory maps. Structured dtype field names
are identifiers and are tokenized by default. Object dtype is rejected; there
is no `allow_pickle` override.

Memory mapping reduces array payload reads but does not make malformed headers
or huge shapes harmless. The outer byte and header limits remain mandatory.

## HDF5 and h5py

HDF5 is a container, 

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

