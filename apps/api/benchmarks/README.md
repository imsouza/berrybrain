# Semantic search benchmark

## Unified maturity release gate

Run every deterministic cognitive quality gate with one command:

```bash
PYTHONPATH=src python -m benchmarks.maturity_release_gate
```

The command produces a machine-readable JSON report and exits non-zero when
semantic retrieval, expert-labeled insight usefulness, graph integrity,
large-graph projection performance, provenance, grounding, idempotency, or
stale-evidence cleanup regresses. CI runs
this command for every backend change. These deterministic gates establish
technical readiness; the runtime maturity endpoint separately requires at least
30 days of real usefulness outcomes before reporting 100% maturity.

The graph performance gate projects and serializes 5,000 nodes and 20,000 edges
through the production graph service. It requires complete projection, p95 at or
below 2.5 seconds, and a payload no larger than 16 MiB. Run it directly with
`PYTHONPATH=src python -m benchmarks.graph_performance_benchmark`.

This benchmark exercises BerryBrain's production hybrid retrieval path with a
deterministic, provider-independent fixture. It creates 100 notes across 10
knowledge domains, runs 40 positive queries and 5 negative queries, and checks
semantic paraphrases that do not share the note vocabulary.

Run the canonical quality benchmark:

```bash
PYTHONPATH=src python -m benchmarks.semantic_search_benchmark
```

Run the 1,000-note latency profile:

```bash
PYTHONPATH=src python -m benchmarks.semantic_search_benchmark --notes-per-topic 100
```

The command exits non-zero when Recall@10, MRR, p95 latency, index coverage, or
fresh-evidence targets from `PLANNING_BERRYBRAIN_100.md` are missed. Fixture
embeddings are deterministic so CI measures retrieval behavior, not provider
availability or model drift.

## Insight usefulness

`PYTHONPATH=src python -m benchmarks.insight_usefulness_benchmark` evaluates the
publication barrier against an expert-labeled internal dataset. Every fixture has
a reviewer rationale. The gate requires at least 80% accuracy, precision, recall,
and usefulness among accepted insights. Operational diagnostics, implementation
data, generic claims, and unsupported hypotheses are negative controls.

## Cognitive graph maturity

`PYTHONPATH=src python -m benchmarks.cognitive_maturity_benchmark` processes six
expert-labeled notes and checks concept and connection precision/recall, complete
provenance, grounded insights, diagnostic leakage, idempotent rebuilds, stale
knowledge cleanup, and preservation of human-reviewed statuses.
