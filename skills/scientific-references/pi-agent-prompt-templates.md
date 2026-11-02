---
id: sciref-pi-agent-prompt-templates
name: "Scientific Ref: Prompt Templates"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (pi-agent): Prompt Templates"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "agent prompt templates"
  - "prompt templates"
keywords:
  - "agent"
  - "prompt"
  - "templates"
  - "specialized"
  - "scientific"
  - "reference"
---

# Prompt Templates

Source: https://pi.dev/docs/latest/prompt-templates

Reviewed against Pi 0.99.2 and the package versions listed in `../SKILL.md` on 2026-09-30.

Prompt templates are Markdown snippets that expand into full prompts. Type `/name` in the editor, where `name` is the filename without `.md` (`review.md` → `/review`).

## Locations

- Global: `~/.pi/agent/prompts/*.md`
- Project: `.pi/prompts/*.md` (only after project trust)
- Packages: `prompts/` directories or `pi.prompts` entries in `package.json`
- Settings: `prompts` array with files or directories
- CLI: `--prompt-template <path>` (repeatable)

Disable discovery with `--no-prompt-templates`.

## Format

```md
---
description: Review staged git changes
argument-hint: "<PR-URL>"
---
Review the staged changes (`git diff --cached`). Focus on: $ARGUMENTS
```

`description` is optional — without it Pi uses the first non-empty line. `argument-hint` is optional and shown **before** the description in the autocomplete dropdown; use `<angle brackets>` for required arguments and `[square brackets]` for optional ones.

## Usage

```text
/review                           # expands review.md
/component Button                 # one argument
/component Button "click handler"  # multiple arguments
```

## Arguments

- `$1`, `$2`, … positional
- `$@` or `$ARGUMENTS` all arguments joined
- `${1:-default}` argument 1 when present and non-empty, otherwise the default
- `${@:-default}` or `${ARGUMENTS:-default}` all arguments when present, otherwise the default
- `${@:N}` arguments from the Nth position (1-indexed)
- `${@:N:L}` `L` arguments starting at N

## Loading Rules

Discovery in `prompts/` is non-recursive. Templates in subdirectories must be added explicitly through the `prompts` setting or a package manifest.

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

