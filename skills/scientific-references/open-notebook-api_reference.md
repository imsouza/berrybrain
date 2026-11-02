---
id: sciref-open-notebook-api-reference
name: "Scientific Ref: Open Notebook API Reference"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (open-notebook): Open Notebook API Reference"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "open notebook api reference"
keywords:
  - "open"
  - "notebook"
  - "api"
  - "reference"
  - "specialized"
  - "scientific"
---

# Open Notebook API Reference

Reviewed 2026-09-30 against **v1.14.0** and main commit
`3127f14ea9dbb519f0e4ddc64a0742ca644ba6ef`. Routes below are from the official
[router source](https://github.com/lfnovo/open-notebook/tree/v1.14.0/api/routers),
[request/response models](https://github.com/lfnovo/open-notebook/blob/v1.14.0/api/models.py),
and [podcast service](https://github.com/lfnovo/open-notebook/blob/v1.14.0/api/podcast_service.py).
Source verification and local mocked tests are not authenticated end-to-end tests.
The installed instance's `/openapi.json` is authoritative for its version.

## Transport and authentication

Base: `http://localhost:5055/api`. Tables use full `/api` paths. Interactive docs
are `/docs` and `/redoc` on the backend origin, not below `/api`.
If `OPEN_NOTEBOOK_PASSWORD` is set on the server, send
`Authorization: Bearer <instance-password>` on every protected request, including
downloads. Otherwise authentication is disabled. The encryption key is for server
credential storage; it is neither a bearer token nor a client requirement.

The [middleware configuration](https://github.com/lfnovo/open-notebook/blob/v1.14.0/api/main.py)
excludes `/`, `/health`, `/docs`, `/openapi.json`, `/redoc`, `/api/auth/status`, and
`/api/config`; CORS `OPTIONS` is also exempt. There is no OAuth token exchange in
this password mechanism.

Use finite HTTP timeouts, check status before parsing, preserve record IDs returned
by the server (`notebook:...`, `source:...`, `model:...`), and URL-encode path segments.
Mutating requests have no documented idempotency-key contract; do not blindly retry
a timed-out creation or generation request. Check for an existing record/job first.
Most responses are JSON with success status 200; credential creation is 201.

## Notebooks

| Method and path | Inputs and response |
| --- | --- |
| `GET /api/notebooks` | Optional `archived` boolean; `order_by` defaults to `updated desc`, accepts `name`, `created`, `updated` with optional `asc`/`desc`. Returns an array; no limit/offset. |
| `POST /api/notebooks` | JSON required `name`, optional `description` default `""`; returns notebook. |
| `GET /api/notebooks/{notebook_id}` | Returns notebook; also records its last-viewed timestamp. |
| `PUT /api/notebooks/{notebook_id}` | JSON optional `name`, `description`, `archived`; returns notebook. |
| `GET /api/notebooks/{notebook_id}/delete-preview` | Returns `notebook_id`, `notebook_name`, `note_count`, `exclusive_source_count`, `shared_source_count`. |
| `DELETE /api/notebooks/{notebook_id}` | Query `delete_exclusive_sources=false`. Always removes associated notes/chat sessions, unlinks shared sources, optionally deletes exclusive sources. Returns `message`, `deleted_notes`, `deleted_sources`, `unlinked_sources`, `deleted_chat_sessions`. |
| `POST /api/notebooks/{notebook_id}/sources/{source_id}` | No body; links source and returns `message`. Verify membership before repeated calls; do not depend on duplicate-link prevention. |
| `DELETE /api/notebooks/{notebook_id}/sources/{source_id}` | No body; removes association, returns `message`. Does not delete the source. |

Notebook objects have `id`, `name`, `description`, `archived`, `created`, `updated`,
`source_count`, and `note_count`. There is no `updated_at` sort field or
`delete_sources` query parameter. The source-link handler's existing-reference
lookup uses the reverse edge direction from its insertion at this reviewed version;
its advertised idempotence is therefore not treated as a reliable contract here.

## Sources

| Method and path | Inputs and response |
| --- | --- |
| `GET /api/sources` | Optional `notebook_id`; `limit=50` (1–100), `offset=0` (nonnegative), `sort_by=updated`, `sort_order=desc`. Allowed sorts: `type`, `title`, `created`, `updated`, `insights_count`, `embedded`. Array of summaries, no total/cursor. |
| `POST /api/sources` | Form fields below; multipart when uploading bytes. Returns source. |
| `POST /api/sources/json` | JSON `SourceCreate` with equivalent native booleans/lists; legacy supported JSON route. Server `file_path` is allowed only within its uploads directory; local client paths do not upload files. |
| `GET /api/sources/{source_id}` | Full source including `full_text`, notebook associations and processing fields; records a view. |
| `PUT /api/sources/{source_id}` | JSON optional `title`, `topics` (list of strings, plural); returns source. |
| `DELETE /api/sources/{source_id}` | Deletes source; returns `message`. |
| `GET /api/sources/{source_id}/status` | Returns nullable `status`, `message`, nullable `processing_info`, nullable `command_id`. |
| `GET /api/sources/{source_id}/download` | Binary original uploaded file; 404 if missing, 403 if outside allowed storage. |
| `HEAD /api/sources/{source_id}/download` | 200 without body if file is available; same access/existence checks. |
| `POST /api/sources/{source_id}/retry` | No body; returns newly queued source with `command_id`. Requires notebook association and reusable content. Retry requests embeddings regardless of original `embed`. |
| `GET /api/sources/{source_id}/insights` | Array with `id`, `source_id`, `insight_type`, `content`, nullable `created`/`updated`. |

Form contract:

| Field | Meaning |
| --- | --- |
| `type` | Required: `link`, `upload`, or `text`. |
| `url` | Required for `link`; server fetches it and rejects disallowed destinations. |
| `file` | Multipart bytes for `upload`. |
| `content` | Required for `text`; `text` is not this field. |
| `title` | Optional source title. |
| `notebooks` | JSON-encoded list of notebook IDs, max 50. |
| `notebook_id` | Deprecated single-notebook alternative; do not combine with `notebooks`. |
| `transformations` | JSON-encoded list of transformation IDs, max 50; default `[]`. |
| `embed` | String boolean, default `false`; explicitly enable for vector retrieval. |
| `delete_source` | String boolean, default `false`; deletes original uploaded file after processing when enabled. |
| `async_processing` | String boolean, default `false`; `process_async` is ignored. |

Source objects include `id`, nullable `title`, `topics`, `asset` (`file_path`, `url`),
`full_text`, `embedded`, `embedded_chunks`, nullable `file_available`, `created`,
`updated`, nullable `command_id`, `status`, `processing_info`, and `notebooks`.
List summaries omit `full_text`/`notebooks` and include `insights_count`.
Paginate until a short/empty page, using fixed sort order; offset pages can shift

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

