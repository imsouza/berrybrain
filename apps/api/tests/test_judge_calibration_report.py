import unittest
from pathlib import Path

from benchmarks.judge_calibration_report import build_report, load_fixture


class JudgeCalibrationReportTest(unittest.TestCase):
    def test_synthetic_fixture_meets_regression_gate_without_human_claim(self) -> None:
        fixture_path = (
            Path(__file__).resolve().parents[3]
            / "tests"
            / "fixtures"
            / "judge_calibration_fixture.json"
        )
        report = build_report(load_fixture(fixture_path))

        self.assertEqual(report["total_evaluations"], 100)
        self.assertEqual(report["total_reference_reviews"], 30)
        self.assertEqual(report["total_human_reviews"], 0)
        self.assertGreaterEqual(report["weighted_kappa"], 0.70)
        self.assertLessEqual(report["false_acceptance_rate"], 0.05)
        self.assertLessEqual(report["false_rejection_rate"], 0.10)
        self.assertTrue(report["regression_gate_passed"])
        self.assertFalse(report["calibrated"])
        self.assertEqual(report["status"], "regression_only")


if __name__ == "__main__":
    unittest.main()
