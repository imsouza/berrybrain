import unittest
from unittest.mock import AsyncMock

from berrybrain_worker.config import WorkerSettings
from berrybrain_worker.main import process_enrich_graph_node


class _Response:
    def __init__(self, payload: dict, status_code: int = 200) -> None:
        self.payload = payload
        self.status_code = status_code

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self.payload


class WorkerEnrichmentTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.client = AsyncMock()
        self.client.post.return_value = _Response({"status": "completed"})
        self.settings = WorkerSettings(api_url="http://api")

    async def test_skips_current_completed_enrichment(self) -> None:
        self.client.get.return_value = _Response(
            {"sourceFingerprint": "current", "semanticState": "completed"}
        )

        await process_enrich_graph_node(
            self.client,
            self.settings,
            {"id": 71},
            {"node_id": 4, "source_fingerprint": "current"},
        )

        self.client.post.assert_awaited_once_with(
            "http://api/api/v1/jobs/71/complete", headers={}
        )

    async def test_skips_stale_enrichment_job(self) -> None:
        self.client.get.return_value = _Response(
            {"sourceFingerprint": "current", "semanticState": "pending"}
        )

        await process_enrich_graph_node(
            self.client,
            self.settings,
            {"id": 72},
            {"node_id": 4, "source_fingerprint": "stale"},
        )

        self.client.post.assert_awaited_once_with(
            "http://api/api/v1/jobs/72/complete", headers={}
        )

    async def test_missing_node_completes_obsolete_enrichment_job(self) -> None:
        self.client.get.return_value = _Response({}, status_code=404)

        await process_enrich_graph_node(
            self.client,
            self.settings,
            {"id": 73},
            {"node_id": 404, "source_fingerprint": "obsolete"},
        )

        self.client.post.assert_awaited_once_with(
            "http://api/api/v1/jobs/73/complete", headers={}
        )


if __name__ == "__main__":
    unittest.main()
