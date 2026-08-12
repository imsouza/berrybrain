# BerryBrain Performance, Quality, Maturity, and Thesis Benchmark Plan

Status: planning only  
Plan date: 2026-08-12  
Execution state: not started  
Publication state: commit, tag, push, and release remain prohibited until explicit user approval

## 1. Purpose

This plan defines a reproducible evaluation program for BerryBrain. It covers system performance,
RAG quality, graph quality, AI behavior, reliability, usability, resource efficiency, and product
maturity. It is designed to serve both engineering decisions and an undergraduate thesis.

This document does not claim new benchmark results. All future claims must be generated from
versioned run artifacts and must identify the code revision, image digests, dataset revision,
hardware, model configuration, and statistical procedure used.

## 2. Executive Decision: How BerryBrain Must Be Compared

BerryBrain must not be evaluated with a single comparison.

The primary design is a four-layer evaluation:

1. **Internal ablation study**: compare BerryBrain modes with one component changed at a time.
   This is the strongest way to establish whether graph retrieval, ontology, HippoRAG, Judge,
   clustering, and reranking add measurable value.
2. **External technical baselines**: compare retrieval and generation against standard BM25,
   dense retrieval, hybrid RRF, and vanilla RAG implementations under the same corpus, chunks,
   models, context limit, hardware, and query set.
3. **Historical regression comparison**: compare a release candidate with a pinned BerryBrain
   baseline revision. This detects regressions but does not establish superiority over other
   methods.
4. **Task-level user study**: compare task correctness, completion time, workload, and usability
   against a conventional folder/search workflow or another clearly defined knowledge workflow.

Direct whole-product comparison with Obsidian, Notion, or another proprietary product is optional
and must not be the core algorithmic experiment. Those products expose different feature sets,
retrieval internals, privacy models, and instrumentation. A fair comparison is possible only for
shared user tasks, not for hidden implementation details.

## 3. Preliminary Audit Findings

The repository already has valuable regression gates, but they are not yet sufficient as thesis
evidence.

### 3.1 Existing strengths

- Deterministic semantic-search fixture with Recall@5, Recall@10, MRR, NDCG@10, negative
  rejection, relationship recall, indexing coverage, stale-evidence checks, and p50/p95 latency.
- Graph projection benchmark for node/edge completeness, payload size, memory, and p50/p95 latency.
- A 10,000-node/40,000-edge browser graph test with load time, interaction p95, geometry, and heap.
- Insight usefulness fixtures with accuracy, precision, recall, and accepted-usefulness rate.
- Cognitive graph checks for concept and connection precision/recall, provenance, cleanup, and
  idempotency.
- Judge calibration support with weighted kappa, false acceptance, and false rejection.
- Web performance budgets for navigation, script transfer, LCP, CLS, and an INP candidate.
- API, Worker, Web, sidecar, security, SBOM, architecture, and container CI gates.

### 3.2 Critical inconsistencies and evidence gaps

- `retrieval_quality_benchmark.py` currently assigns hit counts, citation counts, and negative-case
  outcomes as constants. It calculates arithmetic correctly but does not execute retrieval. It is
  a placeholder report, not valid comparative evidence.
- The release gate excludes `retrieval_quality_benchmark.py` and the Judge calibration report,
  despite README claims that imply those properties are release evidence.
- The graph API benchmark uses an in-memory SQLite database and calls a Python service directly.
  It does not measure HTTP, authentication, serialization over the network, on-disk SQLite,
  concurrent users, or worker contention.
- The graph unit test exercises only 200 nodes and 600 edges. The release gate runs the larger
  default, but neither path stores a complete run manifest or uncertainty estimate.
- Seven latency samples are too few for defensible p95/p99 inference.
- Semantic search uses deterministic fixture embeddings. This is useful for CI regression but does
  not measure real embedding models, model drift, multilingual input, or domain transfer.
- The insight benchmark has twelve embedded examples and uses rules closely aligned with those
  examples. It needs an independent, blinded, human-labeled test set.
- Most quality metrics are point estimates without bootstrap confidence intervals, effect sizes,
  or significance tests.
- No standard public retrieval corpus or multi-hop QA corpus is currently used.
- No controlled external baseline is currently executed.
- No sustained API load, worker throughput, queue saturation, soak, or chaos benchmark exists.
- Web performance is a single lab run. It lacks calibrated CPU/network profiles, repeated samples,
  field data, and confidence intervals.
- README benchmark numbers are manually copied and can drift from current code or hardware.
- `second-brain-maturity-v2.md` is dated 2026-07-21 and still scores removed or changed features,
  including the former review workflow. Its `65/100` and `62/100` scores are stale.
- Current documentation mixes regression-test evidence, measured benchmark results, architecture
  claims, and aspirational maturity claims.
- Benchmark runs do not yet produce one immutable evidence bundle with commit SHA, dirty-state
  hash, image digests, hardware, OS, model IDs, prompts, random seeds, and raw observations.

## 4. Research Scope

### 4.1 System under test

The benchmark covers:

- Next.js web application and browser graph renderer.
- FastAPI HTTP API and SQLite persistence.
- Worker queue, leases, retries, idempotency, agent monitoring, and background pipelines.
- Lexical, vector, hybrid, graph, ontology-aware, and HippoRAG retrieval.
- Ask, Ask Flow, suggestions, citations, refusal, and insight creation.
- Extraction from Markdown, documents, images, audio, and video where dependencies are available.
- Graph node/edge extraction, ontology assignment, clustering, confidence, and lifecycle changes.
- Judge behavior and AI routing.
- Backup, restore, migration, recovery, privacy, and resource consumption.

### 4.2 Out of scope unless separately approved

- Training or fine-tuning foundation models.
- Claims that one AI provider is universally better than another.
- Benchmarking private user vault content without explicit consent and anonymization.
- Treating an LLM judge as ground truth without human calibration.
- Marketing claims based on synthetic CI fixtures alone.
- Publishing secrets, prompts containing private data, raw vault content, or provider credentials.

## 5. Candidate Thesis Directions

The benchmark supports several thesis themes. The final theme should be selected before the
confirmatory experiment so the hypotheses and primary outcomes can be preregistered.

### Theme A: Ontology-aware graph RAG for personal knowledge retrieval

Primary question: does typed graph and ontology retrieval improve multi-hop evidence retrieval and
answer faithfulness over lexical, dense, and conventional hybrid RAG?

### Theme B: Quality-performance trade-offs in local-first second-brain systems

Primary question: what quality, latency, memory, privacy, and cost trade-offs arise when graph,
HippoRAG, Judge, and AI enrichment are enabled?

### Theme C: Evidence-oriented AI agents for maintaining personal knowledge graphs

Primary question: do automatic agents improve graph completeness, useful insight discovery, and
gap detection without increasing unsupported claims or user workload?

### Theme D: Confidence calibration and human control in AI-generated knowledge graphs

Primary question: do evidence-derived confidence intervals and Judge decisions predict human
acceptance and correctness better than raw model confidence?

### Theme E: Usability and cognitive support of graph-enhanced personal knowledge management

Primary question: does BerryBrain improve task correctness, discovery time, perceived usability,
and workload compared with folder search or vanilla RAG?

## 6. Research Questions and Hypotheses

### RQ1: Retrieval quality

- **RQ1**: How much do hybrid, graph, ontology, and HippoRAG stages change single-hop and multi-hop
  retrieval quality?
- **H1**: Graph-aware retrieval produces a positive paired improvement in multi-hop Recall@10 and
  NDCG@10 over hybrid RRF without graph traversal.
- **H2**: The full retrieval path does not materially regress factual single-hop retrieval.

### RQ2: Grounded answer quality

- **RQ2**: Does the full BerryBrain pipeline improve faithfulness, citation correctness,
  completeness, and refusal behavior over vanilla RAG?
- **H3**: Full BerryBrain reduces unsupported-claim rate while preserving answer relevance.

### RQ3: Knowledge-graph quality

- **RQ3**: Are node types, canonical labels, ontology classes, clusters, and directed edge
  properties correct and useful for retrieval?
- **H4**: Ontology validation reduces invalid and duplicate graph artifacts without reducing
  recall beyond the preregistered non-inferiority margin.

### RQ4: Performance and scalability

- **RQ4**: How do latency, throughput, memory, storage, browser responsiveness, and cost scale with
  vault and graph size?
- **H5**: Progressive graph loading keeps interaction latency within its UI budget at 10,000 nodes.
- **H6**: Quality-positive graph modes have an acceptable and quantified latency/resource premium.

### RQ5: Reliability

- **RQ5**: Does the system preserve knowledge integrity under retries, crashes, rate limits,
  stale leases, sidecar outages, and restarts?
- **H7**: Fault injection causes no lost confirmed knowledge, no duplicate promoted artifact, and
  bounded automatic recovery.

### RQ6: User utility

- **RQ6**: Does BerryBrain help users complete knowledge tasks more accurately and efficiently?
- **H8**: BerryBrain improves task correctness or completion time without increasing NASA-TLX
  workload compared with the selected baseline workflow.

## 7. Evaluation Framework

The overall quality model will map evidence to ISO/IEC 25010:2023 product-quality characteristics:
functional suitability, performance efficiency, compatibility, interaction capability,
reliability, security, maintainability, flexibility, and safety. Cognitive quality is evaluated as
a separate BerryBrain-specific layer rather than being hidden inside one software-quality score.

No single composite score may replace the underlying metrics. A maturity score is a navigation
aid; every score must link to evidence and uncertainty.

## 8. Comparator Matrix

### 8.1 Internal ablations: primary causal comparison

| ID | Retrieval configuration | Purpose |
|---|---|---|
| A0 | SQLite FTS lexical only | Sparse baseline |
| A1 | Dense vector only | Semantic baseline |
| A2 | Lexical + dense with RRF | Conventional hybrid baseline |
| A3 | A2 + typed graph traversal | Isolate graph contribution |
| A4 | A3 + ontology aliases, direction, and confidence filters | Isolate semantic-contract contribution |
| A5 | A4 + HippoRAG | Isolate multi-hop sidecar contribution |
| A6 | A5 + reranking/Judge where applicable | Measure full quality and cost |

All ablations must use the same corpus, chunk boundaries, embedding model, answer model, prompt,
context window, top-k budget, hardware, and query order unless the changed variable requires an
explicit exception.

### 8.2 Generation comparison

| ID | Generation configuration | Purpose |
|---|---|---|
| G0 | Closed-book model, no retrieved context | Negative control |
| G1 | Vanilla RAG over A2 | Standard RAG baseline |
| G2 | BerryBrain over A4 | Graph and ontology contribution |
| G3 | Full BerryBrain over A6 | End-to-end result |

The same generator, temperature, seed when supported, maximum output tokens, and context limit must
be used. Retrieval and generation metrics must be reported separately.

### 8.3 External technical baselines

- A standard BM25 reference implementation.
- A standard dense retriever using the same embedding model.
- A standard hybrid RRF implementation.
- A minimal vanilla RAG pipeline with no BerryBrain graph or agent behavior.
- Optional research baseline from the same multi-hop dataset when its implementation and license
  permit reproducible execution.

Each baseline must be containerized, version-pinned, and configured from a checked-in manifest.
Native defaults may be reported as a secondary experiment, but the controlled same-resources
comparison is primary.

### 8.4 Historical baseline

- Pin a clean BerryBrain baseline tag or commit before benchmark implementation.
- Compare candidate versus baseline with the same runner and datasets.
- Use this only for regression and improvement claims within BerryBrain.
- Never use a dirty worktree as the published historical baseline.

### 8.5 User-workflow baseline

Choose one before ethics approval and recruitment:

- Folder and full-text search without AI.
- Vanilla RAG over the same notes.
- An external personal-knowledge application limited to equivalent tasks.

Use a within-subject crossover design with randomized or Latin-square task order to reduce
participant and learning effects.

## 9. Dataset Program

### 9.1 Dataset families

| Dataset | Purpose | Required truth |
|---|---|---|
| Controlled synthetic vault | Scale, fault injection, deterministic regression | Generation seed and exact expected topology |
| Curated personal-knowledge vault | Ecological validity | Relevant notes/chunks, answers, source facts, nodes, edges, insight labels |
| BEIR subsets | External heterogeneous retrieval validity | Official qrels |
| HotpotQA subset | Explainable multi-hop retrieval | Answers and supporting facts |
| MuSiQue subset | Compositional multi-hop robustness | Answers and supporting chains |
| Attachment corpus | OCR, parsing, transcription, and multimodal ingestion | Ground-truth text and metadata |
| Adversarial corpus | Contradiction, stale evidence, prompt injection, secrets, duplicates | Expected refusal/quarantine outcome |
| Longitudinal event stream | Update/delete/rebuild and concept drift | Expected state after every event |

### 9.2 Scale tiers

At minimum, generate and retain reproducible manifests for:

- S: 100 notes, approximately 500 graph nodes.
- M: 1,000 notes, approximately 5,000 graph nodes.
- L: 10,000 notes, approximately 50,000 graph nodes.
- XL: selected stress profile beyond L, bounded by available hardware and thesis scope.

Actual node and edge counts must be measured, not assumed. Edge density, note-length distribution,
folder depth, attachment mix, update rate, and duplicate rate must be recorded.

### 9.3 Gold-standard construction

- Use at least two independent annotators for graph triples, insight usefulness, and generated
  answer quality.
- Provide an annotation guide with positive, negative, ambiguous, and abstain examples.
- Blind annotators to the system configuration that generated each result.
- Resolve disagreements only after preserving original labels.
- Report Cohen's kappa for two annotators or Krippendorff's alpha for more general annotation.
- Calibrate LLM judges against the held-out human labels; never calibrate and evaluate on the same
  examples.
- Keep train/development/pilot and final test partitions separate.

### 9.4 Data governance

- No real user vault enters the repository without explicit consent.
- Remove names, secrets, credentials, private URLs, and identifying metadata.
- Record dataset license, source, transformation, checksum, and allowed uses.
- Keep benchmark fixtures isolated from production seed paths.
- Treat research fixtures as test evidence, never as production knowledge or demo data.
- Preserve user-authored source language; BerryBrain-generated outputs remain English.

## 10. Metrics

### 10.1 Ingestion and indexing

| Dimension | Metrics |
|---|---|
| Correctness | extraction precision/recall, OCR CER/WER, metadata accuracy, duplicate rate |
| Throughput | notes/s, pages/s, audio minutes processed/minute |
| Latency | queue wait, service time, end-to-end time-to-searchable p50/p95/p99 |
| Reliability | failed jobs, retries, dead letters, lost jobs, duplicate effects, stale artifacts |
| Resources | CPU time, peak RSS, I/O bytes, database growth, embedding storage |

### 10.2 Retrieval

- Recall@1, @5, @10, and @20.
- Precision@k.
- Mean Reciprocal Rank.
- NDCG@10.
- Mean Average Precision where qrels support graded or multiple relevance judgments.
- Multi-hop supporting-fact recall and complete-chain recall.
- Citation precision and citation recall.
- Negative-query rejection and stale/deleted-evidence rejection.
- Retrieval p50/p95/p99 and queries per second.
- Index coverage and time-to-freshness after create/update/delete.

### 10.3 Generated answers and Ask

- Claim-level faithfulness to cited evidence.
- Answer relevance and completeness.
- Citation correctness, completeness, and entailment.
- Unsupported-claim and contradiction rates.
- Correct-refusal true-positive and false-positive rates.
- Exact Match/token F1 only where the dataset supports short factual answers.
- Ask Flow consistency and evidence retention across turns.
- Suggestion grounding, duplicate rate, topic diversity, node coverage, click-through, and time to
  first useful question.
- Time to first grounded response and time to final AI response.
- Input/output tokens, provider cost, and failures per 1,000 requests.

RAGAS-style automated metrics may be supplementary. Human-calibrated claim and citation labels are
the primary evidence for thesis conclusions.

### 10.4 Graph and ontology

- Node-type macro/micro precision, recall, and F1.
- Canonical-label exact and normalized match.
- Entity linking accuracy.
- Directed edge-property precision, recall, and F1.
- Complete triple accuracy: source, property, target.
- Ontology violation and quarantine rates.
- Duplicate-node and duplicate-edge rates.
- Provenance/evidence coverage.
- Cluster ARI/NMI when gold clusters exist; silhouette and stability as secondary unsupervised
  measures.
- Graph connectivity, isolated-node ratio, component count, degree distribution, and density.
- Update/delete stale-artifact count and convergence time.
- Confidence calibration using Brier score, log loss, reliability diagrams, expected calibration
  error, and interval coverage.

### 10.5 Insight and agent quality

- Insight precision, recall, usefulness, novelty, actionability, and evidence sufficiency.
- Human accept/reject/abstain rate by insight type.
- Gap-discovery precision and coverage.
- Time from evidence arrival to surfaced insight.
- Repeated or semantically duplicate insight rate.
- Agent intervention yield: useful changes divided by attempted changes.
- Judge false acceptance, false rejection, weighted kappa, and calibration by artifact type.
- Improvement after enrichment versus the un-enriched artifact in paired blind review.

### 10.6 API, worker, database, and infrastructure

- HTTP p50/p90/p95/p99, throughput, saturation point, and error rate by endpoint.
- Cold-start and warm-steady-state results.
- Concurrent-user profiles at 1, 5, 10, 25, and 50 clients, adjusted after pilot.
- Worker queue depth, wait time, service time, throughput, utilization, retry rate, and drain time.
- SQLite transaction latency, lock wait, busy errors, WAL size, checkpoint time, query plans, and
  file growth.
- Container CPU, RSS, network, block I/O, process count, restarts, and healthcheck failures.
- Optional energy measures through RAPL/NVML when hardware access is stable.

### 10.7 Web and graph UI

- LCP, INP, CLS, TTFB, FCP, and Total Blocking Time in controlled lab profiles.
- JavaScript transfer, parsed bundle size, request count, and hydration cost.
- Route navigation and lazy-panel open time.
- Graph first visual, complete load, fit-to-view, zoom, hover, drag, and node-open p50/p95/p99.
- Frame time, long tasks, dropped-frame ratio, canvas pixel validity, and heap growth.
- Desktop/mobile overflow, text clipping, and accessibility violations.
- Soak behavior after repeated graph navigation and Ask sessions.

### 10.8 Reliability, recovery, security, and privacy

- Recovery time and data integrity after API/worker/sidecar restart.
- Behavior under provider `429`, timeout, invalid JSON, partial stream, and wrong model response.
- Duplicate delivery, stale lease, dead-letter, cancellation, and replay behavior.
- Backup RPO/RTO, restore duration, checksum verification, and rollback success.
- Prompt-injection success rate, unsafe URL rejection, secret leakage, authorization failures, and
  cross-session data isolation.
- High/critical vulnerability count, SBOM completeness, and image provenance.

### 10.9 Human study

- Task success and answer correctness.
- Completion time and number of interactions.
- Evidence inspection and correction behavior.
- System Usability Scale score.
- NASA-TLX overall and subscale workload.
- Trust calibration: confidence when correct versus confidence when wrong.
- Qualitative themes from a predefined coding protocol.

## 11. Workload Scenarios

### 11.1 Canonical user journeys

1. Create a note and measure time until searchable, graphed, clustered, and enriched.
2. Update a note and verify stale evidence disappears before new evidence is promoted.
3. Delete a note or graph node and verify complete graph/retrieval convergence.
4. Ask single-hop, multi-hop, structural graph, ontology, gap, contradiction, and no-evidence
   questions.
5. Continue an Ask Flow and create an insight from grounded evidence.
6. Accept/reject an insight and observe recalculation.
7. Research a gap and verify untrusted external evidence cannot be promoted automatically.
8. Drag, zoom, hover, inspect, edit, delete, and return from a graph node.
9. Import representative attachment types.
10. Backup, destroy an isolated test state, restore, and compare checksums and semantic outputs.

### 11.2 Load profiles

- **Smoke**: one user, small vault, functional and metric plumbing validation.
- **Steady**: realistic read/write mix for 15 minutes after warm-up.
- **Ramp**: increase clients until latency or errors violate the preregistered SLO.
- **Spike**: sudden Ask and graph-read burst.
- **Soak**: 4-8 hours to detect leaks, queue drift, and database growth.
- **Stress**: continue beyond the supported envelope to identify failure mode and recovery.
- **Fault**: inject provider, sidecar, network, process, and storage failures.

## 12. Experimental Protocol

### 12.1 Reproducibility controls

- Run only from a clean, pinned commit for publishable results.
- Record dirty diff hash for exploratory runs and mark them non-publishable.
- Pin Docker image digests, Python/Node/browser versions, model IDs, prompt versions, and dataset
  checksums.
- Record CPU model, core count, RAM, storage, GPU/VRAM, kernel, Docker, filesystem, power mode, and
  thermal state.
- Disable unrelated workloads or record system contention.
- Separate local-model and cloud-provider experiments.
- Fix random seeds and temperature where supported.
- Randomize query order and system order with a stored seed.
- Distinguish cold-cache, warm-cache, and pre-indexed results.
- Perform warm-up iterations that are excluded from measured samples.

### 12.2 Sampling

- Use a pilot only to estimate variance and validate instrumentation.
- Freeze hypotheses, primary metrics, datasets, exclusions, and gates before confirmatory runs.
- Use at least 30 independent latency observations per cell for initial lab comparison; increase
  based on variance and power analysis.
- Use query-level paired observations for retrieval and generation comparisons.
- Repeat non-deterministic generation enough times to estimate within-query variance.
- Calculate human-study sample size from an a priori power analysis; do not choose a convenient
  participant count and claim adequate power afterward.

### 12.3 Statistical analysis

- Report count, mean, standard deviation, median, p90, p95, p99, minimum, and maximum where relevant.
- Report 95% bootstrap confidence intervals for retrieval, quality, latency, and effect differences.
- Use paired bootstrap or permutation tests for query-level IR comparisons.
- Use paired t-tests only when assumptions are defensible; otherwise use Wilcoxon signed-rank.
- Report effect size: Cohen's d for suitable continuous paired outcomes and Cliff's delta for
  non-normal outcomes.
- Correct multiple comparisons with Holm's procedure.
- Report non-inferiority margins before testing regression-sensitive metrics.
- Include failures and timeouts in denominators; never drop them as latency outliers.
- Publish both statistical significance and practical effect size.

### 12.4 Run invalidation criteria

Invalidate or mark a run exploratory when:

- code, dataset, model, or prompts change during the run;
- the host experiences unrecorded competing load or thermal throttling;
- cache state differs from the declared profile;
- required spans or raw observations are missing;
- external provider rate limiting exceeds the profile's declared tolerance;
- browser, driver, or image digest differs between comparison cells;
- annotation blinding is broken;
- exclusion rules are changed after results are observed.

## 13. Instrumentation and Tools

### 13.1 Observability foundation

- Add OpenTelemetry spans across Web request, API route, retrieval stages, AI invocation, job claim,
  worker handler, database transaction, and sidecar call.
- Propagate one correlation ID through HTTP, jobs, model calls, graph changes, and notifications.
- Export Prometheus-compatible counters, gauges, and histograms.
- Use Grafana dashboards for exploratory diagnosis, not as the authoritative result store.
- Store raw benchmark events as JSONL or Parquet with a documented schema.

### 13.2 Load and profiling tools

- Use k6 or Locust for repeatable HTTP load; select one in the implementation spike and pin it.
- Use Playwright plus the `web-vitals` library and Lighthouse CI for browser lab measurements.
- Use Chromium tracing for long tasks, frame timing, layout, and heap investigation.
- Use `py-spy`, `cProfile`, or Scalene for Python hotspots after a reproducible regression exists.
- Use `EXPLAIN QUERY PLAN`, SQLite tracing, WAL metrics, and database-size snapshots.
- Use container/cgroup metrics or cAdvisor for CPU, RSS, I/O, and network.
- Use `hyperfine` only for isolated command cold/warm timing, not end-to-end distributed claims.

Tools must not be added merely because they are popular. Every tool must map to a metric and have
an automated export path.

## 14. Benchmark Artifact Architecture

Create the following structure during implementation:

```text
benchmarks/
  README.md
  schemas/
    run-manifest.schema.json
    observation.schema.json
    annotation.schema.json
  datasets/
    manifests/
    qrels/
    queries/
    gold-graphs/
  workloads/
    api/
    worker/
    browser/
    faults/
  runners/
  analysis/
  baselines/
reports/
  benchmarks/
    <run-id>/
      manifest.json
      raw/
      summary.json
      tables/
      plots/
      environment.txt
      checksums.txt
```

The run manifest must include:

- unique run ID and UTC timestamps;
- exploratory or confirmatory classification;
- git commit and clean/dirty status;
- Docker image digests;
- dataset and qrels checksums;
- hardware and software environment;
- component configuration and ablation ID;
- model/provider/prompt/chunking/retrieval settings;
- random seeds and cache state;
- repetitions, warm-ups, timeouts, and concurrency;
- raw artifact paths and checksums;
- failures, exclusions, and invalidation state.

## 15. Maturity Model V3

Replace static impression-based percentages with evidence levels per capability.

### 15.1 Evidence levels

| Level | Meaning |
|---:|---|
| 0 | Absent or contradicted |
| 1 | Implemented but unverified |
| 2 | Unit/integration regression evidence |
| 3 | Representative reproducible benchmark evidence |
| 4 | Independent baseline comparison and fault evidence |
| 5 | Longitudinal field or human-study evidence |

### 15.2 Capability groups

- Capture and extraction.
- Durable semantic memory.
- Retrieval and grounded inference.
- Knowledge graph and ontology.
- Insights and continuous agents.
- Transparency, confidence, and user control.
- Performance efficiency and scalability.
- Reliability and recoverability.
- Security, privacy, and safety.
- Interaction quality and accessibility.
- Maintainability and architecture.
- Reproducibility, governance, and documentation.

### 15.3 Scoring rules

- Every awarded level links to a current run artifact.
- Missing evidence remains missing; it is never inferred from feature presence.
- A failed mandatory safety or data-integrity gate caps overall readiness regardless of average.
- Scores include confidence and date; expired evidence is marked stale.
- Synthetic CI evidence cannot award Level 4 or Level 5.
- A `100% mature` claim is prohibited. Report achieved levels and remaining evidence instead.

## 16. Candidate Acceptance Gates

These are initial engineering gates. Quality and comparative gates must be frozen after the pilot
and before confirmatory analysis.

### 16.1 Retrieval and answer quality

- Recall@10 >= 0.85 and MRR >= 0.75 on the representative private benchmark.
- NDCG@10 >= 0.85 where graded qrels exist.
- Citation precision >= 0.95.
- Claim faithfulness >= 0.90.
- Unsupported claim rate <= 0.02.
- Multi-hop graph/HippoRAG gain must have a positive 95% paired confidence interval and a
  preregistered practically meaningful effect.
- Negative and stale-evidence cases must not promote knowledge.

### 16.2 Graph and confidence

- Directed edge precision >= 0.85 on independent human labels.
- Generated artifact provenance coverage = 1.00.
- Ontology violations promoted as active knowledge = 0.
- Confidence calibration must beat or be non-inferior to the uncalibrated score baseline on Brier
  score and ECE.

### 16.3 Reliability

- Lost confirmed artifacts = 0 in the fault matrix.
- Duplicate promoted effects = 0 under duplicate delivery and replay.
- Backup/restore checksum and semantic-state verification = 100% for required data.
- Provider outage produces no invented knowledge and recovers without manual data repair.

### 16.4 Web

- Use the current Core Web Vitals `good` thresholds for LCP, INP, and CLS at the 75th percentile.
- No horizontal overflow or text occlusion in supported viewports.
- WCAG 2.2 AA automated checks pass; critical workflows receive manual keyboard and screen-reader
  review.
- The 10,000-node graph keeps interaction p95 below the existing 200 ms release budget.

### 16.5 Release evidence

- All required reports are generated from raw artifacts.
- No result is manually copied into canonical documentation.
- Every published table includes revision, dataset, hardware profile, sample size, and uncertainty.
- Exploratory and invalid runs cannot satisfy release gates.

## 17. Documentation Program

The README should remain operationally readable. Detailed academic material belongs in canonical
documents linked by README and rendered in the landing Docs.

### 17.1 New canonical documents

- `docs/evaluation-methodology.md`: research design, metrics, statistics, and validity.
- `docs/benchmark-protocol.md`: exact commands, profiles, manifests, and fault matrix.
- `docs/benchmark-results.md`: generated current results and confidence intervals.
- `docs/maturity-model.md`: evidence-level maturity V3 and current scorecard.
- `docs/reproducibility.md`: environment capture, artifact checksums, and reproduction steps.
- `docs/datasets.md`: corpus manifests, annotation guide, licenses, and privacy controls.
- `docs/limitations.md`: internal/external validity, provider variance, benchmark leakage, and scope.
- `docs/thesis-research-protocol.md`: RQs, hypotheses, variables, power analysis, ethics, and planned
  analysis.

### 17.2 README rewrite

- Add a concise `Evaluation and Evidence` section.
- Distinguish regression tests, benchmark evidence, and field evidence.
- Show only results generated by the latest valid release manifest.
- Link each result to its report and reproduction command.
- Add hardware, dataset, sample size, and confidence interval to every headline result.
- Replace stale test counts and hand-copied benchmark numbers with generated content.
- Replace unsupported maturity percentages with evidence levels.
- Keep installation, operation, security, architecture, and troubleshooting complete.

### 17.3 Landing Docs rewrite

- Add `Benchmark Methodology`, `Measured Performance`, `RAG and Graph Quality`, `Reliability`,
  `Maturity`, `Reproducibility`, `Research Use`, and `Limitations` sections.
- Render benchmark tables from the same machine-readable summary used by README.
- Explain every metric in plain English without overstating results.
- Separate current measured evidence from planned work.
- Include benchmark date, version, environment, and dataset scope.
- Keep all BerryBrain-authored text in English.

### 17.4 Existing-document reconciliation

- Mark dated QA and release reports as historical snapshots.
- Replace `second-brain-maturity-v2.md` with V3 or add an explicit archived banner.
- Reconcile `requirements-traceability.md` with the new benchmark IDs and evidence paths.
- Update `docs/architecture.md` with telemetry boundaries and benchmark data flow.
- Update the changelog only after implementation and validated results.
- Add a documentation consistency CI check that fails when canonical result blocks differ from the
  latest signed summary.

## 18. Execution Phases

### Phase 0: Research freeze and baseline

- [ ] Select the thesis theme and primary outcome.
- [ ] Define the system boundary and supported hardware profiles.
- [ ] Pin a clean BerryBrain baseline revision.
- [ ] Preregister RQs, hypotheses, primary metrics, exclusions, and statistical tests.
- [ ] Complete ethics/LGPD review before collecting participant or private-vault data.

External dependency status is maintained in `docs/external-evidence-register.md`; no result is
substituted for the open approvals, datasets, reviewers, participants, or independent evaluator.

Exit: approved research protocol and immutable baseline manifest.

### Phase 1: Benchmark integrity repair

- [x] Replace hardcoded retrieval benchmark outcomes with executed queries and scored qrels.
- [x] Add retrieval-quality and Judge-calibration evidence to the release-gate graph.
- [x] Separate tiny CI smoke fixtures from representative benchmark profiles.
- [x] Add run manifests, raw observations, checksums, and schema validation.
- [x] Prevent production code from loading benchmark fixtures.

Exit: every benchmark metric is computed from observations, never assigned as a result constant.

### Phase 2: Instrumentation

- [ ] Add correlation propagation and stage-level OpenTelemetry spans.
- [ ] Add API, worker, AI, retrieval, graph, and database metrics.
- [x] Add browser Web Vitals, graph frame, and heap collection.
- [x] Add privacy filters and content-free metric labels.
- [x] Validate metric overhead with instrumentation on/off ablation.

Exit: one user journey can be traced end to end without exposing note content.

### Phase 3: Datasets and annotation

- [x] Build deterministic S/M/L scale manifests.
- [ ] Import licensed BEIR, HotpotQA, and MuSiQue subsets.
- [ ] Build the curated personal-knowledge test set.
- [ ] Build attachment, adversarial, and longitudinal sets.
- [ ] Write annotation guide and tool.
- [ ] Complete blinded dual annotation and agreement analysis.

Exit: versioned datasets with licenses, qrels/gold labels, checksums, and acceptable agreement.

### Phase 4: Internal ablation runners

- [x] Implement A0-A6 and G0-G3 configuration manifests.
- [x] Guarantee shared chunks/models/context limits across controlled cells.
- [ ] Add query-level retrieval, generation, graph, and cost observations.
- [ ] Add deterministic replay and cache controls.

Exit: one command executes a complete paired ablation and emits a valid evidence bundle.

### Phase 5: External baselines

- [ ] Containerize and pin BM25, dense, hybrid, and vanilla RAG baselines.
- [ ] Validate corpus/query parity.
- [ ] Run native-default variants only as secondary evidence.
- [ ] Record licensing and implementation deviations.

Exit: fair task-level technical comparison with reproducible baseline manifests.

### Phase 6: Performance and scale

- [ ] Add HTTP steady/ramp/spike/soak workloads.
- [ ] Add worker queue throughput and saturation workloads.
- [x] Add on-disk SQLite and optional vector/sidecar profiles.
- [x] Repeat browser performance under desktop/mobile and CPU/network profiles.
- [ ] Profile only statistically reproducible bottlenecks.
- [ ] Optimize and rerun the full comparison, not only the improved microbenchmark.

Exit: scalability curves, bottleneck attribution, and before/after effect sizes.

### Phase 7: Reliability and security experiments

- [x] Implement provider, sidecar, process, network, disk, and malformed-output faults.
- [ ] Measure integrity, recovery, retries, dead letters, and user-visible degradation.
- [x] Run backup/restore and upgrade matrices.
- [x] Run prompt-injection, secret, unsafe URL, authorization, and isolation cases.

Exit: fault matrix with zero unresolved critical integrity or privacy failure.

### Phase 8: Human study, if selected

- [ ] Obtain ethics approval or institutional exemption.
- [ ] Complete power analysis and recruitment criteria.
- [ ] Pilot tasks without including pilot results in confirmatory analysis.
- [ ] Run randomized within-subject sessions.
- [ ] Collect task, SUS, NASA-TLX, trust, and qualitative evidence.
- [ ] Analyze with the preregistered protocol.

Exit: anonymized data, agreement checks, statistical report, and limitations.

### Phase 9: Maturity reassessment

- [x] Implement Maturity V3 evidence levels.
- [x] Re-score every capability from current artifacts.
- [x] Apply mandatory safety and integrity caps.
- [x] Remove stale scores and unsupported `100%` language.

Exit: current, evidence-linked maturity report.

### Phase 10: Documentation and TCC package

- [x] Write all canonical documents in Section 17.
- [x] Generate README and landing Docs result blocks from summaries.
- [x] Add architecture and benchmark data-flow diagrams.
- [x] Publish data dictionary, protocol, raw schema, analysis scripts, and limitations.
- [x] Produce thesis-ready tables and plots with captions and provenance.
- [x] Add a replication checklist for an independent evaluator.

Exit: repository, Docs, README, and thesis evidence use one consistent source of truth.

### Phase 11: Final validation and publication hold

- [x] Run API, Worker, HippoRAG, Web, benchmark, security, backup, and documentation gates.
- [ ] Reproduce the confirmatory report from a clean environment.
- [x] Verify every published number against the signed result bundle.
- [x] Review language integrity and confirm all system-authored text is English.
- [ ] Obtain explicit user approval before commit, tag, push, or main publication.

Exit: reproducible release candidate; publication still blocked until explicit approval.

## 19. CI Cadence

| Cadence | Scope | Blocking |
|---|---|---|
| Pull request | deterministic smoke, small graph, schema, lint, unit/integration, UI budget | Yes |
| Nightly | representative retrieval, graph quality, Judge drift, medium scale | Yes after stabilization |
| Weekly | load, soak, large graph, on-disk database, fault subset | Alert then gate after baseline |
| Release candidate | all datasets, ablations, baselines, security, backup, clean reproduction | Yes |
| Field/longitudinal | opt-in aggregate usability/reliability only | Never without privacy review |

## 20. Threats to Validity

### Internal validity

- Cache contamination, model nondeterminism, prompt changes, host contention, and non-equivalent
  baseline settings can create false effects.
- Component interactions mean ablations must be interpreted as configuration effects, not universal
  causal laws.

### Construct validity

- Recall and faithfulness do not fully represent learning value.
- LLM judges can share biases with answer models.
- Graph density is not graph usefulness.
- Acceptance rate can reflect user fatigue rather than correctness.

### External validity

- Public QA corpora differ from personal notes.
- One owner's vault cannot represent all knowledge-management behavior.
- Cloud-provider latency and quality vary by region and time.
- Results from one hardware profile do not generalize to all self-hosted systems.

### Conclusion validity

- Small samples, many metrics, unreported failures, and post-hoc threshold changes can create false
  conclusions.
- Confidence intervals and effect sizes are mandatory; isolated best runs are prohibited.

## 21. Reference Methodology

- ISO/IEC 25010:2023 product quality model:
  https://www.iso.org/standard/78176.html
- BEIR heterogeneous information-retrieval benchmark:
  https://arxiv.org/abs/2104.08663
- RAGAS automated RAG evaluation paper:
  https://aclanthology.org/2024.eacl-demo.16/
- HotpotQA explainable multi-hop QA dataset:
  https://aclanthology.org/D18-1259/
- MuSiQue compositional multi-hop dataset:
  https://arxiv.org/abs/2108.00573
- Core Web Vitals and threshold methodology:
  https://web.dev/articles/vitals
- NASA Task Load Index:
  https://www.nasa.gov/human-systems-integration-division/nasa-task-load-index-tlx/

The literature review must be expanded and formatted according to the institution's required
citation style after the thesis theme is selected.

## 22. Definition of Done

The evaluation program is complete only when:

- all primary metrics come from executed, versioned observations;
- internal ablations and external technical baselines use fair controlled resources;
- representative and public datasets supplement deterministic CI fixtures;
- uncertainty, effect size, failures, and limitations are reported;
- graph, RAG, AI, UI, worker, database, reliability, security, and usability are evaluated at their
  proper layers;
- the maturity model points to current artifacts rather than subjective percentages;
- README, landing Docs, architecture, methodology, results, and thesis material agree;
- an independent evaluator can reproduce the confirmatory report from documented inputs;
- no private user data, secret, mock production knowledge, or manually invented benchmark result is
  published;
- no commit, tag, push, or main update occurs without explicit user approval.
