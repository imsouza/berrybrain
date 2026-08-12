import unittest

from benchmarks.fault_injection_benchmark import run_fault_injection


class FaultInjectionBenchmarkTest(unittest.TestCase):
    def test_contains_isolated_faults_without_state_corruption(self) -> None:
        metrics = run_fault_injection()

        self.assertTrue(metrics.passed)
        self.assertEqual(metrics.fault_count, 3)
        self.assertEqual(metrics.contained_count, 3)
        self.assertEqual(metrics.integrity_preserved_count, 3)
        self.assertEqual(
            {item.fault for item in metrics.observations},
            {
                "provider-or-sidecar-unavailable",
                "malformed-model-output",
                "disk-write-unavailable",
            },
        )


if __name__ == "__main__":
    unittest.main()
