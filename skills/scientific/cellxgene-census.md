---
id: sci-cellxgene-census
name: "Scientific: cellxgene-census"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Queries the CZ CELLxGENE Census programmatically for versioned public single-cell and spatial transcriptomics data. Use when you need population-scale cell metadata, gene expression slices, Census summary counts, source H5AD URIs/downloads, embeddings, spatial Census data, or ref"
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "cellxgene census"
  - "cellxgene-census"
keywords:
  - "cellxgene"
  - "census"
  - "queries"
  - "programmatically"
  - "versioned"
  - "public"
---

# CZ CELLxGENE Census

## Overview

The CZ CELLxGENE Census provides programmatic access to a comprehensive, versioned collection of standardized single-cell and spatial transcriptomics data from CZ CELLxGENE Discover. This skill enables efficient querying and analysis of public Census releases without downloading whole datasets first.

The Census includes:
- **217+ million total cells** and **125+ million unique cells** in the 2025-11-08 stable LTS release
- **1,845 datasets** in the 2025-11-08 stable LTS release
- **Human, mouse, marmoset, rhesus macaque, and chimpanzee** data in the current schema
- **Standardized metadata** (cell types, tissues, diseases, donors)
- **Raw gene expression** matrices and source H5AD lookup/download helpers
- **Pre-calculated summary counts, embeddings, and spatial data**
- **Integration with AnnData, Scanpy, TileDB-SOMA, TileDB-SOMA-ML, and other analysis tools**

## When to Use This Skill

This skill should be used when:
- Querying single-cell expression data by cell type, tissue, or disease
- Exploring available single-cell datasets and metadata
- Training machine learning models on single-cell data
- Performing large-scale cross-dataset analyses
- Integrating Census data with scanpy or other analysis frameworks
- Computing statistics across millions of cells
- Accessing pre-calculated embeddings or model predictions

## Installation and Setup

Install the Census API:
```bash
uv pip install "cellxgene-census==1.18.0"
```

For spatial workflows:
```bash
uv pip install "cellxgene-census[spatial]==1.18.0"
```

For PyTorch model training, use TileDB-SOMA-ML. The old `cellxgene_census.experimental.ml` loaders are absent from 1.18.0:

```bash
uv pip install "cellxgene-census==1.18.0" tiledbsoma-ml
```

## Core Workflow Patterns

Eight patterns, each with code, are in
[references/core_workflow_patterns.md](references/core_workflow_patterns.md):

1. **Opening the Census** — always pin `census_version` so an analysis stays reproducible.
2. **Exploring Census information** — available datasets, cell counts, and summary tables.
3. **Querying expression data** — small to medium scale into an `AnnData`.
4. **Large-scale queries** — out-of-core processing when the slice will not fit in memory.
5. **Machine learning with PyTorch** — TileDB-SOMA-ML data loaders.
6. **Spatial Census data** — accessing spatial assays.
7. **Integration with Scanpy** — handing a Census slice to a standard Scanpy workflow.
8. **Multi-dataset integration** — combining datasets and handling batch effects.

## Key Concepts and Best Practices

The examples pin the current LTS build `2025-11-08`, verified through the live
release directory on 2026-09-30. The SDK and data release are separate versions.
Resolve `stable` once with `get_census_version_description("stable")["release_build"]`
and record that date; never silently switch builds midway through analysis.

### Always Filter for Primary Data
Unless analyzing duplicates, always include `is_primary_data == True` in queries to avoid counting cells multiple times:
```python
obs_value_filter="cell_type == 'B cell' and is_primary_data == True"
```

### Specify Census Version for Reproducibility
Always specify the Census version in production analyses:
```python
census = cellxgene_census.open_soma(census_version="2025-11-08")
```

### Estimate Query Size Before Loading
For large queries, count the selected rows without loading every metadata column.
Cell count alone is not a memory estimate: gene count, sparsity, dtype, layers,
embeddings, and downstream dense copies also matter:
```python
import tiledbsoma as soma
with census["census_data"]["homo_sapiens"].axis_query(
    measurement_name="RNA",
    obs_query=soma.AxisQuery(
        value_filter="tissue_general == 'brain' and is_primary_data == True"
    ),
) as query:
    print(f"Selected {query.n_obs:,} cells and {query.n_vars:,} genes")

# Query axes consume memory too; stream expression if the matrix will not fit.
```

### Use tissue_general for Broader Groupings
The `tissue_general` field provides coarser categories than `tissue`, useful for cross-tissue analyses:
```python
# Broader grouping
obs_value_filter="tissue_general == 'immune system'"

# Specific tissue
obs_value_filter="tissue == 'venous blood'"
```

### Select Only Needed Columns
Minimize data transfer by specifying only required metadata columns:
```python
obs_column_names=["cell_type", "tissue_general", "disease"]  # Not all columns
```

### Check Dataset Presence for Gene-Specific Queries
When analyzing specific genes, verify which datasets measured them:
```python
genes = cellxgene_census.get_var(
    census, "homo_sapiens",
    value_filter="feature_name in ['CD4', 'CD8A']",
    column_names=["soma_joinid", "feature_id", "feature_name"],
)
presence = cellxgene_census.get_presence_matrix(census, "homo_sapiens")
# Columns use Census join IDs, not positions in the filtered gene table.
gene_presence = presence[:, genes["soma_joinid"].to_numpy()]
```

Gene symbols are not necessarily unique in schema 2.4.0; keep `feature_id` as the
feature key, inspect all symbol matches, and never silently select the first match.

Presence rows are dataset `soma_joinid` values, not cell IDs; a zero means the
feature was not measured in that dataset, not that measured expression was zero.
The remote-query snippets are illustrative; verify the selected release and
returned schema before loading a large expression slice.

### Two-Step Workflow: Explore Then Query
First explore metadata to understand available data, then query expression:
```python
# Step 1: Explore what's available
metadata = cellxgene_census.get_obs(
    census, "homo_sapiens",
    value_filter="disease == 'COVID-19' and is_primary_data == True",
    column_names=["cell_type", "tissue_general"]
)
print(metadata.value_counts())

# Step 2: Query based on findings
adata = cellxgene_census.get_anndata(
    census=census,
    organism="Homo sapiens",
    obs_value_filter="disease == 'COVID-19' and cell_type == 'T cell' and is_primary_data == True",
)
```

For complete disease cohorts, use the multi-value disease workflow in
[references/common_patterns.md](references/common_patterns.md). Exact equality in
the small examples selects only cells whose whole disease field equals that label.

## Available Metadata Fields

### Cell Metadata (obs)
Key fields for filtering:
- `cell_type`, `cell_type_ontology_term_id`
- `tissue`, `tissue_general`, `tissue_ontology_term_id`
- `disease

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

