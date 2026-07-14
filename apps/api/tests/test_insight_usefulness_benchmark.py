import unittest

from benchmarks.insight_usefulness_benchmark import run_benchmark


class InsightUsefulnessBenchmarkTest(unittest.TestCase):
    def test_expert_labeled_dataset_meets_publication_target(self) -> None:
        metrics = run_benchmark()
        self.assertGreaterEqual(metrics.fixture_count, 12)
        self.assertGreaterEqual(metrics.accuracy, 0.8)
        self.assertGreaterEqual(metrics.precision, 0.8)
        self.assertGreaterEqual(metrics.recall, 0.8)
        self.assertGreaterEqual(metrics.accepted_usefulness_rate, 0.8)
        self.assertTrue(metrics.meets_target)


if __name__ == "__main__":
    unittest.main()
