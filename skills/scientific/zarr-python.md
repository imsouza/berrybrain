---
id: sci-zarr-python
name: "Scientific: zarr-python"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Stores and queries chunked N-D scientific arrays with Zarr-Python 3, including codecs, sharding, S3/GCS storage, and NumPy/Dask/Xarray integration. Use for array layout, bounded I/O, format migration, or scientific metadata preservation."
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "zarr python"
  - "zarr-python"
keywords:
  - "zarr"
  - "python"
  - "stores"
  - "queries"
  - "chunked"
  - "scientific"
  - "arrays"
---

# Zarr Python

## When to use

Use for chunked scientific arrays, hierarchical stores, codecs, sharding, partial reads,
cloud object storage, and NumPy/Dask/Xarray interoperability. This community guide targets
**Zarr-Python 3.4.0**, released **2026-09-15**, with Python 3.12+. The package version and
on-disk format are separate: this release reads/writes formats 2 and 3; new arrays default
to format 3. Keep downstream packages that require `zarr<3` in their own environments.

## Install

```bash
uv pip install "zarr==3.4.0" "numpy==2.5.3"
# Optional remote backends and migration CLI:
uv pip install "zarr[remote,cli]==3.4.0" "fsspec==2026.9.0" "s3fs==2026.9.0" "gcsfs==2026.8.1"
```

Commit the project's resolved lockfile. Optional integration versions exercised here:
Dask 2026.8.0, Xarray 2026.9.0, h5py 3.16.0, NumCodecs 0.17.0, obstore 0.11.1.
Local examples below and in the references use tiny synthetic arrays; remote snippets
are illustrative and require a real authorized store. This does not establish cloud
permissions, production throughput, or compatibility of every downstream reader.

## Workflow

1. Inspect shape, dtype, axis names, coordinates, units, missing-value convention, format,
   codec availability, and intended readers. Preserve sample IDs and axis order.
2. Choose chunks for actual selections and a memory budget. For sharding, choose shard
   dimensions that are multiples of chunk dimensions. Benchmark representative data.
3. Create a new destination (`overwrite=False` or `mode="w-"`). Use `mode="r"` for
   inspection; `"a"` can create a missing store and `"w"` destroys existing content.
4. Write bounded blocks. Assign one writer per stored chunk, or per **shard** when
   sharded; serialize metadata, append, and resize operations.
5. Reopen read-only and compare values, dtype, shape, coordinates, units, masks and
   metadata. An unwritten or missing chunk normally reads as `fill_value`; a successful
   open alone does not prove data completeness.
6. For a completed group hierarchy, optionally consolidate metadata. Format-3
   consolidation is experimental; refresh it after metadata changes and verify the
   actual consumers. Publish a completed store only after validation.

## Basic array roundtrip

```python
import numpy as np
import zarr
from zarr.codecs import BloscCodec

expected = np.arange(96, dtype="float32").reshape(12, 8)
z = zarr.create_array(
    "array.zarr", shape=expected.shape, dtype=expected.dtype,
    chunks=(4, 4), zarr_format=3,
    compressors=BloscCodec(cname="zstd", clevel=5, shuffle="bitshuffle"),
    dimension_names=("sample", "feature"),
    attributes={"units": "arbitrary", "source": "synthetic example"},
)
for start in range(0, z.shape[0], 4):
    z[start:start + 4] = expected[start:start + 4]

reopened = zarr.open_array("array.zarr", mode="r")
np.testing.assert_array_equal(reopened[:], expected)
assert reopened.dtype == expected.dtype
assert reopened.metadata.dimension_names == ("sample", "feature")
assert reopened.attrs["units"] == "arbitrary"
subset = reopened[2:6, 1:4]  # Only this selection is materialized.
```

`create_array` takes either `data=` or `shape=` plus `dtype=`; do not combine `data=`
with explicit shape/dtype. The format-3 numeric default is a bytes serializer followed
by **ZstdCodec**, not Blosc. Set a codec explicitly for reproducibility.

## Creation and indexing

```python
import numpy as np
import zarr

z = zarr.create_array(None, data=np.arange(80).reshape(10, 8), chunks=(2, 4))
zeros = zarr.zeros((10, 8), chunks=(2, 4), dtype="f4")
ones = zarr.ones((10, 8), chunks=(2, 4), dtype="f4")
filled = zarr.full((10, 8), fill_value=42, chunks=(2, 4), dtype="i4")
like = zarr.zeros_like(z)
np.testing.assert_array_equal(filled[:], np.full((10, 8), 42))

# Coordinate indexing pairs corresponding coordinates; orthogonal indexing is a product.
np.testing.assert_array_equal(z.vindex[[0, 5], [2, 7]], [2, 47])
np.testing.assert_array_equal(z.get_coordinate_selection(([0, 5], [2, 7])), [2, 47])
assert z.oindex[[0, 5], [2, 7]].shape == (2, 2)
assert z.blocks[0, 0].shape == (2, 4)
z[0, :] = np.arange(8)
```

Negative-step slices are unsupported. Array reads return NumPy data in the default CPU
configuration. `np.asarray(z)`, `np.sum(z)`, `z[:]`, or a Dask `.compute()` of a full array
can materialize the entire logical dataset; use bounded selections or lazy reductions.

## Resize and append

```python
import numpy as np
import zarr

series = zarr.create_array(None, shape=(0, 8), chunks=(2, 8), dtype="f4")
series.append(np.ones((2, 8), dtype="f4"), axis=0)
series.resize((4, 8))  # A tuple; append must match all non-appended dimensions.
assert series.shape == (4, 8)
np.testing.assert_array_equal(series[2:], np.zeros((2, 8)))
```

Coordinate resize/append centrally. Shrinking removes chunks outside the new shape,
but values in retained boundary chunks can reappear on re-expansion; resize is not
secure erasure or a missingness policy. Record time/sample coordinates alongside data.

## Groups and attributes

```python
import numpy as np
import zarr

root = zarr.open_group("hierarchy.zarr", mode="w-", zarr_format=3)
temperature = root.create_group("temperature")
temp = temperature.create_array(
    "t2m", data=np.full((3, 4, 6), 280, dtype="f4"), chunks=(1, 4, 6),
    dimension_names=("time", "lat", "lon"), attributes={"units": "K"},
)
root.require_group("quality")
root.require_array("count", shape=(3,), chunks=(3,), dtype="i4")
root.attrs.update({"project": "synthetic climate example", "processing_version": "1.0"})
loaded = zarr.open_group("hierarchy.zarr", mode="r")
assert loaded["temperature/t2m"].attrs["units"] == "K"
assert loaded.attrs["processing_version"] == "1.0"
print(loaded.tree())  # Logical group/array tree, not physical metadata files.
```

Use `create_array` / `require_array`; `create_dataset` / `require_dataset` are removed.
Attributes belong to the specific node on which they are set and must be JSON-compatible.
Names/units are declarations, not unit conversion or scientific validation.
`require_array` checks an existing array's compatibility; it does not rechunk it.

## References

- [Chunking and compression](references/chunking_and_compression.md): measured layout
  decisions, default codecs, sharding, experimental rectilinear grids.
- [Storage backends](references/storage_backends.md): local, memory, ZIP, ObjectStore,
  fsspec, S3/GCS/HTTP paths and credentials.
- [Integration](references/integration.md): bounded Nu

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

