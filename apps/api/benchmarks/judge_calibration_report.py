from __future__ import annotations

import argparse
import json
from pathlib import Path

from berrybrain_api.routers.judge import _scorecard_agreement

DEFAULT_FIXTURE = (
    Path(__file__).resolve().parents[3]
    / "tests"
    / "fixtures"
    / "judge_calibration_fixture.json"
)


def load_fixture(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def build_report(fixture: dict) -> dict:
    reviews = fixture.get("reviews", [])
    classification = str(fixture.get("classification") or "unverified")
    annotation_source = str(fixture.get("annotation_source") or "unverified")
    human_labeled = classification == "human-labeled"
    agreement = _scorecard_agreement(
        [(row.get("judge_verdict", ""), row.get("verdict", "")) for row in reviews]
    )
    total_evaluations = int(fixture.get("total_evaluations", 0))
    total_reference_reviews = len(reviews)
    total_human_reviews = total_reference_reviews if human_labeled else 0
    gates = {
        "min_evals": 100,
        "min_reviews": 30,
        "weighted_kappa_min": 0.70,
        "fa_max": 0.05,
        "fr_max": 0.10,
    }
    regression_gate_passed = (
        total_evaluations >= gates["min_evals"]
        and total_reference_reviews >= gates["min_reviews"]
        and agreement["weighted_kappa"] >= gates["weighted_kappa_min"]
        and agreement["false_acceptance_rate"] <= gates["fa_max"]
        and agreement["false_rejection_rate"] <= gates["fr_max"]
    )
    calibrated = human_labeled and regression_gate_passed
    return {
        "classification": classification,
        "annotation_source": annotation_source,
        "total_evaluations": total_evaluations,
        "total_reference_reviews": total_reference_reviews,
        "total_human_reviews": total_human_reviews,
        **agreement,
        "gates": gates,
        "regression_gate_passed": regression_gate_passed,
        "calibrated": calibrated,
        "status": (
            "calibrated"
            if calibrated
            else "regression_only"
            if regression_gate_passed
            else "NOT_CALIBRATED"
        ),
        "limitation": (
            "Reference labels are synthetic regression fixtures and do not count as "
            "independent human calibration."
            if not human_labeled
            else ""
        ),
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
    parser.add_argument("--fixture", default=str(DEFAULT_FIXTURE))
    parser.add_argument("--output", default="reports/judge-calibration-report.json")
    args = parser.parse_args()
    report = write_report(Path(args.fixture), Path(args.output))
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["regression_gate_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
