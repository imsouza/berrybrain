---
id: sciref-imaging-data-commons-rest-api-guide
name: "Scientific Ref: IDC REST API Guide"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (imaging-data-commons): IDC REST API Guide"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "imaging commons rest api guide"
  - "idc rest api guide"
keywords:
  - "imaging"
  - "commons"
  - "rest"
  - "api"
  - "guide"
  - "specialized"
  - "scientific"
  - "reference"
---

# IDC REST API Guide

**Verified 2026-09-30:** all 21 REST routes, OpenAPI request/response contracts, and representative validation errors. API `3.0.0b3` (build `0640860`), IDC data version v24, `idc_index_data_version` 24.2.2

IDC operates a hosted REST API that exposes discovery, cohort building, metadata SQL, and
download manifests over plain HTTP. No authentication, account, or credentials are required —
HTTP examples use `curl`; the download step separately requires `idc-index` or a transfer tool.

The API and the [MCP server](mcp_guide.md) are the same service behind two transports: the MCP
tools wrap these endpoints. Both are hosted against a current IDC release, independently of the
`idc-index` version installed locally.

## When to Use This Guide

Load this guide when you need to:
- Query IDC from a language or environment with no `idc-index` install (shell, R, Java, JS, a
  notebook without pip access)
- Build cohorts and manifests over HTTP for a pipeline or web application
- Run metadata SQL against a current IDC release without downloading local index files
- Hand a user copy-pasteable `curl` commands they can run anywhere

For downloads, pandas/notebook analysis, reading pixel data, DICOMweb, BigQuery, or digital
pathology tiling, use `idc-index` as documented in `SKILL.md`. The API never moves image bytes:
it returns public `s3://` URLs and manifests, and the transfer happens directly from cloud
storage to the client.

**Choosing among the three interfaces:**

| Situation | Use |
|-----------|-----|
| Session already has the hosted MCP server | MCP tools (`mcp_guide.md`) — same data, no HTTP plumbing |
| `idc-index` already installed, results feed pandas / downloads | `idc-index` (`SKILL.md`) |
| `idc-index` **not** installed and the task is read-only metadata | This REST API — do not install to answer a metadata question |
| No Python, or a non-Python client, or shell commands the user re-runs | This REST API |
| Installed `idc-index` is a whole IDC data release behind and cannot be upgraded here | REST API for the query, **direct bucket transfer** may be needed for the download — `idc-index` cannot fetch what its index does not list |

Being hosted, the API always serves a current IDC release — but so does an up-to-date
`idc-index`. "I want the newest data" is not on its own a reason to prefer the API: the normal
fix for a stale local index is to upgrade it. Reach for the API on version grounds only when
upgrading is not an option in that environment. Avoiding the install *is* a reason, though: the
packaged index data is ~77 MB before pandas, pyarrow, and duckdb, which a metadata question does
not need.

## Endpoint and Versioning

| Property | Value |
|----------|-------|
| Base URL | `https://api.imaging.datacommons.cancer.gov/v3` |
| Authentication | None |
| Content type | `application/json` (request and response), except `cohort/manifest.txt` → `text/plain` |
| Interactive docs | https://api.imaging.datacommons.cancer.gov/v3/docs (Swagger UI) |
| OpenAPI spec | https://api.imaging.datacommons.cancer.gov/v3/openapi.json |
| Source | https://github.com/ImagingDataCommons/IDC-REST-MCP |

**v3 is in beta.** The contract may still change before the final `3.0.0` release, so verify the
running build rather than assuming the values in this guide:

```bash
curl -s https://api.imaging.datacommons.cancer.gov/v3/version
# {"idc_version":"v24","idc_index_data_version":"24.2.2","api_version":"3.0.0b3","build":"0640860"}
```

`idc_version` is the IDC data release the API serves and is the authority when the API is in
use — prefer it over the `idc-data-version` pinned in the `SKILL.md` frontmatter, which records
the release the skill was last verified against.

### Checking the API against a local idc-index

The API and `idc-index` are built on the same `idc-index-data` package, and both report its
version, so consistency is an exact check rather than a guess:

| Side | Data release (coarse) | `idc-index-data` version (exact) |
|------|-----------------------|----------------------------------|
| API | `GET /v3/version` → `idc_version` | `GET /v3/version` → `idc_index_data_version` |
| Local | `IDCClient().get_idc_version()` | `idc_index_data.__version__` |

```python
import idc_index_data
import requests

response = requests.get("https://api.imaging.datacommons.cancer.gov/v3/version", timeout=30)
response.raise_for_status()
api = response.json()
api_version, local_version = api["idc_index_data_version"], idc_index_data.__version__

if api_version.split(".")[0] != local_version.split(".")[0]:
    print(f"Different IDC data release: API {api_version}, local {local_version} — upgrade")
elif api_version != local_version:
    print(f"Same data release, different index build: API {api_version}, local {local_version}")
    # → Same data release, different index build: API 24.2.2, local 24.2.0
```

**The major is the IDC data release; the rest is the index build.** `idc-index-data` `24.x.y`
serves IDC `v24` — 24.0.0 shipped with the v24 release, and 24.1.0 / 24.2.x are later builds of
the *same* release. What differs between them is the index itself (added tables and columns,
corrected metadata). Pin the full index build and compare requested UUIDs; matching
release labels alone do not establish that two queries or exported manifests are identical.

So read a mismatch by its position:

| Difference | Means | Consequence |
|------------|-------|-------------|
| Major (24.x.y vs 25.x.y) | Different IDC data release | Series added, revised, or removed. Counts legitimately differ, and `idc-index` **cannot download** what its index does not list |
| Minor or patch (24.2.0 vs 24.2.2) | Same data release, different index build | Same intended data release; verify selected UUIDs. Metadata corrections can change query results |

Comparing `idc_version` alone cannot make this distinction in the other direction either — the
`vNN` label is exactly the major, so matching `v24` on both sides tells you the release agrees
but says nothing about the index build.

When the two disagree, say so and name both versions, then reconcile rather than mixing
results: upgrading `idc-index` brings the local side to the newer `idc-index-data`, and
`python scripts/check_version.py` reports whether an upgrade is available and prints the
command for the interpreter you are running. Do not present API-derived and locally-derived counts side by side as if they came
from one index.

**A major behind also breaks

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

