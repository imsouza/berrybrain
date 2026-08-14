import unittest
from unittest.mock import patch

import berrybrain_worker.cloud_gateway as cloud_gateway
import berrybrain_worker.main as worker_main
from berrybrain_worker.cloud_gateway import CloudError
from berrybrain_worker.config import WorkerSettings
from berrybrain_worker.ollama_gateway import OllamaError


class WorkerPipelineFallbackTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self._originals = {
            "fetch_note": worker_main.fetch_note,
            "ollama_call": worker_main.ollama_call,
            "upsert_metadata": worker_main.upsert_metadata,
            "complete_job": worker_main.complete_job,
            "cloud_generate_embedding": worker_main.cloud_generate_embedding,
            "cloud_generate": worker_main.cloud_generate,
            "cloud_generate_json": worker_main.cloud_generate_json,
            "generate": worker_main.generate,
            "generate_embedding": worker_main.generate_embedding,
            "generate_json": worker_main.generate_json,
            "check_health": worker_main.check_health,
            "log_ai_call": worker_main.log_ai_call,
            "_ai_config": dict(worker_main._ai_config),
        }

    async def asyncTearDown(self) -> None:
        for name, value in self._originals.items():
            setattr(worker_main, name, value)

    async def test_global_cluster_job_does_not_send_an_empty_scope(self) -> None:
        payloads = []

        class FakeResponse:
            def raise_for_status(self):
                return None

            def json(self):
                return {"previewToken": "token"}

        class FakeClient:
            async def post(self, _url, **kwargs):
                payloads.append(kwargs["json"])
                return FakeResponse()

        async def fake_complete_job(*_args):
            return None

        worker_main.complete_job = fake_complete_job

        await worker_main.process_update_graph_clusters(
            FakeClient(), WorkerSettings(), {"id": 42}, {}
        )

        self.assertEqual(payloads[0], {"preview": True})
        self.assertEqual(payloads[1], {"preview": False, "preview_token": "token"})

    async def test_scoped_cluster_job_preserves_an_explicit_scope(self) -> None:
        payloads = []

        class FakeResponse:
            def raise_for_status(self):
                return None

            def json(self):
                return {"previewToken": "token"}

        class FakeClient:
            async def post(self, _url, **kwargs):
                payloads.append(kwargs["json"])
                return FakeResponse()

        async def fake_complete_job(*_args):
            return None

        worker_main.complete_job = fake_complete_job

        await worker_main.process_update_graph_clusters(
            FakeClient(),
            WorkerSettings(),
            {"id": 43},
            {"scope_node_ids": [7, "8", "invalid"]},
        )

        self.assertEqual(payloads[0]["scope_node_ids"], [7, 8])
        self.assertEqual(payloads[1]["scope_node_ids"], [7, 8])

    async def test_nvidia_nim_embedding_uses_asymmetric_contract(self) -> None:
        requests = []

        class FakeResponse:
            status_code = 200

            def raise_for_status(self):
                return None

            def json(self):
                return {"data": [{"embedding": [0.25, 0.75]}]}

        class FakeClient:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                return None

            async def post(self, url, **kwargs):
                requests.append((url, kwargs["json"]))
                return FakeResponse()

        with patch.object(
            cloud_gateway.httpx, "AsyncClient", return_value=FakeClient()
        ):
            vector = await cloud_gateway.cloud_generate_embedding(
                "https://integrate.api.nvidia.com/v1",
                "secret",
                "nvidia/nv-embedqa-e5-v5",
                "Knowledge graph provenance",
                provider="nvidia-nim",
                input_type="passage",
            )

        self.assertEqual(vector, [0.25, 0.75])
        self.assertEqual(requests[0][1]["input_type"], "passage")
        self.assertEqual(requests[0][1]["encoding_format"], "float")
        self.assertEqual(requests[0][1]["truncate"], "END")

    async def test_extract_concepts_fails_when_ai_returns_error(self) -> None:
        calls = []

        async def fake_fetch_note(client, api_url, note_path):
            return {
                "path": note_path,
                "title": "Distributed Observability",
                "content": "# Observability\nLogs, metrics, and traces in edge computing.",
            }

        async def fake_ollama_call(*args, **kwargs):
            raise CloudError("Cloud returned invalid JSON")

        async def fake_upsert_metadata(*args):
            calls.append(("upsert", args[3], args[4]))

        async def fake_complete_job(client, api_url, job_id):
            calls.append(("complete", job_id))

        class FakeResponse:
            status_code = 200

            def json(self):
                return {"id": 11}

            def raise_for_status(self):
                return None

        class FakeClient:
            async def get(self, *args, **kwargs):
                return FakeResponse()

        worker_main.fetch_note = fake_fetch_note
        worker_main.ollama_call = fake_ollama_call
        worker_main.upsert_metadata = fake_upsert_metadata
        worker_main.complete_job = fake_complete_job

        with self.assertRaises(CloudError):
            await worker_main.process_extract_concepts(
                None,
                WorkerSettings(),
                {"id": 10},
                {"note_path": "inbox/a.md", "content_hash": "abc"},
            )

        self.assertEqual(calls, [])

    async def test_attachment_job_forwards_selected_extractor(self) -> None:
        calls = []

        async def fake_complete_job(client, api_url, job_id):
            calls.append(("complete", job_id))

        class FakeResponse:
            def raise_for_status(self):
                return None

        class FakeClient:
            async def post(self, url, **kwargs):
                calls.append((url, kwargs.get("json")))
                return FakeResponse()

        worker_main.complete_job = fake_complete_job
        await worker_main.process_attachment(
            FakeClient(),
            WorkerSettings(),
            {"id": 12},
            {"attachment_id": 8, "extractor": "tesseract"},
        )

        self.assertEqual(calls[0][1], {"extractor": "tesseract"})
        self.assertEqual(calls[-1], ("complete", 12))

    async def test_cloud_generation_requires_remote_content_consent(self) -> None:
        called = False

        async def fake_cloud_generate_json(*args, **kwargs):
            nonlocal called
            called = True
            return {"ok": True}

        worker_main.cloud_generate_json = fake_cloud_generate_json
        worker_main._ai_config = {
            "provider": "cloud",
            "cloud_api_url": "https://example.test/v1",
            "cloud_api_key": "secret",
            "cloud_model": "model",
            "remote_content_consent": "false",
        }
        with self.assertRaises(CloudError):
            await worker_main.ollama_call(
                None,
                "http://api",
                WorkerSettings(),
                "private.md",
                "local-model",
                "private note content",
            )
        self.assertFalse(called)

    async def test_cloud_mode_never_calls_ollama_and_logs_resolved_route(self) -> None:
        calls = []

        async def fake_cloud_generate_json(*args, **kwargs):
            calls.append(("cloud", args[2]))
            return {"ok": True}

        async def unexpected_local_call(*args, **kwargs):
            self.fail("Cloud mode must not call Ollama")

        async def fake_log(*args, **kwargs):
            calls.append(("log", args[2], args[3]))

        worker_main.cloud_generate_json = fake_cloud_generate_json
        worker_main.generate_json = unexpected_local_call
        worker_main.check_health = unexpected_local_call
        worker_main.log_ai_call = fake_log
        worker_main._ai_config = {
            "provider": "cloud",
            "cloud_provider": "nvidia-nim",
            "cloud_api_url": "https://exclusive-cloud.example/v1",
            "cloud_api_key": "secret",
            "cloud_model": "z-ai/glm-5.2",
            "remote_content_consent": "true",
        }

        result = await worker_main.ollama_call(
            None,
            "http://api",
            WorkerSettings(),
            "private.md",
            "qwen3:14b",
            "private note content",
        )

        self.assertEqual(result, {"ok": True})
        self.assertEqual(calls[0], ("cloud", "z-ai/glm-5.2"))
        self.assertEqual(calls[-1], ("log", "nvidia-nim", "z-ai/glm-5.2"))

    async def test_local_mode_never_calls_cloud_and_logs_ollama(self) -> None:
        calls = []

        async def unexpected_cloud_call(*args, **kwargs):
            self.fail("Local mode must not call a cloud provider")

        async def fake_health(*args, **kwargs):
            return True

        async def fake_generate_json(*args, **kwargs):
            calls.append(("local", args[1]))
            return {"ok": True}

        async def fake_log(*args, **kwargs):
            calls.append(("log", args[2], args[3]))

        worker_main.cloud_generate_json = unexpected_cloud_call
        worker_main.check_health = fake_health
        worker_main.generate_json = fake_generate_json
        worker_main.log_ai_call = fake_log
        worker_main._ai_config = {"provider": "local"}

        result = await worker_main.ollama_call(
            None,
            "http://api",
            WorkerSettings(),
            "local.md",
            "qwen3:14b",
            "local note content",
        )

        self.assertEqual(result, {"ok": True})
        self.assertEqual(calls[0], ("local", "qwen3:14b"))
        self.assertEqual(calls[-1], ("log", "ollama", "qwen3:14b"))

    async def test_unreachable_local_provider_fails_fast_before_generation(
        self,
    ) -> None:
        generated = False

        async def fake_health(*args, **kwargs):
            return False

        async def fake_generate(*args, **kwargs):
            nonlocal generated
            generated = True
            return {"ok": True}

        worker_main.check_health = fake_health
        worker_main.generate_json = fake_generate
        worker_main._ai_config = {"provider": "local"}
        with self.assertRaises(OllamaError):
            await worker_main.ollama_call(
                None,
                "http://api",
                WorkerSettings(),
                "note.md",
                "model",
                "note content",
            )
        self.assertFalse(generated)

    async def test_graph_insight_deterministic_provider_fallback_is_removed(
        self,
    ) -> None:
        self.assertFalse(
            hasattr(
                worker_main,
                "complete_graph_insights_with_deterministic_fallback",
            )
        )

    async def test_generate_embedding_fails_when_provider_fails(
        self,
    ) -> None:
        calls = []

        async def fake_fetch_note(client, api_url, note_path):
            return {
                "path": note_path,
                "title": "Edge Computing",
                "content": "# Edge Computing\nProcessing at the edge.",
            }

        async def fake_cloud_embedding(*args, **kwargs):
            calls.append(("cloud_embedding", kwargs))
            raise CloudError("cloud down")

        async def fake_ollama_embedding(*args, **kwargs):
            raise OllamaError("ollama down")

        async def fake_check_health(*args, **kwargs):
            return False

        async def fake_upsert_metadata(*args):
            calls.append(("upsert", args[3], args[4]))

        async def fake_complete_job(client, api_url, job_id):
            calls.append(("complete", job_id))

        class FakeResponse:
            status_code = 200

            def json(self):
                return {"id": 11}

            def raise_for_status(self):
                return None

        class FakeClient:
            async def get(self, *args, **kwargs):
                return FakeResponse()

        worker_main.fetch_note = fake_fetch_note
        worker_main.cloud_generate_embedding = fake_cloud_embedding
        worker_main.generate_embedding = fake_ollama_embedding
        worker_main.check_health = fake_check_health
        worker_main.upsert_metadata = fake_upsert_metadata
        worker_main.complete_job = fake_complete_job
        worker_main._ai_config = {
            "provider": "cloud",
            "remote_content_consent": "true",
            "cloud_api_url": "https://example.test/v1",
            "cloud_api_key": "secret",
            "cloud_provider": "nvidia-nim",
            "cloud_model": "test-model",
            "kb_embedding_provider": "cloud",
            "embedding_model": "embed-model",
        }

        with self.assertRaises(CloudError):
            await worker_main.process_generate_embedding(
                FakeClient(),
                WorkerSettings(),
                {"id": 11},
                {"note_path": "inbox/b.md", "content_hash": "def"},
            )

        self.assertEqual(
            calls,
            [
                (
                    "cloud_embedding",
                    {"provider": "nvidia-nim", "input_type": "passage"},
                )
            ],
        )

    async def test_generate_embedding_posts_one_embedding_per_chunk(self) -> None:
        calls = []

        class FakeResponse:
            status_code = 200

            def __init__(self, payload=None):
                self._payload = payload or {}

            def json(self):
                return self._payload

            def raise_for_status(self):
                return None

        class FakeClient:
            async def get(self, *args, **kwargs):
                return FakeResponse({"id": 42})

            async def post(self, url, json=None, **kwargs):
                calls.append(("post", url, json))
                return FakeResponse({"embedding": {"id": len(calls)}})

        async def fake_fetch_note(client, api_url, note_path):
            return {
                "path": note_path,
                "title": "Long Note",
                "content": "# Part 1\n"
                + ("Docker containers and Linux namespaces.\n" * 120)
                + "\n# Part 2\n"
                + ("Async Python workers and queues.\n" * 120),
            }

        async def fake_generate_embedding(*args, **kwargs):
            text = args[2]
            return [float(len(text)), 1.0]

        async def fake_check_health(*args, **kwargs):
            return True

        async def fake_upsert_metadata(*args):
            calls.append(("upsert", args[3], args[4]))

        async def fake_complete_job(client, api_url, job_id):
            calls.append(("complete", job_id))

        worker_main.fetch_note = fake_fetch_note
        worker_main.generate_embedding = fake_generate_embedding
        worker_main.check_health = fake_check_health
        worker_main.upsert_metadata = fake_upsert_metadata
        worker_main.complete_job = fake_complete_job
        worker_main._ai_config = {
            "provider": "local",
            "kb_embedding_provider": "local",
            "embedding_model": "embed-model",
            "ollama_base_url": "http://ollama.test",
        }

        await worker_main.process_generate_embedding(
            FakeClient(),
            WorkerSettings(),
            {"id": 12},
            {"note_path": "inbox/long.md", "content_hash": "hash-long"},
        )

        embedding_batches = [
            call
            for call in calls
            if call[0] == "post" and call[1].endswith("/api/v1/embeddings/batch")
        ]
        self.assertGreaterEqual(len(embedding_batches), 1)
        first_embedding = embedding_batches[0][2]["embeddings"][0]
        self.assertEqual(first_embedding["chunk_index"], 0)
        self.assertIn("chunk_text", first_embedding)
        self.assertGreater(
            sum(len(call[2]["embeddings"]) for call in embedding_batches), 1
        )
        status = next(
            call[2]
            for call in calls
            if call[0] == "upsert" and call[1] == "embedding_status"
        )
        self.assertGreater(status["token_count"], 0)
        self.assertIn("duration_ms", status)
        self.assertEqual(calls[-1], ("complete", 12))

    async def test_find_connections_does_not_complete_empty_on_ai_error(self) -> None:
        calls = []

        class FakeResponse:
            status_code = 200

            def json(self):
                return {
                    "results": [
                        {
                            "title": "Docker Essentials",
                            "path": "permanent/docker.md",
                            "snippet": "Containers and Linux namespaces.",
                        }
                    ]
                }

        class FakeClient:
            async def get(self, *args, **kwargs):
                return FakeResponse()

        async def fake_fetch_note(client, api_url, note_path):
            return {
                "path": note_path,
                "title": "Linux Shell",
                "content": "Shell scripts can automate Docker workflows.",
            }

        async def fake_ollama_call(*args, **kwargs):
            raise CloudError("Cloud returned invalid JSON")

        async def fake_complete_job(client, api_url, job_id):
            calls.append(("complete", job_id))

        worker_main.fetch_note = fake_fetch_note
        worker_main.ollama_call = fake_ollama_call
        worker_main.complete_job = fake_complete_job

        with self.assertRaises(CloudError):
            await worker_main.process_find_connections(
                FakeClient(),
                WorkerSettings(),
                {"id": 14},
                {"note_path": "inbox/linux.md", "content_hash": "abc"},
            )

        self.assertEqual(calls, [])

    async def test_find_connections_uses_content_terms_for_retrieval(self) -> None:
        calls = []

        class FakeResponse:
            status_code = 200

            def __init__(self, payload=None):
                self._payload = payload or {}

            def json(self):
                return self._payload

            def raise_for_status(self):
                return None

        class FakeClient:
            async def get(self, url, params=None, **kwargs):
                calls.append(("get", url, params))
                if "similar-chunks" in url:
                    return FakeResponse(
                        {
                            "similar": [
                                {
                                    "title": "Docker Runtime",
                                    "path": "permanent/docker.md",
                                    "similarity": 0.92,
                                    "updatedAt": "2026-07-13T00:00:00",
                                    "evidence": {
                                        "text": "Linux namespaces isolate container processes.",
                                        "headingPath": "Runtime",
                                    },
                                }
                            ]
                        }
                    )
                return FakeResponse(
                    {
                        "results": [
                            {
                                "title": "Docker Runtime",
                                "path": "permanent/docker.md",
                                "snippet": "Linux namespaces appear in containers.",
                                "evidence": [
                                    {
                                        "text": "Linux namespaces isolate container processes.",
                                        "headingPath": "Runtime",
                                    }
                                ],
                            }
                        ]
                    }
                )

            async def post(self, url, json=None, **kwargs):
                calls.append(("post", url, json))
                return FakeResponse({"ok": True})

        async def fake_fetch_note(client, api_url, note_path):
            return {
                "id": 99,
                "path": note_path,
                "title": "Short",
                "content": "# Runtime Isolation\nLinux namespaces and cgroups connect to Docker.",
            }

        async def fake_ollama_call(*args, **kwargs):
            calls.append(("prompt", args[5]))
            return {
                "connections": [
                    {
                        "target_path": "permanent/docker.md",
                        "type": "semantic_similarity",
                        "confidence": 0.8,
                        "reason": "Both notes discuss Linux namespaces.",
                    }
                ]
            }

        async def fake_upsert_metadata(*args):
            calls.append(("upsert", args[3], args[4]))

        async def fake_complete_job(client, api_url, job_id):
            calls.append(("complete", job_id))

        worker_main.fetch_note = fake_fetch_note
        worker_main.ollama_call = fake_ollama_call
        worker_main.upsert_metadata = fake_upsert_metadata
        worker_main.complete_job = fake_complete_job

        await worker_main.process_find_connections(
            FakeClient(),
            WorkerSettings(),
            {"id": 15},
            {"note_path": "inbox/runtime.md", "content_hash": "abc"},
        )

        prompt = next(call[1] for call in calls if call[0] == "prompt")
        self.assertTrue(
            any("similar-chunks" in call[1] for call in calls if call[0] == "get")
        )
        self.assertFalse(
            any(
                call[1].endswith("/api/v1/search") for call in calls if call[0] == "get"
            )
        )
        self.assertIn("Linux namespaces isolate", prompt)
        self.assertIn("signal:", prompt)
        self.assertIn("updated:", prompt)
        self.assertEqual(calls[-1], ("complete", 15))

    async def test_find_connections_text_fallback_uses_content_terms(self) -> None:
        calls = []

        class FakeResponse:
            status_code = 200

            def __init__(self, payload=None):
                self._payload = payload or {}

            def json(self):
                return self._payload

            def raise_for_status(self):
                return None

        class FakeClient:
            async def get(self, url, params=None, **kwargs):
                calls.append(("get", url, params))
                return FakeResponse({"results": []})

        async def fake_fetch_note(client, api_url, note_path):
            return {
                "path": note_path,
                "title": "Short",
                "content": "# Runtime Isolation\nLinux namespaces and cgroups.",
            }

        async def fake_complete_job(client, api_url, job_id):
            calls.append(("complete", job_id))

        worker_main.fetch_note = fake_fetch_note
        worker_main.complete_job = fake_complete_job

        await worker_main.process_find_connections(
            FakeClient(),
            WorkerSettings(),
            {"id": 16},
            {"note_path": "inbox/runtime.md", "content_hash": "abc"},
        )

        query = next(call[2]["q"] for call in calls if call[0] == "get")
        self.assertIn("Runtime Isolation", query)

    async def test_find_connections_uses_markdown_links_as_candidates(self) -> None:
        calls = []

        class FakeResponse:
            status_code = 200

            def __init__(self, payload=None):
                self._payload = payload or {}

            def json(self):
                return self._payload

            def raise_for_status(self):
                return None

        class FakeClient:
            async def get(self, url, params=None, **kwargs):
                calls.append(("get", url, params))
                if "similar-chunks" in url:
                    return FakeResponse({"similar": []})
                return FakeResponse(
                    {
                        "results": [
                            {
                                "title": "Docker Essentials",
                                "path": "permanent/docker.md",
                                "snippet": "Docker basics.",
                            }
                        ]
                    }
                )

            async def post(self, url, json=None, **kwargs):
                calls.append(("post", url, json))
                return FakeResponse({"ok": True})

        async def fake_fetch_note(client, api_url, note_path):
            return {
                "id": 77,
                "path": note_path,
                "title": "Runtime",
                "links": ["Docker Essentials"],
                "content": "[[Docker Essentials]] explains runtime packaging.",
            }

        async def fake_ollama_call(*args, **kwargs):
            calls.append(("prompt", args[5]))
            return {
                "connections": [
                    {
                        "target_path": "permanent/docker.md",
                        "type": "backlink",
                        "confidence": 1.0,
                        "reason": "The source note links to Docker Essentials.",
                    }
                ]
            }

        async def fake_upsert_metadata(*args):
            calls.append(("upsert", args[3], args[4]))

        async def fake_complete_job(client, api_url, job_id):
            calls.append(("complete", job_id))

        worker_main.fetch_note = fake_fetch_note
        worker_main.ollama_call = fake_ollama_call
        worker_main.upsert_metadata = fake_upsert_metadata
        worker_main.complete_job = fake_complete_job

        await worker_main.process_find_connections(
            FakeClient(),
            WorkerSettings(),
            {"id": 17},
            {"note_path": "inbox/runtime.md", "content_hash": "abc"},
        )

        prompt = next(call[1] for call in calls if call[0] == "prompt")
        self.assertIn('The source note links to "Docker Essentials".', prompt)
        self.assertEqual(calls[-1], ("complete", 17))

    async def test_effective_generation_model_uses_configured_cloud_model(self) -> None:
        worker_main._ai_config = {
            "provider": "cloud",
            "remote_content_consent": "true",
            "cloud_api_url": "https://integrate.api.nvidia.com/v1",
            "cloud_api_key": "secret",
            "cloud_model": "qwen/qwen3.5-397b-a17b",
        }

        self.assertEqual(
            worker_main.effective_generation_model("gemma3:4b"),
            "qwen/qwen3.5-397b-a17b",
        )

    async def test_graph_insights_use_graph_and_notes_context_with_provider_model(
        self,
    ) -> None:
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
                                {
                                    "id": "note:1",
                                    "type": "note",
                                    "label": "Docker Essentials",
                                },
                                {
                                    "id": "topic:2",
                                    "type": "topic",
                                    "label": "containers",
                                },
                            ],
                            "edges": [
                                {
                                    "source": "note:1",
                                    "target": "topic:2",
                                    "type": "related",
                                    "reason": "The note explains containers.",
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
                                    "path": "permanent/docker-essentials.md",
                                    "content": "Docker uses containers to package services.",
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
                        "title": "Docker as a runtime foundation",
                        "description": "The note presents Docker as a foundation for packaging services.",
                        "evidence": ["Docker Essentials: Docker uses containers"],
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
            "remote_content_consent": "true",
            "cloud_api_url": "https://integrate.api.nvidia.com/v1",
            "cloud_api_key": "secret",
            "cloud_model": "qwen/qwen3.5-397b-a17b",
        }

        await worker_main.process_generate_graph_insights(
            FakeClient(),
            WorkerSettings(),
            {"id": 12},
            {"note_path": "permanent/docker-essentials.md"},
        )

        sync_call = next(
            call
            for call in calls
            if call[0] == "post" and call[1].endswith("/api/v1/insights/sync")
        )
        synced = sync_call[2]["payload"]["insights"][0]
        prompt = next(call[1] for call in calls if call[0] == "prompt")

        self.assertIn("Docker uses containers", prompt)
        self.assertEqual(synced["provider"], "nvidia-nim")
        self.assertEqual(synced["model"], "qwen/qwen3.5-397b-a17b")
        self.assertEqual(calls[-1], ("complete", 12))


if __name__ == "__main__":
    unittest.main()
