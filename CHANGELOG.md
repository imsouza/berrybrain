# Changelog

All notable BerryBrain changes are documented here.

## 1.4.4 - 2026-08-12

### Added

- Versioned benchmark evidence manifests, raw observations, checksums, schemas, and scale profiles.
- Executed retrieval ablations, independent retrieval baselines, HTTP/worker/on-disk graph/browser
  runners, instrumentation overhead analysis, and a composed evaluation runner.
- Evidence-based Maturity V3, dataset registry, thesis methodology, reproducibility protocol,
  limitations, analysis tables, chart specifications, and documentation freshness checks.
- Privacy-safe API request correlation, `Server-Timing`, and bounded route performance aggregates.

### Changed

- Retrieval quality is computed from real executed queries and qrels rather than assigned outcomes.
- Authenticated Brain and Ask startup avoids a redundant setup-status request in the normal path.
- README and public Docs use current exploratory evidence and explicitly separate regression,
  independent-comparison, and human-study claims.
- The minimum `pypdf` version is now 6.15.0, resolving PYSEC-2026-3655 and PYSEC-2026-3656.

### Evidence boundary

- Public datasets, independent replication, ethics approval, participant studies, and longitudinal
  field evidence remain external requirements; no result is fabricated for those layers.

## 1.4.3 - 2026-08-11

### Added

- Dedicated Ask workspace with voice input, Flow history, Graph/Home navigation, an
  evidence-derived question queue, and a graph-backed topic cloud.
- Non-blocking Ask suggestions: live graph questions render immediately while AI generation runs
  in the background, validates node references, and caches richer suggestions per graph version.
- Automatic worker-heartbeat monitor for enrichment, insight and gap discovery, Judge, and clusters.
- Graph node deletion with automatic statistics and cluster recalculation.
- Persistent notifications for insight proposals and jobs that exhaust their retry budget.

### Changed

- Insights are graph-first proposals with accept/reject actions on the node page.
- AI enrichment is an internal always-active process; manual controls were removed.
- Graph gap research stays explicit and external content remains untrusted until confirmed.
- Ask Flow is the multi-turn memory layer for grounded follow-up questions.

### Removed

- Review Today UI, API routes, worker handler, jobs, and tests.
- Separate Insights page and Home insight cards.

### Fixed

- Notification UI now reads persistent records, marks them read, and follows valid routes.
- Node deletion schedules the recalculation required by changed graph topology.
- Automatic enrichment now carries a live evidence fingerprint, skips stale or duplicate jobs,
  returns invalid semantic contracts as `422`, and cools down after provider dead letters.

## 1.4.2 - 2026-08-11

### Added

- Live microphone waveform and explicit browser speech-recognition failure states in every Ask entry point.
- Rich graph hover summaries with semantic context, calculated confidence, provenance, path, and directed relationships.
- Persisted 95% confidence intervals for concepts, legacy note connections, and graph inferences.
- Schema migration v10 and idempotent runtime backfill for remaining knowledge-confidence records.

### Changed

- Node labels now adapt bounded geometry to content, wrap to three lines, and truncate at 58 characters.
- Dragging pins a node without opening it; a click runs the camera zoom before node-page navigation.
- Node navigation now exposes distinct **Back to Home** and **Back to graph** routes.
- Merged graph artifacts recalculate confidence from consolidated evidence instead of retaining the largest old score.
- Deterministic extraction fallbacks derive confidence from source occurrences and Wilson bounds.
- Graphs with 8,000 or more nodes use a deterministic progressive layout; active camera gestures
  transform the canvas bitmap and redraw crisply after idle.
- Semantic clustering v5 publishes neutral, grammatical fallback labels without exposing legacy
  profile prose.

### Fixed

- Restored microphone activation by preserving the browser user gesture during recognition startup.
- Corrected graph-edge confidence scale in deterministic graph answers.
- Newly created AI edges now always queue Judge evaluation.
- Removed remaining non-English fixture text and production self-check knowledge payloads.
- Removed extreme-graph force-simulation contention; repeated 10,000-node interaction p95 is
  `33-40 ms`.

## 1.4.1 - 2026-08-11

### Added

- Internal graph ontology mapped to SKOS, PROV-O, schema.org, RDF, OWL, and Dublin Core,
  with explicit node criteria and edge domain, range, direction, and symmetry.
- Semantic quarantine and review workflow for invalid generated names and relationships.
- Evidence-derived confidence with persisted 95% Wilson intervals, sample size, factors,
  method, and calculation timestamp.
- Full-page graph node details with zoom-in navigation, context validation, read-only
  confidence, editable manual notes, relationship direction, and semantic-analysis retry.
- Voice prompt controls in Home Ask and Graph Ask.
- Ontology triples synchronized into HippoRAG and retained across sidecar rebuilds.
- Sidebar drag-and-drop ordering and inline note/folder management.

### Changed

- Replaced transitive threshold clustering with deterministic medoid selection and
  silhouette-based cluster count; pending semantic nodes receive provisional colors.
- Graph labels now render once as readable words instead of initials or overlapping text.
- Every node type has a distinct geometry; note roots remain Berry red and insights use a
  highlighted rectangle while context controls the remaining palette.
- Replaced generic graph relationships with canonical ontology roles such as `mentions`,
  `references`, `supports`, `prerequisite_for`, `example_of`, and `contextualizes`.
- Node edits invalidate stale confidence and automatically queue enrichment, Judge,
  expansion, clustering, and graph statistics recalculation.
- New note always opens the editor, including when invoked outside the Brain workspace.
- Insights can be created from Flow answers and generated automatically on a configurable
  interval, defaulting to 24 hours.

### Fixed

- Judge Settings content can scroll instead of being clipped.
- Removed repeated `connections` filler from insight evidence formatting.
- Graph RAG excludes quarantined artifacts and ranks typed, directed relationships by the
  lower bound of calculated confidence.
- PWA code assets now refresh network-first, preventing stale JavaScript after a new deploy.

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
