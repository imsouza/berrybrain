---
id: sciref-markitdown-security
name: "Scientific Ref: Security and Privacy"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (markitdown): Security and Privacy"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "markitdown security"
  - "markitdown seguranca"
  - "security and privacy"
keywords:
  - "markitdown"
  - "security"
  - "seguranca"
  - "specialized"
  - "scientific"
  - "reference"
  - "privacy"
---

# Security and Privacy

MarkItDown is a converter, not a sandbox. It performs file and network I/O with the privileges of the current process and loads parser dependencies for complex, attacker-controlled formats.

## Threat Model

Treat all of these as untrusted unless provenance is established:

- Paths, filenames, and URIs supplied by users or agents
- Uploaded PDFs, Office files, archives, notebooks, images, audio, and EPUBs
- HTTP response headers and redirects
- Installed plugins
- Markdown produced from external documents
- LLM/OCR responses

Potential impacts include:

- Reading arbitrary local files
- Server-side request forgery (SSRF)
- Access to loopback services or cloud metadata
- Archive/decompression bombs and memory exhaustion
- Parser vulnerabilities
- Credential or document exfiltration to cloud/LLM providers
- Prompt injection carried through converted content
- Arbitrary Python execution through plugins

## API Risk Levels

| API | Input capability | Recommended use |
|---|---|---|
| `convert_local()` | Local path only | Trusted, allowlisted local files |
| `convert_stream()` | Caller-controlled bytes | Preferred for validated uploads |
| `convert_response()` | Existing HTTP response | After caller-enforced network policy |
| `convert_uri()` | `file:`, `data:`, `http:`, `https:` | Trusted and validated URI only |
| `convert()` | Dispatches across all of the above | Trusted polymorphic input only |

Use the narrowest API that satisfies the task.

## Local File Controls

Before `convert_local()`:

1. Resolve the candidate path and the approved root.
2. Confirm the resolved candidate remains under that root.
3. Reject symlinks when their semantics are not explicitly required.
4. Require a regular file; reject devices, FIFOs, sockets, and directories.
5. Enforce an extension/MIME allowlist.
6. Apply a maximum byte size before opening.
7. Open with the least-privileged process account.
8. Keep sensitive directories outside the process's readable namespace.

Do not build a path by concatenating an untrusted filename with a directory string.

The bundled batch and literature scripts use `convert_local()` and skip symlink inputs by default. Their type/size checks are input controls, not network enforcement: detected formats, nested archive members, or reviewed plugins can invoke external processing. For a strict offline run, deny network access at the process/container boundary.

## HTTP(S) and SSRF Controls

Do not pass a user-controlled URL directly to `convert()` or `convert_uri()`.

An application-controlled downloader should enforce all of the following:

- Permit only required schemes, preferably HTTPS.
- Reject embedded usernames/passwords and malformed authorities.
- Canonicalize internationalized hostnames.
- Resolve DNS and reject every loopback, private, link-local, multicast, reserved, unspecified, and metadata-service address in IPv4 and IPv6.
- Revalidate the destination on every redirect.
- Defend against DNS rebinding; validation before connection alone is insufficient.
- Disable ambient proxy/environment behavior unless it is an explicit part of policy.
- Use connect and read timeouts.
- Limit redirect count.
- Enforce `Content-Length` when present and a streaming byte limit regardless of the header.
- Limit decompressed size.
- Allowlist response MIME types.
- Verify TLS normally; never disable certificate verification.
- Avoid forwarding credentials across origins.
- Pass the validated `requests.Response` to `convert_response()`.

MarkItDown's own HTTP path calls a Requests session and buffers the complete response before parsing. It does not impose these application-level controls.

## `file:` and `data:` URIs

`file:` URIs can read local files the process user can read. Version 0.1.8 rejects UNC and Windows device paths in this URI path. MarkItDown permits an empty authority or `localhost`; this is not a path allowlist.

`data:` URIs can contain arbitrarily large base64 payloads. Base64 decoding allocates another buffer (normally smaller than the encoded text), and conversion can create additional copies.

Prefer `convert_local()` or a bounded `convert_stream()` path instead of accepting arbitrary URI strings.

## Streams and Memory

- `convert_stream()` copies a non-seekable stream completely into memory.
- `convert_response()` buffers the complete HTTP response.
- ZIP, large tables, base64 images, and generated Markdown can substantially expand data.
- `--keep-data-uris` preserves full embedded payloads and can expose hidden/sensitive data.

Set input, output, member-count, page-count, time, and memory limits outside MarkItDown.

## Archives

MarkItDown's ZIP converter iterates members and applies nested conversion. Before accepting an untrusted archive, enforce:

- Maximum compressed bytes
- Maximum total uncompressed bytes
- Maximum member count
- Maximum single-member bytes
- Maximum nested archive depth
- Compression-ratio threshold
- File-type allowlist
- Conversion timeout

MarkItDown does not turn an archive into a safe bundle merely because it processes members in memory.

## Parser Supply Chain

Use a pinned MarkItDown release:

```bash
uv pip install "markitdown[all]==0.1.8"
```

Relevant release history:

- 0.1.2 moved XML/OMML parsing to `defusedxml`.
- 0.1.3 required safe ExifTool usage at version 12.24 or later.
- 0.1.4 updated Mammoth and `pdfminer.six` for published vulnerabilities.
- 0.1.6 clarified the project's I/O security posture; 0.1.8 tightened `file:` URI paths.

For production:

- Lock transitive dependencies and retain hashes.
- Scan the environment and container image.
- Rebuild when parser security advisories are published.
- Test representative documents after upgrades.

## Plugins

Plugins are arbitrary Python code loaded through package entry points. They run in the same process and can access its files, network, environment, and credentials.

- Keep `enable_plugins=False` by default.
- Pin and review every plugin.
- Inspect install/build hooks and transitive dependencies.
- Run risky plugins in a sandbox with synthetic files.
- Do not install by hashtag or name similarity alone.

The official `markitdown-ocr` plugin still introduces external LLM calls and expands parser dependencies.

## External Processing Map

| Feature | What leaves the process | Destination |
|---|---|---|
| HTTP(S), RSS, Wikipedia, Bing | Request metadata; downloaded response returns | Requested host |
| YouTube conversion | Page and transc

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

