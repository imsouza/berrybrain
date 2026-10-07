import asyncio
import unittest
from unittest.mock import AsyncMock, patch

import httpx

from berrybrain_worker import api_client, main
from berrybrain_worker.config import WorkerSettings


class WorkerLeaseRecoveryTest(unittest.IsolatedAsyncioTestCase):
    async def test_transient_failure_does_not_stop_future_renewals(self):
        request = httpx.Request("POST", "http://api/lease")
        failure = httpx.ReadTimeout("temporary", request=request)
        renew = AsyncMock(side_effect=[failure, None])
        sleep = AsyncMock(side_effect=[None, None, asyncio.CancelledError()])
        with (
            patch.object(api_client, "renew_job_lease", renew),
            patch.object(api_client.asyncio, "sleep", sleep),
        ):
            await api_client.renew_lease_until_done(AsyncMock(), "http://api", 17)
        self.assertEqual(renew.await_count, 2)

    async def test_lost_claim_stops_renewal(self):
        request = httpx.Request("POST", "http://api/lease")
        response = httpx.Response(409, request=request)
        failure = httpx.HTTPStatusError(
            "lost claim", request=request, response=response
        )
        renew = AsyncMock(side_effect=failure)
        with (
            patch.object(api_client, "renew_job_lease", renew),
            patch.object(api_client.asyncio, "sleep", AsyncMock()),
        ):
            await api_client.renew_lease_until_done(AsyncMock(), "http://api", 17)
        self.assertEqual(renew.await_count, 1)

    async def test_graph_statistics_use_explicit_request_timeouts(self):
        requests = []

        def respond(request):
            requests.append(request)
            return httpx.Response(200, json={})

        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            with patch.object(main, "complete_job", AsyncMock()):
                await main.process_update_graph_stats(
                    client, WorkerSettings(), {"id": 17}, {}
                )
        self.assertEqual(len(requests), 2)
        self.assertTrue(all(r.extensions["timeout"]["read"] == 60 for r in requests))
