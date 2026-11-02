---
id: sciref-autoskill-api-contracts
name: "Scientific Ref: Autoskill API contract review"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (autoskill): Autoskill API contract review"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "autoskill api contracts"
  - "autoskill api contract review"
keywords:
  - "autoskill"
  - "api"
  - "contracts"
  - "specialized"
  - "scientific"
  - "reference"
  - "contract"
---

# Autoskill API contract review

Reviewed 2026-09-30. These adapters consume a user's already configured services.
No Screenpipe history was read during maintenance. Tests use invented events,
mock transports, and an ephemeral loopback HTTP fixture. Provider docs and
upstream source checks are not authenticated production verification.

## Screenpipe

Source snapshot: [screenpipe 1e77db8](https://github.com/screenpipe/screenpipe/tree/1e77db8243b6f774d5ba816ca7b2c4e909e24eba), specifically
[search](https://github.com/screenpipe/screenpipe/blob/1e77db8243b6f774d5ba816ca7b2c4e909e24eba/crates/screenpipe-engine/src/routes/search.rs),
[auth middleware](https://github.com/screenpipe/screenpipe/blob/1e77db8243b6f774d5ba816ca7b2c4e909e24eba/crates/screenpipe-engine/src/server.rs), and
[CLI arguments](https://github.com/screenpipe/screenpipe/blob/1e77db8243b6f774d5ba816ca7b2c4e909e24eba/crates/screenpipe-engine/src/cli/mod.rs).
The generated [search reference](https://docs.screenpipe.com/api-reference/search/search-screen-and-audio-content)
is useful but lags source for newer query options. No daemon release was installed,
started, built, or queried in this review.

- `GET /search`: `start_time`, `end_time`, `limit`, `offset`; JSON `data[]` with
  tagged `{type, content}` records and `pagination.{limit,offset,total}`.
  Autoskill requests `content_type=all`; advances by the raw row count, including
  skipped rows, until the total is reached. A fixed historical end time reduces
  drift, but limit/offset pagination is not an atomic snapshot; capture, backfill,
  or deletions can still change a running query. Narrow and rerun inconsistent windows.
- Explicit `include_cloud=false`, `include_frames=false`, `filter_pii=false` keep
  this query from requesting cloud results, images, or remote PII processing.
  Source describes `filter_pii` as enclave-backed, so do not enable it to achieve
  a supposedly local redaction pass. Already synced records present in the local
  database may still be searchable; configure Screenpipe itself separately.
- OCR/UI records use `timestamp`, `app_name`, `window_name`, `text`; input rows
  use `window_title`/`text_content`; audio can use `transcription` and has no app.
  Null optional strings normalize to empty strings. Memory records have creation
  times rather than activity timestamps; they and other non-timeline variants
  are skipped with a warning, not treated as screen sessions.
- Auth-enabled `/search` requires `Authorization: Bearer <local API token>`,
  including loopback. CLI comments about an unconditional localhost exemption
  are stale relative to actual middleware. `screenpipe auth token` resolves the
  local API key, not the separate cloud-session JWT. Some older/custom daemons
  can disable authentication; the client can omit its token in that case.
- `GET /health` is public. `doctor` checks reachability only and never probes
  `/search`; it does not prove credentials, capture permissions, or event flow.
- Capture exclusions use repeated `--ignored-windows` substring patterns,
  optionally `App::Title`. The bundled YAML is a checklist, not a daemon config.
  Do not claim that the prior invented `ignored_apps`/`content_types` keys or
  wildcard-wrapped titles protect captured data.

## LM Studio

[Chat Completions](https://lmstudio.ai/docs/developer/openai-compat/chat-completions),
[model list](https://lmstudio.ai/docs/developer/openai-compat/models),
[authentication](https://lmstudio.ai/docs/developer/core/authentication),
[model loading](https://lmstudio.ai/docs/cli/local-models/load).

- Base `http://localhost:1234/v1`; `POST /chat/completions` appends to that base
  (actual path `/v1/chat/completions`). Body includes the exact server model ID,
  one user message, and `stream=false`; read `choices[0].message.content`.
  Truncated, tool-call, non-text, or missing/null `finish_reason` responses fail
  instead of becoming drafts.
- LM Studio 0.4.0+ can require `Authorization: Bearer <API token>`.
  Set `LM_API_TOKEN` for both `/models` preflight and chat calls.
- `GET /v1/models` returns `data[].id`. With JIT loading, listed models need not
  be loaded. `doctor` verifies visibility of the selected ID, not generation,
  available memory, context capacity, or completion quality.
- `lms load` and `lms server start` are separate actions. The `autoskill-local`
  identifier is a user-assigned alias, not a claim that a model was installed.
  Choosing another model or a smaller context is a user setup decision.

## Anthropic and Microsoft Foundry

[Messages](https://platform.claude.com/docs/en/api/messages/create),
[model lifecycle](https://platform.claude.com/docs/en/about-claude/model-deprecations),
[Foundry API](https://learn.microsoft.com/en-us/azure/foundry/foundry-models/how-to/use-foundry-models-claude).

- Anthropic: `POST https://api.anthropic.com/v1/messages`, `x-api-key`,
  `anthropic-version: 2023-06-01`, JSON `model`, `max_tokens=4096`, `messages`.
  Opus 4.7 remains an active model in the reviewed lifecycle table; this review
  does not silently migrate the user's configured model.
- Responses contain typed `content` blocks, potentially including thinking.
  Collect only `type=text` blocks, preserving their order. Reject non-final stop
  reasons (including `max_tokens`, `tool_use`, and `pause_turn`), missing/null
  `stop_reason`, and empty text. Non-streaming replies require a final stop reason.
  A normal stop is still not proof that generated SKILL.md satisfies the spec.
- Foundry API-key mode uses base
  `https://<resource>.services.ai.azure.com/anthropic`, appending `/v1/messages`;
  same `x-api-key` and version header. `model` means deployment name. Generic
  gateways must implement this contract. No OpenAI-style endpoint is implied.
  Entra bearer acquisition is not implemented; Entra-only models are unsupported
  by this adapter. Cloud `doctor` checks configuration/key presence only.
- Requests are synchronous, single-response calls, so there is no completion
  pagination. HTTP failures propagate without automatic paid retries. No paid
  requests or real credentials were used to verify these adapters.

## Local embeddings and TLS

[SentenceTransformer API](https://sbert.net/docs/package_reference/sentence_transformer/model.html)
was checked against sentence-transformers 6.1.0 release metadata. Construction
accepts `local_files_only`; `encode(str)` returns an embedding usable by the
existing cosine ranking. The
[all-MiniLM-L6-v2 mod

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

