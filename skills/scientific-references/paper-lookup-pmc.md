---
id: sciref-paper-lookup-pmc
name: "Scientific Ref: PMC (PubMed Central)"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (paper-lookup): PMC (PubMed Central)"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "paper lookup pmc"
  - "artigo lookup pmc"
  - "pmc (pubmed central)"
keywords:
  - "paper"
  - "lookup"
  - "pmc"
  - "artigo"
  - "specialized"
  - "scientific"
  - "reference"
  - "pubmed"
---

# PMC (PubMed Central)

PMC is a **full-text archive** of biomedical and life sciences articles. It is separate from PubMed -- PubMed has citations/abstracts, PMC has full text. Not all PubMed articles are in PMC, and vice versa.

## E-utilities for PMC

### Base URL

```
https://eutils.ncbi.nlm.nih.gov/entrez/eutils/
```

Same E-utilities as PubMed, but with `db=pmc`.

### eSearch -- Search PMC

```
GET /esearch.fcgi?db=pmc&term={query}&retmode=json
```

Same parameters as PubMed eSearch. PubMed and PMC ESearch are both limited to the first 10,000 matching IDs; partition larger searches or use an appropriate bulk workflow. Returns PMC UIDs (numeric, e.g., `13033346`). You need to prepend "PMC" to get a PMCID (e.g., `PMC13033346`).

### eFetch -- Get Full Text XML

```
GET /efetch.fcgi?db=pmc&id={pmcid}&retmode=xml
```

| rettype | retmode | Returns |
|---------|---------|---------|
| *(omit)* | `xml` | JATS XML -- full text for **eligible OA and Author Manuscript articles**; metadata only otherwise, with no error. See the hazard below before using this. |

**Example:**
```
https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pmc&id=7029759&retmode=xml
```

The XML uses JATS (Journal Article Tag Suite) format:
- `<front>` -- journal metadata, article metadata, author info
- `<body>` -- full article text with `<sec>` sections, `<p>` paragraphs, `<fig>` figures
- `<back>` -- `<ref-list>` with all references

Pass numeric IDs only (not "PMC7029759", just "7029759").

### Hazard: eFetch returns metadata-only XML for non-OA articles, with HTTP 200

This is the most dangerous failure in this skill, because nothing about the response says it failed.
When the publisher does not permit XML redistribution, eFetch returns a **well-formed
`<pmc-articleset>`** containing `<front>` metadata, **no `<body>`**, and the reason as an XML
*comment* -- which every standard parser discards. Verified 2026-07-27 on PMCID 1500000:

```
HTTP/1.1 200 OK

<pmc-articleset><article article-type="obituary" ...>
  <!--The publisher of this article does not allow downloading of the full text in XML form.-->
  <front>...</front>
</article></pmc-articleset>
```

An agent that fetches this, parses it, and reports "retrieved full text" has retrieved only the
title, journal, and author list. An article being readable on the PMC website does not establish that its XML is available through this API. The absence of a body is a retrieval limitation, not evidence about the article contents.

**Always confirm `<body>` exists before claiming you have full text.** Two ways, in order of
preference:

1. **Use `scripts/jats_to_text.py`**, which exits non-zero with `no <body> element` when the article
   is metadata-only and surfaces the publisher-restriction comment instead of dropping it.
2. **Fall back to Europe PMC** (`references/europepmc.md`), whose `fullTextXML` endpoint returns a
   clean **404** for the same article rather than a 200 with no body -- an honest failure is easier to
   handle than a plausible one.

If full text is unavailable, say so explicitly and offer the abstract (PubMed eFetch) or an OA copy
elsewhere (Unpaywall, CORE) rather than presenting `<front>` metadata as the article.

## Retired OA Web Service

The PMC OA Web Service (`oa.fcgi`) was retired on **2026-08-25**. Do not use it
as an availability preflight, retraction check, or source of FTP package links.
The old OA-package FTP workflow is no longer the supported retrieval path.
For a targeted paper, fetch via E-utilities, BioC, or Europe PMC and validate
that the response actually contains article text. For bulk access consult
[PMC Article Datasets](https://pmc.ncbi.nlm.nih.gov/tools/textmining/) and the
[PMC Cloud Service](https://pmc.ncbi.nlm.nih.gov/tools/cloud/).

Use the article's current license for reuse decisions. For retractions inspect
PubMed/publisher notices and Crossref update relationships; a missing OA copy
says nothing about retraction status.

## BioC API -- Structured Full Text

An alternative way to get full text in a structured passage format.

### Base URL

```
https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/pmcoa.cgi/
```

### Endpoint

```
GET /BioC_{format}/{id}/{encoding}
```

| Parameter | Values |
|-----------|--------|
| `format` | `json` or `xml` |
| `id` | PMID (e.g., `17299597`) or PMCID (e.g., `PMC7029759`) |
| `encoding` | `unicode` or `ascii` |

**Example:**
```
https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/pmcoa.cgi/BioC_json/PMC7029759/unicode
```

**Response structure (JSON):** a list of BioC collections. Read `[0].documents`, not a top-level `documents` object.
```json
[{
  "source": "PMC",
  "documents": [{
    "id": "PMC7029759",
    "infons": {"license": "...", "doi": "..."},
    "passages": [
      {
        "offset": 0,
        "infons": {"section_type": "TITLE"},
        "text": "Article title..."
      },
      {
        "offset": 42,
        "infons": {"section_type": "ABSTRACT"},
        "text": "Abstract text..."
      },
      {
        "offset": 500,
        "infons": {"section_type": "INTRO"},
        "text": "Introduction text..."
      }
    ]
  }]
}]
```

Section types: `TITLE`, `ABSTRACT`, `INTRO`, `METHODS`, `RESULTS`, `DISCUSS`, `CONCL`, `REF`, `SUPPL`, `FIG`, `TABLE`

**Coverage:** PMC Open Access and eligible Author Manuscript articles; not all PMC records. Do not use the count in the 2019 BioC paper as a current coverage total.

## PMC ID Converter API

Converts between PMID, PMCID, DOI, and Manuscript ID.

### Base URL

```
https://pmc.ncbi.nlm.nih.gov/tools/idconv/api/v1/articles/
```

### Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| `ids` | Yes | Up to 200 comma-separated IDs, all of the same identifier type |
| `idtype` | No | `pmcid`, `pmid`, `mid`, `doi` (default: auto-detect) |
| `format` | No | `json`, `xml`, `csv`, `html` (default: xml) |
| `tool` | Recommended | Your application name |
| `email` | Recommended | Your contact email |

**Example:**
```
https://pmc.ncbi.nlm.nih.gov/tools/idconv/api/v1/articles/?ids=PMC7029759&format=json
```

**Response:**
```json
{
  "status": "ok",
  "records": [{
    "pmcid": "PMC7029759",
    "pmid": "32117569",
    "doi": "10.12688/f1000research.22211.2"
  }]
}
```

The JSON `pmid` may be numeric; normalize identifiers to strings before joining across APIs. Inspect per-record errors/availability as well as top-level `status`. Only returns related identifiers for articles tha

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

