# Evidence-Support And Statistical Uncertainty

## Terminology

BerryBrain currently exposes two different uncertainty constructions that must not be conflated:

| Construction | Used for | Interpretation |
| --- | --- | --- |
| Bounded-signal interval | Runtime graph artifacts | Descriptive uncertainty around heterogeneous evidence-support signals |
| Paired percentile bootstrap | Experimental query-level effects | Sampling uncertainty for a paired benchmark effect on the evaluated query set |

The runtime value is called **evidence support** in documentation. Database and API fields retain
the historical `confidence` name for compatibility. Neither construction is a probability that a
claim is true.

## Runtime Bounded-Signal Interval

The implementation is `estimate_confidence` in
`apps/api/src/berrybrain_api/confidence.py`. Its serialized method identifier is
`empirical-bernstein-bounded-signals-v1`.

For each artifact, callers provide finite scored signals. The estimator:

1. deduplicates signals by source identifier;
2. clips every scored observation to `[0,1]`;
3. retains provenance identifiers as auditable factors but excludes provenance-only prefixes from
   the scored-observation count;
4. returns unavailable bounds when `n=0` and deliberately returns `[0,1]` when `n=1`;
5. otherwise calculates the mean, Bessel-corrected sample variance, and the radius below at the
   default nominal level `1-delta=0.95`;
6. clips the interval to `[0,1]` and persists its midpoint as the compatibility score.

For `n>1`:

```text
r = sqrt(2 s^2 log(3/delta) / n) + 3 log(3/delta) / n
L = max(0, mean - r)
U = min(1, mean + r)
score = (L + U) / 2
```

The radius is based on the empirical Bernstein form used by Audibert, Munos, and Szepesvari,
[Exploration-exploitation tradeoff using variance estimates in multi-armed
bandits](https://doi.org/10.1016/j.tcs.2009.01.016). The code uses Bessel-corrected variance, which
does not narrow the variance term relative to the corresponding biased empirical variance.

## Valid Interpretation

The original concentration result assumes bounded independent observations estimating a common
expectation. BerryBrain combines heterogeneous heuristic, model, and user signals. Their
independence, common-mean interpretation, and empirical coverage have not been established with
human correctness labels. Therefore:

- `95%` is a **nominal construction level**, not demonstrated 95% coverage of factual truth;
- the midpoint is a compatibility display score, not a posterior probability;
- the lower bound is suitable for conservative ordering, but is not calibrated risk;
- a full `[0,1]` interval is expected with one scored signal and can remain wide at small `n`;
- repeated provenance records cannot legitimately increase confidence;
- Wilson and Jeffreys intervals are **not** used by the current runtime implementation.

## Benchmark Effect Interval

The retrieval ablation uses a paired percentile bootstrap over query-level differences. The
exploratory run uses 2,000 seeded resamples. A confirmatory run requires at least 10,000 resamples,
preregistered hypotheses and exclusions, retained raw observations, and multiplicity control where
several primary outcomes are tested. A degenerate interval such as `[1.00,1.00]` on a deterministic
fixture reports no variation in that fixture; it does not establish external generalization.

## Calibration Work Still Required

To claim correctness calibration, freeze the signal definition, collect blinded human labels on a
representative corpus, isolate a calibration set from a held-out evaluation set, and report Brier
score, expected calibration error, reliability diagrams, and empirical interval coverage. Compare
the raw support score with a fitted calibration model and retain negative results. Until then, UI,
documentation, and publications must use **evidence-support interval**, not **probability of truth**.

## Verification Sources

- Runtime estimator: `apps/api/src/berrybrain_api/confidence.py`
- Contract tests: `apps/api/tests/test_graph_ontology_confidence.py`
- Persistence fields: `apps/api/src/berrybrain_api/models.py`
- Retrieval consumption: `apps/api/src/berrybrain_api/cognitive_query.py`
- Experimental protocol: `docs/evaluation-methodology.md`
- Current limitations: `docs/limitations.md`
