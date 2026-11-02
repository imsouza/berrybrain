---
id: sciref-pi-agent-rpc
name: "Scientific Ref: RPC Mode"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (pi-agent): RPC Mode"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "agent rpc"
  - "rpc mode"
keywords:
  - "agent"
  - "rpc"
  - "specialized"
  - "scientific"
  - "reference"
  - "mode"
---

# RPC Mode

Sources: https://pi.dev/docs/latest/rpc, https://pi.dev/docs/latest/rpc-commands, https://pi.dev/docs/latest/rpc-extension-ui

Reviewed against Pi 0.99.2 and the package versions listed in `../SKILL.md` on 2026-09-30.

RPC mode runs Pi headlessly over stdin/stdout JSONL. Use it for language-agnostic clients, IDE integrations, custom UIs, or subprocess isolation. For Node/TypeScript in-process apps prefer the SDK unless you want subprocess isolation.

```bash
pi --mode rpc [options]
```

Common options: `--provider`, `--model` (supports `provider/id` and `:<thinking>`), `--name`/`-n`, `--no-session`, `--session-dir`.

## Framing

Commands are JSON objects on stdin, one per line; responses (`type: "response"`) and events stream to stdout as JSON lines. Use LF (`\n`) as the only record delimiter, strip an optional trailing `\r`, and never use readers that split on Unicode separators — Node `readline` is not protocol-compliant because it also splits on U+2028/U+2029, which are valid inside JSON strings.

Commands accept an optional `id`; the response echoes it. Events generally omit `id`; `bash_execution_update` carries the `id` of its originating `bash` command.

Responses have the shape `{"type":"response","command":"...","success":true|false,"data":{...},"error":"..."}`. Parse failures return `command: "parse"`.

## Prompting Commands

`prompt` — `{"id":"req-1","type":"prompt","message":"Hello"}`. Optional `images: [{"type":"image","data":"base64...","mimeType":"image/png"}]`. While streaming, `streamingBehavior` is required (`"steer"` or `"followUp"`) or the command errors. Extension commands execute immediately even during streaming; skill commands and prompt templates expand before sending or queueing. `success: true` returns `data.disposition: "started" | "queued" | "handled"`; later failures arrive as events, not a second response. A handled prompt starts no run. Wait for `agent_settled` only for work that started.

`steer` — queue a steering message delivered after the current assistant turn's tool calls. `follow_up` — queue a message delivered when the agent is fully done. Both accept `images`, invoke input handlers, expand skills/templates, reject extension commands, and return `{ disposition: "queued" | "handled" }`.

`abort` — abort the current agent operation. `clear_queue` clears queued messages and returns the removed `{ steering, followUp }` arrays.

`new_session` — optional `parentSession`; response `data: { cancelled }` (an extension may cancel via `session_before_switch`).

## State, Model, Thinking

- `get_state` → `model` (full Model object or `null`), `thinkingLevel`, `isStreaming`, `isCompacting`, `steeringMode`, `followUpMode`, `sessionFile`, `sessionId`, `sessionName`, `autoCompactionEnabled`, `messageCount`, `pendingMessageCount`.
- `get_messages` → all `AgentMessage` objects.
- `set_model` (`provider`, `modelId`) → full Model object.
- `cycle_model` → `{ model, thinkingLevel, isScoped }`, or `null` data with one model.
- `get_available_models` → array of Model objects.
- `set_thinking_level` (`off`, `minimal`, `low`, `medium`, `high`, `xhigh`, `max`; `xhigh`/`max` only when the model supports them).
- `cycle_thinking_level` → `{ level }`, `null` if the model has no thinking.
- `get_available_thinking_levels` → `{ levels }`; `["off"]` for non-reasoning models.

## Queue, Compaction, Retry

- `set_steering_mode` / `set_follow_up_mode`: `"all"` or `"one-at-a-time"` (default).
- `compact` with optional `customInstructions` → `{ summary, firstKeptEntryId, tokensBefore, estimatedTokensAfter, usage, details }`. `estimatedTokensAfter` is a heuristic over the rebuilt context, not a provider-exact count; `usage` may be omitted by custom compaction handlers.
- `set_auto_compaction` (`enabled`), `set_auto_retry` (`enabled`), `abort_retry`.

## Bash

`bash` (`command`, optional `id`) executes immediately, streams `bash_execution_update` events, and returns `{ output, exitCode, cancelled, truncated }` plus `fullOutputPath` when truncated. Internally a `BashExecutionMessage` is stored in agent state; it reaches the LLM on the **next** `prompt`, rendered as ``Ran `cmd``` plus a fenced output block. Multiple bash commands before a prompt are all included. `abort_bash` aborts a running command.

## Session Commands

- `get_session_stats` → session file/id, message counts, `tokens` (`input`, `output`, `cacheRead`, `cacheWrite`, `total`), `cost`, and `contextUsage` (`tokens`, `contextWindow`, `percent`). Totals include tool-reported usage and summary generation. `contextUsage` is omitted without a model/context window; `tokens`/`percent` are `null` right after compaction until a fresh assistant response provides usage.
- `export_html` with optional `outputPath` → `{ path }`.
- `switch_session` (`sessionPath`) → `{ cancelled }`.
- `fork` (`entryId`) → `{ text, cancelled }`; `clone` → `{ cancelled }`. Both can be cancelled by `session_before_fork`.
- `get_fork_messages` → `[{ entryId, text }]`.
- `get_entries` with optional `since` cursor → `{ entries, leafId }`. Includes pre-compaction history and abandoned branches, unlike `get_messages`. Entry ids are durable cursors across client restarts; an unknown `since` returns `success: false`. `leafId` is `null` for an empty session.
- `get_tree` → `{ tree, leafId }` where each node is `{ entry, children, label?, labelTimestamp? }`. Orphaned entries appear as extra roots.
- `get_last_assistant_text` → `{ text }` or `{ text: null }`.
- `set_session_name` (`name`); read it back from `get_state.sessionName`. Set the initial name with `--name`.

## Commands Discovery

`get_commands` returns extension commands, prompt templates, and skills (`skill:` prefixed) with `name`, `description`, `source` (`extension` | `prompt` | `skill`), optional `location` (`user` | `project` | `path`), and `path`. Built-in TUI commands such as `/settings` are interactive-only and excluded.

## Events

`agent_start`; `agent_end` (`messages`, `willRetry`); `agent_settled` (nothing will continue automatically — no retry, compaction retry, or queued continuation); `turn_start` / `turn_end`; `message_start` / `message_update` / `message_end`; `bash_execution_update`; `tool_execution_start` / `_update` / `_end`; `queue_update`; `compaction_start` / `compaction_end`; `auto_retry_start` / `auto_retry_end`; `summarization_retry_scheduled` / `summarization_retry_attempt_start` / `summarization_retry_finished`; `extension_error`.

`message_update.assistantM

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

