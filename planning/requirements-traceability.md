# Requirements Traceability

Status: active baseline

## Functional requirements

| ID | Requirement | Implementation evidence | Automated evidence | Status |
|---|---|---|---|---|
| FR-INF-001 | Ask a natural-language question against real BerryBrain data | `cognitive_layer.answer_cognitive_query`, `POST /api/v1/graph/infer` | cognitive resilience and integration tests | Implemented |
| FR-INF-002 | Persist every graph inference with provenance | `GraphInferenceRecord`, `persist_graph_inference` | `test_10b_save_graph_inference_as_insight` | Implemented |
| FR-INF-003 | Create a knowledge insight from a grounded inference | `create_insight_from_persisted_inference` | domain and integration tests | Implemented |
| FR-INF-004 | Create a knowledge gap when evidence is insufficient | `build_insight_draft` | `test_insufficient_answer_builds_gap_without_inventing_evidence`, `test_10c_*` | Implemented |
| FR-INF-005 | Never classify provider failure as knowledge | `SAVABLE_STATUSES` domain policy | `test_provider_failure_is_not_knowledge`, `test_10d_*` | Implemented |
| FR-INF-006 | Prevent browser-supplied inference evidence from being trusted | compatibility path re-runs server inference | `test_10e_legacy_client_inference_is_not_trusted` | Implemented |
| FR-INF-007 | Show Create insight next to Close with state feedback | `graph-screen.tsx` inference panel | integration, TypeScript and workspace E2E gates | Implemented |
| FR-GRA-001 | Explain every AI-generated graph edge | graph edge reason/evidence/provenance fields | graph write and quality tests | Implemented |
| FR-GRA-002 | Confirm/ignore graph suggestions persistently | graph action endpoints and canonical writer | graph mutation and integration suites | Implemented |
| FR-INS-001 | Keep knowledge insights separate from system diagnostics | insight type filters and quality rules | insight filter/quality tests | Implemented |
| FR-KB-001 | Index Markdown into chunks and embeddings | cognitive layer, chunk/embedding records | canonical semantic release gate | Implemented |
| FR-JOB-001 | Process cognitive jobs asynchronously and visibly | API jobs plus worker | worker integration suite | Implemented |
| FR-OBS-001 | Record user-visible cognitive actions | automation logs | automation log and inference integration tests | Implemented |
| FR-OBS-002 | Audit model execution without retaining user content | `ModelInvocationRecord`, model gateway ledger, Monitor reliability card | ledger privacy, failure, retry, cancellation and Monitor integration tests | Implemented |

## Cognitive requirements

| ID | Requirement | Acceptance measure | Current state |
|---|---|---|---|
| COG-001 | Claims are grounded in user knowledge | Unsupported claim rate <= 2% | Gate passes at 0% unsupported claims |
| COG-002 | Connections are useful and explainable | Precision >= 85%, reason/evidence coverage 100% | Gate passes at 100% on labeled fixtures |
| COG-003 | Retrieval finds relevant knowledge | Recall@10 >= 85%, MRR >= 75% | 100-note gate passes at 100% Recall@10/MRR |
| COG-004 | Insights lead to learning actions | >= 70% useful/acted-on over rolling 30 days | Feedback schema partial; longitudinal metric pending |
| COG-005 | Knowledge gaps do not invent relationships | 100% gap records distinguish absence from conclusion | Implemented for graph inference |
| COG-006 | Knowledge evolves after note changes | Clean pipeline E2E updates chunks, graph, insights, and Home | Create/update/delete E2E proves stale search, graph, and insight state is retired |
| COG-007 | The system preserves source provenance | Provider/model/prompt/source/evidence coverage 100% | Benchmark and runtime completeness auditors implemented |

## Non-functional requirements

| ID | Requirement | Acceptance measure | Status |
|---|---|---|---|
| NFR-REL-001 | Safe retry, restart and cancellation | No duplicate knowledge after worker crash/retry; queued/running cancellation remains terminal | Implemented with durable job outbox, idempotency, cooperative Worker cancellation, stale-cancel recovery and API/UI tests |
| NFR-REL-003 | Bound and recover provider failures | Transient retry, concurrency cap, open circuit, cooldown recovery and cancellation are tested | Implemented for cognitive gateway and Worker provider paths |
| NFR-REL-004 | Detect actionable queue degradation | Pending age, stale running jobs, and dead letters have explicit SLOs | Implemented in `/jobs/health`, domain tests, and Monitor |
| NFR-REL-002 | Backup portability | Restore verified across supported schema versions | Partial: checksums, v4 -> v6 staged migration, v5 -> v6 DDL, integrity checks and atomic DB/vault rollback pass; historical release drill remains |
| NFR-SEC-001 | No secrets in repository, logs, or API responses | Secret scan clean; redaction tests pass | Implemented, continuous gate |
| NFR-SEC-002 | Secure public deployment | CSRF/session/rate-limit/CSP tests pass | Partial |
| NFR-PERF-001 | Responsive graph and Home | Published p95 API/UI budgets | Landing LCP/CLS/JS, <= 200 ms browser INP candidate, and graph API p95 2,500 ms budget pass |
| NFR-ACC-001 | Accessible UI | WCAG 2.2 AA automated and manual audit | Automated WCAG 2.2 A/AA, keyboard/focus/reduced-motion gate passes; manual screen-reader audit pending |
| NFR-ARCH-001 | Domain independent of frameworks | Architecture test passes | Implemented for graph-inference slice |
| NFR-ARCH-002 | No hidden sessions in migrated use cases | Dependency-injected session and architecture test | Implemented for graph-inference slice |
| NFR-TEST-001 | Regression confidence | 80% overall, 90% domain/application branch coverage | 80% overall branch gate and 90% new domain thresholds enforced in CI |
| NFR-DATA-001 | Non-destructive upgrades | Migration and clean/upgrade tests pass | Schema v6 adds claim-scoped worker inbox; v4 -> v6 staged restore and coordinated rollback pass; historical restore matrix pending |

## Change control

Every pull request that changes behavior must:

1. cite at least one requirement ID;
2. add or update automated evidence;
3. identify migration and rollback impact;
4. distinguish knowledge behavior from system diagnostics;
5. update the status only after the acceptance measure passes.
