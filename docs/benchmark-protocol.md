# Benchmark Protocol

## Preconditions

1. Select a clean revision and record `git rev-parse HEAD` plus dirty state.
2. Record CPU, memory, operating system, storage, container limits, Python, Node, browser, models,
   prompts, and sidecar versions.
3. Verify dataset manifests, upstream licenses, SHA-256 checksums, qrels, and split boundaries.
4. Freeze hypotheses, primary metrics, thresholds, exclusions, seeds, and statistical tests.
5. Start isolated services and confirm that no production vault is mounted into benchmark jobs.

## Execution Order

Run deterministic unit and integration gates first. Then run retrieval A0-A6, graph G0-G3,
on-disk graph/database profiles, worker queue profiles, HTTP smoke/steady/ramp/spike/soak/stress,
browser desktop/mobile profiles, provider and storage faults, backup/restore, and security cases.
Randomize paired configuration order where cache or thermal state could bias results.

Scale profiles are S (100 notes/500 nodes), M (1,000/5,000), L (10,000/50,000), and bounded XL.
PR runs use S; nightly runs use M; release candidates use L. Soak and XL runs are scheduled and
must record their actual duration and available hardware.

## Commands

From `apps/api`, with `PYTHONPATH=src:.`:

```bash
python -m benchmarks.retrieval_quality_benchmark --evidence-root reports/evidence
python -m benchmarks.graph_performance_benchmark --on-disk --evidence-root reports/evidence
python -m benchmarks.worker_queue_benchmark --jobs 1000 --evidence-root reports/evidence
python -m benchmarks.http_load_benchmark --base-url http://127.0.0.1:8000 --path /health
python -m benchmarks.instrumentation_overhead_benchmark --evidence-root reports/evidence
python -m benchmarks.full_evaluation --repository-root ../.. --output-root ../../reports/evaluation
```

From `apps/web`, against a running isolated stack:

```bash
BENCHMARK_BASE_URL=http://127.0.0.1:3000 npm run benchmark:browser
```

External retrieval baselines consume JSONL corpus, queries, and qrels. Dense and hybrid runs refuse
to start when real corpus/query embeddings are absent.

## Evidence Bundle

Every runner writes a manifest, summary, raw JSONL observations, and checksums. Retain stdout/stderr,
service logs, resource samples, browser traces for failures, and the final analysis script. Result
directories are immutable. A rerun creates a new run identifier.

## Repetition and Stopping

CI smoke uses the minimum repetitions needed to detect regressions. Representative latency uses at
least 30 post-warm-up samples. Model-backed cells use enough independent runs for stable intervals,
defined during pilot. Ramp stops at the first sustained SLO breach; stress continues only while data
integrity is protected. Soak duration is four to eight hours unless the preregistered thesis scope
states otherwise.

## Failure Policy

Timeouts, provider errors, malformed outputs, and empty results are observations, not exclusions.
Exclude only preregistered environmental invalidations such as host suspension, and retain them in a
separate ledger. Never rerun only failed configurations until they pass.
