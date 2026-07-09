import unittest

from berrybrain_worker.cloud_gateway import CloudError
from berrybrain_worker.config import WorkerSettings
from berrybrain_worker.ollama_gateway import OllamaError
import berrybrain_worker.main as worker_main


class WorkerPipelineFallbackTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self._originals = {
            "fetch_note": worker_main.fetch_note,
            "ollama_call": worker_main.ollama_call,
            "upsert_metadata": worker_main.upsert_metadata,
            "complete_job": worker_main.complete_job,
            "cloud_generate_embedding": worker_main.cloud_generate_embedding,
            "generate_embedding": worker_main.generate_embedding,
            "check_health": worker_main.check_health,
            "_ai_config": dict(worker_main._ai_config),
        }

    async def asyncTearDown(self) -> None:
        for name, value in self._originals.items():
            setattr(worker_main, name, value)

    async def test_extract_concepts_falls_back_when_ai_returns_error(self) -> None:
        calls = []

        async def fake_fetch_note(client, api_url, note_path):
            return {
                "path": note_path,
                "title": "Observabilidade Distribuida",
                "content": "# Observabilidade\nLogs, metricas e traces em Edge Computing.",
            }

        async def fake_ollama_call(*args, **kwargs):
            raise CloudError("Cloud returned invalid JSON")

        async def fake_upsert_metadata(*args):
            calls.append(("upsert", args[3], args[4]))

        async def fake_complete_job(client, api_url, job_id):
            calls.append(("complete", job_id))

        worker_main.fetch_note = fake_fetch_note
        worker_main.ollama_call = fake_ollama_call
        worker_main.upsert_metadata = fake_upsert_metadata
        worker_main.complete_job = fake_complete_job

        await worker_main.process_extract_concepts(
            None,
            WorkerSettings(),
            {"id": 10},
            {"note_path": "inbox/a.md", "content_hash": "abc"},
        )

        self.assertEqual(calls[0][0], "upsert")
        self.assertEqual(calls[0][1], "concepts")
        self.assertEqual(calls[0][2]["source"], "deterministic_fallback")
        self.assertEqual(calls[-1], ("complete", 10))

    async def test_generate_embedding_completes_with_skipped_status_when_providers_fail(
        self,
    ) -> None:
        calls = []

        async def fake_fetch_note(client, api_url, note_path):
            return {
                "path": note_path,
                "title": "Edge Computing",
                "content": "# Edge Computing\nProcessamento na borda.",
            }

        async def fake_cloud_embedding(*args, **kwargs):
            raise CloudError("cloud down")

        async def fake_ollama_embedding(*args, **kwargs):
            raise OllamaError("ollama down")

        async def fake_check_health(*args, **kwargs):
            return False

        async def fake_upsert_metadata(*args):
            calls.append(("upsert", args[3], args[4]))

        async def fake_complete_job(client, api_url, job_id):
            calls.append(("complete", job_id))

        worker_main.fetch_note = fake_fetch_note
        worker_main.cloud_generate_embedding = fake_cloud_embedding
        worker_main.generate_embedding = fake_ollama_embedding
        worker_main.check_health = fake_check_health
        worker_main.upsert_metadata = fake_upsert_metadata
        worker_main.complete_job = fake_complete_job
        worker_main._ai_config = {
            "provider": "cloud",
            "cloud_api_url": "https://example.test/v1",
            "cloud_api_key": "secret",
            "cloud_model": "test-model",
        }

        await worker_main.process_generate_embedding(
            None,
            WorkerSettings(),
            {"id": 11},
            {"note_path": "inbox/b.md", "content_hash": "def"},
        )

        self.assertEqual(calls[0][0], "upsert")
        self.assertEqual(calls[0][1], "embedding_status")
        self.assertEqual(calls[0][2]["status"], "skipped")
        self.assertEqual(calls[-1], ("complete", 11))

    async def test_effective_generation_model_uses_configured_cloud_model(self) -> None:
        worker_main._ai_config = {
            "provider": "cloud",
            "cloud_api_url": "https://integrate.api.nvidia.com/v1",
            "cloud_api_key": "secret",
            "cloud_model": "qwen/qwen3.5-397b-a17b",
        }

        self.assertEqual(
            worker_main.effective_generation_model("gemma3:4b"),
            "qwen/qwen3.5-397b-a17b",
        )

    async def test_graph_insights_use_graph_and_notes_context_with_provider_model(self) -> None:
        calls = []

        class FakeResponse:
            def __init__(self, payload):
                self._payload = payload
                self.status_code = 200

            def json(self):
                return self._payload

            def raise_for_status(self):
                return None

        class FakeClient:
            async def get(self, url, **kwargs):
                calls.append(("get", url))
                if url.endswith("/api/v1/graph/summary"):
                    return FakeResponse({"nodes": 2, "edges": 1, "orphans": 0})
                if url.endswith("/api/v1/graph"):
                    return FakeResponse(
                        {
                            "nodes": [
                                {"id": "note:1", "type": "note", "label": "Docker Essentials"},
                                {"id": "topico:2", "type": "topico", "label": "containers"},
                            ],
                            "edges": [
                                {
                                    "source": "note:1",
                                    "target": "topico:2",
                                    "type": "related",
                                    "reason": "A nota explica containers.",
                                    "evidence": ["Docker Essentials", "containers"],
                                }
                            ],
                        }
                    )
                if url.endswith("/api/v1/notes"):
                    return FakeResponse(
                        {
                            "notes": [
                                {
                                    "title": "Docker Essentials",
                                    "path": "permanentes/docker-essentials.md",
                                    "content": "Docker usa containers para empacotar serviços.",
                                }
                            ]
                        }
                    )
                return FakeResponse({})

            async def post(self, url, json=None, **kwargs):
                calls.append(("post", url, json))
                return FakeResponse({"ok": True})

        async def fake_ollama_call(*args, **kwargs):
            prompt = args[5]
            calls.append(("prompt", prompt))
            return {
                "insights": [
                    {
                        "type": "hypothesis",
                        "title": "Docker como base de runtime",
                        "description": "A nota sugere Docker como base para empacotar serviços.",
                        "evidence": ["Docker Essentials: Docker usa containers"],
                        "confidence": 0.82,
                    }
                ]
            }

        async def fake_complete_job(client, api_url, job_id):
            calls.append(("complete", job_id))

        worker_main.ollama_call = fake_ollama_call
        worker_main.complete_job = fake_complete_job
        worker_main._ai_config = {
            "provider": "cloud",
            "cloud_api_url": "https://integrate.api.nvidia.com/v1",
            "cloud_api_key": "secret",
            "cloud_model": "qwen/qwen3.5-397b-a17b",
        }

        await worker_main.process_generate_graph_insights(
            FakeClient(),
            WorkerSettings(),
            {"id": 12},
            {"note_path": "permanentes/docker-essentials.md"},
        )

        sync_call = next(call for call in calls if call[0] == "post" and call[1].endswith("/api/v1/insights/sync"))
        synced = sync_call[2]["payload"]["insights"][0]
        prompt = next(call[1] for call in calls if call[0] == "prompt")

        self.assertIn("Docker usa containers", prompt)
        self.assertEqual(synced["provider"], "nvidia-nim")
        self.assertEqual(synced["model"], "qwen/qwen3.5-397b-a17b")
        self.assertEqual(calls[-1], ("complete", 12))


if __name__ == "__main__":
    unittest.main()
