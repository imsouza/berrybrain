"use client";

import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { PublicShell } from "@/components/public-site/public-pages";

type DocSection = { id: string; title: string; md: string };

const DOC_SECTIONS: DocSection[] = [
  {
    id: "introduction",
    title: "Introduction",
    md: `## Introduction

Welcome to the **BerryBrain** documentation. BerryBrain is a local-first, evidence-first
**second brain**: it turns the notes you already write into a connected knowledge system
with a graph, AI-assisted insights, and a full audit trail of every automated decision.

This guide is step-by-step and covers everything from a first demo click to a production
self-hosted deployment. Use the table of contents on the left to jump to any topic.

> Tip: open the **demo** (no account needed) to see the product in action while you read.`,
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
| **api** | FastAPI backend: auth, notes, jobs, graph, insights, connections. |
| **web** | Next.js app: landing, auth, and the workspace UI. |
| **worker** | Runs the autopilot pipeline (parse → classify → assimilate → embed → connect → expand → insights). |
| **nginx** | Reverse proxy: TLS, static assets, and \`/api\` routing to the API. |

Data flow:

1. You write a note → stored as a file in the **vault**.
2. A file watcher (or **Scan vault**) queues a job.
3. The **worker** processes the job and writes results back to the API/database.
4. The **web** UI reads summaries and lets you confirm or ignore suggestions.

The API should **never** be publicly exposed — only the web entrypoint is.`,
  },
  {
    id: "installation",
    title: "Installation",
    md: `## Installation (self-hosting)

### Prerequisites
- A Linux host with Docker and Docker Compose.
- A domain (for TLS) or a local network address for testing.
- (Optional) SMTP credentials for email verification and 2FA.

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
- \`BERRYBRAIN_DOMAIN\` — your domain.
- \`BERRYBRAIN_ADMIN_EMAIL\` — the account that receives admin access.
- \`SESSION_SECRET\` — a long random string.
- SMTP settings (host, user, password, from) for email flows.

### Step 3 — Start
\`\`\`bash
./deploy.sh up
\`\`\`
This builds and starts every service and creates a self-signed certificate placeholder so
nginx can boot.

### Step 4 — TLS (production)
\`\`\`bash
./deploy.sh ssl      # issue Let's Encrypt (DNS challenge)
./deploy.sh status   # verify services
./deploy.sh logs     # tail logs
\`\`\`

### Step 5 — Reverse proxy
Expose **only** the web entrypoint. Do **not** expose the API port publicly.`,
  },
  {
    id: "first-run",
    title: "First run & onboarding",
    md: `## First run & onboarding

### Create an account
1. Open the app and choose **Create account**.
2. Enter email + password (at least 12 characters).
3. Verify your email with the OTP sent to you.
4. Set up 2FA if prompted.

### AI setup (mandatory until configured)
On first login the **AI setup** modal opens automatically. Choose:

- **Local** — uses Ollama on your machine (no API key).
- **Cloud API** — uses NVIDIA NIM or another OpenAI-compatible provider.

Until you finish this step, the setup reappears on every load (exactly like a normal
non-admin login). This guarantees the system is never silently unconfigured.

### Guided tour
A short tour runs **once** on first use, explaining capture, autopilot, graph, insights, and
account controls. Reopen it anytime from the guide (?) button.`,
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
5. Nothing leaves your machine; no API key is required.

### Cloud API (NVIDIA NIM) — step by step
1. Get an API key from your provider (e.g. NVIDIA NIM).
2. In AI setup, choose **Cloud API**.
3. Enter the **Provider URL** (default NVIDIA NIM).
4. Paste your **API key**.
5. Click **Load models**, then pick the recommended one
   (e.g. \`qwen/qwen3.5-397b-instruct\`).
6. Finish.

### Without AI
BerryBrain still works: deterministic insights and the lexical knowledge graph remain
available. Cloud or local models unlock richer embeddings, connections, and graph insights.`,
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

Follow each step in **Activity** (sidebar) and **Monitor / Jobs**. Use **Scan vault** after
importing files externally.`,
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
    id: "account-security",
    title: "Account & security",
    md: `## Account & security

- **First-party accounts** with secure session cookies.
- **CSRF protection**: sensitive requests require an explicit header token.
- **Email verification** and **2FA** (email OTP) are enforced.
- **Admin boundary**: admin routes require the configured administrator account
  (\`BERRYBRAIN_ADMIN_EMAIL\`).
- **Abuse controls**: rate limits, progressive lockout, OTP limits, and audit events.
- **Sessions**: review active sessions, trusted devices, and logout-all from account settings.

Security controls block behavior, not tool names — they resist high-rate and replayed
requests from any interception tool.`,
  },
  {
    id: "privacy",
    title: "Privacy & your data",
    md: `## Privacy & your data

- **Local-first**: notes stay in your vault unless you enable external providers.
- **Opt-in providers**: cloud AI, email, and external enrichment are visible and traceable.
- **Separation**: account data is separate from note content.
- **Provider trace**: provider, model, purpose, status, and evidence are recorded.
- **Data requests**: access, correction, export, or deletion → contato@optlabs.com.br.

Include your account email and request type; never send passwords, OTP codes, API keys, or
private notes by email.`,
  },
  {
    id: "monitor",
    title: "Activity, Monitor & Jobs",
    md: `## Activity, Monitor & Jobs

- **Monitor / Jobs**: queue, execution, and errors for each autopilot task.
- **Activity**: a readable history of what the system did.
- **Diagnostics**: recover stuck or failed jobs.
- **Health**: worker, Ollama, cloud provider, and graph status.
- **Graph expand**: recompute connections from current notes.

Use these to observe the pipeline and recover from failures without losing data.`,
  },
  {
    id: "settings",
    title: "Settings",
    md: `## Settings

- **Appearance**: theme (light/dark).
- **Language**: interface in pt-BR or en (notes unchanged).
- **Fonts**: UI and editor font families and sizes.
- **AI**: switch between Local (Ollama) and Cloud (API), manage keys and models.
- **Vault**: manage folders (create, rename, delete).

Settings are per-browser and stored locally; your notes remain in the vault.`,
  },
  {
    id: "operations",
    title: "Self-hosting operations",
    md: `## Self-hosting operations

- **Logs**: \`./deploy.sh logs\`.
- **Status**: \`./deploy.sh status\`.
- **Updates**: pull the latest code, then \`./deploy.sh up\` to rebuild.
- **Backups**: copy the vault directory and the database volume.
- **Secrets**: keep \`SESSION_SECRET\` and SMTP credentials outside git.
- **TLS**: renew with \`./deploy.sh ssl\`.

Expose only the web entrypoint; keep the API internal.`,
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

**Login loop / session errors**
Clear cookies, ensure \`SESSION_SECRET\` is stable, and verify the proxy forwards cookies.

**Email/OTP not arriving**
Check SMTP settings in \`.env\` and the API logs.`,
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
          A complete, step-by-step guide — from first note to production self-hosting.
        </p>
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
    q: "Why does AI setup appear on every demo refresh?",
    a: "The demo is a read-only showcase. The setup is shown on every load so visitors always see the configuration step, just like a normal non-admin login. The tour appears only once.",
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
    a: "Yes. Deploy with Docker Compose using `./deploy.sh up` and expose only the web entrypoint.",
  },
  {
    q: "How do I request data access or deletion?",
    a: "Email contato@optlabs.com.br with your account email and request type. Never include passwords, OTP codes, API keys, or private notes.",
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
