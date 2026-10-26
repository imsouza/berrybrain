---
id: sciref-imaging-data-commons-mcp-guide
name: "Scientific Ref: IDC MCP Server Guide"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (imaging-data-commons): IDC MCP Server Guide"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "imaging commons mcp guide"
  - "idc mcp server guide"
keywords:
  - "imaging"
  - "commons"
  - "mcp"
  - "guide"
  - "specialized"
  - "scientific"
  - "reference"
  - "server"
---

# IDC MCP Server Guide

IDC operates a hosted [Model Context Protocol](https://modelcontextprotocol.io/) server that
exposes IDC discovery and metadata as agent tools. This guide covers how to recognize it, how
to divide work between it and `idc-index`, and what to hand off across that boundary.

The server is optional. Everything in `SKILL.md` works without it.

## Endpoint

| Property | Value |
|----------|-------|
| URL | `https://api.imaging.datacommons.cancer.gov/mcp` |
| Transport | Streamable HTTP (`streamable-http`, sometimes spelled `http`) |
| Authentication | None |
| Server identity | `IDC (Imaging Data Commons)` |

## Identifying the server

Tool names and resource URIs are defined by the server, so they are the same on every host.
Use them, not host-specific naming conventions, to decide whether the server is present.

**Strongest signal — resource URIs.** The server publishes two resources under an `idc://`
scheme:

| URI | Content |
|-----|---------|
| `idc://guide` | Data model and recommended workflow (Markdown) |
| `idc://tables` | Tables available to `run_sql`, with descriptions and column counts (JSON) |

If the host can enumerate MCP resources, a resource with URI `idc://guide` identifies the
server unambiguously.

**Fallback — tool-name fingerprint.** Require three or more of `build_cohort`,
`get_cohort_urls`, `list_analysis_results`, and `get_idc_version`. Do not treat `run_sql`,
`get_stats`, `list_tables`, or `get_citations` as evidence on their own; those names are
generic enough that another server could expose them.

**This is disambiguation, not authentication.** No runtime check can prove the server on the
other end is operated by NCI — a hostile server could serve `idc://guide` and name its tools
anything. The trust anchor is the URL the user configured plus TLS, which is established when
the server is added, not when the skill runs. That is sufficient for routing: the check only
has to distinguish IDC from the user's other installed servers.

**Fail soft.** If identification is ambiguous, or a tool call fails, fall back rather than
reporting an error — to the REST API (`rest_api_guide.md`) for read-only metadata, which is the
same service with no configuration, or to `idc-index` when it is already installed or the task
needs downloads or local analysis. Tool names may change as the server matures.

## Tool inventory

Live `initialize`, `tools/list`, and `resources/list` verified on 2026-09-30 against server `3.0.0b3`. Treat this as a snapshot, not a contract — call
the server's own listing rather than assuming this list is current.

| Group | Tools |
|-------|-------|
| Version and scale | `get_idc_version`, `get_stats` |
| Collections | `list_collections`, `get_collection`, `list_analysis_results` |
| Attribute grounding | `list_attributes`, `get_attribute_values` |
| Cohorts | `build_cohort`, `get_cohort_urls` |
| SQL | `list_tables`, `get_table_schema`, `run_sql` |
| Clinical data | `list_clinical_tables`, `get_clinical_table_schema`, `get_clinical_table` |
| Attribution | `get_citations`, `get_licenses` |
| Visualization | `get_viewer_url` |

The server ships its own usage instructions, which most hosts inject automatically. Follow
those instructions for tool sequencing (ground with `list_attributes` /
`get_attribute_values` before filtering; check `list_tables` before writing SQL). Do not
re-derive that workflow from `SKILL.md` — the two would drift apart on the server's next
release.

**Cohort results report their own filters.** `build_cohort` and `get_cohort_urls` require at
least one filter predicate and fail cleanly without one, rather than returning the whole archive;
results echo the filters actually applied along with warnings (inside `counts` for `build_cohort`) for any predicate that was dropped
or any value whose casing did not match. Read those warnings before reporting a count — a zero
with no warning means the filter matched nothing, which is a real answer. Same contract as the
REST endpoints they wrap; see `rest_api_guide.md`.

## Division of labor

The server and `idc-index` overlap on metadata queries and diverge everywhere else.

| Task | Use |
|------|-----|
| IDC data version, collection and series counts | Server (`get_idc_version`, `get_stats`) |
| Valid filter values before building a query | Server (`get_attribute_values`) |
| Cohort selection by attribute filters | Server (`build_cohort`) |
| One-off metadata SQL, answer consumed as prose | Server (`run_sql`) |
| Metadata SQL whose result feeds local Python | `idc-index` (`client.sql_query`) |
| Downloading DICOM files | `idc-index` (`client.download_from_selection`) |
| pandas / notebook analysis, plotting | `idc-index` |
| Reading pixel data (pydicom, SimpleITK) | `idc-index` + local files |
| DICOMweb, BigQuery, direct S3/GCS, Parquet | `idc-index` and the relevant reference guide |
| Digital pathology tiling and annotation workflows | `idc-index` + `digital_pathology_guide.md` |
| Reproducible scripts a user will re-run | `idc-index` (a script outlives the session) |

Two rules resolve the overlap:

- **Prefer the server for discovery.** It is hosted against a current IDC release, so it does
  not depend on the `idc-index` version pinned in `SKILL.md`.
- **Prefer `idc-index` when the result must become a Python object.** Round-tripping a
  DataFrame through tool output wastes context and loses types.

## Handing off from the server to `idc-index`

The boundary artifact is a list of `SeriesInstanceUID` values.

```python
# UIDs obtained from the MCP server's build_cohort / run_sql output
series_uids = [
    "1.3.6.1.4.1.14519.5.2.1.7009.2403.334240657131972136850343327463",
    # ...
]

from idc_index import IDCClient
client = IDCClient()

# Confirm size before downloading — the server reports size_TB, but re-check locally
selected = client.index[client.index["SeriesInstanceUID"].isin(series_uids)]
missing = set(series_uids) - set(selected["SeriesInstanceUID"])
if missing:
    raise ValueError(f"{len(missing)} requested series absent from local index; reconcile versions")
print({"series": len(selected), "size_GB": selected["series_size_MB"].sum() / 1000})

client.download_from_selection(
    downloadDir="./data",
    seriesInstanceUID=series_uids,       # a list, not a DataFrame
    dirTemplate="%collection_id/%PatientID/%Modality",
)
```

Run `python scripts/check_version.py` before the first `idc-index` call in a session, even if
discovery happened server-side — 

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

