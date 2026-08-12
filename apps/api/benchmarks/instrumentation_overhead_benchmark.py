from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import time
from dataclasses import asdict, dataclass
from pathlib import Path

from benchmarks.evidence import (
    create_manifest,
    paired_bootstrap_difference,
    write_evidence_bundle,
)
from berrybrain_api.performance_metrics import record_request, reset_performance_metrics


@dataclass(frozen=True)
class InstrumentationOverheadMetrics:
    iterations: int
    samples: int
    disabled_mean_ms: float
    enabled_mean_ms: float
    absolute_overhead_ms: float
    relative_overhead: float
    overhead_ci95: dict


def _sample(iterations: int, *, enabled: bool) -> float:
    payload = b"berrybrain-instrumentation-overhead"
    started = time.perf_counter()
    for index in range(iterations):
        hashlib.sha256(payload + str(index).encode()).digest()
        record_request("GET", "/benchmark", 200, 1.0, enabled=enabled)
    return (time.perf_counter() - started) * 1000 / iterations


def run_instrumentation_overhead(
    *, iterations: int = 5_000, samples: int = 15
) -> InstrumentationOverheadMetrics:
    if iterations < 100 or samples < 3:
        raise ValueError(
            "instrumentation benchmark requires 100 iterations and 3 samples"
        )
    reset_performance_metrics()
    disabled: list[float] = []
    enabled: list[float] = []
    for index in range(samples):
        if index % 2:
            enabled.append(_sample(iterations, enabled=True))
            disabled.append(_sample(iterations, enabled=False))
        else:
            disabled.append(_sample(iterations, enabled=False))
            enabled.append(_sample(iterations, enabled=True))
    disabled_mean = statistics.fmean(disabled)
    enabled_mean = statistics.fmean(enabled)
    difference = enabled_mean - disabled_mean
    return InstrumentationOverheadMetrics(
        iterations=iterations,
        samples=samples,
        disabled_mean_ms=disabled_mean,
        enabled_mean_ms=enabled_mean,
        absolute_overhead_ms=difference,
        relative_overhead=difference / disabled_mean if disabled_mean else 0.0,
        overhead_ci95=asdict(paired_bootstrap_difference(enabled, disabled)),
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Measure API metric recorder overhead."
    )
    parser.add_argument("--iterations", type=int, default=5_000)
    parser.add_argument("--samples", type=int, default=15)
    parser.add_argument("--output", default="reports/instrumentation-overhead.json")
    parser.add_argument("--evidence-root", default="")
    args = parser.parse_args()
    metrics = run_instrumentation_overhead(
        iterations=args.iterations, samples=args.samples
    )
    summary = asdict(metrics)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    if args.evidence_root:
        manifest = create_manifest(
            "instrumentation-overhead",
            dataset={"containsUserContent": False},
            configuration={"iterations": args.iterations, "samples": args.samples},
            classification="exploratory",
        )
        write_evidence_bundle(
            Path(args.evidence_root),
            manifest,
            summary=summary,
            observations=[],
        )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
