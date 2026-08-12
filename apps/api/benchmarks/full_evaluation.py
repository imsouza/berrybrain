from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from benchmarks.benchmark_profiles import SCALE_PROFILES, experiment_manifest
from benchmarks.evidence import create_manifest, write_evidence_bundle
from benchmarks.fault_injection_benchmark import run_fault_injection
from benchmarks.graph_performance_benchmark import write_report as write_graph_report
from benchmarks.http_load_benchmark import write_report as write_http_report
from benchmarks.maturity_release_gate import run_release_gate
from benchmarks.maturity_v3 import assess_maturity
from benchmarks.worker_queue_benchmark import write_report as write_worker_report


def build_maturity_evidence(
    artifact: str,
    *,
    include_http: bool,
    expires_at: datetime,
) -> list[dict[str, Any]]:
    capabilities = (
        "durable-semantic-memory",
        "retrieval-and-grounded-inference",
        "knowledge-graph-and-ontology",
        "insights-and-continuous-agents",
        "transparency-confidence-and-user-control",
        "performance-efficiency-and-scalability",
        "reliability-and-recoverability",
        "maintainability-architecture-and-governance",
    )
    if include_http:
        capabilities += ("interaction-quality-and-accessibility",)
    return [
        {
            "capability": capability,
            "level": 2,
            "classification": "ci-regression",
            "artifact": artifact,
            "expiresAt": expires_at.isoformat(),
        }
        for capability in capabilities
    ]


def run_full_evaluation(
    repository_root: Path,
    output_root: Path,
    *,
    profile_name: str = "S",
    base_url: str = "",
) -> dict[str, Any]:
    if profile_name not in SCALE_PROFILES:
        raise ValueError(f"unknown scale profile: {profile_name}")
    profile = SCALE_PROFILES[profile_name]
    output_root.mkdir(parents=True, exist_ok=True)
    evidence_root = output_root / "evidence"

    release_gate = run_release_gate()
    graph = write_graph_report(
        output_root / "graph-on-disk.json",
        node_count=profile.graph_nodes,
        edge_count=profile.graph_edges,
        sample_count=profile.query_repetitions,
        on_disk=True,
        evidence_root=evidence_root,
    )
    worker = write_worker_report(
        output_root / "worker-queue.json",
        jobs=profile.notes,
        evidence_root=evidence_root,
    )
    faults = run_fault_injection()
    http = None
    if base_url:
        http = write_http_report(
            output_root / "http-load.json",
            base_url=base_url,
            path="/health",
            requests=max(100, profile.notes),
            concurrency=min(50, max(1, profile.notes // 10)),
            timeout_seconds=10,
            evidence_root=evidence_root,
        )
    passed = bool(
        release_gate.passed
        and graph.meets_targets
        and worker.remaining_jobs == 0
        and worker.duplicate_claims == 0
        and faults.passed
        and (http is None or http.failures == 0)
    )
    summary: dict[str, Any] = {
        "schemaVersion": "berrybrain-evaluation.v1",
        "generatedAt": datetime.now(UTC).isoformat(),
        "classification": "exploratory",
        "profile": profile_name,
        "experiment": experiment_manifest(profile_name, ("A0", "A1", "A2", "A3")),
        "releaseGate": asdict(release_gate),
        "graphOnDisk": asdict(graph),
        "workerQueue": asdict(worker),
        "faultInjection": asdict(faults),
        "httpLoad": asdict(http) if http is not None else None,
        "passed": passed,
    }
    summary_path = output_root / "full-evaluation.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")

    manifest = create_manifest(
        "full-evaluation",
        dataset={"profile": asdict(profile)},
        configuration=summary["experiment"],
        classification="exploratory",
    )
    write_evidence_bundle(
        evidence_root,
        manifest,
        summary=summary,
        observations=[
            {"component": "release-gate", "passed": release_gate.passed},
            {"component": "graph-on-disk", "passed": graph.meets_targets},
            {
                "component": "worker-queue",
                "passed": worker.remaining_jobs == 0 and worker.duplicate_claims == 0,
            },
            {"component": "fault-injection", "passed": faults.passed},
            {"component": "http-load", "passed": http is None or http.failures == 0},
        ],
    )

    relative_artifact = str(summary_path.relative_to(repository_root))
    evidence = build_maturity_evidence(
        relative_artifact,
        include_http=http is not None,
        expires_at=datetime.now(UTC) + timedelta(days=90),
    )
    evidence_path = output_root / "maturity-evidence.json"
    evidence_path.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    maturity = assess_maturity(
        evidence,
        repository_root=repository_root,
        mandatory_gates_passed=passed,
    )
    (output_root / "maturity-v3.json").write_text(
        json.dumps(asdict(maturity), indent=2, sort_keys=True) + "\n"
    )
    summary["maturity"] = asdict(maturity)
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Execute the BerryBrain evaluation suite."
    )
    parser.add_argument("--repository-root", default=".")
    parser.add_argument("--output-root", default="reports/evaluation")
    parser.add_argument("--profile", choices=tuple(SCALE_PROFILES), default="S")
    parser.add_argument("--base-url", default="")
    args = parser.parse_args()
    summary = run_full_evaluation(
        Path(args.repository_root).resolve(),
        Path(args.output_root).resolve(),
        profile_name=args.profile,
        base_url=args.base_url,
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
