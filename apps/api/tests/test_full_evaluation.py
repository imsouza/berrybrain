import unittest
from datetime import UTC, datetime

from benchmarks.full_evaluation import build_maturity_evidence


class FullEvaluationTest(unittest.TestCase):
    def test_evidence_mapping_does_not_claim_unmeasured_capabilities(self) -> None:
        evidence = build_maturity_evidence(
            "reports/evaluation/full-evaluation.json",
            include_http=False,
            expires_at=datetime(2026, 12, 1, tzinfo=UTC),
        )
        capabilities = {item["capability"] for item in evidence}
        self.assertNotIn("capture-and-extraction", capabilities)
        self.assertNotIn("security-privacy-and-safety", capabilities)
        self.assertNotIn("interaction-quality-and-accessibility", capabilities)
        self.assertEqual({item["level"] for item in evidence}, {2})


if __name__ == "__main__":
    unittest.main()
