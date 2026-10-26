---
id: sciref-exa-search-web-extract
name: "Scientific Ref: URL Extraction"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (exa-search): URL Extraction"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "exa search web extract"
  - "exa search web extrair"
  - "url extraction"
keywords:
  - "exa"
  - "search"
  - "web"
  - "extract"
  - "extrair"
  - "specialized"
  - "scientific"
  - "reference"
  - "extraction"
---

# URL Extraction

Extract content from: $ARGUMENTS

## Command

Choose a short, descriptive filename based on the URL or content (e.g., `alphafold-paper`, `nature-editorial`). Use lowercase with hyphens, no spaces.

```bash
uv run "$SKILL_PATH/scripts/exa_extract.py" "$ARGUMENTS" \
  --text \
  -o "$FILENAME.json"
```

You can pass up to 100 URLs as positional arguments in one `/contents` call. Split larger lists into separate invocations; the wrapper rejects oversized batches.

Content modes:

- `--text` (default if nothing else is passed) returns full-text content
- `--highlights` returns extracted passages instead of full text

## Academic content handling

When extracting from academic sources (arXiv, PubMed, journal sites, conference proceedings), use `--text` to request the page text:

```bash
uv run "$SKILL_PATH/scripts/exa_extract.py" "$URL" \
  --text \
  -o "$FILENAME.json"
```

For arXiv, `/abs/` is an abstract/metadata page; it is not proof that the full
paper was extracted. Use a public HTML or PDF URL when full paper content is
needed, and inspect for missing methods, results, equations, figures, tables,
and references. Extraction may be partial, unavailable, or blocked by access
controls. Do not present an abstract or truncated extraction as the full paper.

### Freshness and returned status

Add `--max-age-hours 0` for a fresh fetch, `-1` for cache only, or an integer
1–720 to bound cache age. Omit it to let Exa use cached content and fetch when
unavailable. This maps to SDK `max_age_hours` / JSON `maxAgeHours`; the older
`livecrawl` control is deprecated.

Output contains `urls`, `num_results`, `results`, and `statuses`. Each SDK status
contains `id` (requested URL or document ID), `status` (`success` or `error`),
and optional `source` (`cached` or `crawled`). Associate statuses by ID, not array
position, and check that successful results contain usable text/highlights.
SDK 2.23.0 discards API `statuses[].error` and `requestId`; these are unavailable
in this wrapper. Do not guess whether an error was a paywall, timeout, or another
cause. Publication date is not crawl/retrieval time.

## Response format

Return content as:

**[Page Title](URL)**

For academic papers, include structured metadata when available:
- **Authors:** list of authors (from the `author` field)
- **Published:** from `published_date`

Then the extracted content, with these rules:
- Follow the requested extraction scope; quote only content that can be reproduced lawfully, otherwise summarize and link to the saved extraction
- When extracting a requested list, preserve its ordering and note any missing items
- Strip only obvious noise: nav menus, footers, ads
- Preserve the meaning and exact values of facts, names, numbers, and dates
- For academic papers, retain relevant figure/table captions and references when present; report omissions

**Partial-result handling** — when batching multiple URLs, one or more may fail (paywall, robots.txt, timeout). Report which URLs extracted successfully and which failed, rather than silently dropping failures.

After the response, mention the output file path (`$FILENAME.json`) so the user knows it's available for follow-up questions.

Verified against the [Contents API](https://exa.ai/docs/reference/get-contents) and [Python SDK source](https://github.com/exa-labs/exa-py/blob/master/exa_py/api.py) on 2026-09-30; authenticated commands are illustrative.

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

