---
id: sci-onekgpd
name: "Scientific: onekgpd"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: ">"
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "onekgpd"
keywords:
  - "onekgpd"
---

# OneKGPd: Individual-Level Queries over the 1000 Genomes Project

## Scope

This skill queries the 1000 Genomes Project dataset — the extended high-coverage cohort
of 3,202 whole-genome-sequenced individuals, on the GRCh38 assembly. All results
are drawn from this cohort, and sample names returned by the skill (for example
`HG00096` or `NA21130`) identify its participants.

Queries resolve against the cohort's per-individual genotype data. This supports
two complementary classes of question: selecting **variants** carried within a
region (across the whole cohort or within a specified set of individuals), and
selecting the **individuals** who carry variants matching given criteria.
Variant selection can be filtered by allele frequency, predicted consequence,
clinical significance, AlphaMissense classification, and the other annotation
axes listed below. Relatedness between two named individuals is also available.

The genotype state in which a variant is carried — heterozygous or homozygous —
is a criterion that queries may specify; results are returned as variants or as
sample names, not as raw genotypes.

The public service is **TLS gRPC at `db.dnaerys.org:443`**, accessed with
`dnaerys 0.2.1` (Python 3.11+); it is not a REST base URL. The maintained
service snapshot advertises VEP 115 / GENCODE 49, ClinVar 202502, and gnomAD
4.1. These are the service's annotation releases, not the latest release of
each upstream resource. Record them when interpreting results.

## When to Use

**Use this skill when you need to:**

-   Find **variants** carried in a region or set of regions matching some criteria
    across the whole cohort (`select-variants`).
-   Find **variants** carried in a region or set of regions matching some criteria
    in specific set of individuals (`select-variants-in-samples`).
-   Find **which 1000 Genomes individuals** carry variants matching some criteria
    in a region or set of regions (`select-samples`).
-   Count how many individuals carry specific variants (`count-samples`).
-   Restrict any variant query to **heterozygous-only or homozygous-only**
    carriage, or query both together (default).
-   Identify which individuals are **homozygous reference** at a single position
    (`select-samples-hom-ref`).
-   Determine the **relatedness** between two named 1000 Genomes individuals —
    both the degree (twin / 1st / 2nd / 3rd / unrelated) and the KING kinship
    coefficient (`kinship`).
-   Get **dataset totals** — sample count, sex split, variant count, assembly
    (`dataset-info`).
-   Variant selection can be specified by KGP allele frequency, gnomAD 4.1 exome and
    gnomAD 4.1 genome allele frequency, AlphaMissense Score and AlphaMissense Class,
    ClinVar significance (202502), and VEP annotations (impact, biotype, feature type,
    variant class, consequences).

**Do NOT use this skill for:**

-   Resolving a gene symbol, rsID, or transcript to coordinates, or fetching
    reference sequence. Resolve coordinates first (see Coordinate Provenance
    below), then query this skill with the resolved GRCh38 region.
-   Any cohort other than the 1000 Genomes Project — this skill serves only that
    dataset.

## Prerequisites

1.  **`uv`**: This skill's script is run with `uv run`, which reads the script's
    inline dependency metadata and provisions an ephemeral environment. Ensure
    `uv` is installed and on PATH (https://docs.astral.sh/uv/).
2.  **Data use terms**: The 1000 Genomes Project data is open; users should be
    aware of the 1000 Genomes Project / IGSR data-use terms
    (https://www.internationalgenome.org/data).
3.  **Access constraints**: There is no API key, no `.env` file, and no
    rate-limit token to configure.
4.  **Timeouts**: network commands use `--timeout 30` seconds per RPC by default.
    A positive finite override is allowed. Pagination makes several RPCs and
    retryable failures retry the whole fetch up to three times, so this is not
    a deadline for the whole command.

## Core Rules

-   **Use the Wrappers**: ALWAYS execute the provided helper scripts rather than
    constructing your own client calls or network requests. Use
    `scripts/onekgpd_api.py` for variant/sample/kinship queries (it handles the
    connection, streaming, pagination, and JSON serialization), and
    `scripts/onekgpd_meta.py` for sample/population metadata (offline, see
    [Sample & population metadata](#sample--population-metadata-offline)).
-   **Coordinates MUST be resolved against an authoritative source first** — see
    [Coordinate Provenance](#coordinate-provenance-mandatory-first-step). This
    is mandatory, not advisory.
-   **Count before you select**: every variant and sample selection has a paired
    counting command. Call the count command FIRST to size the result set, then
    select only if the count is manageable.
-   **Zygosity defaults to both**: selection and counting commands include both
    heterozygous and homozygous carriage by default. Narrow with `--het-only`
    or `--hom-only` when the question is specifically about one state. (You do
    not need to pass anything to get both.)
-   **Output**: scripts write full JSON to a file (`--output`, default under
    `/tmp/`) and print a concise summary to stdout. Do not read large JSON files
    into context — use `jq` or a small disposable `uv run python` snippet to
    extract fields. `--page-size` retrieves every page but accumulates all
    variants in RAM; it is not a bounded-memory export. Size the query first.
-   **Check completeness**: `result_incomplete=true` means results cannot support
    a definitive zero/absence claim. Re-run after service recovery. For capped
    variant selections, `truncated=true` means the limit was reached and more
    records may exist, even if the cluster result itself was complete.

## Coordinate Provenance (MANDATORY FIRST STEP)

Before any region-based query, resolve the gene or feature to **GRCh38**
coordinates against an authoritative source (for example Ensembl or NCBI), and query
with those resolved coordinates. Inputs are **1-based, inclusive**: a BED interval
`[start0, end0)` becomes `start=start0+1, end=end0`. Record the source accession,
annotation release, and retrieval date; gene boundaries can differ by annotation
release even on the same assembly. The assembly must be explicit, and a gene-range
must be resolved to precise positions before use. This is structural, not
advisory: there is no source-side guardrail 

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

