from __future__ import annotations

import argparse
import json
from pathlib import Path

from berrybrain_api.routers.judge import _scorecard_agreement


def load_fixture(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def build_report(fixture: dict) -> dict:
    reviews = fixture.get("reviews", [])
    agreement = _scorecard_agreement(
        [(row.get("judge_verdict", ""), row.get("verdict", "")) for row in reviews]
    )
    total_evaluations = int(fixture.get("total_evaluations", 0))
    total_reviews = len(reviews)
    gates = {
        "min_evals": 100,
        "min_reviews": 30,
        "weighted_kappa_min": 0.70,
        "fa_max": 0.05,
        "fr_max": 0.10,
    }
    calibrated = (
        total_evaluations >= gates["min_evals"]
        and total_reviews >= gates["min_reviews"]
        and agreement["weighted_kappa"] >= gates["weighted_kappa_min"]
        and agreement["false_acceptance_rate"] <= gates["fa_max"]
        and agreement["false_rejection_rate"] <= gates["fr_max"]
    )
    return {
        "total_evaluations": total_evaluations,
        "total_human_reviews": total_reviews,
        **agreement,
        "gates": gates,
        "calibrated": calibrated,
        "status": "calibrated" if calibrated else "NOT_CALIBRATED",
        "human_review_jsonl_fields": [
            "committee_id",
            "artifact_type",
            "artifact_id",
            "reviewer",
            "verdict",
            "score",
            "notes",
        ],
    }


def write_report(fixture_path: Path, output_path: Path) -> dict:
    report = build_report(load_fixture(fixture_path))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="BerryBrain judge calibration report")
    parser.add_argument(
        "--fixture", default="tests/fixtures/judge_calibration_fixture.json"
    )
    parser.add_argument("--output", default="reports/judge-calibration-report.json")
    args = parser.parse_args()
    report = write_report(Path(args.fixture), Path(args.output))
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["calibrated"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
