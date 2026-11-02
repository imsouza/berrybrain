---
id: sciref-alphagenome-model-api
name: "Scientific Ref: AlphaGenome model API (`alphagenome.models.dna_client`)"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (alphagenome): AlphaGenome model API (`alphagenome.models.dna_client`)"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "alphagenome model api"
  - "alphagenome model api (`alphagenome.models.dna_client`)"
keywords:
  - "alphagenome"
  - "model"
  - "api"
  - "specialized"
  - "scientific"
  - "reference"
---

# AlphaGenome model API (`alphagenome.models.dna_client`)

Reviewed 2026-09-30 against released `alphagenome` 0.9.0, the current official
SDK source, scoring definitions, and research implementation. Network examples
are illustrative; local SDK/plotting contracts were exercised without a key. The client is a thin gRPC wrapper: no
weights, no GPU, one API key. The same key serves the Atlas.

## Setup

```bash
uv pip install alphagenome            # PyPI; Python >= 3.10, tested here on 3.12 and 3.13
export ALPHAGENOME_API_KEY=...        # https://deepmind.google.com/science/alphagenome
```

```python
import os
from alphagenome.data import gene_annotation, genome, transcript
from alphagenome.models import dna_client, variant_scorers
from alphagenome.visualization import plot_components

dna_model = dna_client.create(os.environ["ALPHAGENOME_API_KEY"], timeout=30)
```

`alphagenome.colab_utils.get_api_key()` reads `ALPHA_GENOME_API_KEY` (note the
underscore) or a Colab secret of that name. The scripts here accept both.

## Coordinates and inputs

| Object | Convention |
| --- | --- |
| `genome.Interval(chromosome, start, end, strand='.')` | **0-based, half-open** |
| `genome.Variant(chromosome, position, reference_bases, alternate_bases, name='')` | **1-based** position, VCF-style anchored alleles |
| `genome.Variant.from_str("chr22:36201698:A>C")` | adds `chr` if missing; `VariantFormat.GNOMAD` (`22-1024-A-C`), `GTEX` (`chr22_1024_A_C_b38`), `OPEN_TARGETS` (`22_1024_A_C`), `OPEN_TARGETS_BIGQUERY` (`22:1024:A:C`) |
| `variant.reference_interval.resize(width)` | the usual way to build the model window around a variant |
| Human | hg38 (GRCh38.p13) |
| Mouse | mm10 (GRCm38.p6), `organism=dna_client.Organism.MUS_MUSCULUS` |

Supported input widths (`dna_client.SUPPORTED_SEQUENCE_LENGTHS`):

| Name | bp | Use |
| --- | --- | --- |
| `SEQUENCE_LENGTH_16KB` | 16,384 | ISM scans, fast iteration |
| `SEQUENCE_LENGTH_100KB` | 131,072 | |
| `SEQUENCE_LENGTH_500KB` | 524,288 | |
| `SEQUENCE_LENGTH_1MB` | 1,048,576 | default; best accuracy and full distal context; ContactMapScorer uses a 1 Mb mask |

Any other width raises. Sequences may contain `N` (pad with `'N'` for short
constructs: `seq.center(dna_client.SEQUENCE_LENGTH_1MB, 'N')`). 2 kb inputs were
removed in 0.5.0.

## Output types (`dna_client.OutputType`)

| Type | Signal | Resolution | Human tracks |
| --- | --- | --- | --- |
| `ATAC`, `DNASE` | chromatin accessibility | 1 bp | 167 / 305 |
| `CHIP_TF` | TF binding ChIP-seq | 128 bp | 1,617 |
| `CHIP_HISTONE` | histone marks | 128 bp | 1,116 |
| `CAGE`, `PROCAP` | transcription initiation (5' ends) | 1 bp | 546 / 12 (PROCAP human only) |
| `RNA_SEQ` | stranded coverage | 1 bp | 667 |
| `SPLICE_SITES` | donor/acceptor probability | 1 bp | 4 (donor/acceptor on each strand; 2 after gene-score merging) |
| `SPLICE_SITE_USAGE` | fraction of transcripts using each site | 1 bp | 734 |
| `SPLICE_JUNCTIONS` | split-read counts per junction | junction | 734 |
| `CONTACT_MAPS` | log-fold contact signal over genomic-distance expectation | 2,048 bp bins | 28 |

These are the published human output counts (5,930 including junction tracks),
not the strand-merged scorer counts in the Atlas. Query metadata for the
actual organism and release; metadata fields vary by output type. Track rows carry `name`, `strand`,
`ontology_curie`, `biosample_name`, `biosample_type`, plus `gtex_tissue`
(RNA_SEQ, SPLICE_*), `transcription_factor` (CHIP_TF), `histone_mark`
(CHIP_HISTONE). Discover them with:

```python
meta = dna_model.output_metadata(dna_client.Organism.HOMO_SAPIENS)
df = meta.concatenate()                      # every output type in one DataFrame
df[df.biosample_name.str.contains("liver", case=False)][["output_type", "name", "ontology_curie", "biosample_name"]]
```

or `python scripts/score_variants.py --list-tracks --query liver -o tracks.tsv`.

Ontology terms are CURIEs: `UBERON:0002048` (lung), `UBERON:0001157` (colon,
transverse), `UBERON:0001114` (right liver lobe), `CL:0000084` (T cell),
`CL:0000236` (B cell), `EFO:0002067` (K562), `CLO:...` for cell lines.
Passing `ontology_terms=None` returns every track. The `ontology-term-resolution`
skill turns free text into validated CURIEs; then confirm the term exists in
`output_metadata`, because the model only has tracks for its training biosamples.

## Predictions

```python
interval = genome.Interval("chr22", 36_201_698 - 2**19, 36_201_698 + 2**19)   # 1 Mb

out = dna_model.predict_interval(
    interval=interval,
    requested_outputs=[dna_client.OutputType.RNA_SEQ, dna_client.OutputType.DNASE],
    ontology_terms=["UBERON:0001157"],
)
out.rna_seq.values.shape          # (1048576, n_tracks)  float32
out.rna_seq.metadata              # track DataFrame
out.rna_seq.interval, out.rna_seq.resolution

variant = genome.Variant.from_str("chr22:36201698:A>C")
vo = dna_model.predict_variant(
    interval=variant.reference_interval.resize(dna_client.SEQUENCE_LENGTH_1MB),
    variant=variant,
    requested_outputs=[dna_client.OutputType.RNA_SEQ],
    ontology_terms=["UBERON:0001157"],
)
vo.reference.rna_seq, vo.alternate.rna_seq     # TrackData for REF and ALT haplotypes

# Illustrative synthetic input, with lower reliability than near-reference DNA.
out = dna_model.predict_sequence(
    sequence="ACGT" * (dna_client.SEQUENCE_LENGTH_16KB // 4),
    requested_outputs=[dna_client.OutputType.DNASE], ontology_terms=["UBERON:0001157"],
)
```

`predict_variants` / `predict_intervals` / `predict_sequences` take lists and run
in parallel (`max_workers`, default 5). `TrackData` supports
`filter_to_positive_strand()`, `select_tracks_by_name()`, `slice_by_interval()`,
`resize()`, `change_resolution()`, `reverse_complement()`, and NumPy-style
`tdata[interval, mask]` indexing.

## Variant scoring

```python
scorers = list(variant_scorers.RECOMMENDED_VARIANT_SCORERS.values())    # 19 configurations
adatas = dna_model.score_variant(interval, variant, variant_scorers=scorers)   # list[AnnData], one per scorer
df = variant_scorers.tidy_scores(adatas, match_gene_strand=True)          # long DataFrame
df[["variant_id", "output_type", "variant_scorer", "gene_name", "biosample_name",
    "ontology_curie", "raw_score", "quantile_score"]]

# many variants, same window size
adatas = dna_model.score_variants(
    [v.reference_interval.resize(dna_client.SEQUENCE_LENGTH_1MB) for v in variants],
    variants, scorers, organism=dna_client.Organism.HOMO_SAPIENS, max_workers=5)
df = variant_s

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

