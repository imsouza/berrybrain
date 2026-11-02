---
id: sciref-pathway-enrichment-databases-and-gene-sets
name: "Scientific Ref: Databases, Gene Sets, and Gene-ID Mapping"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (pathway-enrichment): Databases, Gene Sets, and Gene-ID Mapping"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "pathway enrichment databases gene sets"
  - "databases, gene sets, and gene-id mapping"
keywords:
  - "pathway"
  - "enrichment"
  - "databases"
  - "gene"
  - "sets"
  - "specialized"
  - "scientific"
  - "reference"
---

# Databases, Gene Sets, and Gene-ID Mapping

## Contents
- [Picking libraries by question](#picking-libraries-by-question)
- [The main gene-set databases](#the-main-gene-set-databases)
- [MSigDB collections](#msigdb-collections)
- [g:Profiler (alternative ORA, custom background, many organisms)](#gprofiler)
- [Gene-ID types and conversion](#gene-id-types-and-conversion)
- [Organism handling](#organism-handling)
- [Pathway/interaction APIs (Reactome, KEGG, STRING)](#pathwayinteraction-apis)
- [Activity inference (decoupler: PROGENy, DoRothEA/CollecTRI)](#activity-inference)

## Picking libraries by question

Match the database to the biological question instead of running everything:

| Question | Best gene sets |
|----------|----------------|
| "What are the broad themes?" | MSigDB **Hallmark** (50 curated, low redundancy) |
| "What mechanism/process?" | **GO Biological Process** |
| "Which curated pathways?" | **Reactome**, **KEGG**, **WikiPathways** |
| "Molecular function / localization?" | GO MF / GO CC |
| "Immune signatures?" | MSigDB **C7** (ImmuneSigDB) |
| "Oncogenic / perturbation?" | MSigDB **C6** (oncogenic), **C2:CGP** |
| "TF targets / regulons?" | MSigDB **C3**, ChEA, or decoupler (below) |
| "Disease/phenotype association?" | g:Profiler HP, DisGeNET, GWAS Catalog |

Start narrow (Hallmark + one of GO:BP / Reactome). Add libraries only if the
question needs them — each extra library multiplies the testing burden.

## The main gene-set databases

- **GO (Gene Ontology)** — three namespaces: Biological Process (BP), Molecular
  Function (MF), Cellular Component (CC). Hierarchical → highly redundant; collapse
  terms after testing (see `interpretation.md`).
- **KEGG** — manually curated metabolic & signaling pathways. Compact, well known.
- **Reactome** — large, expert-curated, hierarchical human pathway set; good
  granularity. APIs in `database-lookup`.
- **WikiPathways** — community-curated pathways; complements KEGG/Reactome.
- **MSigDB** — collections of collections (Hallmark, curated, GO, immune, etc.);
  the standard source of GMT files for GSEA.

## MSigDB collections

| Collection | Contents |
|-----------|----------|
| **H** (`h.all`) | Hallmark — 50 refined, non-redundant signatures (best default for GSEA) |
| **C2:CP** | Canonical Pathways: `c2.cp.kegg_medicus`, `c2.cp.reactome`, `c2.cp.wikipathways`, `c2.cp.biocarta` |
| **C2:CGP** | Chemical & genetic perturbations |
| **C3** | Regulatory targets (TFT, miRNA) |
| **C5** | Ontology: `c5.go.bp`, `c5.go.mf`, `c5.go.cc`, `c5.hpo` |
| **C6** | Oncogenic signatures |
| **C7** | ImmuneSigDB |
| **C8** | Cell-type signatures |
| **C9** | Computational perturbation signatures from DepMap CRISPR/CCLE analyses |

Current release (reviewed 2026-10-01): **2026.1.Hs / 2026.1.Mm**. Fetch human
Hallmark with `gp.Msigdb.get_gmt(category="h.all", dbver="2026.1.Hs")`.
Mouse uses its own category codes (Hallmark `mh.all`, `m2`, `m5`, etc.); changing
only Hs to Mm is insufficient. List categories for the exact release. Symbols and
Entrez GMTs are available; save the file/hash and comply with MSigDB license terms.
See [gseapy.md](gseapy.md) and the [official collections](https://www.gsea-msigdb.org/gsea/msigdb).

## g:Profiler

The official client (`gprofiler-official`) is the best path when you need a
**custom background**, **many organisms** (discover supported organism codes), or g:Profiler's `g:SCS`
multiple-testing correction. It performs ORA over GO, KEGG, Reactome,
WikiPathways, miRTarBase, CORUM, HP, and more in one call.

```python
from gprofiler import GProfiler

gp = GProfiler(return_dataframe=True)
res = gp.profile(
    organism="hsapiens",                      # mmusculus, dmelanogaster, ...
    query=gene_list,                          # symbols, Ensembl, Entrez — auto-detected
    sources=["GO:BP", "KEGG", "REAC", "WP"],  # restrict sources
    user_threshold=0.05,
    significance_threshold_method="g_SCS",    # default; or "fdr" / "bonferroni"
    domain_scope="custom",                    # use a custom statistical background
    background=expressed_genes,               # the tested/expressed universe
    all_results=True,                        # retain nonsignificant returned terms
    no_evidences=False,                       # required for intersections/evidences
    ordered=False,                           # ranked-prefix ORA is not GSEA
    no_iea=False,                             # True = drop electronic GO annotations
)
# columns: source, native, name, p_value, term_size, query_size,
#          intersection_size, effective_domain_size, intersections
```

`gp.convert(organism="hsapiens", query=ids, target_namespace="ENTREZGENE_ACC")` maps
numeric Entrez IDs. In the live service, target `ENTREZGENE` returned a symbol
(`TP53`), whereas `ENTREZGENE_ACC` returned `7157`; validate the output namespace.
`gp.orth(query=["Trp53"], organism="mmusculus", target="hsapiens")` returns
source `converted`, target `ortholog_ensg`, and target `name`; do not confuse them.

`p_value` is **already adjusted** with the requested method. Do not BH-adjust it
a second time or relabel g:SCS as FDR. `all_results=True` retains nonsignificant
returned terms; it does not promise all database terms including zero overlap.
Save `gp.meta` immediately with results (subsequent calls overwrite it), including
version, effective domains, mapping failures/ambiguities and correction settings.
Client 1.0.0 forces `domain_scope="custom"` whenever background is supplied; it
cannot preserve `custom_annotated` via that method. Use the documented raw API
only if that alternative domain is actually required, and verify echoed metadata.

## Gene-ID types and conversion

Choose one declared namespace and species. Many Enrichr libraries use symbols;
MSigDB also offers numeric Entrez GMTs. Map only when needed and retain the
source-to-target table, failed IDs and ambiguous mappings. No casing operation
constitutes identifier mapping; `capitalize()` can corrupt identifiers.

| You have | Convert with |
|----------|--------------|
| Ensembl gene IDs (`ENSG…`) | `gp.Biomart`, g:Profiler `g:Convert`, or `mygene` |
| Entrez IDs | `mygene`, g:Profiler |
| Mouse symbols → human | g:Profiler `g:Orth` or another explicit orthology resource; querying MyGene with `species="human"` is not orthology conversion |

`mygene` example:
```python
import mygene
mg = mygene.MyGeneInfo()
mapping = mg.querymany(ensembl_ids, scopes="ensembl.gene",
                       fi

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

