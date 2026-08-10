# Changelog

All notable BerryBrain changes are documented here.

## 1.3.0 - 2026-08-08

### Added

- Exclusive Cloud XOR Local AI configuration with provider presets, normalized model loading,
  and explicit generation, embedding, Judge, and HippoRAG slots.
- Persistent grounded Ask Flow with ordered evidence, isolated sessions, cancellation, and
  graph inference continuation.
- Global Check Online research runs with progress, cancellation, SSRF protection, untrusted
  evidence storage, and review before promotion.
- Semantic graph profiles, stable clusters, accessible topic colors, reserved vault namespaces,
  pending-state styling, homonym separation, and explainable node analysis.
- Progressive graph nodes/edges/deltas, layout worker, canvas level-of-detail, and a browser
  stress gate for 10,000 nodes and 40,000 edges.
- Operational HippoRAG worker integration for index, delete, reconcile, and rebuild jobs.

### Changed

- Enabled SQLite WAL, a 30-second busy timeout, and per-connection foreign keys so
  authenticated reads remain available while the worker persists graph updates.
- Preloaded the critical Settings and Graph panels after workspace hydration to keep
  their first interaction within the release performance budget.
- Rebuilt graph node details around evidence, provenance, Ask, analysis, review, and actions.
- Reorganized Settings and mandatory onboarding for non-technical users while preserving
  technical health and provider controls.
- Graph scan now returns canonical rebuilt state instead of waiting for a delayed worker pass.
- Note-bound jobs follow stable note IDs across renames and reject changed content, eliminating
  false HTTP 404/provider failures.
- Backup metadata now derives note/job counts from the exported tables and is checksum verified.
- Updated FastAPI/HippoRAG runtime packages, PostCSS, NanoID, brace-expansion, and js-yaml to
  close current dependency advisories.

### Verification

- 352 API tests plus 55 subtests, 44 Worker tests, and 7 HippoRAG tests.
- 43 Playwright E2E checks including accessibility, mobile, public/authenticated route budgets,
  graph workflows, onboarding, Settings, Flow, research, and 10k graph stress.
- 5,000-node/20,000-edge API graph gate: p95 2.54 s, 11.3 MB payload, 82.1 MB peak memory.
- Semantic Recall@10/MRR/NDCG@10 of 1.0; cognitive and insight maturity gates pass.
- Ruff, ESLint, TypeScript, production build, architecture, security, dependency, container,
  backup/restore, migration, SBOM, and runtime smoke gates are release requirements.

## 1.2.0 - 2026-07-29

### Added

- Capability-based Model Router and invocation ledger for generation, embeddings, Judge, and
  retrieval workloads.
- Deterministic, single-model, and committee RAG Judge modes with calibration evidence.
- Optional HippoRAG sidecar foundation and RRF retrieval across lexical, vector, and graph data.
- Provider dropdowns with automatic endpoint presets and normalized cloud model discovery.
- User-focused graph sidebar, Ask emphasis, expanded Settings, default local/dev owner, and
  updated public landing/docs.

### Changed

- Consolidated provider health, privacy consent, provenance, and model selection in Settings.
- Hardened release images, dependency pins, SBOM/provenance workflows, and default-owner
  production blocking.

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

- 278 API tests plus 55 subtests.
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
