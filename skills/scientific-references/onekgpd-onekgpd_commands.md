---
id: sciref-onekgpd-onekgpd-commands
name: "Scientific Ref: OneKGPd command reference"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (onekgpd): OneKGPd command reference"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "onekgpd onekgpd commands"
  - "onekgpd command reference"
keywords:
  - "onekgpd"
  - "commands"
  - "specialized"
  - "scientific"
  - "reference"
  - "command"
---

# OneKGPd command reference

Full argument tables for every `onekgpd_api.py` subcommand and the schema of a
returned variant. Run with `uv run scripts/onekgpd_api.py <command> [flags]`.

Coordinates are **GRCh38, 1-based inclusive**. Resolve a gene/feature to
coordinates against an authoritative source before querying. Every command
writes full JSON to a file (`--output PATH`, default a temp file) and prints a
short summary to stdout.

## Shared flags

### Connection / output (all commands)

| flag | type | required | default | description |
| --- | --- | --- | --- | --- |
| `--timeout` | float | no | 30 | Positive finite seconds per RPC. Whole-fetch retries and pagination can exceed this overall. |
| `--output` | path | no | temp file | Write full JSON here; otherwise a `onekgpd_<cmd>_*.json` temp file is created and its path printed. |

There is no endpoint, credential, or assembly override: the skill targets
the public 1000 Genomes instance on GRCh38 only.

### Region input (count/select variants and samples)

Provide **either** a single region **or** one-or-more `--region`, not both.

| flag | type | required | default | description |
| --- | --- | --- | --- | --- |
| `--chrom` | str | single-region mode | – | Chromosome: `chr17`, `17`, `X`, `MT` (case-insensitive). |
| `--start` | int | with `--chrom` | – | 1-based inclusive start. |
| `--end` | int | with `--chrom` | – | 1-based inclusive end (≥ start). |
| `--ref` | str | no | – | Narrow to one reference allele (single-region only). |
| `--alt` | str | no | – | Narrow to one alternate allele (single-region only). |
| `--region` | `CHR:START-END` | multi-region mode | – | A region; repeat the flag for multiple regions. |
| `--min-len-bp` | int | no | – | Minimum alternate-allele length (bp). |
| `--max-len-bp` | int | no | – | Maximum alternate-allele length (bp). |

### Zygosity (count/select variants and samples)

| flag | type | required | default | description |
| --- | --- | --- | --- | --- |
| `--het-only` | switch | no | both | Include HETEROZYGOUS variants ONLY (0/1 genotypes). |
| `--hom-only` | switch | no | both | Include HOMOZYGOUS variants ONLY (1/1 genotypes). |

With no zygosity flag, both HETEROZYGOUS (0/1) and HOMOZYGOUS (1/1) carriage are
queried — use the default when you need homozygous OR heterozygous variants, or
when uncertain. `--het-only` and `--hom-only` are mutually exclusive.

### Annotation filters (count/select variants and samples)

See `annotation_vocabularies.md` for the valid CSV terms. Different filter fields
combine with **AND**; multiple CSV values within one field combine with **OR**.

| flag | type | maps to |
| --- | --- | --- |
| `--af-lt` / `--af-gt` | float | 1000 Genomes dataset AF bounds |
| `--gnomad-exomes-af-lt` / `--gnomad-exomes-af-gt` | float | gnomAD v4.1 exomes AF bounds |
| `--gnomad-genomes-af-lt` / `--gnomad-genomes-af-gt` | float | gnomAD v4.1 genomes AF bounds |
| `--clin-significance` | CSV | ClinVar significance terms |
| `--consequence` | CSV | SO consequence terms |
| `--impact` | CSV | VEP impact (HIGH,MODERATE,LOW,MODIFIER) |
| `--variant-type` | CSV | SO variant class terms |
| `--feature-type` | CSV | VEP feature types |
| `--bio-type` | CSV | VEP biotypes |
| `--alpha-missense-class` | CSV | AM_LIKELY_BENIGN,AM_LIKELY_PATHOGENIC,AM_AMBIGUOUS |
| `--alpha-missense-score-lt` / `--alpha-missense-score-gt` | float | AlphaMissense score bounds |
| `--biallelic-only` / `--multiallelic-only` | switch | site multiplicity (mutually exclusive) |
| `--exclude-males` / `--exclude-females` | switch | sex exclusion (mutually exclusive) |

Mutual exclusions enforced: `--biallelic-only`/`--multiallelic-only`,
`--exclude-males`/`--exclude-females`, and `--alpha-missense-class` vs the
AlphaMissense score bounds. Every numeric AF/AlphaMissense bound must be finite,
in `(0, 1]`, and remain nonzero when encoded as float32. **Zero means unset in
the protobuf API**; the wrapper rejects it rather than silently dropping the
filter. Setting a positive `*-gt` ≥ its matching `*-lt` defines an empty range.

The gnomAD `< X` bounds include unannotated variants, represented by AF = 0.
Choose a scientifically meaningful positive lower bound to exclude those zeros;
this also excludes annotated values at or below that bound. For exact annotation
presence, retrieve complete variants and post-filter the relevant AF > 0 locally.
Do not substitute an arbitrary epsilon without documenting its effect.

---

## Commands

### `dataset-info`

No flags beyond `--output` / `--timeout`. Returns dataset totals (sample count, sex split,
variant total, assembly) and the cohort breakdown. Doubles as a connectivity
check.

JSON: `{command, samples_total, females_total, males_total, variants_total,
assembly, cohorts:[{cohort_name, samples_count, female_count, male_count,
synthetic}]}`.

### `count-variants`

Region + zygosity + annotation flags. Counts variants in the region(s),
cohort-wide. JSON: `{command, count, request, result_incomplete}`.

### `select-variants`

SELECT variants which exist in ANY genomic region provided.

Region + zygosity + annotation flags, plus pagination:

| flag | type | required | default | description |
| --- | --- | --- | --- | --- |
| `--limit` | int | no | 200 | Hard cap on returned variants (mutually exclusive with `--page-size`). |
| `--page-size` | int | no | – | Retrieve ALL matching variants in pages of this size (full walk). |

JSON: `{command, count_returned, truncated, request, result_incomplete,
variants:[…]}`. `truncated` is true when the count hit `--limit` (more may
exist; raise `--limit` or use `--page-size`). Empty `variants` array if no
matches. Paging accumulates the complete result in memory. Check
`result_incomplete` separately from `truncated`; a count taken before selection
is not a transactional snapshot.

### `count-variants-in-samples`

As `count-variants`, plus `--samples CSV` (required) — counts variants carried
by the named individuals. Blank/empty CSV is rejected before connecting, because
the SDK otherwise routes an empty sample list to the cohort-wide endpoint.

### `select-variants-in-samples`

As `select-variants`, plus `--samples CSV` (required) — selects variants carried
by the named individuals.

### `count-samples`

Region + zygosity + annotation flags. Counts how many individuals carry a
matching variant. JSON: `{command, count, request, result_incomplete}`.

### `select-samples`

Region + zygosity + annotation flags, plus pagination:

| f

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

