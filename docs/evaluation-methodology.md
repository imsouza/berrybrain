# Evaluation Methodology

## Purpose

BerryBrain is evaluated as a local-first knowledge system, not only as a web application or a
language-model wrapper. The evaluation therefore measures retrieval quality, grounded generation,
graph semantics, insight quality, latency, throughput, reliability, security, usability, and
reproducibility. No single score represents the system.

## Comparative Design

Four complementary comparisons answer different questions:

1. **Internal ablation** isolates the contribution of lexical, dense, hybrid, graph, generation,
   Judge, and continuous-agent components under shared corpus, query, model, context, and cache
   controls.
2. **External technical baselines** compare task outcomes with independent BM25, dense cosine,
   reciprocal-rank hybrid, and vanilla RAG implementations using identical corpus and qrels.
3. **Historical regression** compares the same frozen workload across BerryBrain revisions and
   hardware profiles.
4. **Task-level user study** compares complete workflows, time, success, trust calibration, and
   workload. This layer requires an approved protocol and real participants.

Internal ablations provide causal evidence about configurations. External datasets provide
generalization evidence. Neither substitutes for a user study.

## Research Questions

- **RQ1:** Does graph expansion improve multi-hop retrieval without harming factual retrieval?
- **RQ2:** Do Judge and provenance controls reduce unsupported promoted claims?
- **RQ3:** How do latency, throughput, memory, payload size, and queue delay scale with vault size?
- **RQ4:** Does continuous enrichment improve useful insight discovery without unacceptable noise?
- **RQ5:** Does the complete system improve knowledge-work task success compared with search-only
  and non-graph RAG baselines?
- **RQ6:** Are confidence values calibrated against observed correctness and reviewer decisions?

## Primary Metrics

Retrieval uses Recall@10, MRR, NDCG@10, negative rejection, stale-evidence rejection, and latency
p50/p95/p99. Answers use claim faithfulness, citation precision, unsupported-claim rate, answer
correctness, refusal correctness, and cost per successful answer. Graph evaluation uses entity/node
precision and recall, edge precision and recall, ontology violations, duplicate rate, orphan rate,
provenance coverage, and path-answer success. Systems evaluation uses request rate, error rate,
queue wait, drain rate, CPU, RSS, database growth, payload bytes, LCP, CLS, long tasks, and heap.

## Statistical Method

Query-level comparisons are paired. The default uncertainty estimator is a deterministic paired
bootstrap percentile interval with a recorded seed and at least 10,000 resamples for confirmatory
runs. Report absolute effect, relative effect where meaningful, 95% confidence interval, sample
count, exclusions, and raw observations. Multiple primary hypotheses require a preregistered family
and Holm correction. Latency reports distributions and percentiles rather than only means.

Model-backed runs pin provider, model identifier, temperature, prompt version, context limit, and
cache policy. Repeat nondeterministic cells and report variance. A result is not confirmatory when
the revision is dirty, a dataset checksum is absent, or the analysis changed after outcomes were
seen.

## Validity Controls

- Same corpus, chunks, qrels, query order, context limit, and model budget across controlled cells.
- Cold and warm cache runs are separate; warm-up observations are excluded and retained.
- Benchmark fixtures cannot enter production startup or user data.
- Human labels require two reviewers, adjudication, and inter-rater agreement.
- LLM-as-judge scores are secondary until calibrated against human labels.
- Private vault data requires explicit consent, minimization, redaction, and an LGPD review.
- Synthetic data supports regression and fault injection but does not establish ecological validity.

## Acceptance

Candidate thresholds are frozen after a pilot and before confirmatory analysis. Mandatory integrity,
privacy, authorization, backup, and stale-evidence gates cap readiness regardless of average quality.
Missing evidence is reported as missing; it is never converted to a passing value.
