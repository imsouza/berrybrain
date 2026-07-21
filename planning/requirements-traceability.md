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
| FR-INF-007 | Show Create insight next to Close with state feedback | `graph-screen.tsx` inference panel | TypeScript gate; Playwright pending | Partial |
| FR-GRA-001 | Explain every AI-generated graph edge | graph edge reason/evidence/provenance fields | graph write and quality tests | Implemented |
| FR-GRA-002 | Confirm/ignore graph suggestions persistently | graph action endpoints and canonical writer | integration coverage exists; full E2E pending | Partial |
| FR-INS-001 | Keep knowledge insights separate from system diagnostics | insight type filters and quality rules | insight filter/quality tests | Implemented |
| FR-KB-001 | Index Markdown into chunks and embeddings | cognitive layer, chunk/embedding records | vector-store and semantic benchmarks | Implemented with quality gates pending |
| FR-JOB-001 | Process cognitive jobs asynchronously and visibly | API jobs plus worker | worker integration suite | Implemented |
| FR-OBS-001 | Record user-visible cognitive actions | automation logs | automation log and inference integration tests | Implemented |

## Cognitive requirements

| ID | Requirement | Acceptance measure | Current state |
|---|---|---|---|
| COG-001 | Claims are grounded in user knowledge | Unsupported claim rate <= 2% | Benchmark gate pending |
| COG-002 | Connections are useful and explainable | Precision >= 85%, reason/evidence coverage 100% | Structural coverage exists; precision gate pending |
| COG-003 | Retrieval finds relevant knowledge | Recall@10 >= 85%, MRR >= 75% | Small benchmark exists; public representative corpus pending |
| COG-004 | Insights lead to learning actions | >= 70% useful/acted-on over rolling 30 days | Feedback schema partial; longitudinal metric pending |
| COG-005 | Knowledge gaps do not invent relationships | 100% gap records distinguish absence from conclusion | Implemented for graph inference |
| COG-006 | Knowledge evolves after note changes | Clean pipeline E2E updates chunks, graph, insights, and Home | Cross-service E2E pending |
| COG-007 | The system preserves source provenance | Provider/model/prompt/source/evidence coverage 100% | Strong model support; completeness audit pending |

## Non-functional requirements

| ID | Requirement | Acceptance measure | Status |
|---|---|---|---|
| NFR-REL-001 | Safe retry and restart | No duplicate knowledge after worker crash/retry | Partial |
| NFR-REL-002 | Backup portability | Restore verified across supported schema versions | Partial |
| NFR-SEC-001 | No secrets in repository, logs, or API responses | Secret scan clean; redaction tests pass | Implemented, continuous gate |
| NFR-SEC-002 | Secure public deployment | CSRF/session/rate-limit/CSP tests pass | Partial |
| NFR-PERF-001 | Responsive graph and Home | Published p95 API/UI budgets | Missing |
| NFR-ACC-001 | Accessible UI | WCAG 2.2 AA automated and manual audit | Missing |
| NFR-ARCH-001 | Domain independent of frameworks | Architecture test passes | Implemented for graph-inference slice |
| NFR-ARCH-002 | No hidden sessions in migrated use cases | Dependency-injected session and architecture test | Implemented for graph-inference slice |
| NFR-TEST-001 | Regression confidence | 80% overall, 90% domain/application branch coverage | In progress |
| NFR-DATA-001 | Non-destructive upgrades | Migration and clean/upgrade tests pass | Implemented for schema metadata; restore matrix pending |

## Change control

Every pull request that changes behavior must:

1. cite at least one requirement ID;
2. add or update automated evidence;
3. identify migration and rollback impact;
4. distinguish knowledge behavior from system diagnostics;
5. update the status only after the acceptance measure passes.
