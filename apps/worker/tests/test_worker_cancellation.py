import asyncio
import unittest
from contextlib import suppress
from unittest.mock import AsyncMock, patch

import httpx

from berrybrain_worker.api_client import (
    JobCancellationRequested,
    _claim_tokens,
    claim_next_job,
    complete_job,
)
from berrybrain_worker.main import cancel_process_when_requested


class WorkerCancellationTest(unittest.IsolatedAsyncioTestCase):
    def tearDown(self) -> None:
        _claim_tokens.clear()

    async def test_claim_token_is_returned_on_terminal_message(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path.endswith("/claim"):
                return httpx.Response(
                    200,
                    json={"job": {"id": 12, "claim_token": "claim-12"}},
                    request=request,
                )
            self.assertEqual(request.headers["X-BerryBrain-Claim-Token"], "claim-12")
            return httpx.Response(200, json={"job": {"id": 12}}, request=request)

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            await claim_next_job(client, "http://api")
            await complete_job(client, "http://api", 12)

        self.assertNotIn(12, _claim_tokens)

    async def test_complete_surfaces_server_cancellation(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(request.url.path, "/api/v1/jobs/7/complete")
            return httpx.Response(
                409,
                json={"detail": "Job cancellation requested"},
                request=request,
            )

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            with self.assertRaises(JobCancellationRequested):
                await complete_job(client, "http://api", 7)

    async def test_watcher_cancels_running_process(self) -> None:
        process_task = asyncio.create_task(asyncio.sleep(60))
        cancel_event = asyncio.Event()
        with patch(
            "berrybrain_worker.main.is_job_cancellation_requested",
            new=AsyncMock(side_effect=[False, True]),
        ):
            await cancel_process_when_requested(
                AsyncMock(),
                "http://api",
                9,
                process_task,
                cancel_event,
                poll_seconds=0,
            )

        with suppress(asyncio.CancelledError):
            await process_task
        self.assertTrue(cancel_event.is_set())
        self.assertTrue(process_task.cancelled())


if __name__ == "__main__":
    unittest.main()
