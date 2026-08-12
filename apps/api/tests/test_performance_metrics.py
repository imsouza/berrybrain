import unittest

from berrybrain_api.performance_metrics import (
    begin_request,
    performance_snapshot,
    record_request,
    reset_performance_metrics,
)


class PerformanceMetricsTest(unittest.TestCase):
    def setUp(self) -> None:
        reset_performance_metrics()

    def test_accepts_safe_correlation_and_trace_identifiers(self) -> None:
        self.assertEqual(
            begin_request({"x-correlation-id": "request-42"}), "request-42"
        )
        trace_id = "a" * 32
        self.assertEqual(
            begin_request({"traceparent": f"00-{trace_id}-{'b' * 16}-01"}), trace_id
        )
        self.assertEqual(len(begin_request({"x-correlation-id": "unsafe value"})), 32)

    def test_aggregates_only_bounded_route_metadata(self) -> None:
        record_request("GET", "/api/v1/notes/{note_id}", 200, 10)
        record_request("GET", "/api/v1/notes/{note_id}", 500, 30)
        snapshot = performance_snapshot()
        route = snapshot["routes"][0]
        self.assertEqual(route["route"], "/api/v1/notes/{note_id}")
        self.assertEqual(route["samples"], 2)
        self.assertEqual(route["errorRate"], 0.5)
        self.assertEqual(route["latencyP50Ms"], 20)


if __name__ == "__main__":
    unittest.main()
