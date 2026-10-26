---
id: sciref-bulk-rnaseq-upstream-nfcore
name: "Scientific Ref: Path A — nf-core/rnaseq"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (bulk-rnaseq): Path A — nf-core/rnaseq"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "bulk rnaseq upstream nfcore"
  - "path a — nf-core/rnaseq"
keywords:
  - "bulk"
  - "rnaseq"
  - "upstream"
  - "nfcore"
  - "specialized"
  - "scientific"
  - "reference"
  - "path"
---

# Path A — nf-core/rnaseq

`nf-core/rnaseq` is the field-standard, community-audited pipeline for the reads → counts stage. It chains FastQC → trimming (Trim Galore or fastp) → optional contaminant/rRNA removal → alignment + quantification (STAR+Salmon, STAR+RSEM, or HISAT2) → tximport gene/transcript count merging → extensive QC → MultiQC, with reviewed defaults and per-process containers.

This file covers *how to run it and what comes out*. For the Nextflow engine itself — profiles, executors, containers (Docker/Singularity/Conda/Wave), HPC/cloud, `-resume` caching, offline/`nf-core pipelines download` — use the **`nextflow`** skill. Don't duplicate that here.

Documentation/schema reviewed 2026-09-30; recipes are illustrative, not a full pipeline execution. Current stable revision: **3.27.0** (always pin with `-r`).

## Samplesheet

`nf-core/rnaseq` takes a CSV, not loose files. The first four headers are required in this order; `fastq_2` may be empty for single-end data:

```csv
sample,fastq_1,fastq_2,strandedness
CONTROL_REP1,/data/ctrl1_R1.fastq.gz,/data/ctrl1_R2.fastq.gz,auto
CONTROL_REP2,/data/ctrl2_R1.fastq.gz,/data/ctrl2_R2.fastq.gz,auto
TREATED_REP1,/data/trt1_R1.fastq.gz,/data/trt1_R2.fastq.gz,auto
TREATED_REP2,/data/trt2_R1.fastq.gz,/data/trt2_R2.fastq.gz,auto
```

- **sample** — sample ID. Rows that share a `sample` value are treated as the same sample sequenced over multiple lanes and are merged.
- **fastq_1 / fastq_2** — paths or URLs to gzipped FASTQ. Leave `fastq_2` empty for single-end.
- **strandedness** — `auto` (recommended; the pipeline infers it with Salmon and warns on mismatch), or `forward` / `reverse` / `unstranded` if you know the kit. TruSeq stranded mRNA is typically `reverse`.

Validate before launching: `python scripts/validate_samplesheet.py --samplesheet samplesheet.csv --nfcore`.

## Choosing the aligner / quantifier

Set with `--aligner` (genome alignment) or `--pseudo_aligner` (lightweight). Defaults are well chosen.

| Option | What it does | When |
|--------|--------------|------|
| `--aligner star_salmon` (default) | STAR genome alignment, Salmon quantifies against the transcriptome from the BAM | The standard, defensible default — gives counts **and** a genome BAM for QC/IGV |
| `--aligner star_rsem` | STAR + RSEM | You specifically need RSEM estimates |
| `--aligner bowtie2_salmon` | Bowtie2 transcriptome alignment + Salmon | When that alignment route is required |
| `--aligner hisat2` | HISAT2 alignment (no built-in transcript quant) | Lower memory than STAR |
| `--pseudo_aligner salmon` (+ `--skip_alignment`) | Salmon reads-based selective alignment, no BAM | Fastest/lightest; you don't need a genome BAM |

`star_salmon` is recommended unless you have a specific reason otherwise. You can also add `--pseudo_aligner salmon` alongside an aligner to get both.

## Running

```bash
# Smoke-test first (tiny bundled data; proves the environment works)
nextflow run nf-core/rnaseq -r 3.27.0 -profile test,docker --outdir test_results

# Real run with an iGenomes reference key
nextflow run nf-core/rnaseq -r 3.27.0 \
  -profile docker \
  --input samplesheet.csv \
  --genome GRCh38 \
  --aligner star_salmon \
  --outdir results \
  -resume

# Or supply your own reference explicitly (more reproducible than iGenomes keys)
nextflow run nf-core/rnaseq -r 3.27.0 \
  -profile singularity \
  --input samplesheet.csv \
  --fasta /ref/genome.fa --gtf /ref/annotation.gtf \
  --aligner star_salmon --outdir results -resume
```

Generate a validated, documented command + params file interactively with `nf-core pipelines launch rnaseq` (see the `nextflow` skill).

### Useful parameters

- `--save_reference` — keep the built STAR/Salmon indices so re-runs and other projects don't rebuild them.
- `--trimmer trimgalore|fastp` — trimming tool (default `trimgalore`).
- `--remove_ribo_rna` — sortmerna rRNA depletion (use if libraries weren't poly-A/ribo-depleted, or to quantify rRNA contamination).
- `--extra_salmon_quant_args='--gcBias'` — pass tool flags through.
- `--skip_*` (e.g. `--skip_markduplicates`, `--skip_stringtie`) — drop stages you don't need.
- `--gencode` — set when using GENCODE (not Ensembl) annotation, so gene IDs/biotypes parse correctly.

Pick the reference release deliberately and record it. iGenomes keys (`--genome GRCh38`) are convenient but version-pinning your own `--fasta`/`--gtf` is more reproducible.

## Outputs

Key paths under `--outdir` (for `star_salmon`):

```
results/
├── multiqc/             # MultiQC report — read this first
├── star_salmon/
│   ├── salmon.merged.gene_counts.tsv                 # raw estimated gene counts (tximport, countsFromAbundance=no)
│   ├── salmon.merged.gene_counts_length_scaled.tsv   # length-scaled counts -> use for DESeq2
│   ├── salmon.merged.gene_tpm.tsv                     # TPM (for visualization, NOT for DESeq2)
│   ├── salmon.merged.gene.SummarizedExperiment.rds                  # SummarizedExperiment (R)
│   ├── <SAMPLE>/                                      # per-sample Salmon quant dirs
│   └── deseq2_qc/                                     # PCA + sample-distance plots the pipeline already made
└── pipeline_info/        # execution report, software versions, params
```

**The pipeline already runs tximport**, so on Path A you do **not** need this skill's `build_counts_matrix.py`. Use the merged TSV directly. This assumes `--skip_quantification_merge` is false:
that mode omits length-scaled merged counts and DESeq2 QC. Preserve the emitted
`salmon.merged.tx2gene_augmented.tsv` to reproduce the actual import; it can contain
self-mappings for orphan transcripts, which must not be mistaken for genuine gene IDs.

## Handoff to PyDESeq2

`salmon.merged.gene_counts_length_scaled.tsv` is genes × samples, with a leading `gene_id` (and usually `gene_name`) column, and non-integer values. Round to integers for PyDESeq2:

```python
import pandas as pd

df = pd.read_csv("results/star_salmon/salmon.merged.gene_counts_length_scaled.tsv", sep="\t")
df = df.drop(columns=[c for c in ["gene_name"] if c in df.columns]).set_index("gene_id")
assert df.index.is_unique and df.columns.is_unique
assert not df.empty and df.notna().all().all()
assert (df >= 0).all().all() and (df < float("inf")).all().all()
counts = df.round().astype("int64")          # genes x samples, integer
counts.to_csv("counts.csv")              # hand to the pydeseq2 skill (it transposes to samples x genes)
```

Build `metadata.csv` (index = sam

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

