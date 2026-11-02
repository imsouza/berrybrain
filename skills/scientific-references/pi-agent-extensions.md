---
id: sciref-pi-agent-extensions
name: "Scientific Ref: Extensions"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (pi-agent): Extensions"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "agent extensions"
  - "extensions"
keywords:
  - "agent"
  - "extensions"
  - "specialized"
  - "scientific"
  - "reference"
---

# Extensions

Source: https://pi.dev/docs/latest/extensions

Reviewed against Pi 0.99.2 and the package versions listed in `../SKILL.md` on 2026-09-30.

Extensions are TypeScript modules that extend Pi. They register tools, commands, shortcuts, CLI flags, providers, renderers, UI, event handlers, and persistent session entries. They run with the full permissions of the Pi process — only install extensions you trust.

## Locations

- `~/.pi/agent/extensions/*.ts` and `~/.pi/agent/extensions/*/index.ts` (global)
- `.pi/extensions/*.ts` and `.pi/extensions/*/index.ts` (project-local, loaded only after project trust)
- Paths from `settings.json` `extensions` / `packages`

Use `pi -e ./my-extension.ts` for quick tests only; auto-discovered extensions can be hot-reloaded with `/reload`. Extensions load via [jiti](https://github.com/unjs/jiti), so TypeScript needs no compilation.

## Quick Extension

```ts
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { Type } from "typebox";

export default function (pi: ExtensionAPI) {
  pi.on("session_start", async (_event, ctx) => {
    ctx.ui.notify("Extension loaded", "info");
  });

  pi.on("tool_call", async (event, ctx) => {
    if (event.toolName === "bash" && event.input.command?.includes("rm -rf")) {
      const ok = await ctx.ui.confirm("Dangerous", "Allow rm -rf?");
      if (!ok) return { block: true, reason: "Blocked by user" };
    }
  });

  pi.registerTool({
    name: "greet",
    label: "Greet",
    description: "Greet someone by name",
    parameters: Type.Object({ name: Type.String() }),
    async execute(_toolCallId, params) {
      return { content: [{ type: "text", text: `Hello, ${params.name}!` }], details: {} };
    },
  });

  pi.registerCommand("hello", {
    description: "Say hello",
    handler: async (args, ctx) => ctx.ui.notify(`Hello ${args || "world"}`, "info"),
  });
}
```

## Imports

`@earendil-works/pi-coding-agent` (extension types and APIs), `typebox` (tool parameter schemas), `@earendil-works/pi-ai` (`StringEnum` for Google-compatible enums), `@earendil-works/pi-tui` (TUI components), plus Node built-ins. Add a `package.json` next to the extension and run `npm install` for npm dependencies. Distributed packages must put runtime deps in `dependencies` — package installs use `npm install --omit=dev`.

## Factory Semantics

The default export receives `ExtensionAPI` and may be async; Pi awaits it before `session_start`, `resources_discover`, and flushing queued `pi.registerProvider()` calls. Use async factories for one-time startup work such as dynamic model discovery. Do **not** start background resources (processes, sockets, watchers, timers) in the factory — factories can run in invocations that never start a session. Start them in `session_start` or on demand, and close them in an idempotent `session_shutdown` handler.

## Event Lifecycle

Startup: `project_trust` (user/global and CLI `-e` extensions only) → `session_start { reason: "startup" }` → `resources_discover { reason: "startup" }`.

Prompt: extension commands checked first (they bypass `input`) → `input` → skill/template expansion → `before_agent_start` → `agent_start` → message events → per turn: `turn_start`, `context`, `before_provider_headers`, `before_provider_request`, `after_provider_response`, then `tool_execution_start`, `tool_call`, `tool_execution_update`, `tool_result`, `tool_execution_end` → `turn_end` → `agent_end` → `agent_settled`.

Session replacement (`/new`, `/resume`): `session_before_switch` (cancellable) → `session_shutdown` → `session_start { reason: "new" | "resume", previousSessionFile }` → `resources_discover`. `/fork` and `/clone` use `session_before_fork` (with `position: "before" | "at"`) then `reason: "fork"`. `/name` emits `session_info_changed`. Compaction: `session_before_compact` → `session_compact`. `/tree`: `session_before_tree` → `session_tree`. Model changes: `thinking_level_select` then `model_select`. Exit: `session_shutdown`.

## High-Value Hooks

- `project_trust` — must return `{ trusted: "yes" | "no" | "undecided", remember?: boolean }`. First yes/no decision wins and suppresses the built-in prompt. `ctx` is a limited trust context (cwd, mode, hasUI, select/confirm/input/notify).
- `resources_discover` — return `{ skillPaths, promptPaths, themePaths }`.
- `before_agent_start` — return `{ message }` to inject a persistent custom message. Prefer structured prompt-section/tool updates so Pi persists transcript deltas; `{ systemPrompt }` or `forceSystemPrompt` forces the leading provider prompt for this run. `event.systemPromptOptions` exposes the structured inputs Pi used: `customPrompt`, `selectedTools`, `toolSnippets`, `promptGuidelines`, `appendSystemPrompt`, `cwd`, `contextFiles`, `skills`.
- `context` — transforms the conversation without prompt/tool system messages; Pi restores that state afterward. Use `context_with_system` only to own the complete request-local transcript and preserve a system message at index zero.
- `provider_stream_event` — observes each parsed provider event before normalization; awaited, notification-only, not persisted.
- `turn_end` / `agent_before_settle` — may propose `custom`, `custom_message`, `context_edit`, or `compaction` entries and request one continuation with `continue: true`; guard against unconditional loops.
- `before_provider_headers` — mutate `event.headers` in place; a string adds/overrides, `null` deletes. Fires once per request; retries reuse the headers.
- `before_provider_request` — inspect or replace `event.payload`; handlers run in load order and `undefined` keeps it unchanged. Payload-level system-instruction rewrites are not reflected by `ctx.getSystemPrompt()`.
- `after_provider_response` — `event.status` and normalized `event.headers` before the stream body is consumed.
- `tool_call` — `event.input` is mutable and mutations affect execution (no re-validation); return `{ block: true, reason?, terminate? }` to block. `terminate` applies only to a blocked call, and the agent stops early only when every finalized result in the batch is terminating. Narrow with `isToolCallEventType("bash", event)`, or `isToolCallEventType<"my_tool", MyToolInput>(...)` for custom tools.
- `tool_result` — middleware-style chain; return partial patches (`content`, `details`, `isError`, `usage`). Use `isBashToolResult(event)` for typed bash details and `ctx.signal` for nested async work.
- `message_end` — return `{ message }` to replace the finalize

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

