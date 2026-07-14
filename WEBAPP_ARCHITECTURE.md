# BerryBrain Web App Architecture

Status: architecture baseline for the `webapp` branch. No hosted authentication or browser
knowledge persistence is considered production-ready until the security and recovery gates below
pass.

## Product modes

BerryBrain must keep two explicit deployment modes:

1. **Self-hosted** — the existing FastAPI, worker, SQLite/Postgres, vault, and local owner account.
2. **Hosted web app** — Netlify serves the Next.js frontend; personal knowledge remains on the
   user's device unless the user deliberately exports or later enables an encrypted sync service.

The hosted mode must not silently fall back to a server database for notes, attachments, graph
content, embeddings, prompts, or provider keys.

## Non-negotiable storage decision

Browser storage is viable for a local-only knowledge workspace, with hard limits:

- Use **OPFS** for Markdown, attachments, and encrypted archive blobs.
- Use **IndexedDB** for metadata, graph records, job state, retrieval indexes, and migrations.
- Use `navigator.storage.persist()` and show whether durable storage was granted.
- Use `localStorage` only for non-sensitive UI preferences. Never store passwords, session tokens,
  provider keys, note content, recovery codes, or encryption keys there.
- Encrypt sensitive browser records with Web Crypto AES-GCM. Derive wrapping keys with a reviewed,
  memory-hard KDF; maintain format and migration versions.
- Provide encrypted export/import and scheduled backup reminders.
- Detect quota pressure, failed writes, private browsing, unsupported OPFS, eviction risk, and
  partial migrations before accepting writes.

Browser persistence is device- and origin-bound. Clearing site data, browser eviction, changing
origin, or losing the device can permanently remove local knowledge. Email recovery cannot recover
browser-only notes. Cross-device recovery requires user-controlled encrypted backup or an optional
zero-knowledge sync service in a later phase.

## Account data reality

Login, email confirmation, 2FA, password recovery, sessions, abuse prevention, and account deletion
cannot be implemented without persistent authentication state. A static Netlify site and Umbler
SMTP alone are insufficient. Umbler sends email; it is not an authentication database.

Hosted mode may store only this minimal control-plane data:

- normalized email and verification state;
- password hash, never the password;
- encrypted TOTP secret and hashed recovery codes;
- hashed email verification and recovery challenges with expiry and attempt counters;
- hashed sessions, device label, creation, expiry, revocation, and last-use metadata;
- security audit events and rate-limit state with short retention;
- privacy consent version and account deletion state.

No notes or cognitive data belong in this account store. The UI and privacy policy must disclose the
minimal account metadata before signup.

## Recommended runtime

- Netlify: static/SSR frontend and narrowly scoped server functions.
- Authentication API: reuse the reviewed BerryBrain FastAPI security core, deployed on a runtime
  with stable secrets and a transactional Postgres database. Do not place SMTP or database secrets
  in the browser bundle.
- Email: Umbler SMTP over TLS from the authentication API only.
- Knowledge runtime: Web Workers for parsing, graph operations, embeddings where supported, and
  IndexedDB/OPFS access through one versioned repository layer.
- AI: bring-your-own-provider key encrypted locally. Prefer direct provider calls only where CORS
  and provider policy allow it; otherwise use an explicit stateless relay that disables body logs
  and never persists prompts or keys.

## Authentication controls

- Argon2id password hashing with calibrated memory/time parameters and automatic rehashing.
- Password length and compromised-password checks; no arbitrary composition rules.
- Generic signup, login, resend, and recovery responses to prevent account enumeration.
- One-time, hashed, expiring email confirmation and recovery tokens.
- TOTP authenticator 2FA with QR setup, confirmation challenge, recovery codes, replay prevention,
  and step-up authentication for destructive actions.
- Email OTP is recovery/verification fallback, not the preferred second factor.
- HttpOnly, Secure, host-only, SameSite cookies; session rotation after login and 2FA.
- CSRF tokens bound to the session for every state-changing request.
- Progressive per-account and per-network rate limits, exponential delays, lockout notifications,
  challenge escalation, and short-retention abuse telemetry.
- Session/device list, revoke-one, revoke-all, password-change revocation, and idle/absolute expiry.
- Reauthentication for email, password, 2FA, export, and account deletion changes.
- Constant-time secret comparisons and transaction-safe challenge consumption.

## Web security controls

- Strict CSP with nonces/hashes; no `unsafe-eval`; smallest possible `connect-src` allowlist.
- HSTS, `frame-ancestors 'none'`, `X-Content-Type-Options`, strict referrer policy, and restrictive
  permissions policy.
- Validate redirects and origins; reject malformed hosts and cross-origin credential requests.
- Escape rendered Markdown, sanitize HTML, reject dangerous attachment previews, and isolate PDFs,
  images, audio, and video in sandboxed viewers.
- Validate request size, MIME and file signatures; quarantine unsupported active content.
- No secrets in `NEXT_PUBLIC_*`, source maps, logs, analytics, error reports, URL parameters, or
  client-side build artifacts.
- Dependency pinning, lockfile review, secret scanning, SAST, dependency review, SBOM, signed release
  artifacts, and automated security updates.
- Third-party scripts stay outside the knowledge workspace. The authenticated app uses a native
  Ko-fi link; the public site may load the Ko-fi widget. Google Analytics runs only on public routes,
  only after consent, with advertising signals disabled.
- Treat interception proxies as clients, not special attack classes. Enforce authorization,
  validation, replay resistance, rate limits, and audit controls server-side.

## Privacy and analytics

- Official Google Analytics property: `G-36YL9QLC5K`.
- Self-hosted analytics default: disabled. Operators may set
  `NEXT_PUBLIC_GOOGLE_ANALYTICS_ID` for their own property.
- No note titles, paths, search terms, graph questions, provider names, emails, user IDs, or content
  in analytics events.
- Consent must be explicit, revocable, versioned, and independent from product access.
- Publish retention, subprocessors, legal basis, data-subject request, deletion, and breach handling
  details before hosted signup opens.

## Delivery phases

### Phase 0 — Boundaries and threat model

- [x] Create `webapp` from published `origin/main`.
- [x] Define self-hosted and hosted modes.
- [x] Reject `localStorage` as the knowledge database.
- [x] Define minimal account metadata and no-knowledge-data boundary.
- [ ] Produce STRIDE/LINDDUN threat models and data-flow diagrams.
- [ ] Approve retention periods, subprocessors, and incident owner.

### Phase 1 — Browser knowledge repository

- [x] Versioned IndexedDB repository and migration boundary.
- [ ] OPFS attachment repository.
- [x] Transactional note writes.
- [ ] Transactional graph writes with crash recovery.
- [ ] Encryption envelope, key lifecycle, migration tests, and lock screen.
- [x] Quota and persistent-storage diagnostics.
- [ ] Eviction, private-mode, and cross-browser support diagnostics.
- [x] Complete backup/export/import with SHA-256 corruption checks.
- [ ] Optional encrypted backup envelope and key recovery design.
- [ ] Web Worker pipeline and deterministic migration fixtures.

### Phase 2 — Hosted account control plane

- [ ] Transactional account schema and migration process.
- [ ] Signup, generic email confirmation, login, logout, and session lifecycle.
- [ ] Umbler SMTP adapter with TLS, retry, idempotency, and redacted logs.
- [ ] TOTP 2FA, recovery codes, step-up auth, and secure reset.
- [ ] Progressive rate limits, enumeration resistance, audit events, and alerts.
- [ ] Account privacy/settings screen, export, revoke sessions, and deletion workflow.

### Phase 3 — Hosted cognitive runtime

- [ ] Browser parser, graph store, retrieval index, and jobs state machine.
- [ ] Local/provider model router with explicit data-egress confirmation.
- [ ] No-log stateless relay only where direct provider access is impossible.
- [ ] Explainable insights and graph inference using local evidence.
- [ ] Performance budgets and background cancellation/recovery.

### Phase 4 — Security and release gates

- [ ] Unit, integration, browser E2E, migration, and storage-failure suites.
- [ ] Authentication abuse tests, CSRF, XSS, IDOR, replay, fixation, and race tests.
- [ ] CSP/headers tests and proof that third-party scripts cannot access the workspace.
- [ ] Secret scan, SAST, dependency review, SBOM, container scan, and signed artifacts.
- [ ] Independent security review and remediation before public hosted accounts.
- [ ] Restore and deletion drills with published evidence.

## Definition of ready

Hosted BerryBrain is ready only when account recovery works without exposing knowledge data, local
knowledge survives tested reload/crash/migration scenarios, encrypted backups restore cleanly,
third-party scripts cannot execute in the workspace, all authentication abuse tests pass, and the
privacy UI truthfully describes every persisted field and external data flow.
