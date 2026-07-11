# BerryBrain

<img src="apps/web/public/berrylogo.png" alt="BerryBrain" width="96" align="right">

**A local-first second brain for Markdown notes, knowledge graphs, and explainable AI-assisted learning.**

BerryBrain turns notes into connected knowledge. It watches a Markdown vault, parses note structure, extracts concepts, expands a knowledge graph, creates explainable connections, and surfaces insights that help the user study, assimilate, and discover gaps.

---

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.12+-3670A0?logo=python)
![Next.js](https://img.shields.io/badge/next.js-15-black?logo=next.js)
![FastAPI](https://img.shields.io/badge/fastapi-0.115-009688?logo=fastapi)
![Docker](https://img.shields.io/badge/docker-ready-2496ED?logo=docker)
![Local-first](https://img.shields.io/badge/local--first-yes-3C8F5A)
![License](https://img.shields.io/badge/license-MIT-green)

---

## Table of Contents

- [What BerryBrain Is](#what-berrybrain-is)
- [Core Capabilities](#core-capabilities)
- [Architecture](#architecture)
- [Cognitive Layer](#cognitive-layer)
- [Knowledge Graph](#knowledge-graph)
- [Autopilot Pipeline](#autopilot-pipeline)
- [Data Model](#data-model)
- [API Surface](#api-surface)
- [Repository Structure](#repository-structure)
- [Getting Started](#getting-started)
- [Configuration](#configuration)
- [Engineering Practices](#engineering-practices)
- [Security and Privacy](#security-and-privacy)
- [Roadmap](#roadmap)
- [Troubleshooting](#troubleshooting)

---

## What BerryBrain Is

BerryBrain is not just a Markdown editor with AI bolted on. The product goal is to behave like a **real second brain**:

- capture notes without friction;
- assimilate concepts from real note content;
- detect relationships between notes, concepts, topics, entities, gaps, and insights;
- maintain a dynamic knowledge graph;
- answer questions using evidence from the user's vault;
- expose what the system did, why it did it, and what evidence supports each conclusion.

The system is designed around one rule:

> Important knowledge artifacts must be explainable, persisted, traceable, and reversible.

---

## Core Capabilities

| Area | Capability |
| --- | --- |
| Markdown Vault | Real `.md` files, wiki links, frontmatter, folder organization, vault scan, file watcher |
| Editor | Editor-first workflow, autosave, preview/split mode, backlinks, attachments |
| Autopilot | Async job queue for parsing, classification, assimilation, embeddings, graph expansion, insights |
| Knowledge Graph | Notes, concepts, topics, entities, contexts, gaps, insights, and explainable edges |
| Cognitive Layer | Knowledge Base + Knowledge Graph + Semantic Data Layer + Model Router |
| AI Providers | NVIDIA NIM/cloud, OpenAI-compatible providers, DeepSeek-compatible providers, Ollama/local |
| Insights | Knowledge gaps, central concepts, recurring ideas, weak concepts, connections, study suggestions |
| Graph Inference | Ask questions about the graph with evidence-backed answers |
| Activity and Monitor | Human-readable activity timeline plus technical job diagnostics |
| Settings | Theme, editor, provider/model configuration, graph/cognitive settings, attachment limits |
| Privacy Direction | Local-first storage, explicit cloud provider configuration, future LGPD/GDPR workflows |

---

## Architecture

BerryBrain is split into three primary applications:

- **Web**: Next.js + React UI.
- **API**: FastAPI service, persistence, routes, graph/cognitive services.
- **Worker**: Python async worker that claims jobs and performs background processing.

```mermaid
flowchart LR
  User[User] --> Web[Next.js Web App]
  Web --> API[FastAPI API]
  API --> DB[(SQLite / Future Postgres)]
  API --> Vault[(Markdown Vault)]
  API --> Jobs[(Jobs Queue)]
  Worker[Python Worker] --> Jobs
  Worker --> API
  Worker --> Providers[AI Providers]
  Providers --> NIM[NVIDIA NIM]
  Providers --> Ollama[Ollama Local]
  Providers --> Other[OpenAI-compatible APIs]
  API --> Graph[Knowledge Graph Services]
  API --> KB[Knowledge Base / Vector Layer]
  API --> SDL[Semantic Data Layer]
```

### Runtime Contract

The frontend never calls AI providers directly. All cognitive operations flow through API services and queued jobs:

```mermaid
sequenceDiagram
  participant U as User
  participant W as Web
  participant A as API
  participant Q as Jobs
  participant WK as Worker
  participant AI as AI Provider
  participant G as Graph/KB

  U->>W: Create or update note
  W->>A: PUT /api/v1/notes/:path
  A->>A: Sync note record
  A->>Q: Enqueue note pipeline jobs
  WK->>Q: Claim next job
  WK->>A: Fetch note/context
  WK->>AI: Optional model call
  WK->>G: Persist metadata, nodes, edges, insights
  WK->>A: Complete job + activity event
  W->>A: GET /api/v1/home/summary
  A-->>W: Current progress, insights, graph summary
```

---

## Cognitive Layer

BerryBrain's long-term architecture is a **Cognitive Layer** made of four cooperating systems.

```mermaid
flowchart TB
  Input[Notes, links, attachments, metadata] --> Orchestrator[Retrieval Orchestrator]
  Orchestrator --> KB[Knowledge Base]
  Orchestrator --> KG[Knowledge Graph]
  Orchestrator --> SDL[Semantic Data Layer]
  Orchestrator --> Router[Model Router]
  Router --> Local[Local Model / Ollama]
  Router --> Cloud[Cloud Provider / NVIDIA NIM]
  KB --> Insight[Insight Engine]
  KG --> Insight
  SDL --> Insight
  KB --> Infer[Graph Inference Engine]
  KG --> Infer
  SDL --> Infer
  Insight --> UI[Home, Insights, Graph, Editor]
  Infer --> UI
```

### Knowledge Base

Purpose: semantic retrieval over unstructured knowledge.

Current direction:

- Markdown note indexing;
- chunking;
- embeddings;
- semantic retrieval;
- future Qdrant/Chroma support.

Future expansion:

- OCR text from images;
- PDF extraction;
- audio/video transcription;
- document parsing;
- attachment evidence.

See [OCR and Attachment Processing Plan](docs/planning/ocr.md).

### Knowledge Graph

Purpose: represent relationships and explain why knowledge is connected.

Graph nodes can represent:

- note;
- concept;
- topic;
- entity;
- context;
- gap;
- insight;
- attachment;
- source/reference;
- future study path/cluster.

Graph edges must have:

- source and target;
- type;
- reason;
- evidence;
- confidence;
- provider/model when generated by AI;
- status (`suggested`, `confirmed`, `ignored`, etc.).

### Semantic Data Layer

Purpose: answer questions about structured system state.

Examples:

- How many jobs are pending?
- Which notes are not assimilated?
- Which graph nodes have no context?
- Which providers are failing?
- Which insights need attention?

This layer prevents system diagnostics from leaking into knowledge insights. Job failures belong in Monitor/Activity, not in graph insights.

### Model Router

Purpose: centralize provider selection and traceability.

The router should record:

- provider;
- model;
- prompt version;
- status;
- duration;
- error;
- generated artifact;
- source evidence.

---

## Knowledge Graph

The graph is the core representation of BerryBrain's second brain.

```mermaid
graph TD
  N1[Note: Docker Essentials] -->|backlink| N2[Note: Linux Shell Scripting]
  N1 -->|contains concept| C1[Concept: containers]
  N2 -->|contains concept| C2[Concept: shell automation]
  C1 -->|related concept| C3[Topic: infrastructure]
  C2 -->|related concept| C3
  I1[Insight: automation connects Docker and shell] -->|cites evidence| N1
  I1 -->|cites evidence| N2
  G1[Gap: missing deployment note] -->|suggested by| I1
```

### Node Types

| Type | Meaning |
| --- | --- |
| `note` | A Markdown file in the vault |
| `concept` | A semantic concept extracted from notes |
| `topico` / `topic` | A topic detected from content or metadata |
| `entidade` / `entity` | A named entity, tool, person, project, place, or technology |
| `contexto` / `context` | A broader context connecting multiple notes |
| `lacuna` / `gap` | A detected missing piece of knowledge |
| `insight` | A knowledge insight with evidence and action |
| `attachment` | Future node for processed files such as PDFs, images, audio, video |

### Edge Types

| Type | Meaning |
| --- | --- |
| `backlink` | A wiki link between notes |
| `shared_concept` | Notes or nodes share a concept |
| `semantic_similarity` | Similarity from embeddings/model inference |
| `insight_suggested` | An insight cites or suggests a relationship |
| `attachment_related` | Future edge from processed attachment to note/concept/insight |
| `prerequisite` | One topic should be understood before another |
| `example_of` | One note/example illustrates a concept |
| `application_of` | A note applies a broader concept |
| `contrast` | Two ideas differ in a meaningful way |
| `duplicate` | Possible redundant notes/content |

### Graph Interaction Rules

- Single click: open graph details panel.
- Double click note node: open the source note.
- Insight nodes can be shown/hidden in Brain View.
- Suggested nodes/connections can be confirmed or ignored.
- AI enrichment must update evidence, context, model/provider, and activity.
- Web validation is only allowed when research/external enrichment is enabled.

---

## Autopilot Pipeline

The note pipeline turns file changes into cognitive artifacts.

```mermaid
stateDiagram-v2
  [*] --> ParseNote
  ParseNote --> ClassifyNote
  ClassifyNote --> AssimilateNote
  AssimilateNote --> ExtractConcepts
  ExtractConcepts --> ExtractEntities
  ExtractEntities --> DetectTopics
  DetectTopics --> ExtractContext
  ExtractContext --> GenerateEmbedding
  GenerateEmbedding --> FindConnections
  FindConnections --> ExpandKnowledgeGraph
  ExpandKnowledgeGraph --> GenerateInferredConnections
  GenerateInferredConnections --> ExpandConceptToNote
  ExpandConceptToNote --> GenerateGraphInsights
  GenerateGraphInsights --> UpdateGraphStats
  UpdateGraphStats --> [*]
```

### Job Design

Jobs are persisted and claimed by the worker. This makes the system resilient to provider failures and API restarts.

| Job Family | Purpose |
| --- | --- |
| Parse/classify | Understand the Markdown note shape |
| Assimilation | Extract knowledge from note content |
| Embedding | Build semantic search vectors |
| Connection finding | Create explainable links between notes |
| Graph expansion | Create/update nodes and edges |
| Insight generation | Produce useful knowledge insights |
| Graph quality | Stats, cleanup, duplicate detection, enrichment |
| Future attachment processing | OCR, PDF parsing, transcription, attachment graph expansion |

---

## Data Model

High-level entity relationship diagram:

```mermaid
erDiagram
  NOTES ||--o{ JOBS : queues
  NOTES ||--o{ GENERATED_METADATA : produces
  NOTES ||--o{ EMBEDDINGS : indexes
  NOTES ||--o{ CONNECTIONS : source
  NOTES ||--o{ CONNECTIONS : target
  NOTES ||--o{ GRAPH_NODES : source
  GRAPH_NODES ||--o{ GRAPH_EDGES : source
  GRAPH_NODES ||--o{ GRAPH_EDGES : target
  GRAPH_NODES ||--o{ INSIGHTS : evidence
  NOTES ||--o{ NOTE_ATTACHMENTS : owns
  JOBS ||--o{ AUTOMATION_LOGS : records

  NOTES {
    int id
    string title
    string path
    string content_hash
    string status
    datetime updated_at
  }

  GRAPH_NODES {
    int id
    string type
    string label
    string status
    float confidence
    string provider
    string model
  }

  GRAPH_EDGES {
    int id
    int source_node_id
    int target_node_id
    string type
    string reason
    float confidence
    string status
  }

  JOBS {
    int id
    string type
    string status
    string payload
    int attempts
  }
```

### Assimilation Metric

Home assimilation is not a simple note status flag. A note is considered assimilated when durable cognitive output exists for the current note version, such as:

- generated metadata;
- embedding;
- connected graph note;
- completed cognitive pipeline job.

This avoids showing `0%` when the graph already contains real knowledge artifacts.

---

## API Surface

The API is versioned under `/api/v1`.

| Endpoint | Purpose |
| --- | --- |
| `GET /api/v1/home/summary` | Home state: status, progress, stats, insights, graph summary |
| `GET /api/v1/notes` | List notes in the vault |
| `POST /api/v1/notes` | Create a note |
| `GET /api/v1/notes/{path}` | Read a note |
| `PUT /api/v1/notes/{path}` | Update a note and queue processing |
| `POST /api/v1/notes/{path}/reprocess` | Re-run note pipeline |
| `GET /api/v1/notes/{path}/attachments` | List note attachments |
| `POST /api/v1/notes/{path}/attachments` | Upload an attachment |
| `GET /api/v1/graph` | Graph nodes, edges, and stats |
| `GET /api/v1/graph/summary` | Lightweight graph summary |
| `POST /api/v1/graph/expand` | Expand/rebuild graph artifacts |
| `POST /api/v1/graph/infer` | Ask the graph with evidence |
| `GET /api/v1/insights` | List knowledge insights |
| `POST /api/v1/insights/from-inference` | Save a graph inference as insight |
| `GET /api/v1/jobs` | List job queue state |
| `GET /api/v1/jobs/pipeline-progress` | Per-note pipeline progress |
| `GET /api/v1/activity` | Human activity timeline |
| `GET /api/v1/settings` | Read settings |
| `PUT /api/v1/settings/{key}` | Update a setting |
| `GET /health` | API health |

---

## Repository Structure

```text
berrybrain/
  apps/
    api/
      src/berrybrain_api/        FastAPI app, routers, models, graph/cognitive services
      tests/                     API and service tests
    web/
      src/                       Next.js app, components, contexts, UI
      public/                    Runtime public assets
    worker/
      src/berrybrain_worker/     Async worker and provider execution
      tests/                     Worker integration tests
  docs/
    planning/                    Planning documents and future work specs
      assets/                    Planning images and screenshots
  prompts/                       Versioned AI prompts
  vault/                         Local Markdown vault
  docker-compose.yml             Local orchestration
```

---

## Getting Started

### Prerequisites

- Docker + Docker Compose
- Optional: NVIDIA NIM/OpenAI-compatible API key
- Optional: Ollama for local models

### Run Locally

```bash
git clone https://github.com/imsouza/berrybrain.git
cd berrybrain
cp .env.example .env
docker compose up -d
```

| Service | URL |
| --- | --- |
| Web | `http://localhost:3000` |
| API | `http://localhost:8000` |
| Health | `http://localhost:8000/health` |

### Common Commands

```bash
# Start services
docker compose up -d

# Stop services
docker compose down

# View API logs
docker logs berrybrain-api-1 --tail 120

# View worker logs
docker logs berrybrain-worker-1 --tail 120

# Run API tests locally
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=apps/api/src python -m unittest discover apps/api/tests

# Frontend typecheck
npm --prefix apps/web run typecheck
```

---

## Configuration

Configuration lives in `.env`, Settings UI, and persisted settings.

### AI Providers

| Provider | Use |
| --- | --- |
| NVIDIA NIM | Cloud reasoning, graph inference, high-quality insights |
| Ollama | Local-first inference where available |
| OpenAI-compatible API | Alternative cloud model route |
| DeepSeek-compatible API | Reasoning and analysis route |

Recommended current cloud model:

```text
qwen/qwen3.5-397b-a17b
```

### Attachment Limits

The editor supports attaching files to notes, with limits configured in Settings:

- image MB limit;
- video MB limit;
- audio MB limit;
- other MB limit.

Current state: attachments are stored and linked to notes. Future state: attachments become cognitive sources through OCR/transcription. See [OCR Roadmap](#ocr-and-attachment-roadmap).

---

## Engineering Practices

### Design Principles

- **Local-first**: user knowledge lives in local files and local database by default.
- **Explainable**: graph edges and insights need reasons/evidence.
- **Asynchronous**: expensive work is queued and processed by the worker.
- **Traceable**: AI-generated artifacts record provider/model/prompt version where possible.
- **Reversible**: suggested nodes/connections can be confirmed or ignored.
- **Human UI, technical monitor**: knowledge insights stay human; job diagnostics stay in Monitor/Activity.

### Quality Gates

Before merging significant changes:

- API unit/integration tests pass.
- Worker integration tests pass when worker behavior changes.
- Frontend typecheck/build pass when dependencies are installed.
- No hardcoded secrets.
- No raw JSON or internal job names in primary knowledge UI.
- No flashcard surface; study suggestions should be insight/review oriented, not legacy flashcard UI.

### Error Handling

Provider failures should:

- fail jobs with clear reason;
- update Monitor/Activity;
- not create fake insights;
- not silently corrupt graph state;
- allow retry/reprocess.

---

## Security and Privacy

Current BerryBrain is primarily a local-first app. The security roadmap turns it into a public SaaS-ready app with account isolation, login, 2FA, admin, and legal pages.

### Current Safety Expectations

- Keep API keys out of git.
- Do not embed GitHub tokens in remote URLs.
- Treat any token pasted into chat/logs as compromised.
- Keep `.env` local.
- Prefer local providers when privacy is required.
- Use cloud providers only when explicitly configured.

### Planned Security Program

The formal security/auth/admin plan is tracked in [Security, Auth, Admin, and Public Site Plan](docs/planning/sec.md).

Planned work includes:

- first-party signup/login;
- email verification;
- email 2FA through `contato@optlabs.com.br`;
- TOTP support;
- password reset;
- rate limiting;
- CSRF;
- CORS hardening;
- security headers;
- admin panel restricted to the configured administrator account;
- user/account management;
- LGPD/GDPR pages and data export/delete workflows.

---

## Roadmap

### Version Direction

| Version | Status | Focus |
| --- | --- | --- |
| `1.0.x` | Current | Local vault, editor, jobs, graph, insights, activity, settings |
| `1.1.x` | In progress/planned | Cognitive quality, graph action cleanup, stronger inference, better Home observability |
| `1.2.x` | Planned | Attachment OCR/transcription and attachment graph nodes |
| `1.3.x` | Planned | Public SaaS auth/security/admin foundation |
| `2.0.x` | Future | Multi-user collaboration, optional Postgres/Neo4j, advanced sync |

### OCR and Attachment Roadmap

Tracked in [docs/planning/ocr.md](docs/planning/ocr.md).

Planned capabilities:

- `PROCESS_ATTACHMENT` job;
- PDF text extraction;
- OCR for images/scanned PDFs;
- audio transcription;
- video audio extraction/transcription;
- attachment extraction records;
- attachment chunks in Knowledge Base;
- `attachment` graph nodes;
- attachment-backed insights and graph answers.

### Security and SaaS Roadmap

Tracked in [docs/planning/sec.md](docs/planning/sec.md).

Planned capabilities:

- public marketing site;
- login/signup;
- 2FA;
- password reset;
- admin panel;
- administrator account controls;
- rate limiting and abuse protection;
- privacy, security, LGPD/GDPR pages.

---

## Troubleshooting

### API is unhealthy

```bash
docker logs berrybrain-api-1 --tail 120
curl http://localhost:8000/health
```

### Worker is not processing

Check:

- worker container is running;
- jobs are pending;
- provider/model settings are valid;
- API is reachable from worker;
- provider key is configured if using cloud.

```bash
docker ps | grep berrybrain
curl http://localhost:8000/api/v1/jobs?limit=10
docker logs berrybrain-worker-1 --tail 120
```

### Graph looks empty

Check:

- notes exist in the vault;
- graph expansion jobs completed;
- filters are not hiding node types;
- insight nodes are not hidden if you expect to see insight nodes;
- ignored nodes are filtered by default.

```bash
curl http://localhost:8000/api/v1/graph
curl http://localhost:8000/api/v1/graph/summary
```

### Home stats look wrong

The Home uses durable cognitive signals, not only raw note status. If assimilation looks stale:

- reprocess the note;
- check job failures in Monitor;
- verify graph nodes/edges exist;
- inspect `/api/v1/home/summary`.

### Frontend typecheck fails

Ensure dependencies are installed:

```bash
npm --prefix apps/web install
npm --prefix apps/web run typecheck
```

---

## Documentation Index

| Document | Purpose |
| --- | --- |
| [OCR and Attachment Processing Plan](docs/planning/ocr.md) | Future multimodal attachment processing |
| [Security, Auth, Admin, and Public Site Plan](docs/planning/sec.md) | Future SaaS security/auth/admin work |
| [Graph Planning](docs/planning/planing-grafos.md) | Graph maturity and improvement planning |
| [Second Brain Plan](docs/planning/planing-100-segundo-cerebro.md) | 100% second brain maturation plan |
| [Maturation Plan](docs/planning/maturacao.md) | Broader system maturity work |

---

## License

MIT © BerryBrain
