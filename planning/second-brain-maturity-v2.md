# BerryBrain Second-Brain Maturity V2

Audit date: 2026-07-21

Conclusion: BerryBrain is a functional evidence-oriented second brain, but it is not yet a
100% mature second brain. It already captures local knowledge, builds a graph, retrieves
evidence, runs configured models, generates traceable insights, and exposes learning actions.
It still lacks the measured retrieval/connection quality, longitudinal learning outcomes,
failure recovery, architectural isolation, and release evidence required for a 100% claim.

Scores are evidence-based release gates, not marketing percentages.

## Cognitive scorecard: 65/100

| Capability | Weight | Current | Evidence | Missing for full score |
|---|---:|---:|---|---|
| Capture and ownership | 10 | 8 | Markdown vault, watcher, attachments, export/backup | Complete extractor coverage and clean-install fixtures |
| Durable semantic memory | 15 | 10 | chunks, embeddings, SQLite fallback, Qdrant/Chroma adapters | representative Recall@10/MRR gates and stale-index proof |
| Knowledge graph | 15 | 10 | typed nodes/edges, reason, evidence, confidence, provenance | measured edge precision, deterministic versioning, undo completeness |
| Grounded inference | 15 | 11 | hybrid retrieval, configured AI, persisted inference records | citation validation, larger benchmark, cancellation/SLOs |
| Knowledge insights | 15 | 10 | knowledge/system split, evidence rules, gaps, graph nodes | usefulness metric, longitudinal recalculation, unsupported-claim gate |
| Review and learning | 10 | 5 | review items and evidence-backed actions | measured retention loop and adaptive scheduling outcomes |
| Longitudinal cognition | 10 | 3 | timestamps, activity, limited feedback/expiry | concept mastery, trend history, forgetting and study efficacy models |
| Transparency and control | 10 | 8 | provider/model/evidence/status, confirm/ignore/activity | complete provenance audit and reversible event history |

## Engineering scorecard: 62/100

| Capability | Weight | Current | Evidence | Missing for full score |
|---|---:|---:|---|---|
| Architecture | 15 | 5 | first framework-free graph-inference domain slice | migrate remaining contexts; repositories/UoW/outbox |
| Clean code | 10 | 4 | lint/type gates and scoped modules | split large API/worker/web files; zero warnings/complexity gates |
| Automated tests | 15 | 12 | broad API/worker/web/security suites | 80/90 coverage gates, mutation/property tests, more E2E |
| Reliability | 15 | 10 | leases, retries, diagnostics, migrations | crash/restart matrix, dead letters, cancellation, SLOs |
| Security | 15 | 11 | auth, redaction, token rotation, CI security | completed threat model and public-deployment adversarial suite |
| Data portability | 10 | 7 | Markdown ownership and backup/restore support | version restore matrix and disaster-recovery drill |
| Observability | 10 | 7 | Activity, Monitor, provider/job diagnostics | correlation IDs, metrics, traces, actionable alerts/SLOs |
| UX, accessibility, performance | 5 | 3 | responsive product and explicit states | WCAG 2.2 AA and published performance budgets |
| Requirements, docs, release | 5 | 3 | requirements and phased plan | reproducible signed release evidence and current operational docs |

## Mandatory gates for a 100% cognitive claim

- [ ] Source/provenance coverage is 100% for generated claims, nodes, edges, and insights.
- [ ] Unsupported knowledge claims are <= 2% on a versioned independent benchmark.
- [ ] AI/deterministic connection precision is >= 85% with human-reviewed fixtures.
- [ ] Retrieval Recall@10 is >= 85% and MRR is >= 75% on representative vaults.
- [ ] No system diagnostic can be stored or displayed as a Knowledge Insight.
- [ ] At least 70% of surfaced insights are marked useful or acted on over 30 days.
- [ ] A clean-install E2E proves note -> chunks -> embedding -> graph -> insight -> Home.
- [ ] Note update/delete E2E proves stale knowledge disappears everywhere.
- [ ] Provider outage never invents knowledge and recovers without manual data repair.
- [ ] Review outcomes measurably update future scheduling and concept mastery.

## Mandatory gates for a 100% engineering claim

- [ ] All context dependencies satisfy architecture tests.
- [ ] Overall branch coverage >= 80%; domain/application >= 90%.
- [ ] Ruff, strict MyPy for migrated modules, ESLint, and TypeScript have zero warnings.
- [ ] Worker crash, duplicate delivery, stale lease, retry, and dead-letter tests pass.
- [ ] Clean install, upgrade, backup, and restore pass on every supported release path.
- [ ] No critical/high security findings; threat model and abuse tests are current.
- [ ] Images and release artifacts are signed and include SBOM/provenance attestations.
- [ ] WCAG 2.2 AA and defined p95 performance budgets pass.
- [ ] Operational runbooks match the released Docker configuration.

## Implemented in this iteration

- [x] Graph questions now create persisted, auditable inference records.
- [x] The web receives an `inferenceId` instead of being the knowledge authority.
- [x] `Create insight` creates a grounded insight or an explicit knowledge gap.
- [x] Waiting/error provider results cannot become knowledge.
- [x] Legacy client payloads are re-evaluated server-side instead of trusted.
- [x] Created insights link back to inference provenance and appear in Activity/graph refresh.
- [x] The cognitive policy is framework-free and protected by architecture tests.
- [x] Schema version 4 documents persisted graph inference support.

## Next release decision

Do not advertise BerryBrain as “100% mature” until both scorecards reach 100 and every
mandatory gate has reproducible CI/release evidence. The accurate current statement is:

> BerryBrain is a real, local-first second brain with an evidence-oriented cognitive layer,
> currently progressing from functional maturity toward measured production maturity.
