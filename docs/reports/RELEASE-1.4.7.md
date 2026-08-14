# BerryBrain 1.4.7 Release Validation

**Validation date:** 2026-08-13
**Environment:** local ARM64 self-hosted stack, Docker Compose, NVIDIA NIM cloud mode
**Status:** local acceptance passed; remote PR checks pending

## Scope

This release validates durable graph feedback, incident-only deletion repair, automatic dependent
insight invalidation, scoped clustering, visible mutation progress, provider-aware Judge defaults,
and Judge model compatibility checks.

## Real Runtime Evidence

| Observation | Measured result |
| --- | --- |
| Deleted node | `Skip`, record 216 |
| Source scope captured before deletion | Notes 3 and 4 |
| Incident edges removed | 16 |
| Surviving affected nodes | 15 |
| Dependent insight invalidated | Insight 65, status `expired` |
| Node after a fresh database session | 0 rows |
| Active deletion feedback after refresh | 1 record, source scope `[3, 4]` |
| Scoped repair jobs | 4/4 completed on first attempt |
| HippoRAG synchronization | 4 documents, 448 triples, 0 errors |
| Schema migration | 11 |

The four deletion repairs were `UPDATE_GRAPH_STATS`, `UPDATE_GRAPH_CLUSTERS`,
`GENERATE_GRAPH_INSIGHTS`, and `SYNC_HIPPORAG_GRAPH`. Cluster and insight payloads contained only
the incident neighborhood and affected source notes; the delete route did not request a full graph
recalculation.

## Judge Compatibility Evidence

The live NVIDIA catalog returned 102 model IDs. Catalog presence did not imply chat compatibility:
several listed candidates returned `404` or timed out. The final default selection was admitted only
after each model completed the same structured JSON route used by Judge execution.

| Role | Compatibility-tested runtime model |
| --- | --- |
| Faithfulness | `deepseek-ai/deepseek-v4-flash-0731` |
| Relevance | `meta/llama-3.1-70b-instruct` |
| Contradiction | `meta/llama-3.1-8b-instruct` |

A real node evaluation used all three members and persisted aggregate evaluation 419 with status
`review` and score 7.8. Four historical Judge dead letters caused by incompatible catalog models
were retried after configuration repair; jobs 1303-1306 then completed on their first new attempt.
These model IDs are runtime evidence, not hardcoded provider defaults.

## Verification Matrix

| Gate | Result |
| --- | --- |
| API Ruff lint and format | Passed |
| Focused API regressions | 40 passed |
| Full API suite | 436 passed in 226.307 seconds |
| API coverage | 79%; critical coverage gate passed |
| MyPy progressive CI scope | 13 source files, no issues |
| Worker Ruff lint and format | Passed |
| Worker suite | 53 passed in 12.926 seconds |
| Web ESLint | Passed |
| Web TypeScript | Passed |
| Next.js production build | 23 pages generated |
| Node deletion Playwright scenario | 1 passed in 33.3 seconds |
| API, Worker, Web, HippoRAG Compose health | Healthy after rebuild |

## Known Non-Blocking Warnings

- Several legacy unit tests emit SQLAlchemy `ResourceWarning` messages for temporary SQLite
  connections. The suites pass, but fixture disposal should be tightened in a future maintenance
  release.
- Starlette reports that its current `httpx` TestClient adapter is deprecated in favor of
  `httpx2`. This does not affect production requests.
- The local kernel does not expose Docker memory-limit capabilities, so Compose discards local
  container memory limits. Production hosts should enable the appropriate cgroup controller.

## Acceptance Boundary

Local release acceptance is complete. GitHub branch protection, remote CI, merge, tag, and release
publication remain separate delivery gates and must pass before this report is marked released.
