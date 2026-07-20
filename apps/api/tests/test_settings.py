import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from berrybrain_api.database import Base
from berrybrain_api.config import _discover_project_root
from berrybrain_api.routers import settings as settings_router
from berrybrain_api.settings_store import (
    get_setting,
    list_settings,
    serialize_setting,
    set_setting,
)


class SettingsStoreTest(unittest.TestCase):
    def setUp(self) -> None:
        engine = create_engine(
            "sqlite:///:memory:", connect_args={"check_same_thread": False}
        )
        Base.metadata.create_all(bind=engine)
        self.session_factory = sessionmaker(bind=engine)
        self.session = self.session_factory()
        self.session_local_patch = patch.object(
            settings_router, "SessionLocal", self.session_factory
        )
        self.session_local_patch.start()

    def tearDown(self) -> None:
        self.session_local_patch.stop()
        self.session.close()

    def test_set_setting_creates_and_updates_value(self) -> None:
        created = set_setting(self.session, "automation.mode", "autopilot")
        updated = set_setting(self.session, "automation.mode", "manual")

        self.assertEqual(created.id, updated.id)
        self.assertEqual(updated.value, "manual")
        self.assertEqual(get_setting(self.session, "automation.mode").value, "manual")

    def test_list_settings_orders_by_key_and_serializes(self) -> None:
        set_setting(self.session, "ui.theme", "light")
        setting = set_setting(self.session, "automation.mode", "autopilot")

        settings = list_settings(self.session)
        serialized = serialize_setting(setting)

        self.assertEqual(
            [item.key for item in settings], ["automation.mode", "ui.theme"]
        )
        self.assertEqual(serialized["key"], "automation.mode")
        self.assertEqual(serialized["value"], "autopilot")

    def test_project_root_can_be_explicit_in_packaged_runtime(self) -> None:
        with (
            tempfile.TemporaryDirectory() as tmp,
            patch.dict(os.environ, {"BERRYBRAIN_PROJECT_ROOT": tmp}),
        ):
            self.assertEqual(_discover_project_root(), Path(tmp).resolve())

    def test_api_never_returns_saved_ai_secrets(self) -> None:
        set_setting(self.session, "ai_api_key", "secret-main")
        set_setting(self.session, "graph_ai_api_key", "secret-graph")

        result = settings_router.get_settings_list(None)
        by_key = {item["key"]: item for item in result["settings"]}

        self.assertEqual(by_key["ai_api_key"]["value"], "")
        self.assertTrue(by_key["ai_api_key"]["configured"])
        self.assertEqual(by_key["graph_ai_api_key"]["value"], "")
        self.assertTrue(by_key["graph_ai_api_key"]["configured"])

        updated = settings_router.update_setting_endpoint(
            "ai_api_key",
            settings_router.UpdateSettingRequest(value="replacement-value"),
            None,
        )
        self.assertEqual(updated["setting"]["value"], "")
        self.assertTrue(updated["setting"]["configured"])

    def test_ai_status_explains_local_disabled_and_connected_states(self) -> None:
        set_setting(self.session, "ai_api_url", "https://integrate.api.nvidia.com/v1")
        set_setting(self.session, "ai_api_key", "sample-value")
        set_setting(self.session, "ai_model", "nvidia/test-model")

        local = settings_router.get_ai_status(None)
        self.assertEqual(local["state"], "local")

        set_setting(self.session, "ai_provider", "cloud")
        disabled = settings_router.get_ai_status(None)
        self.assertEqual(disabled["state"], "disabled")

        set_setting(self.session, "remote_content_consent", "true")
        settings_router._record_ai_test(
            self.session,
            "connected",
            api_url="https://integrate.api.nvidia.com/v1",
            method="chat_completions",
        )
        connected = settings_router.get_ai_status(None)
        self.assertEqual(connected["state"], "connected")
        self.assertTrue(connected["keyConfigured"])

        set_setting(self.session, "ai_api_key", "replacement-value")
        set_setting(self.session, "ai_key_revision", "changed")
        changed = settings_router.get_ai_status(None)
        self.assertEqual(changed["state"], "configured")
        self.assertEqual(changed["lastTestStatus"], "untested")

    def test_model_test_records_provider_health_without_exposing_key(self) -> None:
        set_setting(self.session, "ai_api_url", "https://integrate.api.nvidia.com/v1")
        set_setting(self.session, "ai_api_key", "sample-value")

        class FakeResponse:
            def __init__(self, payload: bytes):
                self.payload = payload

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return None

            def read(self):
                return self.payload

        with patch.object(
            settings_router.urllib.request,
            "urlopen",
            side_effect=[
                FakeResponse(b'{"data":[{"id":"nvidia/test-model"}]}'),
                FakeResponse(b'{"choices":[{"message":{"content":"OK"}}]}'),
            ],
        ):
            result = settings_router.get_ai_models(
                settings_router.AiModelsRequest(model="nvidia/test-model")
            )

        self.assertTrue(result["connected"])
        self.assertEqual(result["provider"], "nvidia-nim")
        self.assertEqual(result["models"], [{"id": "nvidia/test-model"}])
        self.assertEqual(
            get_setting(self.session, "ai_last_test_status").value, "connected"
        )
        self.assertEqual(
            get_setting(self.session, "ai_last_test_method").value,
            "chat_completions",
        )

    def test_model_listing_alone_does_not_mark_provider_connected(self) -> None:
        set_setting(self.session, "ai_api_url", "https://integrate.api.nvidia.com/v1")
        set_setting(self.session, "ai_api_key", "sample-value")

        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return None

            def read(self):
                return b'{"data":[{"id":"nvidia/test-model"}]}'

        with patch.object(
            settings_router.urllib.request,
            "urlopen",
            return_value=FakeResponse(),
        ):
            result = settings_router.get_ai_models(settings_router.AiModelsRequest())

        self.assertFalse(result["connected"])
        self.assertTrue(result["requiresModel"])
        self.assertEqual(
            get_setting(self.session, "ai_last_test_status").value, "untested"
        )

    def test_new_key_and_model_remain_connected_after_verified_save(self) -> None:
        set_setting(self.session, "ai_api_url", "https://integrate.api.nvidia.com/v1")
        set_setting(self.session, "ai_api_key", "old-key")
        set_setting(self.session, "ai_model", "old-model")

        settings_router._record_ai_test(
            self.session,
            "connected",
            api_url="https://integrate.api.nvidia.com/v1",
            method="chat_completions",
            model="new-model",
            key_revision="verified-revision",
        )
        settings_router.update_settings_batch(
            settings_router.BatchUpdateSettingsRequest(
                values={
                    "ai_provider": "cloud",
                    "ai_api_url": "https://integrate.api.nvidia.com/v1",
                    "ai_api_key": "new-key",
                    "ai_model": "new-model",
                    "remote_content_consent": "true",
                },
                aiTestRevision="verified-revision",
            )
        )

        status = settings_router.get_ai_status(None)
        self.assertEqual(status["state"], "connected")
        self.assertEqual(status["lastTestStatus"], "connected")

        set_setting(self.session, "ai_model", "untested-model")
        changed = settings_router.get_ai_status(None)
        self.assertEqual(changed["state"], "configured")
        self.assertEqual(changed["lastTestStatus"], "untested")

    def test_unverified_key_change_invalidates_provider_test(self) -> None:
        set_setting(self.session, "ai_provider", "cloud")
        set_setting(self.session, "ai_api_url", "https://api.example.com/v1")
        set_setting(self.session, "ai_api_key", "old-key")
        set_setting(self.session, "ai_model", "tested-model")
        set_setting(self.session, "remote_content_consent", "true")
        settings_router._record_ai_test(
            self.session,
            "connected",
            api_url="https://api.example.com/v1",
            method="chat_completions",
            model="tested-model",
            key_revision="verified-revision",
        )

        settings_router.update_settings_batch(
            settings_router.BatchUpdateSettingsRequest(
                values={"ai_api_key": "untested-key"},
                aiTestRevision="wrong-revision",
            )
        )

        status = settings_router.get_ai_status(None)
        self.assertEqual(status["state"], "configured")
        self.assertEqual(status["lastTestStatus"], "untested")

    def test_blank_secret_batch_preserves_saved_key_and_clear_is_explicit(self) -> None:
        set_setting(self.session, "ai_api_key", "sample-value")

        settings_router.update_settings_batch(
            settings_router.BatchUpdateSettingsRequest(
                values={"ai_api_key": "", "theme": "dark"}
            )
        )
        self.session.expire_all()
        self.assertEqual(get_setting(self.session, "ai_api_key").value, "sample-value")

        settings_router.clear_ai_key()
        self.session.expire_all()
        self.assertEqual(get_setting(self.session, "ai_api_key").value, "")


if __name__ == "__main__":
    unittest.main()
