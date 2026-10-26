---
id: sciref-literature-review-database-strategies
name: "Scientific Ref: Literature database search strategies"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (literature-review): Literature database search strategies"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "literature review database strategies"
  - "literatura revisao database strategies"
  - "literature database search strategies"
keywords:
  - "literature"
  - "review"
  - "database"
  - "strategies"
  - "literatura"
  - "revisao"
  - "specialized"
  - "scientific"
  - "reference"
---

# Literature database search strategies

Reviewed 2026-09-30. These are bibliographic discovery contracts, not a promise
of complete retrieval. Save query, platform, date/time, date-field meaning,
filters, raw pages, reported total, exported count, and any failures. Mark a
capped or interrupted retrieval incomplete before screening it.

## Source selection and query design

1. Define the review type and eligibility criteria before seeing results. Use
   PICO for intervention questions; adapt the framework for other questions.
2. Select complementary bibliographic databases, relevant registries, preprint
   servers, and grey literature sources. A web search and a biological entity
   database are not substitutes for a discipline's bibliographic index.
3. Build synonym groups with OR and combine concepts with AND. Pilot against
   known eligible papers. Consider whether outcome filters, language limits,
   publication-type limits, or NOT terms discard relevant studies.
4. Translate each query to that platform. Wildcards and field syntax are not
   portable: do not copy PubMed `[MeSH]`, arXiv `ti:`, or search-engine operators
   into another API. Record the actual translated query, not just keywords.
5. For systematic reviews, screen against protocol criteria regardless of venue,
   author reputation, institutional affiliation, or citation count. Bibliometric
   metrics reflect exposure and field/age effects, not risk of bias.

## PubMed and PMC

Use the [PubMed interface](https://pubmed.ncbi.nlm.nih.gov/advanced/) or NCBI
E-utilities. `gget search` searches Ensembl and has no PubMed/bioRxiv mode.
PubMed contains bibliographic records; PMC is a full-text repository with a
partly overlapping corpus. Do not equate access to an abstract with full text.

A small first-page request, not a complete review search:

```bash
mkdir -p sources
curl --fail-with-body --get 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi' \
  --data-urlencode 'db=pubmed' \
  --data-urlencode 'term=(CRISPR[Title/Abstract]) AND ("Anemia, Sickle Cell"[MeSH Terms])' \
  --data-urlencode 'retmode=json' --data-urlencode 'retmax=5' \
  --data-urlencode 'tool=literature_review' -o sources/pubmed-first-page.json
```

- ESearch returns `esearchresult.count` (often a string), `idlist`, and query
  translation/warnings. Inspect these; HTTP 200 alone does not confirm success.
- Use `retstart`/`retmax` for paging **within the first 10,000 PubMed matches**.
  Partition larger searches into recorded, deduplicated subqueries or use a
  documented bulk method; the History server does not bypass this limit.
- EFetch is `GET .../efetch.fcgi?db=pubmed&id=PMID1,PMID2&retmode=xml` (or POST for
  large ID sets). Parse `PubmedArticleSet` XML, preserve article/book records,
  and reconcile requested versus returned IDs.
- No key is needed for small requests. Supply a real contact `email` and `tool`
  for sustained use; optional `api_key` raises the default shared limit from
  3 requests/s per IP to 10/s per key. Account for concurrent clients.
- Use explicit `[Publication Date]` ranges, and record the selected field.
  A historical example such as `2020:2024[DP]` does not mean "current years".

Sources: [NLM parameter guide](https://www.nlm.nih.gov/dataguide/eutilities/utilities.html),
[PubMed 10,000-result ceiling](https://ncbiinsights.ncbi.nlm.nih.gov/2021/10/05/updated-pubmed-api/),
[NCBI usage guidelines](https://eutilities.github.io/site/API_Key/usageandkey/).

## bioRxiv and medRxiv

The [official API](https://api.biorxiv.org/) provides date/DOI metadata retrieval,
not a general keyword query endpoint. Use the server's search interface for
keyword discovery or filter the downloaded metadata explicitly.

- `GET https://api.biorxiv.org/details/{server}/{from}/{to}/{cursor}/json`, with
  server `biorxiv` or `medrxiv`, date strings `YYYY-MM-DD`, zero-based
  cursor (start at 0), and optional `category=cell_biology`.
- Response `collection[]` holds records; `messages[]` describes status, count,
  cursor, and totals. Date-range calls return at most 30 records; advance the
  cursor by the number received, retain all versions, and check totals/status.
- Single DOI: `/details/{server}/{doi}/na/json`. Preserve DOI, `version`, `date`,
  abstract, license, and `published` linkage. A preprint and a published report
  may describe one study but are distinct reports.
- `/pubs/{server}/{from}/{to}/{cursor}` maps publication links, with up to 100
  entries per page. It has a different schema (`biorxiv_doi`, `published_doi`).
- Public reads need no API key. Use conservative sequential calls and stop on
  throttling/errors; do not interpret missing publication links as proof that
  a preprint remains unpublished.

## arXiv

`GET https://export.arxiv.org/api/query` accepts `search_query`, `id_list`,
`start` (zero-based), `max_results`, `sortBy`, and `sortOrder`. No key is needed.

```bash
curl --fail-with-body --get 'https://export.arxiv.org/api/query' \
  --data-urlencode 'search_query=cat:q-bio.QM AND ti:"single cell"' \
  --data-urlencode 'start=0' --data-urlencode 'max_results=5' \
  --data-urlencode 'sortBy=submittedDate' --data-urlencode 'sortOrder=descending' \
  -o sources/arxiv-first-page.xml
```

Parse Atom namespaces, `opensearch:totalResults`, and entry IDs; error entries
can arrive in an Atom feed. Preserve `vN`, original `published`, and `updated`
dates. `ti:` is the title field, not `title:`. Use a single connection with at
least three seconds between requests. Use pages no larger than 2,000 and do
not expect offsets to provide more than 30,000 matches; partition or use the
bulk interfaces. This is preprint discovery, not evidence of peer review.

Source: [arXiv API manual](https://info.arxiv.org/help/api/user-manual.html).

## Semantic Scholar

Use the [Graph API contract](https://api.semanticscholar.org/api-docs/graph)
(and its downloadable [schema](https://api.semanticscholar.org/graph/v1/swagger.json)).

- Relevance search: `GET https://api.semanticscholar.org/graph/v1/paper/search`;
  plain-text `query`, separate `year=2020-2024`, optional `fields`, `offset`,
  `limit` (maximum 100). Response has `data[]`, `total`, and optional `next`.
  Only 1,000 relevance-ranked records are retrievable; not an exhaustive export.
- Bulk search: `GET .../paper/search/bulk`; query uses its documented Boolean
  grammar (`+`, `|`, `-`, quotes, parentheses), with separate filters and
  `fields`. Response has `data[]` and a continuation `t

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

