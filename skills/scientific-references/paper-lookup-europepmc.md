---
id: sciref-paper-lookup-europepmc
name: "Scientific Ref: Europe PMC API"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (paper-lookup): Europe PMC API"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "paper lookup europepmc"
  - "artigo lookup europepmc"
  - "europe pmc api"
keywords:
  - "paper"
  - "lookup"
  - "europepmc"
  - "artigo"
  - "specialized"
  - "scientific"
  - "reference"
  - "europe"
---

# Europe PMC API

Europe PMC is a single search surface over PubMed abstracts, PMC full text, **preprints** (bioRxiv,
medRxiv, Research Square, SSRN and others), patents, NHS guidelines, and theses. It is the one API in
this skill that does keyword search *across* those corpora at once.

Reach for it when you need something the others cannot do:

- **Keyword search of bioRxiv/medRxiv preprints.** The preprint servers' own APIs have no keyword
  search at all (see `references/biorxiv.md`). Europe PMC indexes them and filters with `SRC:"PPR"`.
- **Search inside full text**, not just titles and abstracts, with the results-limiting filters
  (`HAS_FT:Y`, `OPEN_ACCESS:Y`) applied server-side.
- **Full text that fails honestly.** `fullTextXML` returns a clean **404** when an article is not
  open access, where NCBI eFetch returns HTTP 200 with metadata and no `<body>` (see the hazard
  section of `references/pmc.md`).

All figures below verified 2026-07-27.

## Base URL

```
https://www.ebi.ac.uk/europepmc/webservices/rest
```

## Authentication

None. No key, no email parameter, no registration.

## Rate Limits

No published per-second limit. Europe PMC asks for reasonable use and recommends `cursorMark`
pagination over deep `page` offsets for large walks. Keep concurrency low and serialize long walks.

## Key Endpoints

### 1. Search

```
GET /search?query={query}&format=json&pageSize={n}&resultType={type}
```

| Parameter | Default | Description |
|---|---|---|
| `query` | required | Query language below. URL-encode it. |
| `format` | `xml` | `json`, `xml`, or `dc` |
| `resultType` | `lite` | `idlist` (IDs only), `lite` (core bibliographic), `core` (adds abstract, full-text links, MeSH, grants) |
| `pageSize` | 25 | Max **1,000**. Over that is rejected, not clamped -- see the error shape below. |
| `cursorMark` | `*` | Deep pagination -- use this, not `page` |
| `page` | 1 | 1-based. Only for shallow paging. |
| `sort` | relevance | `CITED desc`, `P_PDATE_D desc` (publication date), `TITLE asc` -- note the **space** before the direction, not a colon |

**Example** -- preprints about CRISPR:

```bash
curl -s --get "https://www.ebi.ac.uk/europepmc/webservices/rest/search" \
  --data-urlencode 'query=CRISPR AND SRC:"PPR"' \
  --data-urlencode 'format=json' \
  --data-urlencode 'pageSize=2' \
  --data-urlencode 'resultType=lite'
```

Returns `hitCount` 13341 with `resultList.result[]` entries whose `id` values look like `PPR1283561`
and `source` is `PPR`.

**Response envelope:**

```json
{
  "version": "6.9",
  "hitCount": 13341,
  "nextCursorMark": "AoIIQExCVyg1NTg2NjE3NQ==",
  "nextPageUrl": "https://www.ebi.ac.uk/europepmc/webservices/rest/search?...",
  "request": {"queryString": "CRISPR AND SRC:\"PPR\"", "resultType": "lite", "cursorMark": "*", "pageSize": 2},
  "resultList": {"result": [...]}
}
```

The echoed `request.queryString` is the query **as parsed** -- diff it against what you sent to catch
a mangled or truncated query before trusting `hitCount`.

**Errors arrive with HTTP 200 and no `resultList`.** `pageSize=1001` returns:

```json
{"errCode": 404, "errMsg": "Invalid page size provided. Valid size is between 1 and 1000"}
```

Note the `errCode` is 404 *inside a 200 response*. Check for `errCode` / the absence of `resultList`
before indexing into results -- neither the HTTP status nor an exception will tell you.

### 2. Full text XML

```
GET /{PMCID}/fullTextXML
```

```
https://www.ebi.ac.uk/europepmc/webservices/rest/PMC7029759/fullTextXML
```

Returns a JATS `<article>` (not wrapped in `<pmc-articleset>` the way eFetch is). Pipe it through
`scripts/jats_to_text.py`, which handles both wrappers.

**404 means this endpoint did not supply the requested XML.** Check the PMCID and metadata before attributing it to licensing; an absent/wrong identifier can also fail. The historical PMC1500000 probe returned 404, but a single failure is not a universal OA classifier.

### 3. Citations and references

```
GET /{source}/{id}/citations?format=json&pageSize={n}&page={n}
GET /{source}/{id}/references?format=json&pageSize={n}&page={n}
```

`source` is the corpus code: `MED` (PubMed), `PMC`, `PPR` (preprints), `PAT` (patents), `AGR`, `CBA`,
`CTX`, `ETH`, `HIR`, `NBK`.

```
https://www.ebi.ac.uk/europepmc/webservices/rest/MED/32117569/citations?format=json&pageSize=1
```

Returns `hitCount` plus `citationList.citation[]` (or `referenceList.reference[]`). Both wrap the
list in a corpus-specific key, so parse by endpoint rather than assuming `resultList`.

### 4. Supplementary files and annotations

```
GET /{PMCID}/supplementaryFiles
```

This route takes a **PMCID without a source segment**, e.g.
`/PMC5998401/supplementaryFiles`, and returns a ZIP archive, not JSON.
`/MED/32117569/supplementaryFiles` is not the documented route. Its 404
cannot establish that an article has no supplements. Inspect `hasSuppl` in
`resultType=core` and the archive content; non-OA images may be excluded.

The previously listed `/textMinedTerms/{semanticType}` route is not in the
current Articles REST operation list and was not verified as supported.
Use PubTator3 for this skill's entity workflow, or consult the official
[Europe PMC Annotations API](https://europepmc.org/AnnotationsApi). Do not
interpret a legacy-route 404 as evidence that no annotations exist.

## Query Language

Field-prefixed terms combined with `AND` / `OR` / `NOT` (uppercase), quoted phrases, and
parentheses.

| Field | Matches | Example |
|---|---|---|
| `SRC` | Corpus | `SRC:"PPR"` (preprints), `SRC:"MED"`, `SRC:"PMC"` |
| `PUBLISHER` | Preprint server or publisher | `PUBLISHER:"bioRxiv"`, `PUBLISHER:"medRxiv"` |
| `AUTH` | Author name | `AUTH:"Doudna J"` |
| `TITLE` | Title | `TITLE:"gene editing"` |
| `ABSTRACT` | Abstract | `ABSTRACT:organoid` |
| `PUB_YEAR` | Publication year | `PUB_YEAR:2023`, `PUB_YEAR:[2020 TO 2024]` |
| `HAS_FT` | Full text indexed | `HAS_FT:Y` |
| `OPEN_ACCESS` | Open access | `OPEN_ACCESS:Y` |
| `IN_EPMC` | Full text hosted in Europe PMC | `IN_EPMC:Y` |
| `DOI` | DOI | `DOI:"10.1038/nature12373"` |
| `EXT_ID` | PMID | `EXT_ID:32117569` |
| `JOURNAL` | Journal title | `JOURNAL:"Nature"` |
| `MESH` | MeSH term | `MESH:"CRISPR-Cas Systems"` |
| `LANG` | Language | `LANG:eng` |

A bare term with no prefix searches title, abstract, and full text together.

**The pattern that closes the preprint gap:**

```bash
curl -s --get "https://www.ebi.ac.uk/europepmc/webservices/rest/search" \
  --data-urlencode 'query

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

