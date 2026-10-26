---
id: sciref-pi-agent-termux
name: "Scientific Ref: Termux Setup"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (pi-agent): Termux Setup"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "agent termux"
  - "termux setup"
keywords:
  - "agent"
  - "termux"
  - "specialized"
  - "scientific"
  - "reference"
  - "setup"
---

# Termux Setup

Source: https://pi.dev/docs/latest/termux

Reviewed against Pi 0.99.2 and the package versions listed in `../SKILL.md` on 2026-09-30.

Pi runs on Android through Termux.

## Prerequisites

Install Termux from GitHub or F-Droid, not Google Play. Optionally install Termux:API from the same distribution source as Termux for clipboard and device integrations.

## Install

```bash
pkg update && pkg upgrade
pkg install nodejs termux-api git
npm install -g --ignore-scripts @earendil-works/pi-coding-agent
mkdir -p ~/.pi/agent
pi
```

## Clipboard

Pi uses `termux-clipboard-set` and `termux-clipboard-get` when available. Image clipboard is not supported in Termux.

## Useful `AGENTS.md` Context

Add Termux environment notes to `~/.pi/agent/AGENTS.md`: OS is Android/Termux, home is `/data/data/com.termux/files/home`, prefix is `/data/data/com.termux/files/usr`, shared storage is `/storage/emulated/0`, use `termux-open-url`, `termux-open`, `termux-share`, `termux-notification`, and clipboard commands where appropriate.

## Limitations and Troubleshooting

No image clipboard. Some optional native binaries may be unavailable on Android ARM64. Run `termux-setup-storage` once for `/storage/emulated/0`. If `pi` is not found, open a fresh shell, check `npm prefix -g` and `command -v pi`, then ensure the global npm binary directory is on PATH.

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

