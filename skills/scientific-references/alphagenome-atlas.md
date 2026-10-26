---
id: sciref-alphagenome-atlas
name: "Scientific Ref: AlphaGenome Atlas: data model, scorers, AVI, and access"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (alphagenome): AlphaGenome Atlas: data model, scorers, AVI, and access"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "alphagenome atlas"
  - "alphagenome atlas: data model, scorers, avi, and access"
keywords:
  - "alphagenome"
  - "atlas"
  - "specialized"
  - "scientific"
  - "reference"
---

# AlphaGenome Atlas: data model, scorers, AVI, and access

Reviewed 2026-09-30 against `alphagenome` 0.9.0 (released 2026-09-08, the first version
with `alphagenome.atlas`), the Atlas technical report (Cheng, Taylor,
Nicolaisen, Pan, Bycroft, Perino, Ward, *et al.*, "AlphaGenome Atlas: in silico
mutagenesis of the entire human genome improves prioritization and
interpretation of non-coding variants", 2026 preprint), and DeepMind's own
Atlas agent skills in `google-deepmind/science-skills`. Source and local SDK checks cover the client contracts below. No authenticated
Atlas query was run in this review; server-side catalogues and portal rendering
remain unverified. The report now has medRxiv DOI
[10.64898/2026.09.16.26363192](https://doi.org/10.64898/2026.09.16.26363192).

## What is in the Atlas

| Item | Value |
| --- | --- |
| Genome build | GRCh38 / hg38 only. Gene annotations: GENCODE v46. |
| Variants | Every possible SNV at every non-`N` reference base (about 9 billion). Over 100 million observed indels (gnomAD v4.1, UK Biobank, All of Us) were scored for the paper, but the public API is currently limited to SNVs; indel expansion is promised "upon final publication". |
| Model | The distilled AlphaGenome model, 1 Mb input centred on a 128 bp scoring window (so a variant sits within 64 bp of the centre; the paper shows this does not change scores). |
| Per-variant content | Raw scores for every track of 19 recommended scorer configurations (about 27,000 scalars per variant, about 15,000 without the `_ACTIVE` scorers), the AVI score with its quantile, 18 SHAP feature attributions, and motif instances. |
| Motifs | 2,601 motifs (94 main TF labels, 122 zinc-finger labels, 464 composite patterns) and about 253 billion motif instances. Browsable on the portal; bulk download promised. |
| Size | About 1 PB. |

### Index key semantics

Each record is keyed by `chromosome:position:alt` on GRCh38. The REF allele is
implied by the reference and is **not** part of the key, so:

- a variant written with REF and ALT swapped (for example minor-allele-first
  from a GWAS table) can produce a **lookup miss**;
- non-reference to non-reference substitutions do not exist;
- positions where the reference is `N` were never scored;
- GRCh37 coordinates return wrong-but-plausible answers. Lift over first.

The SDK sends the full variant (including REF) and returns the server variant
in `obs["variant"]`; these helpers reject a response with a different variant
identity. Do not assume the service independently validates REF or the assembly.
Check REF against the reference FASTA before trusting any Atlas result
(`genomic-coordinates` has `normalize_variant.py` and `check_contigs.py`).

## The scorers (Table S1 of the report)

`requested_scorers=` takes these names. Track counts are for human; the
`_ACTIVE` names match the SDK recommended configuration keys, but the served Atlas
catalogue was not checked with an authenticated `scorer_metadata()` call.

| Name | Scorer class | Parameters | Biosamples | Tracks | Signed | Obs axis |
| --- | --- | --- | --- | --- | --- | --- |
| `ATAC` | CenterMaskScorer | width 501, DIFF_LOG2_SUM | 167 | 167 | yes | variant |
| `DNASE` | CenterMaskScorer | width 501, DIFF_LOG2_SUM | 305 | 305 | yes | variant |
| `CHIP_TF` | CenterMaskScorer | width 501, DIFF_LOG2_SUM | 163 | 1,617 | yes | variant |
| `CHIP_HISTONE` | CenterMaskScorer | width 2001, DIFF_LOG2_SUM | 219 | 1,116 | yes | variant |
| `CAGE` | CenterMaskScorer | width 501, DIFF_LOG2_SUM | 264 | 546 | yes | variant |
| `PROCAP` | CenterMaskScorer | width 501, DIFF_LOG2_SUM | 6 | 12 | yes | variant |
| `RNA_SEQ` | GeneMaskLFCScorer | natural-log fold change over exons | 285 | 371 | yes | variant x gene |
| `POLYADENYLATION` | PolyadenylationScorer | max log-fold change of isoform ratio | 285 | 371 | no | variant x gene |
| `SPLICE_SITES` | GeneMaskSplicingScorer | SPLICE_SITES, width None | - | 2 (donor, acceptor) | no | variant x gene |
| `SPLICE_SITE_USAGE` | GeneMaskSplicingScorer | SPLICE_SITE_USAGE, width None | 282 | 367 | no | variant x gene |
| `SPLICE_JUNCTIONS` | SpliceJunctionScorer | | 282 | 367 | no | variant x junction |
| `CONTACT_MAPS` | ContactMapScorer | | 12 | 28 | no | variant |
| `*_ACTIVE` (ATAC, DNASE, CHIP_TF, CHIP_HISTONE, CAGE, PROCAP, RNA_SEQ) | same widths, ACTIVE_SUM / GeneMaskActiveScorer | absolute activity of the stronger allele, not a difference | as above | as above | no | as above |
| `AVI_SCORE` | composite | one score per variant | - | 1 | no | variant |
| `AVI_SCORE_FEATURE_IMPORTANCE` | SHAP | 18 attribution values | - | 18 | yes | variant |

"Signed" raw scorers can go negative (ALT lowers the signal). Their calibrated
quantiles are on `[-1, 1]` (CDF `p` mapped to `2*p-1`); unsigned scorers
use `[0, 1]`. Use `abs(quantile_score)` for the CLI magnitude filter.
The AVI CDF described below is unsigned and has its own background. These
semantics follow the official scoring FAQ; authenticated Atlas quantile values
were not checked in this review. For unsigned effect scorers the direction is
not meaningful; `_ACTIVE` ranks activity rather than an allelic change.

Table S1 totals 9,440 scorer-track entries, including repeated tracks for
active and difference scorers; it is not 9,440 distinct model outputs. `python scripts/atlas_query.py tracks
--scorer RNA_SEQ --query liver` shows the metadata for any of them.

## AlphaGenome Variant Impact (AVI)

AVI is a small neural network trained on **proxy labels**: gnomAD v4.1 variants
with a group-maximum filtering allele frequency above 0.001 are "proxy benign"
(about 2e7), below 0.001 "proxy impactful" (about 1e8). It therefore learns to
rank variants by how strongly negative selection appears to act on them, using
18 features:

| Group | Features (`var['name']` keys) |
| --- | --- |
| AlphaGenome, max absolute effect across all tracks and genes | `MAX_ABS_ATAC`, `MAX_ABS_DNASE`, `MAX_ABS_CHIP_TF`, `MAX_ABS_CHIP_HISTONE`, `MAX_ABS_CAGE`, `MAX_ABS_PROCAP`, `MAX_ABS_RNA_SEQ`, `MAX_ABS_POLYADENYLATION`, `MAX_ABS_CONTACT_MAPS` |
| AlphaGenome splicing (sites + usage + junctions/5, each max over genes) | `MERGED_SPLICING` |
| Protein | `ALPHAMISSENSE` (0 when there is no AlphaMissense prediction) |
| Conservation | `CACTUS_241_WAY` (Zoonomia phyloP, range -20 to 8.9), `PHASTCONS_470_WAY` |
| VEP loss-of-function indicators | `PROTEIN_TERMINATION` (stop gained or frameshift), `START_LOST`, `STOP_LOST` |
| Indel type | `IS_INSERTION`, `IS_DEL

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

