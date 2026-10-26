---
id: sci-alphagenome
name: "Scientific: alphagenome"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Looks up precomputed AlphaGenome Atlas effects for any GRCh38 single-nucleotide variant (AVI score with Phred and 18 SHAP feature attributions, plus raw and quantile scores for RNA-seq, DNase, ATAC, ChIP-TF, ChIP-histone, CAGE, PRO-cap, splicing, polyadenylation and contact-map t"
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "alphagenome"
keywords:
  - "alphagenome"
  - "looks"
  - "precomputed"
  - "atlas"
  - "effects"
  - "grch"
---

# AlphaGenome and the AlphaGenome Atlas

AlphaGenome is DeepMind's sequence-to-function model: 1 Mb of DNA in,
predictions at modality-specific resolutions for eleven assay types across
thousands of human and mouse tracks out. The **AlphaGenome Atlas** (released 2026-09-08) is that model run once over
every possible single-nucleotide change in GRCh38, about 9 billion variants,
stored with a single ranking number, the **AlphaGenome Variant Impact (AVI)**
score, its genome-wide percentile, and an 18-way attribution of what drives it.
Both are reached through one `pip install alphagenome` and one API key.

> Research and theoretical modelling only. API outputs must not be used to train
> other models, and are not for diagnostic procedures or medical decisions.
> Permissive-use downloads have separate terms; check the artifact licence.

## When to use which

| You have | Use | Why |
| --- | --- | --- |
| hg38 SNVs (a VCF, a credible set, a region up to ~1 kb) | **Atlas** via `scripts/atlas_query.py` | precomputed, higher quota, includes AVI and attributions |
| indels, mouse variants, a non-reference background, a custom scorer or window | **model** via `scripts/score_variants.py` or Python | the Atlas is SNV-only and hg38-only |
| a hypothesis to explain (which motif, which tissue, REF vs ALT tracks) | model `predict_variant` + plots, Atlas track scores, portal link | mechanism, not just rank |
| GRCh37 coordinates, rsIDs, unnormalised indels | `genomic-coordinates` first, then come back | wrong build or swapped REF gives a plausible wrong answer |
| ClinVar assertions, gene-disease validity, ACMG framing | `folklore-variant-evidence`, `database-lookup` | AlphaGenome is one evidence line, never the verdict |
| promoter/enhancer/expression predictions without a DeepMind key | `genomic-intelligence` | different provider, keyless demo tier |

## Setup

```bash
uv pip install alphagenome                     # PyPI; tested on Python 3.12 and 3.13, alphagenome 0.9.0
export ALPHAGENOME_API_KEY="..."               # https://deepmind.google.com/science/alphagenome
cd skills/alphagenome/scripts
python atlas_query.py scorers                  # proves key + network in one call
```

Shell examples quote variant strings because `>` otherwise redirects output.
Network examples below are illustrative and were checked against SDK 0.9.0
contracts, without authenticated prediction/Atlas calls during this review.

Never put the key on a command line or in a file you commit; the scripts only
read it from the environment. Authentication failures may surface as
`ValueError` or `PermissionError`,
depending on the gRPC status returned by the service.

## The coordinate contract

- A variant is **1-based** `chr:pos:ref>alt` (`chr22:36201698:A>C`). gnomAD
  (`22-36201698-A-C`), GTEx (`chr22_36201698_A_C_b38`), and Open Targets
  spellings are autodetected by the scripts. In the SDK, pass the matching
  `variant_format=genome.VariantFormat.GNOMAD` (or `GTEX`, `OPEN_TARGETS`,
  `OPEN_TARGETS_BIGQUERY`); `from_str` defaults to `chr:pos:ref>alt`.
- An interval on the command line is **1-based closed** `chr:start-end`; the
  SDK's `genome.Interval` is **0-based half-open**. The scripts convert.
- Human is **GRCh38 only**. The Atlas key is `chr:pos:alt`; REF is implied by
  the reference. Swapping REF/ALT can cause a miss; a wrong REF or build can
  misidentify a record. The scripts reject a returned variant that differs
  from the request, but cannot validate the build. Check REF against GRCh38 FASTA.
- rsIDs are not accepted by the API or the portal. Resolve them to coordinates.
- Use the `chr` prefix; `MT` becomes `chrM`.

## Atlas workflow

### 1. Rank with AVI

```bash
python atlas_query.py avi --variant "chr22:36201698:A>C" "chr9:128225994:G>A"
python atlas_query.py avi --input candidates.vcf --min-phred 20 -o avi.tsv
python atlas_query.py avi --interval chr11:5225727-5226575 --top-k 25 -o hbb_window.tsv
python atlas_query.py avi --input credible_set.tsv --with-tracks -o avi_tracks.tsv
```

Output, one row per variant:

| Column | Meaning |
| --- | --- |
| `avi_raw` | composite model output (the 18 attributions sum to it) |
| `avi_cdf_quantile` | cumulative quantile against all genome-wide SNVs, as served |
| `avi_tail_quantile`, `avi_phred`, `avi_top_percent` | `tail = 1 - cdf`, `phred = -10 log10(tail)`; Phred 20 = top 1 %, 30 = top 0.1 % |
| `top_feature`, `top_feature_value` | largest absolute SHAP attribution and its value |
| `fi_MERGED_SPLICING` ... `fi_IS_DELETION` | all 18 attributions (keys in `references/atlas.md`) |
| `top_track_*` (with `--with-tracks`) | the strongest track behind the top feature: scorer, track, biosample, ontology CURIE, gene, raw score |
| `atlas_url` | deep link to the variant on the portal |
| `error` | per-variant lookup failure or mismatched returned allele instead of a crash |

The Atlas report's advice: **rank, do not threshold**, and pick thresholds by
region or application. Pathogenic regulatory variants sit in lower AVI bins
than protein-truncating or splice-motif variants, so a single genome-wide
cut-off under-calls exactly the variants this resource was built for.

Read the attribution before the number. `MERGED_SPLICING` or `ALPHAMISSENSE`
on top means a splice or coding mechanism; `MAX_ABS_DNASE`, `MAX_ABS_CHIP_TF`,
`MAX_ABS_RNA_SEQ` mean a regulatory mechanism you can resolve by track;
`CACTUS_241_WAY` or `PHASTCONS_470_WAY` on top means conservation is carrying
the score and the molecular mechanism is not resolved.

### 2. Resolve the mechanism by track

```bash
python atlas_query.py scorers                                   # what the server serves right now
python atlas_query.py tracks --scorer RNA_SEQ --query colon     # find ontology CURIEs
python atlas_query.py scores --variant "chr22:36201698:A>C" \
    --scorers RNA_SEQ DNASE SPLICE_SITE_USAGE --ontology UBERON:0001157 -o colon.tsv
python atlas_query.py scores --interval chr11:5225727-5226575 --scorers CHIP_TF -o hbb_tf.tsv
```

One row per variant x track (x gene or splice junction where applicable),
with `raw_score` and, where served, `quantile_score`. Track-level
scorer names: `ATAC`, `DNASE`, `CHIP_TF`, `CHIP_HISTONE`, `CAGE`, `PROCAP`,
`RNA_SEQ`, `POLYADENYLATION`, `SPLICE_SITES`, `SPLICE_SITE_USAGE`,
`SPLICE_JUNCTIONS`, `CONTACT_MAPS`, plus `*_ACTIVE` variants; `scorers` is the
authority on the live list. Filter by the tissue the question is about, not
by the genome-wide maximum: 9,440 scorer-trac

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

