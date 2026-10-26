---
id: sci-pi-agent
name: "Scientific: pi-agent"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Builds with and operates Pi, the minimal terminal coding harness. Use for installing Pi, configuring providers/models/settings/environment variables, creating Pi skills/extensions/packages/themes/prompt templates, embedding Pi through the SDK, integrating over RPC or JSON event s"
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "agent"
  - "pi-agent"
keywords:
  - "agent"
  - "builds"
  - "operates"
  - "minimal"
  - "terminal"
  - "coding"
  - "harness"
---

# Pi Agent

Use this skill when the user wants to operate Pi or build on top of Pi. Pi is a minimal terminal coding harness extended through TypeScript extensions, skills, prompt templates, themes, packages, custom models/providers, SDK integrations, RPC mode, JSON event streams, and TUI components.

## First Decision

Pick the reference before answering or coding:

| User intent | Read |
|---|---|
| What Pi is, docs map, install methods | `references/overview.md` |
| Install, authenticate, first run | `references/quickstart.md` |
| Day-to-day CLI usage, commands, modes, flags, project trust | `references/usage.md` |
| Provider auth, API keys, cloud provider setup | `references/providers.md` |
| Custom model entries, local models, proxies, compat flags | `references/models.md` |
| Local llama.cpp router, `/llama`, model download/load | `references/llama-cpp.md` |
| Settings keys and defaults | `references/settings.md` |
| `PI_*` and other environment variables | `references/environment-variables.md` |
| Extension development, custom tools, events, commands | `references/extensions.md` |
| Custom provider implementation, OAuth, custom streaming | `references/custom-provider.md` |
| Embed Pi in Node/TypeScript | `references/sdk.md` |
| Integrate from another process/language | `references/rpc.md` |
| Consume JSONL event output | `references/json.md` |
| Build terminal UI components | `references/tui.md` |
| Package extensions/skills/prompts/themes | `references/packages.md` |
| Delegate to subagents, chains, parallel runs, orchestration | `references/pi-subagents.md` |
| Connect MCP servers, codemode, MCP tool discovery/config | `references/mcp.md` (built-in), `references/pi-mcp-adapter.md` (optional adapter) |
| Interactive interview forms, structured user input | `references/pi-interview.md` |
| Web search, URL/PDF/repo fetching, video understanding | `references/pi-web-access.md` |
| Author Pi skills | `references/skills.md` |
| Prompt templates or themes | `references/prompt-templates.md`, `references/themes.md` |
| Sessions, branching, compaction, parsing JSONL | `references/sessions.md`, `references/compaction.md`, `references/session-format.md` |
| Security, sandboxing, trust | `references/security.md`, `references/containerization.md` |
| Keyboard or terminal issues | `references/keybindings.md`, `references/terminal-setup.md`, `references/tmux.md`, `references/windows.md`, `references/termux.md`, `references/shell-aliases.md` |
| Working on Pi itself | `references/development.md` |

## Build-On-Pi Defaults

Prefer the SDK for Node/TypeScript apps that need type safety, direct state access, in-process custom tools/extensions, or custom resource loading. Use `createAgentSession()` for a single stable session; use `createAgentSessionRuntime()` when the app must replace sessions through new/resume/fork/clone/import flows. Auth and model lookup go through `ModelRuntime.create()`.

Prefer RPC mode when the client is not Node.js, needs process isolation, or wants a language-agnostic JSONL protocol. Start with `pi --mode rpc --no-session` for stateless subprocess integration, then add session flags when persistence matters. Split records on `\n` only — Node `readline` is not protocol-compliant.

For RPC clients, correlate responses by unique request `id`, not arrival order,
and keep consuming events after a successful `prompt` response. Success means
accepted, queued, or handled; it is not completion. Subscribe before sending the
prompt, and wait for `agent_settled` for runs that actually start, because
`agent_end` may precede retries or queued work. If the response reports
`disposition: "handled"`, no run started and no settled event is owed. See the
[upstream RPC lifecycle](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/rpc.md).

Prefer JSON mode for one-shot command-line pipelines that only need streamed events, not bidirectional control: `pi --mode json "prompt"`.

Use extensions for Pi-native behavior: custom tools, command handlers, event hooks, provider registration, custom compaction, path protection, project trust policy, UI prompts, widgets, and TUI components.

Use packages when sharing or installing reusable extensions, skills, prompt templates, or themes across machines or projects.

## Safety Defaults

Pi is local and not sandboxed by default. Treat extensions, packages, skills, shell commands, and project-local `.pi` resources as code with the permissions of the Pi process. Project trust only guards which project inputs load — it is not a sandbox. For untrusted repos or unattended automation, isolate with Docker, OpenShell, Gondolin, a VM, or a remote sandbox.

Do not store secrets in project files. Prefer env vars, `~/.pi/agent/auth.json`, OAuth via `/login`, or command-backed secret lookups in `models.json`/provider config.

## Common Commands

```bash
npm install -g --ignore-scripts @earendil-works/pi-coding-agent
pi
pi -p "Summarize this codebase"
pi --mode json "List files"
pi --mode rpc --no-session
pi --provider anthropic --model claude-sonnet-4-5
pi --model sonnet:high "Solve this complex problem"
pi --tools read,grep,find,ls -p "Review this repository"
pi --tui-mode fullscreen
pi install npm:pi-subagents
pi update --all
```

## Source Coverage

These references were reviewed against the official Pi **0.99.2** release (2026-09-30), its published npm runtime and declarations, and current [Pi documentation](https://pi.dev/docs/latest). Source: [earendil-works/pi v0.99.2](https://github.com/earendil-works/pi/tree/v0.99.2/packages/coding-agent). Ecosystem contracts were checked against published `pi-subagents` **0.74.0**, `pi-mcp-adapter` **4.0.0**, `pi-interview` **0.13.0**, and `pi-web-access` **0.35.0** sources. These releases are the compatibility baseline, not interchangeable historical APIs.

Local checks cover CLI/RPC control, SDK sessions and transcript projection, mocked model/tool execution, extension loading, and example configuration/schema contracts. Authentication flows, paid model/search calls, graphical UI, and external sandboxes are documentation-verified only; deployment examples requiring them are illustrative. Check `pi --version`, `pi --help`, the installed package README, and TypeScript declarations before adapting examples to another release. Pi 0.99 includes native MCP; pi-subagents 0.74 removes `workflowScript`; adapter 4.0 uses `mcp-adapter.json` and `/mcp-adapter`.

## Citing Scientific Agent Skills

This s

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

