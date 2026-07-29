# Semantic search benchmark

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
