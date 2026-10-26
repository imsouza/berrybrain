---
id: sciref-pi-agent-custom-provider
name: "Scientific Ref: Custom Providers"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (pi-agent): Custom Providers"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "agent custom provider"
  - "custom providers"
keywords:
  - "agent"
  - "custom"
  - "provider"
  - "specialized"
  - "scientific"
  - "reference"
  - "providers"
---

# Custom Providers

Source: https://pi.dev/docs/latest/custom-provider

Reviewed against Pi 0.99.2 and the package versions listed in `../SKILL.md` on 2026-09-30.

Extensions register providers with `pi.registerProvider()` for proxies, private deployments, OAuth/SSO, and non-standard streaming APIs. Two forms exist: a complete pi-ai `Provider` (preferred when you need custom authentication, filtering, refresh, or streaming) and the legacy provider-config object. `models.json` overrides compose **above** registered native providers.

## Complete Provider Form

```ts
import { createProvider } from "@earendil-works/pi-ai";
import * as openaiCompletionsApi from "@earendil-works/pi-ai/api/openai-completions";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

export default function (pi: ExtensionAPI) {
  pi.registerProvider(createProvider({
    id: "native-local",
    name: "Native Local",
    baseUrl: "http://localhost:8080/v1",
    auth: {
      apiKey: {
        name: "Local server API key",
        async login(interaction) {
          return { type: "api_key", key: await interaction.prompt({ type: "secret", message: "API key" }) };
        },
        async resolve({ credential }) {
          return credential?.key ? { auth: { apiKey: credential.key }, source: "stored API key" } : undefined;
        },
      },
    },
    models: [],
    api: openaiCompletionsApi,
  }));
}
```

The object form accepts a complete `Provider`, including native `auth`, `getModels`, `refreshModels`, `filterModels`, `stream`, and `streamSimple`.

## Legacy Config Form

```ts
// Override baseUrl and/or headers only — existing models are preserved
pi.registerProvider("anthropic", { baseUrl: "https://proxy.example.com" });
pi.registerProvider("openai", { headers: { "X-Custom-Header": "value" } });

// New provider with models — replaces all existing models for that provider
pi.registerProvider("my-provider", {
  name: "My Provider",
  baseUrl: "https://api.example.com",
  apiKey: "$MY_API_KEY",
  api: "openai-completions",
  models: [{
    id: "my-model",
    name: "My Model",
    reasoning: false,
    input: ["text", "image"],
    cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 },
    contextWindow: 128000,
    maxTokens: 4096,
  }],
});
```

Use an **async extension factory** for dynamic model discovery so models are registered before startup finishes and are visible to `pi --list-models`. Dynamic providers can also implement `refreshModels(context)`. Complete Providers return nothing and call `context.publish({ update })` to install provider-owned state exposed by `getModels()`. Legacy config callbacks return model definitions. Use the generation-checked publish persistence contract, never the removed `context.store` pattern; pass `context.signal` to I/O.

`pi.unregisterProvider(name)` removes that provider's dynamic models, API key fallback, OAuth registration, and custom stream handlers, restoring overridden built-in behavior. Calls made after the initial load phase take effect immediately — no `/reload`.

## API Types

`anthropic-messages`, `openai-completions`, `openai-responses`, `azure-openai-responses`, `openai-codex-responses`, `mistral-conversations`, `google-generative-ai`, `google-vertex`, `bedrock-converse-stream`.

Most OpenAI-compatible providers work with `openai-completions`; use model-level `thinkingLevelMap` for thinking levels and `compat` for quirks (full flag list in `references/models.md`). `xhigh` and `max` are opt-in and require non-null map entries. Mistral moved from `openai-completions` to `mistral-conversations` (native Mistral Chat Completions streaming) — use the latter for native Mistral models.

## Auth Header and Secrets

`authHeader: true` adds `Authorization: Bearer <apiKey>`; the key is resolved per request and an explicit request `Authorization` header wins. `apiKey` and custom header values use the same syntax as `models.json`: leading `!command` executes for the whole value, `$ENV`/`${ENV}` interpolate, `$$` and `$!` escape literals.

## OAuth

```ts
oauth: {
  name: "Corporate AI (SSO)",
  async login(callbacks: OAuthLoginCallbacks): Promise<OAuthCredentials>,
  async refreshToken(credentials: OAuthCredentials, signal: AbortSignal): Promise<OAuthCredentials>,
  getApiKey(credentials: OAuthCredentials): string,
}
```

`OAuthLoginCallbacks`: `onAuth({ url })` (open in browser), `onDeviceCode({ userCode, verificationUri, intervalSeconds?, expiresInSeconds? })`, `onProgress?(message)`, `onPrompt({ message }): Promise<string>`, `onSelect({ message, options: { id, label }[] }): Promise<string | undefined>`.

`OAuthCredentials` is `{ refresh, access, expires }` (expiry in ms), persisted in `~/.pi/agent/auth.json`. Users authenticate with `/login <provider-name>`. `refreshToken` receives an `AbortSignal` — pass it to blocking I/O and call `signal.throwIfAborted()` early.

## Custom Streaming

Implement `streamSimple(model, context, options?)` with a normalized `TranscriptContext`: read prompt/tools with `getCurrentSystemPrompt(context.messages)` and `getCurrentTools(context.messages)`, or use `collapseSystemMessages(context)` for transports that cannot represent mid-conversation updates. Do not read removed `context.systemPrompt`/`context.tools`. Return an `AssistantMessageEventStream` from `createAssistantMessageEventStream()`. Initialize an `AssistantMessage` (`role`, `content: []`, `api`, `provider`, `model`, zeroed `usage`, `stopReason: "pending"`, `timestamp`), then:

1. `stream.push({ type: "start", partial: output })`
2. Content events, tracking `contentIndex` per block: `text_start`, `text_delta`, `text_end`, `thinking_start`, `thinking_delta`, `thinking_end`, `toolcall_start`, `toolcall_delta`, `toolcall_end`
3. `stream.push({ type: "done", reason, message })` or `{ type: "error", reason, error }`, then `stream.end()`

`stopReason: "pending"` marks the partial message; set a terminal reason before pushing `done` (throw for `"error"`/`"aborted"`). Content/start events carry `partial` with the current `AssistantMessage` state; terminal events instead carry `message` or `error` — mutate `output.content` as data arrives and pass `output`. Tool calls accumulate JSON deltas, parse into `{ id, name, arguments }`, and finish with `toolcall_end` carrying the full `toolCall`. Update usage from the API response and call `calculateCost(model, output.usage)`. Register with `streamSimple` on the provider config.

Reference implementations live in 

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

