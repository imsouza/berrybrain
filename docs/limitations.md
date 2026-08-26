# Limitations and Threats to Validity

## Current Evidence Boundary

The executable controlled retrieval fixture establishes that graph expansion follows intended
production paths and rejects stale or ignored evidence. It does not establish performance on real
personal knowledge, public multi-hop datasets, or competing graph-RAG systems. Local performance is
hardware-specific. Continuous-integration calibration fixtures are not human validation.
The current Judge reference labels are authored synthetic fixtures: weighted kappa `0.9801` is a
regression result with zero human reviews and does not establish calibration. The SciFact BM25 run
is a verified public baseline, but it is not directly comparable with BerryBrain's internal corpus.

## Technical Limits

- SQLite is appropriate for local-first ownership but write concurrency and very large graphs need
  measured envelopes.
- Local and cloud models differ in latency, cost, context, determinism, and language behavior.
- Browser memory metrics are Chromium-specific and may be unavailable outside Chromium.
- Runtime evidence support uses a nominal 95% empirical-Bernstein-style bounded-signal interval.
  Its persisted display score is the midpoint of clipped bounds; retrieval may use the lower bound.
  Heterogeneous signals have not been shown to satisfy the estimator's sampling assumptions, so
  neither value is a calibrated probability of truth. See [Confidence Model](confidence-model.md).
- Automatic enrichment depends on provider availability and can be delayed by backoff/cooldown.
- External online research is untrusted evidence until validated and must not bypass provenance.
- Feedback adaptation changes contextual policy, not model weights. Its long-term benefit, bias,
  stability, and resistance to malicious or accidental feedback have not been established in a
  longitudinal user study.

## Study Limits

Public QA benchmarks differ from evolving personal vaults. Synthetic graphs can encode the expected
algorithmic advantage. LLM judges can share model bias. Participants may learn tasks across
conditions. Acceptance rate mixes usefulness with user fatigue. A small convenience sample cannot
support broad productivity claims.

## Mitigation

Use paired ablations, independent baselines, hidden curated cases, counterbalanced user-study order,
human calibration, longitudinal updates, complete raw observations, preregistration, and explicit
effect intervals. Report null and negative outcomes. Do not claim “100% mature,” “best,” or
“production proven” without corresponding independent evidence.
