---
id: sciref-pi-agent-settings
name: "Scientific Ref: Settings"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (pi-agent): Settings"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "agent settings"
  - "settings"
keywords:
  - "agent"
  - "settings"
  - "specialized"
  - "scientific"
  - "reference"
---

# Settings

Source: https://pi.dev/docs/latest/settings

Reviewed against Pi 0.99.2 and the package versions listed in `../SKILL.md` on 2026-09-30.

Pi uses JSON settings files. Project settings override global settings; nested objects merge key by key and resource arrays combine. Edit directly or use `/settings` for common options.

| Location | Scope |
|---|---|
| `~/.pi/agent/settings.json` | Global |
| `.pi/settings.json` | Project |

Resource paths in the global file resolve relative to `~/.pi/agent`; in the project file relative to `.pi`. Absolute paths and `~` work.

## Project Trust

Interactive startup asks before trusting a project folder that has project-local settings, resources, or project `.agents/skills` and no saved decision for that folder or a parent in `~/.pi/agent/trust.json`. Non-interactive modes never prompt and use `defaultProjectTrust` (`"ask"` default, `"never"`, `"always"`); `--approve`/`-a` and `--no-approve`/`-na` override for one run. `/trust` saves a decision (including for the immediate parent folder) but does not reload the current session. `pi config` and package commands follow the same flow; `pi update` never prompts.

## Model and Thinking

| Setting | Default | Notes |
|---|---|---|
| `defaultProvider` | – | Provider id |
| `defaultModel` | – | Model id |
| `defaultThinkingLevel` | `"medium"` | `off`, `minimal`, `low`, `medium`, `high`, `xhigh`, `max` |
| `hideThinkingBlock` | `false` | Hide thinking blocks in output |
| `showCacheMissNotices` | `false` | Transcript notices for significant prompt-cache misses |
| `thinkingBudgets` | – | Custom token budgets per thinking level |

## UI and Display

`theme` (`"system"`), `externalEditor` (Ctrl+G command; takes precedence over `$VISUAL`/`$EDITOR` — use `"code --wait"` for VS Code), `quietStartup` (`false`), `defaultProjectTrust` (`"ask"`, global only), `collapseChangelog` (`false`), `enableInstallTelemetry` (`true`), `enableAnalytics` (`false`, only asked during experimental first-time setup with `PI_EXPERIMENTAL=1`), `trackingId`, `doubleEscapeAction` (`"tree"` | `"fork"` | `"none"`), `treeFilterMode` (`"default"` | `"no-tools"` | `"user-only"` | `"labeled-only"` | `"all"`), `editorPaddingX` (`0`, range 0–3), `outputPad` (`1`, 0 or 1), `autocompleteMaxVisible` (`5`, range 3–20), `showHardwareCursor` (`false`).

Fullscreen TUI: `tuiMode` (`"regular"` default, or experimental `"fullscreen"`; `/settings` changes apply immediately and `--tui-mode` overrides at startup), `fullscreenExitOutput` (`"transcript"` prints the final transcript plus resume hint, `"resume-hint"` restores the previous screen and prints only the hint), `fullscreenScrollbar` (`"auto"` shows it while scrolling, `"always"` reserves the rightmost column, `"hidden"`). These have no effect in regular mode. `fullscreenCopyOnSelect` defaults to `true`; `fullscreenWheelScrollLines` is `"auto"` or 1–100.

## Network, Warnings, Markdown

`httpProxy` (applied as `HTTP_PROXY`/`HTTPS_PROXY`, global only). `warnings.anthropicExtraUsage` (`true`) warns when Anthropic subscription auth may use paid extra usage. `markdown.codeBlockIndent` (`"  "`), `markdown.mermaid` (`"streaming"`, or `"final"` / `"off"`).

## Compaction and Branch Summary

`compaction.enabled` (`true`), `compaction.reserveTokens` (`16384`), `compaction.keepRecentTokens` (`20000`), and `compaction.modelOverrides` keyed by exact `provider/modelId` with independently resolved non-negative safe-integer budgets. `branchSummary.reserveTokens` (`16384`), `branchSummary.skipPrompt` (`false`, defaults to no summary).

## Retry

`retry.enabled` (`true`), `retry.maxRetries` (`3`), `retry.baseDelayMs` (`2000`, so 2s/4s/8s), `retry.maxAgentDelayMs` (`60000`), `retry.provider.timeoutMs` (`httpIdleTimeoutMs`), `retry.provider.maxRetries` (`0`), `retry.provider.maxRetryDelayMs` (`60000`; `0` disables the limit).

Keep `retry.provider.maxRetries` at `0` unless provider-level retries are explicitly needed — above `0`, SDK retries can swallow out-of-usage-limit errors before Pi sees them and block the agent until quota resets. When a provider requests a delay longer than `maxRetryDelayMs`, the request fails immediately with an informative error instead of waiting silently.

## Message Delivery

`steeringMode` / `followUpMode` (`"one-at-a-time"` or `"all"`), `transport` (`"auto"`, `"sse"`, `"websocket"`, `"websocket-cached"`), `httpIdleTimeoutMs` (`300000`, `0` disables), `websocketConnectTimeoutMs` (`15000`, `0` disables).

## Terminal and Images

`terminal.showImages` (`true`), `terminal.imageWidthCells` (`60`), `terminal.clearOnShrink` (`false`), `terminal.showTerminalProgress` (`false`), `terminal.hyperlinks` / `terminal.trueColor` (`"auto"` or boolean), `terminal.images` (`"auto"`, `"kitty"`, `"iterm2"`, or `false`), `images.autoResize` (`true`, 2000×2000 max; applies to `@file` attachments, `read`, and images returned by tools), `images.blockImages` (`false`).

## Tools

`defaultTools` is a string array of built-in tools enabled at startup; omitting it uses Pi's standard defaults. Extension and SDK custom tools stay enabled, and an empty array starts with no built-ins while preserving them. `--tools` replaces this with a strict allowlist for all tools, `--no-tools` disables everything, `--no-builtin-tools` disables the built-in defaults, and `--exclude-tools` filters the result. Plain names replace the inherited selection. Lists of only `+name`/`-name` adjust it; project deltas apply over global defaults. For example `["+codemode"]` adds codemode, while `["-bash", "+powershell"]` selects native Windows PowerShell. `/reload` enables newly added defaults but does not deactivate removed tools or re-enable unchanged tools disabled at runtime. CLI tool overrides still win. `codemode.mode` is `"on"` or `"only"`; `codemode.inlineBudget` defaults to `3000` tokens.

## Shell

`shellPath` (supports leading `~`; Windows paths in JSON need forward slashes or escaped backslashes, e.g. `"C:/Program Files/Git/bin/bash.exe"`), `shellCommandPrefix` (prefix for every bash command), `npmCommand` (argv array, e.g. `["mise", "exec", "node@24", "--", "npm"]`). `npmCommand` covers all npm package-manager operations; user npm packages install under `~/.pi/agent/npm/`, project ones under `.pi/npm/`. When `npmCommand` is configured, git package dependency installs use plain `install` for wrapper compatibility.

## Sessions and Model Cycling

`sessionDir` (absolute, relative, or `~`); precedence is `--session-dir`

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

