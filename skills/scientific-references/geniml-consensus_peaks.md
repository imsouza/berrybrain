---
id: sciref-geniml-consensus-peaks
name: "Scientific Ref: Consensus peaks and universe assessment"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (geniml): Consensus peaks and universe assessment"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "geniml consensus peaks"
  - "consensus peaks and universe assessment"
keywords:
  - "geniml"
  - "consensus"
  - "peaks"
  - "specialized"
  - "scientific"
  - "reference"
---

# Consensus peaks and universe assessment

Verified against `geniml==0.8.4` release source and official BEDbase
documentation on 2026-10-01.

## Method scope

A Geniml universe is a reference interval vocabulary derived from coverage
across a collection of BED files. Release 0.8.4 implements:

- **CC**: coverage cutoff;
- **CCF**: coverage cutoff with flexible core/boundary fields;
- **ML**: maximum-likelihood flexible universe;
- **HMM**: hidden-state model over start/core/end coverage.

Primary source: Rymuza et al. (2024), *Methods for constructing and evaluating
consensus genomic interval sets*,
doi:[10.1093/nar/gkae685](https://doi.org/10.1093/nar/gkae685).

The paper motivates and evaluates these methods; it does not make one method
universally best. Choose using training-only data, assay-specific validation,
resource constraints, and held-out universe-fit metrics.

## Non-negotiable input contract

All source BED files and chromosome sizes must agree on:

- assembly/accession and patch;
- 0-based half-open BED coordinates;
- chromosome/contig naming and inclusion policy;
- sort order;
- duplicate and overlap handling;
- strand interpretation;
- liftover provenance, if any.

Reject malformed rows, negative starts, `end <= start`, coordinates beyond
contig length, unknown contigs, mixed assemblies, and integer overflow before
coverage generation. A chromosome name match alone is not proof of assembly
compatibility.

Build the universe only from the training patients/donors. If samples from a
held-out patient contribute to coverage, the resulting vocabulary leaks test
feature prevalence.

```bash
python skills/geniml/scripts/corpus_auditor.py \
  --manifest data/train_manifest.tsv \
  --group-column patient_id \
  --split-column split \
  --assembly-column assembly
```

## Coverage prerequisites

Geniml consumes bigWig tracks in a local coverage directory. With the default
prefix `all`, methods expect:

```text
all_start.bw
all_core.bw
all_end.bw
```

CC and CCF read `all_core.bw`. HMM and likelihood-based methods use
start/core/end tracks. The tracks must share contigs and lengths with the
checksummed chromosome-sizes file. CC, CCF, and HMM cast coverage to uint16:
require finite nonnegative integer counts no greater than 65,535. Fractional
coverage is truncated and larger counts can wrap. Do not feed normalized
BigWigs into these methods without verifying the required count semantics.

Official Geniml pages describe producing these tracks with the ecosystem's
coverage tooling, but the current Gtars CLI has changed across releases. Do not
emit or run a guessed `uniwig` command. Pin the exact Gtars/uniwig executable,
capture its `--help`, and smoke-test its output naming on synthetic local BED
data. Record:

- tool version and binary SHA-256;
- complete argv (not a shell-expanded wildcard);
- chromosome-sizes SHA-256;
- ordered input manifest and checksums;
- smoothing/binning parameters;
- output track sizes, contigs, lengths, and checksums.

The bundled planner validates local inputs and emits the Geniml stage, but
intentionally marks coverage generation as an external prerequisite:

```bash
python skills/geniml/scripts/consensus_plan.py \
  --manifest data/train_manifest.tsv \
  --chrom-sizes refs/GRCh38.chrom.sizes \
  --assembly GRCh38 \
  --method cc \
  --cutoff 2 \
  --output-dir work/consensus
```

It does not execute Geniml, Gtars, native binaries, or network requests.

## Exact 0.8.4 CLI

All shown CLI forms were checked against installed help. CC was executed on a
synthetic BigWig; CCF, likelihood/ML, HMM, and assessment are source-verified
illustrative templates, not completed end-to-end workflows in this review.

The top-level command is `build-universe`, not `universe build`.

### CC

```bash
geniml build-universe cc \
  --coverage-folder /absolute/project/coverage \
  --coverage-prefix all \
  --output-file /absolute/project/universe_cc.bed \
  --cutoff 2 \
  --merge 100 \
  --filter-size 50
```

`--cutoff` is an integer. If omitted, release source uses mean base coverage
for each chromosome. `--merge` merges nearby output segments; `--filter-size`
removes shorter segments. The output file must not already exist.
A tiny count-track smoke produced the exact expected BED interval. In contrast,
all-zero selected positions, 0.5-valued tracks, and 65,536-valued tracks
reproduced empty-selection IndexError failures. The release can leave partial
output if a later chromosome fails; reconcile every requested chromosome.

`merge=0, filter_size>0` enters the merging implementation and can split
adjacent covered bases into individual bases. Until that upstream behavior is
corrected, build with both zero and perform a separately validated BED
length-filter/merge step when precise gap semantics matter.

Do not claim `cutoff=number_of_files` is a strict sample intersection unless
coverage generation contributes exactly one unit per sample at each base.
Fragment/read coverage or duplicated intervals can violate that assumption.

Python:

```python
from geniml.universe.cc_universe import cc_universe

cc_universe(
    cove="work/coverage",
    file_out="work/universe_cc.bed",
    cove_prefix="all",
    merge=100,
    filter_size=50,
    cutoff=2,
)
```

### CCF

```bash
geniml build-universe ccf \
  --coverage-folder /absolute/project/coverage \
  --coverage-prefix all \
  --output-file /absolute/project/universe_ccf.bed
```

Python:

```python
from geniml.universe.ccf_universe import ccf_universe

ccf_universe(
    cove="work/coverage",
    file_out="work/universe_ccf.bed",
    cove_prefix="all",
)
```

The stable source has no CCF `--confidence`, `--merge`, or `--filter-size`
arguments. CCF writes BED9-like rows carrying core/boundary information; do
not reduce them to BED3 before confirming downstream semantics.

### Likelihood model and ML universe

The 0.8.4 likelihood command has no `build_model` subcommand:

```bash
geniml lh \
  --model-file /absolute/project/model.tar \
  --coverage-folder /absolute/project/coverage \
  --coverage-prefix all \
  --file-no 4
```

Then:

```bash
geniml build-universe ml \
  --model-file /absolute/project/model.tar \
  --coverage-folder /absolute/project/coverage \
  --coverage-prefix all \
  --output-file /absolute/project/universe_ml.bed
```

Python:

```python
from geniml.likelihood.build_model import main as build_likelihood
from geniml.universe.ml_universe import ml_universe

build_likelihood(
    model_file="work/model.tar",
    

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

