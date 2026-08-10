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
    load_configuration,
    provider_catalog,
    save_configuration,
)
from berrybrain_api.database import Base
from berrybrain_api.routers.ai_configuration import _validate_provider_endpoint
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
