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
- **RQ7:** Does context-scoped user feedback reduce recurrence of rejected artifacts and correction
  effort without suppressing valid knowledge in unrelated contexts?

## Primary Metrics

Retrieval uses Recall@10, MRR, NDCG@10, negative rejection, stale-evidence rejection, and latency
p50/p95/p99. Answers use claim faithfulness, citation precision, unsupported-claim rate, answer
correctness, refusal correctness, and cost per successful answer. Graph evaluation uses entity/node
precision and recall, edge precision and recall, ontology violations, duplicate rate, orphan rate,
provenance coverage, and path-answer success. Systems evaluation uses request rate, error rate,
queue wait, drain rate, CPU, RSS, database growth, payload bytes, LCP, CLS, long tasks, and heap.
Feedback adaptation uses rejected-pattern recurrence, accepted-artifact precision, correction edit
distance, decisions overridden by later feedback, unrelated-context spillover, and time-to-resolution.

## Judge Evaluation Design

Judge quality is measured against human review rather than treated as ground truth. BerryBrain
retains each model verdict and reports comparable count, exact agreement, quadratic weighted
kappa, false-acceptance rate, and false-rejection rate. Enforcement remains blocked until the
declared calibration thresholds are met.

The committee uses role separation because RAG quality is multidimensional:

| Role | Primary failure targeted |
| --- | --- |
| Faithfulness | Claims not entailed by cited source evidence |
| Relevance | Artifacts that are semantically true but not useful in the current context |
| Contradiction | Conflicts, unsupported inference, and incidental cross-domain shared words |
| Source quality | Weak provenance, insufficient coverage, or confidence unsupported by evidence |
| Ontology consistency | Invalid class, property, direction, naming, or neighborhood semantics |

The default committee uses three distinct compatibility-tested, non-generator models from the
active provider. Discovery and compatibility are separate measurements: a catalog entry must also
complete the Judge's structured JSON request on the active endpoint. This operationalizes panel
diversity without embedding provider catalogs in source. Provider/model, prompt version, role,
rubric, reasoning, latency, and availability are retained per call. Failed members are reported but
excluded from consensus and score; fewer than two valid members means no committee decision.

### Research basis

- Es et al., [Ragas: Automated Evaluation of Retrieval Augmented Generation](https://arxiv.org/abs/2309.15217), separates retrieval relevance, faithfulness, and generation quality.
- Ru et al., [RAGChecker](https://arxiv.org/abs/2408.08067), motivates fine-grained retrieval and generation diagnostics plus human-correlated meta-evaluation.
- Liu et al., [G-Eval](https://arxiv.org/abs/2303.16634), supports structured evaluation criteria while documenting model bias risk.
- Kim et al., [Prometheus 2](https://arxiv.org/abs/2405.01535), supports custom criteria and evaluator specialization aligned with human judgments.
- Verga et al., [Replacing Judges with Juries](https://arxiv.org/abs/2404.18796), motivates multiple disjoint model families to reduce single-judge and intramodel bias.

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
- Learning evaluation compares feedback disabled/enabled on the same ordered event stream. It must
  include related and unrelated contexts, correction reversals, and deletion/regeneration probes.

## Acceptance

Candidate thresholds are frozen after a pilot and before confirmatory analysis. Mandatory integrity,
privacy, authorization, backup, and stale-evidence gates cap readiness regardless of average quality.
Missing evidence is reported as missing; it is never converted to a passing value.
