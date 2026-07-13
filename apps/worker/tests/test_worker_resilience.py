import unittest

import berrybrain_worker.main as worker_main


class WorkerResilienceTest(unittest.TestCase):
    def setUp(self) -> None:
        worker_main._provider_circuit.clear()

    def tearDown(self) -> None:
        worker_main._provider_circuit.clear()

    def test_provider_circuit_opens_after_repeated_failures(self) -> None:
        provider = "cloud:test"

        worker_main.record_provider_failure(provider)
        worker_main.record_provider_failure(provider)
        worker_main.assert_provider_available(provider)

        worker_main.record_provider_failure(provider)

        with self.assertRaises(RuntimeError):
            worker_main.assert_provider_available(provider)

    def test_provider_success_resets_circuit(self) -> None:
        provider = "ollama:test"
        for _ in range(worker_main.CIRCUIT_FAILURE_THRESHOLD):
            worker_main.record_provider_failure(provider)

        worker_main.record_provider_success(provider)
        worker_main.assert_provider_available(provider)
        self.assertEqual(worker_main.circuit_state(provider)["failures"], 0.0)


if __name__ == "__main__":
    unittest.main()
