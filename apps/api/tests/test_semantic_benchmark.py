import unittest

from benchmarks.semantic_search_benchmark import (
    NEGATIVE_QUERIES,
    TOPICS,
    run_benchmark,
)


class SemanticBenchmarkTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.metrics = run_benchmark()

    def test_dataset_has_planned_scale_and_negative_cases(self) -> None:
        self.assertEqual(self.metrics.note_count, 100)
        self.assertEqual(self.metrics.query_count, 45)
        self.assertEqual(self.metrics.positive_query_count, len(TOPICS) * 4)
        self.assertEqual(self.metrics.negative_query_count, len(NEGATIVE_QUERIES))

    def test_quality_targets(self) -> None:
        self.assertGreaterEqual(self.metrics.recall_at_10, 0.85)
        self.assertGreaterEqual(self.metrics.mean_reciprocal_rank, 0.70)
        self.assertGreaterEqual(self.metrics.ndcg_at_10, 0.85)
        self.assertEqual(self.metrics.unexpected_zero_result_rate, 0.0)
        self.assertEqual(self.metrics.negative_rejection_rate, 1.0)
        self.assertEqual(self.metrics.relationship_recall_at_10, 1.0)

    def test_operational_targets(self) -> None:
        self.assertLessEqual(self.metrics.latency_p95_ms, 500)
        self.assertGreaterEqual(self.metrics.indexing_coverage, 0.995)
        self.assertEqual(self.metrics.stale_evidence_count, 0)
        self.assertTrue(self.metrics.meets_initial_targets)


if __name__ == "__main__":
    unittest.main()
