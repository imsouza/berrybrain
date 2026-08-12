# BerryBrain security and trust model

## Scope and assumptions

BerryBrain is a local-first, single-owner, self-hosted application. Markdown and original attachments are the primary user assets. The Web, API, Worker, SQLite database, configured model providers, reverse proxy, and host filesystem form separate trust boundaries.

The repository is public. Security must depend on runtime secrets and explicit authorization, never on hidden source code. The default deployment must not expose the API or vault directly to the internet.

## Authorization matrix

| Surface | Public | Authenticated owner session | Worker bearer token | Maintenance owner |
|---|---:|---:|---:|---:|
| Landing, login, setup, health | Read | Read | Read | Read |
| Notes, graph, insights, reviews | No | Read/write | Read/write for jobs | Read/write |
| Settings without secrets | No | Read/write | Read | Read/write |
| Provider secrets | No | Write; masked on read | Read only through protected config endpoint | Read/write |
| Backups and restore | No | No | No | Read/write |
| Account and sessions | Own account only | Read/write | No | Recovery operations |
| Security audit | No | Own events where exposed | No | Read |

The current maintenance routes use the configured owner email as a compatibility boundary. They are not a multi-tenant administration model.

## Threats and controls

| Threat | Primary control | Verification |
|---|---|---|
| Credential stuffing and brute force | Argon2id, per-IP/email failure counters, lockout, OTP attempt limits | API security tests |
| Session theft | Hashed session tokens, HttpOnly cookie, expiry, revocation, secure-cookie production setting | Auth integration tests |
| CSRF | SameSite cookies, origin allowlist, double-submit CSRF token on account/maintenance mutations | Security tests |
| Cross-site scripting from Markdown | ReactMarkdown without raw HTML execution and restrictive CSP | Web build and browser tests |
| Host/path traversal | Resolved vault boundary checks and attachment filename validation | Attachment and vault tests |
| Malicious attachment instructions | Untrusted-content policy on every model call; attachments are evidence, never instructions | AI content-safety tests |
| Silent cloud disclosure | Cloud generation and embeddings require explicit `remote_content_consent` | API and Worker tests |
| Provider/key leakage | Secrets masked from browser reads, excluded from backup exports, bearer headers never logged | Settings/backup tests and review |
| Corrupt or malicious backup | Safe backup IDs, manifest path validation, SHA-256 before restore, schema compatibility check | Backup corruption tests |
| Supply-chain vulnerability | Immutable Docker builds, Trivy gates, generated SPDX SBOM | Container CI |
| Compromised extractor | Fixed executable allowlist, no shell, timeout, bounded output, vault-contained input | Attachment processing tests |
| Future-schema data loss | Startup blocks databases newer than the running binary | Schema migration tests |

## Residual risks

- Tesseract, Whisper, FFmpeg, model runtimes, and reverse proxies are external components and need host-level patching.
- The optional extractor subprocesses are resource-bounded by timeout and fixed invocation, but are not yet isolated in a separate container or OS sandbox.
- Image signing requires release identity and registry configuration; local images are not automatically signed.
- A host administrator can read the vault, SQLite file, environment variables, and process memory. BerryBrain does not defend against a fully compromised host.
- Legacy backups without a manifest can be restored only as explicitly reported, unverified backups.

## Operational requirements

1. Replace development session/API secrets before non-local deployment.
2. Terminate TLS at the reverse proxy and enable secure session cookies.
3. Bind API and model services to private interfaces.
4. Keep cloud consent disabled unless the owner accepts sending selected content to the configured provider.
5. Keep offline copies of checksummed backups and test restore after upgrades.
6. Review security audit events after lockouts, password resets, restore, or provider changes.
