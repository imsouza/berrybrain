from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path


def expected_documentation_tokens(report: dict) -> tuple[str, ...]:
    generated = datetime.fromisoformat(
        str(report["generatedAt"]).replace("Z", "+00:00")
    )
    graph = report["graphOnDisk"]
    worker = report["workerQueue"]
    http = report.get("httpLoad") or {}
    maturity = report["maturity"]
    return (
        generated.strftime("%-d %B %Y"),
        str(report["profile"]),
        f"{int(graph['node_count']):,}",
        f"{int(graph['edge_count']):,}",
        f"{float(graph['latency_p95_ms']):.2f}",
        f"{float(worker['drain_rate_jobs_per_second']):.2f}",
        str(int(http.get("requests", 0))),
        f"{float(http.get('latency_p95_ms', 0)):.2f}",
        str(maturity["readiness"]),
        str(int(maturity["minimum_level"])),
        str(int(maturity["median_level"])),
    )


def check_documentation_consistency(
    report_path: Path,
    documents: tuple[Path, ...],
) -> list[str]:
    report = json.loads(report_path.read_text(encoding="utf-8"))
    tokens = expected_documentation_tokens(report)
    combined = "\n".join(path.read_text(encoding="utf-8") for path in documents)
    return [token for token in tokens if token not in combined]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check benchmark documentation freshness."
    )
    parser.add_argument("--report", default="reports/evaluation/full-evaluation.json")
    parser.add_argument("documents", nargs="+")
    args = parser.parse_args()
    missing = check_documentation_consistency(
        Path(args.report), tuple(Path(item) for item in args.documents)
    )
    print(json.dumps({"consistent": not missing, "missingTokens": missing}, indent=2))
    return 0 if not missing else 1


if __name__ == "__main__":
    raise SystemExit(main())
