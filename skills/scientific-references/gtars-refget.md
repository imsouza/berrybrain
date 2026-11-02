---
id: sciref-gtars-refget
name: "Scientific Ref: Refget, sequence digests, stores, and BEDbase"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (gtars): Refget, sequence digests, stores, and BEDbase"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "gtars refget"
  - "refget, sequence digests, stores, and bedbase"
keywords:
  - "gtars"
  - "refget"
  - "specialized"
  - "scientific"
  - "reference"
  - "sequence"
---

# Refget, sequence digests, stores, and BEDbase

Local synthetic FASTA/store tests on **2026-10-01** used Python `gtars==0.10.0`,
with bundled refget 0.10.0. CLI 0.10.0 and direct Rust refget 0.11.0
were source reviewed, not compiled or executed.

## Digest terminology

Current Python functions:

```python
from gtars.refget import (
    compute_fai,
    digest_fasta,
    digest_sequence,
    load_fasta,
    md5_digest,
    sha512t24u_digest,
)

digest = sha512t24u_digest("ACGT")
assert digest == "aKF498dAxcJAqme6QYQ7EZ07-fiw8Kw2"
assert md5_digest("ACGT") == "f1f8f4bf413b16ad135722aa4591043e"
```

Gtars returns the 32-character unprefixed `sha512t24u` value. The preferred
GA4GH refget sequence identifier adds `SQ.`:

```text
SQ.aKF498dAxcJAqme6QYQ7EZ07-fiw8Kw2
```

MD5 is retained for legacy lookup and is not a collision-resistant provenance
hash. Keep an independent SHA-256 for artifact integrity.

`digest_sequence(data: bytes, name=None, description=None)` uppercases sequence
bytes and returns a `SequenceRecord` containing metadata and data.
`digest_fasta(path)` computes a `SequenceCollection`; `load_fasta(path)` loads
sequence data into memory. `compute_fai(path)` is for uncompressed FASTA.

GA4GH refget normalizes sequence content before computing its sequence
identifier. Do not hash raw FASTA bytes and call that a sequence digest: headers,
line wrapping, compression, and sequence normalization are different layers.

## Current Python store class

The runtime class is `RefgetStore`, not the older tutorial name
`GlobalRefgetStore`:

```python
from gtars.refget import RefgetStore
```

Verified constructors:

```text
RefgetStore.in_memory()
RefgetStore.on_disk(cache_path)
RefgetStore.open_local(path)
RefgetStore.open_remote(cache_path, remote_url)
RefgetStore.store_exists(path)
```

### Local and in-memory modes

```python
from gtars.refget import RefgetStore

store = RefgetStore.in_memory()
metadata, was_new = store.add_sequence_collection_from_fasta(
    "reviewed-reference.fa",
    force=False,
    namespaces=["refseq"],
    collection_alias="local:reference",
)

store.write_store_to_dir("approved-store")
reopened = RefgetStore.open_local("approved-store")
```

Side effects:

- `in_memory()` does not write.
- `on_disk(path)` opens an existing store or creates a new disk-backed store.
- `open_local(path)` reads store metadata/indexes and lazy-loads local sequence
  data.
- `write_store_to_dir` and `enable_persistence` create/write files.
- `force=True` can replace existing collection/sequence entries.

Use `store_exists(path)` before choosing create versus open. Refuse symlinks,
unexpected files, output collisions, and unapproved stores.

Batch import:

```python
report = store.add_sequence_collections_from_fastas(
    ["ref-a.fa.gz", "ref-b.fa.gz"],
    file_list=None,
    jobs=1,
    force=False,
    namespaces=["refseq"],
)
```

In 0.10.0 the return is `ImportReport`: iterate `report.collections` for
`(metadata, was_new)` results. `report.n_collections_new`,
`report.n_sequences_written`, and `report.n_sequences_deduped` describe this
import run. `len(report)` is the number of file results. The report itself is
not a list or iterator. A skipped existing collection may contribute no sequence
counters if the import short-circuits before reading it.

`store.stats()` instead describes totals and current RAM residency. Its Python
values are strings: convert counts with `int(...)`. The keys now include
`n_sequences_in_memory`, `n_collections_in_memory`, and `logical_sequence_bytes`;
old `*_loaded` names are removed. Logical sequence bytes are encoded data volume,
not a measured cache-directory size.

`collection_alias="namespace:alias"` applies to the single-FASTA method. An
invalid syntax raises `ValueError`; alias conflicts require explicit resolution.
Do not silently overwrite a reference assembly alias.

`fastas` can also accept globs or directories and `jobs=0` means automatic
concurrency. For controlled runs, enumerate reviewed files explicitly and set a
positive bounded job count.

## Metadata-only and sequence access

Metadata methods avoid loading full sequence content:

```python
collections_page = store.list_collections(page=0, page_size=100)
sequence_metadata = store.list_sequences()
one_metadata = store.get_sequence_metadata(sequence_digest)
collection_metadata = store.get_collection_metadata(collection_digest)
```

`list_collections` returns a dictionary with `results` and `pagination`
(`page`, `page_size`, `total`); pages are zero-based. Advance the page until the
collected count reaches `total`. `list_sequences()` returns the full metadata
list without pagination, so it can still be large.

Data methods (the loop's `consume_bounded` is an application-specific callback):

```python
record = store.get_sequence(sequence_digest)
by_name = store.get_sequence_by_name(collection_digest, "chr1")
piece = store.get_substring(sequence_digest, 100, 200)
pieces = store.get_substrings(sequence_digest, [(100, 200), (500, 550)])

for chunk in store.stream_sequence(
    sequence_digest,
    start=0,
    end=1_000_000,
    chunk_size=65_536,
):
    consume_bounded(chunk)
```

Substring ranges are 0-based half-open. Validate `0 <= start <= end <= length`.
`stream_sequence` bounds peak result memory, but downstream accumulation can
still defeat streaming.

The 0.10.0 runtime also exposes `load_sequence`, `load_collection`,
`load_all_sequences`, and `load_all_collections`. These materialize more data;
do not call an all-load method without an explicit byte/RAM budget.

## Remote stores require an approval gate

```python
# Network + cache side effects: do not call before approval.
remote = RefgetStore.open_remote(
    approved_cache_path,
    approved_https_base_url,
)
```

`open_remote` takes only a cache path and base URL. It fetches remote metadata,
creates/uses local cache state, and enables persistence by default. In 0.10.0:

- `get_substring` can issue remote byte-range reads without downloading the
  whole sequence;
- `stream_sequence` can stream remote ranges;
- `load_sequence` is the whole-sequence path and can persist it.

This URL is the base of a **Gtars static store**, not an arbitrary GA4GH
`/sequence` REST endpoint. Source reads `rgstore.json`, referenced index files,
`collections/<digest>.rgsi`, and sequence files specified by the store manifest.
Substring requests use HTTP `Range` over encoded storage bytes, not genomic
coordinates in the URL; a range response must b

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

