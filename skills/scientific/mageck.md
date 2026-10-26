---
id: sci-mageck
name: "Scientific: mageck"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Analyzes pooled CRISPR screen FASTQ reads and guide-count matrices with MAGeCK, validates guide libraries and contrasts, measures replicate and library QC, and produces gene hit rankings with effect sizes and FDR. Use for new knockout, CRISPRi, or CRISPRa screen analysis, enrichm"
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "mageck"
keywords:
  - "mageck"
  - "analyzes"
  - "pooled"
  - "crispr"
  - "screen"
  - "fastq"
  - "reads"
---

# MAGeCK pooled-screen analysis

## When to use

Use this skill to count existing sequencing reads against a supplied guide library or compare
already-counted pooled screens. Deliver the count matrix, QC, guide and gene results, contrast
provenance, and a short interpretation of enrichment/depletion. This workflow analyzes screens;
it does not design guides or infer gene function from a hit alone.

## Runtime

The tested source installation and external-runtime caveat are in
[references/runtime.md](references/runtime.md). Verify both `mageck --version` and
`mageck test --help` before an analysis. The bundled Python helper is standard-library only.
MAGeCK itself also needs NumPy, SciPy, and the `RRA` binary. PDF/R reporting is optional and not
needed by the helper.

The [official release directory](https://sourceforge.net/projects/mageck/files/0.5/) still lists
0.5.9.5 as its latest MAGeCK release. Upstream now links the separate
[MAGeCK2 project](https://github.com/davidliwei/mageck2); these commands and the helper target
MAGeCK 0.5.9.5, not an interchangeable MAGeCK2 installation. This is a local CLI workflow with
no service API or authentication.

## Workflow

1. Establish the library version, perturbation modality, sample names, selection direction,
   biological replicates, baseline material, time point, and batch. Separate sequencing lanes
   from independent biological replicates. A plasmid baseline and a cell day-zero baseline
   answer different questions. Require an explicit treatment/control contrast; the helper
   never silently assigns all unused samples to the control group.
2. Validate a **headerless TSV library** containing guide ID, DNA sequence, gene. IDs and
   sequences must be unique. The helper requires a count-table header beginning `sgRNA`, `Gene`,
   followed by unique nonnumeric sample names such as `c1`. MAGeCK can interpret numeric names
   as column indices or count values; rename them before analysis. Guide/gene IDs must have no
   whitespace. The helper rejects ambiguous sequences and any count/library ID or gene mismatch;
   resolve intentional multi-target guides explicitly upstream. These are deliberate helper
   restrictions; native MAGeCK also accepts other input variants.
3. For FASTQ, inspect read structure and known guide sequences to establish trimming and
   orientation. Use MAGeCK `count`, with one space-separated argument per biological sample;
   comma-join lanes only when they are technical replicates of that same sample. Preserve
   unmapped-read and count-summary evidence when mapping is poor. A zero-count guide remains
   in the library; do not drop it to improve QC.
4. Run QC before statistical testing. Review library representation, median reads per guide,
   zero fractions, Gini coefficients, and within-condition replicate correlations. The
   helper's 10% zero and 0.8 correlation flags are review prompts, not universal acceptance
   thresholds. High correlation can coexist with systematic artifacts. Read depth is not
   experimental cell coverage. The helper uses a raw-count population Gini; MAGeCK's native
   count-summary Gini uses log(count + 1) with a finite-sample correction. Do not compare their
   values or thresholds as the same statistic.
5. Choose normalization based on the screen. Median normalization assumes most guides are
   stable. For a strong global shift, supplied validated negative-control guides may support
   `--normalization control`. These must be **guide IDs**, one per line; a gene list is not
   interchangeable. Biological control samples and negative-control guides serve different
   roles. At least two controls must be present, and every guide assigned to a control gene
   must be designated a control. Supplying `--control-guides` also changes the RRA null distribution,
   even with median normalization. Record their origin and check their count distribution.
   MAGeCK 0.5.9.5 switches median normalization to total-count scaling for a zero median or
   more than 45% zero guides in any selected sample; for control normalization it evaluates
   the control-guide subset. Check the report's applied method, size factors, and warnings.
6. Use `test` for a two-group comparison. `--paired` requires both lists in corresponding
   biological order and equal length; matching lengths alone do not establish pairing.
   The helper reports genes at the requested FDR in both directions and retains full rankings.
   For a multi-factor design, see [references/design.md](references/design.md); do not collapse
   batches or time courses into an unjustified two-group test.
7. Inspect guide concordance for leading genes, essential-gene recovery where appropriate,
   negative controls, replicate consistency, and copy-number artifacts in nuclease knockout
   screens. Report effect sizes alongside FDR. An enriched guide can indicate resistance,
   growth advantage, or a sampling artifact depending on the selection; depletion need not
   imply universal essentiality. Lack of replication or low-count guides weakens inference.

## Commands

Run paths relative to the installed skill directory. Input and output paths refer to the user's
analysis directory. The helper refuses to reuse an existing results directory.

```bash
# Single-end guide reads; trim and orientation must match the user's library preparation.
mageck count -l library.tsv --fastq c1.fastq.gz c2.fastq.gz t1.fastq.gz t2.fastq.gz \
  --sample-label c1,c2,t1,t2 --trim-5 0 --norm-method none -n counts

python scripts/screen_analysis.py qc --counts counts.count.txt --library library.tsv \
  --control c1 c2 --treatment t1 t2 --output qc.json

python scripts/screen_analysis.py test --counts counts.count.txt --library library.tsv \
  --control c1 c2 --treatment t1 t2 --normalization median --fdr 0.05 --output result
```

The FASTQ command structure was exercised with a synthetic two-guide library: counts of 30 and
12 were recovered exactly. A separate trimmed, reverse-complemented, two-lane fixture recovered
15, 7, and 0 reads. The two-group helper was exercised with 500 guides and two replicates per
condition in unpaired and paired modes; known depleted and enriched genes ranked first in their
respective directions and passed FDR 0.05. Sparse fixtures verified the total-normalization fallback.
These tests establish execution and signal direction, not real-screen statistical calibration.
Real-file paths above are illustrative.

`result/report.json` records count/library/co

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

