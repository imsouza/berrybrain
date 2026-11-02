---
id: sciref-geniml-utilities
name: "Scientific Ref: I/O, tokenization, caches, evaluation, and security"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (geniml): I/O, tokenization, caches, evaluation, and security"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "geniml utilities"
  - "i/o, tokenization, caches, evaluation, and security"
keywords:
  - "geniml"
  - "utilities"
  - "specialized"
  - "scientific"
  - "reference"
  - "tokenization"
  - "caches"
---

# I/O, tokenization, caches, evaluation, and security

Research snapshot: 2026-10-01. API claims below use official documentation,
PyPI metadata, and the `geniml` v0.8.4 release source. Where current docs and
release code disagree, the discrepancy is stated explicitly.

## Release and dependency facts

`geniml==0.8.4` was released on 2026-01-14. PyPI metadata:

- does not set `Requires-Python`;
- classifies Python 3.10, 3.11, 3.12, 3.13, and 3.14;
- provides `ml` and `test` extras;
- ships a pure-Python wheel, but dependencies include native packages;
- uses Trusted Publishing with a Sigstore provenance link to tag `v0.8.4`.

Release files:

```text
geniml-0.8.4-py3-none-any.whl
sha256 ac0fc520cde6f6461120aee6b40d3cbf20e1e3d8bdb95a3a45345724eee545b5

geniml-0.8.4.tar.gz
sha256 6f429c7c89d06a4c2c378e349d14b3a2d984dc441440ada38473772fce6addb1
```

The stable release requires `gtars>=0.2.5` without an upper bound. The
2026-10-01 synthetic CPU checks used `gtars==0.10.0`, Python 3.12,
AnnData 0.12.19, Scanpy 1.12.4, Zarr 2.18.7, Gensim 4.4.0, Torch 2.14.1,
PyArrow 25.0.1, NumPy 2.5.3, pandas 2.3.3, and Hugging Face Hub 2.0.0.
They exercised Region2Vec/scEmbed training, explicit token/cell pooling,
local bundles, CC construction, and local BED/token caches. Gtars 0.10.0 was released 2026-09-05 and requires
Python >=3.10.

Pin the tested stack and retain `uv.lock`; upstream transitive requirements
are mostly lower bounds. Geniml's Zarr <3 constraint is incompatible with
AnnData 0.13 (Zarr >=3). AnnData 0.12.19 works with the tested Zarr 2.18.7.
The full ml extra resolves but brings additional old pinned components;
it was resolver-checked only, unlike the selective stack above.

## BED coordinates and validation

BED is normally 0-based, half-open `[start, end)`. A valid BED3 row requires:

- nonempty contig;
- integer `start >= 0`;
- integer `end > start`;
- `end` no greater than the declared contig length;
- values within bounded integer limits.

Do not confuse BED with 1-based closed VCF/GFF coordinates. BED columns beyond
BED3 have their own constraints; preserve them rather than guessing.
BED3 carries no strand. When BED6 strand exists, preserve `+`, `-`, or `.`
unless a documented assay conversion says otherwise.

Assembly compatibility requires more than matching `chr` prefixes. BEDbase
describes chromosome-name sensitivity (XS), out-of-bounds regions (OOBR), and
sequence fit (SF) as separate criteria. Record a concrete assembly/accession
and chromosome-sizes digest. Reject unknown alt/decoy contigs rather than
dropping them silently.

Run:

```bash
python skills/geniml/scripts/bed_validator.py \
  --input data/peaks.bed \
  --assembly GRCh38 \
  --chrom-sizes refs/GRCh38.chrom.sizes
```

The script emits aggregate errors and a normalization plan. It never rewrites
coordinates or performs liftover.

## Region and RegionSet APIs

### Gtars API for new workflows

```python
from gtars.models import Region, RegionSet

region = Region("chr1", 100, 200, None)
regions = RegionSet("data/peaks.bed")
print(len(regions))
regions.to_bed("work/peaks.copy.bed")
```

Gtars 0.10.0 requires the fourth `Region` constructor argument (`rest`),
including `None` for BED3. It exposes operations including `sort`, `reduce`, `coverage`,
`count_overlaps`, `jaccard`, `nearest_neighbors`, `to_bed`, `to_bed_gz`, and
`to_bigbed`. Do not assume these operations validate assembly or coordinate
semantics. Validate before constructing the object and after writing output.

Official Gtars constructors can accept URLs. This skill restricts them to
validated local regular files by default.

### Legacy Geniml I/O

```python
from geniml.io import BedSet, Region, RegionSet

region = Region("chr1", 100, 200)  # third field is named stop
regions = RegionSet("data/peaks.bed", backed=False)
```

`geniml.io.RegionSet(regions, backed=False)` accepts a path/URL or a list of
legacy Regions. With `backed=True`, it streams the BED, supports iteration and
length, and does not support indexing. Other release classes include `BedSet`,
`Maf`, `SNP`, `TokenizedRegionSet`, and `RegionSetCollection`, though only
`Region`, `RegionSet`, and `BedSet` are exported from `geniml.io`.

The 0.7.0 changelog says RegionSet use switched toward Gtars. Avoid mixing
legacy and Gtars Region objects accidentally: field names and accepted types
differ.

## Tokenization

### Current Gtars tokenizer

```python
from gtars.models import RegionSet
from gtars.tokenizers import Tokenizer

tokenizer = Tokenizer.from_bed("refs/universe.bed")
encoded = tokenizer(RegionSet("data/peaks.bed"))
input_ids = encoded["input_ids"]
```

Gtars exposes `Tokenizer.from_config(cfg)` and
`Tokenizer.from_pretrained(path)`. The latter can access Hugging Face and has
no revision/cache kwargs. For authorized downloads, use the Hub client with
an immutable revision, then `Tokenizer.from_bed` on verified local bytes.

With Gtars 0.10.0, a two-region universe produced `len(tokenizer) == 9` because
seven special tokens are included. Preserve:

- universe bytes, row order, and assembly;
- Gtars version;
- `special_tokens_map` and every special-token ID;
- tokenizer length;
- token-corpus schema and checksum.

Run the local compatibility planner:

```bash
python skills/geniml/scripts/tokenizer_compatibility.py \
  --model-dir models/region2vec \
  --universe refs/universe.bed \
  --assembly GRCh38
```

### Legacy hard tokenization

The stable file `geniml.tokenization.main` defines:

```python
hard_tokenization_main(
    src_folder,
    dst_folder,
    universe_file,
    fraction=1e-9,
    file_list=None,
    num_workers=10,
    bedtools_path="bedtools",
)
```

It invokes an external Bedtools executable and multiprocessing. The
`fraction` is passed to interval intersection logic; it is **not a statistical
p-value**. The package `geniml.tokenization.__init__` comments out its public
exports, so `from geniml.tokenization import hard_tokenization` and the
installed `geniml tokenize` dispatcher are unreliable in 0.8.4.

Do not use an arbitrary `bedtools` found on `PATH`. If reproducing the legacy
path, pin and checksum the binary, pass an explicit absolute path, validate
argv, bound workers, use a fresh output directory, and compare synthetic
results with the Gtars tokenizer.

The current preferred token corpus is a bounded Parquet file with one
list-valued `tokens` column. Upstream issue #14 proposes deprecating one
`.gtok` file per cell.

## BBClient and cache behavior

```python
from g

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

