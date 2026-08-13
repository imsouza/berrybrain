import unittest

from berrybrain_worker.parity import check_api_parity


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


class FakeClient:
    def __init__(self):
        self.urls = []

    async def get(self, url, **kwargs):
        self.urls.append(url)
        if url.endswith("/api/v1/status"):
            return FakeResponse({"status": "ok"})
        return FakeResponse({"diagnostics": []})


class WorkerParityTest(unittest.IsolatedAsyncioTestCase):
    async def test_uses_the_registered_vault_diagnostic_route(self) -> None:
        client = FakeClient()

        result = await check_api_parity(client, "http://api:8000")

        self.assertTrue(result["ok"])
        self.assertEqual(result["warnings"], [])
        self.assertEqual(
            client.urls,
            [
                "http://api:8000/api/v1/status",
                "http://api:8000/api/v1/vault/debug/vault-graph-pipeline",
            ],
        )


if __name__ == "__main__":
    unittest.main()
