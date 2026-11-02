---
id: sciref-qiime2-amplicon-runtime-and-interpretation
name: "Scientific Ref: Release-pinned runtime and interpretation"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (qiime2-amplicon): Release-pinned runtime and interpretation"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "qiime2 amplicon runtime interpretation"
  - "release-pinned runtime and interpretation"
keywords:
  - "qiime2"
  - "amplicon"
  - "runtime"
  - "interpretation"
  - "specialized"
  - "scientific"
  - "reference"
  - "qiime"
  - "release"
---

# Release-pinned runtime and interpretation

## Installation and environment

This runner targets **QIIME 2 2026.7**, still the stable release selected by the official
quickstart on 2026-10-01. The official distribution image is
`quay.io/qiime2/qiime2:2026.7` (the image naming changed from earlier `amplicon` releases).
Use the official [quickstart](https://library.qiime2.org/quickstart/qiime2) for its conda environment
or container. A PyPI package with a similar name is not a replacement for the distribution's R,
DADA2 and plugin environment. On Apple Silicon, the previously tested container uses Linux amd64
emulation; official conda instructions require x86-64/Rosetta, rather than an ARM build.

For example, mount a data directory at `/data` and this skill at `/skill`, and run the Python helper
inside the container. Manifest absolute paths must be `/data/...`, not host-only paths. Ensure
enough disk space for both image download/unpacking and working artifacts; artifact creation can
copy/intermediately materialize the reads.

This installation example was checked against current documentation, not rerun during the
2026-10-01 refresh:

```bash
docker run --rm --platform linux/amd64 \
  -v "$PWD/data:/data" -v "$PWD/qiime2-amplicon:/skill:ro" \
  quay.io/qiime2/qiime2:2026.7 qiime info
```

`qiime info` and `qiime dada2 denoise-paired --help` in the target environment are the authoritative
command contract. Rolling web documentation can already describe `2026.10.0.dev0` and Python
`rachis` imports while an installed release has a different action signature. The runner uses the
CLI and release check rather than relying on rolling Python import paths. Both trimming and
DADA2 use `--output-dir`, preserving release-specific additional outputs. In 2026.7,
`feature-table summarize` takes `--m-metadata-file` and produces `--o-summary`,
`--o-feature-frequencies`, and `--o-sample-frequencies`; older tutorials using
`--m-sample-metadata-file` and `--o-visualization` do not apply to this action.
The helper checks the framework, q2cli and every used plugin's version line, rather than accepting
an unrelated occurrence of `2026.7` in the environment report. Development/mixed releases fail
preflight. This verifies reported package versions, not native-library health.

## Verified 2026.7 action contract

The 2026.7.0 plugin registrations and implementations were checked alongside rolling docs:

| Action | Contract used by this workflow |
| --- | --- |
| `tools import` | `SampleData[PairedEndSequencesWithQuality]`, format `PairedEndFastqManifestPhred33V2`; `.qza` output. The underlying V2 manifest is QIIME metadata; this helper accepts a narrower literal-path three-column profile. |
| `cutadapt trim-paired` | `demultiplexed_sequences`, IUPAC `front_f/front_r` anchored with `^`, `discard_untrimmed`, `cores`; outputs `trimmed_sequences` and `stats` (`ImmutableMetadata`). With both primers supplied, default pair filtering discards a pair if either mate is untrimmed. |
| `demux summarize` | `data` input and `visualization` output; positional quality plots sample reads, rather than verifying all per-base qualities. |
| `dada2 denoise-paired` | `demultiplexed_seqs`, positive `trunc_len_f/r`, zero `trim_left_f/r`, `min_overlap`, `n_threads`; outputs table, representative sequences, denoising stats and base-transition stats. |
| `feature-table summarize` | A pipeline accepting `table` and metadata; produces two `ImmutableMetadata` artifacts and a `summary` visualization. |
| `feature-classifier classify-sklearn` | `TaxonomicClassifier` and sequence reads, `n_jobs`; output `FeatureData[Taxonomy]`. Default confidence is 0.7; `read_orientation=auto` selects an orientation using the first 100 reads. |
| `taxa barplot` | Frequency table, taxonomy and metadata; all table feature IDs need taxonomy annotations. `barplot` remains supported; the separate `barplot2` is experimental. |
| `tools export` / `tools validate` | Export the DADA2 stats artifact to `stats.tsv`; validate each QZA with positional artifact path and `--level max`. Exports omit artifact provenance. |

The fixture additionally imports `FeatureData[Sequence]` and headerless
`FeatureData[Taxonomy]` using `HeaderlessTSVTaxonomyFormat`, then calls
`feature-classifier fit-classifier-naive-bayes` with `reference_reads` and `reference_taxonomy`
to produce a `TaxonomicClassifier`. These are local CLI/plugin APIs, not hosted analysis endpoints.

Defaults matter: the runner inherits Cutadapt error rate 0.1, indel matching, one removal pass and
no quality trimming; DADA2 uses maximum expected errors 2 per mate, `trunc_q=2`, independent
denoising, consensus chimera removal, zero merge mismatches and `retain_unmerged=False`.
DADA2's minimum overlap API permits 4 or more bases, but this helper deliberately requires at
least 12. `retain_unmerged=True` produces linked sequences and adds concatenated counts; those
are outside this helper's merged-ASV retention contract. Samples with zero retained frequency
remain represented by the default `retain_all_samples=True`. The official distribution pins
Cutadapt 5.2, R 4.5.2 and DADA2 1.38.0; do not independently upgrade them in the pinned environment.

## Classifiers and provenance

Supply a trusted `TaxonomicClassifier` with suitable database coverage, training choices and
compatible QIIME/scikit-learn environment. Full-length training is supported; the official resource
page no longer requires region-specific classifiers. Record database citation, any region extraction primers,
training parameters, confidence threshold, source URL, artifact UUID and SHA-256. Keep the training
artifact lineage when available. QIIME's ZIP/schema validation does not establish the safety of an
untrusted serialized sklearn model.

If no matching classifier exists, train within the target distribution from an appropriate curated
reference sequence/taxonomy pair using its feature-classifier actions. A classifier trained on a
tiny test reference only validates execution and label plumbing; it says nothing about taxonomic
accuracy on biological samples. Do not silently substitute such a test reference for a real database.

The resulting QZA files preserve QIIME action provenance. `commands.json` supplements this with
actual CLI arguments; the runner also records release information and hashes. Copying only exported
FASTA/TSV/BIOM loses the artifact provenance graph. Retain the original FASTQs and classifier.

## Read retention and assay inte

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

