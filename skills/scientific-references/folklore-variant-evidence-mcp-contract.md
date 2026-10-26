---
id: sciref-folklore-variant-evidence-mcp-contract
name: "Scientific Ref: Folklore Clinical Variant Interpretation MCP public contract"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (folklore-variant-evidence): Folklore Clinical Variant Interpretation MCP public contract"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "folklore variant evidence mcp contract"
  - "folklore clinical variant interpretation mcp public contract"
keywords:
  - "folklore"
  - "variant"
  - "evidence"
  - "mcp"
  - "contract"
  - "specialized"
  - "scientific"
  - "reference"
---

# Folklore Clinical Variant Interpretation MCP public contract

Use this reference when constructing calls or interpreting public results.
Reviewed 2026-09-30 against adapter 1.5.0, official source commit
`fef7220d66f99c3c021f8eee1cdd6b8ea4b0a64b`, and live discovery/calls. Discover the
live schemas rather than assuming the published adapter source and deployment
are identical.

## Connection

- Endpoint: `https://api.helena.bio/folklore/v1/mcp`
- Authentication: none
- Transport: stateless Streamable HTTP
- Publisher: Helena Bioinformatics
- Registry identity: `io.github.helena-bioinformatics/folklore`
- Reviewed modern protocol: `2026-07-28`

Verify tools with `tools/list` at call time. Do not infer tool availability from
this skill alone.

For direct JSON-RPC POST requests, use `Content-Type: application/json` and
`Accept: application/json, text/event-stream`. Send `MCP-Protocol-Version` plus
`Mcp-Method` equal to the body `method`; for `tools/call`, send `Mcp-Name` equal
to `params.name`. Include the protocol version and client capabilities in
`params._meta`, as in the skill's curl example. The discovery request is:

```bash
curl --silent --show-error --fail-with-body --max-time 60 \
  -X POST https://api.helena.bio/folklore/v1/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -H 'MCP-Protocol-Version: 2026-07-28' \
  -H 'Mcp-Method: tools/list' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{"_meta":{"io.modelcontextprotocol/protocolVersion":"2026-07-28","io.modelcontextprotocol/clientCapabilities":{}}}}'
```

`server/discover` is an optional preflight using the same pattern with that
method in both header and body. It reports supported versions and server
metadata, without a stateful initialization exchange. This modern recipe does
not establish compatibility with every legacy MCP client.

## Read the correct response envelope

First handle HTTP failure or a JSON-RPC `error`; then inspect MCP `result.isError`
and `result.structuredContent`. Call that structured object `s` below. Handle any
non-null `s.adapter_error` before reading scientific fields; preserve its `code`,
`message` and `retryable`. Invalid inputs can fail validation before reaching a
scientific status. Retry only a retryable failure, with bounded backoff and any
`Retry-After` guidance. A live HTTP 429 with JSON-RPC code `-32029` was observed;
there is no verified universal request quota to hardcode.

| Tool | Successful structured content |
|---|---|
| `search_variant_evidence` | `s.result.status`; identity at `s.result.identity`; interpretation at `s.result.interpretation`; outer `record_url`, `usage_boundary`, `adapter_error` |
| `search_variant_literature` | Direct `s.status`, `s.variant_result`, and nullable `s.literature`; no extra `s.result` wrapper |
| `get_publication_details` | `s.publication` and `s.usage_boundary`; no scientific `status` field |
| `search_literature_corpus` | `s.results`, `returned_count`, pagination and retrieval metadata; no scientific `status` field |
| Both gene-disease tools | Direct `s.status` (`ok` or `not_found`), `associations`, `pagination`, `source`, `warnings`, `usage_boundary` |

The evidence envelope has `contract_version: "1"` and its scientific result has
`search_contract_version: "1.0"`. Literature/details/corpus use
`contract_version: "1.0"`; gene-disease uses camel-case `contractVersion: "1.0"`.
Do not impose the evidence envelope on the other tools. Adapter failures for
literature/details/corpus can use the evidence-style envelope with `result: null`;
gene-disease failures contain `adapter_error` and `usage_boundary` directly.
Unrecognized status values or missing required fields are a contract problem,
not an empty result.

Preserve complete structured content. The evidence and literature text fallbacks
are summaries and need not contain all provenance or candidate data.

## `search_variant_evidence`

Required input:

```yaml
assembly: GRCh38
query: <one public germline nuclear SNV or simple indel>
```

`query` is 1–512 characters. `assembly` defaults to `GRCh38`, but send it
explicitly for reproducibility. The schema forbids additional arguments.
The `query` may be a coordinate, genomic/coding/protein HGVS, SPDI, rsID, or a
returned `canonical_key` in this form:

```text
GRCh38:chrN:position:REF:ALT
```

The six public outcome states are:

- `resolved`
- `ambiguous`
- `not_found`
- `invalid_request`
- `unsupported`
- `resolution_unavailable`

Do not collapse these states. In particular, never convert `ambiguous` into
`resolved`, and never convert `resolution_unavailable` into `not_found`.
For ambiguity, preserve `total_candidate_count` and `candidates_truncated`;
the candidate list may contain only the first ten. For resolution, reuse
`s.result.identity.canonical_key`. Check `s.result.interpretation.status`:
`success` permits reading the returned classification, whereas `unavailable`
requires preserving its error despite a resolved identity.

## `search_variant_literature`

Use only after resolution when composing an automatic workflow:

```yaml
assembly: GRCh38
query: <returned canonical_key>
question: <optional public scientific focus>
limit: <1 to 25>
```

The optional `question` is 3–500 characters, `limit` defaults to 10, and there is
no cursor/offset argument for this tool. The response preserves the variant
result at `s.variant_result` and returns literature at `s.literature` only when
variant resolution permits it. Preserve `candidate_count`, aliases, corpus
provenance and limitations; `limit` does not make a page exhaustive. Publication
match types are `exact_variant`, `variant_alias`, and `gene_association`.

## `get_publication_details`

Input `{"pmid":"<returned PMID>"}`, a string of 1–12 digits without a `PMID:`
prefix. Preserve `publication.is_retracted`, bibliographic metadata, source URLs,
gene mentions, and variant mentions. A `publication_not_found` adapter error
means no record in this service's corpus, not that the PMID does not exist in
PubMed. A missing abstract or full-text URL is not a missing publication.

## `search_literature_corpus`

Use for source-linked scientific-literature discovery with a natural-language
question, publication identifier, gene, variant, phenotype, HPO, or OMIM
concept. Arguments are `query` (3–200 characters), `limit` (1–25, default 20),
`sort` (`relevance`, `newest`, `oldest`; default `relevance`) and optional `cursor`.
Keep all queries publi

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

