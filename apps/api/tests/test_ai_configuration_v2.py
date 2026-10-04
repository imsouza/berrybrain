import unittest
from unittest.mock import patch

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from berrybrain_api.ai_configuration import (
    AIConfiguration,
    HippoRagSlot,
    JudgeSlot,
    ModelSlot,
    configuration_gate,
    embedding_execution_configuration,
    load_configuration,
    load_provider_credentials,
    provider_api_key,
    provider_catalog,
    save_configuration,
    save_provider_credentials,
)
from berrybrain_api.database import Base
from berrybrain_api.models import EmbeddingRecord, JobRecord, NoteRecord
from berrybrain_api.routers.ai_configuration import (
    _filter_models_by_capability,
    _probe_requested_capabilities,
    _queue_embedding_reindex,
    _validate_provider_endpoint,
)
from berrybrain_api.settings_store import set_setting


class AIConfigurationV2Test(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine(
            "sqlite:///:memory:", connect_args={"check_same_thread": False}
        )
        Base.metadata.create_all(bind=self.engine)
        self.session = sessionmaker(bind=self.engine)()

    def tearDown(self) -> None:
        self.session.close()
        self.engine.dispose()

    def test_cloud_and_local_providers_cannot_be_mixed(self) -> None:
        with self.assertRaises(ValidationError):
            AIConfiguration(
                mode="cloud",
                main=ModelSlot(provider_id="openai", model_id="chat"),
                embedding=ModelSlot(provider_id="ollama", model_id="embed"),
                judge=JudgeSlot(provider_id="openai", model_id="judge"),
                hipporag=HippoRagSlot(provider_id="openai", model_id="rag"),
                endpoint_url="https://api.openai.com/v1",
            )

    def test_disabled_judge_or_hipporag_is_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            AIConfiguration(
                mode="local",
                main=ModelSlot(provider_id="ollama", model_id="chat"),
                embedding=ModelSlot(provider_id="ollama", model_id="embed"),
                judge=JudgeSlot(provider_id="ollama", model_id="judge", enabled=False),
                hipporag=HippoRagSlot(provider_id="ollama", model_id="rag"),
                endpoint_url="http://ollama:11434",
            )

    def test_validated_configuration_opens_gate_and_updates_legacy_contract(
        self,
    ) -> None:
        configuration = AIConfiguration(
            mode="local",
            main=ModelSlot(provider_id="ollama", model_id="qwen"),
            embedding=ModelSlot(provider_id="ollama", model_id="nomic-embed-text"),
            judge=JudgeSlot(provider_id="ollama", model_id="qwen-judge"),
            hipporag=HippoRagSlot(provider_id="ollama", model_id="qwen-rag"),
            endpoint_url="http://ollama:11434",
        )

        saved = save_configuration(self.session, configuration, validated=True)
        self.session.commit()

        gate = configuration_gate(self.session)
        loaded = load_configuration(self.session)
        self.assertTrue(gate["valid"])
        self.assertFalse(gate["required"])
        self.assertEqual(loaded, saved)
        self.assertEqual(loaded.mode, "local")

    def test_legacy_mixed_configuration_requires_gate(self) -> None:
        set_setting(self.session, "ai_provider", "cloud")
        set_setting(self.session, "graph_ai_provider", "local")
        set_setting(self.session, "kb_embedding_provider", "cloud")
        self.session.commit()

        self.assertIsNone(load_configuration(self.session))
        self.assertEqual(
            configuration_gate(self.session)["reason"],
            "missing_or_conflicting_configuration",
        )

    def test_provider_catalog_supplies_mode_and_default_url(self) -> None:
        providers = {item["id"]: item for item in provider_catalog()}

        self.assertEqual(providers["nvidia-nim"]["mode"], "cloud")
        self.assertEqual(
            providers["nvidia-nim"]["url"],
            "https://integrate.api.nvidia.com/v1",
        )
        self.assertEqual(providers["ollama"]["mode"], "local")

    def test_known_provider_rejects_endpoint_override(self) -> None:
        with self.assertRaisesRegex(HTTPException, "registered endpoint"):
            _validate_provider_endpoint("openai", "https://attacker.example/v1")

    def test_custom_cloud_rejects_private_network_resolution(self) -> None:
        with (
            patch(
                "berrybrain_api.routers.ai_configuration.socket.getaddrinfo",
                return_value=[(2, 1, 6, "", ("127.0.0.1", 443))],
            ),
            self.assertRaisesRegex(HTTPException, "public addresses"),
        ):
            _validate_provider_endpoint("custom-cloud", "https://llm.example/v1")

    def test_ollama_allows_local_endpoint(self) -> None:
        _validate_provider_endpoint("ollama", "http://ollama:11434")

    def test_capability_probe_rejects_chat_model_in_embedding_slot(self) -> None:
        configuration = AIConfiguration(
            mode="cloud",
            main=ModelSlot(provider_id="nvidia-nim", model_id="chat-main"),
            embedding=ModelSlot(provider_id="nvidia-nim", model_id="chat-only"),
            judge=JudgeSlot(provider_id="nvidia-nim", model_id="chat-judge"),
            hipporag=HippoRagSlot(provider_id="nvidia-nim", model_id="chat-rag"),
            endpoint_url="https://integrate.api.nvidia.com/v1",
        )

        def probe(**kwargs):
            return {
                "available": kwargs["capability"] != "embeddings",
                "model": kwargs["model"],
                "capability": kwargs["capability"],
                "status": 404 if kwargs["capability"] == "embeddings" else 200,
            }

        with (
            patch(
                "berrybrain_api.routers.ai_configuration._probe_model_capability",
                side_effect=probe,
            ),
            self.assertRaises(HTTPException) as error,
        ):
            _probe_requested_capabilities(
                configuration,
                {
                    "nvidia-nim": {
                        "endpoint": configuration.endpoint_url,
                        "api_key": "secret",
                        "models": [
                            "chat-main",
                            "chat-only",
                            "chat-judge",
                            "chat-rag",
                        ],
                    }
                },
            )

        self.assertEqual(error.exception.status_code, 422)
        self.assertEqual(
            error.exception.detail["code"],
            "model_capability_mismatch",
        )
        self.assertEqual(error.exception.detail["failures"][0]["slot"], "embedding")

    def test_embedding_model_discovery_returns_only_api_verified_models(self) -> None:
        def probe(**kwargs):
            supported = kwargs["model"] == "embed-capable"
            return {
                "available": supported,
                "model": kwargs["model"],
                "capability": kwargs["capability"],
                "status": 200 if supported else 404,
                **({"dimensions": 1024} if supported else {}),
            }

        with patch(
            "berrybrain_api.routers.ai_configuration._probe_model_capability",
            side_effect=probe,
        ):
            models = _filter_models_by_capability(
                "nvidia-nim",
                "https://integrate.api.nvidia.com/v1",
                "secret",
                ["chat-only", "embed-capable"],
                "embeddings",
            )

        self.assertEqual(
            models,
            [
                {
                    "id": "embed-capable",
                    "capability": "embeddings",
                    "dimensions": 1024,
                }
            ],
        )

    def test_mixed_cloud_slots_use_their_own_provider_context(self) -> None:
        configuration = AIConfiguration(
            mode="cloud",
            main=ModelSlot(provider_id="deepseek", model_id="deepseek-v4-pro"),
            embedding=ModelSlot(provider_id="nvidia-nim", model_id="nvidia/embed"),
            judge=JudgeSlot(provider_id="deepseek", model_id="deepseek-v4-pro"),
            hipporag=HippoRagSlot(provider_id="deepseek", model_id="deepseek-v4-pro"),
            endpoint_url="https://api.deepseek.com",
        )
        contexts = {
            "deepseek": {
                "endpoint": "https://api.deepseek.com",
                "api_key": "deepseek-secret",
                "models": ["deepseek-v4-pro"],
            },
            "nvidia-nim": {
                "endpoint": "https://integrate.api.nvidia.com/v1",
                "api_key": "nvidia-secret",
                "models": ["nvidia/embed"],
            },
        }
        calls = []

        def probe(**kwargs):
            calls.append(kwargs)
            return {
                "available": True,
                "model": kwargs["model"],
                "capability": kwargs["capability"],
                "status": 200,
            }

        with patch(
            "berrybrain_api.routers.ai_configuration._probe_model_capability",
            side_effect=probe,
        ):
            result = _probe_requested_capabilities(configuration, contexts)

        embedding_call = next(
            item for item in calls if item["capability"] == "embeddings"
        )
        self.assertEqual(embedding_call["provider_id"], "nvidia-nim")
        self.assertEqual(
            embedding_call["endpoint"], "https://integrate.api.nvidia.com/v1"
        )
        self.assertEqual(embedding_call["api_key"], "nvidia-secret")
        self.assertEqual(result["main"]["model"], "deepseek-v4-pro")

    def test_embedding_runtime_uses_embedding_provider_key_and_endpoint(self) -> None:
        configuration = AIConfiguration(
            mode="cloud",
            main=ModelSlot(provider_id="deepseek", model_id="deepseek-v4-pro"),
            embedding=ModelSlot(provider_id="nvidia-nim", model_id="nvidia/embed"),
            judge=JudgeSlot(provider_id="deepseek", model_id="deepseek-v4-pro"),
            hipporag=HippoRagSlot(provider_id="deepseek", model_id="deepseek-v4-pro"),
            endpoint_url="https://api.deepseek.com",
        )
        save_provider_credentials(
            self.session,
            {"deepseek": "deepseek-secret", "nvidia-nim": "nvidia-secret"},
        )
        save_configuration(self.session, configuration, validated=True)
        self.session.commit()

        runtime = embedding_execution_configuration(self.session)

        self.assertEqual(runtime["cloud_provider"], "nvidia-nim")
        self.assertEqual(
            runtime["cloud_api_url"], "https://integrate.api.nvidia.com/v1"
        )
        self.assertEqual(runtime["cloud_api_key"], "nvidia-secret")
        self.assertEqual(provider_api_key(self.session, "deepseek"), "deepseek-secret")
        self.assertEqual(
            sorted(load_provider_credentials(self.session)), ["deepseek", "nvidia-nim"]
        )

    def test_embedding_provider_change_invalidates_vectors_and_queues_notes(
        self,
    ) -> None:
        previous = AIConfiguration(
            mode="cloud",
            main=ModelSlot(provider_id="deepseek", model_id="deepseek-v4-pro"),
            embedding=ModelSlot(provider_id="deepseek", model_id="old-embed"),
            judge=JudgeSlot(provider_id="deepseek", model_id="deepseek-v4-pro"),
            hipporag=HippoRagSlot(provider_id="deepseek", model_id="deepseek-v4-pro"),
            endpoint_url="https://api.deepseek.com",
        )
        current = previous.model_copy(
            update={
                "embedding": ModelSlot(
                    provider_id="nvidia-nim", model_id="nvidia/embed"
                )
            }
        )
        note = NoteRecord(
            title="Evidence",
            slug="evidence",
            path="evidence.md",
            content="Grounded content.",
            content_hash="content-v1",
        )
        self.session.add(note)
        self.session.flush()
        self.session.add(
            EmbeddingRecord(
                note_id=note.id,
                content_hash=note.content_hash,
                vector="[0.1, 0.2]",
                model="old-embed",
                provider="cloud",
                vector_dimensions=2,
            )
        )
        self.session.flush()

        result = _queue_embedding_reindex(self.session, previous, current)
        self.session.commit()

        self.assertTrue(result["required"])
        self.assertEqual(result["vectorsInvalidated"], 1)
        self.assertEqual(result["jobsQueued"], 1)
        self.assertEqual(self.session.query(EmbeddingRecord).count(), 0)
        job = self.session.query(JobRecord).one()
        self.assertEqual(job.type, "GENERATE_EMBEDDING")
        self.assertIn("nvidia-nim", job.idempotency_key)
