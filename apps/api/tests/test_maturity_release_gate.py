import sys
import unittest

from benchmarks.maturity_release_gate import run_release_gate


class MaturityReleaseGateTest(unittest.TestCase):
    def test_all_cognitive_release_gates_pass(self) -> None:
        if sys.gettrace() is not None:
            self.skipTest("timing budgets require an uninstrumented process")
        result = run_release_gate()

        self.assertTrue(result.passed, result.failed_gates)
        self.assertEqual(result.failed_gates, ())


if __name__ == "__main__":
    unittest.main()
