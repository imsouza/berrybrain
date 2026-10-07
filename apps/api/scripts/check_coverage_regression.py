from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


def _coverage_scope(
    report: dict[str, Any],
    *,
    prefix: str,
) -> dict[str, float]:
    files = report.get("files")
    if not isinstance(files, dict):
        raise ValueError("Coverage report does not contain a files map")
    statements = covered_lines = branches = covered_branches = 0
    normalized_prefix = prefix.replace("\\", "/").lstrip("/")
    for path, file_report in files.items():
        normalized_path = str(path).replace("\\", "/").lstrip("/")
        if not normalized_path.startswith(normalized_prefix):
            continue
        summary = file_report.get("summary") if isinstance(file_report, dict) else None
        if not isinstance(summary, dict):
            continue
        statements += int(summary.get("num_statements") or 0)
        covered_lines += int(summary.get("covered_lines") or 0)
        branches += int(summary.get("num_branches") or 0)
        covered_branches += int(summary.get("covered_branches") or 0)
    if statements == 0:
        raise ValueError(f"Coverage report has no files under {prefix}")
    measured = statements + branches
    return {
        "linePercent": covered_lines / statements * 100,
        "branchPercent": covered_branches / branches * 100 if branches else 100.0,
        "combinedPercent": (covered_lines + covered_branches) / measured * 100,
    }


def regression_failures(
    report: dict[str, Any],
    baseline: dict[str, Any],
) -> list[str]:
    scope = str(baseline.get("scope") or "src/berrybrain_api/")
    measured = _coverage_scope(report, prefix=scope)
    allowed_drop = float(baseline.get("allowedDropPercentagePoints") or 0.0)
    comparisons = (
        ("linePercent", "linePercent"),
        ("branchPercent", "branchPercent"),
        ("combinedPercent", "combinedPercent"),
    )
    failures: list[str] = []
    for measured_key, baseline_key in comparisons:
        expected = baseline.get(baseline_key)
        if not isinstance(expected, int | float):
            failures.append(f"Baseline field {baseline_key} is missing or invalid.")
            continue
        actual = float(measured[measured_key])
        floor = float(expected) - allowed_drop
        if actual < floor:
            failures.append(
                f"{measured_key}: {actual:.4f}% < {floor:.4f}% regression floor"
            )
    return failures


def main(argv: list[str] | None = None) -> int:
    args = argv or sys.argv[1:]
    report_path = Path(args[0] if args else "coverage.json")
    baseline_path = Path(args[1] if len(args) > 1 else "scripts/coverage-baseline.json")
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
        baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
        failures = regression_failures(report, baseline)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Coverage regression gate could not validate evidence: {exc}")
        return 2

    if failures:
        print("Coverage regression gate failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Coverage regression gate passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
