---
id: sciref-pi-agent-quickstart
name: "Scientific Ref: Quickstart"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (pi-agent): Quickstart"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "agent quickstart"
  - "quickstart"
keywords:
  - "agent"
  - "quickstart"
  - "specialized"
  - "scientific"
  - "reference"
---

# Quickstart

Source: https://pi.dev/docs/latest/quickstart

Reviewed against Pi 0.99.2 and the package versions listed in `../SKILL.md` on 2026-09-30.

## Install and Uninstall

```bash
npm install -g --ignore-scripts @earendil-works/pi-coding-agent
```

`--ignore-scripts` disables dependency lifecycle scripts. Pi does not need install scripts for normal npm installs.

Uninstall with the package manager that installed Pi. The curl installer uses global npm, so curl and npm installs both remove with npm:

```bash
npm uninstall -g @earendil-works/pi-coding-agent
pnpm remove -g @earendil-works/pi-coding-agent
yarn global remove @earendil-works/pi-coding-agent
bun uninstall -g @earendil-works/pi-coding-agent
```

Uninstalling Pi leaves settings, credentials, sessions, and installed packages in `~/.pi/agent/`.

## Authenticate

Use `/login` in interactive mode for subscription providers; built-in logins include OpenAI Sign in with ChatGPT, legacy OpenAI Codex, Claude, GitHub Copilot, Meta, xAI, OpenRouter, and Radius (available methods depend on the provider). API-key providers can be configured by environment variable or stored through `/login` in `~/.pi/agent/auth.json`.

```bash
export ANTHROPIC_API_KEY=sk-ant-...
pi
```

See `references/providers.md` for the full provider list.

## First Session

```bash
cd /path/to/project
pi
```

By default the model gets four tools: `read`, `write` (create/overwrite), `edit` (patch), and `bash`. Read-only built-ins `grep`, `find`, and `ls` are available through tool options. Pi works in the current directory and can modify files there — use git or another checkpointing workflow for rollback.

## Project Instructions

Pi loads context files at startup:

- `~/.pi/agent/AGENTS.md`
- `AGENTS.md` or `CLAUDE.md` from parent directories and the current directory

A directory containing `AGENTS.override.md` contributes that file instead of its `AGENTS.md`/`CLAUDE.md`. Run `/reload` or restart after changing context files.

## Common First Tasks

```bash
pi @README.md "Summarize this"
pi @src/app.ts @src/app.test.ts "Review these together"
!npm run lint
!!npm run lint
pi -c
pi -r
pi --name "my task"
pi --session <path|id>
pi -p "Summarize this codebase"
cat README.md | pi -p "Summarize this text"
pi -p @screenshot.png "What's in this image?"
pi --mode json "List files"
pi --mode rpc --no-session
```

Use `!command` to run shell and send output to the model; `!!command` runs without adding output to model context. Paste text or images with Ctrl+V (Alt+V on Windows and WSL), or drag images into supported terminals.

Switch models with `/model` or Ctrl+L, cycle thinking level with Shift+Tab, and cycle scoped models with Ctrl+P / Shift+Ctrl+P.

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

