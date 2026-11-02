---
id: sciref-cellxgene-census-core-workflow-patterns
name: "Scientific Ref: Core Workflow Patterns"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (cellxgene-census): Core Workflow Patterns"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "cellxgene census core workflow patterns"
  - "core workflow patterns"
keywords:
  - "cellxgene"
  - "census"
  - "core"
  - "workflow"
  - "patterns"
  - "specialized"
  - "scientific"
  - "reference"
---

# Core Workflow Patterns

Reviewed against Census 1.18.0, TileDB-SOMA 2.3.0, and the 2025-11-08 LTS.
Snippets share an open `census` context unless shown otherwise. Large cohort,
model-training, and downstream analysis blocks are illustrative: first inspect
metadata and size, restrict datasets/genes, and supply the named callbacks/model.
API and sparse-statistics contracts were exercised on a small local SOMA fixture;
a 10-cell/3-gene slice and metadata were also read from the public LTS.


The eight patterns in full, with code: opening the Census, exploring Census information,
querying expression data at small to medium scale, large-scale out-of-core queries,
machine learning with PyTorch, spatial Census data, Scanpy integration, and
multi-dataset integration.

## Core Workflow Patterns

### 1. Opening the Census

Always use the context manager to ensure proper resource cleanup:

```python
import cellxgene_census

# Resolve a moving alias once, then record the concrete build
build = cellxgene_census.get_census_version_description("stable")["release_build"]
with cellxgene_census.open_soma(census_version=build) as census:
    print(build, list(census["census_data"]))

# Open the reviewed LTS version for reproducibility
with cellxgene_census.open_soma(census_version="2025-11-08") as census:
    print(list(census["census_data"]))
```

**Key points:**
- Use context manager (`with` statement) for automatic cleanup
- Specify `census_version` for reproducible analyses
- `stable` opens the current LTS Census release; `latest` opens the newest weekly release retained for a shorter period

### 2. Exploring Census Information

Before querying expression data, explore available datasets and metadata.

**Access summary information:**
```python
# Get summary statistics as label/value rows
summary = census["census_info"]["summary"].read().concat().to_pandas()
summary_values = summary.set_index("label")["value"]
print(f"Total cells: {int(summary_values['total_cell_count']):,}")
print(f"Unique cells: {int(summary_values['unique_cell_count']):,}")

# Get all datasets
datasets = census["census_info"]["datasets"].read().concat().to_pandas()

# Get precomputed counts by organism, cell type, tissue, disease, and assay
summary_counts = census["census_info"]["summary_cell_counts"].read().concat().to_pandas()
tissue_counts = summary_counts[summary_counts["category"].eq("tissue_general")]
```

**Query cell metadata to understand available data:**
```python
# Get unique cell types in a tissue
cell_metadata = cellxgene_census.get_obs(
    census,
    "homo_sapiens",
    value_filter="tissue_general == 'brain' and is_primary_data == True",
    column_names=["cell_type"]
)
unique_cell_types = cell_metadata["cell_type"].unique()
print(f"Found {len(unique_cell_types)} cell types in brain")

# Count cells by tissue
tissue_metadata = cellxgene_census.get_obs(
    census,
    "homo_sapiens",
    value_filter="is_primary_data == True",
    column_names=["tissue_general"],
)
tissue_counts = tissue_metadata["tissue_general"].value_counts()
```

**Important:** Always filter for `is_primary_data == True` to avoid counting duplicate cells unless specifically analyzing duplicates.

### 3. Querying Expression Data (Small to Medium Scale)

For slices whose expression, metadata, and downstream copies fit in memory, use `get_anndata()`:

```python
# Basic query with cell type and tissue filters
adata = cellxgene_census.get_anndata(
    census=census,
    organism="Homo sapiens",  # or "Mus musculus"
    obs_value_filter="cell_type == 'B cell' and tissue_general == 'lung' and is_primary_data == True",
    obs_column_names=["assay", "disease", "sex", "donor_id"],
)

# Query specific genes with multiple filters
adata = cellxgene_census.get_anndata(
    census=census,
    organism="Homo sapiens",
    var_value_filter="feature_name in ['CD4', 'CD8A', 'CD19', 'FOXP3']",
    obs_value_filter="cell_type == 'T cell' and disease == 'COVID-19' and is_primary_data == True",
    obs_column_names=["cell_type", "tissue_general", "donor_id"],
)
```

**Filter syntax:**
- Use `obs_value_filter` for cell filtering
- Use `var_value_filter` for gene filtering
- Combine conditions with `and`, `or`
- Use `in` for multiple values: `tissue in ['lung', 'liver']`
- Select only needed columns with `obs_column_names`
- In current LTS releases, `disease` and `disease_ontology_term_id` may contain ` || `-delimited multiple values; inspect available values before relying on exact equality filters for disease cohorts

**Getting metadata separately:**
```python
# Query cell metadata
cell_metadata = cellxgene_census.get_obs(
    census, "homo_sapiens",
    value_filter="disease == 'COVID-19' and is_primary_data == True",
    column_names=["cell_type", "tissue_general", "donor_id"]
)

# Query gene metadata
gene_metadata = cellxgene_census.get_var(
    census, "homo_sapiens",
    value_filter="feature_name in ['CD4', 'CD8A']",
    column_names=["feature_id", "feature_name", "feature_length"]
)
```

### 4. Large-Scale Queries (Out-of-Core Processing)

For queries exceeding available RAM, use `axis_query()` with iterative processing:

```python
import tiledbsoma as soma

# Create axis query
with census["census_data"]["homo_sapiens"].axis_query(
    measurement_name="RNA",
    obs_query=soma.AxisQuery(
        value_filter="tissue_general == 'brain' and is_primary_data == True"
    ),
    var_query=soma.AxisQuery(
        value_filter="feature_name in ['FOXP2', 'TBR1', 'SATB2']"
    ),
) as query:
    # Iterate through expression matrix in chunks
    iterator = query.X("raw").tables()
    for batch in iterator:
        # batch is a pyarrow.Table with columns:
        # - soma_data: expression value
        # - soma_dim_0: cell (obs) coordinate
        # - soma_dim_1: gene (var) coordinate
        process_batch(batch)
```

**Computing incremental statistics:**

Use the tested per-gene `mean_variance(..., nnz_only=False)` workflow in
[common_patterns.md](common_patterns.md). Sparse tables contain stored entries,
so averaging their values silently excludes zeros. Also exclude datasets that did
not measure a gene; missing measurements are not biological zero expression.

### 5. Machine Learning with PyTorch

For training models, use TileDB-SOMA-ML. The former `cellxgene_census.experimental.ml` PyTorch loaders are absent from 1.18.0.

```python
import tiledbsoma as soma
import torch
from tiledbsoma_ml import ExperimentDataset, experiment_dataloader

with cellxgene_ce

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

