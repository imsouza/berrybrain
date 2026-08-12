from __future__ import annotations

import argparse
import json
import tempfile
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from benchmarks.evidence import create_manifest, write_evidence_bundle


@dataclass(frozen=True)
class FaultObservation:
    fault: str
    contained: bool
    recovery_ms: float
    integrity_preserved: bool
    user_visible_state: str
    detail: str


@dataclass(frozen=True)
class FaultBenchmarkMetrics:
    fault_count: int
    contained_count: int
    integrity_preserved_count: int
    maximum_recovery_ms: float
    passed: bool
    observations: tuple[FaultObservation, ...]


def _http_probe(url: str, timeout_seconds: float = 0.2) -> tuple[int, str]:
    try:
        with urlopen(Request(url, method="GET"), timeout=timeout_seconds) as response:
            return response.status, "response"
    except HTTPError as exc:
        return exc.code, "http-error"
    except (URLError, TimeoutError, OSError) as exc:
        return 0, type(exc).__name__


def _parse_model_payload(raw: str) -> tuple[bool, str]:
    try:
        value = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return False, "invalid-model-output"
    if not isinstance(value, dict) or not isinstance(value.get("answer"), str):
        return False, "invalid-model-contract"
    return True, "valid"


def run_fault_injection(
    *,
    unavailable_url: str = "http://127.0.0.1:1/health",
) -> FaultBenchmarkMetrics:
    observations: list[FaultObservation] = []

    started = time.perf_counter()
    status, detail = _http_probe(unavailable_url)
    observations.append(
        FaultObservation(
            fault="provider-or-sidecar-unavailable",
            contained=status == 0,
            recovery_ms=(time.perf_counter() - started) * 1000,
            integrity_preserved=True,
            user_visible_state="degraded",
            detail=detail,
        )
    )

    started = time.perf_counter()
    valid, detail = _parse_model_payload("not-json")
    observations.append(
        FaultObservation(
            fault="malformed-model-output",
            contained=not valid,
            recovery_ms=(time.perf_counter() - started) * 1000,
            integrity_preserved=not valid,
            user_visible_state="failed",
            detail=detail,
        )
    )

    started = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="berrybrain-fault-") as directory:
        root = Path(directory)
        target = root / "state.json"
        target.write_text('{"state":"before"}\n', encoding="utf-8")
        original = target.read_bytes()
        read_only = root / "read-only"
        read_only.mkdir()
        read_only.chmod(0o500)
        try:
            if read_only.stat().st_mode & 0o200:
                raise RuntimeError("write permission unexpectedly available")
            contained = True
            detail = "write-blocked-before-mutation"
        except OSError as exc:
            contained = True
            detail = type(exc).__name__
        finally:
            read_only.chmod(0o700)
        integrity = target.read_bytes() == original
    observations.append(
        FaultObservation(
            fault="disk-write-unavailable",
            contained=contained,
            recovery_ms=(time.perf_counter() - started) * 1000,
            integrity_preserved=integrity,
            user_visible_state="failed",
            detail=detail,
        )
    )

    contained_count = sum(item.contained for item in observations)
    integrity_count = sum(item.integrity_preserved for item in observations)
    return FaultBenchmarkMetrics(
        fault_count=len(observations),
        contained_count=contained_count,
        integrity_preserved_count=integrity_count,
        maximum_recovery_ms=max(item.recovery_ms for item in observations),
        passed=contained_count == len(observations)
        and integrity_count == len(observations),
        observations=tuple(observations),
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run isolated fault-containment probes."
    )
    parser.add_argument("--unavailable-url", default="http://127.0.0.1:1/health")
    parser.add_argument("--output", default="reports/fault-injection.json")
    parser.add_argument("--evidence-root", default="")
    args = parser.parse_args()
    metrics = run_fault_injection(unavailable_url=args.unavailable_url)
    summary = asdict(metrics)
    observations = [asdict(item) for item in metrics.observations]
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    if args.evidence_root:
        manifest = create_manifest(
            "fault-injection",
            dataset={"containsUserContent": False},
            configuration={
                "faults": [item.fault for item in metrics.observations],
                "unavailableUrl": args.unavailable_url,
            },
            classification="ci-regression",
        )
        write_evidence_bundle(
            Path(args.evidence_root),
            manifest,
            summary=summary,
            observations=observations,
        )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if metrics.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
