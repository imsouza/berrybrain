---
id: sciref-pi-agent-pi-interview
name: "Scientific Ref: pi-interview Package"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (pi-agent): pi-interview Package"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "agent interview"
  - "pi-interview package"
keywords:
  - "agent"
  - "interview"
  - "specialized"
  - "scientific"
  - "reference"
  - "package"
---

# pi-interview Package

Source: https://pi.dev/packages/pi-interview

Reviewed against Pi 0.99.2 and the package versions listed in `../SKILL.md` on 2026-09-30.

Interactive interview forms: the agent collects structured user responses through a form with single/multi-select, text input, image upload, and info panels, plus rich media (code, diffs, Markdown, images, Chart.js charts, Mermaid diagrams, tables, HTML).

```bash
pi install npm:pi-interview
pi install npm:glimpseui   # optional: native macOS window; browser fallback otherwise
```

Requires Pi v0.82.1 or later. Restart Pi after installing.

## Invocation

```javascript
await interview({
  questions: '/path/to/questions.json',
  timeout: 600,    // optional, seconds (default 600)
  verbose: false   // optional, debug logging
});
```

Lifecycle: the tool starts a local server and opens a Glimpse window (macOS), an Orca tab, or a browser tab → the user answers at their own pace with auto-save and timeout reset on any activity → the session ends by Submit (`⌘+Enter`), timeout (warning overlay with an option to stay), or Escape twice → the window closes and the agent receives responses, or `null` if cancelled.

Remote and Moshi sessions: when the session looks remote (ssh/mosh env, or an active remote login on the host), the tool skips or supplements the local window and prints the form URL with access hints — a Moshi tip when the moshi-hook gateway is running (tap the preview button in the terminal title bar and pick the interview server), and an exact `ssh -L` command for plain SSH (mosh cannot forward ports). The server binds low ports (8377+, scanning forward on collision) and answers tokenless loopback opens with a landing page that hops to the form, so Moshi's browser preview reaches it in one tap. Requests with a non-loopback `Host` header are rejected.

With multiple concurrent interviews, only the first auto-opens; the rest are queued and surfaced as URLs in tool output, plus a top-right toast with a dropdown to open queued sessions. Submitting the active interview redirects the window to the next queued one. A status bar shows project path, git branch, and session ID.

## Question Schema

```json
{
  "title": "Project Setup",
  "description": "Review my suggestions and adjust as needed.",
  "questions": [
    { "id": "context", "type": "info", "question": "Architecture context",
      "context": "This project needs SSR and edge deployment support." },
    { "id": "framework", "type": "single", "question": "Which framework?",
      "options": ["React", "Vue", "Svelte"],
      "recommended": "React", "conviction": "strong", "weight": "critical" },
    { "id": "features", "type": "multi", "question": "Which features?",
      "options": ["Auth", "Database", "API"], "recommended": ["Auth", "Database"] },
    { "id": "notes", "type": "text", "question": "Additional requirements?" },
    { "id": "mockup", "type": "image", "question": "Upload a design mockup" }
  ]
}
```

Question types: `single` (radio), `multi` (checkbox), `text`, `image` (upload), `info` (non-interactive panel).

| Field | Purpose |
|---|---|
| `id`, `type`, `question` | Identifier, type, question text |
| `options` | Choices for single/multi; strings or `{ label, content?, recommended?, conviction? }` objects |
| `recommended` | Pre-selected option(s) with a "Recommended" badge |
| `conviction` | `"strong"` or `"slight"` (slight opts out of pre-selection); requires `recommended` |
| `weight` | `"critical"` (prominent card) or `"minor"` (compact card) |
| `context` | Help text below the question |
| `content` | Code/diff/Markdown block: `{ source, lang, file, lines, highlights, showSource }`; `lang: "diff"` renders a diff, `lang: "md"`/`"markdown"` previews Markdown |
| `media` | Object or array of `image`, `table`, `chart`, `mermaid`, `html`; each supports `position` (`"above"`/`"below"`/`"side"`) and `caption`; tables take `{ headers, rows, highlights }` |

Single/multi questions also support an "Other" custom-text option, per-question image attachments (button or drag & drop), "✦ Generate more" and "↻ Review options" LLM actions, an "Ask about an option" inline assistant panel with prompt chips and provider/model overrides, and an optional per-option clarification field.

Question IDs must be unique. `conviction` requires a recommendation. Use either question-level recommendations or option-level flags, never both; a single-select recommendation names exactly one option. Markdown `content` rejects `lines`/`highlights`, and `showSource` is Markdown-only. The shipped question example was executed against 0.13.0 `validateQuestions`. GUI launch, remote browser routing, and paid option generation were not exercised.

## Response Format

```typescript
interface Response {
  id: string;
  value: string | string[];
  attachments?: string[];  // image paths attached to non-image questions
}
```

## Settings

`~/.pi/agent/settings.json`:

```json
{
  "interview": {
    "timeout": 600,
    "port": 19847,
    "snapshotDir": "~/.pi/interview-snapshots/",
    "autoSaveOnSubmit": true,
    "generateModel": "anthropic/claude-haiku-4-5",
    "launcher": "browser",
    "browser": "Firefox",
    "glimpseFloating": false,
    "theme": {
      "mode": "auto",
      "name": "default",
      "lightPath": "/path/to/light.css",
      "darkPath": "/path/to/dark.css",
      "toggleHotkey": "mod+shift+l"
    }
  }
}
```

Timeout precedence: function parameter > settings > default 600s. A fixed `port` keeps the URL stable across sessions. `generateModel` drives the generate/review option actions, defaulting to the agent's current model then a cheap available model; if an explicitly configured model fails and the session uses a different one, it retries once with the session model. `glimpseFloating` keeps the native macOS window above others (browser fallback unaffected).

`launcher` chooses where the form opens; omit it for the default (Glimpse on a local macOS session with `glimpseui` installed, otherwise a browser tab):

- `"glimpse"` — native macOS Glimpse window; requires a local macOS session with `glimpseui`, and reports why the window could not open instead of falling back to a browser.
- `"browser"` — browser tab even when Glimpse is installed.
- `"orca"` — a browser tab in the current [Orca](https://github.com/stablyai/orca)-managed worktree, or Orca's focused worktree when the cwd is outside one; the tab is focused when that worktree is visible, otherwise staged in it

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

