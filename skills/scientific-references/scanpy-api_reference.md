---
id: sciref-scanpy-api-reference
name: "Scientific Ref: Scanpy API Quick Reference"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (scanpy): Scanpy API Quick Reference"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "scanpy api reference"
  - "scanpy api quick reference"
keywords:
  - "scanpy"
  - "api"
  - "reference"
  - "specialized"
  - "scientific"
  - "quick"
---

# Scanpy API Quick Reference

Reviewed for Scanpy 1.12.4 / AnnData 0.13.4 on 2026-10-01. These snippets are
illustrative and require the named genes, groups and prior results to exist.
Use the tested CLI workflow for a runnable starting point. Counts, normalized
expression and `.raw` have distinct roles; see [upstream-review.md](upstream-review.md).


Quick reference for commonly used scanpy functions organized by module.

## Import Convention

```python
import scanpy as sc
```

## Reading and Writing Data (sc.read_*)

### Reading Functions

```python
sc.read_10x_h5(filename)                    # Read 10X HDF5 file
sc.read_10x_mtx(path)                       # Read 10X mtx directory
sc.read_h5ad(filename)                      # Read h5ad (AnnData) file
sc.read_csv(filename)                       # Read CSV file
sc.read_excel(filename, sheet=0)            # Requires a sheet and Excel reader dependency
sc.read_loom(filename)                      # Read loom file
sc.read_text(filename)                      # Read text file
sc.read_visium(path)                        # Deprecated; use spatialdata-io for new workflows
```

### Writing Functions

```python
adata.write_h5ad(filename)                  # Write to h5ad format
adata.write_csvs(dirname)                   # Write to CSV files
adata.write_loom(filename)                  # Write to loom format
adata.write_zarr(filename)                  # Write to zarr format
```

## Preprocessing (sc.pp.*)

### Quality Control

```python
sc.pp.calculate_qc_metrics(adata, qc_vars=['mt'], percent_top=None, inplace=True)
sc.pp.filter_cells(adata, min_genes=200)
sc.pp.filter_genes(adata, min_cells=3)
sc.pp.scrublet(adata)                              # Doublet detection (core since 1.10)
sc.pp.scrublet_simulate_doublets(adata)            # Simulate doublets for benchmarking
```

### Normalization and Transformation

```python
sc.pp.normalize_total(adata, target_sum=1e4)    # Normalize to target sum
sc.pp.log1p(adata)                               # Log(x + 1) transformation
sc.pp.sqrt(adata)                                # Square root transformation
```

### Feature Selection

```python
sc.pp.highly_variable_genes(adata, min_mean=0.0125, max_mean=3, min_disp=0.5)
sc.pp.highly_variable_genes(adata, flavor='seurat_v3', n_top_genes=2000)
# Dask support is experimental; v3 flavors gained support in 1.12.
```

### Scaling and Regression

```python
sc.pp.scale(adata, max_value=10)                      # Scale to unit variance
sc.pp.regress_out(adata, ['total_counts', 'pct_counts_mt'])  # Regress out unwanted variation
```

### Dimensionality Reduction (Preprocessing)

```python
sc.pp.pca(adata, n_comps=50)                     # Principal component analysis
sc.pp.neighbors(adata, n_neighbors=10, n_pcs=40) # Compute neighborhood graph
sc.pp.neighbors(adata, method='jaccard')         # Jaccard connectivities (scanpy 1.12)
```

### Batch Correction

```python
sc.pp.combat(adata, key='batch')                 # ComBat batch correction
```

## Tools (sc.tl.*)

### Dimensionality Reduction

```python
sc.tl.pca(adata, svd_solver='arpack')            # PCA
sc.tl.umap(adata)                                 # UMAP embedding
sc.tl.tsne(adata)                                 # t-SNE embedding
sc.tl.diffmap(adata)                              # Diffusion map
sc.tl.draw_graph(adata, layout='fa')             # Force-directed graph
```

### Clustering

```python
sc.tl.leiden(adata, resolution=0.5)              # Leiden clustering (recommended)
# sc.tl.louvain(adata, resolution=0.5)           # Deprecated in scanpy 1.12 — use leiden
# K-means is not a scanpy.tl function; use sklearn.cluster.KMeans explicitly.
```

### Marker Genes and Differential Expression

```python
sc.tl.rank_genes_groups(adata, groupby='leiden', method='wilcoxon')
sc.tl.rank_genes_groups(adata, groupby='leiden', method='t-test')
sc.tl.rank_genes_groups(adata, groupby='leiden', method='logreg')

# Get results as dataframe
sc.get.rank_genes_groups_df(adata, group='0')
# Exploratory only — per-cell tests inflate significance (often making p-values too small); pseudobulk for rigorous DE
```

### Aggregation (Pseudobulk)

```python
sc.get.aggregate(adata, by='cell_type', func='sum', layer='counts')
pb = sc.get.aggregate(adata, by=['sample', 'cell_type'], func='sum', layer='counts')
counts = pb.layers['sum']  # cells/groups x genes; pb.X is None
# Keep biological replicate metadata; PyDESeq2 expects sample rows and gene columns.
```

### Trajectory Inference

```python
sc.tl.paga(adata, groups='leiden')               # PAGA trajectory
sc.tl.diffmap(adata, n_comps=10)  # choose fewer for small datasets
sc.tl.dpt(adata, n_dcs=10)                                  # Diffusion pseudotime
```

### Gene Scoring

```python
sc.tl.score_genes(adata, gene_list, score_name='score')
sc.tl.score_genes_cell_cycle(adata, s_genes=s_genes, g2m_genes=g2m_genes)
```

### Embeddings and Projections

```python
sc.tl.ingest(adata, adata_ref)                   # Map to reference
sc.tl.embedding_density(adata, basis='umap', groupby='leiden')
```

## Plotting (sc.pl.*)

### Basic Embeddings

```python
sc.pl.umap(adata, color='leiden')                # UMAP plot
sc.pl.tsne(adata, color='gene_name')             # t-SNE plot
sc.pl.pca(adata, color='leiden')                 # PCA plot
sc.pl.diffmap(adata, color='leiden')             # Diffusion map plot
```

### Heatmaps and Dot Plots

```python
sc.pl.heatmap(adata, var_names=genes, groupby='leiden')
sc.pl.dotplot(adata, var_names=genes, groupby='leiden')
sc.pl.matrixplot(adata, var_names=genes, groupby='leiden')
sc.pl.stacked_violin(adata, var_names=genes, groupby='leiden')
```

### Violin and Scatter Plots

```python
sc.pl.violin(adata, keys=['gene1', 'gene2'], groupby='leiden')
sc.pl.scatter(adata, x='gene1', y='gene2', color='leiden')
```

### Marker Gene Visualization

```python
sc.pl.rank_genes_groups(adata, n_genes=25, sharey=False)
sc.pl.rank_genes_groups_violin(adata, groups='0')
sc.pl.rank_genes_groups_heatmap(adata, n_genes=10)
sc.pl.rank_genes_groups_dotplot(adata, n_genes=5)
```

### Trajectory Visualization

```python
sc.pl.paga(adata, color='leiden')                # PAGA graph
# Legacy branch-order plot requires dpt_order_indices/dpt_changepoints,
# which default n_branchings=0 does not create. Prefer the pseudotime UMAP.
# sc.pl.dpt_timeseries(adata)                      # DPT timeseries
```

### QC Plots

```python
sc.pl.highest_expr_genes(adata, n_top=20)
sc.pl.vi

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

