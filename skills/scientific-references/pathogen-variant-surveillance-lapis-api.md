---
id: sciref-pathogen-variant-surveillance-lapis-api
name: "Scientific Ref: LAPIS API reference"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (pathogen-variant-surveillance): LAPIS API reference"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "pathogen variant surveillance lapis api"
  - "lapis api reference"
keywords:
  - "pathogen"
  - "variant"
  - "surveillance"
  - "lapis"
  - "api"
  - "specialized"
  - "scientific"
  - "reference"
---

# LAPIS API reference

Reviewed 2026-10-01 against live `/api-docs`, `/sample/databaseConfig` and `/sample/info`.
SARS-CoV-2 used LAPIS 0.8.7/SILO 0.14.3. The other 14 registry entries used LAPIS 0.8.0/SILO
0.11.0. Upstream had released 0.8.8 on 2026-09-16; hosted deployments lag it.
This is a per-deployment contract; a current documentation page can describe features
an older server does not support.

## Deployment discovery and access

| Registry names | Base URL |
| --- | --- |
| `sars-cov-2` | `https://lapis.cov-spectrum.org/open/v2` |
| `influenza-a`, `h1n1pdm`, `h3n2`, `h5n1` | `https://lapis.genspectrum.org/<name>` |
| `rsv-a`, `rsv-b`, `hmpv`, `measles`, `mpox`, `west-nile`, `dengue`, `ebola-zaire`, `ebola-sudan`, `cchf` | `https://lapis.pathoplexus.org/<name>` |

All 15 schema/info endpoints answered without authentication in this review. Pathoplexus and
GenSpectrum use Loculus records; applicable terms, versions and revocations matter. The helpers
select latest, nonrevoked and OPEN records when those schema fields exist. Inspect and report
these filters; do not assume every publicly queryable record permits unrestricted reuse.

Other deployments can require OAuth bearer tokens or separate access controls. These CLIs do
not implement authenticated access. Do not put credentials in `--base-url`. GISAID-derived access
is outside the verified open workflow; do not infer its access method from these deployments.
Open GenBank/INSDC and GISAID datasets have different coverage and submission processes, so neither
strict set inclusion nor comparable proportions should be assumed.

Official sources: [authentication](https://lapis.cov-spectrum.org/open/v2/docs/concepts/authentication),
[Pathoplexus API usage](https://pathoplexus.org/docs/how-to/search-download-seqs-api),
[Pathoplexus terms](https://pathoplexus.org/about/terms-of-use).

## Endpoint methods and response shapes

Use `<base>/api-docs` for the deployment's generated OpenAPI. The introductory documentation's
statement that every endpoint supports GET and POST is too broad; inspected schemas distinguish:

| Path | Methods | Response/purpose |
| --- | --- | --- |
| `/sample/aggregated` | GET, POST | `data` rows with `count`, grouped by `fields`; `info` envelope |
| `/sample/details` | GET, POST | metadata rows; `fields` is a projection |
| `/sample/aminoAcidMutations`, `/sample/nucleotideMutations` | GET, POST | site-wise mutation count, coverage, proportion |
| `/sample/aminoAcidInsertions`, `/sample/nucleotideInsertions` | GET, POST | insertion counts; separate from mutations |
| `/sample/databaseConfig` | GET | raw schema object, including `schema.metadata` |
| `/sample/referenceGenome` | GET | `nucleotideSequences` and `genes`, each with `name` and reference sequence |
| `/sample/lineageDefinition/{column}` | GET | raw lineage dictionary for an indexed column |
| `/sample/info` | GET | raw `dataVersion`, `lapisVersion`, `siloVersion`, request provenance |
| `/sample/unalignedNucleotideSequences`, `/sample/alignedNucleotideSequences` | GET, POST | nucleotide sequences; FASTA or specified supported format |
| `/sample/unalignedNucleotideSequences/{segment}`, `/sample/alignedNucleotideSequences/{segment}` | GET, POST | per-segment forms on segmented instances |
| `/sample/alignedAminoAcidSequences`, `/sample/alignedAminoAcidSequences/{gene}` | GET, POST | all or selected translated sequences |
| `/sample/mostRecentCommonAncestor`, `/sample/phyloSubtree` | GET, POST | tree queries requiring a supported `phyloTreeField` |
| `/component/queriesOverTime` | POST | JSON `filters`, `dateField`, `dateRanges`, `queries` |
| `/component/aminoAcidMutationsOverTime`, `/component/nucleotideMutationsOverTime` | POST | JSON `filters`, `dateField`, `dateRanges`, `includeMutations` |

Component `dateRanges` entries use `dateFrom`/`dateTo`; `dateField` chooses the actual schema
column. `queries` entries specify `countQuery`, optional `coverageQuery` and `displayLabel`.
These component/tree/download routes were schema-reviewed, not exercised with large datasets.
Tree results ignore records absent from the tree; MRCA reports `missingNodeCount` and supports
`printNodesNotInTree`. Inspect the response schema rather than assume every filtered record has
an evolutionary placement.

GET uses URL parameters. POST query routes accept JSON with `Content-Type: application/json`;
arrays are JSON arrays. Form-encoded POST uses repeated keys. For GET, comma-delimited lists are
documented and repeated keys also work for metadata list filters. Unknown keys fail rather than
being silently ignored. The bundled CLIs issue GET requests only.

Sources: [SARS-CoV-2 OpenAPI](https://lapis.cov-spectrum.org/open/v2/api-docs),
[H5N1 OpenAPI](https://lapis.genspectrum.org/h5n1/api-docs),
[RSV-A OpenAPI](https://lapis.pathoplexus.org/rsv-a/api-docs),
[request methods](https://lapis.cov-spectrum.org/open/v2/docs/concepts/request-methods).

## Read the schema before filtering

`schema.metadata[]` declares `name`, `type` and optional `generateLineageIndex`. Since LAPIS 0.6,
that index value can be a string naming the index. Test for an enabled value, not identity with
boolean `true`. Indexed taxonomic fields such as `hostTaxonId` are not necessarily lineage calls.

`date`, `int`, and `float` fields support inclusive `<field>From`/`<field>To`; the date-analysis
scripts require `date`, not merely any range-capable field. A string holding a date is still a
string. In the reviewed schemas:

| Deployment | Collection | Submission/release | Geography |
| --- | --- | --- | --- |
| SARS-CoV-2 | `date` | `dateSubmitted` | `country` |
| GenSpectrum influenza | `sampleCollectionDateRangeLower` / `RangeUpper` | `ncbiReleaseDate` | `country` |
| Pathoplexus | `sampleCollectionDateRangeLower` / `RangeUpper` | `earliestReleaseDate` or `ncbiReleaseDate` | `geoLocCountry` |

`sampleCollectionDate` in the latter deployments is a string that can encode partial dates.
Choosing the lower range endpoint as though it were an exact date would put a month/year-only
sample into one arbitrary week. The bundled date analyses retain only equal lower/upper bounds.
A submission/release field is a provenance choice: NCBI release and first Pathoplexus release are
different events; neither guarantees the date the record first became queryable in this LAPIS.

Null filtering uses `<field>.isNull=true` or `false`; empty strings no longer mean null. The
scripts' `--where` is a narrow metadata filter inte

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

