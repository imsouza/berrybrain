import unittest
from unittest.mock import AsyncMock

from berrybrain_worker.config import WorkerSettings
from berrybrain_worker.main import process_judge_artifact


class _SuccessfulResponse:
    status_code = 200

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, str]:
        return {"status": "success"}


class WorkerJudgeTest(unittest.IsolatedAsyncioTestCase):
    async def test_judge_request_uses_ai_job_timeout(self) -> None:
        client = AsyncMock()
        client.post.return_value = _SuccessfulResponse()
        settings = WorkerSettings(ollama_timeout=120)

        await process_judge_artifact(
            client,
            settings,
            {"id": 42},
            {"artifact_type": "node", "artifact_id": 7},
        )

        judge_call = client.post.await_args_list[0]
        self.assertEqual(judge_call.kwargs["timeout"], 150)
        self.assertEqual(client.post.await_count, 2)


if __name__ == "__main__":
    unittest.main()
