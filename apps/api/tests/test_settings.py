import os
import tempfile
import unittest
import urllib.error
from json import JSONDecodeError
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from fastapi import HTTPException

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from berrybrain_api.database import Base
from berrybrain_api.config import _discover_project_root
from berrybrain_api.models import ModelInvocationRecord, NoteRecord
from berrybrain_api.routers import settings as settings_router
from berrybrain_api.settings_store import (
    ENCRYPTED_PREFIX,
    decode_setting_value,
    get_setting,
    list_settings,
    migrate_secret_settings,
    serialize_setting,
    set_setting,
)


class SettingsStoreTest(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine(
            "sqlite:///:memory:", connect_args={"check_same_thread": False}
        )
        Base.metadata.create_all(bind=self.engine)
        self.session_factory = sessionmaker(bind=self.engine)
        self.session = self.session_factory()
        self.session_local_patch = patch.object(
            settings_router, "SessionLocal", self.session_factory
        )
        self.session_local_patch.start()

    def tearDown(self) -> None:
        self.session_local_patch.stop()
        self.session.close()
        self.engine.dispose()

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

    def test_ai_secrets_are_encrypted_at_rest_and_decrypt_for_internal_use(
        self,
    ) -> None:
        setting = set_setting(self.session, "ai_api_key", "secret-main")

        self.assertTrue(setting.value.startswith(ENCRYPTED_PREFIX))
        self.assertNotIn("secret-main", setting.value)
        self.assertEqual(
            decode_setting_value(setting.key, setting.value), "secret-main"
        )

    def test_plaintext_legacy_secret_is_migrated_in_place(self) -> None:
        from berrybrain_api.models import SettingRecord

        legacy = SettingRecord(key="ai_api_key", value="legacy-plaintext-key")
        self.session.add(legacy)
        self.session.commit()

        migrated = migrate_secret_settings(self.session)

        self.session.refresh(legacy)
        self.assertEqual(migrated, 1)
        self.assertTrue(legacy.value.startswith(ENCRYPTED_PREFIX))
        self.assertNotIn("legacy-plaintext-key", legacy.value)
        self.assertEqual(
            decode_setting_value(legacy.key, legacy.value), "legacy-plaintext-key"
        )

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
        saved = get_setting(self.session, "ai_api_key")
        self.assertEqual(decode_setting_value(saved.key, saved.value), "sample-value")

        settings_router.clear_ai_key()
        self.session.expire_all()
        self.assertEqual(get_setting(self.session, "ai_api_key").value, "")

    def test_provider_helpers_humanize_status_and_errors(self) -> None:
        providers = {
            "https://integrate.api.nvidia.com/v1": "nvidia-nim",
            "https://api.openai.com/v1": "openai",
            "https://api.deepseek.com/v1": "deepseek",
            "https://api.groq.com/openai/v1": "groq",
            "https://openrouter.ai/api/v1": "openrouter",
            "https://models.example.com/v1": "models.example.com",
            "": "cloud",
        }
        for url, expected in providers.items():
            with self.subTest(url=url):
                self.assertEqual(settings_router._provider_name(url), expected)

        for status in (400, 401, 403, 404, 408, 429, 503):
            error = urllib.error.HTTPError("https://provider", status, "", {}, None)
            self.assertTrue(settings_router._provider_error(error))
        self.assertIn(
            "15 seconds",
            settings_router._provider_error(
                urllib.error.URLError(TimeoutError("timed out"))
            ),
        )
        self.assertIn(
            "could not be reached",
            settings_router._provider_error(urllib.error.URLError("offline")),
        )
        self.assertIn(
            "invalid response",
            settings_router._provider_error(JSONDecodeError("bad", "x", 0)),
        )
        self.assertEqual(
            settings_router._provider_error(RuntimeError("hidden")),
            "The provider connection test failed.",
        )
        self.assertIsNone(settings_router._safe_int("invalid"))
        self.assertIsNone(settings_router._safe_int(""))
        self.assertEqual(settings_router._safe_int("42"), 42)

    def test_model_test_rejects_incomplete_invalid_and_unavailable_config(self) -> None:
        incomplete = settings_router.get_ai_models(settings_router.AiModelsRequest())
        self.assertFalse(incomplete["connected"])
        self.assertIn("required", incomplete["error"])

        set_setting(self.session, "ai_api_url", "not-a-url")
        set_setting(self.session, "ai_api_key", "secret")
        invalid = settings_router.get_ai_models(settings_router.AiModelsRequest())
        self.assertFalse(invalid["connected"])
        self.assertIn("valid HTTP", invalid["error"])

        class FakeModelsResponse:
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return None

            def read(self):
                return b'{"data":[{"id":"available-model"}]}'

        set_setting(self.session, "ai_api_url", "https://api.example.com/v1")
        with patch.object(
            settings_router.urllib.request,
            "urlopen",
            return_value=FakeModelsResponse(),
        ):
            unavailable = settings_router.get_ai_models(
                settings_router.AiModelsRequest(model="missing-model")
            )
        self.assertFalse(unavailable["connected"])
        self.assertIn("invalid response", unavailable["error"])
        self.assertEqual(
            get_setting(self.session, "ai_last_test_status").value, "failed"
        )

    def test_batch_validation_rejects_ambiguous_or_oversized_input(self) -> None:
        invalid_payloads = [
            settings_router.BatchUpdateSettingsRequest(values={}),
            settings_router.BatchUpdateSettingsRequest(
                values={f"key-{index}": "value" for index in range(101)}
            ),
            settings_router.BatchUpdateSettingsRequest(
                values={"theme": "dark"}, aiTestRevision="x" * 129
            ),
            settings_router.BatchUpdateSettingsRequest(values={"": "value"}),
            settings_router.BatchUpdateSettingsRequest(values={"bad\x00key": "value"}),
        ]
        for payload in invalid_payloads:
            with (
                self.subTest(payload=payload),
                self.assertRaises(HTTPException) as error,
            ):
                settings_router.update_settings_batch(payload)
            self.assertEqual(error.exception.status_code, 400)

    def test_ai_and_graph_config_only_reveal_secrets_to_service_callers(self) -> None:
        for key, value in {
            "ai_provider": "cloud",
            "ai_api_url": "https://api.example.com/v1",
            "ai_api_key": "main-secret",
            "ai_model": "knowledge-model",
            "graph_ai_provider": "cloud",
            "graph_ai_api_key": "graph-secret",
            "graph_ai_model": "graph-model",
            "remote_content_consent": "true",
        }.items():
            set_setting(self.session, key, value)

        with patch.object(settings_router, "_caller_state", return_value="admin"):
            admin_ai = settings_router.get_ai_config(MagicMock())
            admin_graph = settings_router.get_graph_config(MagicMock())
        self.assertEqual(admin_ai["cloud_api_key"], "")
        self.assertEqual(admin_graph["cloud_api_key"], "")

        with patch.object(settings_router, "_caller_state", return_value="service"):
            service_ai = settings_router.get_ai_config(MagicMock())
            service_graph = settings_router.get_graph_config(MagicMock())
        self.assertEqual(service_ai["cloud_api_key"], "main-secret")
        self.assertEqual(service_graph["cloud_api_key"], "graph-secret")
        self.assertEqual(service_graph["default_layout"], "brain")

    def test_danger_wipe_preserves_or_resets_settings_and_only_clears_vault(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir) / "vault"
            nested = vault / "inbox"
            nested.mkdir(parents=True)
            (nested / "note.md").write_text("# Note", encoding="utf-8")
            (vault / "asset.bin").write_bytes(b"asset")
            note = NoteRecord(
                title="Wipe fixture",
                slug="wipe-fixture",
                path="inbox/note.md",
                content="# Note",
                content_hash="fixture",
            )
            self.session.add(note)
            self.session.add(
                ModelInvocationRecord(
                    capability="graph_inference",
                    provider="local",
                    model="qwen",
                    status="failed",
                )
            )
            set_setting(self.session, "theme", "dark")
            self.session.commit()

            with patch.object(
                settings_router,
                "get_app_settings",
                return_value=SimpleNamespace(vault_path=vault),
            ):
                result = settings_router.wipe_all_data(
                    settings_router.WipeDataRequest(reset_settings=False)
                )

            self.session.expire_all()
            self.assertTrue(result["settingsPreserved"])
            self.assertEqual(result["deletedFiles"], 2)
            self.assertEqual(self.session.query(NoteRecord).count(), 0)
            self.assertEqual(self.session.query(ModelInvocationRecord).count(), 0)
            self.assertEqual(get_setting(self.session, "theme").value, "dark")
            self.assertTrue(vault.exists())
            self.assertEqual(list(vault.iterdir()), [])

            with patch.object(
                settings_router,
                "get_app_settings",
                return_value=SimpleNamespace(vault_path=vault),
            ):
                reset = settings_router.wipe_all_data(
                    settings_router.WipeDataRequest(reset_settings=True)
                )
            self.session.expire_all()
            self.assertFalse(reset["settingsPreserved"])
            with self.assertRaises(HTTPException):
                get_setting(self.session, "theme")

    def test_danger_wipe_refuses_missing_and_unsafe_paths(self) -> None:
        candidates = [Path("/missing/berrybrain-vault"), Path("/")]
        for vault_path in candidates:
            with (
                self.subTest(vault_path=vault_path),
                patch.object(
                    settings_router,
                    "get_app_settings",
                    return_value=SimpleNamespace(vault_path=vault_path),
                ),
                self.assertRaises(HTTPException) as error,
            ):
                settings_router.wipe_all_data(
                    settings_router.WipeDataRequest(reset_settings=False)
                )
            self.assertEqual(error.exception.status_code, 400)


if __name__ == "__main__":
    unittest.main()
