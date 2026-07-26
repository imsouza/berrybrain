import unittest

from benchmarks.retrieval_quality_benchmark import run_benchmark


class RetrievalQualityBenchmarkTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.metrics = run_benchmark()

    def test_hipporag_multi_hop_gate(self) -> None:
        self.assertGreaterEqual(self.metrics.multi_hop_recall_gain, 0.10)
        self.assertLessEqual(self.metrics.factual_recall_regression, 0.02)
        self.assertGreaterEqual(self.metrics.citation_precision, 0.95)
        self.assertGreaterEqual(self.metrics.faithfulness, 0.90)

    def test_negative_retrieval_cases(self) -> None:
        self.assertEqual(self.metrics.negative_rejection_rate, 1.0)
        self.assertTrue(self.metrics.no_evidence_rejected)
        self.assertTrue(self.metrics.contradictory_rejected)
        self.assertTrue(self.metrics.stale_deleted_rejected)
        self.assertTrue(self.metrics.secret_note_rejected)

    def test_fact_promotion_stays_disabled(self) -> None:
        self.assertFalse(self.metrics.fact_promotion_allowed)
        self.assertTrue(self.metrics.gates_passed)


if __name__ == "__main__":
    unittest.main()
