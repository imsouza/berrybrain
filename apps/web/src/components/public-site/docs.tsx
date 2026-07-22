"use client";

import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { PublicShell } from "@/components/public-site/public-pages";

type DocSection = { id: string; title: string; md: string };
const GITHUB_URL = "https://github.com/imsouza/berrybrain";

const DOC_SECTIONS: DocSection[] = [
  {
    id: "introduction",
    title: "Introduction",
    md: `## Introduction

Welcome to the **BerryBrain** documentation. BerryBrain is a local-first, evidence-oriented
**second brain**: it turns a real Markdown vault into searchable evidence, a typed knowledge
graph, grounded AI-assisted insights, and an audit trail of cognitive and operational work.

BerryBrain is **free and source-available for non-commercial use**. There is no central
BerryBrain account, SaaS tenant, or paid feature gate. The source code, license, and
installation path live on GitHub.

This guide explains what BerryBrain is, what it is not, how RAG differs from fine-tuning,
the cognitive and software architecture, self-hosting, providers, reliability, security,
quality gates, and daily workflows.`,
  },
  {
    id: "quickstart",
    title: "Quickstart",
    md: `## Quickstart

### Fast local run
\`\`\`bash
git clone https://github.com/imsouza/berrybrain
cd berrybrain
cp .env.example .env
docker compose up -d
\`\`\`

Open:

- Web: \`http://localhost:3000/berrybrain\`
- API health: \`http://localhost:8000/health\`

### Public page behavior
The landing page explains the project, links to GitHub, and provides **Login** for the owner
of that self-hosted instance. Public signup is disabled; an unconfigured deployment directs
the owner to the one-time local setup.

### Production URL
The public landing/app can be served at:

\`\`\`txt
https://optlabs.com.br/berrybrain
\`\`\`

Set the web env values to:

\`\`\`bash
NEXT_PUBLIC_BERRYBRAIN_BASE_PATH=/berrybrain
NEXT_PUBLIC_BERRYBRAIN_ASSET_PREFIX=/berrybrain
NEXT_PUBLIC_BERRYBRAIN_API_URL=/berrybrain
\`\`\`

Expose only the web/reverse-proxy entrypoint. Keep the raw API port private.`,
  },
  {
    id: "source-model",
    title: "Source and license model",
    md: `## Source and license model

BerryBrain is a source-available, self-hosted product. The core is free for personal,
educational, research, and internal non-commercial use; commercial use requires written
permission under the repository license.

- **No hosted account required**: setup creates one local owner account for the instance.
- **No billing system in core**: all features are available in the codebase.
- **Donations are optional**: operators can link PayPal, card, Pix, or another donation page
  outside the core app.
- **Portable knowledge**: Markdown files remain inspectable and the stack is Docker-friendly.
- **GitHub-first distribution**: source, issues, and releases live in the repository.

Repository:

\`\`\`txt
https://github.com/imsouza/berrybrain
\`\`\``,
  },
  {
    id: "what-is",
    title: "What is BerryBrain",
    md: `## What is BerryBrain

BerryBrain is not merely a notes app and not a chatbot. It is a **personal knowledge system**:

- You capture plain Markdown notes (the only source of truth).
- An **autopilot** pipeline parses, classifies, assimilates, embeds, connects, and expands them.
- Notes, concepts, gaps, insights, and sources become a **knowledge graph**.
- AI assistance is **evidence-first**: every output records *who* (provider), *what* (model),
  *how* (prompt version), *status*, and *which notes* supported the claim.

The result is a private cognitive layer you can query and inspect. Model output remains a
candidate until BerryBrain validates evidence and persists provenance; confidence is not a
guarantee of truth.`,
  },
  {
    id: "rag-or-finetuning",
    title: "RAG, GraphRAG, or fine-tuning?",
    md: `## RAG, GraphRAG, or fine-tuning?

BerryBrain is a **hybrid retrieval-augmented knowledge application**. It uses RAG and
graph-assisted retrieval, but it does **not** fine-tune or train a model on your vault.

| Technique | Used? | What happens |
| --- | --- | --- |
| RAG | Yes | Relevant note chunks and attachment evidence are retrieved before generation. |
| Hybrid retrieval | Yes | Lexical, semantic, graph, chunk, and structured evidence can be combined. |
| Graph-assisted RAG | Yes | Typed nodes, edges, neighborhoods, and evidence participate in inference. |
| Fine-tuning | No | Model weights are never changed by BerryBrain. |
| LoRA/training/checkpoints | No | BerryBrain produces no private model or adapter. |

Keeping knowledge outside model weights means a note can be updated, deleted, cited, backed
up, or reprocessed immediately. Fine-tuning would not provide that lifecycle or provenance.

### What Ask does

1. Retrieves real note chunks, graph nodes/edges, and relevant structured state.
2. Routes the bounded request through the configured Local or Cloud provider.
3. Validates whether the answer is supported by evidence.
4. Persists an auditable inference record with provider, model, prompt version, and sources.
5. Creates an insight only when the result is grounded and the user requests it.

Provider failures and job diagnostics cannot become Knowledge Insights. Insufficient evidence
produces an explicit knowledge gap instead of an invented relationship.`,
  },
  {
    id: "concepts",
    title: "Core concepts",
    md: `## Core concepts

### Notes
Plain Markdown files in your vault. They never leave your machine unless you configure an
external provider. Notes are real files, so they survive restarts and are easy to back up.

### Concepts
Ideas, entities, and topics detected from your notes. A concept can later become a permanent
note.

### Knowledge graph
Notes, concepts, gaps, insights, and sources become connected **nodes** and **edges**. The
graph is your working map of how ideas relate.

### Insights
Findings — knowledge gaps, contradictions, study paths, suggested notes — each with a
**confidence score** and the **evidence** behind it.

### Autopilot
The background pipeline that keeps your knowledge current automatically.

### Single local account
BerryBrain is designed as a self-hosted personal system. One local owner account controls
the instance, settings, provider keys, and vault access. It is not a SaaS user model.

### Evidence
The recorded provider, model, prompt version, status, and source notes for every AI-assisted
result. Evidence is what makes BerryBrain accountable rather than a black box.`,
  },
  {
    id: "architecture",
    title: "Architecture",
    md: `## Architecture

BerryBrain is composed of small services:

| Service | Role |
| --- | --- |
| **api** | FastAPI backend: local auth, setup, notes, jobs, graph, insights, connections. |
| **web** | Next.js app: public project pages and self-hosted workspace UI. |
| **worker** | Runs the autopilot pipeline (parse → classify → assimilate → embed → connect → expand → insights). |
| **reverse proxy (operator supplied)** | TLS and the public entrypoint. Caddy, nginx, or a tunnel can be used. |

Data flow:

1. You write a note → stored as a file in the **vault**.
2. A file watcher (or **Scan vault**) queues a job.
3. The **worker** processes the job and writes results back to the API/database.
4. The **web** UI reads summaries and lets you confirm or ignore suggestions.

The API should **never** be publicly exposed directly. Publish the reverse-proxy/web entrypoint
and route API calls through the same origin.`,
  },
  {
    id: "cognitive-architecture",
    title: "Cognitive architecture",
    md: `## Cognitive architecture

BerryBrain separates four concerns instead of asking one model to do everything.

### Knowledge Base

Markdown and extracted attachments become deterministic chunks, embeddings, metadata, and
searchable evidence. SQLite is the built-in store; Qdrant and Chroma are optional external
vector adapters. Retrieval can combine lexical, vector, chunk, and graph signals.

### Knowledge Graph

The graph persists notes, concepts, topics, entities, contexts, sources, attachments, gaps,
insights, review questions, study paths, and clusters. AI-generated relationships require a
reason, evidence, confidence, provider, model, prompt version, origin, status, and timestamps.

### Semantic Data Layer

Structured state such as pending jobs, stale work, graph health, settings, review state, and
provider failures is queried independently from note knowledge. This boundary keeps system
diagnostics in Monitor/Activity instead of presenting them as cognitive discoveries.

### Model Router

The router applies provider preference, remote-content consent, model availability, bounded
timeouts, retry policy, concurrency, cancellation, and circuit state. Every invocation writes
privacy-preserving telemetry without storing prompts, notes, retrieved passages, keys, or
model output.

### Retrieval Orchestrator

Graph questions and cognitive queries decide whether to use the Knowledge Base, Knowledge
Graph, Semantic Data Layer, or a combination. The browser never owns the source evidence;
persisted server records are authoritative.`,
  },
  {
    id: "system-requirements",
    title: "System requirements",
    md: `## System requirements

The values below are deployment baselines, not model-quality benchmarks. Storage grows with
your notes, attachments, extracted text, embeddings, backups, and local model files.

| Profile | CPU | Memory | Free storage | Suitable for |
| --- | ---: | ---: | ---: | --- |
| Minimum, cloud AI | 2 x86-64/ARM64 cores | 4 GB RAM | 10 GB SSD | Small vault and cloud inference. |
| Recommended, cloud AI | 4 cores | 8 GB RAM | 20+ GB SSD | Daily use, attachments, and concurrent services. |
| Recommended, local AI | 6+ cores | 16 GB RAM | 30+ GB SSD | Quantized 7B–8B Ollama models and moderate vaults. |
| Larger local models | 8+ cores and supported GPU | 32+ GB RAM/VRAM as required | 60+ GB SSD | Larger context windows and higher throughput. |

Required software:

- 64-bit Linux host or Linux VM with a recent Docker Engine and Docker Compose v2.
- A modern Chromium, Firefox, or Safari browser.
- HTTPS for public deployments and PWA installation outside \`localhost\`.
- Ollama plus an installed model for Local mode, **or** an OpenAI-compatible provider URL,
  API key, and model for Cloud mode.

The baseline does not include the disk or RAM required by your chosen Ollama model. Check the
model artifact size before downloading it. Keep the API port private and use a same-origin TLS
reverse proxy for public deployments.`,
  },
  {
    id: "installation",
    title: "Installation",
    md: `## Installation (self-hosting)

### Prerequisites
- A Linux host with Docker and Docker Compose.
- A domain (for TLS) or a local network address for testing.
- A strong local owner password for first-run setup.

### Step 1 — Clone
\`\`\`bash
git clone https://github.com/imsouza/berrybrain
cd berrybrain
\`\`\`

### Step 2 — Configure environment
\`\`\`bash
cp .env.example .env
\`\`\`
Edit \`.env\` and set at least:
- \`BERRYBRAIN_SESSION_SECRET\` — long random secret for sessions and password hashing.
- \`BERRYBRAIN_API_TOKEN\` — random bearer token for service-to-service automation.
- \`BERRYBRAIN_ADMIN_EMAIL\` — legacy environment name for the single local owner email.
- \`BERRYBRAIN_OWNER_USERNAME\` — owner login alias; defaults to \`admin\`.
- \`BERRYBRAIN_CORS_ORIGINS\` — the exact public web origins.
- \`BERRYBRAIN_ALLOWED_HOSTS\` — hostnames accepted by the API.
- \`BERRYBRAIN_DONATION_URL\` — optional external donation link.

Generate secrets:

\`\`\`bash
python -c "import secrets; print(secrets.token_hex(32))"
\`\`\`

### Step 3 — Start
\`\`\`bash
docker compose up -d
\`\`\`
This starts the web app, API, and Worker. The Worker is mandatory because it executes the
background cognitive pipeline.

### Step 4 — TLS (production)
\`\`\`bash
docker compose ps
docker compose logs -f api web worker
\`\`\`

### Step 5 — Reverse proxy
Expose **only** the web entrypoint. Do **not** expose the API port publicly.`,
  },
  {
    id: "first-run",
    title: "First run & onboarding",
    md: `## First run & onboarding

### Configure a self-hosted instance
1. Clone the repository from GitHub.
2. Configure \`.env\`.
3. Start the Docker stack.
4. Open \`http://localhost:3000/berrybrain\`, choose **Setup**, and create the local owner.
5. The guided tour opens. You may skip the tour, but not provider configuration.
6. Choose Local or Cloud AI and finish the required provider setup.

The setup endpoint is one-shot. After the configured owner exists, setup returns
\`Instance already configured\`.

The default username alias is \`admin\`, configurable with \`BERRYBRAIN_OWNER_USERNAME\`.
BerryBrain deliberately ships with **no default password**. Setup requires the owner to create
a strong password so an exposed fresh instance cannot be taken over with a published credential.

### AI setup (mandatory until configured)
On first login the **AI setup** modal opens automatically. Choose:

- **Local** — uses Ollama on your machine (no API key).
- **Cloud API** — uses NVIDIA NIM or another OpenAI-compatible provider.

Until you finish this step, the setup reappears on every load. This guarantees the system is
never silently unconfigured.

### Guided tour
A short tour runs **once** on first use, explaining capture, autopilot, graph, insights, and
session controls. **Skip** moves directly to AI setup; it does not dismiss onboarding. The
completion state is stored in the local database, so a clean instance always starts with the
tour. Reopen it anytime from the guide (?) button.`,
  },
  {
    id: "pwa",
    title: "Installable PWA",
    md: `## Install BerryBrain as a PWA

BerryBrain can be installed from a supported browser and opens directly in \`/brain\`.

1. Serve the instance through HTTPS, or open it on \`localhost\`.
2. Sign in and open **BerryBrain**.
3. Use the browser's **Install app** action.

Security behavior:

- API responses, authenticated pages, and note contents are not stored in the Service Worker cache.
- Static assets are cached for reliable loading.
- When the server is unreachable, a neutral offline page is shown instead of stale private content.
- Editing and cognitive processing still require a connection to your self-hosted server.`,
  },
  {
    id: "ai-providers",
    title: "Configuring AI providers",
    md: `## Configuring AI providers

### Local (Ollama) — step by step
1. Install Ollama for your OS.
2. Start it: \`ollama serve\`.
3. Pull a model: \`ollama pull qwen3:14b\`.
4. In BerryBrain AI setup, choose **Local**.
5. Keep the Docker default URL \`http://host.docker.internal:11434\`, or enter an address
   reachable from the API and Worker containers.
6. Enter the installed model name. Nothing leaves your machine; no API key is required.

### Cloud API (NVIDIA NIM) — step by step
1. Get an API key from your provider (e.g. NVIDIA NIM).
2. In AI setup, choose **Cloud API**.
3. Enter the **Provider URL** (default NVIDIA NIM).
4. Paste your **API key**.
5. Click **Load models**, then select a model returned by your provider.
6. Finish.

### Provider setup is required
BerryBrain does not allow onboarding to finish without an explicit Local or Cloud choice.
Local mode requires an installed Ollama model name. Cloud mode requires a provider URL, API
key, and model. This prevents the cognitive pipeline from appearing ready while no inference
provider is available.`,
  },
  {
    id: "pipeline",
    title: "The Autopilot pipeline",
    md: `## The Autopilot pipeline

Whenever you create or edit a note, the pipeline runs:

1. **PARSE_NOTE** — reads the Markdown.
2. **CLASSIFY_NOTE** — detects the note type.
3. **ASSIMILATE_NOTE** — extracts concepts, entities, and topics.
4. **EXTRACT_CONTEXT / TOPICS / ENTITIES** — deeper structure.
5. **GENERATE_EMBEDDING** — similarity vector (if an embeddings provider is set).
6. **FIND_CONNECTIONS / INFER_CONNECTIONS** — relate to other notes.
7. **EXPAND_KNOWLEDGE_GRAPH** — build and enrich the graph.
8. **GENERATE_GRAPH_INSIGHTS** — gaps, contradictions, study paths.
9. **UPDATE_GRAPH_STATS** — refresh counts and health.

Attachments use their own \`PROCESS_ATTACHMENT\` job. Supported paths include PDF/document
text extraction, Tesseract image OCR, and local Faster Whisper audio/video transcription.
Successful extraction becomes searchable chunks and traceable graph evidence.

Follow each step in **Activity** (sidebar) and **Monitor / Jobs**. Use **Scan vault** after
importing files externally.`,
  },
  {
    id: "cognitive-attachments",
    title: "Cognitive attachments",
    md: `## Cognitive attachments

Attachments are knowledge sources, not passive downloads.

- **PDF and documents**: page-aware text extraction for searchable evidence.
- **Images**: local Tesseract OCR with configurable language and timeout.
- **Audio and video**: local Faster Whisper transcription with timestamps and confidence.
- **Knowledge Base**: extracted text is chunked and included in hybrid retrieval.
- **Knowledge Graph**: processed files become attachment nodes linked to their source note.
- **Provenance**: evidence keeps attachment ID, extractor, model, page or timestamp, and status.

Extraction runs in a constrained subprocess with fixed arguments, bounded resources,
\`no_new_privs\`, limited output, and no shell interpolation. File-size limits are configured
separately for image, audio, video, and other attachments in **Settings**.

### OCR languages

The OCR language value is passed directly to Tesseract's \`-l\` option. A code works only
when its matching \`traineddata\` package is installed in the API image. The default image
includes \`eng\` and \`osd\`; changing Settings to \`por\`, \`spa\`, \`deu\`, or another
code does not download that language automatically.

Install the required Debian package, rebuild the API, and verify the result:

\`\`\`dockerfile
RUN apt-get update \\
    && apt-get install -y --no-install-recommends \\
       tesseract-ocr tesseract-ocr-por tesseract-ocr-spa \\
    && rm -rf /var/lib/apt/lists/*
\`\`\`

\`\`\`bash
docker compose build api
docker compose up -d api
docker compose exec api tesseract --list-langs
\`\`\`

Use \`por+eng\` for multilingual documents after both packs are installed. Missing or invalid
language data makes the OCR job fail. This requirement applies to every Tesseract language.`,
  },
  {
    id: "notes",
    title: "Writing & organizing notes",
    md: `## Writing & organizing notes

- **Write fast**: use the Home box, "New note", or **Ctrl+K**.
- **Link notes**: type \`[[Note Name]]\` to create a backlink.
- **Drafts**: saved as real files in the vault \`inbox\` folder.
- **Folders**: organize the vault from the sidebar; rename and delete folders.
- **Language**: notes keep their original language when you switch the UI language.
- **Scan vault**: re-read disk to import external Markdown.

Notes are the source of truth — BerryBrain only adds structure around them.`,
  },
  {
    id: "graph",
    title: "The knowledge graph",
    md: `## The knowledge graph

The graph is where notes, concepts, entities, topics, gaps, and insights become inspectable.

- **Open** it from the top bar.
- **Click a node** to review evidence and actions.
- **Confirm** a suggested node (green) to validate it.
- **Ignore** a node (amber) to hide it from the default Brain View.
- **Reprocess** / **Enrich with AI** a single node.
- **Recalculate connections** from the Home graph card.
- **Open note** jumps to the source note.

Confirm good nodes and ignore weak suggestions to keep the graph clean and meaningful.`,
  },
  {
    id: "insights",
    title: "Insights",
    md: `## Insights

Insights are discoveries: knowledge gaps, central concepts, possible contradictions, study
paths, and suggested notes.

- Each insight shows a **confidence %** based on evidence.
- **Apply** creates a note or review from the insight.
- **Ignore** discards it.
- Deterministic insights work without AI; AI insights add graph-evidence reasoning.

Review confidence before relying on any insight, and create permanent notes from the useful
ones.`,
  },
  {
    id: "connections",
    title: "Connections",
    md: `## Connections

BerryBrain suggests connections automatically. They appear as edges in the graph.

- **Suggested** — proposed by the system, awaiting your decision.
- **Confirm** — becomes an official connection.
- **Ignore** — discarded.

Confirmed connections feed the Brain View and search; ignored ones keep the graph tidy.`,
  },
  {
    id: "commands",
    title: "Command palette & shortcuts",
    md: `## Command palette & shortcuts

Press **Ctrl+K** to open the command palette. From there you can:

- Search notes and commands.
- Create a new note or draft.
- Open the knowledge graph.
- Scan the vault.

Editor shortcuts:

| Shortcut | Action |
| --- | --- |
| **Ctrl+K** | Command palette |
| **Ctrl+S** | Save note |
| **Ctrl+K** (editor) | Commands |

Editor modes: **Edit**, **Preview**, **Split**.`,
  },
  {
    id: "account-recovery",
    title: "Account recovery & deletion",
    md: `## Account recovery & deletion

### Forgot the owner password

If SMTP is configured, choose **Forgot password** on the Login page and use the one-time code
sent to the configured owner email. If SMTP is not configured, reset the password locally on
the host without placing it in shell history:

\`\`\`bash
read -s SEED_ADMIN_PASSWORD
export SEED_ADMIN_PASSWORD
docker compose exec -e SEED_ADMIN_PASSWORD api python /app/scripts/seed_admin.py
unset SEED_ADMIN_PASSWORD
\`\`\`

This revokes the old password by replacing its hash and disables email 2FA unless
\`--enable-2fa\` is explicitly passed. If \`BERRYBRAIN_SESSION_SECRET\` changes, run this
recovery again because that secret is part of password verification.

### Remove only the local owner account

This keeps notes, graph data, and Settings, but revokes access and reopens one-time Setup:

\`\`\`bash
docker compose exec -e DELETE_OWNER_CONFIRM=DELETE_LOCAL_OWNER api \\
  python /app/scripts/delete_owner.py
\`\`\`

Create a new owner through **Setup** afterward. The explicit confirmation protects against
accidental lockout.

### Delete knowledge data but keep Settings

In **Settings → Danger zone**, use **Erase all data and keep settings**. This removes vault
notes and derived knowledge while preserving provider, appearance, and instance settings.

### Factory-reset the whole instance

Stop the stack, back up anything you need, remove the local runtime volumes/directories, and
start again. This removes the owner, settings, provider keys stored in the database, notes,
jobs, graph, and insights:

\`\`\`bash
docker compose down
rm -rf data/* vault/*
mkdir -p data vault
docker compose up -d
\`\`\`

Also remove any provider keys you deliberately placed in \`.env\`. Never commit \`.env\`, data,
vault content, backups, or exported diagnostics.`,
  },
  {
    id: "account-security",
    title: "Account & security",
    md: `## Account & security

- **Single local owner account** with secure session cookies.
- **CSRF protection**: sensitive requests require an explicit header token.
- **Self-hosted setup** creates the owner once; public signup is disabled.
- **Owner boundary**: dangerous actions require the authenticated local owner session.
- **Abuse controls**: rate limits, progressive lockout, and audit events.
- **Sessions**: session cookies can be revoked by the local owner.
- **Danger operations**: backup, maintenance, settings danger, and system reset require authentication.
- **Setup protection**: one-shot owner creation is rate-limited and concurrency-safe.
- **Owner alias**: sign in as \`admin\` by default or configure another alias before startup.

Security controls block behavior, not tool names — they resist high-rate and replayed
requests from any interception tool.`,
  },
  {
    id: "workspace",
    title: "Workspace model",
    md: `## Workspace model

BerryBrain uses a single local workspace per self-hosted owner account.

Current behavior:

- The local vault is the source of truth.
- Settings, provider keys, jobs, graph data, and insight data belong to the local instance.
- Public signup and multi-tenant account management are intentionally not part of the core app.

Planned network automation:

- Discover trusted LAN devices or agents.
- Provision local sources automatically.
- Keep source ingestion auditable.

BerryBrain is not a SaaS user system. It is a self-hosted personal knowledge system.`,
  },
  {
    id: "privacy",
    title: "Privacy & your data",
    md: `## Privacy & your data

- **Local-first**: notes stay in your vault unless you enable external providers.
- **Opt-in providers**: cloud AI and external enrichment are visible and traceable.
- **Separation**: account/session data is separate from note content.
- **Provider trace**: provider, model, purpose, status, and evidence are recorded.
- **Operator control**: self-hosted operators control backup, export, and deletion.

Never paste passwords, API keys, tokens, or private notes into support chats, issue trackers,
or logs.`,
  },
  {
    id: "monitor",
    title: "Activity, Monitor & Jobs",
    md: `## Activity, Monitor & Jobs

- **Monitor / Jobs**: queue, execution, and errors for each autopilot task.
- **Activity**: a readable history of what the system did.
- **Diagnostics**: recover stuck or failed jobs.
- **Health**: Worker, selected provider, graph state, model reliability, and Queue SLO.
- **Graph expand**: recompute connections from current notes.

Inactive providers are configuration choices, not alerts. Use Monitor to observe the active
pipeline and recover actionable failures without losing data.`,
  },
  {
    id: "reliability",
    title: "Reliability & recovery",
    md: `## Reliability & recovery

The Autopilot persists work before execution and treats each note version as immutable input.

- Structured pipeline runs, job dependencies, note version, content hash, and idempotency key.
- Atomic claim, lease, heartbeat, cooperative cancellation, timeout, retry with backoff, circuit breaker, and dead-letter state.
- Superseded pipelines cannot overwrite results from a newer note version.
- AI failures remain visible failures; they do not become empty successful results.
- Canonical graph writes prevent duplicate nodes and edges during retry or reprocessing.
- Suggested graph artifacts can be confirmed, ignored, reprocessed, or reverted.

Technical failures belong in **Monitor** and **Activity**. Knowledge insights remain limited to
claims supported by notes, concepts, connections, or processed attachments.`,
  },
  {
    id: "software-engineering",
    title: "Software engineering",
    md: `## Software engineering

BerryBrain uses evidence-driven engineering. Feature presence is not enough: behavior needs
tests, metrics, failure states, migration behavior, rollback, and user-visible feedback.

### Architectural direction

The project is migrating legacy modules by vertical slice toward Clean Architecture:

1. **Domain** — framework-free policies and invariants.
2. **Application** — use cases, orchestration, ports, and transactions.
3. **Adapters** — SQLAlchemy repositories, providers, filesystem, HTTP, and vector stores.
4. **Delivery** — FastAPI routes, Next.js screens, Worker bootstrap, and Docker.

Graph-inference decisions, model routing, and Queue SLO evaluation already have isolated
domain policies and architecture tests. Remaining legacy boundaries are documented rather
than hidden.

### Reliability patterns

- Durable job outbox and claim-scoped exactly-once Worker inbox.
- Idempotency keys, note content hashes, dependencies, leases, and heartbeats.
- Cooperative cancellation, bounded retry, dead letters, and stale-job recovery.
- Provider timeout, concurrency cap, circuit breaker, and cooldown recovery.
- Canonical graph identity and mutation events to prevent retry duplicates.
- Versioned schemas and fail-closed future-schema detection.
- Checksummed backup, staged migration, integrity check, and coordinated DB/vault rollback.

### Quality gates

- API, Worker, and production-browser suites.
- Branch and critical-module coverage gates.
- Ruff, formatting, progressive MyPy, ESLint, and TypeScript.
- Cognitive benchmarks for retrieval, grounding, provenance, insight usefulness, stale cleanup,
  idempotency, and graph projection performance.
- Automated WCAG A/AA, keyboard, reduced-motion, LCP, CLS, JavaScript transfer, and interaction
  latency budgets.
- Dependency, secret, CodeQL, container, SBOM, and signed-image workflows.

See the repository's requirements traceability, architecture plan, maturity scorecard, and
operations runbook for the current evidence and remaining gates.`,
  },
  {
    id: "settings",
    title: "Settings",
    md: `## Settings

- **Appearance**: theme (light/dark).
- **Language**: interface in pt-BR or en (notes unchanged).
- **Fonts**: UI and editor font families and sizes.
- **AI**: switch between Local (Ollama) and Cloud (API), manage keys and models.
- **Cognitive layer**: retrieval mode, chunks, graph inference, confidence, and external vector stores.
- **Attachments**: size limits, OCR language, transcription executable/model, and extractor timeout.
- **Vault**: manage folders (create, rename, delete).

Settings are persisted by the authenticated local API; display preferences may also use browser
storage. Your notes remain in the vault.`,
  },
  {
    id: "operations",
    title: "Self-hosting operations",
    md: `## Self-hosting operations

- **Logs**: \`docker compose logs -f api web worker\`.
- **Status**: \`docker compose ps\`.
- **Updates**: back up first, deploy a reviewed tag or exact commit, validate health, and keep
  the previous revision available for rollback. Do not run a blind \`git pull\` on stateful data.
- **Backups**: create manifest-backed backups that include checksums and can validate before restore.
- **Restore**: use the authenticated maintenance flow; corrupted or path-traversing archives are rejected.
- **Migrations**: startup applies versioned schema migrations before serving workspace data.
- **Secrets**: keep \`BERRYBRAIN_SESSION_SECRET\`, \`BERRYBRAIN_API_TOKEN\`, and provider keys outside git.
- **TLS**: terminate HTTPS at your reverse proxy.
- **Subpath hosting**: set the Next public base path/asset prefix to \`/berrybrain\`.

Expose only the web entrypoint; keep the API internal.`,
  },
  {
    id: "verification",
    title: "Verification & release status",
    md: `## Verification & release status

Current local verification evidence from 22 July 2026:

- **API**: 276 tests plus 51 subtests pass; branch coverage is 81% and the critical-module gate passes.
- **Worker**: 37 tests pass, including disposable-database integration and cancellation paths.
- **Browser**: 26 production Playwright checks pass, covering auth, onboarding, notes, graph inference, Monitor, accessibility, mobile layout, and performance.
- **Cognitive gate**: retrieval, grounding, provenance, insight quality, diagnostic isolation, stale cleanup, idempotency, and graph projection pass.
- **Scale fixture**: 5,000 graph nodes and 20,000 edges serialize under the 2.5 s p95 and 16 MiB budgets.
- **Static gates**: Ruff, formatting, progressive MyPy, ESLint, TypeScript, and production build pass.
- **Supply chain**: tagged AMD64/ARM64 images include SPDX SBOMs, provenance, and OIDC signatures.

BerryBrain is a functional second brain, not a claimed 100% mature one. Current evidence-based
scores are 86/100 cognitive and 84/100 engineering. Remaining gates include 30-day usefulness
outcomes, manual screen-reader evidence, historical restore fixtures, an external disaster
recovery drill, and further legacy-boundary isolation.`,
  },
  {
    id: "troubleshooting",
    title: "Troubleshooting",
    md: `## Troubleshooting

**AI setup keeps reopening**
Expected until you finish it. Complete the Local or Cloud configuration and click Finish.

**Notes not processing**
Open **Monitor / Jobs**; if jobs are stuck, use **Diagnostics** to recover them. Check the
worker container logs.

**Graph looks empty**
Run **Recalculate connections** from the Home graph card, or **Scan vault** after adding
files.

**Self-hosted session errors**
Clear cookies, ensure \`BERRYBRAIN_SESSION_SECRET\` is stable, and verify the proxy forwards cookies.

**Self-hosted setup says the instance is already configured**
This is expected after the first local owner exists. Use the existing login or the headless
owner seed script for recovery.

**I forgot the owner password and email delivery is not configured**
Run \`/app/scripts/seed_admin.py\` inside the API container as documented in **Account recovery
& deletion**. Do not delete the database merely to reset a password.

**The install-app option is missing**
Use HTTPS or \`localhost\`, verify \`manifest.webmanifest\` and \`sw.js\` are reachable under the
same path prefix, then reload after the Service Worker activates.

**Static assets fail under /berrybrain**
Verify \`NEXT_PUBLIC_BERRYBRAIN_BASE_PATH=/berrybrain\` and
\`NEXT_PUBLIC_BERRYBRAIN_ASSET_PREFIX=/berrybrain\` before building the web app.`,
  },
  {
    id: "glossary",
    title: "Glossary",
    md: `## Glossary

- **Vault** — the folder where your Markdown notes live.
- **Autopilot** — the automatic processing pipeline.
- **Concept** — an extracted idea, entity, or topic.
- **Node** — an item in the knowledge graph (note, concept, insight, gap).
- **Edge** — a relationship between two nodes.
- **Insight** — a finding with confidence and evidence.
- **Evidence** — the recorded provenance of an AI-assisted result.
- **RAG** — retrieval of relevant evidence before a model generates an answer.
- **Graph-assisted RAG** — retrieval that also uses graph nodes, edges, and neighborhoods.
- **Fine-tuning** — changing model weights through training; BerryBrain does not do this.
- **Model Router** — the policy boundary selecting provider/model and recording execution.
- **Queue SLO** — the target for pending age, stale running work, and dead letters.
- **Brain View** — the default graph view of confirmed/suggested nodes.
- **Source-available** — source can be inspected and used under the project license; this is
  not the same as an OSI-approved open-source license.`,
  },
];

function DocsContent() {
  const [active, setActive] = useState(DOC_SECTIONS[0].id);
  const [tocOpen, setTocOpen] = useState(false);

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) setActive(entry.target.id);
        });
      },
      { rootMargin: "-96px 0px -70% 0px", threshold: 0 }
    );
    DOC_SECTIONS.forEach((s) => {
      const el = document.getElementById(s.id);
      if (el) observer.observe(el);
    });
    return () => observer.disconnect();
  }, []);

  return (
    <div className="mx-auto w-full max-w-6xl px-6 py-12">
      <header className="mb-10">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-accent">Documentation</p>
        <h1 className="mt-2 text-3xl font-semibold tracking-tight">BerryBrain Docs</h1>
        <p className="mt-3 max-w-2xl text-sm leading-6 text-muted">
          Product model, RAG and graph architecture, software engineering, security,
          self-hosting, operations, and measured maturity.
        </p>
        <div className="mt-5 flex flex-wrap gap-3">
          <a
            href={GITHUB_URL}
            target="_blank"
            rel="noreferrer"
            className="bb-action inline-flex items-center gap-2 px-4 py-2 text-sm font-semibold"
          >
            <svg viewBox="0 0 24 24" fill="currentColor" className="size-4" aria-hidden="true">
              <path d="M12 .5C5.73.5.5 5.73.5 12c0 5.08 3.29 9.39 7.86 10.91.58.11.79-.25.79-.56v-2c-3.2.7-3.88-1.54-3.88-1.54-.53-1.34-1.29-1.7-1.29-1.7-1.05-.72.08-.71.08-.71 1.16.08 1.77 1.19 1.77 1.19 1.03 1.77 2.7 1.26 3.36.96.1-.75.4-1.26.73-1.55-2.55-.29-5.24-1.28-5.24-5.69 0-1.26.45-2.29 1.19-3.1-.12-.29-.52-1.46.11-3.05 0 0 .97-.31 3.18 1.18a11.1 11.1 0 0 1 5.8 0c2.2-1.49 3.17-1.18 3.17-1.18.63 1.59.23 2.76.11 3.05.74.81 1.19 1.84 1.19 3.1 0 4.42-2.69 5.39-5.25 5.68.41.36.78 1.07.78 2.16v3.2c0 .31.21.68.8.56A11.51 11.51 0 0 0 23.5 12C23.5 5.73 18.27.5 12 .5Z" />
            </svg>
            GitHub
          </a>
          <a href={`${GITHUB_URL}#readme`} target="_blank" rel="noreferrer" className="rounded-md border border-border px-4 py-2 text-sm text-foreground hover:bg-surface">
            README
          </a>
        </div>
      </header>
      <div className="lg:grid lg:grid-cols-[220px_1fr] lg:gap-12">
        <aside className="mb-4 lg:mb-0">
          <button
            className="mb-3 flex w-full items-center justify-between rounded-lg border border-border px-3 py-2 text-sm text-muted hover:text-foreground lg:hidden"
            onClick={() => setTocOpen(!tocOpen)}
            aria-expanded={tocOpen}
          >
            <span>Table of contents</span>
            <svg className={`size-4 shrink-0 transition-transform ${tocOpen ? "rotate-180" : ""}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          <nav className={`lg:sticky lg:top-24 lg:block lg:max-h-[80vh] lg:overflow-y-auto ${tocOpen ? "block" : "hidden"}`}>
            <ul className="space-y-1 border-l border-border text-sm">
              {DOC_SECTIONS.map((s) => (
                <li key={s.id}>
                  <a
                    href={`#${s.id}`}
                    onClick={() => setTocOpen(false)}
                    className={`-ml-px block border-l-2 py-1.5 pl-3 transition ${
                      active === s.id
                        ? "border-accent font-medium text-foreground"
                        : "border-transparent text-muted hover:text-foreground"
                    }`}
                  >
                    {s.title}
                  </a>
                </li>
              ))}
            </ul>
          </nav>
        </aside>
        <div className="prose max-w-none">
          {DOC_SECTIONS.map((s) => (
            <section key={s.id} id={s.id} className="scroll-mt-24">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{s.md}</ReactMarkdown>
            </section>
          ))}
        </div>
      </div>
    </div>
  );
}

export function DocsPage() {
  return (
    <PublicShell>
      <DocsContent />
    </PublicShell>
  );
}

type FaqItem = { q: string; a: string };

const FAQ_ITEMS: FaqItem[] = [
  {
    q: "What is BerryBrain?",
    a: "A local-first, evidence-oriented second brain. It combines a Markdown vault, hybrid retrieval, a persistent knowledge graph, structured system data, and grounded AI-assisted inference while keeping source evidence attached to knowledge claims.",
  },
  {
    q: "Is BerryBrain a RAG application?",
    a: "Yes, but not only RAG. It uses hybrid retrieval over chunks, embeddings, graph neighborhoods, and structured data. The retrieved evidence can ground a model answer, while the graph, jobs, insight lifecycle, provenance, and user controls remain persistent systems outside the model.",
  },
  {
    q: "Does BerryBrain fine-tune a model on my notes?",
    a: "No. BerryBrain never changes model weights and creates no LoRA adapter or checkpoint. Your knowledge stays in files, chunks, embeddings, and graph records so it can be updated, deleted, backed up, and cited immediately.",
  },
  {
    q: "Is my data private?",
    a: "Yes. Notes live in your own vault. External AI, email, and enrichment are opt-in and fully visible in the provider trace.",
  },
  {
    q: "Do I need an AI provider to use it?",
    a: "Yes for the complete cognitive workflow. First-run onboarding requires an explicit Local/Ollama or Cloud provider configuration. Markdown files and deterministic parsing still exist without successful inference, but Ask, enrichment, and model-backed insight generation require a working provider.",
  },
  {
    q: "What is Ollama and do I need it?",
    a: "Ollama runs models locally. It is optional; choose it in the AI setup for fully offline processing. Cloud API is the alternative.",
  },
  {
    q: "How do notes become connected?",
    a: "The autopilot parses, classifies, assimilates, embeds, connects, and expands your notes into a graph. You confirm or ignore each suggested connection.",
  },
  {
    q: "Is there a tour?",
    a: "Yes — a guided tour runs on first use. Reopen it anytime from the guide (?) button.",
  },
  {
    q: "How do I import existing notes?",
    a: "Drop Markdown files into the vault and use **Scan vault** from the command palette.",
  },
  {
    q: "Can I self-host?",
    a: "Yes. Docker Compose starts Web, API, and Worker. The default URL is `/berrybrain`; expose only the HTTPS web/reverse-proxy entrypoint and keep the raw API private.",
  },
  {
    q: "Is BerryBrain open source?",
    a: "BerryBrain is source-available under a non-commercial license, not OSI-approved open source. Personal, educational, research, and internal non-commercial self-hosting are allowed; commercial use requires written permission.",
  },
  {
    q: "How do I request data access or deletion?",
    a: "Self-hosted operators control their own vault, database, backups, and deletion. Never include passwords, API keys, tokens, or private notes in public issues.",
  },
  {
    q: "Which languages are supported?",
    a: "The interface supports pt-BR and en. Note content is never translated.",
  },
  {
    q: "Is there an API?",
    a: "Yes — a REST API powers the web app (auth, notes, jobs, graph, insights, connections). External API access should be restricted to trusted origins.",
  },
];

function FaqContent() {
  const [open, setOpen] = useState<number | null>(0);
  return (
    <div className="mx-auto w-full max-w-3xl px-6 py-12">
      <header className="mb-8">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-accent">Help</p>
        <h1 className="mt-2 text-3xl font-semibold tracking-tight">Frequently asked questions</h1>
      </header>
      <div className="divide-y divide-border/70 border-y border-border/70">
        {FAQ_ITEMS.map((item, i) => {
          const isOpen = open === i;
          return (
            <div key={item.q}>
              <button
                onClick={() => setOpen(isOpen ? null : i)}
                aria-expanded={isOpen}
                className="flex w-full items-center justify-between gap-4 py-4 text-left text-sm font-medium"
              >
                <span>{item.q}</span>
                <svg
                  className={`size-4 shrink-0 text-muted transition-transform ${isOpen ? "rotate-180" : ""}`}
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>
              {isOpen && (
                <div className="prose max-w-none pb-5 text-sm leading-7 text-muted">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{item.a}</ReactMarkdown>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

export function FaqPage() {
  return (
    <PublicShell>
      <FaqContent />
    </PublicShell>
  );
}
