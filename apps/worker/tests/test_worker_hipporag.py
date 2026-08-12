import unittest
from unittest.mock import AsyncMock

from berrybrain_worker.config import WorkerSettings
from berrybrain_worker.main import (
    process_hipp_delete,
    process_hipp_index,
    process_hipp_rebuild,
    process_hipp_reconcile,
    process_sync_hipporag_graph,
)


class _SuccessfulResponse:
    status_code = 200

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return {"status": "completed"}


class WorkerHippoRagTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.client = AsyncMock()
        self.client.post.return_value = _SuccessfulResponse()
        self.client.delete.return_value = _SuccessfulResponse()
        self.settings = WorkerSettings(
            api_url="http://api",
            hipporag_url="http://hipporag:8000/",
            hipporag_service_token="service-token",
        )

    async def test_indexes_before_completing_job(self) -> None:
        await process_hipp_index(
            self.client,
            self.settings,
            {"id": 41},
            {"vault_id": "main", "doc_id": "folder/note.md", "content": "Evidence"},
        )

        index_call = self.client.post.await_args_list[0]
        self.assertEqual(index_call.args[0], "http://hipporag:8000/index")
        self.assertEqual(
            index_call.kwargs["headers"]["Authorization"], "Bearer service-token"
        )
        self.assertEqual(index_call.kwargs["json"]["doc_id"], "folder/note.md")
        self.assertEqual(self.client.post.await_count, 2)

    async def test_rejects_incomplete_index_payload(self) -> None:
        with self.assertRaisesRegex(ValueError, "requires vault_id"):
            await process_hipp_index(self.client, self.settings, {"id": 42}, {})
        self.client.post.assert_not_awaited()

    async def test_deletes_before_completing_job(self) -> None:
        await process_hipp_delete(
            self.client,
            self.settings,
            {"id": 43},
            {"vaultId": "main", "docId": "folder/note.md"},
        )

        delete_call = self.client.delete.await_args
        self.assertEqual(
            delete_call.args[0],
            "http://hipporag:8000/index/main/folder/note.md",
        )
        self.assertEqual(delete_call.kwargs["timeout"], 30)
        self.client.post.assert_awaited_once()

    async def test_runs_maintenance_operations_before_completion(self) -> None:
        await process_hipp_reconcile(self.client, self.settings, {"id": 44}, {})
        await process_hipp_rebuild(self.client, self.settings, {"id": 45}, {})

        requested_urls = [call.args[0] for call in self.client.post.await_args_list]
        self.assertEqual(
            requested_urls,
            [
                "http://hipporag:8000/reconcile",
                "http://api/api/v1/jobs/44/complete",
                "http://hipporag:8000/rebuild",
                "http://api/api/v1/jobs/45/complete",
            ],
        )

    async def test_syncs_graph_retrieval_after_topology_changes(self) -> None:
        await process_sync_hipporag_graph(
            self.client, self.settings, {"id": 46}, {"trigger": "node_deleted"}
        )

        requested_urls = [call.args[0] for call in self.client.post.await_args_list]
        self.assertEqual(
            requested_urls,
            [
                "http://api/api/v1/hipporag/sync-graph",
                "http://api/api/v1/jobs/46/complete",
            ],
        )


if __name__ == "__main__":
    unittest.main()
