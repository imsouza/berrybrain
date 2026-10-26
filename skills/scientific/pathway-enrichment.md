---
id: sci-pathway-enrichment
name: "Scientific: pathway-enrichment"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Performs pathway and gene-set enrichment analysis on gene lists or ranked gene data and interprets the results. Used when the user has a set of genes (differentially expressed genes from PyDESeq2/Scanpy, CRISPR-screen hits, cluster marker genes, proteomics hits) and wants to know"
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "pathway enrichment"
  - "pathway-enrichment"
keywords:
  - "pathway"
  - "enrichment"
  - "performs"
  - "gene"
  - "analysis"
---

# Pathway Enrichment

## Overview

Enrichment analysis answers "what biology is over-represented in my genes?" It is the standard last step after differential expression, a screen, or clustering. There are two core methods, and choosing correctly is the single most important decision:

- **ORA (over-representation analysis)** — take a *thresholded* gene list (e.g., padj < 0.05) and test which gene sets it overlaps more than chance, using Fisher's exact / hypergeometric tests. Tools: Enrichr, g:Profiler.
- **GSEA (gene set enrichment analysis)** — take the *whole ranked list* of genes (no threshold) and test whether each gene set is concentrated toward the top or bottom. Preranked GSEA uses a per-gene score (e.g., the DESeq2 `stat`). Better when effects are broad and subtle.

This skill orchestrates these analyses, the gene-set databases behind them, and the interpretation pitfalls that make results wrong or unpublishable.

## When to Use This Skill

Use this skill when the user wants to:
- Find enriched GO terms / KEGG / Reactome / WikiPathways / MSigDB Hallmark sets in a gene list.
- Run GSEA / preranked GSEA on DESeq2, edgeR, limma, or Scanpy `rank_genes_groups` output.
- Score gene-set expression per sample/cell (ssGSEA, GSVA).
- Interpret, deduplicate, and visualize enrichment results, or build a publication table/figure.
- Decide between ORA and GSEA, pick gene-set libraries, choose a background, or fix gene-ID problems.

For quick one-off Enrichr lookups the `gget` skill (`gget enrichr`) is lighter weight; for raw pathway/interaction APIs (Reactome, KEGG, STRING) see the `database-lookup` skill. Use **this** skill for full, defensible enrichment workflows.

## Choosing the Right Method

| Situation | Method | Tool / entry point |
|-----------|--------|--------------------|
| You have a discrete hit list (DE genes, screen hits, cluster markers) | **ORA** | `gp.enrichr(...)` or g:Profiler |
| You have a full ranked list (every tested gene + a score) | **Preranked GSEA** | `gp.prerank(...)` |
| You have an expression matrix + class labels | **GSEA** | `gp.gsea(...)` |
| You want a gene-set score per sample/cell | **ssGSEA / GSVA** | `gp.ssgsea(...)`, `gp.gsva(...)` |
| You need a custom background or additional organisms | **ORA with custom domain** | g:Profiler (`domain_scope='custom'`) |
| You want TF / signaling *activity* (PROGENy, DoRothEA) | activity inference | see `references/databases-and-gene-sets.md` (decoupler) |

When in doubt: a thresholded list → ORA; a ranked table with scores → GSEA. Never threshold a list and then feed it to GSEA — that discards the ranking GSEA depends on.

## Setup

```bash
uv pip install gseapy==1.3.1 gprofiler-official==1.0.0 mygene==3.2.2 lxml
# gseapy pulls pandas, numpy, scipy, matplotlib. Network access is needed for
# Enrichr, g:Profiler, and MSigDB downloads. For fully offline ORA, use a local
# GMT file with gp.enrich() (see references/gseapy.md).
```

The examples target GSEApy 1.3.1 (released stable); the helper runs classic
permutation GSEA. Current MSigDB is 2026.1.Hs/2026.1.Mm. Local synthetic workflows
and small public mapping/catalog queries were executed; Enrichr submission
routes were verified from released source with mocked transport. BioMart returned
service-unavailable HTML during review; validate its output schema. See
[verified API contracts](references/verified-api.md) for evidence and boundaries.

Verify and list available gene-set libraries (names change over time — never hardcode blindly):

```python
import gseapy as gp
names = gp.get_library_name(organism="human")   # discover current Enrichr libraries
print([n for n in names if "Reactome" in n or "KEGG" in n or "Hallmark" in n])
```

## Quick Start

### ORA on a hit list (gseapy + Enrichr)

```python
import gseapy as gp

# Match the library organism and identifier namespace; map aliases explicitly.
# Keep original spelling: capitalization is not gene-ID or orthology mapping.
genes = [g.strip() for g in open("deg_symbols.txt") if g.strip()]
tested = [g.strip() for g in open("tested_symbols.txt") if g.strip()]
assert set(genes) <= set(tested)

enr = gp.enrichr(
    gene_list=genes,
    gene_sets=["MSigDB_Hallmark_2020", "GO_Biological_Process_2026",
               "KEGG_2026", "Reactome_Pathways_2024"],
    organism="human", background=tested,
    outdir=None,            # in-memory; set a path to also write tables/plots
)
res = enr.results
sig = res[res["Adjusted P-value"] < 0.05].sort_values("Adjusted P-value")
print(sig[["Gene_set", "Term", "Adjusted P-value", "Combined Score", "Genes"]].head(20))
# Speedrichr results omit Overlap; retain its actual response schema.
```

### Preranked GSEA from DESeq2 results

```python
import gseapy as gp
import pandas as pd
import numpy as np

res = pd.read_csv("deseq2_results.csv", index_col=0)   # index = gene symbols
# Rank by the test statistic (sign = direction, magnitude = evidence). This is
# more stable than ranking by log2FoldChange, which is noisy for low-count genes.
rnk = res["stat"].dropna().sort_values(ascending=False, kind="stable")
rnk.index = rnk.index.str.strip()
assert rnk.index.is_unique, "Resolve duplicate mappings before ranking"
assert np.isfinite(rnk.to_numpy()).all()

pre = gp.prerank(
    rnk=rnk,
    gene_sets=["MSigDB_Hallmark_2020", "GO_Biological_Process_2026"],
    organism="human", method="permutation",
    min_size=15, max_size=500,        # size AFTER intersection with ranked genes
    permutation_num=1000, seed=123,   # seed = reproducible p-values
    threads=4, ascending=None, outdir=None,
)
out = pre.res2d.sort_values("FDR q-val")
print(out[["Term", "ES", "NES", "NOM p-val", "FDR q-val", "Lead_genes"]].head(20))
```

Use a **signed Wald statistic**, not the unsigned DESeq2 likelihood-ratio statistic.
If unavailable, `sign(log2FoldChange) * -log10(raw pvalue)` is a fallback: validate
p-values in [0, 1], bound numerical zeros (the helper uses 1e-300), and report ties
and exclusions. Do not use adjusted p-values or select only significant genes.

## Core Workflow

For a defensible analysis, work through these steps. The middle steps (ID type, background) are where results most often silently go wrong.

### Step 1 — Pin down inputs and pick the method
Confirm: which genes, what organism, is there a per-gene score (→ GSEA) or just a list (→ ORA), and what comparison they represent (direction matters for interpretation).

### Step 2 — Get gene IDs into the right namespace
Match the identifie

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

