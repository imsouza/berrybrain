---
id: sciref-cellxgene-census-common-patterns
name: "Scientific Ref: Common Query Patterns and Best Practices"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (cellxgene-census): Common Query Patterns and Best Practices"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "cellxgene census common patterns"
  - "common query patterns and best practices"
keywords:
  - "cellxgene"
  - "census"
  - "common"
  - "patterns"
  - "specialized"
  - "scientific"
  - "reference"
---

# Common Query Patterns and Best Practices

Reviewed against Census 1.18.0, TileDB-SOMA 2.3.0, and the 2025-11-08 LTS.
Snippets share an open `census` context unless shown otherwise. Large cohort,
model-training, and downstream analysis blocks are illustrative: first inspect
metadata and size, restrict datasets/genes, and supply the named callbacks/model.
API and sparse-statistics contracts were exercised on a small local SOMA fixture;
a 10-cell/3-gene slice and metadata were also read from the public LTS.


## Query Pattern Categories

### 1. Exploratory Queries (Metadata Only)

Use when exploring available data without loading expression matrices.

**Pattern: Get unique cell types in a tissue**
```python
import cellxgene_census

with cellxgene_census.open_soma(census_version="2025-11-08") as census:
    cell_metadata = cellxgene_census.get_obs(
        census,
        "homo_sapiens",
        value_filter="tissue_general == 'brain' and is_primary_data == True",
        column_names=["cell_type"]
    )
    unique_cell_types = cell_metadata["cell_type"].unique()
    print(f"Found {len(unique_cell_types)} unique cell types")
```

**Pattern: Count cells by condition**
```python
cell_metadata = cellxgene_census.get_obs(
    census,
    "homo_sapiens",
    value_filter="disease != 'normal' and is_primary_data == True",
    column_names=["disease", "tissue_general"]
)
counts = cell_metadata.groupby(["disease", "tissue_general"]).size()
```

**Pattern: Explore dataset information**
```python
# Access datasets table
datasets = census["census_info"]["datasets"].read().concat().to_pandas()

# Title search is discovery only; disease labels are on obs, not datasets.
candidates = datasets[datasets["dataset_title"].str.contains("COVID", case=False, na=False)]
```

### 2. Small-to-Medium Queries (AnnData)

Use `get_anndata()` when results fit in memory. There is no safe universal cell-count threshold; include gene count, sparsity, embeddings, and downstream copies in the estimate.

**Pattern: Tissue-specific cell type query**
```python
adata = cellxgene_census.get_anndata(
    census=census,
    organism="Homo sapiens",
    obs_value_filter="cell_type == 'B cell' and tissue_general == 'lung' and is_primary_data == True",
    obs_column_names=["assay", "disease", "sex", "donor_id"],
)
```

**Pattern: Gene-specific query with multiple genes**
```python
marker_genes = ["CD4", "CD8A", "CD19", "FOXP3"]

# First get gene IDs
gene_metadata = cellxgene_census.get_var(
    census, "homo_sapiens",
    value_filter=f"feature_name in {marker_genes}",
    column_names=["feature_id", "feature_name"]
)
gene_ids = gene_metadata["feature_id"].tolist()
if not gene_ids:
    raise ValueError("No requested marker genes found")
# Inspect duplicate symbols; retain feature_id rather than collapsing matches.

# Query with gene filter
adata = cellxgene_census.get_anndata(
    census=census,
    organism="Homo sapiens",
    var_value_filter=f"feature_id in {gene_ids}",
    obs_value_filter="cell_type == 'T cell' and is_primary_data == True",
)
```

**Pattern: Multi-tissue query**
```python
adata = cellxgene_census.get_anndata(
    census=census,
    organism="Homo sapiens",
    obs_value_filter="tissue_general in ['lung', 'liver', 'kidney'] and is_primary_data == True",
    obs_column_names=["cell_type", "tissue_general", "dataset_id"],
)
```

**Pattern: Disease-specific query**
```python
adata = cellxgene_census.get_anndata(
    census=census,
    organism="Homo sapiens",
    obs_value_filter="disease == 'COVID-19' and tissue_general == 'lung' and is_primary_data == True",
)
```

**Pattern: Include compound disease labels**

Schema 2.4.0 stores multiple disease labels/IDs in one string separated by ` || `.
Use summary rows to discover the actual strings and token membership to choose
whole values; substring matching can confuse distinct disease names. This
includes co-diagnoses rather than only the exact single-label cohort.

```python
summary = census["census_info"]["summary_cell_counts"].read().concat().to_pandas()
disease_values = summary.loc[
    summary["organism"].eq("homo_sapiens") & summary["category"].eq("disease"),
    "label",
].unique()
matching = [value for value in disease_values if "COVID-19" in value.split(" || ")]
if not matching:
    raise ValueError("Requested disease not present in this release")
disease_filter = f"disease in {matching!r} and is_primary_data == True"
# Add dataset/tissue restrictions after inspecting cohort size.
```

For precise ontology-based cohorts, inspect `disease_ontology_term_id` as well;
matching one ontology term does not automatically include all descendants.

### 3. Large Queries (Out-of-Core Processing)

Use `axis_query()` for queries that exceed available RAM.

**Pattern: Iterative processing**
```python
import tiledbsoma as soma

# Create query
with census["census_data"]["homo_sapiens"].axis_query(
    measurement_name="RNA",
    obs_query=soma.AxisQuery(
        value_filter="tissue_general == 'brain' and is_primary_data == True"
    ),
    var_query=soma.AxisQuery(
        value_filter="feature_name in ['FOXP2', 'TBR1', 'SATB2']"
    ),
) as query:
    # Iterate through X matrix in chunks
    iterator = query.X("raw").tables()
    for batch in iterator:
        # Process batch (a pyarrow.Table); soma_dim_0 = cells, soma_dim_1 = genes
        # batch has columns: soma_data, soma_dim_0, soma_dim_1
        process_batch(batch)
```

**Pattern: Per-gene mean and variance including measured zeros**

Restrict to datasets that measured every requested feature before computing the
statistics. This example selects CD4 by its unique Ensembl ID. It includes sparse
zeros, returns one row per gene, and rejects empty or one-cell selections rather
than returning an undefined sample variance.

```python
from cellxgene_census.experimental.pp import mean_variance

# Assumes census and soma are imported/open as above.
genes = cellxgene_census.get_var(
    census, "homo_sapiens", value_filter="feature_id == 'ENSG00000010610'",
    column_names=["soma_joinid", "feature_id"],
)
if len(genes) != 1:
    raise ValueError("Expected one CD4 feature")
datasets = census["census_info"]["datasets"].read().concat().to_pandas()
presence = cellxgene_census.get_presence_matrix(census, "homo_sapiens")
covered = presence[datasets["soma_joinid"].to_numpy(), :][:, genes["soma_joinid"].to_numpy()]
eligible_ids = datasets.loc[covered.toarray().all(axis=1), "dataset_id"].tolist()
if not eligible_ids:
    ra

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

