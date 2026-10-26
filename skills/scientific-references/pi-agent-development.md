---
id: sciref-pi-agent-development
name: "Scientific Ref: Development"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (pi-agent): Development"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "agent development"
  - "development"
keywords:
  - "agent"
  - "development"
  - "specialized"
  - "scientific"
  - "reference"
---

# Development

Source: https://github.com/earendil-works/pi/tree/v0.99.2 (README.md, CONTRIBUTING.md, AGENTS.md, package.json and pi-test.sh; development is no longer a current docs page)

Reviewed against Pi 0.99.2 and the package versions listed in `../SKILL.md` on 2026-09-30.

Use this when working on Pi itself.

## Setup

```bash
git clone https://github.com/earendil-works/pi
cd pi
npm install
npm run build
```

Run from source:

```bash
/path/to/pi/pi-test.sh
```

The script can be run from any directory and preserves the caller's cwd.

## Forking and Rebranding

Configure `package.json`:

```json
{
  "piConfig": {
    "name": "pi",
    "configDir": ".pi"
  }
}
```

Change `name`, `configDir`, and `bin` for a fork. This affects CLI banner, config paths, and environment variable names.

## Path Resolution

Pi has npm install, standalone binary, and Node type-stripping source execution modes. Always use `src/config.ts` helpers such as `getPackageDir` and `getThemeDir` for package assets. Do not use `__dirname` directly for assets.

## Debugging and Tests

`/debug` writes rendered TUI lines and last LLM messages to `~/.pi/agent/pi-debug.log`.

```bash
npm run check
./test.sh
npm test
npm --prefix packages/coding-agent test -- test/specific.test.ts
```

These are upstream developer commands, not commands executed by this review. `npm run check` includes formatting writes, and the full test/build workflows can use native tools or network services. For a targeted test, run from the owning package.

## Project Structure

```text
packages/
  ai/            # LLM provider abstraction
  agent/         # Agent loop and message types
  tui/           # Terminal UI components
  coding-agent/  # CLI and interactive mode
  codemode/      # QuickJS tool composition
  mcp/           # Native MCP clients
  protocol/      # Shared wire definitions
  client/        # Client integration
  server/        # Server integration
```

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

