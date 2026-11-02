---
id: sci-autoskill
name: "Scientific: autoskill"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Analyzes user-requested Screenpipe history windows to detect repeated research workflows, match existing scientific skills, and stage new skill drafts or composition recipes for review. Requires a reachable Screenpipe HTTP API, normally on localhost:3030. Detection and embedding "
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "autoskill"
keywords:
  - "autoskill"
  - "analyzes"
  - "user"
  - "requested"
  - "screenpipe"
  - "history"
  - "windows"
---

# autoskill

> **Requires a running [screenpipe](https://github.com/screenpipe/screenpipe) daemon.** This skill has no alternate data source — it reads exclusively from the local screenpipe HTTP API (default `http://localhost:3030`). If the daemon isn't running, `run()` raises `ScreenpipeUnreachable` with install instructions.

> **Network access & environment variables.** This skill makes authenticated HTTP requests to (a) the user's local screenpipe daemon on loopback, and (b) the user-configured LLM backend — one of `http://localhost:1234/v1` (LM Studio, default), `https://api.anthropic.com` (opt-in Claude), or a user-supplied BYOK Foundry gateway. The adapters read `SCREENPIPE_TOKEN`, `LM_API_TOKEN`, `ANTHROPIC_API_KEY`, and `FOUNDRY_API_KEY` for the corresponding configured service. HTTPX also honors its standard proxy and CA environment settings; sentence-transformers uses Hugging Face cache/download settings. Opt-in cloud backends receive redacted cluster summaries and matched skill descriptions. Embedding-model installation may also download public model files; local inference does not imply zero network access.

## Overview

Turn the user's own workflow history — captured passively by the local [screenpipe](https://github.com/screenpipe/screenpipe) daemon — into new skills. This skill is on-demand: the user invokes it with a time window, it queries screenpipe's local HTTP API, clusters repeated workflow patterns, compares each pattern against the existing skills in this repo, and produces a staged folder of proposals the user can review, edit, and promote.

## When to Use This Skill

Invoke this skill when the user asks to:
- "Analyze my last 4 hours / day / week and propose new skills."
- "Look at what I've been doing and tell me what's not covered yet."
- "Draft a skill from my recent workflow."
- "Find composition recipes for workflows I repeat."

Do **not** invoke it for one-off questions about screenpipe itself, for real-time screen queries, or without an explicit user request — the skill analyzes sensitive local content and must stay explicitly user-triggered.

## Privacy Posture

- **Configure capture filtering in Screenpipe before collecting history.** `references/screenpipe-config.yaml` is a checklist of literal, case-insensitive app/title substrings, not a Screenpipe-importable YAML file. Apply them in Screenpipe settings or as repeated `--ignored-windows` arguments; `*` is not a glob. Check exclusions with synthetic windows. Filtering cannot remove sensitive material already captured or guarantee complete exclusion.
- **Raw OCR is not sent to the synthesis backend by this pipeline.** `scripts/fetch_window.py` pulls data over localhost HTTP. `scripts/cluster.py` reduces the timeline to app/duration/title summaries. `scripts/redact.py` scrubs recognizable emails, API keys, bearer tokens, and selected phone formats as defense-in-depth before any cluster summary reaches the LLM.
- **LLM backend defaults to `local`.** Use an already installed chat model served by [LM Studio](https://lmstudio.ai/); its exact server model ID belongs in `local.model`. Summaries stay on the machine only while this endpoint is loopback. A remote HTTPS endpoint also sends summaries off-host. Cloud backends (`claude`, `foundry`) remain opt-in. Detection and embedding inference run locally regardless of backend choice.
- **Dry-run mode** (`--dry-run`) skips skill matching and LLM synthesis and writes a clustered `plan.md`. Review the retained app names and window titles before selecting a cloud backend; the regex scrubber does not guarantee anonymization or removal of unpublished research details.
- **TLS for localhost** (optional, for corporate policy): see `references/https-proxy.md` for the Caddy pattern.

## Prerequisites

### 1. Screenpipe daemon

Either install the official release or build from source. Either way the daemon binds HTTP on `localhost:3030` by default.

**From source** (recommended if you want the CLI daemon without the desktop GUI):

```bash
git clone --depth 1 https://github.com/screenpipe/screenpipe.git
cd screenpipe
cargo build -p screenpipe-engine --release
# System deps (macOS): cmake + full Xcode.app (not just Command Line Tools).
#   brew install cmake
#   # if xcodebuild plug-ins error: sudo xcodebuild -runFirstLaunch
./target/release/screenpipe doctor   # confirm permissions + ffmpeg
./target/release/screenpipe record --disable-audio --use-pii-removal \
  --ignored-windows "1Password" --ignored-windows "Bitwarden" \
  --ignored-windows "Private Browsing" --ignored-windows "Incognito"
```

This source-build example is illustrative and was not compiled in the API review. Check the installed `screenpipe record --help`; permissions and system dependencies vary by platform/release. On macOS, grant the requested Screen Recording/Accessibility permissions and relaunch. Review the full deny-list before real capture.

### 2. Screenpipe API token

Current Screenpipe enables API auth by default; protected routes such as `/search` require a bearer token even on loopback. `/health` is exempt, so a successful health check does not validate search authorization. For an authenticated instance, retrieve its local API token:

```bash
export SCREENPIPE_TOKEN="$(screenpipe auth token)"
```

(Or set `screenpipe.token` directly in `config.yaml` — env var is preferred since it keeps secrets out of version control.)

Screenpipe connections permit HTTP only on loopback; remote endpoints require HTTPS.
Generated draft names must be valid skill names, so model output cannot write outside the proposal directory.

### 3. Python environment

Create a separate environment; do not add scientific dependencies to the repository environment:

```bash
uv venv .venv-autoskill --python 3.12
uv pip install --python .venv-autoskill/bin/python httpx==0.28.1 pyyaml==6.0.3 sentence-transformers==6.1.0
source .venv-autoskill/bin/activate
```

The public `sentence-transformers/all-MiniLM-L6-v2` model downloads on first use. For an existing cache, set `embeddings.local_files_only: true` to prevent download attempts. Its 384-dimensional embeddings truncate inputs beyond 256 word pieces; long summaries may lose detail. Similarity is a retrieval heuristic, not proof of workflow equivalence.

### 4. Local LLM (default path) — LM Studio

- Install [LM Studio](https://lmstudio.ai/).
- Choose a chat model already installed on your machine (`lms ls`). Match the context length to its supported limits and availa

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

