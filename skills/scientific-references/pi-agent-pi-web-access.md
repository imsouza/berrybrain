---
id: sciref-pi-agent-pi-web-access
name: "Scientific Ref: pi-web-access Package"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (pi-agent): pi-web-access Package"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "agent web access"
  - "pi-web-access package"
keywords:
  - "agent"
  - "web"
  - "access"
  - "specialized"
  - "scientific"
  - "reference"
  - "package"
---

# pi-web-access Package

Sources: [official package](https://www.npmjs.com/package/pi-web-access/v/0.35.0), [maintainer documentation](https://github.com/nicobailon/pi-web-access).

Reviewed the published 0.35.0 source and README with Pi 0.99.2 on 2026-09-30. Install with `pi install npm:pi-web-access`. External searches, authenticated extraction, model summaries, and video/cloud PDF conversion below are illustrative; this review did not spend provider credits or access browser cookies.

The package provides web search, bounded content extraction, source-evidence artifacts, GitHub views, PDF conversion, and video analysis. Keyless search is available through Exa MCP; OpenAI can reuse Pi's Sign in with ChatGPT credentials (or legacy Codex auth). DuckDuckGo is keyless but explicit-only. Remote services may rate-limit or change availability.

## Tool activation

`toolActivation: "auto"` exposes only `web_enable` at the start of a new session when the model supports dynamic tool addition; otherwise tools register eagerly. `"dynamic"` forces activation, and `"eager"` exposes the full tool set. Continued sessions retain the activation state recorded in their transcript. Discover/enable the tools before calling the examples below.

## Search and evidence

```javascript
web_search({ query: "Pi extension API", workflow: "none" })
web_search({ queries: ["query one", "query two"], workflow: "auto-summary" })
web_search({ query: "recent changes", numResults: 10, recencyFilter: "week" })
web_search({ query: "...", domainFilter: ["github.com", "-old.example.com"], provider: "openai" })
web_search({ query: "...", provider: ["brave", "exa"] })
source_check({ claim: "The API supports streaming", queries: ["API streaming documentation"],
  fetchContent: true, domainFilter: ["docs.example.com"] })
```

`query`/`queries` select the questions; `numResults` defaults to 5 and is capped at 20. `recencyFilter` accepts `day`, `week`, `month`, `year`; prefix a `domainFilter` entry with `-` to exclude. Additional options include `provider`, `includeContent`, `workflow`, and `proxy`.

**The fresh-install workflow default is `none`**: bounded source results return directly, with full content stored for retrieval, without opening the curator or making an extra summary-model call. `summary-review` opens the curator and drafts a summary; `auto-summary` drafts one without the curator. The search provider itself may still use an LLM.

`auto` chooses available providers: configured SearXNG is preferred; OpenAI precedes Exa with suitable ChatGPT login, while Exa precedes API-key OpenAI. Use `searchRouting.providers` for a controlled order instead of depending on the changing default chain. Named providers are strict. Provider arrays run concurrently and cannot contain `auto` or `all`. `all` runs every eligible provider, preserves successful per-provider answers, deduplicates sources, and keeps failures as diagnostics. It can consume multiple configured providers' credits.

In 0.35.0, explicit-only providers excluded from automatic selection and `all` include `parallel-mcp`, `duckduckgo`, `kimi`, `anysearch`, `xcrawl`, `valyu`, `xai`, `mistral`, `brightdata`, `serpbase`, `serpapi`, `serper`, `serply`, `you`, `baizhi`, and `zai`. Browser-cookie access alone does not opt Gemini into `all`. Consult the installed README for each provider's credentials and account eligibility; commercial pricing is not pinned here.

`source_check` gathers passages for **manual semantic review**, not automated fact verification. Its schema allows `supported`, `contradicted`, `unclear`, and `missing-evidence`, but extraction itself produces `unclear` when passages exist or `missing-evidence` when none exist. Artifacts include SHA-256 content hashes, exact offsets, passage IDs, source-quality hints, and retained errors. At most 20 sources are retained and `fetchContent` fetches at most 5 pages. Retrieve the artifact using its `responseId`; paginated artifacts are JSON slices.

## Fetching and retrieval

```javascript
fetch_content({ url: "https://example.com/article" })
fetch_content({ urls: ["https://example.com/one", "https://example.com/two"] })
fetch_content({ url: "https://example.com/api", mode: "raw" })
fetch_content({ url: "https://example.com/guide", mode: "answer", prompt: "What are the installation steps?" })
get_search_content({ responseId: "returned-id", urlIndex: 0, offset: 30000 })
get_search_content({ responseId: "returned-id", url: "https://example.com/guide", findText: ["timeout", "retry"], findMode: "fuzzy" })
```

Modes are `readable` (default), `raw`, and `answer`. Answer mode requires `prompt`; its model order is per-call `answerModel: "provider/model-id"`, configured `fetch.answerProvider` + `fetch.answerModel`, then the active enabled Pi model. It sends fetched text to that model and may incur charges. For PDFs it answers from extracted Markdown, while retaining both the saved file and original extraction.

`fetch.defaultMode` and the nonempty `fetch.allowedModes` list constrain defaults and accepted requests; the default must be allowed. A disabled mode fails before I/O, without substitution. Raw mode uses direct HTTP only, preserves textual bodies including non-2xx responses, reports status in details, and skips specialized source handlers, readability, and hosted fallbacks. Raw/direct-image requests use SSRF checks, hostname policy, redirect checks, timeout, and a 5 MB streamed-response limit. Readable extraction recognizes Cloudflare challenge pages; raw mode preserves them.

`fetch.timeout` is seconds (default 30) for direct HTTP and Jina fallback, not one universal deadline for every extractor. `maxInlineContentChars` defaults to 30,000 and caps at 200,000; it controls initial output and retrieval `limit`. `get_search_content` supports `query`/`queryIndex` for searches and `url`/`urlIndex` for fetched content. `findText` returns bounded matching passages, accepts `exact`, `case-insensitive` (default), or `fuzzy`, and cannot combine with `offset`/`limit`; matches cap at 20,000 characters.

Full content is cached under the Pi config directory in private `web-search-cache`, not embedded in the transcript. The cache expires after one hour and is bounded to 128 entries / 128 MiB, oldest first; POSIX permissions are 0700 for directories and 0600 for files. `PI_WEB_ACCESS_CACHE_ROOT` can isolate process caches. Answer-mode originals remain retrievable. Do not treat a cache ID as permanent evidence storage.

## Source

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

