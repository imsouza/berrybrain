import unittest

from benchmarks.retrieval_quality_benchmark import run_benchmark


class RetrievalQualityBenchmarkTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.metrics = run_benchmark()

    def test_executed_graph_ablation_improves_multi_hop_retrieval(self) -> None:
        self.assertGreaterEqual(self.metrics.multi_hop_recall_gain, 0.10)
        self.assertGreater(self.metrics.multi_hop_gain_ci95["lower"], 0)
        self.assertLessEqual(self.metrics.factual_recall_regression, 0.02)
        self.assertGreaterEqual(self.metrics.citation_precision, 0.95)
        self.assertGreaterEqual(self.metrics.evidence_faithfulness, 0.90)
        self.assertEqual(
            {item.configuration for item in self.metrics.ablations},
            {
                "lexical_only",
                "dense_only",
                "standard_hybrid",
                "graph_lexical",
                "graph_hybrid",
            },
        )

    def test_negative_retrieval_cases(self) -> None:
        self.assertEqual(self.metrics.negative_rejection_rate, 1.0)
        self.assertTrue(self.metrics.ignored_edge_rejected)
        self.assertTrue(self.metrics.stale_deleted_rejected)

    def test_every_metric_has_query_level_observations(self) -> None:
        self.assertEqual(len(self.metrics.observations), self.metrics.query_count * 5)
        self.assertTrue(all(row["success"] for row in self.metrics.observations))
        self.assertTrue(self.metrics.gates_passed)


if __name__ == "__main__":
    unittest.main()
