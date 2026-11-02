---
id: sci-geniml
name: "Scientific: geniml"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Supports audited local Geniml genomic-interval workflows: validate BED and universe contracts, plan Region2Vec or scEmbed runs, inspect model/tokenizer compatibility, and assess consensus universes."
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "geniml"
keywords:
  - "geniml"
  - "supports"
  - "audited"
  - "local"
  - "genomic"
  - "interval"
---

# Geniml

Use Geniml for machine learning and statistical workflows over genomic interval
sets. Treat coordinates, assemblies, token vocabularies, model artifacts, and
sample grouping as explicit contracts. The bundled scripts validate or plan;
they do not import Geniml, contact services, deserialize models, or execute
training.

`Bash` is declared only for explicit, user-approved `uv`, Python, Geniml,
Gtars, Git, and native CLI commands shown in this guide; bundled Python helpers
do not spawn subprocesses. Example paths under `data/`, `refs/`, `work/`, and
`models/` are user-provided project placeholders, not missing bundled files.

## Verified release snapshot

- Latest stable PyPI release on 2026-10-01: `geniml==0.8.4` (2026-01-14).
- PyPI does not declare `Requires-Python`; its classifiers list Python
  3.10-3.14. The current recipes below were tested on Python 3.12.
- `geniml==0.8.4` accepts `gtars>=0.2.5`; the verified base smoke used current
  `gtars==0.10.0` (2026-09-05, Python >=3.10).
- Extras are `ml` and `test`. The base install omits Torch, Gensim, Scanpy,
  Hugging Face Hub, pyBigWig, and HMM dependencies.
- Upstream documentation contains stale examples. Release source and installed
  `--help` output take precedence where they conflict.

## Install reproducibly

Use a separate project environment. The tested CPU stack uses Python 3.12:

```bash
uv venv --python 3.12
uv pip install "geniml==0.8.4" "gtars==0.10.0"
```

For the Region2Vec/scEmbed recipes tested here, add only their required libraries:

```bash
uv pip install "torch==2.14.1" "gensim==4.4.0" "huggingface-hub==2.0.0" \
  "scanpy==1.12.4" "anndata==0.12.19" "zarr==2.18.7"
```

For the consensus recipes, also install `pyBigWig==0.3.26` and
`hmmlearn==0.3.3`. For a durable project, use the same requirements with
`uv add` and retain `uv.lock`.

Geniml requires Zarr <3. AnnData 0.13 requires Zarr >=3, so current AnnData
cannot share this environment. Keep AnnData 0.12.19 here; transfer H5AD files
between separate environments when newer AnnData features are needed. Never
force an incompatible installation with `--no-deps`.

The full `geniml[ml]==0.8.4` extra includes additional, older pinned components.
Its resolution was checked with `anndata==0.12.19` and `gtars==0.10.0`, but
that full stack was not executed; it selected Scanpy 1.11.5 and Transformers
4.57.6. It is unnecessary for the workflows above.

Do not install an unpinned Git branch. Record Python, OS/architecture, the
resolved lockfile, and the PyPI artifact digest. Geniml itself is BSD-2-Clause;
the `MIT` frontmatter value licenses this skill's content.

## Start with the safety gate

Before importing Geniml or running an external binary:

1. Work only with explicit local regular files. Reject URLs, FIFOs, devices,
   and symlinks unless the user deliberately changes that policy.
2. Validate BED structure and the declared assembly against a trusted local
   chromosome-sizes file.
3. Bound file count, bytes, rows, workers, epochs, and output size.
4. Separate train/validation/test by patient, donor, biological replicate, or
   other independent unit—not by BED row or cell alone.
5. Inventory and checksum the universe, tokenizer, model, config, inputs,
   metadata manifest, and native binaries.
6. Obtain explicit approval before any BEDbase or Hugging Face download. Never
   infer approval from a model ID or BEDbase identifier.
7. Keep logs aggregate and bounded. BED filenames, sample IDs, phenotypes,
   labels, barcodes, and genomic intervals may be sensitive.

## Coordinate and assembly contract

BED intervals are normally **0-based, half-open** `[start, end)`: start is
included, end is excluded, and length is `end - start`. Do not mix them with
1-based closed coordinates from VCF/GFF or user-facing genome browsers.

For every corpus and artifact, record:

- assembly and patch/accession where possible (for example GRCh38 versus
  GRCh38.p14), plus the chromosome-sizes checksum;
- contig naming convention (`chr1` versus `1`), alt/random/decoy policy, and
  mitochondrial naming;
- coordinate convention, sorting order, duplicate/overlap policy, and whether
  BED strand is meaningful;
- liftover tool, chain digest, source/target assemblies, unmapped fraction, and
  post-liftover validation.

Reject negative coordinates, `end <= start`, integer overflow, unknown
contigs, ends beyond contig length, malformed columns, mixed assemblies, and
silent contig renaming. Sorting and normalization never repair an assembly
mismatch. BED3 has no strand; when column 6 is present, preserve `+`, `-`, or
`.` unless the assay contract says otherwise.

Run a bounded validation and normalization **plan** before analysis:

```bash
python skills/geniml/scripts/bed_validator.py \
  --input data/peaks.bed \
  --assembly GRCh38 \
  --chrom-sizes refs/GRCh38.chrom.sizes
```

The validator reports proposed actions but never rewrites the BED file.

## Current API map

### Region and tokenizer I/O

Prefer Gtars for new interval/tokenizer code:

```python
from gtars.models import Region, RegionSet
from gtars.tokenizers import Tokenizer

regions = RegionSet("data/peaks.bed")
tokenizer = Tokenizer.from_bed("refs/universe.bed")
encoded = tokenizer(regions)
input_ids = encoded["input_ids"]
```

`RegionSet` and `Tokenizer` also accept remote inputs in some constructors;
this skill permits local paths only unless network access is explicitly
approved. `geniml.io.RegionSet(regions, backed=False)` remains available as a
legacy Python implementation; backed sets are iterable but not indexable.
`geniml.io.Region` uses `stop`, while `gtars.models.Region` uses `end`.

With gtars 0.10.0, seven special tokens are added to a BED vocabulary. Therefore
`len(tokenizer)` is not simply the number of universe rows. Preserve universe
row order and the exact special-token map.

### Region2Vec

The modern class lives at a concrete module path:

```python
from geniml.region2vec.main import Region2VecExModel
from geniml.region2vec.utils import Region2VecDataset
from gtars.tokenizers import Tokenizer

tokenizer = Tokenizer.from_bed("refs/universe.bed")
dataset = Region2VecDataset("work/tokens.parquet", shuffle=True, convert_to_str=True)
model = Region2VecExModel(tokenizer=tokenizer, embedding_dim=100)
model.train(dataset, epochs=10, window_size=5, num_cpus=4, seed=42)
```

The Parquet input must contain one list-valued `tokens` column, one document
per row. Record token frequencies and `min_count`: in the
[

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

