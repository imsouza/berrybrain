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

Welcome to the **BerryBrain** documentation. BerryBrain is a local-first, evidence-first
**second brain**: it turns the notes you already write into a connected knowledge system
with a graph, AI-assisted insights, and a full audit trail of every automated decision.

BerryBrain is **free and source-available for non-commercial use**. There is no central
BerryBrain account, SaaS tenant, or paid feature gate. The source code, license, and
installation path live on GitHub.

This guide covers the project idea, architecture, self-hosting model, AI providers, vault
workflow, and operational notes. Use the table of contents on the left to jump to any topic.`,
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

- Web: \`http://localhost:3000\`
- API health: \`http://localhost:8000/health\`

### Public page behavior
The landing page explains the project, links to GitHub, and provides **Login** for the owner
of that self-hosted instance. Public signup is disabled; an unconfigured deployment directs
the owner to the one-time local setup.

### Production URL
The public landing/app can be served at:

\`\`\`txt
https://your-domain.example/berrybrain
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

BerryBrain is not a notes app and not a chatbot. It is a **structured thinking system**:

- You capture plain Markdown notes (the only source of truth).
- An **autopilot** pipeline parses, classifies, assimilates, embeds, connects, and expands them.
- Notes, concepts, gaps, insights, and sources become a **knowledge graph**.
- AI assistance is **evidence-first**: every output records *who* (provider), *what* (model),
  *how* (prompt version), *status*, and *which notes* supported the claim.

The result is a private cognitive layer you can query, inspect, and trust.`,
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
| **hipporag** | Optional internal sidecar for indexed multi-hop retrieval and reconciliation. |
| **nginx** | Reverse proxy: TLS, static assets, and \`/api\` routing to the API. |

Data flow:

1. You write a note → stored as a file in the **vault**.
2. A file watcher (or **Scan vault**) queues a job.
3. The **worker** processes the job and writes results back to the API/database.
4. The **web** UI reads summaries and lets you confirm or ignore suggestions.

The API should **never** be publicly exposed directly. Publish the reverse-proxy/web entrypoint
and route API calls through the same origin.`,
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
- A strong local owner password, or the local/dev default owner for first-run testing.

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
- \`BERRYBRAIN_ENABLE_DEFAULT_OWNER\` — creates the default owner on local/dev startup when true.
- \`BERRYBRAIN_DEFAULT_OWNER_PASSWORD\` — local/dev default password; never use it for public production.
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
4. Choose **Setup** on the landing page and create the local owner account when prompted.
5. The guided tour opens. You may skip the tour, but not provider configuration.
6. Choose Local or Cloud AI and finish the required provider setup.

The setup endpoint is one-shot. After the configured owner exists, setup returns
\`Instance already configured\`.

The default local username alias is \`admin\`, configurable with
\`BERRYBRAIN_OWNER_USERNAME\`. Local/dev instances can enable the default owner with:

- username: \`admin\`
- password: \`BerryBrain123!\`

This convenience is blocked when \`BERRYBRAIN_ENV=production\`. Change the password before
exposing any instance publicly, or disable \`BERRYBRAIN_ENABLE_DEFAULT_OWNER\` and create the
owner through Setup.

### AI setup (mandatory until configured)
On first login the **AI setup** modal opens automatically. Choose:

- **Local** — uses Ollama on your machine (no API key).
- **Cloud API** — uses NVIDIA NIM or another OpenAI-compatible provider.

Until you finish this step, the setup reappears on every load. This guarantees the system is
never silently unconfigured.

The configuration contract is exclusive: one active mode, **Cloud XOR Local**. Main
generation, embeddings, Judge, and HippoRAG each have an explicit model slot. BerryBrain
validates the complete configuration before AI jobs can run, so legacy mixed settings cannot
silently choose a provider.

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
3. Pull the local model configured for this instance.
4. In BerryBrain AI setup, choose **Local**.
5. Keep the Docker default URL \`http://host.docker.internal:11434\`, or enter an address
   reachable from the API and Worker containers.
6. Enter the installed model name. Nothing leaves your machine; no API key is required.

### Cloud API — step by step
1. Get an API key from an OpenAI-compatible provider such as NVIDIA NIM, OpenAI,
   OpenRouter, Groq, or DeepSeek.
2. In AI setup, choose **Cloud API**.
3. Choose the provider in the dropdown. BerryBrain fills the compatible base URL automatically.
4. Paste your **API key**.
5. Click **Load models**, then select a model returned by your provider.
6. Finish.

If the provider returns models as strings, OpenAI-style \`data[].id\`, or another common
\`id/name/model\` object shape, BerryBrain normalizes the list before rendering the model
selector. Presets store provider base URLs, while the selected provider and model are persisted
in Settings. Custom OpenAI-compatible endpoints remain editable.

### Provider setup is required
BerryBrain does not allow onboarding to finish without an explicit Local or Cloud choice.
Local mode requires an installed Ollama model name. Cloud mode requires a provider URL, API
key, and model. This prevents the cognitive pipeline from appearing ready while no inference
provider is available.`,
  },
  {
    id: "rag-judge",
    title: "RAG Judge",
    md: `## RAG Judge

The Judge is a validation layer for generated knowledge. It is not the same thing as the
model that writes an answer or proposes an edge.

### Modes

| Mode | Uses LLM? | Purpose |
| --- | --- | --- |
| \`deterministic\` | No | Rule-based checks for low-cost validation. |
| \`single_model\` | Yes, one configured model | Evaluates grounding, evidence, confidence, and risk. |
| \`committee\` | Yes, multiple configured judges | High-impact nodes, edges, and insights only. |

### Configuration behavior

- The Judge always resolves the provider/model slot saved in the active AI configuration.
- Local mode lists installed Ollama models; choose the Judge model explicitly.
- Cloud presets reuse the selected provider endpoint and key, but the Judge model is explicit.
- The default \`single_model\` mode makes one evaluation call; it does not silently invoke other LLMs.
- Committee mode requires each judge slot to be configured separately.
- A generator model cannot judge its own high-impact output in committee mode.

### Enforcement gate

Strict enforcement requires calibration evidence:

- at least 100 judge evaluations;
- at least 30 human reviews;
- weighted kappa >= 0.70;
- false acceptance <= 5%;
- false rejection <= 10%.

The current release-candidate validation includes a calibration fixture and report showing
\`weighted_kappa=0.9801\`.`,
  },
  {
    id: "hipporag",
    title: "HippoRAG",
    md: `## HippoRAG

HippoRAG is an optional sidecar for multi-hop retrieval. It helps answer questions that need
connections across separate notes, but it does **not** replace the canonical BerryBrain graph.

### Safety model

- Disabled by default.
- Runs as an optional Docker profile, not in the core API image.
- Stays on the internal Docker network by default.
- Falls back to standard lexical/vector/graph retrieval when disabled or unavailable.
- Suggested facts must remain evidence-backed and Judge-reviewable before promotion.
- Worker jobs call the sidecar for index, delete, reconcile, and rebuild operations.
- Nested note paths are preserved as document IDs and operations are idempotent.

### When it helps

Use HippoRAG for associative and multi-hop questions, such as connecting Docker runtime
behavior, Linux namespaces, shell automation, and security notes across different files.

### Release gate

The current benchmark requires:

- HippoRAG multi-hop recall improvement >= 10 percentage points;
- factual recall regression <= 2 percentage points;
- citation precision >= 0.95;
- faithfulness >= 0.90;
- negative cases rejected.

The current report passes with multi-hop recall gain \`0.25\`.`,
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
importing files externally. A rename-safe job reference follows the stable note ID and content
hash, so queued work continues on the current path instead of failing with a false 404.`,
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
includes \`eng\` and \`osd\`; changing Settings to \`spa\`, \`deu\`, \`fra\`, or another
code does not download that language automatically.

Install the required Debian package, rebuild the API, and verify the result:

\`\`\`dockerfile
RUN apt-get update \\
    && apt-get install -y --no-install-recommends \\
       tesseract-ocr tesseract-ocr-spa tesseract-ocr-deu \\
    && rm -rf /var/lib/apt/lists/*
\`\`\`

\`\`\`bash
docker compose build api
docker compose up -d api
docker compose exec api tesseract --list-langs
\`\`\`

Use \`eng+spa\` for multilingual documents after both packs are installed. Missing or invalid
language data makes the OCR job fail. This requirement applies to every Tesseract language.`,
  },
  {
    id: "notes",
    title: "Writing & organizing notes",
    md: `## Writing & organizing notes

- **Write fast**: use the Home box, "New note", or **Ctrl+K**.
- **Always edit immediately**: New note opens the editor from every application page.
- **Link notes**: type \`[[Note Name]]\` to create a backlink.
- **Drafts**: saved as real files in the vault \`inbox\` folder.
- **Folders and notes**: drag to reorder them in the sidebar; rename, move, and delete there.
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
- **Click a node** to zoom in and open a full page without replacing the vault sidebar or navbar.
- **Drag a node** to pin its position without opening it. Movement is separated from a click.
- **Hover a node** for a nearby summary of its content, ontology type, context cluster,
  calculated confidence, semantic state, provenance, path, and directed relationships.
- **Edit a node** from that page. BerryBrain validates name/type against current evidence,
  invalidates old confidence, and queues Judge, enrichment, graph, cluster, and stats recalculation.
- **Confidence is read-only** and shows its 95% evidence interval, sample size, method, and factors.
- **Confirm** a suggested node (green) to validate it.
- **Pending** artifacts use a neutral beige channel; status is never encoded by topic color alone.
- Node enrichment runs automatically after changes and during agent monitoring.
- **Recalculate connections** from the Home graph card.
- **Open note** jumps to the source note.
- **Ask** starts a grounded question from the selected node and can continue in Flow.

Every node type has exclusive geometry. Context determines cluster color, except note roots stay
Berry red and insights are highlighted rectangles. Labels render once, adapt the bounded node
geometry, wrap to three lines, and truncate after 58 characters. Pending semantic nodes receive
provisional context colors instead of a generic pending color.

The ontology maps internal types and roles to SKOS, PROV-O, schema.org, RDF, OWL, and Dublin Core.
Canonical edges include \`mentions\`, \`references\`, \`derived_from\`, \`supports\`,
\`contradicts\`, \`broader\`, \`narrower\`, \`instance_of\`, \`part_of\`,
\`prerequisite_for\`, \`example_of\`, \`applies_to\`, \`attached_to\`,
\`contextualizes\`, and symmetric relations. Domain, range, and direction are validated.
Generic metadata labels, sentences posing as concepts, and invalid endpoint combinations enter
semantic quarantine outside graph and RAG until reviewed.

The graph loads progressively, applies deltas, computes layout in a worker, and uses canvas
level-of-detail for large datasets. **Back to graph** restores the complete graph state;
**Back to Home** returns to Brain home.

Confirm good nodes and ignore weak suggestions to keep the graph clean and meaningful.`,
  },
  {
    id: "ask-flow-research",
    title: "Ask, Flow & graph research",
    md: `## Ask, Flow & graph research

### Ask and Flow

Ask returns a grounded answer only when BerryBrain can attach evidence. **Continue in Flow**
creates a persistent multi-turn session, preserves evidence IDs in order, isolates concurrent
sessions, and supports cancellation. A grounded Flow answer can be saved directly as an insight.
Flow is useful when a follow-up depends on prior grounded turns; one-shot questions do not need it.
Home Ask and Graph Ask open the dedicated Ask workspace and support browser speech recognition.
Listening renders a live Web Audio waveform. On local HTTP, BerryBrain links to the configured
HTTPS address when the browser blocks microphone access. Permission, device, network, and
no-speech failures remain visible. Provider/model and inference provenance remain visible.

The Ask workspace immediately builds a question queue and topic cloud from live nodes, typed
relationships, clusters, insights, and gaps. AI refreshes that queue in the background. Every AI
question is validated against live node IDs and exact graph labels before it is cached for the
current graph version. Graph changes invalidate the cache. An empty graph produces no suggestions;
provider downtime never replaces available graph evidence with an empty queue.

Graph retrieval understands ontology class, relationship property, direction, aliases, and the
lower bound of calculated confidence. Quarantined artifacts never enter retrieval. HippoRAG is
synchronized after graph expansion with canonical triples that survive sidecar rebuilds.

### Research gaps

**Research gaps** is a graph-wide maintenance command. It plans unresolved gaps, runs as observable
background work, stores external text as untrusted evidence, rejects unsafe result URLs, and
requires explicit confirmation before knowledge promotion. It is useful for missing or uncertain
external facts, but unnecessary when local evidence is sufficient.

Automatic enrichment handles graph artifacts internally. Use Research gaps only when the graph
needs evidence beyond the local vault. Research progress and failures remain visible in Monitor.`,
  },
  {
    id: "graph-performance",
    title: "Graph performance",
    md: `## Graph performance

The release gate exercises both API projection and browser interaction:

- API budget: 5,000 nodes and 20,000 edges, p95 under 5 seconds, payload under 16 MiB,
  peak memory under 512 MiB.
- Browser stress: 10,000 nodes and 40,000 edges with progressive pages, cold/warm checks,
  deterministic extreme-scale layout, canvas LOD, bitmap camera gestures, selected-node
  preservation, and interaction p95 measurement.
- Default pages: public and authenticated route navigation, script transfer, mobile overflow,
  accessibility, LCP, CLS, and interaction candidates.

The API exposes bounded graph pages and \`/api/v1/graph/delta?since_version=\`. When the delta
cannot be applied safely, \`requiresFullRefresh\` tells the client to reload canonical state.`,
  },
  {
    id: "insights",
    title: "Insights",
    md: `## Insights

Insights are discoveries: knowledge gaps, central concepts, possible contradictions, study
paths, and suggested notes.

- Each insight shows calculated confidence and a **95% evidence interval**; no sample means
  confidence is unavailable.
- Suggested insights appear as rectangular graph nodes with description and evidence.
- **Accept insight** confirms the proposal in the graph.
- **Reject insight** removes the proposal from active graph retrieval.
- Deterministic insights work without AI; AI insights add graph-evidence reasoning.
- The active agent monitor queues generation every 24 hours by default. The interval is
  configurable; the monitor itself cannot be disabled.
- Flow answers can be promoted to insights when they retain evidence.

Inspect confidence before relying on an insight, and create permanent notes from useful ones.`,
  },
  {
    id: "connections",
    title: "Connections",
    md: `## Connections

BerryBrain suggests connections automatically. They appear as directed, typed ontology edges.

Knowledge confidence is calculated from distinct evidence/model signals and stored with its
95% Wilson interval, sample size, method, factors, and timestamp. This contract covers concepts,
note connections, graph nodes and edges, insights, cluster assignments, and graph inferences.
An artifact without evidence reports confidence as unavailable; users cannot edit the value.

- **Suggested** — proposed by the system, awaiting your decision.
- **Confirm** — becomes an official connection.
- **Ignore** — discarded.

Confirmed connections feed the Brain View and search; ignored ones keep the graph tidy.
The Legend explains each edge role and distinguishes symmetric relations from arrowed relations.`,
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
- **Health**: worker, active AI mode, Judge, HippoRAG, queue, enrichment, and graph status.
- **Graph expand**: recompute connections from current notes.

Use these to observe the pipeline and recover from failures without losing data.`,
  },
  {
    id: "reliability",
    title: "Reliability & recovery",
    md: `## Reliability & recovery

The Autopilot persists work before execution and treats each note version as immutable input.

- Structured pipeline runs, job dependencies, note version, content hash, and idempotency key.
- Atomic claim, lease, heartbeat, timeout, retry with backoff, circuit breaker, and dead-letter state.
- Superseded pipelines cannot overwrite results from a newer note version.
- AI failures remain visible failures; they do not become empty successful results.
- Enrichment jobs carry the current evidence fingerprint, skip stale or completed duplicates, and
  cool down for 15 minutes after a provider dead letter before automatic monitoring retries them.
- Canonical graph writes prevent duplicate nodes and edges during retry or reprocessing.
- Suggested graph artifacts can be confirmed, ignored, reprocessed, or reverted.

Technical failures belong in **Monitor** and **Activity**. Knowledge insights remain limited to
claims supported by notes, concepts, connections, or processed attachments.`,
  },
  {
    id: "settings",
    title: "Settings",
    md: `## Settings

- **Appearance**: theme (light/dark).
- **Language**: the interface and generated structures use English; source notes remain unchanged.
- **Fonts**: UI and editor font families and sizes.
- **AI**: choose exactly one Local or Cloud mode, then configure main, embedding, Judge, and HippoRAG model slots.
- **Cognitive layer**: retrieval mode, chunks, graph inference, confidence, and external vector stores.
- **Graph**: rendering, clustering, enrichment, semantic color, and online research controls.
- **Monitor**: operational limits, model calls, retries, dead letters, and service health.
- **Attachments**: size limits, OCR language, transcription executable/model, and extractor timeout.
- **Vault**: manage folders (create, rename, delete).

Settings are persisted by the authenticated local API; display preferences may also use browser
storage. Your notes remain in the vault.`,
  },
  {
    id: "operations",
    title: "Self-hosting operations",
    md: `## Self-hosting operations

- **Logs**: \`docker compose logs -f api web worker hipporag\`.
- **Status**: \`docker compose ps\`.
- **HippoRAG profile**: \`docker compose --profile cognitive-advanced up -d\`.
- **Updates**: pull the latest code, then rebuild/restart Docker Compose.
- **Backups**: create manifest-backed backups that include checksums and can validate before restore.
- **Restore**: use the authenticated maintenance flow; corrupted or path-traversing archives are rejected.
- **Migrations**: startup applies versioned schema migrations before serving workspace data.
- **Secrets**: keep \`BERRYBRAIN_SESSION_SECRET\`, \`BERRYBRAIN_API_TOKEN\`, and provider keys outside git.
- **TLS**: terminate HTTPS at your reverse proxy.
- **Subpath hosting**: set the Next public base path/asset prefix to \`/berrybrain\`.

Expose only the web entrypoint; keep the API internal.`,
  },
  {
    id: "evaluation",
    title: "Evaluation & benchmarking",
    md: `## Evaluation & benchmarking

BerryBrain is evaluated through four complementary comparisons:

1. **Internal ablations** isolate lexical, dense, hybrid, graph, generation, Judge, and continuous-agent contributions under shared controls.
2. **External technical baselines** run independent BM25, dense cosine, reciprocal-rank hybrid, and vanilla RAG against the same corpus and qrels.
3. **Historical regression** repeats frozen workloads across revisions and declared hardware profiles.
4. **Task-level studies** evaluate completion, time, evidence coverage, trust calibration, and workload with real participants after ethics and privacy approval.

The S/M/L/XL profiles cover HTTP, worker queue, on-disk graph/database, browser desktop/mobile,
retrieval quality, graph semantics, Judge calibration, reliability, and security. Query-level paired
effects use bootstrap confidence intervals. Each run retains revision and dirty state, environment,
seed, dataset checksum, configuration, raw observations, summary, and artifact checksums.

Controlled synthetic fixtures are engineering regression evidence. They are not BEIR, HotpotQA,
MuSiQue, independent HippoRAG, productivity, or field-validation claims. External runners require
real qrels and embeddings and fail instead of substituting mock outcomes. Participant and private
vault collection requires an approved ethics/LGPD protocol and informed consent.

Maturity V3 reports Levels 0-5 per capability. Missing or stale evidence remains Level 0;
synthetic CI evidence cannot award independent or field-validation levels.`,
  },
  {
    id: "measured-performance",
    title: "Measured performance",
    md: `## Measured performance

The latest S profile measures distributions rather than isolated best runs. HTTP reports request
rate, errors, and p50/p95/p99 latency. Worker evidence reports enqueue and drain rates, end-to-end
queue latency, completion, and duplicate claims. On-disk graph evidence records nodes, edges,
projection latency, payload, and traced memory. Browser evidence records authenticated desktop and
mobile navigation, LCP, CLS, long tasks, transfer bytes, heap, and application errors.

Latest executed profile, generated 12 August 2026 at 19:13 UTC:

| Workload | Throughput | p50 | p95 | p99 | Failures |
| --- | ---: | ---: | ---: | ---: | ---: |
| HTTP, 100 requests, concurrency 10 | 67.98 req/s | 138.02 ms | 248.62 ms | 293.22 ms | 0 |
| Worker queue, 100 jobs | 12.48 jobs/s drain | 5,036.14 ms | 7,693.75 ms | 7,954.86 ms | 0 duplicate claims |
| On-disk graph, 500 nodes and 1,000 edges | - | 175.46 ms | 306.76 ms | - | Gate passed |
| Semantic retrieval, 45 queries | - | 31.50 ms | 69.20 ms | - | 0 unexpected zero results |

| Graph resource | Actual | Budget | Utilization |
| --- | ---: | ---: | ---: |
| Serialized payload | 541,592 B | 16,777,216 B | 3.23% |
| Peak traced memory | 3,181,953 B | 536,870,912 B | 0.59% |

S is a pull-request engineering profile, not a supported capacity claim. M, L, steady, ramp, spike,
soak, stress, constrained mobile, and provider-sidecar profiles must run on pinned hardware before
publishing scalability conclusions. Instrumentation overhead is measured with paired enabled and
disabled samples and reported separately from endpoint latency.`,
  },
  {
    id: "rag-graph-quality",
    title: "RAG & graph quality",
    md: `## RAG & graph quality

Retrieval uses Recall@10, MRR, NDCG@10, negative rejection, stale-evidence rejection, citation
precision, claim faithfulness, and p50/p95/p99 latency. Paired A0-A6 configurations isolate lexical,
dense, hybrid, graph expansion, generation, Judge, and continuous-agent effects while keeping
corpus, qrels, model, context, query order, and cache policy controlled.

The current controlled corpus executed 44 queries per configuration, or 220 query observations:

| Executed configuration | Recall@10 | MRR | NDCG@10 | p95 |
| --- | ---: | ---: | ---: | ---: |
| A0 lexical only | 0.050 | 0.017 | 0.025 | 11.01 ms |
| A1 dense only | 0.500 | 0.500 | 0.500 | 9.70 ms |
| A2 standard hybrid | 0.500 | 0.500 | 0.500 | 18.27 ms |
| A3 graph lexical | 0.500 | 0.250 | 0.315 | 21.99 ms |
| A3 graph hybrid | 1.000 | 0.750 | 0.815 | 30.84 ms |

Graph hybrid improved multi-hop Recall@10 from 0.000 to 1.000, with paired bootstrap 95% CI
\`[1.000, 1.000]\`, while factual Recall@10 remained 1.000. Citation precision and evidence
faithfulness were both 1.000. A4-A6 and G0-G3 remain protocol definitions, not measured results.

Graph evaluation covers canonical node types, ontology domain/range, named directed edges,
duplicates, orphans, evidence provenance, confidence lower bounds, stale deletion, ignored edges,
and path-answer success. Confidence is calculated from evidence and cannot be edited by clients.
An edge or insight without valid current provenance cannot be promoted as knowledge.`,
  },
  {
    id: "evaluation-reliability",
    title: "Reliability evidence",
    md: `## Reliability evidence

Deterministic gates cover job idempotency, lease ownership, retry, dead letter, cancellation, stale
pipeline supersession, graph transaction rollback, malformed model output, unavailable providers,
backup checksums, isolated restore, schema migration, unsafe archives, authorization, CSRF, and
secret handling. Failures remain observations; a benchmark does not rerun only failed cells until
they pass.

Release readiness is capped when data integrity, privacy, authorization, stale-evidence, or backup
gates fail. Long provider, process, network, disk, and soak experiments remain separate scheduled
evidence and must record recovery time and user-visible degradation.`,
  },
  {
    id: "maturity-v3",
    title: "Maturity V3",
    md: `## Maturity V3

- **Level 0**: absent, contradicted, missing, or stale evidence.
- **Level 1**: implementation without verification.
- **Level 2**: current unit, integration, or deterministic regression evidence.
- **Level 3**: representative reproducible benchmark evidence.
- **Level 4**: independent comparison plus fault evidence.
- **Level 5**: approved longitudinal field or human-study evidence.

Every awarded level links to a current artifact and expiry. Synthetic evidence cannot award Levels
4-5. The report publishes minimum and median levels, never a misleading percentage or a “100%
mature” claim. Mandatory safety and integrity failures set readiness to blocked.`,
  },
  {
    id: "evaluation-reproducibility",
    title: "Reproducibility",
    md: `## Reproducibility

Each run retains git revision and dirty state, Docker/image and runtime versions, hardware and
container limits, seed, dataset checksum, configuration, raw JSONL observations, aggregate summary,
and SHA-256 artifact checksums. Result directories are immutable; reruns receive new identifiers.

An independent evaluator verifies source and dataset checksums, confirms that no private production
vault is mounted, executes unchanged thresholds, recomputes aggregates from raw observations, and
records every environmental or protocol deviation. A dirty exploratory run cannot become a
confirmatory release certificate.`,
  },
  {
    id: "research-use",
    title: "Research use",
    md: `## Research use

The candidate thesis theme evaluates ontology-aware graph-augmented retrieval and continuous
knowledge enrichment in a local-first personal knowledge system. The mixed-method design combines
paired technical ablations, external datasets, task-level comparison, and an optional longitudinal
study. Primary hypotheses, smallest effect of interest, exclusions, metrics, and statistical tests
must be preregistered after pilot work and before confirmatory collection.

Participant or private-vault data requires institutional ethics/LGPD approval or exemption,
informed consent, minimization, pseudonymization, retention/deletion rules, and incident handling.
The repository contains the protocol but no fabricated participant, reviewer, or field results.`,
  },
  {
    id: "evaluation-limitations",
    title: "Evaluation limitations",
    md: `## Evaluation limitations

Controlled synthetic fixtures demonstrate production-path behavior and causal regressions; they do
not establish generalization to personal knowledge, public QA datasets, or competing graph-RAG
systems. Public QA differs from evolving private vaults. LLM judges can share model bias. Graph
density is not usefulness. Acceptance rate can reflect fatigue. Cloud latency varies by provider,
region, and time, and one local hardware profile does not define universal capacity.

BEIR, HotpotQA, and MuSiQue payloads are not vendored and remain unexecuted until licenses and
checksums are verified. Independent replication, human annotation, participant studies, and field
evidence remain open external requirements and are reported as missing rather than replaced.`,
  },
  {
    id: "verification",
    title: "Verification & release status",
    md: `## Verification & release status

Latest exploratory S-profile evidence from 12 August 2026:

| Evidence | Executed sample | Result |
| --- | ---: | --- |
| Composed engineering gate | Retrieval, cognition, insight, Judge, graph, HTTP, worker, and faults | Passed, zero failed gates |
| Controlled retrieval | 44 queries x 5 configurations | 220 observations; graph-hybrid Recall@10 1.000 |
| Judge calibration | 100 evaluations; 30 human reviews | Weighted kappa 0.9801; calibrated |
| Fault injection | 3 isolated faults | 3/3 contained; prior state preserved; maximum 9.26 ms |
| HTTP | 100 requests | 100/100 successful; 67.98 req/s; p95 248.62 ms |
| Worker queue | 100 jobs | 100/100 completed; 12.48 jobs/s drain; no duplicate claims |
| On-disk graph | 500 nodes; 1,000 edges | p95 306.76 ms; 541,592 B payload |
| Maturity V3 | 11 capability groups | \`incomplete-evidence\`; minimum 0; median 2 |

Authenticated desktop/mobile browser exploration recorded zero application errors. Five repetitions
showed host-load variance and are not a confirmatory browser performance claim. Public external
datasets, independent comparison, and approved participant/field evidence remain open.

The machine-readable evidence bundle is authoritative. Manually copied values must not be used
after a newer run without updating the linked report.

Local evidence becomes a published release certificate only after protected remote checks,
clean-revision reproduction, tagging, signed registry artifacts, SBOM/provenance publication,
and post-deploy smoke.`,
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
- **Brain View** — the default graph view of confirmed/suggested nodes.`,
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
          Project overview, architecture, self-hosting notes, and links to the source.
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
    a: "A local-first, evidence-first knowledge system. It connects your notes, concepts, graph, and AI-assisted insights while keeping the source attached to every claim.",
  },
  {
    q: "Is my data private?",
    a: "Yes. Notes live in your own vault. External AI, email, and enrichment are opt-in and fully visible in the provider trace.",
  },
  {
    q: "Do I need an AI provider to use it?",
    a: "No. Without AI you still get deterministic insights and the lexical knowledge graph. Cloud or local models unlock richer embeddings, connections, and graph insights.",
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
    a: "Yes. Deploy with Docker Compose and expose only the web/reverse-proxy entrypoint.",
  },
  {
    q: "How do I request data access or deletion?",
    a: "Self-hosted operators control their own vault, database, backups, and deletion. Never include passwords, API keys, tokens, or private notes in public issues.",
  },
  {
    q: "Which languages are supported?",
    a: "The interface and generated brain structures use English. Source-note content is never translated.",
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
