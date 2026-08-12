# BerryBrain Clean Architecture and Refactoring Plan

Status: active, incremental migration

Last updated: 2026-07-21

## Objective

Evolve BerryBrain into a maintainable modular monolith without breaking the public API,
SQLite data, Markdown vaults, Docker deployment, or worker compatibility. Refactoring is
performed by vertical slice: each changed behavior receives a domain rule, an application
boundary, adapters, contract tests, and observability before the next slice starts.

## Non-negotiable constraints

- Markdown files remain the portable source of user-authored knowledge.
- Existing SQLite databases migrate forward without destructive resets.
- Provider calls pass through the Model Router and preserve provider/model/prompt provenance.
- Knowledge claims require evidence. System diagnostics never become knowledge insights.
- HTTP routers do not own business rules or open hidden database sessions in migrated flows.
- Worker handlers are idempotent and safe to retry.
- Every migration remains deployable and backwards compatible.

## Target boundaries

Each bounded context follows these inward dependencies:

```text
Presentation (FastAPI / Next.js)
        |
        v
Application (use cases / ports / transactions)
        |
        v
Domain (rules / value objects / policies)
        ^
        |
Infrastructure (SQLAlchemy / vault / providers / vector stores)
```

Target contexts:

1. Identity and Settings
2. Vault and Attachments
3. Knowledge Base and Retrieval
4. Knowledge Graph
5. Graph Inference
6. Knowledge Insights
7. Jobs and Autopilot
8. Review and Learning
9. Backup and Portability
10. Observability and Diagnostics

## Engineering rules

- New domain modules may not import FastAPI, SQLAlchemy, filesystem, HTTP, or provider SDKs.
- Application modules depend on protocols, not concrete adapters.
- Infrastructure implements repositories and external-provider ports.
- Routes validate transport data and call one use case.
- Transactions commit once at the use-case boundary; an outbox records cross-context events.
- New files target 400 lines or fewer, functions 50 lines or fewer, and complexity 10 or less.
- New domain/application code requires 90% branch coverage; repository-wide target is 80%.
- Ruff, MyPy, ESLint, TypeScript, architecture tests, API tests, worker tests, and E2E are gates.
- Exceptions require a dated ADR with an owner and removal condition.

## Delivery phases

### Phase 0 - Safety baseline

- [x] Keep existing API routes and database tables compatible.
- [x] Add versioned schema migrations and compatibility diagnostics.
- [x] Maintain API, worker, web, security, and container CI workflows.
- [x] Add requirement IDs and a traceability matrix.
- [x] Establish cognitive and engineering scorecards.
- [ ] Raise repository-wide coverage gate from 60% to 80% in measured increments.
- [ ] Eliminate current ESLint warnings before enforcing zero-warning CI.

Exit: every subsequent change maps to a requirement and automated test.

### Phase 1 - Graph inference and knowledge insight slice

- [x] Persist every graph inference in `graph_inferences`.
- [x] Return an immutable `inferenceId` to the web client.
- [x] Create insights from persisted server records instead of browser JSON.
- [x] Convert insufficient evidence into an explicit `knowledge_gap`.
- [x] Block provider failures and incomplete executions from becoming knowledge.
- [x] Record provider, model, prompt version, evidence, routes, confidence, and timestamps.
- [x] Link the inference to the created insight and make repeated requests idempotent.
- [x] Register `INSIGHT_CREATED_FROM_INFERENCE` in Activity.
- [x] Add `Create insight` next to `Close` with loading, success, error, and disabled states.
- [x] Extract the inference-to-insight decision into a framework-free domain module.
- [x] Inject the database session for the migrated endpoints.
- [x] Add domain, integration, tamper-resistance, gap, and architecture tests.
- [ ] Replace direct graph expansion after insight creation with a transactional outbox event.
- [ ] Add Playwright coverage for the visible button states and graph refresh.

Exit: a saved inference is auditable and cannot be forged by client-supplied evidence.

### Phase 2 - Settings and Model Router

- [ ] Create `ModelCapability`, `ProviderPolicy`, and `RoutingDecision` domain types.
- [ ] Move provider selection, consent, health, timeout, and fallback into one application use case.
- [ ] Replace provider-specific branches in routers and jobs with a `ModelGateway` port.
- [ ] Persist each invocation with latency, outcome, prompt version, provider, model, and error class.
- [ ] Encrypt secrets at rest and keep secret values out of API responses and logs.
- [ ] Add provider contract tests for NIM, OpenAI-compatible APIs, and local adapters.
- [ ] Add circuit breaker, bounded retry, concurrency limit, and cancellation.
- [ ] Expose user-readable provider diagnostics in Monitor, not Knowledge Insights.

Exit: all AI execution is observable, policy-driven, and independently testable.

### Phase 3 - Knowledge Graph and Knowledge Insights

- [ ] Move canonical node/edge identity rules into the Graph domain.
- [ ] Introduce repository ports for nodes, edges, evidence, and graph snapshots.
- [ ] Enforce edge invariants: origin, reason, evidence, confidence, status, and provenance.
- [ ] Make node/edge confirmation, ignore, archive, merge, and delete transactional use cases.
- [ ] Route all graph writes through one canonical writer and event stream.
- [ ] Split technical diagnostics from knowledge insight generation at the domain boundary.
- [ ] Add insight usefulness feedback and expiry/recalculation policies.
- [ ] Benchmark edge precision and unsupported claims against versioned fixtures.
- [ ] Add property tests for deduplication, merge, and idempotent rebuilds.

Exit: graph state is deterministic, explainable, versioned, and reversible.

### Phase 4 - Knowledge Base and Retrieval

- [ ] Define `Document`, `Chunk`, `Embedding`, and `Citation` domain contracts.
- [ ] Make chunking deterministic by content hash and parser version.
- [ ] Add vector-store ports with SQLite fallback and Qdrant/Chroma adapters.
- [ ] Implement incremental index update, deletion, and recovery.
- [ ] Add hybrid retrieval fusion, reranking, diversity, and citation validation.
- [ ] Publish Recall@10 and MRR benchmarks using reproducible fixtures.
- [ ] Prevent stale chunks and embeddings from surviving note changes/deletes.
- [ ] Add attachment source locations to every citation.

Exit: clean-install indexing and retrieval quality are reproducible.

### Phase 5 - Vault and Attachments

- [ ] Isolate filesystem access behind a Vault port.
- [ ] Make note save atomic and distinguish persistence success from downstream job failure.
- [ ] Enforce attachment size/type/path controls before storage.
- [ ] Add extractor sandbox limits for CPU, memory, time, decompression, and output size.
- [ ] Complete PDF/OCR/image/audio/video transcription only after phases 1-4 pass their gates.
- [ ] Preserve page, timestamp, frame, and source-file evidence in chunks and graph nodes.
- [ ] Add malicious file, corrupt file, and large-file test fixtures.

Exit: every indexed attachment is safe, attributable, and removable.

### Phase 6 - Worker and Autopilot

- [ ] Reduce worker `main.py` to bootstrap, dispatch, and lifecycle management.
- [ ] Create one handler per job type with typed payloads.
- [ ] Add job idempotency keys, leases, heartbeats, cancellation, retry classes, and dead letters.
- [ ] Persist stage progress and user-readable outcomes.
- [ ] Use an outbox/inbox pair for API-worker consistency.
- [ ] Add crash/restart, duplicate delivery, provider timeout, and stale lease integration tests.
- [ ] Define queue SLOs and alert only on actionable conditions.

Exit: the pipeline resumes safely after interruption and never processes silently forever.

### Phase 7 - Web application

- [ ] Split Graph, Settings, Home, Editor, Insights, and Activity into feature modules.
- [ ] Generate a typed client from OpenAPI.
- [ ] Centralize HTTP auth, CSRF, timeouts, retries, error mapping, and cancellation.
- [ ] Remove direct `fetch` outside the client adapter.
- [ ] Remove direct `localStorage` outside a versioned persistence adapter.
- [ ] Use query caching/invalidation for graph, Home, Insights, and Activity consistency.
- [ ] Add runtime response validation for critical endpoints.
- [ ] Meet WCAG 2.2 AA keyboard, contrast, focus, reduced-motion, and screen-reader gates.
- [ ] Set performance budgets for LCP, INP, bundle size, and large graph rendering.

Exit: UI state reflects canonical server state and failures are actionable.

### Phase 8 - Security, backup, and release

- [ ] Complete threat models for self-hosted, reverse-proxy, and public-network deployments.
- [ ] Add rate limiting, lockout policy, session rotation, CSRF, CSP, and secure-cookie tests.
- [ ] Produce SBOM, signed images, provenance attestations, and pinned release dependencies.
- [ ] Test encrypted backup and restore across supported schema versions.
- [ ] Add secret scanning and a documented key-rotation incident procedure.
- [ ] Validate empty first-run state contains no personal vault, key, or user data.
- [ ] Run release smoke tests from a clean machine and a restored backup.

Exit: release is reproducible, recoverable, and has no critical/high open security findings.

## Refactoring order for legacy hotspots

1. `routers/settings.py` and provider configuration
2. `cognitive_layer.py` and graph inference
3. `routers/insights.py` and insight lifecycle
4. `second_brain.py` and graph generation
5. `services.py` graph/insight functions
6. worker `main.py`
7. web `graph-screen.tsx`
8. web Settings and Home screens

Each extraction must keep a characterization test around the old behavior, move one rule,
switch callers, and only then remove the legacy branch.

## Definition of done

A phase is complete only when code, migrations, tests, metrics, user-facing error states,
Activity events, documentation, rollback behavior, and clean-install validation are present.
Checkboxes are evidence markers, not estimates.
