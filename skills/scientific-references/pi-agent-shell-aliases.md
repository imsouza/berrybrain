---
id: sciref-pi-agent-shell-aliases
name: "Scientific Ref: Shell Aliases"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (pi-agent): Shell Aliases"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "agent shell aliases"
  - "shell aliases"
keywords:
  - "agent"
  - "shell"
  - "aliases"
  - "specialized"
  - "scientific"
  - "reference"
---

# Shell Aliases

Source: https://pi.dev/docs/latest/shell-aliases

Reviewed against Pi 0.99.2 on 2026-09-30.

Pi normally runs a separate non-interactive `bash -c` for each built-in Bash or `!`/`!!` command. To use aliases, create a Bash-compatible `~/.bash_aliases`:

```bash
alias ll='ls -la'
alias gs='git status --short'
```

Then configure `~/.pi/agent/settings.json`:

```json
{
  "shellCommandPrefix": "shopt -s expand_aliases\nsource ~/.bash_aliases"
}
```

Run `/reload`, then `!ll`. The prefix runs before every Bash command. Do not parse/evaluate arbitrary alias lines from `.zshrc` or source a zsh configuration into Bash. Configure `shellPath` when Bash is unavailable; `shopt` will fail under a `sh` fallback. Extensions replacing the shell own their setup.

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

