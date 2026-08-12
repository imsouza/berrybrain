import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

from benchmarks.maturity_v3 import CAPABILITIES, assess_maturity


class MaturityV3Test(unittest.TestCase):
    def test_awards_only_current_verifiable_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "evidence.json").write_text("{}", encoding="utf-8")
            evidence = [
                {
                    "capability": capability,
                    "level": 2,
                    "classification": "ci-regression",
                    "artifact": "evidence.json",
                    "expiresAt": "2027-01-01T00:00:00Z",
                }
                for capability in CAPABILITIES
            ]
            assessment = assess_maturity(
                evidence,
                repository_root=root,
                mandatory_gates_passed=True,
                now=datetime(2026, 8, 12, tzinfo=UTC),
            )
            self.assertEqual(assessment.minimum_level, 2)
            self.assertEqual(assessment.readiness, "engineering-evidence")
            self.assertFalse(assessment.rejected_evidence)

    def test_rejects_missing_stale_and_overclaimed_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "evidence.json").write_text("{}", encoding="utf-8")
            evidence = [
                {
                    "capability": CAPABILITIES[0],
                    "level": 4,
                    "classification": "ci-regression",
                    "artifact": "evidence.json",
                },
                {
                    "capability": CAPABILITIES[1],
                    "level": 2,
                    "classification": "ci-regression",
                    "artifact": "missing.json",
                },
                {
                    "capability": CAPABILITIES[2],
                    "level": 2,
                    "classification": "ci-regression",
                    "artifact": "evidence.json",
                    "expiresAt": "2025-01-01T00:00:00Z",
                },
            ]
            assessment = assess_maturity(
                evidence,
                repository_root=root,
                mandatory_gates_passed=False,
                now=datetime(2026, 8, 12, tzinfo=UTC),
            )
            self.assertEqual(assessment.readiness, "blocked")
            self.assertEqual(len(assessment.rejected_evidence), 3)
            self.assertEqual(assessment.minimum_level, 0)


if __name__ == "__main__":
    unittest.main()
