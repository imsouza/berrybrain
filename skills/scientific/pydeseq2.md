---
id: sci-pydeseq2
name: "Scientific: pydeseq2"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Performs bulk RNA-seq differential expression analysis with PyDESeq2, including count validation, formula designs, explicit contrasts, Wald tests, FDR correction, coefficient-matched LFC shrinkage, and result visualization. Use for PyDESeq2 or Python DESeq2 workflows with biologi"
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "pydeseq2"
keywords:
  - "pydeseq2"
  - "performs"
  - "bulk"
  - "differential"
  - "expression"
  - "analysis"
  - "pydeseq"
---

# PyDESeq2

Use this skill for bulk RNA-seq negative-binomial GLMs, with explicit biological
replicates, covariates, and comparisons. Cells, sequencing lanes, and repeated
measurements from the same donor are not independent biological replicates.
Donor-level pseudobulk can be appropriate when its aggregation and design match
the scientific question; this is not a single-cell per-cell testing workflow.

Current [PyDESeq2 0.5.4](https://github.com/scverse/PyDESeq2/releases/tag/v0.5.4)
provides Wald tests and apeGLM-style coefficient shrinkage. Do not assume every
feature or numerical result of current R DESeq2 is implemented identically.
See [API and tested versions](references/api_reference.md) for supported calls,
AnnData storage, and source/runtime verification limits.

## Analysis contract

1. Establish the experimental unit, count provenance, sample exclusions, reference
   levels, and intended comparison before fitting. Use nonnegative integer counts
   in **samples × genes** order, with unique sample/gene IDs. TPM, FPKM, log data,
   VST data, and library-normalized counts are not model inputs. Integer checks
   alone cannot establish raw-count provenance. Approved estimated-count imports
   need an explicit upstream conversion and offset/length-correction policy.
2. Require equal sample sets and reorder metadata to the count index. Resolve
   unmatched IDs and missing design annotations explicitly; never silently take
   an intersection. Determine orientation from the file schema, not its shape.
3. Apply a prespecified gene prefilter after intentional sample exclusions. Total
   counts >=10 is a small example rule, not a universal biological threshold.
   Keep enough genes to estimate normalization and dispersion trends jointly.
4. Build a full-rank formula design with residual degrees of freedom. Explicitly
   encode categories/reference levels; numeric variables are continuous. Formula
   term order does not decide the tested effect when a contrast is explicit.
5. Fit size factors, gene-wise/trend/MAP dispersions, LFCs, and Cook diagnostics.
   Inspect warnings, convergence and normalization assumptions before interpreting
   results. Large size factors can reflect real library-depth differences.
6. Test an explicit contrast with the intended `alpha`, preserve the full Wald
   table, and optionally shrink the **same single positive coefficient**. Export
   counts/model metadata separately from statistical results.

## Quick start

Install in an isolated environment; the repository test runner supplies the
scientific dependencies separately from the project environment:

```bash
uv venv --python 3.13 .venv-pydeseq2
uv pip install --python .venv-pydeseq2/bin/python 'pydeseq2==0.5.4' 'anndata==0.13.4'
```

Paths below are illustrative; run from this skill directory with your own files.
The bundled driver expects counts CSV as **genes × samples** by default, and
metadata CSV as samples × annotations, each with IDs in its first column:

```bash
python scripts/run_deseq2_analysis.py \
  --counts counts.csv --metadata metadata.csv \
  --design '~batch + condition' --contrast condition treated control \
  --min-counts 10 --alpha 0.05 --n-cpus 1 --plots --output results/
```

Use `--no-transpose` for a counts file already in samples × genes order. The driver
rejects duplicate source CSV headers, unequal sample sets, invalid count values,
zero-count samples, missing contrast annotations, and unidentifiable designs. It
sets the CLI contrast variable's reference level before fitting; numeric category
codes supplied as the contrast variable are deliberately treated as categories.
Resolve other design variables' types and missing values in the input metadata.

The driver performs Wald testing and shrinkage by default. `--no-shrink` exports
only unshrunk effect estimates; `--shrink-coeff` can select only the coefficient
that exactly matches the tested contrast. For interactions, continuous effects,
or custom design matrices, use the Python patterns rather than guessing a CLI
coefficient. The CLI does not expose thresholded tests or alternative normalization
methods; use the API for those choices.

Outputs:

- `deseq2_results.csv`: current estimates (shrunken if requested) with original
  Wald `stat`, `pvalue`, and `padj`.
- `deseq2_results_unshrunken.csv`: preserved original Wald table.
- `significant_genes.csv` and `results_sorted_by_padj.csv`: the configured `alpha`
  selects the significant table; missing `padj` is never significant.
- `deseq_dataset.h5ad`: fitted AnnData snapshot for inspection, with counts and
  model fields; it is not a reconstituted `DeseqDataSet` or a `DeseqStats` object.
- `analysis_manifest.json`: contrast, alpha, shrinkage coefficient, and versions.
- With `--plots`: volcano and MA PNGs using the same alpha. Missing adjusted
  p-values stay missing; zero adjusted p-values are capped only for plotting.

Use a fresh output directory for each run. Record input provenance and sample/gene
exclusion decisions alongside these files.

## Statistical interpretation

Positive `log2FoldChange` for `['condition', 'treated', 'control']` means
**treated / control**. A `padj < alpha` rule controls the selected multiple-testing
procedure under its assumptions; it is not the probability that an individual
result is false. BH adjustment within each contrast does not jointly adjust all
contrasts in a multi-comparison analysis.

Separate a descriptive `abs(log2FoldChange) > 1` filter from a formal test of an
effect exceeding one log2 unit (`lfc_null=1`, `alt_hypothesis='greaterAbs'`).
Thresholded or one-sided statistics are not automatically suitable signed
preranking scores.

Missing p-values can result from all-zero genes or Cook filtering; independent
filtering may leave a finite p-value with missing `padj`. Preserve these distinctions
and report how many genes received finite tests. Do not replace missing values with
zero or one in result tables.

For standard two-sided zero-null Wald tests, preranked enrichment commonly uses
finite **signed `stat` values from the unshrunken table**, including eligible genes
that are not significant. Inspect Cook-filtered rows (a statistic can remain finite
while its p-value is missing), identifier mappings, and tied scores. Do not use an
unsigned DESeq2 LRT statistic, absolute LFC, or a thresholded hit list as this signed
ranking. ORA instead needs a prespecified hit rule and the tested/detectable mapped
background. A product such as `-l

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

