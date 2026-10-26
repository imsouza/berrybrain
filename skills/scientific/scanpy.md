---
id: sci-scanpy
name: "Scientific: scanpy"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Performs Scanpy single-cell RNA-seq QC, normalization, HVG selection, PCA/UMAP/t-SNE, clustering, exploratory marker ranking, pseudobulk preparation, visualization, and Seurat or SingleCellExperiment RDS conversion to h5ad. Applies to established exploratory scRNA-seq workflows w"
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "scanpy"
keywords:
  - "scanpy"
  - "performs"
  - "single"
  - "cell"
  - "normalization"
  - "selection"
---

# Scanpy: Single-Cell Analysis

## Overview

Scanpy is a scalable Python toolkit for analyzing single-cell RNA-seq data, built on AnnData. Apply this skill for complete single-cell workflows including quality control, normalization, dimensionality reduction, clustering, marker gene identification, visualization, and trajectory analysis. Targets **Scanpy 1.12.4** (released 2026-08-27), reviewed 2026-10-01. Native synthetic tests establish data/API contracts, not biological validity.

## Installation

Requires Python **3.12+** (scanpy 1.12 dropped Python ≤3.11) and anndata **≥0.10**.

```bash
uv pip install "scanpy[leiden]"
```

The `[leiden]` extra installs `igraph` and `leidenalg`; the scripts explicitly select `flavor="igraph"`. For reproducible environments, pin a version: `uv pip install "scanpy[leiden]==1.12.4"`.

For large or out-of-core datasets, many functions support [Dask](https://docs.dask.org/) arrays (experimental):

```bash
uv pip install "scanpy[leiden]" dask
```

See the [Using dask with Scanpy](https://scanpy.scverse.org/en/stable/tutorials/experimental/dask.html) tutorial. For GPU-accelerated scanpy-like operations, use [rapids-singlecell](https://rapids-singlecell.readthedocs.io/) as a separate package.

If the input is an R-native single-cell object (`.rds`, `.RData`, Seurat, or SingleCellExperiment), first convert it to `.h5ad` with R tooling, then load it with Scanpy. Read `references/r_interop.md` for agent-run installation and conversion instructions across macOS, Linux, and Windows.

For AnnData structure and I/O details, use the **anndata** skill. For probabilistic models and batch correction, use **scvi-tools**.

## Representation and inference contracts

- Input to QC/preprocessing must be identified raw counts. The scripts reject negative,
  fractional, nonfinite or zero-total cells. Use `--counts-layer counts` when X is already
  normalized; never infer provenance from integer-looking values alone.
- `layers["counts"]` remains unnormalized; `.raw` is an independent full-gene
  log-normalized snapshot. Gene subsetting also subsets every layer, but does not subset
  `.raw` genes. Retain a full-gene object for pseudobulk; the full pipeline does so.
- `seurat`/`cell_ranger` HVGs use log-normalized values; `seurat_v3` and
  `seurat_v3_paper` use counts and require `scanpy[skmisc]`. Scaling/regression are optional,
  may densify sparse data, and can remove biology along with covariates.
- Marker ranking defaults to `.raw` when present; `--no-use-raw` selects X and `--layer`
  selects an explicit log-normalized layer. `--groups`/`--reference` control contrasts.
  Wilcoxon/t-test adjusted p-values use BH within each comparison; logreg returns ranking
  scores without p-values. Clusters chosen from the same data yield exploratory markers.
- Condition DE requires raw-count sums per sample and cell type, independent biological
  replicates, aligned condition/donor metadata and a full-rank design. Analyze each cell
  type separately; repeated donor samples require a suitable paired design. Aggregation
  cannot fix confounding, missing replication, doublets or incorrect annotations.
- Harmony (`harmonypy`) changes PCA coordinates; BBKNN (`bbknn`) changes the graph;
  ComBat changes X. Keep original expression/counts for DE, and assess biological
  conservation and batch mixing together. Requested integration/doublet failures stop.
- The toolkit loads files into memory. For backed data, explicitly call `.to_memory()`
  on a chosen subset and close the file; backed mode is not a general out-of-core
  pipeline. Copy views before mutation. Dask support varies by function/array layout.
- `.rds` needs an explicit R conversion stage. Cluster IDs do not determine cell types:
  all mappings/signature assets are illustrative human marker examples, requiring review.

Harmony 2 returns cells x PCs; the toolkit calls its native API because the
Scanpy 1.12.4 wrapper still transposes that output and fails with current Harmony.

Optional packages: `scikit-image` for Scrublet automatic thresholding, `loompy` for Loom,
`scikit-misc` for v3 HVGs, `harmonypy==2.0.2`/`bbknn==1.6.0` for their integration branches, and `louvain`
for the deprecated Louvain option (separate environment: louvain 0.8.2 requires
igraph <0.12, conflicting with the tested igraph 1.0). Install only needed branches. R and optional integration
execution boundaries are recorded in [references/upstream-review.md](references/upstream-review.md).

## When to Use This Skill

This skill should be used when:
- Analyzing single-cell RNA-seq data (.h5ad, 10X, CSV formats)
- Working with R-friendly single-cell datasets (`.rds`, `.RData`, Seurat, SingleCellExperiment) that need conversion to `.h5ad`
- Performing quality control on scRNA-seq datasets
- Creating UMAP, t-SNE, or PCA visualizations
- Identifying cell clusters and finding marker genes
- Annotating cell types based on gene expression
- Conducting trajectory inference or pseudotime analysis
- Generating publication-quality single-cell plots

## Script Toolkit (prefer these over writing code from scratch)

This skill bundles ready-to-run CLI scripts in `scripts/` for every common step. **Run these instead of hand-writing scanpy code** — they handle file loading by extension, figure setup, sensible defaults, raw-count preservation, and progress logging. Each reads and writes `.h5ad`, so they chain together, and each has its own `--help`. Only drop down to writing scanpy code when a task isn't covered by a script or needs unusual customization.

All scripts use a shared `scripts/_common.py` helper (loading, saving, figure config) — keep it alongside the others. Run from the skill directory or pass full paths; figures default to `./figures/`.

| Script | Purpose | Typical call |
|--------|---------|--------------|
| `run_pipeline.py` | **Full workflow in one command**: load → QC → normalize → HVG → PCA → (batch) → UMAP → Leiden → markers | `python scripts/run_pipeline.py raw.h5ad -o processed.h5ad` |
| `inspect_data.py` | Summarize an unknown dataset (shape, obs/var, layers, what's already computed, raw vs normalized) | `python scripts/inspect_data.py data.h5ad` |
| `convert.py` | Load any format (10x dir/.h5, csv, loom, mtx) and write `.h5ad` | `python scripts/convert.py 10x_dir/ -o data.h5ad` |
| `qc_analysis.py` | QC metrics, before/after plots, filtering, optional Scrublet doublets | `python scripts/qc_analysis.py raw.h5ad -o qc.h5ad --scrublet` |
| `preprocess.

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

