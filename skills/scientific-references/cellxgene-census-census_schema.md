---
id: sciref-cellxgene-census-census-schema
name: "Scientific Ref: CZ CELLxGENE Census Data Schema Reference"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (cellxgene-census): CZ CELLxGENE Census Data Schema Reference"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "cellxgene census census schema"
  - "cz cellxgene census data schema reference"
keywords:
  - "cellxgene"
  - "census"
  - "schema"
  - "specialized"
  - "scientific"
  - "reference"
---

# CZ CELLxGENE Census Data Schema Reference

## Overview

The CZ CELLxGENE Census is a versioned collection of single-cell and spatial transcriptomics data built on the TileDB-SOMA framework. This reference documents the data structure, available metadata fields, and query syntax.

Current reference point:
- Package examples target `cellxgene-census==1.18.0`
- Current stable LTS Census: `2025-11-08`
- Census schema version: `2.4.0`
- CELLxGENE dataset schema version: `7.0.0`
- SDK tested against this LTS: `cellxgene-census` 1.18.0 / TileDB-SOMA 2.3.0
- Sources: [official schema](https://github.com/chanzuckerberg/cellxgene-census/blob/main/docs/cellxgene_census_schema.md) and [release notes](https://chanzuckerberg.github.io/cellxgene-census/cellxgene_census_docsite_data_release_info.html), reviewed 2026-09-30.

## High-Level Structure

The Census is organized as a `SOMACollection` with these main components:

### 1. census_info
Summary information including:
- **summary**: Build date, cell counts, dataset statistics
- **datasets**: Source datasets included in this release (not all of Discover); fields include `dataset_id`, `dataset_version_id`, `dataset_title`, `collection_id`, `collection_name`, `collection_doi`, `citation`, `dataset_h5ad_path`, and `dataset_total_cell_count`. Disease and tissue live on `obs`, not this table.
- **organisms**: `organism`, `organism_label`, and `organism_ontology_term_id` mappings
- **summary_cell_counts**: Cell counts stratified by metadata categories

### 2. census_data
Organism-specific `SOMAExperiment` objects:
- **"homo_sapiens"**: Human single-cell data
- **"mus_musculus"**: Mouse single-cell data
- **"callithrix_jacchus"**: Common marmoset single-cell data
- **"macaca_mulatta"**: Rhesus macaque single-cell data
- **"pan_troglodytes"**: Chimpanzee single-cell data

### 3. census_spatial_sequencing
Spatial organism-specific `SOMAExperiment` objects for supported releases. Spatial and non-spatial data share core metadata requirements, while spatial observations also include spatial columns such as `array_col`, `array_row`, and `in_tissue`.

## Single-Cell Data Structure Per Organism

Each organism experiment contains:

### obs (Cell Metadata)
Cell-level annotations stored as a `SOMADataFrame`. Access via:
```python
census["census_data"]["homo_sapiens"].obs
```

### ms["RNA"] (Measurement)
RNA measurement data including:
- **X**: Data matrices with layers:
  - `raw`: Raw count data
  - `normalized`: Library-size-normalized values; full-gene assays also receive gene-length normalization. This is not log-transformed. Inspect `list(experiment.ms["RNA"].X)` for the selected release. Spatial data provides `raw` only.
- **var**: Gene metadata
- **feature_dataset_presence_matrix**: Sparse boolean array showing which genes were measured in each dataset

## Spatial Data Structure Per Organism

Spatial data is stored separately from the single-cell Census data:
```python
census["census_spatial_sequencing"]["homo_sapiens"]
```

Each spatial organism experiment contains:
- `obs`: Spatial observation metadata, including core Census metadata and spatial fields such as `array_col`, `array_row`, and `in_tissue`
- `ms["RNA"]`: RNA measurement matrices and feature metadata
- `spatial[scene_id].obsl["loc"]`: point-cloud positions for each scene, with `x`, `y`, and `soma_joinid`

Use `axis_query(...).to_spatialdata(X_name="raw")` when exporting a spatial slice to `spatialdata`.

## Cell Metadata Fields (obs)

### Required/Core Fields

**Identity & Dataset:**
- `soma_joinid`: Unique integer identifier for joins
- `dataset_id`: Source dataset identifier
- `is_primary_data`: Boolean flag (True = primary representation, False = duplicate across datasets)

**Cell Type:**
- `cell_type`: Human-readable cell type name
- `cell_type_ontology_term_id`: Standardized ontology term (e.g., "CL:0000236")

**Tissue:**
- `tissue`: Specific tissue name
- `tissue_general`: Broader tissue category (useful for grouping)
- `tissue_ontology_term_id`: Standardized ontology term
- `tissue_general_ontology_term_id`: Standardized ontology term for the broader tissue category

**Assay:**
- `assay`: Sequencing technology used
- `assay_ontology_term_id`: Standardized ontology term

**Disease:**
- `disease`: Disease status or condition
- `disease_ontology_term_id`: Standardized ontology term

**Donor:**
- `donor_id`: Source-provided donor identifier; do not assume global uniqueness across studies
- `sex`: Biological sex (male, female, unknown)
- `self_reported_ethnicity`: Ethnicity information
- `development_stage`: Life stage (adult, child, embryonic, etc.)
- `development_stage_ontology_term_id`: Standardized ontology term

**Organism:**
Select the experiment by its organism key. Organism labels/ontology IDs are in
`census_info["organisms"]`, not guaranteed `obs` columns.

**Technical:**
- `suspension_type`: Sample preparation type (cell, nucleus, na)
- `tissue_type`: `tissue` or `organoid` for included observations
- `observation_joinid`: Source observation identity
- `nnz`, `n_measured_vars`, `raw_sum`, `raw_mean_nnz`, `raw_variance_nnz`: Count summaries; the `_nnz` statistics exclude zeros

## Gene Metadata Fields (var)

Access via:
```python
census["census_data"]["homo_sapiens"].ms["RNA"].var
```

**Available Fields:**
- `soma_joinid`: Unique integer identifier for joins
- `feature_id`: Ensembl gene ID (e.g., "ENSG00000161798")
- `feature_name`: Gene symbol (e.g., "FOXP2"); duplicates are allowed since schema 2.4.0, so use `feature_id` as the stable feature key
- `feature_type`: Present in the verified 2025-11-08 build, although omitted from the upstream schema field list; inspect the live schema
- `feature_length`: Gene length in base pairs
- `nnz`: Non-zero count summary
- `n_measured_obs`: Number of measured observations for the feature

## Value Filter Syntax

Queries use Python-like expressions for filtering. The syntax is processed by TileDB-SOMA.

### Comparison Operators
- `==`: Equal to
- `!=`: Not equal to
- `<`, `>`, `<=`, `>=`: Numeric comparisons
- `in`: Membership test (e.g., `feature_id in ['ENSG00000161798', 'ENSG00000188229']`)

### Logical Operators
- `and`, `&`: Logical AND
- `or`, `|`: Logical OR

### Examples

**Single condition:**
```python
value_filter="cell_type == 'B cell'"
```

**Multiple conditions with AND:**
```python
value_filter="cell_type == 'B cell' and tissue_general == 'lung' and is_primary_data == True"
```

**Using IN for multiple values:**
```python
va

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

