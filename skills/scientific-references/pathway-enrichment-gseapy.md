---
id: sciref-pathway-enrichment-gseapy
name: "Scientific Ref: GSEApy reference (tested 1.3.1)"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (pathway-enrichment): GSEApy reference (tested 1.3.1)"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "pathway enrichment gseapy"
  - "gseapy reference (tested 1.3.1)"
keywords:
  - "pathway"
  - "enrichment"
  - "gseapy"
  - "specialized"
  - "scientific"
  - "reference"
---

# GSEApy reference (tested 1.3.1)

Python/Rust implementation, BSD-3-Clause. These patterns require your own validated
inputs; offline numerical/plotting APIs were exercised with synthetic data. See
[verified-api.md](verified-api.md) for online verification and service limitations.

## ORA: online and local

```python
import gseapy as gp
# genes and tested_genes must already use the library's namespace/species.
enr = gp.enrichr(
    gene_list=genes, gene_sets=["MSigDB_Hallmark_2020"], organism="human",
    background=tested_genes, outdir=None,
)
results = enr.results                  # all submitted libraries
```

In 1.3.1, named libraries with a nonempty iterable background use **Speedrichr**.
Without that background, the standard Enrichr service supplies its default.
The public wrapper docstring still says online backgrounds are ignored; released
`enrich_online()` code contradicts that and was tested with mocked transport.
A numeric background count does not select the custom-background route.
Speedrichr's base URL is not organism-specific; use local GMT for custom
backgrounds with fly/fish/worm/yeast rather than assuming the routing is correct.

For offline analysis, pass a GMT/dict **and explicit gene universe**:

```python
sets = gp.read_gmt("pathways.symbols.gmt")
assert set(genes) <= set(tested_genes)
enr = gp.enrich(gene_list=genes, gene_sets=sets,
                background=tested_genes, outdir=None)
```

The local one-sided hypergeometric test intersects each set and query with the
background. `Overlap` is hits / set size after intersection. It returns only
terms with at least one hit and applies BH over those returned terms, not every
zero-hit term in the GMT. If the planned testing family includes all eligible
terms, retain zero-hit tests with p=1 and recompute BH over that full family.
Its `Odds Ratio` includes a 0.5 continuity correction in all four cells; this
need not equal the online service's odds ratio. `Combined Score` is a ranking
heuristic, not an adjusted p-value or biological effect size.

`enr.results` can remain a list when no terms match. Check that it is a DataFrame
before filtering. Standard export, Speedrichr and local results have different
columns: Speedrichr JSON does not include `Overlap`; do not require it universally.
`outdir=None` suppresses result files, but online library downloads may still cache.

## Preranked GSEA

```python
pre = gp.prerank(
    rnk=rnk,                          # unique IDs, finite signed scores, all tested genes
    gene_sets="pathways.symbols.gmt",
    organism="human",                # only routes named Enrichr libraries
    min_size=15, max_size=500,        # matched size after intersection with rank
    method="permutation", permutation_num=1000,
    weight=1.0, seed=123, threads=4, ascending=None, outdir=None,
)
results = pre.res2d
```

Sort `rnk` descending first; `ascending=None` preserves that order, including ties.
The helper uses a stable sort and reports ties. GSEApy itself can uppercase
inputs when sampled gene sets are uppercase; this heuristic is not orthology.
Verify matching IDs beforehand and inspect matched/leading genes afterward. A seed cannot make ambiguous
identifier mapping or arbitrary tied ranks scientifically valid. Check sensitivity
when many ranks tie. Never let upstream duplicate renaming (`GENE_1`) stand in for
resolving multiple probes/transcripts. Do not feed an unsigned DESeq2 LRT statistic
when interpreting positive/negative enrichment; use the signed contrast statistic.

Classic permutation results include `ES`, `NES`, `NOM p-val`, `FDR q-val`,
`FWER p-val`, `Tag %`, `Gene %`, `Lead_genes`. FDR is based on NES nulls and is
scoped by the prefix before `__` in 1.3.1. GSEApy prefixes combined libraries;
avoid `__` inside custom term names unless that grouping is intentional. A single
dict without such prefixes defines one family. The hosted API prose describing
pooled FDR across all named libraries is stale relative to the 1.2.1+ source.

`method="multilevel"` is a separate, optional backend in 1.3.x: supports one
ranked list, `sample_size=101`, `eps=1e-50`, plus `permutation_num` for simple-null
normalization. It estimates smaller tail p-values, uses fgsea-style NES, applies
**BH across all tested terms**, reports `log2err`, and omits `FWER p-val`.
Do not mix its q-values/NES with the classic method without identifying the
backend. The bundled helper deliberately uses `method="permutation"`. In a 1.3.1 native
smoke, extreme sets still returned nominal p=0 despite release notes describing
a p-value floor. Interpret zero as no observed exceedances at the chosen
permutation resolution, never as a mathematically zero probability.

## Standard GSEA (matrix and independent class labels)

```python
result = gp.gsea(
    data=expr_df, gene_sets="pathways.symbols.gmt",  # genes x samples
    cls=["A"] * 7 + ["B"] * 7,                   # aligned with columns
    permutation_type="phenotype", method="signal_to_noise",
    min_size=15, max_size=500, permutation_num=1000,
    seed=123, threads=4, outdir=None,
)
```

Phenotype permutation requires exchangeable independent biological samples;
paired/block/confounded designs need a design-aware analysis upstream, not
unrestricted label shuffling. Signal-to-noise and t-test metrics need at least
three samples per phenotype; the GSEA guide recommends at least seven for
phenotype permutation. For smaller groups, gene-set permutations change the
null and fail to preserve gene correlation; disclose that limitation. Do not
pretend thousands of cells are independent biological replicates.

## ssGSEA and GSVA

```python
ss = gp.ssgsea(data=expr_df, gene_sets="pathways.symbols.gmt",
               sample_norm_method="rank", min_size=15, max_size=500,
               permutation_num=0, outdir=None, threads=4)
scores = ss.res2d.pivot(index="Term", columns="Name", values="NES")
gsva = gp.gsva(data=expr_df, gene_sets="pathways.symbols.gmt",
               kcdf="Gaussian", min_size=15, max_size=500, outdir=None)
```

These are sample-level scores, not differential-enrichment p-values. ssGSEA NES
normalization depends on the submitted score range, so separately processed
cohorts need not be comparable. Choose GSVA `kcdf` for the supplied scale:
Gaussian for continuous/log expression, Poisson for nonnegative counts, or None
for direct ECDF. Do not call pathway-membership scores evidence of activation;
use signed responsive signatures and a study design when that is 

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

