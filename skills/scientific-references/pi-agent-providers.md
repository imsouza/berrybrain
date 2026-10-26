---
id: sciref-pi-agent-providers
name: "Scientific Ref: Providers"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (pi-agent): Providers"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "agent providers"
  - "providers"
keywords:
  - "agent"
  - "providers"
  - "specialized"
  - "scientific"
  - "reference"
---

# Providers

Source: https://pi.dev/docs/latest/providers

Reviewed against Pi 0.99.2 and the package versions listed in `../SKILL.md` on 2026-09-30.

Pi supports subscription providers via OAuth and API-key providers via environment variables or `~/.pi/agent/auth.json`. Built-in catalogs ship with Pi; configured providers may refresh newer catalogs and cache them in `~/.pi/agent/models-store.json` for offline use.

## Subscription Providers

Run `/login` to choose the provider and one of its supported methods. Pi 0.99 adds Sign in with ChatGPT on `openai`; `openai-codex` remains a legacy provider. Other methods include Claude, GitHub Copilot, Meta Muse, xAI, OpenRouter, and Radius. `/logout` clears credentials. Tokens live in `auth.json` and auto-refresh.

- **OpenAI** Sign in with ChatGPT supersedes the legacy Codex login; check current account entitlements in the login flow.
- **Claude**: use the login flow offered by the installed provider and confirm current account eligibility and billing with Anthropic; subscription entitlement is not guaranteed by a successful token exchange.
- **GitHub Copilot**: Enter for github.com, or enter a GitHub Enterprise Server domain. "Model not supported" is fixed by enabling the model in VS Code Copilot Chat.
- **xAI**: `/login xai` → **Use a subscription**; `XAI_API_KEY` remains available under **Use an API key**.
- **OpenRouter**: `/login openrouter` → **Sign in with OpenRouter** runs a PKCE flow that mints a user-controlled API key billed from OpenRouter credits (it does not expire automatically). On remote/headless machines (e.g. over SSH) the browser cannot reach the loopback callback — paste the final redirect URL or the authorization code into the login prompt instead.
- **Radius**: a dynamic `pi-messages` gateway. `/login radius` stores OAuth tokens; the catalog refreshes independently into `models-store.json`. Custom Radius gateways can be declared in `models.json` with `"oauth": "radius"` plus a gateway `baseUrl`.

## API Key Providers

Set an environment variable before startup, or store a key with `/login`.

| Provider | Environment Variable | `auth.json` key |
|---|---|---|
| Anthropic | `ANTHROPIC_API_KEY` | `anthropic` |
| Ant Ling | `ANT_LING_API_KEY` | `ant-ling` |
| Azure OpenAI Responses | `AZURE_OPENAI_API_KEY` | `azure-openai-responses` |
| OpenAI | `OPENAI_API_KEY` | `openai` |
| DeepSeek | `DEEPSEEK_API_KEY` | `deepseek` |
| NVIDIA NIM | `NVIDIA_API_KEY` | `nvidia` |
| Google Gemini | `GEMINI_API_KEY` | `google` |
| Amazon Bedrock | `AWS_BEARER_TOKEN_BEDROCK` | `amazon-bedrock` |
| Meta | `META_API_KEY` | `meta` |
| TypeSafe classifiers | `TYPESAFE_API_KEY` | `typesafe` |
| Moonshot AI | `MOONSHOT_API_KEY` | `moonshotai` / `moonshotai-cn` |
| GitHub Copilot | `COPILOT_GITHUB_TOKEN` | `github-copilot` |
| Mistral | `MISTRAL_API_KEY` | `mistral` |
| Groq | `GROQ_API_KEY` | `groq` |
| Cerebras | `CEREBRAS_API_KEY` | `cerebras` |
| Cloudflare AI Gateway | `CLOUDFLARE_API_KEY` (+ `CLOUDFLARE_ACCOUNT_ID`, `CLOUDFLARE_GATEWAY_ID`) | `cloudflare-ai-gateway` |
| Cloudflare Workers AI | `CLOUDFLARE_API_KEY` (+ `CLOUDFLARE_ACCOUNT_ID`) | `cloudflare-workers-ai` |
| xAI | `XAI_API_KEY` | `xai` |
| OpenRouter | `OPENROUTER_API_KEY` | `openrouter` |
| Vercel AI Gateway | `AI_GATEWAY_API_KEY` | `vercel-ai-gateway` |
| ZAI Coding Plan (Global / China) | `ZAI_API_KEY` / `ZAI_CODING_CN_API_KEY` | `zai` / `zai-coding-cn` |
| OpenCode Zen / Go | `OPENCODE_API_KEY` | `opencode` / `opencode-go` |
| Radius | `RADIUS_API_KEY` | `radius` |
| Hugging Face | `HF_TOKEN` | `huggingface` |
| Fireworks | `FIREWORKS_API_KEY` | `fireworks` |
| Together AI | `TOGETHER_API_KEY` | `together` |
| Baseten | `BASETEN_API_KEY` | `baseten` |
| Kimi For Coding | `KIMI_API_KEY` | `kimi-coding` |
| MiniMax (Global / China) | `MINIMAX_API_KEY` / `MINIMAX_CN_API_KEY` | `minimax` / `minimax-cn` |
| Qwen Token Plan (existing catalog / Individual) | `QWEN_TOKEN_PLAN_API_KEY` | `qwen-token-plan` / `qwen-token-plan-individual` |
| Qwen Token Plan (China) | `QWEN_TOKEN_PLAN_CN_API_KEY` | `qwen-token-plan-cn` |
| Xiaomi MiMo | `XIAOMI_API_KEY` | `xiaomi` |
| Xiaomi MiMo Token Plan (CN / AMS / SGP) | `XIAOMI_TOKEN_PLAN_CN_API_KEY`, `XIAOMI_TOKEN_PLAN_AMS_API_KEY`, `XIAOMI_TOKEN_PLAN_SGP_API_KEY` | `xiaomi-token-plan-cn`, `-ams`, `-sgp` |

`qwen-token-plan-individual` uses the same international endpoint and `QWEN_TOKEN_PLAN_API_KEY` as `qwen-token-plan`, but limits the picker to models documented for Individual subscriptions; the older provider keeps its broader catalog for backward compatibility. With `auth.json`, store the credential under the provider you select — the environment variable is shared by both international providers.

Authoritative source: `packages/ai/src/providers/` and `packages/coding-agent/docs/providers.md` in `earendil-works/pi`.

## Auth File

`~/.pi/agent/auth.json` is created with `0600` permissions and takes priority over environment variables.

```json
{
  "anthropic": { "type": "api_key", "key": "sk-ant-..." },
  "openai": { "type": "api_key", "key": "sk-..." }
}
```

An API-key credential can carry provider-scoped environment values in an `env` object. These are used before process environment variables when resolving the credential key, provider/model headers, and provider configuration such as Cloudflare account IDs, Azure settings, Vertex project/location, Bedrock settings, `PI_CACHE_RETENTION`, and `HTTP_PROXY`/`HTTPS_PROXY`:

```json
{
  "cloudflare-ai-gateway": {
    "type": "api_key",
    "key": "$CLOUDFLARE_API_KEY",
    "env": {
      "CLOUDFLARE_API_KEY": "...",
      "CLOUDFLARE_ACCOUNT_ID": "account-id",
      "CLOUDFLARE_GATEWAY_ID": "gateway-id"
    }
  }
}
```

OAuth credentials are also stored here after `/login` and managed automatically.

## Key Resolution Syntax

```json
{ "type": "api_key", "key": "!op read 'op://vault/item/credential'" }
{ "type": "api_key", "key": "$MY_API_KEY" }
{ "type": "api_key", "key": "${KEY_PREFIX}_${KEY_SUFFIX}" }
{ "type": "api_key", "key": "$$literal-dollar" }
{ "type": "api_key", "key": "$!literal-bang" }
```

A leading `!` executes the whole value as a command and uses stdout (cached for the process lifetime). `$VAR`/`${VAR}` interpolate, including inside larger literals; `$FOO_BAR` is the variable `FOO_BAR`, so use `${FOO}_BAR` when `BAR` is literal. Missing variables leave the value unresolved. Plain uppercase strings such as `MY_API_KEY` are literals.

## Cloud Providers

**Azure OpenAI*

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

