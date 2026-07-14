import unittest
import asyncio

from berrybrain_worker.cloud_gateway import CloudError
from berrybrain_worker import resilience


class WorkerResilienceTest(unittest.TestCase):
    def setUp(self) -> None:
        resilience._provider_circuit.clear()

    def tearDown(self) -> None:
        resilience._provider_circuit.clear()

    def test_provider_circuit_opens_after_repeated_failures(self) -> None:
        provider = "cloud:test"

        resilience.record_provider_failure(provider)
        resilience.record_provider_failure(provider)
        resilience.assert_provider_available(provider)

        resilience.record_provider_failure(provider)

        with self.assertRaises(CloudError):
            resilience.assert_provider_available(provider)

    def test_provider_success_resets_circuit(self) -> None:
        provider = "ollama:test"
        for _ in range(resilience.CIRCUIT_FAILURE_THRESHOLD):
            resilience.record_provider_failure(provider)

        resilience.record_provider_success(provider)
        resilience.assert_provider_available(provider)
        self.assertEqual(resilience.circuit_state(provider)["failures"], 0.0)

    def test_format_job_failure_humanizes_timeout(self) -> None:
        message = resilience.format_job_failure(
            "GENERATE_GRAPH_INSIGHTS", asyncio.TimeoutError()
        )

        self.assertIn("timed out", message)
        self.assertIn("retry", message.lower())
        self.assertNotIn("Traceback", message)

    def test_provider_timeout_is_transient(self) -> None:
        self.assertFalse(resilience.is_permanent_job_error(asyncio.TimeoutError()))

    def test_format_job_failure_humanizes_invalid_ai_json(self) -> None:
        message = resilience.format_job_failure(
            "GENERATE_GRAPH_INSIGHTS",
            CloudError('Cloud returned invalid JSON (len=100): {"broken":'),
        )

        self.assertIn("invalid AI response", message)
        self.assertIn("provider/model", message)
        self.assertNotIn('{"broken"', message)

    def test_format_job_failure_humanizes_provider_circuit(self) -> None:
        message = resilience.format_job_failure(
            "GENERATE_EMBEDDING",
            RuntimeError("Provider circuit open for cloud:test; retry in 120s"),
        )

        self.assertIn("provider failed repeatedly", message)
        self.assertIn("Settings", message)


if __name__ == "__main__":
    unittest.main()
