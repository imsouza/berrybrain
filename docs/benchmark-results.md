# Benchmark Results

## Evidence Status

| Field | Value |
| --- | --- |
| Generated | 12 August 2026, 19:13:05 UTC |
| Version | 1.4.4 |
| Classification | Exploratory engineering evidence |
| Scale profile | S, pull-request regression |
| Shared seed | 20260812 |
| Cache policy | Cold |
| Composed gate | Passed, zero failed gates |
| Maturity V3 | `incomplete-evidence`, minimum Level 0, median Level 2 |
| Authoritative result | `reports/evaluation/full-evaluation.json` |

The worktree was dirty when measured. These results are real executions on the recorded host, but
they are not a clean-revision release certificate or an external-validity claim. Controlled fixtures
are deterministic regression evidence; they are not substituted for public datasets, independent
baselines, participant studies, or field observations.

## Retrieval Comparison

The controlled retrieval corpus contains 44 queries: 20 factual, 20 multi-hop, and 4 negative.
Every configuration processed the same queries, producing 220 query-level observations.

| Executed configuration | Recall@10 | MRR | NDCG@10 | p50 (ms) | p95 (ms) | p99 (ms) | Negative rejection |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| A0 lexical only | 0.050 | 0.017 | 0.025 | 8.54 | 11.01 | 14.21 | 1.000 |
| A1 dense only | 0.500 | 0.500 | 0.500 | 7.98 | 9.70 | 12.25 | 1.000 |
| A2 standard hybrid | 0.500 | 0.500 | 0.500 | 15.27 | 18.27 | 19.95 | 1.000 |
| A3 graph lexical | 0.500 | 0.250 | 0.315 | 15.36 | 21.99 | 24.49 | 1.000 |
| A3 graph hybrid | 1.000 | 0.750 | 0.815 | 22.47 | 30.84 | 32.57 | 1.000 |

| Paired graph result | Standard hybrid | Graph hybrid | Difference |
| --- | ---: | ---: | ---: |
| Multi-hop Recall@10 | 0.000 | 1.000 | +1.000 |
| Factual Recall@10 | 1.000 | 1.000 | 0.000 |
| Multi-hop gain 95% bootstrap CI | - | - | [1.000, 1.000] |
| Citation precision | - | 1.000 | - |
| Evidence faithfulness | - | 1.000 | - |
| Stale/deleted evidence rejected | - | Yes | - |
| Ignored edge rejected | - | Yes | - |

The result supports a causal regression claim for this fixture: graph expansion recovered the
designed multi-hop paths without reducing factual recall. It does not establish superiority over an
external RAG system. A4-A6 and G0-G3 remain protocol definitions until model-backed and
generation-backed runs are executed under parity controls.

## Runtime Performance

| Subsystem | Workload | Throughput | p50 | p95 | p99 | Errors |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| HTTP health | 100 requests, concurrency 10 | 67.98 req/s | 138.02 ms | 248.62 ms | 293.22 ms | 0.0% |
| Worker queue | 100 jobs | 52.39 enqueue/s; 12.48 drain/s | 5,036.14 ms end-to-end | 7,693.75 ms end-to-end | 7,954.86 ms end-to-end | 0 duplicate claims |
| On-disk graph | 500 nodes, 1,000 edges, 7 samples | - | 175.46 ms | 306.76 ms | - | Gate passed |
| Release-gate graph | 5,000 nodes, 20,000 edges, 7 samples | - | 2,381.13 ms | 2,464.51 ms | - | Gate passed |
| Semantic retrieval | 100 notes, 45 queries | - | 31.50 ms | 69.20 ms | - | 0 unexpected zero results |

| Resource measurement | Actual | Budget | Utilization |
| --- | ---: | ---: | ---: |
| S graph serialized payload | 541,592 B | 16,777,216 B | 3.23% |
| S graph peak traced memory | 3,181,953 B | 536,870,912 B | 0.59% |
| Release-gate graph payload | 8,778,919 B | 16,777,216 B | 52.33% |
| Release-gate graph peak traced memory | 51,925,644 B | 536,870,912 B | 9.67% |
| Metrics recorder absolute overhead | 0.00355 ms/op | Report-only | - |

These are host-specific observations, not supported production capacity. Worker end-to-end latency
includes serial queue drain. Browser measurements remain exploratory because five repetitions showed
host-load variance; at least 30 post-warm-up observations on pinned CPU and network profiles are
required for a confirmatory browser claim.

## Quality And Reliability

| Evaluation | Samples | Result | Gate |
| --- | ---: | ---: | --- |
| Judge calibration | 100 evaluations; 30 human reviews | Weighted kappa 0.9801 | Passed, minimum 0.70 |
| Judge false acceptance | 30 comparable reviews | 0.000 | Passed, maximum 0.05 |
| Judge false rejection | 30 comparable reviews | 0.000 | Passed, maximum 0.10 |
| Cognitive extraction | 6 controlled notes | Precision 1.000; recall 1.000 | Passed |
| Graph connections | 6 controlled notes | Precision 1.000; recall 1.000 | Passed |
| Grounded insights | 12 fixtures | Precision 1.000; recall 1.000 | Passed |
| Provenance coverage | Controlled cognition fixture | 1.000 | Passed |
| Unsupported claim rate | Controlled cognition fixture | 0.000 | Passed |

| Injected fault | Contained | Integrity preserved | Recovery observation | User-visible state |
| --- | --- | --- | ---: | --- |
| Provider or sidecar unavailable | Yes | Yes | 9.26 ms | Degraded |
| Malformed model output | Yes | Yes | 0.07 ms | Failed operation |
| Disk write unavailable | Yes | Yes | 1.33 ms | Failed operation |

Recovery values measure synchronous fault containment in isolated probes. They do not represent
service restoration after process, host, network, or region failure.

## Maturity Interpretation

| Capability group | Level | Current evidence |
| --- | ---: | --- |
| Capture and extraction | 0 | No current representative evidence registered |
| Durable semantic memory | 2 | Current deterministic CI/regression evidence |
| Retrieval and grounded inference | 2 | Current deterministic CI/regression evidence |
| Knowledge graph and ontology | 2 | Current deterministic CI/regression evidence |
| Insights and continuous agents | 2 | Current deterministic CI/regression evidence |
| Transparency, confidence, and control | 2 | Current deterministic CI/regression evidence |
| Performance, efficiency, and scalability | 2 | Current deterministic CI/regression evidence |
| Reliability and recoverability | 2 | Current deterministic CI/regression evidence |
| Security, privacy, and safety | 0 | No current evidence registered in the maturity bundle |
| Interaction quality and accessibility | 2 | Current deterministic CI/regression evidence |
| Maintainability and governance | 2 | Current deterministic CI/regression evidence |

Level 2 means implementation plus current automated regression evidence. It is not a percentage.
Levels 4-5 require independent comparison, approved human evidence, or longitudinal field evidence;
synthetic fixtures cannot award them.

## Reproducible Artifacts

- `reports/evaluation/full-evaluation.json`: composed machine-readable result.
- `reports/evaluation/thesis-table.md`: generated publication table.
- `reports/evaluation/retrieval-chart.vl.json`: generated Vega-Lite chart specification.
- `reports/evaluation/maturity-v3.json`: evidence-based capability assessment.
- `reports/evaluation/browser-performance*.json`: exploratory authenticated browser observations.
- `reports/evaluation/instrumentation-overhead.json`: paired recorder microbenchmark.
- `reports/evaluation/fault-injection.json`: isolated resilience observations.
- `reports/evaluation/evidence/`: manifests, raw observations, summaries, and SHA-256 checksums.

Interpret these values with the methodology, protocol, reproducibility, dataset, and limitations
documents. Re-run on a clean revision before using them as thesis-confirmatory or release-certified
claims.
