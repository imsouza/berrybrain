---
id: sciref-alphagenome-interpretation
name: "Scientific Ref: Interpreting AlphaGenome and Atlas scores"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (alphagenome): Interpreting AlphaGenome and Atlas scores"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "alphagenome interpretation"
  - "interpreting alphagenome and atlas scores"
keywords:
  - "alphagenome"
  - "interpretation"
  - "specialized"
  - "scientific"
  - "reference"
  - "interpreting"
---

# Interpreting AlphaGenome and Atlas scores

Distilled from the AlphaGenome and Atlas papers, the official FAQ, and the
interpretation guide DeepMind ships with its own AlphaGenome agent skill.
Reviewed against official scoring definitions and model source on 2026-09-30.
These rules describe predictions, not established effects in a patient.

## The frame

AlphaGenome predicts what a genomics assay would read out from a DNA sequence.
An Atlas or model score is therefore a **predicted molecular effect in a
biosample the model was trained on**, nothing more:

- It is not pathogenicity. AVI is trained to separate rare from common
  variants; that correlates with impact and is validated on ClinVar, but a high
  AVI is one line of evidence in a chain, "not sufficient evidence on its own"
  (Atlas report, Discussion).
- It is not a measurement. Predictions are correlative and can be wrong in
  either direction; independent epigenomic or functional data decides.
- It is not clinical. Terms of use and the report both exclude diagnostic use.
  Never turn a score into a diagnosis, penetrance, prognosis, or treatment
  statement. If the question is clinical, answer about molecular mechanism and
  say so.

## Raw score and quantile: always both

| Quantity | What it is | Use it for |
| --- | --- | --- |
| `raw_score` | effect size on the scorer's own scale (RNA_SEQ: natural-log fold change with 0.001 pseudocount; center-mask scorers: log2 ratio of summed signal; splicing: change in probability or usage) | magnitude, direction, comparing tissues **within one scorer** |
| `quantile_score` | rank against common variants (gnomAD v3 MAF > 0.01), signed scorers map CDF p to 2p-1; unsigned retain p; finite ranks saturate near 1 | unusualness; comparing across scorers |
| AVI `avi_raw` | composite model output | ranking within a set |
| AVI Phred | -10 log10(1 - cdf); 10 / 20 / 30 = top 10 % / 1 % / 0.1 % of all SNVs | genome-wide rank, thresholds |

For `RNA_SEQ`, the scorer is
`ln(mean ALT + 0.001) - ln(mean REF + 0.001)`. Thus `exp(raw_score)`
is the ratio of pseudocount-adjusted means: -1 is about 0.37x, not 0.5x;
`ln(2)` is about 0.693. At very low expression the pseudocount matters, so
inspect baseline tracks before translating a score into a biological fold change.
Recommended center-mask accessibility/TF/TSS scorers instead use a **log2**
ratio of summed signal with a +1 pseudocount. `RNA_SEQ_ACTIVE` is the larger
mean activity, with no log transform. Never apply one scorer's scale to another.

The scripts' `--min-abs-quantile 0.99` keeps signed quantiles at or beyond
+/-0.99 (the two 0.5% CDF tails), or unsigned quantiles >=0.99 (the upper 1%).
It does not retain small unsigned scores near zero. Missing calibration does
not pass this filter; mouse and custom scorers may have only raw scores.
AVI has a separate genome-wide SNV CDF and Phred transformation.
Quantiles are ranks, not significance tests or evidence of benignity. See the
[official scoring definitions](https://www.alphagenomedocs.com/variant_scoring.html)
and [calibration FAQ](https://www.alphagenomedocs.com/faqs.html).

**The common trap: high quantile, tiny raw score.** In low-expression genes and
quiet regions the background distribution is so narrow that a raw change of
0.05 ranks above 0.99. Report a small predicted change in the named track and
inspect the baseline signal; this does not establish a statistically nonsignificant
or biologically absent effect. Conversely a raw -1.5 with quantile 0.9 in a highly variable track is
still a large predicted effect worth mentioning.

Unsigned scorers (`POLYADENYLATION`, `SPLICE_*`, `CONTACT_MAPS`, all
`*_ACTIVE`) have no direction; `*_ACTIVE` scores are the activity of the
stronger allele and cannot be read as a difference at all.

## AVI thresholds

The report recommends **ranking over hard cut-offs** and thresholds that are
"genomic region- or application-aware": pathogenic regulatory variants sit in
lower AVI bins than pathogenic protein-truncating or splice-motif variants, so a
single genome-wide Phred cut-off systematically under-calls regulatory hits.
Practical pattern:

1. Rank the candidate set by Phred and report the ranks.
2. State the top-percentile the Phred implies (Phred 20 = top 1 % of SNVs).
3. Read the feature attribution. `MERGED_SPLICING` or `ALPHAMISSENSE` dominant
   means a coding or splice mechanism; `MAX_ABS_DNASE` / `MAX_ABS_CHIP_TF` /
   `MAX_ABS_RNA_SEQ` mean a regulatory mechanism you can drill into by track;
   `CACTUS_241_WAY` / `PHASTCONS_470_WAY` dominant means conservation is
   carrying the score and the molecular mechanism is **not** resolved by AVI.
4. Only then drill into the per-track scores for the matched tissue.

## Tissue matching

- Choose biosamples by the disease's organ system and cell type, resolved to
  ontology terms, not by name similarity. Cardiac muscle is not smooth muscle;
  a fibroblast line is not brain.
- Report both the tissue with the largest predicted effect and the
  disease-relevant tissue, even when the latter shows nothing. An unexpected
  top tissue is a finding; a silent relevant tissue is also a finding.
- If the specific cell type has no track, fall back to the organ and say so.
- Evidence from an unrelated tissue is evidence about a different question.

## Negative results

A flat prediction does not establish that a variant is benign. "AlphaGenome predicts no
appreciable change in the queried DNase and RNA-seq tracks" is a complete,
valuable answer. Do not invent a cryptic splice site or an enhancer disruption
that the tracks do not show; do not infer disruption from location in a peak
when REF and ALT tracks are identical.

## What the model cannot see

- **Trans effects.** Only cis-regulatory grammar in a 1 Mb window; nothing about
  TF abundance, signalling, or the rest of the genome.
- **Training-data gaps.** RNA-seq training includes poly(A)+ and total RNA assays,
  with uneven coverage of non-polyadenylated RNAs (including snRNAs);
  inspect the relevant assay before claiming the model captures them. Many cell types are absent;
  coverage is uneven across assays. A flat prediction in an untrained cell type
  is absence of data, not absence of effect.
- **Protein-level consequences.** Missense stability, catalysis, folding: use
  AlphaMissense (already an AVI feature) or protein tools.
- **Post-transcriptional biology** beyond splicing and polyadenylation: RNA
  structure, miRNA processing, localisation, tra

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

