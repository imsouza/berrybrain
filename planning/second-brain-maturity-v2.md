# BerryBrain Second-Brain Maturity V2

Audit date: 2026-07-22

Conclusion: BerryBrain is a measured evidence-oriented second brain, but it is not yet a
100% mature second brain. Deterministic release benchmarks now prove retrieval quality,
connection precision, provenance, grounding, stale-data cleanup, and diagnostic isolation.
The remaining blockers are longitudinal learning outcomes, broader architectural isolation,
manual accessibility evidence and recovery drills across all supported releases.

Scores are evidence-based release gates, not marketing percentages.

## Cognitive scorecard: 86/100

| Capability | Weight | Current | Evidence | Missing for full score |
|---|---:|---:|---|---|
| Capture and ownership | 10 | 9 | Markdown vault, watcher, attachments, export/backup, sandbox and extractor tests | complete cross-format clean-install fixtures |
| Durable semantic memory | 15 | 15 | 100-note benchmark: Recall@10/MRR/nDCG 100%, stale evidence 0 | independent real-vault profiles |
| Knowledge graph | 15 | 15 | typed graph plus 100% labeled precision/recall, idempotency and stale cleanup | larger independent expert corpus |
| Grounded inference | 15 | 14 | hybrid retrieval, persisted inference, server-owned evidence, bounded execution and cancellation audit | production SLO history |
| Knowledge insights | 15 | 12 | 100% fixture usefulness/grounding and zero diagnostic leakage | real 30-day usefulness gate |
| Review and learning | 10 | 7 | grounded review lifecycle and adaptive scheduling tests | measured retention outcomes |
| Longitudinal cognition | 10 | 4 | runtime 30-day outcome auditor and persisted feedback | sufficient real observation period and mastery trends |
| Transparency and control | 10 | 10 | runtime provenance audit, canonical graph writer, versioned mutations | continuous production audit |

## Engineering scorecard: 84/100

| Capability | Weight | Current | Evidence | Missing for full score |
|---|---:|---:|---|---|
| Architecture | 15 | 8 | framework-free inference domain, canonical graph writer, architecture-tested job outbox, and persisted claim-scoped worker inbox | migrate remaining contexts and introduce repository/UoW ports |
| Clean code | 10 | 8 | zero-warning ESLint/TypeScript and expanded MyPy cognitive/provider/ledger gate | split API/worker monoliths; full strict typing |
| Automated tests | 15 | 14 | 276 API tests, 37 worker tests, 26 browser tests, unified benchmarks, and 81% branch coverage | mutation testing and broader adapter contracts |
| Reliability | 15 | 14 | crash, duplicate, lease, bounded retry, dead-letter, cooperative queued/running cancellation, stale-cancel recovery, concurrency and provider-circuit tests | measured production SLO history |
| Security | 15 | 13 | auth/abuse tests, secret scan, dependency audits with no high/critical | complete public-deployment threat drill |
| Data portability | 10 | 9 | checksum backup, staged v4 -> v6 migration, explicit v5 -> v6 DDL, full-vault replacement, integrity validation and coordinated swap rollback tests | historical release matrix and external disaster-recovery drill |
| Observability | 10 | 9 | Activity, Monitor, invocation ledger, correlation IDs, provider/job diagnostics and circuit state | exported metrics/traces and actionable SLO alerts |
| UX, accessibility, performance | 5 | 4 | responsive E2E, automated WCAG 2.2 A/AA, reduced-motion, landing LCP/CLS/JS and <= 200 ms INP-candidate budgets, and graph API p95 1.74 s at 5,000 nodes/20,000 edges | manual screen-reader audit |
| Requirements, docs, release | 5 | 5 | traceability, signed multi-arch images, SBOM/provenance, and Compose-validated operations runbook | keep release evidence synchronized |

## Mandatory gates for a 100% cognitive claim

- [x] Source/provenance coverage is 100% for generated claims, nodes, edges, and insights.
- [x] Unsupported knowledge claims are <= 2% on a versioned expert-labeled benchmark.
- [x] AI/deterministic connection precision is >= 85% with human-reviewed fixtures.
- [x] Retrieval Recall@10 is >= 85% and MRR is >= 75% on the canonical 100-note corpus.
- [x] No system diagnostic can be stored or displayed as a Knowledge Insight in benchmark and UI filters.
- [ ] At least 70% of surfaced insights are marked useful or acted on over 30 days.
- [x] A clean-install API E2E proves note -> chunks -> embedding -> graph -> insight -> Home.
- [x] Note update/delete E2E proves stale knowledge disappears everywhere.
- [x] Provider outage never invents knowledge and circuit recovery does not require data repair.
- [x] Review outcomes update future scheduling; measured concept mastery remains longitudinal work.

## Mandatory gates for a 100% engineering claim

- [ ] All context dependencies satisfy architecture tests.
- [x] Overall branch coverage >= 80%; new domain modules meet the 90% threshold.
- [x] Ruff, strict MyPy for migrated modules, ESLint, and TypeScript have zero warnings.
- [x] Worker crash, duplicate delivery, stale lease, retry, and dead-letter tests pass.
- [ ] Clean install, upgrade, backup, and restore pass on every supported release path; v4 -> v6, v5 -> v6 and atomic swap rollback pass, historical release fixtures remain.
- [x] No critical/high dependency findings; auth abuse and secret/redaction tests are current.
- [x] Images and release artifacts are signed and include SBOM/provenance attestations.
- [ ] WCAG 2.2 AA and defined p95 performance budgets pass; graph API and automated landing budgets pass, manual screen-reader evidence remains.
- [x] Operational runbooks match the released Docker configuration and are guarded by an automated topology/recovery contract test.

## Implemented in this iteration

- [x] Graph questions now create persisted, auditable inference records.
- [x] The web receives an `inferenceId` instead of being the knowledge authority.
- [x] `Create insight` creates a grounded insight or an explicit knowledge gap.
- [x] Waiting/error provider results cannot become knowledge.
- [x] Legacy client payloads are re-evaluated server-side instead of trusted.
- [x] Created insights link back to inference provenance and appear in Activity/graph refresh.
- [x] The cognitive policy is framework-free and protected by architecture tests.
- [x] Schema version 5 adds persisted graph inference and privacy-preserving model invocation diagnostics.
- [x] Schema version 6 adds claim tokens and a privacy-preserving worker inbox for exactly-once terminal-message consumption.
- [x] A unified cognitive release gate blocks retrieval, insight, provenance, or graph regressions.
- [x] Runtime `GET /api/v1/cognitive/maturity` reports structural and 30-day outcome blockers from real data.
- [x] Canonical graph rebuild preserves reviewed states and retires stale generated relations.
- [x] ESLint has zero warnings; cognitive modules pass expanded MyPy checks.
- [x] Clean-install browser suite covers setup, auth, onboarding, PWA, notes, accessibility, and responsive states.
- [x] Every cognitive model call records capability, provider, model, prompt version, attempts, latency, status, and sanitized error without storing prompts or note content.
- [x] Provider execution has bounded transient retries, concurrency control, circuit breaking, cooldown recovery, and cancellation accounting.
- [x] Restore stages and migrates the database, verifies integrity, replaces the full vault, and rolls both resources back if a coordinated swap fails.
- [x] The release gate projects and serializes 5,000 nodes/20,000 edges under a 2,500 ms p95 and 16 MiB payload budget.
- [x] `OPERATIONS.md` defines checkpoint upgrades, backup verification, rollback, health checks, recovery drills, and incident triage against the released Compose topology.
- [x] Graph-inference projection now crosses only the durable idempotent job outbox; synchronous duplicate projection is forbidden by an architecture test.
- [x] Queued/running jobs support persisted cooperative cancellation, Worker interruption, terminal acknowledgement, stale recovery, Activity events, and a tested Monitor action.
- [x] Duplicate or stale Worker completion/failure messages cannot mutate a newer claim; the inbox record and job transition commit together.
- [x] The 2026-07-22 clean gate run passes 276 API tests, 37 Worker tests, 26 production-browser tests, 81% branch coverage, critical-module coverage, Ruff, MyPy, ESLint, TypeScript, production build, and the unified cognitive benchmark.
- [x] Queue latency, stale active work, and dead letters now have explicit domain SLOs surfaced as actionable Monitor state.

## Next release decision

Do not advertise BerryBrain as “100% mature” until both scorecards reach 100 and every
mandatory gate has reproducible CI/release evidence. The accurate current statement is:

> BerryBrain is a real, local-first second brain with an evidence-oriented cognitive layer,
> currently progressing from functional maturity toward measured production maturity.
