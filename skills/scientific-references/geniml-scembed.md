---
id: sciref-geniml-scembed
name: "Scientific Ref: scEmbed"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (geniml): scEmbed"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "geniml scembed"
  - "scembed"
keywords:
  - "geniml"
  - "scembed"
  - "specialized"
  - "scientific"
  - "reference"
---

# scEmbed

Verified against `geniml==0.8.4` release source, current Gtars
`0.10.0`, and official BEDbase documentation on 2026-10-01.

## Scope and evidence

scEmbed learns region embeddings from scATAC-seq accessibility and pools them
to represent cells. The primary paper reports that pre-trained region
embeddings can support clustering and transfer to unseen datasets. Do not turn
that result into a universal accuracy claim; performance depends on assay,
reference corpus, universe, filtering, cell types, and split design.

Primary source: LeRoy et al. (2024), *Fast clustering and cell-type annotation
of scATAC data with pre-trained embeddings*,
doi:[10.1093/nargab/lqae073](https://doi.org/10.1093/nargab/lqae073).

## Stable API and known drift

Use:

```python
from geniml.scembed.main import ScEmbed
from geniml.region2vec.utils import Region2VecDataset
from gtars.tokenizers import Tokenizer
```

Do not use `from geniml.scembed import ScEmbed`: the 0.8.4 package
`__init__` does not export it. The installed `geniml scembed` command parses
legacy MatrixMarket options but its 0.8.4 command body does no training or
encoding.

With Geniml 0.8.4 / Gtars 0.10.0, both `tokenize_anndata` and
`ScEmbed.encode` fail: Geniml omits the required fourth `Region(..., rest)`
argument. Even after that is fixed, `ScEmbed.encode` assumes an extra nesting
level that the tokenizer does not return. Use the explicit recipe below; it
was tested on small synthetic cells, including cell-order and pooling checks.
The environment must keep AnnData 0.12.19 and Zarr 2.18.7; AnnData 0.13's
Zarr >=3 requirement conflicts with Geniml.

## AnnData contract

The AnnData object must satisfy:

- rows (`obs`) are cells;
- columns (`var`) are accessible regions/features;
- `var["chr"]`, `var["start"]`, and `var["end"]` describe each feature;
- coordinates are validated 0-based half-open BED coordinates;
- all features use one declared assembly and contig convention;
- `X` is sparse CSR for bounded tokenization performance;
- duplicate feature coordinates and duplicate barcodes have an explicit policy.

Confirm matrix orientation. A 10x peak-by-barcode MatrixMarket file is often
transposed when constructing AnnData; inspect dimensions instead of copying a
blind `.T`.

Do not expose barcodes, patient IDs, phenotypes, rare cell labels, or raw
intervals in logs. An `.h5ad` may contain identifying metadata in `obs`,
`uns`, embeddings, and file provenance. Output only bounded aggregate counts
unless the user explicitly approves disclosure.

## Leakage-safe split order

Split before fitting or selecting anything:

1. Group cells by patient/donor and biological replicate.
2. Assign complete groups to train/validation/test.
3. Fit QC thresholds, feature/universe selection, token vocabulary, model,
   annotation references, and hyperparameters on training data only.
4. Apply the frozen universe/tokenizer/model to validation and test.
5. Keep technical replicates and multiple samples from one patient together.

Randomly splitting cells from the same donor leaks donor- and batch-specific
accessibility. Building a consensus universe from all patients can also leak
test-set feature prevalence even when labels are hidden.

Audit a local manifest without printing metadata values:

```bash
python skills/geniml/scripts/corpus_auditor.py \
  --manifest data/cells.tsv \
  --group-column patient_id \
  --split-column split \
  --assembly-column assembly
```

## Build and validate the tokenizer

Use a local, checksummed universe from the training partition:

```python
from gtars.tokenizers import Tokenizer

tokenizer = Tokenizer.from_bed("refs/training_universe.bed")
```

Record:

- source cohort and split;
- assembly, chromosome sizes, coordinate/contig/strand policy;
- universe SHA-256, row order, and row count;
- Gtars version and special-token map/IDs;
- `len(tokenizer)`.

Gtars 0.10.0 `Tokenizer.from_pretrained(path)` accepts only a path argument;
it provides no revision/cache kwargs. For an authorized Hub download, fetch
the exact universe through the Hub client at a reviewed revision and build
`Tokenizer.from_bed` from those verified local bytes. A model and tokenizer
are compatible only when the exact universe,
special-token IDs, and model vocabulary size agree.

## Pre-tokenize to one bounded Parquet file

```python
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import scanpy as sc
from scipy.sparse import csr_matrix
from gtars.models import Region

adata = sc.read_h5ad("data/train.h5ad")
# Validate coordinates/assembly first; do not truncate noninteger coordinates.
adata.X = csr_matrix(adata.X)
adata.X.sum_duplicates()
adata.X.eliminate_zeros()
if not np.isfinite(adata.X.data).all() or (adata.X.data < 0).any():
    raise ValueError("accessibility must be finite and nonnegative")
features = [
    Region(chrom, int(start), int(end), None)
    for chrom, start, end in zip(adata.var["chr"], adata.var["start"], adata.var["end"])
]
cells = []
for row in range(adata.n_obs):
    indices = adata.X.indices[adata.X.indptr[row]:adata.X.indptr[row + 1]]
    ids = tokenizer([features[i] for i in indices])["input_ids"] if len(indices) else []
    cells.append(ids)
special_ids = {getattr(tokenizer, key + "_id") for key in tokenizer.special_tokens_map}
if any(not ids or special_ids.intersection(ids) for ids in cells):
    raise ValueError("empty or unmatched cells require an explicit QC policy")

table = pa.table({"tokens": pa.array(cells, type=pa.list_(pa.int32()))})
pq.write_table(table, "work/train_tokens.parquet")
```

Before writing:

- verify `len(cells) == adata.n_obs`;
- check each token list is bounded and contains IDs in
  `[0, len(tokenizer))`;
- quantify empty cells and out-of-vocabulary/unmatched features;
- preserve row correspondence in a separate protected manifest;
- do not include barcodes or labels in the training Parquet unless required.

The upstream issue
[`databio/geniml#14`](https://github.com/databio/geniml/issues/14)
(opened 2025-09-05) proposes moving away from one `.gtok` file per cell.
Prefer the single Parquet corpus for current work; treat `.gtok` as legacy.

## Train

```python
from geniml.region2vec.utils import Region2VecDataset
from geniml.scembed.main import ScEmbed

dataset = Region2VecDataset(
    "work/train_tokens.parquet",
    shuffle=True,
    convert_to_str=True,
)
model = ScEmbed(
    tokenizer=tokenizer,
    embedding_dim=100,
    pooling_method="mean",
    device="cpu",
)
model.t

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

