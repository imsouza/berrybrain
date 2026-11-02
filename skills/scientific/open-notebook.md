---
id: sci-open-notebook
name: "Scientific: open-notebook"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Organizes research with the self-hosted Open Notebook alternative to NotebookLM. Supports source ingestion (PDFs, web pages, audio, video, and Office documents), cited document chat, text and vector search, notes, custom transformations, and multi-speaker podcasts. Use when autom"
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "open notebook"
  - "open-notebook"
keywords:
  - "open"
  - "notebook"
  - "organizes"
  - "research"
  - "self"
  - "hosted"
---

# Open Notebook

## Overview

Open Notebook organizes sources, notes, and AI conversations into research notebooks.
It supports several AI providers through Esperanto, full-text and vector search,
custom transformations, and podcast generation with speaker profiles. Application
storage is self-hosted; content sent to configured cloud models is not local-only.

This skill targets the latest published release observed on 2026-09-30,
[v1.14.0](https://github.com/lfnovo/open-notebook/releases/tag/v1.14.0).
Request/response contracts were checked against its official source and current main
commit `3127f14ea9dbb519f0e4ddc64a0742ca644ba6ef`. Bundled helpers have mocked HTTP
regression tests; deployment, ingestion, and paid AI calls were not run against a
live instance. Deployment and remote workflow examples are illustrative.

## Quick Start

### Installation

Use Docker Desktop/Engine with Compose. The upstream docker-compose file configures
SurrealDB v2 and the `lfnovo/open_notebook:v1-latest` application image. It mounts
`./notebook_data` at `/app/data` and `./surreal_data` at `/mydata`.

```bash
curl --fail --location --output docker-compose.yml \
  https://raw.githubusercontent.com/lfnovo/open-notebook/v1.14.0/docker-compose.yml
```

Before starting, edit the downloaded Compose file: replace the literal
`OPEN_NOTEBOOK_ENCRYPTION_KEY=change-me-to-a-secret-string` value, or change it to
`${OPEN_NOTEBOOK_ENCRYPTION_KEY:?Set OPEN_NOTEBOOK_ENCRYPTION_KEY}` and supply that
variable. Exporting a shell variable alone does **not** replace the upstream literal.
Retain the key across restarts; it encrypts provider credentials, not source documents.
Set `OPEN_NOTEBOOK_PASSWORD` in the application's container environment when password
protection is wanted; clients then send `Authorization: Bearer <instance-password>`.
For a reproducible deployment, resolve and record an image digest; `v1-latest` moves.

```bash
docker compose up -d
docker compose logs --tail=100 open_notebook
```

- Web UI: `http://localhost:8502`
- Backend: `http://localhost:5055`; API base: `http://localhost:5055/api`
- Instance contracts: `/docs`, `/redoc`, `/openapi.json`

Source installation is also supported; it needs a separate processing worker.
See [configuration](references/configuration.md) for persistence and provider setup.

### Configure AI providers

In **Manage → Models**, add a configuration/credential, test it, discover models,
and register the particular models needed. Assign chat and embedding defaults;
assign speech models separately for transcription/podcasts. OpenAI, Anthropic,
Google, Ollama, Groq, and Mistral have different modalities. Discover support from
the instance's `/api/models/providers`; do not infer speech support from LLM support.

Credential discovery returns `discovered[]` with `name` and `provider`, often without
a usable `model_type`. Registration requires `models[]` containing `name`, `provider`,
and an explicitly chosen `model_type`. The four types are `language`, `embedding`,
`speech_to_text`, and `text_to_speech`. They are not `llm`, `stt`, or `tts`.
See the [API reference](references/api_reference.md) and
[credential example](references/configuration.md).

### Use the bundled helpers

Resolve this skill's directory and run from its `scripts/` directory, or add that
directory to the Python import path. Install requests in a dedicated environment,
for example `uv run --isolated --with requests python notebook_management.py --help`.
Each CLI only lists records; creation, AI calls, and deletion are explicit functions.
Set `OPEN_NOTEBOOK_URL` to the backend origin (an existing `/api` suffix is also
accepted). Set `OPEN_NOTEBOOK_PASSWORD` only if the instance requires authentication.

```python
from notebook_management import create_notebook
from source_ingestion import add_text_source, wait_for_processing
from chat_interaction import build_context, create_chat_session, send_chat_message

notebook = create_notebook("Methods review", "Compare reported experimental designs")
source = add_text_source(
    notebook["id"], "Pilot study excerpt",
    "Illustrative study: 24 samples were randomized to two treatments.",
    process_async=True, embed=False,
)
wait_for_processing(source["id"])
built = build_context(notebook["id"], source_ids=[source["id"]], note_ids=[])
if not built["context"]["sources"]:
    raise RuntimeError("No source content was included")
session = create_chat_session(notebook["id"], "Methods discussion")
answer = send_chat_message(
    session["id"], "What design was reported? Cite the source and identify gaps.",
    built["context"],
)
ai_messages = [m for m in answer["messages"] if m["type"] == "ai"]
```

## Core Features and Workflow

### Notebooks and notes

Create a notebook with `POST /api/notebooks` and JSON `name`, `description`.
Use `POST /api/notes` with `content`, optional `title`, `notebook_id`, and
`note_type="human"` or `"ai"`. A missing title on an AI note invokes a model.
Notebook deletion removes notes and chat sessions; source deletion is controlled by
`delete_exclusive_sources`. Inspect `/delete-preview` before intentional deletion.

### Source ingestion

`POST /api/sources` takes form fields, including **required** `type`: `link`, `upload`,
or `text`. Supply respectively `url`, multipart `file`, or `content`. Use `notebooks`
as a JSON-encoded list in form data. `async_processing` and `embed` both default to
false. The fields `text` and `process_async` do not implement these options.
Use `/api/sources/json` for JSON bodies; the form endpoint does not accept arbitrary JSON.

Wait for `/api/sources/{id}/status`; a failed job must not flow into analysis as if
it succeeded. Inspect `full_text` after extraction, especially for scanned PDFs,
tables, and transcripts. Vector retrieval additionally needs `embed=true`, a default
embedding model, and completed embeddings (`embedded_chunks > 0`). Source list pages
are limited to 100; use `iter_sources` for a stable collection. It defaults to a
1,000-page cap and raises on repeated IDs, malformed pages, or an exhausted cap.
Discard partial results after an error; raise `max_pages` explicitly if needed.

### Context-aware chat

Call `/api/chat/context` with `notebook_id` and `context_config`, whose `sources` and
`notes` maps associate IDs with `"full content"`, `"insights"` (sources), or
`"not in context"`. An empty config includes all notebook items in short form;
explicit empty maps select nothing. Review returned i

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

