---
id: sci-deeptools
name: "Scientific: deeptools"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "NGS analysis toolkit. BAM to bigWig conversion, QC (correlation, PCA, fingerprints), heatmaps/profiles (TSS, peaks), for ChIP-seq, RNA-seq, ATAC-seq visualization."
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "deeptools"
keywords:
  - "deeptools"
  - "analysis"
  - "toolkit"
  - "bigwig"
  - "conversion"
  - "correlation"
  - "fingerprints"
---

# deepTools: NGS Data Analysis Toolkit

## Overview

deepTools is a comprehensive suite of Python command-line tools designed for processing and analyzing high-throughput sequencing data. Use deepTools to perform quality control, normalize data, compare samples, and generate publication-quality visualizations for ChIP-seq, RNA-seq, ATAC-seq, MNase-seq, and other NGS experiments.

**Core capabilities:**
- Convert BAM alignments to normalized coverage tracks (bigWig/bedGraph)
- Quality control assessment (fingerprint, correlation, coverage)
- Sample comparison and correlation analysis
- Heatmap and profile plot generation around genomic features
- Enrichment analysis and peak region visualization

## When to Use This Skill

This skill should be used when:

- **File conversion**: "Convert BAM to bigWig", "generate coverage tracks", "normalize ChIP-seq data"
- **Quality control**: "check ChIP quality", "compare replicates", "assess sequencing depth", "QC analysis"
- **Visualization**: "create heatmap around TSS", "plot ChIP signal", "visualize enrichment", "generate profile plot"
- **Sample comparison**: "compare treatment vs control", "correlate samples", "PCA analysis"
- **Analysis workflows**: "analyze ChIP-seq data", "RNA-seq coverage", "ATAC-seq analysis", "complete workflow"
- **Working with specific file types**: BAM files, bigWig files, BED region files in genomics context

## Quick Start

For users new to deepTools, start with file validation and common workflows:

### 1. Validate Input Files

Before running any analysis, validate BAM, bigWig, and BED files using the validation script:

```bash
python scripts/validate_files.py --bam sample1.bam sample2.bam --bed regions.bed
```

This checks local files, readable BAM/BAI/CSI structure and coordinate order, bigWig headers, and every BED row. It does not establish assembly identity or biological suitability.

### 2. Generate Workflow Template

For standard analyses, use the workflow generator to create customized scripts:

```bash
# List available workflows
python scripts/workflow_generator.py --list

# Generate ChIP-seq QC workflow
python scripts/workflow_generator.py chipseq_qc -o qc_workflow.sh \
    --input-bam Input.bam --chip-bams "ChIP1.bam ChIP2.bam"

# Make executable and run
chmod +x qc_workflow.sh
./qc_workflow.sh
```

### 3. Most Common Operations

See `assets/quick_reference.md` for frequently used commands and parameters.

## Installation

```bash
uv venv --python 3.13 .venv-deeptools
uv pip install --python .venv-deeptools/bin/python deepTools==4.0.0
source .venv-deeptools/bin/activate
bamCoverage --version
```

Upstream recommends conda/bioconda for full dependency resolution, especially on shared HPC systems:

```bash
conda create -n deeptools -c conda-forge -c bioconda python=3.13 deeptools=4.0.0 samtools
```

The 4.0.0 PyPI release includes native macOS Intel/Apple Silicon and Linux wheels. Conda availability varies by platform; the PyPI workflow above was exercised on macOS.

**4.0 migration:** The five rewritten commands use Rust. `bamCoverage`, `bamCompare`, and `multiBamSummary` no longer accept `--ignoreDuplicates`; use `--samFlagExclude 1024` only after duplicate marking. `bamCompare` no longer accepts SES. Its released Rust backend accepts RPGC despite a contradictory rolling-doc note; several advertised operations are incorrect (see review). `--exactScaling` is removed from the rewritten coverage commands because scaling now uses all reads. See [references/review.md](references/review.md) for verified contracts and remaining limits.

## Core Workflows and Tool Categories

Complete command sequences for ChIP-seq QC, full ChIP-seq analysis, RNA-seq coverage, and
ATAC-seq analysis — plus the BAM/bigWig processing, quality control, and visualization
tool categories — are in [references/core_workflows.md](references/core_workflows.md) and
[references/workflows.md](references/workflows.md). Per-tool options are in
[references/tools_reference.md](references/tools_reference.md).

## Normalization Methods

Choosing the correct normalization is critical for valid comparisons. Consult `references/normalization_methods.md` for comprehensive guidance.

**Quick selection guide:**

- **ChIP-seq coverage**: Use RPGC or CPM
- **ChIP-seq comparison**: Use bamCompare with log2 and readCount
- **RNA-seq bins**: Use CPM
- **RNA-seq genes**: Quantify with an annotation-aware gene/transcript workflow; bamCoverage RPKM scales genomic bins, not genes
- **ATAC-seq**: Use CPM for the shifted-alignment template; RPGC without extension failed on shifted BAMs in 4.0.0

**Normalization methods:**
- **RPGC**: 1× genome coverage (requires --effectiveGenomeSize)
- **CPM**: Counts per million mapped reads
- **RPKM**: Reads per kb per million (per-bin length and library-size scaling)
- **BPM**: The released 4.0.0 Rust implementation reduces to CPM; do not interpret it as gene TPM
- **None**: Raw counts (not recommended for comparisons)

Full explanation: `references/normalization_methods.md`

## Effective Genome Sizes

RPGC normalization requires effective genome size. Examples from the **4.0.0 tagged source**, not universal assembly constants (the rolling documentation differs):

| Organism | Assembly | Size | Usage |
|----------|----------|------|-------|
| Human | GRCh38/hg38 | 2,913,022,398 | `--effectiveGenomeSize 2913022398` |
| Human | T2T/CHM13CAT_v2 | 3,117,292,070 | `--effectiveGenomeSize 3117292070` |
| Mouse | GRCm39/mm39 | 2,654,621,783 | `--effectiveGenomeSize 2654621783` |
| Mouse | GRCm38/mm10 | 2,652,783,500 | `--effectiveGenomeSize 2652783500` |
| Zebrafish | GRCz11 | 1,368,780,147 | `--effectiveGenomeSize 1368780147` |
| *Drosophila* | dm6 | 142,573,017 | `--effectiveGenomeSize 142573017` |
| *C. elegans* | WBcel235/ce11 | 100,286,401 | `--effectiveGenomeSize 100286401` |

Verify the exact FASTA, contig set, and mapping/filter policy before choosing a value. Details: `references/effective_genome_sizes.md`

## Common Parameters Across Tools

Many deepTools commands share these options:

**Performance:**
- `--numberOfProcessors, -p`: Use the CPU allocation allowed by your scheduler
- `max` / `max/2`: Supported values for `--numberOfProcessors`; useful under schedulers because recent deepTools releases detect CPU affinity more carefully
- `--region`: Process specific regions for testing (e.g., `chr1:1:1000000`)

**Read Filtering:**
- `--samFlagExclude 1024`: Exclude alignments already marked duplicate (0x400); does not

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

