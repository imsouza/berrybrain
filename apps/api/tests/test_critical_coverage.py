import unittest

from scripts.check_critical_coverage import coverage_failures


class CriticalCoverageGateTest(unittest.TestCase):
    def test_reports_missing_and_regressed_modules(self) -> None:
        report = {
            "files": {
                "src/covered.py": {"summary": {"percent_covered": 79.99}},
            }
        }

        failures = coverage_failures(
            report,
            {
                "src/covered.py": 80.0,
                "src/missing.py": 70.0,
            },
        )

        self.assertEqual(
            failures,
            [
                "src/covered.py: 79.99% < 80.00%",
                "src/missing.py: missing from coverage report",
            ],
        )

    def test_accepts_modules_at_their_threshold(self) -> None:
        report = {
            "files": {
                "src/covered.py": {"summary": {"percent_covered": 80.0}},
            }
        }

        self.assertEqual(
            coverage_failures(report, {"src/covered.py": 80.0}),
            [],
        )


if __name__ == "__main__":
    unittest.main()
