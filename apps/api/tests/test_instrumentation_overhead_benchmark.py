import unittest

from benchmarks.instrumentation_overhead_benchmark import run_instrumentation_overhead


class InstrumentationOverheadBenchmarkTest(unittest.TestCase):
    def test_executes_paired_enabled_disabled_samples(self) -> None:
        metrics = run_instrumentation_overhead(iterations=100, samples=3)
        self.assertEqual(metrics.iterations, 100)
        self.assertEqual(metrics.samples, 3)
        self.assertGreater(metrics.disabled_mean_ms, 0)
        self.assertGreater(metrics.enabled_mean_ms, 0)
        self.assertEqual(metrics.overhead_ci95["method"], "bootstrap-percentile")


if __name__ == "__main__":
    unittest.main()
