---
id: sciref-pi-agent-pi-mcp-adapter
name: "Scientific Ref: pi-mcp-adapter Package"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (pi-agent): pi-mcp-adapter Package"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "agent mcp adapter"
  - "pi-mcp-adapter package"
keywords:
  - "agent"
  - "mcp"
  - "adapter"
  - "specialized"
  - "scientific"
  - "reference"
  - "package"
---

# pi-mcp-adapter Package

Source: https://pi.dev/packages/pi-mcp-adapter

Reviewed against Pi 0.99.2 and the package versions listed in `../SKILL.md` on 2026-09-30.

MCP adapter extension for Pi. Instead of loading hundreds of tool definitions upfront, it exposes one `mcp` proxy tool (~200 tokens) that discovers and calls tools on demand. Servers connect lazily and disconnect when idle; tool metadata is cached to disk so search/describe work offline.

```bash
pi install npm:pi-mcp-adapter
```

Version 4.0.0 was reviewed with Pi 0.99.2. Restart Pi after installation. Native Pi owns `/mcp` and `mcp.json`; the adapter uses `/mcp-adapter` and `mcp-adapter.json`. `/mcp` is an adapter alias only without native MCP. On first run the adapter reads standard MCP files automatically. If you only have host-specific configs (Cursor, Claude Code, Codex, …), run `/mcp-adapter setup` to adopt them, or `pi-mcp-adapter init` to scan and add compatibility imports to the Pi agent dir config.

## Configuration Files

Precedence, lowest to highest:

1. `~/.config/mcp/mcp.json` — user-global shared
2. `~/.agents/mcp.json` — user-global tool-agnostic
3. `~/.agents/mcp/mcp.json` — user-global tool-agnostic
4. `<Pi agent dir>/mcp-adapter.json` — Adapter global override (`~/.pi/agent/mcp-adapter.json`, or `$PI_CODING_AGENT_DIR/mcp-adapter.json`)
5. `.mcp.json` — project-local shared (preferred for projects)
6. `.pi/mcp-adapter.json` — Adapter project override

```json
{
  "mcpServers": {
    "chrome-devtools": { "command": "npx", "args": ["-y", "chrome-devtools-mcp@1.6.0"] }
  }
}
```

Host-specific configs are detected but **not** loaded automatically, and the normal `/mcp-adapter` panel does not scan them while `settings.hostConfigDiscovery` is `"off"` (the default). Opt in with `"on"` (or `pi-mcp-adapter init --discover-host-configs`); `"prompt"` detects without activating. Host configs sit below every shared and Pi-owned source.

Import specific host formats explicitly with `"imports": ["cursor", "claude-code", "claude-desktop", "opencode", "vscode", "windsurf", "codex"]`.

### Agent Plugins

List [Agent Plugins](https://agent-plugins.org/) package directories in `settings.agentPluginPaths` to load their MCP servers:

```json
{ "settings": { "agentPluginPaths": ["./plugins/acme-tools"] }, "mcpServers": {} }
```

Each directory needs a valid Agent Plugins 1.0 `plugin.json`; a root `mcp.json` there contributes `mcpServers` entries prefixed `<plugin>__<server>`. The loader uses the transport declared by each server `type` and skips invalid entries without blocking others. For stdio plugin servers, `${PLUGIN_ROOT}` and `${PLUGIN_DATA}` expand only in `args`, `env`, and `cwd`; both are set for the child process and plugin data is stored under the Pi agent directory. The adapter reads shared `.mcp.json`/`~/.config/mcp/mcp.json` plus adapter-owned overrides. It never reads native Pi global/project `mcp.json`.

`/mcp-adapter disable <server>` / `/mcp-adapter enable <server>` persist only the `disabled` field into `.pi/mcp-adapter.json` (never rewriting the source file or copying credentials); run `/reload` to apply. The manual equivalent is `{ "disabled": true }` in any MCP config.

### SDK Configuration

```ts
import { createMcpAdapter } from "pi-mcp-adapter";
const extension = createMcpAdapter({ config: { mcpServers: { docs: { url: "https://mcp.example.com/mcp", lifecycle: "eager" } } } });
```

A supplied `config` is a complete isolated snapshot — never merged with files, imports, or `--mcp-config`, and cloned per adapter/session. Status, reconnect, explicit `/mcp-auth <server>`, proxy calls, and direct tools still work; setup and no-argument auth/status panels report the limitation. With `configPath` and no `config`, normal file merging applies and that path outranks argv and `--mcp-config`. The package ships TypeScript source, so standalone Node processes need a TS-capable loader (e.g. `node --import tsx`).

OAuth credentials are stored in the OS credential store keyed by configured server name, with URL binding so credentials cannot be reused for a different server URL. `settings.oauthDir` / `MCP_OAUTH_DIR` are legacy plaintext `tokens.json` import locations only.

Cooperating Pi extensions can reuse URL-bound tokens through the public `pi-mcp-adapter/oauth` subpath (`getMcpOAuthTokensForUrl(server, url)`, `updateMcpOAuthTokensForUrl(server, url, tokens)`, plus a status helper). The async read path applies the adapter's refresh logic first. It exposes token read/update only — never client registration secrets, PKCE verifiers, or OAuth state — and keeps secure-store storage, URL binding, refresh persistence, chunk handling, legacy import, and fail-closed credential-store errors.

## Server Options

| Field | Description |
|---|---|
| `command`, `args` | stdio transport; mutually exclusive with `url` and `socket` |
| `socket` | `rmcp-mux` Unix socket path; supports `${VAR}`, `$env:VAR`, `~` |
| `env`, `cwd` | Interpolation supported; an `env` value starting with `!` runs a command at connect (`!!` escapes) |
| `url`, `headers` | StreamableHTTP with SSE fallback; interpolation supported, missing URL vars fail before any request |
| `auth` | `"bearer"` or `"oauth"` |
| `oauth.*` | `grantType` (`authorization_code` default, or `client_credentials`), `clientId` (MCP 2026 prefers pre-registered clients or Client ID Metadata Documents; Dynamic Client Registration is the fallback when omitted), `clientSecret`, `scope`, `redirectUri` (exact localhost callback for pre-registered clients), `clientName`, `clientUri` (defaults to the host manifest's `piConfig.clientUri`, omitted under a rebranded host), `logoUri` (absolute `http(s)` URL, RFC 7591 `logo_uri`), `authorizationParams` (extra authorization-URL parameters; flow-owned ones such as `client_id`, `redirect_uri`, `scope`, `state`, `code_challenge`, `response_type`, `resource` cannot be overridden), `skipIssuerMetadataValidation` |
| `bearerToken` / `bearerTokenEnv` | Token or env var name; interpolation and `!command` supported |
| `lifecycle` | `"lazy"` (default), `"eager"`, `"keep-alive"`, `"lazy-keep-alive"` |
| `idleTimeout` | Minutes before idle disconnect (overrides global) |
| `requestTimeoutMs` | Per-server request timeout; omitted or `<= 0` uses the MCP SDK default |
| `protocolVersion` | `"legacy"` (default), `"auto"`, or `"2026-07-28"` — modern negotiation is opt-in |
| `exposeResources` | Expose MCP resources as tools (default `true`) |
| `directTo

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

