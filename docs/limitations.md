# Limitations and Threats to Validity

## Current Evidence Boundary

The executable controlled retrieval fixture establishes that graph expansion follows intended
production paths and rejects stale or ignored evidence. It does not establish performance on real
personal knowledge, public multi-hop datasets, or competing graph-RAG systems. Local performance is
hardware-specific. CI calibration fixtures are not human validation.

## Technical Limits

- SQLite is appropriate for local-first ownership but write concurrency and very large graphs need
  measured envelopes.
- Local and cloud models differ in latency, cost, context, determinism, and language behavior.
- Browser memory metrics are Chromium-specific and may be unavailable outside Chromium.
- Confidence is an estimated lower bound from available evidence, not a probability of universal
  truth and not a user-editable field.
- Automatic enrichment depends on provider availability and can be delayed by backoff/cooldown.
- External online research is untrusted evidence until validated and must not bypass provenance.

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
