---
id: sci-waypoint-bio
name: "Scientific: waypoint-bio"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Supports work with Outpost Bio's open microbiome foundation models - the Waypoint checkpoints (Waypoint-6m, Waypoint-45m, Waypoint-170m), the Atlas pretraining corpus, the Compass eight-task benchmark, or the `waypoint` CLI from the `waypoint-bio` package. Covers embedding microb"
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "waypoint bio"
  - "waypoint-bio"
keywords:
  - "waypoint"
  - "bio"
  - "supports"
  - "work"
  - "outpost"
  - "open"
  - "microbiome"
  - "foundation"
---

# Waypoint: Outpost Bio's Open Microbiome Foundation Models

## Overview

Outpost Bio open-sourced three artefacts under Apache 2.0, described in
[Treloar et al., bioRxiv 2026.05.02.722381](https://www.biorxiv.org/content/10.64898/2026.05.02.722381v2):

| Artefact | What it is | Hugging Face |
| --- | --- | --- |
| **Waypoint** | GPT-2-style causal LMs over taxonomic tokens, 6M–170M params | `outpost-bio/Waypoint-6m`, `-45m`, `-170m` |
| **Atlas** | 539,308 microbiome samples scraped from MGnify (485,377 pretrain / 53,931 benchmark) | `outpost-bio/Atlas` |
| **Compass** | Eight downstream tasks over four studies | `outpost-bio/Compass` |

The unifying idea: a microbiome sample is a *sentence*. Each taxon is one token, tokens are ordered
by descending abundance z-score, and the model is trained with next-token prediction. A pretrained
checkpoint then supplies sample-level embeddings or a fine-tuning backbone for prediction tasks.

All of it is driven by one CLI, `waypoint`, with five subcommands: `prepare-dataset`, `embed`,
`finetune`, `benchmark`, `pretrain`.

## When to use

- Embedding 16S/shotgun taxonomic profiles into fixed-size vectors for clustering, visualisation, or
  a downstream classifier.
- Fine-tuning a Waypoint checkpoint to predict a phenotype, treatment, or continuous readout from
  community composition.
- Scoring your own microbiome model on Compass with an explicitly recorded protocol.
- Pretraining a taxonomic language model on Atlas or on your own corpus.
- Converting profiler output (MetaPhlAn, Kraken2/Bracken, QIIME 2, MGnify TSVs) into the input format
  these tools expect.

For small labelled datasets, start with a random-forest baseline and grouped validation. The
paper's sample-size crossover is an empirical result from its experiments, not a universal cutoff
for using embeddings or a guarantee of performance on a new study.

## Setup

```bash
pip install "waypoint-bio==1.0.2" "transformers==4.57.6" "peft==0.18.1" "huggingface-hub<1"
```

The 2026-10-01 review checked the published wheel, GitHub main `f45eee6d07a480bfc90f84ab8082bbc969dec15d`
(1.0.4), and current Hub metadata. Small native CPU/tokenizer tests used Python 3.12, Torch
2.14.1, Transformers 4.57.6, PEFT 0.18.1 and pandas 3.0.6; no pretrained weights or gated rows
were downloaded. The package leaves dependencies unbounded: Transformers 5 removes its
pretraining `logging_dir` argument. Keep a separate compatible environment.

**Upstream limitations:** local `TaxonomicTokenizer.save_pretrained()` raises
`NotImplementedError` in both reviewed versions, blocking `pretrain` before training and
`finetune` export when using that local tokenizer. Released 1.0.2 does not merge LoRA adapters
or write training logs; GitHub 1.0.4 does. See `references/upstream-review.md` before training.
Training examples below are source-checked templates, not completed scientific runs.

Atlas, Compass, and every Waypoint checkpoint are **gated**. Access is auto-approved, but you must
click through once per repo and then authenticate:

1. Request access on each repo page you need: [Waypoint-6m](https://huggingface.co/outpost-bio/Waypoint-6m),
   [Waypoint-45m](https://huggingface.co/outpost-bio/Waypoint-45m),
   [Waypoint-170m](https://huggingface.co/outpost-bio/Waypoint-170m),
   [Atlas](https://huggingface.co/datasets/outpost-bio/Atlas),
   [Compass](https://huggingface.co/datasets/outpost-bio/Compass).
2. Authenticate locally:

   ```bash
   hf auth login          # or: export HF_TOKEN=hf_...
   ```

For 401/403 errors, check token validity, read scope, and approval for the specific repo.
The tokenizer loader executes repository code with `trust_remote_code=True`. Review that code
and pin an immutable Hub commit. The upstream CLI has no `--revision`; download a reviewed
snapshot and pass its local path so model, tokenizer and ordering statistics share one revision
(see `references/python-api.md`).

## The waypoint data format

Everything except `prepare-dataset` consumes **waypoint format**: a `.parquet` / `.csv` / `.tsv`
whose rows are samples, with two aligned list-columns plus any label columns you need.

| Column | Type | Notes |
| --- | --- | --- |
| `Taxa` | `list[str]` | Full lineage strings, `;`-separated: `k__Bacteria; p__Firmicutes; ...; g__Lactobacillus` |
| `Relative Abundances` | `list[float]` | Same length as `Taxa`, same order |
| *(any)* | scalar | Targets, covariates, or a `Split` column |

Use parquet to preserve list values and sample IDs. Upstream CSV/TSV loading loses the sample-ID
index and, with pandas 3, does not parse string lists. The bundled coverage reader handles the
converter's CSV/TSV, but that does not repair the upstream loader.

**Give full lineages, not bare names.** The tokenizer extracts the genus segment (`g__`) from each
lineage and falls back to the most specific higher rank when genus is missing. Bare names disable
that fallback entirely.

## Workflow

### 1. Get your data into waypoint format

If you already have a sample × taxa (or taxa × sample) abundance matrix with lineage labels:

```bash
waypoint prepare-dataset \
    --input abundance_matrix.tsv \
    --metadata sample_labels.csv \
    --output dataset.parquet
```

Orientation is auto-detected from the first column header (`taxonomy`, `lineage`, `taxon`, `otu`,
`#otu id` ⇒ taxa-as-rows); override with `--orientation`. Rows are normalised to sum to 1 unless you
pass `--no_normalize`, and zeros are dropped unless you pass `--keep_zeros`.

`prepare-dataset` cannot read profiler output directly — MetaPhlAn uses `|` separators, Kraken2
reports encode the hierarchy as indentation, and QIIME 2/SILVA prefixes the domain `d__` instead of
`k__` (which the tokenizer silently ignores). Use the bundled converter for those:

```bash
python scripts/profiler_to_waypoint.py \
    --input merged_metaphlan.tsv --format metaphlan \
    --output dataset.parquet

python scripts/profiler_to_waypoint.py \
    --input reports/*.kreport --format kraken \
    --output dataset.parquet

python scripts/profiler_to_waypoint.py \
    --input feature-table.tsv --format qiime2 --taxonomy-column taxonomy \
    --output dataset.parquet
```

See `references/data-preparation.md` for every input layout, rank handling, and the `d__`/`|` gotchas.

### 2. Check vocabulary coverage before anything else

Waypoint's vocabulary is fixed at pretraining time from Atlas. Taxa absent from it become `<unk>` and
are **silently dropped** by `waypoint embed`; the pape

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

