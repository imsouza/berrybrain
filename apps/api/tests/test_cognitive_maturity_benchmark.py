import unittest

from benchmarks.cognitive_maturity_benchmark import run_benchmark


class CognitiveMaturityBenchmarkTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.metrics = run_benchmark()

    def test_concepts_and_connections_meet_expert_labeled_targets(self) -> None:
        self.assertGreaterEqual(self.metrics.concept_recall, 0.95)
        self.assertGreaterEqual(self.metrics.concept_precision, 0.95)
        self.assertGreaterEqual(self.metrics.connection_recall, 0.90)
        self.assertGreaterEqual(self.metrics.connection_precision, 0.85)

    def test_knowledge_is_grounded_and_traceable(self) -> None:
        self.assertEqual(self.metrics.insight_grounded_rate, 1.0)
        self.assertEqual(self.metrics.provenance_coverage, 1.0)
        self.assertLessEqual(self.metrics.unsupported_claim_rate, 0.02)
        self.assertEqual(self.metrics.diagnostic_leakage_rate, 0.0)

    def test_rebuild_is_safe_and_removes_stale_knowledge(self) -> None:
        self.assertTrue(self.metrics.idempotent_rebuild)
        self.assertTrue(self.metrics.stale_knowledge_removed)
        self.assertTrue(self.metrics.review_status_preserved)
        self.assertTrue(self.metrics.meets_targets)


if __name__ == "__main__":
    unittest.main()
