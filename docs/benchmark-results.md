# Benchmark Results

## Evidence Status

| Field | Value |
| --- | --- |
| Generated | 14 August 2026, 04:48:50 UTC |
| Target version | 1.4.8 |
| Classification | Exploratory engineering evidence |
| Internal profile | S, pull-request regression |
| Shared seed | 20260812 |
| Cache policy | Cold |
| Composed engineering gate | Passed, zero failed gates |
| Maturity V3 | `incomplete-evidence`, minimum Level 0, median Level 2 |
| Authoritative result | `reports/evaluation/full-evaluation.json` |

The run used real local execution against controlled fixtures. The worktree was dirty, so the
result is not a clean-revision release certificate. Synthetic fixtures measure regression, not
field effectiveness. Human calibration, independent replication, and longitudinal use remain open.

## Internal Retrieval Ablation

The controlled corpus contains 44 queries: 20 factual, 20 multi-hop, and 4 negative. All five
configurations used the same query and relevance sets, producing 220 query-level observations.

| Configuration | Recall@10 | MRR | NDCG@10 | p50 (ms) | p95 (ms) | p99 (ms) | Negative rejection |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Lexical only | 0.050 | 0.017 | 0.025 | 7.72 | 10.22 | 12.59 | 1.000 |
| Dense only | 0.500 | 0.500 | 0.500 | 8.34 | 10.85 | 14.57 | 1.000 |
| Standard hybrid | 0.500 | 0.500 | 0.500 | 19.44 | 23.38 | 24.82 | 1.000 |
| Graph lexical | 0.500 | 0.250 | 0.315 | 15.97 | 19.56 | 24.73 | 1.000 |
| Graph hybrid | 1.000 | 0.750 | 0.815 | 22.69 | 31.47 | 34.95 | 1.000 |

| Paired result | Standard hybrid | Graph hybrid | Difference |
| --- | ---: | ---: | ---: |
| Multi-hop Recall@10 | 0.000 | 1.000 | +1.000 |
| Factual Recall@10 | 1.000 | 1.000 | 0.000 |
| Multi-hop gain 95% bootstrap CI | - | - | [1.000, 1.000] |
| Citation precision | - | 1.000 | - |
| Evidence faithfulness | - | 1.000 | - |
| Stale/deleted and ignored evidence rejected | - | Yes | - |

This supports a causal regression claim only for the designed fixture: graph expansion recovers the
fixture's multi-hop paths without reducing its factual recall. It does not establish general or
competitive superiority.

## Public Baseline Context

The official BEIR SciFact test split was downloaded from its upstream registry and normalized for
an independent BM25 run. The corpus is not vendored. Its archive SHA-256 is
`536e14446a0ba56ed1398ab1055f39fe852686ecad24a6306c80c490fa8e0165`.

| Dataset/method | Documents | Queries | Recall@10 | MRR | NDCG@10 | Build | p50 | p95 | p99 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| BEIR SciFact / BM25 | 5,183 | 300 | 0.7816 | 0.6386 | 0.6644 | 1,393.12 ms | 309.78 ms | 386.21 ms | 406.30 ms |

This is an external baseline implementation check, not a head-to-head BerryBrain comparison. The
internal fixture and SciFact use different corpora, qrels, tasks, and runtime paths. A comparative
claim requires BerryBrain and every baseline to run on the same public corpus with parity controls.

## Runtime Performance

| Subsystem | Workload | Throughput | p50 | p95 | p99 | Integrity |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| HTTP health | 100 requests, concurrency 10 | 76.12 req/s | 119.26 ms | 224.55 ms | 257.96 ms | 0 errors |
| Worker queue | 100 jobs | 49.15 enqueue/s; 11.92 drain/s | 5,452.56 ms | 8,060.36 ms | 8,326.85 ms | 0 duplicate claims |
| On-disk graph | 500 nodes, 1,000 edges, 7 samples | - | 188.62 ms | 222.63 ms | - | Gate passed |
| Release-gate graph | 5,000 nodes, 20,000 edges, 7 samples | - | 2,733.77 ms | 2,824.20 ms | - | Gate passed |
| Semantic retrieval | 100 notes, 45 queries | - | 32.56 ms | 64.33 ms | - | 0 stale evidence |

| Resource measurement | Actual | Budget | Utilization |
| --- | ---: | ---: | ---: |
| S graph serialized payload | 864,092 B | 16,777,216 B | 5.15% |
| S graph peak traced memory | 3,933,306 B | 536,870,912 B | 0.73% |
| Release-gate graph payload | 14,153,919 B | 16,777,216 B | 84.36% |
| Release-gate graph peak traced memory | 63,961,535 B | 536,870,912 B | 11.91% |
| Metrics recorder absolute overhead | 0.003884 ms/op | Report-only | - |
| Metrics overhead 95% bootstrap CI | [0.003526, 0.004281] ms/op | Report-only | - |

The metrics-overhead relative ratio is 1.077 because the disabled operation is only 0.003605 ms;
the absolute difference is the meaningful quantity. Runtime values are host-specific observations,
not supported production capacity.

## Quality And Reliability

| Evaluation | Samples | Result | Interpretation |
| --- | ---: | ---: | --- |
| Judge reference regression | 100 evaluations; 30 synthetic reference labels | Weighted kappa 0.9801; 29/30 match | Regression passed; not human-calibrated |
| Judge false acceptance/rejection | 30 comparable synthetic labels | 0.000 / 0.000 | Fixture result only |
| Cognitive extraction | 6 controlled notes | Precision 1.000; recall 1.000 | Regression passed |
| Graph connections | 6 controlled notes | Precision 1.000; recall 1.000 | Regression passed |
| Grounded insights | 12 fixtures | Precision 1.000; recall 1.000 | Regression passed |
| Fault injection | 3 isolated faults | 3/3 contained; 3/3 prior state preserved | Maximum synchronous containment 9.59 ms |

The Judge report has `classification=synthetic-regression`, `total_human_reviews=0`,
`calibrated=false`, and `status=regression_only`. Strict human-calibration claims require at least
100 evaluations, 30 independent human reviews, weighted kappa at least 0.70, false acceptance at
most 5%, and false rejection at most 10%.

## Learning Evaluation

Feedback-guided adaptation is covered by automated behavioral tests rather than a fabricated
learning percentage. Tests verify source-context overlap, unrelated-context exclusion,
latest-decision precedence, correction and annotation propagation, graph suppression after delete,
Ask/inference provenance, note lifecycle events, Worker policy consumption, and Monitor telemetry.

No longitudinal user dataset exists yet. Therefore v1.4.8 makes no claim that the policy improves
quality over time in real use. The required future comparison is a repeated pre/post or crossover
study using accepted-artifact precision, recurrence of rejected patterns, correction effort,
retrieval relevance, and time-to-resolution.

## Maturity Interpretation

| Capability group | Level | Evidence |
| --- | ---: | --- |
| Capture and extraction | 0 | No current representative evidence registered |
| Durable semantic memory | 2 | Current automated regression evidence |
| Retrieval and grounded inference | 2 | Current automated regression evidence |
| Knowledge graph and ontology | 2 | Current automated regression evidence |
| Insights and continuous agents | 2 | Current automated regression evidence |
| Transparency, confidence, and control | 2 | Current automated regression evidence |
| Performance, efficiency, and scalability | 2 | Current automated regression evidence |
| Reliability and recoverability | 2 | Current automated regression evidence |
| Security, privacy, and safety | 0 | No current evidence registered in the maturity bundle |
| Interaction quality and accessibility | 2 | Current automated regression evidence |
| Maintainability and governance | 2 | Current automated regression evidence |

Level 2 means implementation plus current automated evidence. Levels 4-5 require independent
comparison, approved human evidence, or longitudinal field evidence; fixtures cannot award them.

## Reproducible Artifacts

- `reports/evaluation/full-evaluation.json`: composed result and gate status.
- `reports/retrieval-benchmark.json`: internal retrieval observations and ablations.
- `reports/evaluation/external-beir-scifact-bm25.json`: public SciFact BM25 context run.
- `reports/judge-calibration-report.json`: synthetic Judge regression with explicit limitation.
- `reports/evaluation/instrumentation-overhead.json`: paired instrumentation overhead.
- `reports/evaluation/evidence/`: manifests, summaries, raw observations, and checksums.
- `benchmarks/datasets/manifests/beir.json`: upstream acquisition, checksums, and corpus counts.
- `reports/evaluation/thesis-table.md`: generated publication table.
- `reports/evaluation/retrieval-chart.vl.json`: generated Vega-Lite chart specification.
- `reports/evaluation/maturity-v3.json`: evidence-based capability assessment.
