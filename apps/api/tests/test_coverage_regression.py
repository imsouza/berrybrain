import unittest

from scripts.check_coverage_regression import regression_failures


def _report(*, covered_lines: int = 83, covered_branches: int = 68) -> dict:
    return {
        "files": {
            "src/berrybrain_api/example.py": {
                "summary": {
                    "num_statements": 100,
                    "covered_lines": covered_lines,
                    "num_branches": 100,
                    "covered_branches": covered_branches,
                }
            },
            "tests/test_example.py": {
                "summary": {
                    "num_statements": 1000,
                    "covered_lines": 1000,
                    "num_branches": 0,
                    "covered_branches": 0,
                }
            },
        }
    }


class CoverageRegressionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.baseline = {
            "scope": "src/berrybrain_api/",
            "allowedDropPercentagePoints": 0.1,
            "linePercent": 83.0,
            "branchPercent": 68.0,
            "combinedPercent": 75.5,
        }

    def test_ignores_test_files_and_accepts_the_measured_baseline(self) -> None:
        self.assertEqual(regression_failures(_report(), self.baseline), [])

    def test_rejects_a_branch_coverage_regression(self) -> None:
        failures = regression_failures(
            _report(covered_branches=67),
            self.baseline,
        )
        self.assertTrue(any("branchPercent" in failure for failure in failures))

    def test_rejects_a_missing_production_scope(self) -> None:
        with self.assertRaisesRegex(ValueError, "no files"):
            regression_failures({"files": {}}, self.baseline)


if __name__ == "__main__":
    unittest.main()
