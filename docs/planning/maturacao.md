# BerryBrain Maturation Plan

Status date: 2026-07-10

Goal: mature BerryBrain from a functional second-brain foundation into a reliable, evidence-based cognitive system.

## Phase 1 — Stabilization

- [x] Keep note save independent from secondary job failures.
- [x] Remove provider-config noise such as Ollama offline from Home attention alerts.
- [x] Ignore `.attachments` during vault note scans.
- [x] Remove `Delete Node` from Brain View actions.
- [x] Hide technical/system insights from Graph and Insights surfaces.
- [x] Add Settings maintenance actions.
- [x] Run full legacy cleanup on the active database.
- [x] Rebuild the graph from the current vault after cleanup.
- [x] Validate graph consistency after rebuild.

## Phase 2 — Knowledge Insights

- [x] Separate Knowledge Insights from System Diagnostics.
- [x] Reject insights based only on jobs, queue, provider, worker, pipeline, or raw JSON.
- [x] Humanize evidence in Graph, Insights, and note panels.
- [x] Queue all existing notes for reprocessing with the new insight prompt.
- [x] Add automated tests for technical insight rejection.
- [x] Add automated tests for graph-worthy insight requirements.
- [ ] Verify new insights include conclusion/hypothesis/premise/gap/action/graph impact.

## Phase 3 — Knowledge Graph

- [x] Persist graph nodes and graph edges in SQLite.
- [x] Keep node/connection actions scoped and auditable.
- [x] Add graph validation maintenance endpoint.
- [ ] Deduplicate all legacy concept/topic nodes.
- [ ] Ensure every visible edge has reason, evidence, confidence, status, provider/model.
- [ ] Ensure concepts are contextualized by AI, not only extracted headings/tags.
- [ ] Ensure Brain View shows useful edges after rebuild.

## Phase 4 — Knowledge Base

- [x] Add Cognitive Layer with Knowledge Base / Graph / Semantic Data separation.
- [x] Add Knowledge Base reindex maintenance endpoint.
- [x] Add note attachments with per-type MB limits.
- [x] Add Qdrant/Chroma real write integration with deterministic embedding payloads.
- [x] Add Qdrant/Chroma real read integration for graph/cognitive inference.
- [x] Keep SQLite/local lexical retrieval as fallback when an external vector store is missing or unavailable.
- [x] Add automated tests for Qdrant write, Qdrant read, Chroma read, and external fallback.
- [ ] Assimilate attachment text into the Knowledge Base.
- [ ] Add PDF/document text extraction.
- [ ] Add image OCR/vision metadata.
- [ ] Add audio/video transcription status and future processing hooks.

## Phase 5 — Worker And Autopilot

- [x] Make active job lookup tolerate duplicate jobs.
- [x] Add duplicate active job cleanup in maintenance validation.
- [x] Add stronger job idempotency by `type + note_path + content_hash`.
- [x] Add progress by note and by pipeline stage.
- [x] Add stuck-job detection and clear diagnostics.
- [x] Ensure failed optional jobs never break user-facing note save.

## Phase 6 — UI/Product Maturity

- [x] Keep Graph action labels in English.
- [x] Add Maintenance section to Settings.
- [x] Update guide text for current graph actions.
- [ ] Remove remaining legacy PT-BR UI strings from active English UI.
- [ ] Remove remaining flashcard/review UI surfaces and stale docs.
- [ ] Add clear empty states for no graph edges, no concepts, no insights, and no attachment processing.
- [ ] Add rebuild status/progress in Monitor.

## Phase 7 — Maintenance APIs

Implemented endpoints:

- [x] `POST /api/v1/maintenance/rebuild-brain`
- [x] `POST /api/v1/maintenance/cleanup-legacy-insights`
- [x] `POST /api/v1/maintenance/validate-graph`
- [x] `POST /api/v1/maintenance/reindex-knowledge-base`

Expected behavior:

- Cleanup archives technical insights and hides their graph nodes.
- Validation deletes orphan edges, ignores self/duplicate edges, and marks duplicate active jobs failed.
- Rebuild scans the vault, queues note processing, expands graph, reindexes KB, and validates graph.
- Reindex recomputes current Knowledge Base indexing status without deleting notes.

## Phase 8 — Integration And Automated Tests

- [x] Fix API integration test database isolation so routers use the test `SessionLocal` consistently.
- [x] Run focused integration tests for notes, jobs, insights, graph, settings, backups, and auth.
- [x] Run full API test discovery.
- [x] Validate Cognitive Layer import/runtime inside the API container.
- [x] Run web TypeScript typecheck inside the web container.
- [x] Add HTTP contract tests for maintenance cleanup, validation, reindex, and rebuild endpoints.
- [ ] Add end-to-end browser tests for Home, Graph, Settings, Insights, and note attachments.
- [x] Add worker integration tests against a disposable database.
- [x] Add fixture-based tests for a realistic vault with at least 10 notes and explainable graph edges.
- [x] Add regression tests proving ignored/archived technical insights never return to Home, Graph, or `/insights`.

## Acceptance Criteria

- Home AI Insights contains only learner-facing knowledge insights.
- Monitor/Activity contains system diagnostics.
- Graph contains no visible `Pipeline Bottleneck`, `jobsByType`, `semantic_data`, `graphSummary`, or `GENERATE_NOTE_TITLE`.
- Graph has visible note nodes, concept/context/topic nodes, and explainable edges after rebuild.
- Every visible AI insight has evidence, confidence, provider/model, suggested action, and graph impact.
- Settings can rebuild, validate, cleanup, and reindex without deleting user notes.
- UI remains English except for user-authored note content.

## 2026-07-10 Execution Log

- Legacy insight cleanup archived 4 technical insights, ignored 4 technical insight nodes, and ignored 6 linked edges.
- Graph validation deleted 0 orphan edges, ignored 0 self edges, ignored 0 duplicate edges, and marked 1 duplicate active job failed.
- Knowledge Base reindex reported 3 notes, 3 processable notes, 6 chunks, and 3 embeddings.
- Full rebuild queued 27 processing jobs.
- Added Qdrant and Chroma HTTP adapters for Knowledge Base indexing and retrieval.
- Added fallback behavior so external vector store failures do not break graph/cognitive inference.
- Added automated tests for vector store integration, maintenance cleanup/validation, and insight filtering.
- Fixed integration test database isolation for routers that import `SessionLocal` directly.
- Added HTTP contract tests for maintenance cleanup, validation, reindex, and rebuild.
- Validation passed: API unittest discovery ran 71 tests successfully.
- Validation passed: API container imported and executed the Cognitive Layer.
- Validation passed: web container TypeScript typecheck completed successfully.
- Added job idempotency by `type + note_path + content_hash`; same content does not duplicate jobs, new content queues a fresh pipeline.
- Added realistic 10-note graph fixture test proving explainable edges after graph expansion.
- Added regression test proving technical/system insights stay out of Home, `/insights`, and Graph.
- Updated vault scan expectations so changed note content queues new processing by hash.
- Validation passed: API unittest discovery ran 74 tests successfully.

## 2026-07-11 Verification Log

- Verified containers running: API healthy, web running, worker running.
- Verified `GET /api/v1/jobs/pipeline-progress` works after API restart.
- Verified API tests: 74 tests passed.
- Verified worker tests: 13 tests passed.
- Fixed optional embedding failure path so unavailable embedding providers mark `embedding_status=skipped` and complete the job.
- Verified web TypeScript typecheck passed.
- E2E specs exist for Home, Activity, Insights, and Settings, but could not pass in the current Docker web container because Playwright uses a glibc browser build inside Alpine and fails before loading the app.
- Runtime cognitive state is not mature yet: active vault currently reports 3 note nodes, 0 graph edges, 0 concepts, 0 insights, and pending processing jobs after rebuild.
- Fixed graph assimilation fallback so current notes generate content-based concepts even when AI metadata is malformed.
- Rebuilt active graph: 38 nodes, 128 edges, 0 orphans, content concepts, shared-concept connections, and knowledge insights now visible.
- Current useful insights include shared patterns around Hulk, Bruce Banner, strength, and Rio de Janeiro.
- Validation passed: API unittest discovery ran 74 tests successfully after graph assimilation changes.
