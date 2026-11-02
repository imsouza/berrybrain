---
id: sciref-geniml-region2vec
name: "Scientific Ref: Region2Vec"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (geniml): Region2Vec"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "geniml region2vec"
  - "region2vec"
keywords:
  - "geniml"
  - "region2vec"
  - "specialized"
  - "scientific"
  - "reference"
  - "region"
---

# Region2Vec

Verified against `geniml==0.8.4` release source and the official BEDbase
documentation on 2026-10-01.

## What the method does

Region2Vec learns vectors for genomic regions from region co-occurrence within
interval sets. The primary paper describes randomizing regions within each set
to create word2vec-like contexts, then pooling region vectors to represent
sets. Treat learned proximity as a property of the training corpus and
universe, not as proof of a biological mechanism.

Primary method source: Gharavi et al. (2021), *Embeddings of genomic region sets
capture rich biological associations in low dimensions*,
doi:[10.1093/bioinformatics/btab439](https://doi.org/10.1093/bioinformatics/btab439).

## Stable 0.8.4 API reality

Use concrete module paths:

```python
from geniml.region2vec.main import Region2VecExModel
from geniml.region2vec.utils import Region2VecDataset
from gtars.tokenizers import Tokenizer
```

The release's `geniml.region2vec.__init__` does not export
`Region2VecExModel` or the legacy `region2vec` function. Consequently,
`from geniml.region2vec import region2vec` and the installed
`geniml region2vec ...` dispatch path are not reliable in 0.8.4. The old
function still exists at `geniml.region2vec.main_legacy.region2vec`, but use it
only to reproduce an existing workflow after a pinned smoke test.

## Universe and tokenizer contract

Create the tokenizer from a validated local BED universe:

```python
from gtars.tokenizers import Tokenizer

tokenizer = Tokenizer.from_bed("refs/universe.bed")
```

With verified `gtars==0.10.0`:

- universe regions receive stable IDs in file order;
- seven special tokens are added (`unk`, `pad`, `mask`, `cls`, `eos`, `bos`,
  and `sep`);
- `len(tokenizer)` is universe row count plus special tokens;
- `tokenizer(region_set)["input_ids"]` returns integer IDs.

Compatibility requires the exact universe bytes/order, assembly, contig policy,
Gtars version, special-token map/IDs, and tokenization behavior. Re-sorting a
universe changes IDs even when the interval set is mathematically identical.
Never infer compatibility from a shared filename such as `hg38.bed`.

Before tokenizing:

1. Validate BED as 0-based half-open intervals.
2. Confirm a single assembly with a checksummed chromosome-sizes file.
3. Resolve `chr1`/`1`, alt-contig, mitochondrial, and strand policies.
4. Split by patient/donor before learning or evaluating representations.
5. Record the universe SHA-256 and row count.

Run:

```bash
python skills/geniml/scripts/bed_validator.py \
  --input refs/universe.bed \
  --assembly GRCh38 \
  --chrom-sizes refs/GRCh38.chrom.sizes
```

## Prepare the token corpus

`Region2VecDataset` reads a Parquet file with one list-valued column named
`tokens`; each row is one BED document, sample, or cell. IDs must come from the
same tokenizer that initializes the model.

```python
import pyarrow as pa
import pyarrow.parquet as pq
from gtars.models import RegionSet

documents = []
for local_bed in validated_local_beds:
    ids = tokenizer(RegionSet(local_bed))["input_ids"]
    documents.append(ids)

table = pa.table({"tokens": pa.array(documents, type=pa.list_(pa.int32()))})
pq.write_table(table, "work/tokens.parquet")
```

This example assumes `validated_local_beds` came from a bounded, local
manifest. Do not discover arbitrary directory contents, follow symlinks, or
log sample filenames. Ensure every token is an integer in
`[0, len(tokenizer))`. Empty or unusually short documents need an explicit
policy; do not silently discard them after splitting.

`Region2VecDataset(path, shuffle=True, convert_to_str=False)` loads the full
Parquet `tokens` column into memory. Bound rows and total tokens before
construction. `shuffle=True` mutates each document order when accessed; record
the training seed, but do not assume every library/thread schedule is bitwise
deterministic.

## Train the modern model

```python
from geniml.region2vec.main import Region2VecExModel
from geniml.region2vec.utils import Region2VecDataset

dataset = Region2VecDataset("work/tokens.parquet", shuffle=True, convert_to_str=True)
model = Region2VecExModel(
    tokenizer=tokenizer,
    embedding_dim=100,
    pooling_method="mean",
    device="cpu",
)
model.train(
    dataset,
    window_size=5,
    epochs=10,
    min_count=10,
    num_cpus=4,
    seed=42,
)
```

The recipe was executed with a tiny synthetic corpus on the pinned CPU stack.
Seed Python's `random` before dataset iteration and Torch before model
construction as well as passing Gensim's `seed`: `shuffle=True` uses Python's
global RNG. `convert_to_str=True` makes vocabulary keys explicit strings.

Current source defaults are not fully consistent across legacy and modern
modules. Pass every material setting explicitly. `train` uses Gensim
Word2Vec, then copies learned weights into a Torch embedding matrix.
`load_from_checkpoint` and per-epoch Gensim `.model` files deserialize Gensim
artifacts; load only artifacts you created or independently trust.

Suggested run record:

- Geniml, Gtars, Python, Torch, Gensim, NumPy, and PyArrow versions;
- lockfile digest and platform;
- universe/checkpoint/config/token-corpus/manifest SHA-256;
- assembly, coordinate and contig contracts;
- vocabulary and special-token sizes;
- embedding dimension, window, epochs, `min_count`, workers, seed, shuffling,
  pooling, and device;
- train/validation/test grouping and excluded documents.

Generate a bounded plan first:

```bash
python skills/geniml/scripts/embedding_plan.py \
  --mode region2vec \
  --data work/tokens.parquet \
  --universe refs/universe.bed \
  --output-dir work/region2vec \
  --assembly GRCh38 \
  --embedding-dim 100 --epochs 10 --workers 4 --seed 42
```

## Export and inspect artifacts

The 0.8.4 constants are:

- `checkpoint.pt`
- `config.yaml`
- `universe.bed`

The config uses `vocab_size` and `embedding_dim`; `embedding_size` is accepted
only for backward compatibility and is marked for future deprecation.

Important release-source caveat: `model.export(path)` calls
`export_region2vec_model`, which writes the Torch checkpoint and YAML config
but does **not** write the tokenizer's universe or the pooling method, despite
the API docstring. A model initialized with max pooling reloads as mean pooling
unless `pooling_method` is added to `config.yaml`.
Copy the exact validated universe into the bundle yourself, without changing
row order, then create a checksum manifest.

```python
from pathlib import Path
i

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

