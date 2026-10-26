---
id: sciref-pi-agent-sdk
name: "Scientific Ref: SDK"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (pi-agent): SDK"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "agent sdk"
keywords:
  - "agent"
  - "sdk"
  - "specialized"
  - "scientific"
  - "reference"
---

# SDK

Source: https://pi.dev/docs/latest/sdk

Reviewed against Pi 0.99.2 and the package versions listed in `../SKILL.md` on 2026-09-30.

The SDK ships in the main package:

```bash
npm install @earendil-works/pi-coding-agent
```

Use it to embed Pi, build custom UIs, automate workflows, spawn sub-agents, test behavior, or customize tools/resources in process.

## Quick Start

```ts
import { createAgentSession, ModelRuntime, SessionManager } from "@earendil-works/pi-coding-agent";

const modelRuntime = await ModelRuntime.create();
const { session } = await createAgentSession({
  sessionManager: SessionManager.inMemory(),
  modelRuntime,
});

session.subscribe((event) => {
  if (event.type === "message_update" && event.assistantMessageEvent.type === "text_delta") {
    process.stdout.write(event.assistantMessageEvent.delta);
  }
});

try {
  await session.prompt("What files are in the current directory?");
} finally {
  await session.extensionRunner.emit({ type: "session_shutdown", reason: "quit" });
  session.dispose();
}
```

`createAgentSession()` returns `{ session, extensionsResult, modelFallbackMessage? }` and uses `DefaultResourceLoader` when no `resourceLoader` is passed.

## `AgentSession`

Methods: `prompt(text, options?)`, `steer(text)`, `followUp(text)`, `subscribe(listener)` (returns unsubscribe), `setModel`, `setThinkingLevel`, `cycleModel`, `cycleThinkingLevel`, `navigateTree(targetId, { summarize, customInstructions, replaceInstructions, label })`, `compact(customInstructions?)`, `abortCompaction()`, `abort()`, `dispose()`.

State: `sessionFile`, `sessionId`, `agent`, `model`, `thinkingLevel`, `messages`, `isStreaming`.

`session.agent.state` exposes `messages`, `model`, `thinkingLevel`, `systemPrompt`, `tools`, `streamingMessage`, `errorMessage`; `SessionManager` is authoritative for finalized context: assigning `agent.state.messages` does not replace persisted history. Restore external history with `SessionManager.inMemory(cwd, options, entries)` before creating the session. Use `session.waitForIdle()` to wait for the full session run.

Session replacement (new/resume/fork/clone/import) lives on `AgentSessionRuntime`, not `AgentSession`.

## Runtime API

```ts
const createRuntime: CreateAgentSessionRuntimeFactory = async ({ cwd, sessionManager, sessionStartEvent }) => {
  const services = await createAgentSessionServices({ cwd });
  return {
    ...(await createAgentSessionFromServices({ services, sessionManager, sessionStartEvent })),
    services,
    diagnostics: services.diagnostics,
  };
};

const runtime = await createAgentSessionRuntime(createRuntime, {
  cwd: process.cwd(),
  agentDir: getAgentDir(),
  sessionManager: SessionManager.create(process.cwd()),
});
```

`await runtime.dispose()` emits extension shutdown and releases the active session. `AgentSessionRuntime` owns `newSession()`, `switchSession(path)`, `fork(entryId)`, clone via `fork(entryId, { position: "at" })`, and `importFromJsonl()`. `runtime.session` changes after each, so re-subscribe to events and call `runtime.session.bindExtensions(...)` again if you manage extensions manually. Creation returns `runtime.diagnostics`; failures throw.

## Prompting and Queueing

```ts
interface PromptOptions {
  expandPromptTemplates?: boolean;
  images?: ImageContent[];
  streamingBehavior?: "steer" | "followUp";
  source?: InputSource;
  preflightResult?: (disposition: "started" | "queued" | "handled") => void;
}
```

`preflightResult` is an internal RPC hook called only after acceptance with a disposition string. It is not called when preflight rejects; it no longer receives a boolean. Failures after acceptance surface through events and messages. `prompt()` resolves only after the full accepted run finishes, including retries.

Extension commands execute immediately even during streaming. File-based prompt templates expand before sending or queueing. Calling `prompt()` while streaming without `streamingBehavior` throws — use `session.steer()` (delivered after the current assistant turn's tool calls) or `session.followUp()` (after all work finishes). Both pass through extension input handlers, expand templates, reject extension commands, and return `"queued"` or `"handled"`.

## Events

`message_update` (with `assistantMessageEvent` deltas such as `text_delta`, `thinking_delta`), `tool_execution_start` / `_update` / `_end`, `message_start` / `message_end`, `agent_start` / `agent_end` / `agent_settled`, `entry_appended`, `session_info_changed`, `thinking_level_changed`, `turn_start` / `turn_end`, `queue_update`, `compaction_start` / `compaction_end`, `auto_retry_start` / `auto_retry_end`, `summarization_retry_scheduled` / `summarization_retry_attempt_start` / `summarization_retry_finished`.

## Models and Auth

`ModelRuntime` replaces the older `AuthStorage` + `ModelRegistry` pair (a synchronous `ModelRegistry` facade remains exported for extension compatibility).

```ts
const modelRuntime = await ModelRuntime.create({ authPath, modelsPath, credentials });
modelRuntime.getModel(provider, id);        // built-ins + models.json, no auth check
await modelRuntime.getAvailable();          // only models with valid auth
await modelRuntime.checkAuth(providerId);
modelRuntime.getProviders();                // provider.auth methods and status
await modelRuntime.setRuntimeApiKey(provider, key); // not persisted
```

Credential priority: runtime overrides → `auth.json` → configured `models.json` API key → provider environment/ambient auth (native provider extensions can define their own resolution). `getModel(provider, id)` from `@earendil-works/pi-ai/compat` looks up built-ins only. Inject any pi-ai `CredentialStore` (for example `InMemoryCredentialStore`) via `credentials`.

### Catalog Refresh and Deadlines

`create()` restores cached catalogs but does not refresh them from `pi.dev` by default. Opt in with `ModelRuntime.create({ allowModelNetwork: true, modelRefreshTimeoutMs: 15_000 })`. Remote catalogs persist to `~/.pi/agent/models-store.json` (override with `modelsStorePath`, or inject `modelsStore`); refreshes are throttled to once per provider every four hours unless forced, and `PI_OFFLINE` disables model network access entirely.

Public model/auth operations and `ModelRuntime.create({ signal })` accept optional abort signals and are unbounded when omitted — SDK applications own deadline policy:

```ts
const result = await modelRuntime.refresh({ providers: ["anthropic"], signal: AbortSignal.timeout(15

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

