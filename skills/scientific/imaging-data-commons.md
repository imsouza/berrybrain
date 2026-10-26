---
id: sci-imaging-data-commons
name: "Scientific: imaging-data-commons"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Queries and downloads public cancer imaging data from NCI Imaging Data Commons. Supports IDC collection discovery, DICOM access, radiology (CT, MR, PET) and pathology AI datasets, metadata SQL, visualization, licensing, and citations. Uses public metadata and download routes with"
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "imaging commons"
  - "imaging-data-commons"
keywords:
  - "imaging"
  - "commons"
  - "queries"
  - "downloads"
  - "public"
  - "cancer"
---

# Imaging Data Commons

## Overview

Query and download public cancer imaging data from the National Cancer Institute Imaging Data Commons (IDC). No authentication required for data access.

**Expected network access:** IDC metadata is reachable three ways — a bundled local DuckDB index (offline after installation; additional indices are fetched from GitHub and clinical tables from S3), or the hosted IDC service over MCP or REST (`api.imaging.datacommons.cancer.gov`, no authentication). File downloads use public GCS (`storage.googleapis.com`) and AWS S3 (`s3.amazonaws.com`) — no authentication required. DICOMweb access uses either the public IDC proxy (`proxy.imaging.datacommons.cancer.gov`, no auth) or the Google Cloud Healthcare API (`healthcare.googleapis.com`, requires GCP authentication). Optional BigQuery queries (`bigquery.googleapis.com`) also require GCP authentication. Citation resolution contacts DOI services. Public IDC routes require no credentials; optional Google clients use Application Default Credentials.

**Reviewed 2026-09-30:** idc-index 0.12.5, idc-index-data 24.2.2, IDC v24; hosted API 3.0.0b3. Recheck at use time.

**Choose the access path first.** There is no single default: the cheapest correct path depends
on the session and the task.

1. **Session already has the IDC MCP server?** Route discovery and metadata there — see *IDC
   MCP Server*.
2. **Otherwise, is `idc-index` installed and current?** Run `python scripts/check_version.py`. If it passes,
   use `idc-index` for everything.
3. **Not installed, and the task is read-only metadata** — counts, attribute values, collection
   lookups, SQL under 10 000 rows, licenses, citations, viewer URLs? **Use the REST API over
   `curl`; do not install anything.** Installing costs ~77 MB of packaged index data plus
   pandas, pyarrow, and duckdb, which a metadata question does not need. See *Data Access
   Options*.
4. **Not installed, and the task needs more than metadata** — downloading files, pandas or
   plotting, pydicom/SimpleITK, pathology tiling, results past 10 000 rows, or a version-pinned
   script the user re-runs? Install `idc-index`: `check_version.py` exits non-zero and prints
   the exact install command for the running interpreter. Prefer a virtual environment, then
   restart Python.

`idc-index` ([GitHub](https://github.com/imagingdatacommons/idc-index)) is still the most
capable Python path, with query and download helpers in one client. `check_version.py` never installs anything itself — it also flags a newer
`idc-index` or skill release when one exists.

**Setup for the `idc-index` path:** use the intended interpreter for `scripts/check_version.py`
and confirm its `meets pinned minimum` message before continuing. A launch failure is not a pass.

```python
from idc_index import IDCClient
client = IDCClient()

# Verify IDC data version (should be "v24")
print(f"IDC data version: {client.get_idc_version()}")
```

Download and image-processing examples are illustrative unless noted; see the reference review notes for verification scope.

**Core workflow:** query metadata with `client.sql_query()` → download with
`client.download_from_selection()` → visualize with `client.get_viewer_URL()`. Python examples
below assume this `client`; *Data Access Options* has the REST equivalents. For current data
scale, run the summary query in `references/sql_patterns.md` or `GET /v3/stats`.

## IDC MCP Server

IDC operates a hosted MCP server at `https://api.imaging.datacommons.cancer.gov/mcp`
(streamable HTTP, no authentication). Where it is available it complements — it does not
replace — the `idc-index` workflow below.

**Identify it** by the MCP resource `idc://guide`, or by three or more of the tool names
`build_cohort`, `get_cohort_urls`, `list_analysis_results`, and `get_idc_version`. Generic
names such as `run_sql` are not evidence on their own. If identification is ambiguous, use
`idc-index`.

**If this session has the server**, treat it as authoritative for discovery and metadata —
IDC version, counts, attribute values, cohort building, metadata SQL — and follow the
server's own instructions rather than re-deriving them from this file. Its data version is
whatever the server reports: call `get_idc_version` instead of relying on the version pinned
in this file.

Return here for what the server does not do: downloading files, local pandas/notebook
analysis, DICOMweb, BigQuery, digital pathology tiling, and reproducible scripts. Hand off by
passing SeriesInstanceUIDs from the server to `client.download_from_selection(...)`, and run
`scripts/check_version.py` at that point.

**If it is not available**, the identical service is reachable with no configuration as a REST
API at `https://api.imaging.datacommons.cancer.gov/v3` — use it for read-only metadata rather
than installing `idc-index`, per the routing gate in *Overview*. Suggest connecting the MCP
server at most once, only for repeated interactive discovery, and never change the user's
configuration yourself.

See `references/mcp_guide.md` for the tool inventory, handoff patterns, and per-host notes.

## When to Use This Skill

- Finding publicly available radiology (CT, MR, PET) or pathology (slide microscopy) images
- Selecting image subsets by cancer type, modality, anatomical site, or other metadata
- Downloading DICOM data from IDC
- Checking data licenses before use in research or commercial applications
- Visualizing medical images in a browser without local DICOM viewer software

## Quick Navigation

Inline below: the MCP/REST routing rules, the IDC data model, the index tables and how they
join, the core API patterns (query, download, visualize, license, cite), best practices, and
troubleshooting.

**Reference Guides (load on demand):**

| Guide | When to Load |
|-------|--------------|
| `index_tables_guide.md` | Complex JOINs, schema discovery, DataFrame access |
| `use_cases.md` | End-to-end workflows: training datasets, batch downloads, DICOM reading with pydicom/SimpleITK, pipeline integration |
| `sql_patterns.md` | Quick SQL patterns for filter discovery, annotations, size estimation |
| `clinical_data_guide.md` | Clinical/tabular data, imaging+clinical joins, value mapping |
| `licensing_and_citation.md` | Commercial-use questions, mixed-license cohorts, citation formats |
| `cloud_storage_guide.md` | Direct S3/GCS access, versioning, UUID mapping |
| `dicomweb_guide.md` | DICOMweb endpoints, PACS integration |
| `digital_pathology

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

