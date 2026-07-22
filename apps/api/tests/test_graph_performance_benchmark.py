import unittest

from benchmarks.graph_performance_benchmark import run_benchmark


class GraphPerformanceBenchmarkTest(unittest.TestCase):
    def test_projection_is_complete_and_measured(self) -> None:
        result = run_benchmark(
            node_count=200,
            edge_count=600,
            sample_count=3,
            p95_budget_ms=2_000,
            payload_budget_bytes=2 * 1024 * 1024,
        )

        self.assertEqual(result.node_count, 200)
        self.assertEqual(result.edge_count, 600)
        self.assertGreater(result.payload_bytes, 0)
        self.assertGreaterEqual(result.latency_p95_ms, result.latency_p50_ms)
        self.assertTrue(result.meets_targets)

    def test_invalid_fixture_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            run_benchmark(node_count=1, edge_count=0, sample_count=1)


if __name__ == "__main__":
    unittest.main()
