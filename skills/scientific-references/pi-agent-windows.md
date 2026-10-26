---
id: sciref-pi-agent-windows
name: "Scientific Ref: Windows Setup"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (pi-agent): Windows Setup"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "agent windows"
  - "windows setup"
keywords:
  - "agent"
  - "windows"
  - "specialized"
  - "scientific"
  - "reference"
  - "setup"
---

# Windows Setup

Source: https://pi.dev/docs/latest/windows

Reviewed against Pi 0.99.2 and the package versions listed in `../SKILL.md` on 2026-09-30.

On native Windows, Pi supports both `bash` and a dedicated `powershell` tool (PowerShell 7 when available, then Windows PowerShell). Select it explicitly with `"defaultTools": ["-bash", "+powershell"]`; `!` and `!!` commands still use Bash. For Bash execution, Pi checks, in order:

1. Custom path from `~/.pi/agent/settings.json`
2. Git Bash (`C:\Program Files\Git\bin\bash.exe`)
3. `bash.exe` on PATH (Cygwin, MSYS2, WSL)

[Git for Windows](https://git-scm.com/download/win) is sufficient for most users.

## Custom Shell Path

```json
{
  "shellPath": "C:\\cygwin64\\bin\\bash.exe"
}
```

The value is JSON, so each literal backslash in the Windows path must be doubled.

Related Windows notes: Ctrl+Enter for multi-line input, Alt+V to paste images, `app.suspend` has no default binding (`references/keybindings.md`), and the default follow-up shortcut is Ctrl+Q (Alt+Q dequeues); remap Alt+Enter only if explicitly binding it instead of fullscreen (`references/terminal-setup.md`).

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

