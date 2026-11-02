---
id: sciref-zarr-python-v3-migration
name: "Scientific Ref: Zarr-Python 3 migration"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (zarr-python): Zarr-Python 3 migration"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "zarr python migration"
  - "zarr-python 3 migration"
keywords:
  - "zarr"
  - "python"
  - "migration"
  - "specialized"
  - "scientific"
  - "reference"
---

# Zarr-Python 3 migration

Targets **3.4.0**. Separate upgrading the Python package, migrating application APIs,
and changing an existing store's on-disk format. Choosing `zarr_format=2` when creating
with Zarr-Python 3 does not make its Python API compatible with code written for v2.
Some scientific consumers still require a separate environment pinned to Zarr-Python 2.

| Older API | Current guidance |
|---|---|
| `DirectoryStore` / `FSStore` | `zarr.storage.LocalStore` / `FsspecStore` |
| `TempStore` | `tempfile.TemporaryDirectory` plus LocalStore |
| `group.create_dataset` / `require_dataset` | `create_array` / `require_array` |
| `group.foo` | `group["foo"]` |
| `resize(n, m)` | `resize((n, m))` |
| `compressor=` legacy creation | `compressors=` with the codec family appropriate to the on-disk format |
| `synchronizer`, separate `chunk_store` | Not implemented for the v3 API; coordinate ownership externally |
| `copy`, `copy_all`, `copy_store`, `Group.move` | Not implemented; use explicit validated copying in a new destination |

Python 3.12+ and NumPy 2+ are required for the current package. Upstream states the
Zarr-Python 2 support window ended; choosing an exact legacy pin is a compatibility
choice, not a claim of current maintenance. Do not invent a Python upper bound for all
v2 releases. Generic object dtype is ambiguous; choose a supported explicit dtype and
validate consumer support for variable-length/string/extension data.

## Format-2 creation with the current package

```python
import numpy as np
import zarr
from numcodecs import Blosc

legacy = zarr.create_array(
    "legacy.zarr", data=np.arange(24, dtype="i4").reshape(6, 4), chunks=(2, 2),
    zarr_format=2, compressors=Blosc(cname="zstd"),
    attributes={"units": "counts"},
)
assert legacy.metadata.zarr_format == 2
```

## The CLI migrates metadata, not chunk data

Install `zarr[cli]==3.4.0`. `zarr migrate v3 input.zarr output.zarr` writes new
`zarr.json` metadata at the destination **without copying chunk payloads**. That output
can open successfully while reading fill values instead of original data. Do not report
it as a converted dataset. Test a **complete copy** of the source, then migrate in place
on that copy; preserve the original until all consumers pass.

Continuing the synthetic example above, copy the small closed local store:

```python
from shutil import copytree
copytree("legacy.zarr", "migration-copy.zarr")
```

```bash
zarr migrate v3 migration-copy.zarr --dry-run
zarr migrate v3 migration-copy.zarr
```

Then verify both formats against the original source, including non-fill data:

```python
import numpy as np
import zarr

original = zarr.open_array("legacy.zarr", mode="r", zarr_format=2)
converted = zarr.open_array("migration-copy.zarr", mode="r", zarr_format=3)
np.testing.assert_array_equal(converted[:], original[:])
assert converted.dtype == original.dtype
assert dict(converted.attrs) == dict(original.attrs)
```

Only after validation and consumer compatibility checks, retire v2 metadata on the copy:

```bash
zarr remove-metadata v2 migration-copy.zarr --dry-run
zarr remove-metadata v2 migration-copy.zarr
```

This is a local homogeneous numeric example, not a guarantee for all codecs/dtypes or
remote hierarchies. Back up complete objects; list/metadata operations aren't snapshots.
When both v2/v3 metadata exist, specify the intended format on open. For full conversion
with changed chunks/codecs, create a new store and copy bounded selections, preserving
scientific metadata deliberately.

Rectilinear chunks remain experimental (`array.rectilinear_chunks=True`), and format-3
consolidation remains experimental. Don't make either an accidental migration default.

Sources: [migration guide](https://zarr.readthedocs.io/en/stable/user-guide/v3_migration/),
[CLI](https://zarr.readthedocs.io/en/stable/user-guide/cli/),
[released migration code](https://github.com/zarr-developers/zarr-python/blob/v3.4.0/src/zarr/metadata/migrate_v3.py).

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

