---
id: sciref-research-lookup-api-contracts
name: "Scientific Ref: Reviewed service contracts"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (research-lookup): Reviewed service contracts"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "research lookup api contracts"
  - "pesquisa lookup api contracts"
  - "reviewed service contracts"
keywords:
  - "research"
  - "lookup"
  - "api"
  - "contracts"
  - "pesquisa"
  - "specialized"
  - "scientific"
  - "reference"
  - "reviewed"
---

# Reviewed service contracts

Reviewed 2026-09-30 against official schemas, `parallel-web-tools` 0.9.3 source
and local help, plus unauthenticated OpenRouter model metadata. No paid or
authenticated generation/retrieval requests were submitted during this review.
Mocked tests exercise request formation, response parsing, and packet behavior.

## Parallel Search and Extract through CLI 0.9.3

- Search uses `POST https://api.parallel.ai/v1/search`; Extract uses
  `POST https://api.parallel.ai/v1/extract`. API keys use `x-api-key`; the CLI
  resolves `PARALLEL_API_KEY` before stored login credentials. Never put keys in
  command arguments. Login is device OAuth by default; `--no-browser` suppresses
  launching a local browser. The CLI guide's old `--device` example conflicts
  with the reviewed 0.9.3 source/help.
- V1 Search requires `search_queries`; `objective` adds context. The wrapper
  always supplies both using its positional objective and repeated `-q` flags.
  Modes are `turbo`, `fast`, `basic`, and `advanced`; the wrapper explicitly sets
  one, avoiding the difference between CLI `basic` and raw API `advanced` defaults.
- V1 request limits and filters are nested under `advanced_settings`, including
  `max_results`, `source_policy`, and `excerpt_settings`. CLI flags construct this
  shape. `after_date` filters page publication dates, not database indexing dates.
  No cursor, page, or offset is documented: use distinct bounded queries to
  improve coverage, without claiming exhaustive retrieval.
- Search returns `search_id`, `session_id`, and ranked `results`; result objects
  contain `url`, `excerpts`, and optional `title`/`publish_date`. `usage` and
  `warnings` can be absent/null. CLI adds its own status wrapper; raw V1 has no
  top-level status. The ledger uses application status and preserves warnings.
- Extract accepts up to **20 URLs per request**; the wrapper defaults to batches
  of 10. It uses objective-focused excerpts, not structured bibliographic JSON or
  guaranteed full text. V1 excerpts are always returned; full content is optional.
- Extract returns `extract_id`, `session_id`, `results`, and **`errors`**. Each
  error identifies `url` and `error_type`, with optional HTTP status/content.
  Reconcile success and error records per URL; empty excerpts never count as
  retrieval verification. Sessions are propagated from Search through Extract.
  Errors, warnings, and unresolved URLs remain in the ledger; redirected URLs may
  need manual identity reconciliation.

Sources: [Search schema](https://docs.parallel.ai/api-reference/search/search),
[Extract schema](https://docs.parallel.ai/api-reference/extract/extract),
[Search migration](https://docs.parallel.ai/search/search-migration-guide),
[Extract migration](https://docs.parallel.ai/extract/extract-migration-guide),
[CLI 0.9.3 source](https://github.com/parallel-web/parallel-web-tools/tree/v0.9.3),
[release metadata](https://pypi.org/project/parallel-web-tools/0.9.3/).

## Explicit Research

`parallel-cli research run --text --json -o BASE` creates a Task with
`POST /v1/tasks/runs`, polls `GET /v1/tasks/runs/{run_id}`, and retrieves
`GET /v1/tasks/runs/{run_id}/result`. Auth uses the same CLI credentials. The
payload includes `input`, `processor`, `task_spec.output_schema.type="text"`,
and optional `previous_interaction_id`; it is not a Search session ID.

The raw API result has `run` and `output` objects. CLI 0.9.3 normalizes metadata
to top-level `run_id`, `interaction_id`, `status`, and `output`. Saving a text
result writes `BASE.md` and replaces JSON `output.content` with
`output.content_file`; `--json` prints that same saved shape. The wrapper reads
the known sibling Markdown file, retains `output.basis`, and rejects empty or
unfinished reports. It rejects inputs exceeding 15,000 characters before the CLI
can silently truncate them. Client timeout does not cancel the server run.

Sources: [create Task](https://docs.parallel.ai/api-reference/tasks/create-task-run),
[retrieve result](https://docs.parallel.ai/api-reference/tasks/retrieve-task-run-result),
[interactions](https://docs.parallel.ai/task-api/guides/interactions),
[CLI source](https://github.com/parallel-web/parallel-web-tools/tree/v0.9.3).

## Explicit beta Chat

The current reference documents `POST https://api.parallel.ai/v1beta/chat/completions`
with `x-api-key`. The wrapper sends `model`, `messages`, and `stream=false` and
reads `choices[0].message.content`, optional `basis`, and `usage`. The published
research-model announcement names `speed`, `lite`, `base`, and `core`; the current
schema leaves model as a string and does not enumerate availability. No live model
execution was checked. Basis is retained, not treated as independent validation.

The old unversioned `/chat/completions` URL and Bearer auth appeared in older
SDK examples. The wrapper now follows the versioned current schema. The former
Chat quickstart redirects to Responses; that API uses `/v1/responses`, a different
model and response envelope, and is not implemented by this wrapper.

Sources: [Chat reference](https://docs.parallel.ai/api-reference/chat-api-beta/chat-completions),
[research-model announcement](https://parallel.ai/blog/research-models-chat),
[Responses quickstart](https://docs.parallel.ai/responses-api/responses-quickstart).

## Explicit or authorized fallback Perplexity

The wrapper calls `POST https://openrouter.ai/api/v1/chat/completions` with
`Authorization: Bearer` and model `perplexity/sonar-pro-search`. The public model
catalog and endpoint listing confirmed this model and `web_search_options`
support. Search context is nested as `web_search_options.search_context_size`.
The former top-level `search_mode="academic"` is not part of the documented
OpenRouter contract used here; academic focus comes from the prompt.

Read text from `choices[0].message.content` and citations from
`choices[0].message.annotations[].url_citation` (`url`, `title`, optional
`content` and character offsets). Legacy `search_results`/`citations` fields are
also accepted, deduplicated by URL. Keep raw response data for provenance; a
source link or a model's synthesis still requires verification. Neither key
presence nor an unavailable Parallel CLI authorizes provider switching.

Sources: [request format](https://openrouter.ai/docs/api_reference/overview),
[web search and citations](https://openrouter.ai/docs/guides/features/plugins/web-search),
[model catalog](https://openrouter.ai/api

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

