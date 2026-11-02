---
id: sciref-waypoint-bio-data-preparation
name: "Scientific Ref: Preparing data for Waypoint"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (waypoint-bio): Preparing data for Waypoint"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "waypoint bio preparation"
  - "preparing data for waypoint"
keywords:
  - "waypoint"
  - "bio"
  - "preparation"
  - "specialized"
  - "scientific"
  - "reference"
  - "preparing"
---

# Preparing data for Waypoint

## Waypoint format

Rows are samples. Two aligned list-columns, plus whatever labels you need.

| Column | Type | Required |
| --- | --- | --- |
| `Taxa` | `list[str]` — full lineage strings | yes |
| `Relative Abundances` | `list[float]` — same length and order as `Taxa` | yes |
| `Split` | `str` — `train` / `validation` / `test` | only when using `split_column` |
| *(any)* | scalar targets and covariates | as needed |

The parquet DataFrame index holds the sample ID and is preserved through `embed`.
The upstream CSV/TSV reader does not restore that index.

Use `.parquet`. Upstream CSV/TSV list parsing checks `dtype == object`, so pandas 3
string columns remain strings and produce degenerate or omitted samples. The bundled coverage
reader parses them correctly; convert to parquet before passing data to the upstream CLI.

```python
import pandas as pd

df = pd.DataFrame(
    {
        "Taxa": [["k__Bacteria; p__Firmicutes; c__Bacilli; o__Lactobacillales; f__Lactobacillaceae; g__Lactobacillus",
                  "k__Bacteria; p__Bacteroidota; c__Bacteroidia; o__Bacteroidales; f__Bacteroidaceae; g__Bacteroides"]],
        "Relative Abundances": [[0.41, 0.59]],
        "Group": ["Case"],
    },
    index=pd.Index(["sample_001"], name="sample_id"),
)
df.to_parquet("dataset.parquet")
```

## How taxonomy strings are read

`TaxonomicTokenizer` splits each lineage on `;`, strips whitespace, and inspects each segment's
three-character prefix:

| Prefix | Rank |
| --- | --- |
| `s__` | species |
| `g__` | genus |
| `f__` | family |
| `o__` | order |
| `c__` | class |
| `p__` | phylum |
| `k__` | kingdom |

With `taxon_rank: genus` and `fallback_to_higher_rank: true` (the published defaults), each lineage
becomes one token:

1. If a `g__` segment exists, that segment *including the prefix* is the token — `g__Lactobacillus`.
2. Otherwise the **most specific higher rank** present is used — a lineage stopping at
   `f__Lactobacillaceae` tokenises to `f__Lactobacillaceae`.
3. If nothing matches, the token is `<unk>`.

Consequences that bite:

- **Any prefix outside that table is invisible.** QIIME 2 / SILVA / Greengenes2 write the domain as
  `d__Bacteria`; `d__` is not in the table, so such a segment is skipped entirely. A lineage
  truncated at domain becomes `<unk>`. Rewrite `d__` to `k__`.
- **A `s__` species segment does not help by itself.** Species is *more* specific than genus, so
  fallback (which only goes up) cannot use it. A lineage with `s__` but no `g__` tokenises to
  whatever higher rank is present — or `<unk>` if none is. Keep the full lineage, not just the tip.
- **Separator is `;`, not `|`.** A `|`-joined MetaPhlAn lineage is one unsplittable segment. Its
  first three characters are `k__`, so it matches at kingdom rank and the *entire pipe-joined
  string* is returned as a single token — which is not in the vocabulary, so it becomes `<unk>`.
  Verified natively against `TaxonomicTokenizer` 1.0.2 with Transformers 4.57.6:
  `k__Bacteria|p__Firmicutes|g__Lactobacillus` extracts to itself, while the `;`-separated form
  extracts to `g__Lactobacillus`.
- **Bare names never tokenise.** `Lactobacillus` has no prefix. Use `prepare-dataset
  --taxonomy_format genus` to prefix them, accepting the loss of fallback.

## Token ordering and truncation

Samples are encoded as `[BOS] + ordered_token_ids + [EOS]`, padded to `max_length` (512).

Ordering is by **descending abundance z-score** — `(ra - mean) / std` per token, using
`token_std_means.parquet` from the checkpoint. This puts taxa that are unusually abundant *for that
taxon* first, rather than merely abundant. Without that file, ordering falls back to raw descending
abundance.

Truncation keeps at most `max_length - 2` in-vocabulary entries. Discarded entries have lower
ordering scores; this is not evidence they are biologically uninformative. Upstream does not
aggregate repeated genus tokens from different species/lineages. Count encoded entries (including
duplicates) when reporting truncation, and keep rank/aggregation conventions fixed.

`compute_token_std_means` computes moments over observed entries, not across all samples with
absent taxa filled as zeros. Duplicate mapped tokens each contribute an observation. For a new
model, estimate preprocessing statistics on training data only; the upstream `pretrain` command
computes vocabulary/statistics before its random validation split, so that validation loss is not
an independent assessment of preprocessing generalization.

## Out-of-vocabulary taxa

The vocabulary is frozen at pretraining time from the Atlas corpus. During `waypoint embed`, tokens
resolving to `<unk>` are dropped before ordering; during fine-tuning and benchmarking,
`filter_unk_taxa: true` does the same. Neither warns you.

Every Compass dataset carries out-of-vocabulary taxa, and the paper names this the models' key
limitation. Measure it before drawing conclusions:

```bash
python scripts/vocab_coverage.py --model outpost-bio/Waypoint-6m --data dataset.parquet
```

If coverage is poor, the usual causes are, in order: a different taxonomy database (SILVA vs. NCBI
vs. GTDB naming), the `d__` prefix problem, `|` separators, and genuinely novel environments.

## Converting profiler output

`waypoint prepare-dataset` reads a plain abundance matrix whose labels are already `;`-separated
lineages. `scripts/profiler_to_waypoint.py` handles the formats it cannot.

### MetaPhlAn

Merged tables from `merge_metaphlan_tables.py`: rows are clades with `|`-separated lineages, columns
are samples, values are **percentages**, and the table is cumulative — every rank appears as its own
row.

```bash
python scripts/profiler_to_waypoint.py \
    --input merged_abundance_table.txt --format metaphlan \
    --rank species --output dataset.parquet
```

The converter drops `#` comment lines and the `NCBI_tax_id` / `clade_taxid` column, keeps only rows
whose deepest rank equals `--rank` (default `species`, which avoids double-counting parents),
rewrites `|` to `; `, and renormalises each sample to sum to 1. Strain/SGB rows ending below species (`t__`) are excluded before normalization, preventing
double-counting their species parents. A profile containing only SGB rows is unsupported by this
rank-selection mode; aggregate with the profiler's documented taxonomy mapping first.

### Kraken2 / Bracken

Kraken2 reports are per-sample and encode the hierarchy as two-space indentation, with no lineage
string

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

