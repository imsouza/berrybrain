from __future__ import annotations

import hashlib
import json
import math
import os
import platform
import random
import subprocess
import sys
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "berrybrain-benchmark.v1"


@dataclass(frozen=True)
class ConfidenceInterval:
    confidence: float
    lower: float
    upper: float
    method: str
    samples: int


@dataclass(frozen=True)
class RunManifest:
    schema_version: str
    run_id: str
    benchmark: str
    classification: str
    started_at: str
    git_commit: str
    git_dirty: bool
    python_version: str
    platform: str
    machine: str
    processor: str
    cpu_count: int
    random_seed: int
    dataset_checksum: str
    configuration: dict[str, Any]


def percentile(values: Sequence[float], quantile: float) -> float:
    if not values:
        return 0.0
    if not 0 <= quantile <= 1:
        raise ValueError("quantile must be between zero and one")
    ordered = sorted(float(value) for value in values)
    position = (len(ordered) - 1) * quantile
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def bootstrap_interval(
    values: Sequence[float],
    *,
    statistic: Callable[[Sequence[float]], float] | None = None,
    confidence: float = 0.95,
    resamples: int = 2_000,
    seed: int = 20260812,
) -> ConfidenceInterval:
    if not values:
        return ConfidenceInterval(confidence, 0.0, 0.0, "bootstrap-percentile", 0)
    if not 0 < confidence < 1 or resamples < 100:
        raise ValueError("bootstrap confidence and resamples are invalid")
    sample = [float(value) for value in values]
    measure = statistic or (lambda rows: sum(rows) / len(rows))
    rng = random.Random(seed)
    estimates = [
        measure([sample[rng.randrange(len(sample))] for _ in sample])
        for _ in range(resamples)
    ]
    alpha = (1 - confidence) / 2
    return ConfidenceInterval(
        confidence=confidence,
        lower=round(percentile(estimates, alpha), 6),
        upper=round(percentile(estimates, 1 - alpha), 6),
        method="bootstrap-percentile",
        samples=len(sample),
    )


def paired_bootstrap_difference(
    candidate: Sequence[float],
    baseline: Sequence[float],
    *,
    confidence: float = 0.95,
    resamples: int = 2_000,
    seed: int = 20260812,
) -> ConfidenceInterval:
    if len(candidate) != len(baseline) or not candidate:
        raise ValueError("paired samples must have the same non-zero length")
    differences = [
        float(left) - float(right) for left, right in zip(candidate, baseline)
    ]
    return bootstrap_interval(
        differences,
        confidence=confidence,
        resamples=resamples,
        seed=seed,
    )


def checksum_json(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _git_value(*args: str, default: str = "unknown") -> str:
    try:
        return (
            subprocess.run(
                ["git", *args],
                check=True,
                capture_output=True,
                text=True,
                timeout=5,
            ).stdout.strip()
            or default
        )
    except (OSError, subprocess.SubprocessError):
        return default


def create_manifest(
    benchmark: str,
    *,
    dataset: Any,
    configuration: dict[str, Any],
    classification: str = "exploratory",
    seed: int = 20260812,
) -> RunManifest:
    if classification not in {"exploratory", "confirmatory", "ci-regression"}:
        raise ValueError("unsupported benchmark classification")
    started_at = datetime.now(UTC)
    dataset_checksum = checksum_json(dataset)
    commit = _git_value("rev-parse", "HEAD")
    dirty = bool(_git_value("status", "--porcelain", default=""))
    identity = checksum_json(
        {
            "benchmark": benchmark,
            "startedAt": started_at.isoformat(),
            "commit": commit,
            "dataset": dataset_checksum,
            "seed": seed,
        }
    )[:16]
    return RunManifest(
        schema_version=SCHEMA_VERSION,
        run_id=f"{started_at.strftime('%Y%m%dT%H%M%SZ')}-{identity}",
        benchmark=benchmark,
        classification=classification,
        started_at=started_at.isoformat(),
        git_commit=commit,
        git_dirty=dirty,
        python_version=sys.version.split()[0],
        platform=platform.platform(),
        machine=platform.machine(),
        processor=platform.processor() or "unknown",
        cpu_count=os.cpu_count() or 1,
        random_seed=seed,
        dataset_checksum=dataset_checksum,
        configuration=configuration,
    )


def write_evidence_bundle(
    output_root: Path,
    manifest: RunManifest,
    *,
    summary: dict[str, Any],
    observations: Sequence[dict[str, Any]],
) -> Path:
    run_dir = output_root / manifest.run_id
    raw_dir = run_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=False)
    files = {
        run_dir / "manifest.json": asdict(manifest),
        run_dir / "summary.json": summary,
    }
    for path, value in files.items():
        path.write_text(
            json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    observations_path = raw_dir / "observations.jsonl"
    observations_path.write_text(
        "".join(
            json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n"
            for row in observations
        ),
        encoding="utf-8",
    )
    checksums = []
    for path in [*files, observations_path]:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        checksums.append(f"{digest}  {path.relative_to(run_dir)}")
    (run_dir / "checksums.txt").write_text(
        "\n".join(checksums) + "\n", encoding="utf-8"
    )
    return run_dir
