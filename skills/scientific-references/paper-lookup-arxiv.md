---
id: sciref-paper-lookup-arxiv
name: "Scientific Ref: arXiv API"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (paper-lookup): arXiv API"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "paper lookup arxiv"
  - "artigo lookup arxiv"
  - "arxiv api"
keywords:
  - "paper"
  - "lookup"
  - "arxiv"
  - "artigo"
  - "specialized"
  - "scientific"
  - "reference"
---

# arXiv API

arXiv is a preprint server for physics, mathematics, computer science, quantitative biology, quantitative finance, statistics, electrical engineering, and economics.

**Important:** The arXiv API returns **Atom XML**, not JSON. There is no JSON option.

## Base URL

```
https://export.arxiv.org/api/query
```

## Authentication

None required. Fully public.

## Query Parameters

```
GET https://export.arxiv.org/api/query?search_query={query}&start={n}&max_results={n}
```

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `search_query` | Yes* | -- | Search using field prefixes + boolean operators |
| `id_list` | Yes* | -- | Comma-separated arXiv IDs (e.g., `2103.15348,2005.14165`) |
| `start` | No | 0 | Pagination offset (0-based) |
| `max_results` | No | 10 | Use slices of at most 2,000; refine searches exceeding 1,000. The manual describes a 30,000-result query limit |
| `sortBy` | No | `relevance` | `relevance`, `lastUpdatedDate`, `submittedDate` |
| `sortOrder` | No | `descending` | `ascending` or `descending` |

*At least one of `search_query` or `id_list` must be provided. They can be combined (intersection).

## Search Field Prefixes

| Prefix | Searches |
|--------|----------|
| `ti:` | Title |
| `au:` | Author |
| `abs:` | Abstract |
| `co:` | Comment |
| `jr:` | Journal reference |
| `cat:` | Subject category |
| `rn:` | Report number |
| `all:` | All fields |

## Boolean Operators

- `AND` -- both conditions
- `OR` -- either condition
- `ANDNOT` -- exclude
- Parentheses for grouping (URL-encode as `%28` / `%29`)
- Quoted phrases (URL-encode as `%22`)

## Example Queries

**Search all fields:**
```
https://export.arxiv.org/api/query?search_query=all:transformer+attention&max_results=5
```

**Author + category:**
```
https://export.arxiv.org/api/query?search_query=au:hinton+AND+cat:cs.LG&max_results=10
```

**Title search:**
```
https://export.arxiv.org/api/query?search_query=ti:%22attention+is+all+you+need%22
```

**By ID:**
```
https://export.arxiv.org/api/query?id_list=2103.15348
```

**Multiple IDs:**
```
https://export.arxiv.org/api/query?id_list=2103.15348,2005.14165,1706.03762
```

**Date range** -- the brackets **must** be percent-encoded as `%5B` / `%5D`:
```
https://export.arxiv.org/api/query?search_query=cat:cs.AI+AND+submittedDate:%5B202401010000+TO+202412312359%5D
```

Passing literal `[` and `]` to `curl` fails before the request is even sent: curl reads them as a
globbing range and exits **3** (`bad range specification`) with no output and no HTTP status to
diagnose. Verified 2026-07-27:

```bash
# exit 3, nothing fetched, no error body to read
curl -s "https://export.arxiv.org/api/query?search_query=submittedDate:[202401010000+TO+202401020000]"

# exit 0, totalResults 35 -- either fix works
curl -s  "https://export.arxiv.org/api/query?search_query=cat:cs.AI+AND+submittedDate:%5B202401010000+TO+202401020000%5D"
curl -sg "https://export.arxiv.org/api/query?search_query=cat:cs.AI+AND+submittedDate:[202401010000+TO+202401020000]"
```

Prefer the encoded form over `curl -g`: it is what the API expects, and it survives being copied
into a fetch tool, a Python client, or a shell that is not curl. Timestamps are `YYYYMMDDHHMM` in
UTC and the range is inclusive on both ends.

## Response Format (Atom XML)

```xml
<feed xmlns="http://www.w3.org/2005/Atom">
  <opensearch:totalResults>1234</opensearch:totalResults>
  <opensearch:startIndex>0</opensearch:startIndex>
  <opensearch:itemsPerPage>10</opensearch:itemsPerPage>

  <entry>
    <id>http://arxiv.org/abs/1706.03762v7</id>   <!-- http, while the links below are https -->
    <title>Attention Is All You Need</title>
    <summary>The dominant sequence transduction models are based on...</summary>
    <published>2017-06-12T17:57:34Z</published>
    <updated>2023-08-02T00:00:12Z</updated>
    <author><name>Ashish Vaswani</name></author>
    <author><name>Noam Shazeer</name></author>
    <!-- more authors -->
    <category term="cs.CL" scheme="http://arxiv.org/schemas/atom"/>
    <arxiv:primary_category term="cs.CL"/>
    <link rel="alternate" type="text/html" href="https://arxiv.org/abs/1706.03762v7"/>
    <link rel="related" type="application/pdf" title="pdf" href="https://arxiv.org/pdf/1706.03762v7"/>
    <arxiv:comment>15 pages, 5 figures</arxiv:comment>
    <!-- <arxiv:doi> and <arxiv:journal_ref> appear only when the author registered them.
         1706.03762 has neither. -->
  </entry>
</feed>
```

### Key XML elements per entry

| Element | Description |
|---------|-------------|
| `<id>` | arXiv URL: `http://arxiv.org/abs/{id}` |
| `<title>` | Paper title |
| `<summary>` | Abstract |
| `<published>` | Original submission date (ISO 8601) |
| `<updated>` | Date of latest version |
| `<author><name>` | One per author |
| `<category term="...">` | Subject categories |
| `<arxiv:primary_category>` | Primary classification |
| `<link rel="alternate">` | Abstract page URL |
| `<link rel="related" title="pdf">` | PDF URL |
| `<arxiv:doi>` | The **journal** DOI, and only when the author registered one -- see below |
| `<arxiv:comment>` | Author comments |
| `<arxiv:journal_ref>` | Journal reference, same conditional presence |

### `<arxiv:doi>` is not the arXiv DOI

`<arxiv:doi>` carries the DOI of the *published journal version*
(`10.1103/PhysRevD.50.43`), and it is **absent** for any preprint that was never
published or whose author never registered it. Verified 2026-07-27: `id_list=1706.03762`
("Attention Is All You Need") returns **no** `<arxiv:doi>` element at all.

arXiv also mints its own DOI, conventionally `10.48550/arXiv.{id}`, but **the API never returns it**,
and constructing one is only sometimes a usable key. Verified 2026-07-27 for `1706.03762`:

| Where you send `10.48550/arXiv.1706.03762` | Result |
|---|---|
| `doi.org` | **200** -- it resolves |
| Crossref `/works/10.48550%2FarXiv.1706.03762` | **404** `Resource not found` -- it is a DataCite DOI, not registered with Crossref |
| OpenAlex `/works/doi:10.48550/arXiv.1706.03762` | **404**, and `filter=doi:...` gives `count: 0` |

The OpenAlex miss is not a case problem -- `doi:10.48550/arxiv.2102.05095` and
`doi:10.48550/arXiv.2102.05095` both return 200, so the lookup is case-insensitive and *does* work for
many arXiv preprints. It is that **not every arXiv paper is under a `10.48550` DOI there**:
OpenAlex holds "Attention Is All You Need" as `W2626778328` with DOI `10.65215/2q58a426`,

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

