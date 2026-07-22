# Changelog

All notable BerryBrain changes are documented here.

## 1.1.0 - 2026-07-22

### Added

- Persisted graph inference with server-owned evidence and an idempotent **Create insight** flow.
- Model Router domain policy, privacy-preserving invocation ledger, provider retries,
  concurrency limits, circuit breaking, cancellation accounting, and Monitor diagnostics.
- Cognitive maturity endpoint and deterministic release gates for retrieval, insight quality,
  grounding, provenance, stale cleanup, graph idempotency, and diagnostic isolation.
- Large-graph projection benchmark covering 5,000 nodes and 20,000 edges.
- Cooperative cancellation for queued/running jobs and claim-scoped exactly-once Worker inbox.
- Queue SLO for pending age, stale running work, and dead letters, surfaced in Monitor.
- Atomic staged restore with schema upgrade, integrity checks, full-vault replacement, and
  coordinated database/vault rollback.
- Automated WCAG A/AA, keyboard, reduced-motion, LCP, CLS, transfer, and INP-candidate gates.
- Operations runbook covering checkpoint upgrades, backup verification, rollback, recovery,
  and incident triage.

### Changed

- Graph insight creation now queues durable projection instead of mutating the graph twice.
- Knowledge Insights reject system diagnostics, generic claims, unsupported hypotheses, and
  raw implementation data.
- Worker terminal messages require the active claim token; stale or duplicate messages cannot
  overwrite a newer claim.
- Graph reads avoid ORM hydration and no longer mutate state, reducing large-graph latency.
- Documentation now defines BerryBrain as hybrid RAG plus a persistent Knowledge Graph and
  Semantic Data Layer, and explicitly states that BerryBrain does not fine-tune models.
- Public Docs, FAQ, architecture diagrams, version metadata, and engineering evidence were
  aligned with the current implementation.

### Verification

- 276 API tests plus 51 subtests.
- 37 Worker tests.
- 26 production-browser tests.
- 81% branch coverage with a critical-module coverage gate.
- Ruff, formatting, progressive MyPy, ESLint, TypeScript, production build, and cognitive
  release gate pass locally.

### Known maturity gates

- Real 30-day insight usefulness outcomes are still required for a 100% cognitive claim.
- Manual screen-reader evidence, historical restore fixtures, external disaster recovery, and
  further legacy-boundary isolation remain engineering gates.

## 1.0.1 - 2026-07-14

### Changed

- Consolidated the self-hosted workspace, landing page, local owner setup, provider onboarding,
  graph interactions, documentation, and release presentation after the initial v1.0 tag.
- Published the stable self-hosted release status and follow-up fixes from the v1.0 review.

## 1.0.0 - 2026-07-14

### Added

- Chunk-based hybrid retrieval, embedding provenance, semantic and insight benchmarks.
- Canonical knowledge graph writes, evidence-bearing AI edges, deduplication, undo, list accessibility mode, and node/edge actions.
- Grounded cognitive reviews with scheduling and evidence validation.
- Cognitive attachments with content MIME detection, checksums, PDF page locations, Tesseract OCR confidence, Whisper timestamp adapter, extractor selection, and derived-data cleanup.
- Versioned additive schema migrations with future-schema startup blocking.
- Checksummed SQLite/vault backups, verified restore, JSONL portability exports, and GraphML.
- Explicit cloud-content consent and a shared prompt-injection trust policy.
- Managed API/Worker token rotation, secret redaction, and security audit documentation.
- Immutable API, Worker, and Web Docker build definitions with Trivy and SBOM CI steps.

### Changed

- Worker now starts in the default Compose stack.
- Progress uses the actual pipeline stages queued for a note.
- Fresh browser settings default to local providers; cloud processing requires explicit consent.
- Knowledge Insights exclude system diagnostics and require note/graph evidence.

### Removed

- Flashcard UI and flashcard-oriented review behavior. Reviews are evidence-grounded cognitive prompts.

### Known limitations

- Audio transcription requires an installed/configured local Whisper CLI.
- Extractor subprocesses are not yet isolated in a dedicated sandbox/container.

### Release evidence

- Protected CI and 12 consecutive green container smokes.
- Immutable AMD64/ARM64 API, Worker, and Web images on GHCR.
- Keyless OIDC signatures and SPDX JSON attestations verified with Cosign.
- Final audit and downloadable SBOMs published with the GitHub release.
