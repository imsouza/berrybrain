---
id: sciref-imaging-data-commons-licensing-and-citation
name: "Scientific Ref: Licensing and Citation Guide for IDC"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (imaging-data-commons): Licensing and Citation Guide for IDC"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "imaging commons licensing citation"
  - "imaging commons licensing citacao"
  - "licensing and citation guide for idc"
keywords:
  - "imaging"
  - "commons"
  - "licensing"
  - "citation"
  - "citacao"
  - "specialized"
  - "scientific"
  - "reference"
---

# Licensing and Citation Guide for IDC

## When to Use This Guide

Load this guide when:
- A user asks whether IDC data can be used commercially, redistributed, or included in a product
- You are assembling a cohort that mixes collections and need to know which terms govern it
- A user is publishing results and needs formatted citations (APA, BibTeX, CSL JSON, RDF Turtle)
- You need the parameters or output formats for citation generation

The obligation summary — check the license, generate citations — lives in `SKILL.md`. This
guide holds the detail behind it.

**These are the two IDC tasks least tied to any one access path.** Licenses and citations are
available identically from `idc-index`, the REST API, and the hosted MCP server. Use whichever
route the session is already on rather than installing Python to answer a licensing question,
or dropping out of an MCP session to run a script.

| Task | `idc-index` (Python) | REST API | MCP server |
|------|----------------------|----------|------------|
| License breakdown for a selection | `sql_query` on `license_short_name` | `POST /v3/licenses` | `get_licenses` |
| Citations for a selection | `citations_from_selection()` | `POST /v3/citations` | `get_citations` |

Route-specific detail lives in `references/rest_api_guide.md` (endpoint reference, filter
syntax, and the strict request-body validation) and
`references/mcp_guide.md` (tool inventory). The license semantics below apply to all three.

## Licenses in IDC

The license is IDC metadata alongside the images, not a DICOM attribute inside the file.
Every row in the `index` table carries a `license_short_name` column; retain it with the manifest. There is no single IDC-wide license.

The following is the official IDC v24 snapshot, reviewed 2026-09-30; query your selection again at use time.

| License | Share of data | Commercial use | Attribution required |
|---------|---------------|----------------|----------------------|
| CC BY 4.0 | 74.7% | Yes | Yes |
| CC BY 3.0 | 22.1% | Yes | Yes |
| CC BY-NC 4.0 | 2.1% | **No** | Yes |
| CC BY-NC 3.0 | 0.8% | **No** | Yes |
| NLM Terms and Conditions | 0.3% | Read the terms | Yes |

About 97% of IDC data by size permits commercial reuse; just under 3% is non-commercial. Treat
any `license_short_name` that is not a recognizable Creative Commons string as custom, and
report the exact value to the user rather than assuming it permits reuse.

**Licenses attach to individual series, not to whole collections.** 39 of IDC's 176 collections
carry more than one license — analysis results and original images within one collection can
differ, as can series from different sources. Never conclude that a collection is
commercially usable from one series, or from the collection's headline license: group by
`license_short_name` over the exact selection you intend to use.

**A combined workflow must satisfy every component license.** CC BY annotations do not
relicense their CC BY-NC source images. Exclude restricted source series from a commercial
cohort unless separate permission covers the intended use.

Some commercially restricted data is in `idc-open-data-cr` (AWS) / `idc-open-cr` (GCS),
but CC BY-NC series also occur in `idc-open-data`. Never use the bucket as a license filter. See
`references/cloud_storage_guide.md` for bucket details.

## Checking licenses

### Via `idc-index`

```python
from idc_index import IDCClient
client = IDCClient()

# Licenses across all collections
licenses = client.sql_query("""
    SELECT DISTINCT
      collection_id,
      license_short_name,
      COUNT(DISTINCT SeriesInstanceUID) as series_count
    FROM index
    GROUP BY collection_id, license_short_name
    ORDER BY collection_id
""")
print(licenses)
```

```python
# Licenses present in one specific cohort — run this before handing a dataset to a user
cohort_licenses = client.sql_query("""
    SELECT license_short_name, COUNT(DISTINCT SeriesInstanceUID) as series_count
    FROM index
    WHERE Modality = 'MR' AND BodyPartExamined = 'BREAST'
    GROUP BY license_short_name
""")
print(cohort_licenses)
```

```python
# Explicit CC BY subset; custom license strings need separate review
commercial_ok = client.sql_query("""
    SELECT collection_id, SeriesInstanceUID
    FROM index
    WHERE Modality = 'CT'
      AND license_short_name IN ('CC BY 3.0', 'CC BY 4.0')
    LIMIT 20
""")
```

### Via the REST API

`POST /v3/licenses` takes the filter object **under `filters`**, just like `/v3/citations`, and
returns the per-license breakdown with series counts and sizes:

```bash
B=https://api.imaging.datacommons.cancer.gov/v3
curl -s $B/licenses \
  -H 'content-type: application/json' \
  -d '{"filters": {"terms": {"Modality": ["MR"], "BodyPartExamined": ["BREAST"]}}}'
```

Response shape: `licenses[{license_short_name, series, size_TB}]`, plus `filters_applied` and
`warnings`. Read both; a bare `terms` object returns HTTP 422 on the reviewed live build. A collection's licenses are
also included in `GET /v3/collections/{id}`.

### Via the MCP server

Call `get_licenses` with the same selection you built with `build_cohort`. The result carries
the same per-license breakdown; the CC BY vs CC BY-NC distinction above applies unchanged.

## Citations and attribution

The `source_DOI` column links to the publications describing how each dataset was generated.
All three routes resolve a selection into formatted citations. Also preserve required license
links, notices, and modification statements for the intended reuse; a citation alone is not
a complete check of every license condition.

Generate citations from the *same* selection you downloaded, not from the collection as a
whole — a five-series subset of a collection that spans several source publications should
cite only the publications it actually draws on.

### Via `idc-index`

```python
# Citations for a collection (APA is the default format)
citations = client.citations_from_selection(collection_id="rider_pilot")
for citation in citations:
    print(citation)
```

```python
# Citations for a specific set of series — matches what you actually downloaded
results = client.sql_query("""
    SELECT SeriesInstanceUID FROM index
    WHERE collection_id = 'tcga_luad' LIMIT 5
""")
citations = client.citations_from_selection(
    seriesInstanceUID=list(results['SeriesInstanceUID'].values)
)
```

```python
# BibTeX, for LaTeX manuscripts
bibtex_citations = client.citations_from_selection(
    collection_id="tcga_luad",
    c

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

