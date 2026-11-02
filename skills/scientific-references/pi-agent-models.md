---
id: sciref-pi-agent-models
name: "Scientific Ref: Custom Models"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (pi-agent): Custom Models"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "agent models"
  - "custom models"
keywords:
  - "agent"
  - "models"
  - "specialized"
  - "scientific"
  - "reference"
  - "custom"
---

# Custom Models

Source: https://pi.dev/docs/latest/models

Reviewed against Pi 0.99.2 and the package versions listed in `../SKILL.md` on 2026-09-30.

Add custom providers and models through `~/.pi/agent/models.json` for Ollama, LM Studio, vLLM, SGLang, proxies, and custom endpoints.

## Minimal Local Example

```json
{
  "providers": {
    "ollama": {
      "baseUrl": "http://localhost:11434/v1",
      "api": "openai-completions",
      "apiKey": "ollama",
      "compat": {
        "supportsDeveloperRole": false,
        "supportsReasoningEffort": false
      },
      "models": [
        { "id": "llama3.1:8b" },
        { "id": "qwen2.5-coder:7b" }
      ]
    }
  }
}
```

Only `id` is required per model. The `apiKey` placeholder matters because Pi treats models as requiring auth before they appear in `/model`; keyless local servers should keep a dummy value, store a key via `/login`, or pass `--api-key`. Set `compat.supportsDeveloperRole: false` for OpenAI-compatible servers that reject the `developer` role, and `compat.supportsReasoningEffort: false` when `reasoning_effort` is unsupported. `compat` can be set at provider level (all models) or model level (override). The file reloads each time `/model` opens — no restart needed.

For `google-generative-ai` custom models, `baseUrl` is required (for example `https://generativelanguage.googleapis.com/v1beta`).

## Supported APIs

`openai-completions` (most compatible), `openai-responses`, `anthropic-messages`, `google-generative-ai`. Set `api` at provider level as the default, or per model to override.

## Provider Fields

`baseUrl`, `api`, `apiKey`, `oauth`, `headers`, `authHeader`, `models`, `modelOverrides`.

- `oauth`: dynamic OAuth provider type; currently `"radius"`, which requires the gateway `baseUrl`.
- `authHeader: true` adds `Authorization: Bearer <apiKey>`.
- `apiKey` is optional — omit it when auth comes from `/login`/`auth.json`/`--api-key`. Non-built-in providers with `models` need `baseUrl` and an `api` value at provider or model level. Without any auth, models load but stay unavailable in `/model` and `--list-models`.

`apiKey` and `headers` support command execution (`!command`, whole value), env interpolation (`$ENV` / `${ENV}`, works inside larger literals), escapes (`$$`, `$!`), and literals (plain uppercase strings are literals). Shell commands in `models.json` resolve at request time with no built-in TTL, stale reuse, or recovery — wrap slow or flaky secret commands yourself. `/model` availability checks use configured auth presence and do not execute shell commands.

## Model Fields

Required: `id`. Optional: `name` (defaults to `id`), `api`, `reasoning` (`false`), `thinkingLevelMap`, `input` (`["text"]` or `["text","image"]`), `contextWindow` (`128000`), `maxTokens` (`16384`), `samplingParams`, `cost` (zeros), `compat` (merged with provider `compat`).

`/model`, `--list-models`, and the footer display entries by model `id`; `name` is used for `--model` pattern matching and secondary detail text.

`cost` is per million tokens and supports request-wide input pricing tiers. A tier supplies a complete alternate rate set and applies to the whole request when `input + cacheRead + cacheWrite` exceeds `inputTokensAbove`; the highest matching threshold wins.

```json
{
  "cost": {
    "input": 5, "output": 30, "cacheRead": 0.5, "cacheWrite": 6.25,
    "tiers": [{ "inputTokensAbove": 272000, "input": 10, "output": 45, "cacheRead": 1, "cacheWrite": 12.5 }]
  }
}
```

## Sampling Parameters

`samplingParams` is a free-form object merged verbatim into every request body for that model, after the fields Pi sets itself — so its keys win, including over Pi's own `temperature`. Use it for sampling controls Pi does not model, such as llama.cpp `min_p` or vLLM `top_k`:

```json
{ "id": "deepseek-v4-flash",
  "samplingParams": { "temperature": 1.0, "top_p": 0.95, "top_k": 0, "min_p": 0.0 } }
```

Only OpenAI-compatible APIs apply it (`openai-completions`, `openai-responses`, `azure-openai-responses`); other APIs ignore it. Treat it as the single source of sampling truth for a model. In `modelOverrides`, `samplingParams` merges per key with the base model's value.

## Thinking Level Map

Keys are Pi levels: `off`, `minimal`, `low`, `medium`, `high`, `xhigh`, `max`. Maps may have holes. Values are tristate: omitted means standard levels through `high` use the provider default mapping while `xhigh`/`max` are unsupported; a string is sent to the provider; `null` marks the level unsupported so it is hidden/skipped/clamped away.

```json
{ "id": "deepseek-v4-pro", "reasoning": true,
  "thinkingLevelMap": { "minimal": null, "low": null, "medium": null, "high": "high", "xhigh": null, "max": "max" } }
```

Use `{ "off": null }` for models where thinking cannot be disabled. Older `compat.reasoningEffortMap` configs should move to model-level `thinkingLevelMap`.

## Overriding Built-in Providers

Base-URL-only overrides keep all built-in models and existing auth:

```json
{ "providers": { "anthropic": { "baseUrl": "https://my-proxy.example.com/v1" } } }
```

If `models` is included, built-in models are kept and custom models are upserted by `id` — a matching `id` replaces the built-in, a new `id` is added.

`modelOverrides` customizes built-in and matching extension-registered models without replacing the provider list. Supported per-model fields: `name`, `reasoning`, `thinkingLevelMap`, `input`, `cost` (partial), `contextWindow`, `maxTokens`, `samplingParams` (merged per key), `headers`, `compat`. Unknown model IDs are ignored; provider-level `baseUrl`/`headers` can be combined with it. If `models` is also defined, custom models merge after built-in overrides.

Example — opt a direct OpenAI GPT-5.6 model into the 1.05M context window (they default to `272000` to stay in the short-context pricing tier):

```json
{ "providers": { "openai": { "modelOverrides": { "gpt-5.6-sol": { "contextWindow": 1050000 } } } } }
```

## Anthropic Messages Compatibility Flags

`supportsEagerToolInputStreaming` (default `true`; `false` omits `tools[].eager_input_streaming` and sends the legacy fine-grained-tool-streaming beta header), `supportsLongCacheRetention` (default `true`, `cache_control.ttl: "1h"`), `sendSessionAffinityHeaders` (auto-detected), `supportsCacheControlOnTools` (default `true`), `forceAdaptiveThinking` (`thinking.type: "adaptive"` plus `output_config.effort`; built-in adaptive models set it automatically), `allowEmptySignature` (rep

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

