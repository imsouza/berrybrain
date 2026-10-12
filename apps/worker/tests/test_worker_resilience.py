import unittest

import httpx

from berrybrain_worker import resilience
from berrybrain_worker.cloud_gateway import CloudError
from berrybrain_worker.config import WorkerSettings


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
            "GENERATE_GRAPH_INSIGHTS", TimeoutError()
        )

        self.assertIn("timed out", message)
        self.assertIn("retry", message.lower())
        self.assertNotIn("Traceback", message)

    def test_provider_timeout_is_transient(self) -> None:
        self.assertFalse(resilience.is_permanent_job_error(TimeoutError()))

    def test_local_graph_timeout_does_not_blame_ai_provider(self) -> None:
        message = resilience.format_job_failure("UPDATE_GRAPH_STATS", TimeoutError())
        self.assertIn("API/database load", message)
        self.assertNotIn("AI provider", message)

    def test_wrapped_provider_http_status_controls_retry(self) -> None:
        for status in (400, 401, 403, 404, 422, 408, 429, 500, 503):
            with self.subTest(status=status):
                response = httpx.Response(
                    status, request=httpx.Request("POST", "https://provider.test/chat")
                )
                try:
                    try:
                        response.raise_for_status()
                    except httpx.HTTPStatusError as exc:
                        raise CloudError(f"Cloud HTTP error: {exc}")
                except CloudError as wrapped:
                    self.assertEqual(
                        resilience.is_permanent_job_error(wrapped),
                        status in (400, 401, 403, 404, 422),
                    )

    def test_permanent_provider_message_explains_manual_action(self) -> None:
        message = resilience.format_job_failure(
            "JUDGE_ARTIFACT", CloudError("HTTP 404"), permanent=True
        )
        self.assertIn("model availability", message)
        self.assertIn("Automatic retry is disabled", message)

    def test_transient_provider_messages_keep_retryable_signals(self) -> None:
        for detail, signal in (
            ("Cloud HTTP 429", "HTTP 429"),
            ("Cloud HTTP 503", "HTTP 503"),
            ("Provider circuit open for cloud:test", "circuit"),
        ):
            with self.subTest(detail=detail):
                error = CloudError(detail)
                self.assertFalse(resilience.is_permanent_job_error(error))
                self.assertIn(
                    signal, resilience.format_job_failure("JUDGE_ARTIFACT", error)
                )

    def test_reclustering_timeout_allows_preview_and_guarded_apply(self) -> None:
        settings = WorkerSettings(ollama_timeout=30)

        self.assertEqual(
            resilience.timeout_for_job(settings, "UPDATE_GRAPH_CLUSTERS"), 660
        )
        self.assertEqual(
            resilience.timeout_for_job(settings, "UPDATE_GRAPH_STATS"), 120
        )

    def test_cloud_concurrency_is_limited_independently(self) -> None:
        settings = WorkerSettings(
            max_concurrent_jobs=6,
            cloud_max_concurrent_jobs=1,
        )

        self.assertEqual(resilience.concurrent_job_limit(settings, "cloud"), 1)
        self.assertEqual(resilience.concurrent_job_limit(settings, "local"), 6)

    def test_retry_after_controls_transient_http_backoff(self) -> None:
        request = httpx.Request("POST", "http://api/judge")
        response = httpx.Response(
            503,
            headers={"Retry-After": "30"},
            request=request,
        )
        error = httpx.HTTPStatusError("unavailable", request=request, response=response)

        self.assertGreaterEqual(resilience.retry_delay_for_error(0, error), 30)

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
