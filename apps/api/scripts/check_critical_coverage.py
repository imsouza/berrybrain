from __future__ import annotations

import json
import sys
from pathlib import Path

CRITICAL_THRESHOLDS = {
    "src/berrybrain_api/jobs.py": 90.0,
    "src/berrybrain_api/graph_write_service.py": 80.0,
    "src/berrybrain_api/search.py": 90.0,
    "src/berrybrain_api/backup.py": 85.0,
    "src/berrybrain_api/review_service.py": 80.0,
    "src/berrybrain_api/attachment_processing.py": 70.0,
}


def coverage_failures(
    report: dict[str, object],
    thresholds: dict[str, float] | None = None,
) -> list[str]:
    configured = thresholds or CRITICAL_THRESHOLDS
    files = report.get("files")
    if not isinstance(files, dict):
        return ["Coverage report does not contain a files map."]

    failures: list[str] = []
    for path, minimum in configured.items():
        file_report = files.get(path)
        if not isinstance(file_report, dict):
            failures.append(f"{path}: missing from coverage report")
            continue
        summary = file_report.get("summary")
        percent = summary.get("percent_covered") if isinstance(summary, dict) else None
        if not isinstance(percent, (int, float)):
            failures.append(f"{path}: invalid coverage summary")
            continue
        if float(percent) < minimum:
            failures.append(f"{path}: {float(percent):.2f}% < {minimum:.2f}%")
    return failures


def main(argv: list[str] | None = None) -> int:
    args = argv or sys.argv[1:]
    report_path = Path(args[0] if args else "coverage.json")
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Critical coverage gate could not read {report_path}: {exc}")
        return 2

    failures = coverage_failures(report)
    if failures:
        print("Critical coverage gate failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Critical coverage gate passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
