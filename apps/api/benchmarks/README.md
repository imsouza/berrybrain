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
publication barrier against an authored synthetic regression set. Every fixture has
a reference rationale. The gate requires at least 80% accuracy, precision, recall,
and usefulness among accepted insights. Operational diagnostics, implementation
data, generic claims, and unsupported hypotheses are negative controls.

## Executed retrieval ablation

`PYTHONPATH=src:. python -m benchmarks.retrieval_quality_benchmark` creates a
versioned controlled corpus and executes five retrieval configurations: lexical-only,
dense-only, lexical/vector hybrid, graph lexical, and graph hybrid.
It records query-level observations, p50/p95/p99 latency, negative rejection,
stale-delete behavior, citation support, and a paired bootstrap confidence interval.

This fixture is an internal causal regression benchmark. It does not establish
external validity or measure the optional HippoRAG sidecar. Public datasets and
containerized external baselines belong to the confirmatory benchmark profile.

Write an evidence bundle with manifests, raw JSONL observations, and checksums:

```bash
PYTHONPATH=src:. python -m benchmarks.retrieval_quality_benchmark \
  --output reports/retrieval-benchmark.json \
  --evidence-root reports/benchmarks
```

## Release gate composition

`PYTHONPATH=src:. python -m benchmarks.maturity_release_gate` requires semantic
search, insight usefulness, cognitive graph integrity, graph performance, executed
retrieval ablation, and Judge reference-fixture agreement to pass. The synthetic
Judge fixture does not count as independent human calibration. CI fixtures are
regression evidence; they must not be described as independent comparative evidence.

## Performance and comparative runners

From `apps/api`, with `PYTHONPATH=src:.`:

```bash
python -m benchmarks.http_load_benchmark --base-url http://127.0.0.1:8000 --path /health
python -m benchmarks.worker_queue_benchmark --jobs 1000 --evidence-root ../../reports/evidence
python -m benchmarks.graph_performance_benchmark --on-disk --evidence-root ../../reports/evidence
python -m benchmarks.instrumentation_overhead_benchmark --evidence-root ../../reports/evidence
python -m benchmarks.fault_injection_benchmark --evidence-root ../../reports/evidence
python -m benchmarks.external_retrieval_baseline --corpus corpus.jsonl --queries queries.jsonl --qrels qrels.jsonl --method bm25
python -m benchmarks.full_evaluation --repository-root ../.. --output-root ../../reports/evaluation --profile S
```

`benchmark_profiles.py` is the source of truth for S/M/L/XL scales and A0-A6/G0-G3 controls.
`maturity_v3.py` rejects missing, stale, or overclaimed evidence rather than inferring maturity from
feature presence.
