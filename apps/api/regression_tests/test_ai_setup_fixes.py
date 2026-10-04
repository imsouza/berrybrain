"""Isolated product regressions. No production DB, vault, benchmark or model calls."""

import ast
import atexit
import io
import json
import os
import tempfile
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

_sandbox = tempfile.TemporaryDirectory(prefix="berrybrain-ai-setup-")
atexit.register(_sandbox.cleanup)
os.environ.update(
    {
        "BERRYBRAIN_PROJECT_ROOT": _sandbox.name,
        "BERRYBRAIN_DATABASE_URL": f"sqlite:///{_sandbox.name}/unused.db",
        "BERRYBRAIN_VAULT_PATH": f"{_sandbox.name}/vault",
        "BERRYBRAIN_VAULT_WATCHER_ENABLED": "false",
        "BERRYBRAIN_ENABLE_DEFAULT_OWNER": "false",
        "BERRYBRAIN_LOG_PATH": f"{_sandbox.name}/logs",
    }
)

from pydantic import ValidationError  # noqa: E402
from sqlalchemy import create_engine, select  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from berrybrain_api.ai_configuration import (  # noqa: E402
    AIConfiguration,
    HippoRagSlot,
    JudgeSlot,
    ModelSlot,
    provider_catalog,
    save_configuration,
    save_provider_credentials,
)
from berrybrain_api.ai_status import saved_test_status  # noqa: E402
from berrybrain_api.database import Base  # noqa: E402
from berrybrain_api.home_summary import _ai_config, _cloud_status  # noqa: E402
from berrybrain_api.judge_committee import eligible_committee_slots  # noqa: E402
from berrybrain_api.models import JobRecord, NoteRecord, SettingRecord  # noqa: E402
from berrybrain_api.routers import ai_configuration as routes  # noqa: E402
from berrybrain_api.routers import judge, settings  # noqa: E402
from berrybrain_api.settings_store import (  # noqa: E402
    decode_setting_value,
    set_setting,
)


class AISetupRegressions(unittest.TestCase):
    def test_claim_after_move_supersedes_duplicate_without_unique_key_collision(self):
        from berrybrain_api.jobs import PARSE_NOTE, RUNNING, SUPERSEDED, claim_next_job

        with self.engine.begin() as connection:
            connection.exec_driver_sql(
                "CREATE UNIQUE INDEX test_job_keys ON jobs(idempotency_key)"
            )
        note = NoteRecord(
            title="Moved", slug="moved", path="Matematica/moved.md", content_hash="abc"
        )
        self.session.add(note)
        self.session.flush()
        old = JobRecord(
            type=PARSE_NOTE,
            note_id=note.id,
            note_path="inbox/moved.md",
            content_hash="abc",
            idempotency_key=f"{PARSE_NOTE}:inbox/moved.md:abc",
        )
        current = JobRecord(
            type=PARSE_NOTE,
            note_id=note.id,
            note_path=note.path,
            content_hash="abc",
            idempotency_key=f"{PARSE_NOTE}:{note.path}:abc",
        )
        self.session.add_all([old, current])
        self.session.commit()
        claimed = claim_next_job(self.session)
        self.assertEqual(claimed.id, current.id)
        self.session.refresh(old)
        self.assertEqual(old.status, SUPERSEDED)
        self.assertEqual(claimed.status, RUNNING)
        self.assertNotEqual(old.idempotency_key, current.idempotency_key)

    def test_move_without_duplicate_refreshes_original_job(self):
        from berrybrain_api.jobs import PARSE_NOTE, canonicalize_job_note_reference

        note = NoteRecord(
            title="Moved", slug="moved", path="Matematica/moved.md", content_hash="abc"
        )
        self.session.add(note)
        self.session.flush()
        job = JobRecord(
            type=PARSE_NOTE,
            note_id=note.id,
            note_path="inbox/moved.md",
            content_hash="abc",
            idempotency_key=f"{PARSE_NOTE}:inbox/moved.md:abc",
        )
        self.session.add(job)
        self.session.commit()
        self.assertEqual(
            canonicalize_job_note_reference(self.session, job), "refreshed"
        )
        self.session.commit()
        self.assertEqual(job.note_path, note.path)
        self.assertEqual(job.idempotency_key, f"{PARSE_NOTE}:{note.path}:abc")

    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.factory = sessionmaker(bind=self.engine)
        self.session = self.factory()
        self.addCleanup(self.engine.dispose)
        self.addCleanup(self.session.close)
        for target in ("socket.create_connection", "urllib.request.urlopen"):
            block = patch(target, side_effect=AssertionError("Live network forbidden"))
            block.start()
            self.addCleanup(block.stop)

    def configuration(self):
        return AIConfiguration(
            mode="cloud",
            endpoint_url="https://opencode.ai/zen/v1",
            main=ModelSlot(provider_id="opencode-zen", model_id="big-pickle"),
            embedding=ModelSlot(provider_id="nvidia-nim", model_id="embed"),
            judge=JudgeSlot(provider_id="opencode-zen", model_id="glm-5"),
            hipporag=HippoRagSlot(provider_id="opencode-zen", model_id="kimi-k2.5"),
        )

    def save(self, validated=True):
        save_provider_credentials(self.session, {"opencode-zen": "fixture-key"})
        set_setting(self.session, "ai_api_key", "fixture-key")
        saved = save_configuration(
            self.session, self.configuration(), validated=validated
        )
        self.session.commit()
        return saved

    def values(self):
        self.session.expire_all()
        return {
            r.key: decode_setting_value(r.key, r.value)
            for r in self.session.execute(select(SettingRecord)).scalars()
        }

    def slots(self):
        return [
            {
                "slot": f"judge-{i+1}",
                "provider": "opencode-zen",
                "model": model,
                "role": "general",
                "focus": "Check evidence",
            }
            for i, model in enumerate(["glm-5", "kimi-k2.5", "minimax-m2.5"])
        ]

    def mode(self, slots, size=3):
        with patch.object(judge, "SessionLocal", self.factory):
            return judge.set_judge_mode(
                judge.JudgeModeUpdate(
                    mode="committee",
                    committee=slots,
                    committee_size=size,
                    consent_at=datetime.now(UTC).isoformat(),
                )
            )

    def test_saved_v2_validation_is_connected_in_home_and_settings(self):
        self.save()
        self.assertEqual(saved_test_status(self.session, self.values())[0], "connected")
        self.assertEqual(_cloud_status(_ai_config(self.session)), "connected")
        with patch.object(settings, "SessionLocal", self.factory):
            status = settings.get_ai_status(None)
        self.assertEqual(status["state"], "connected")
        self.assertEqual(status["provider"], "opencode-zen")
        self.assertTrue(status["lastTestAt"])

    def test_saved_unvalidated_draft_is_not_connected(self):
        self.save(validated=False)
        self.assertEqual(
            saved_test_status(self.session, self.values()), ("untested", "")
        )
        self.assertEqual(_cloud_status(_ai_config(self.session)), "configured")

    def test_worker_records_zen_provenance_even_for_nemotron(self):
        # Extract this pure helper without importing or starting the async worker.
        worker = (
            Path(__file__).resolve().parents[2] / "worker/src/berrybrain_worker/main.py"
        )
        tree = ast.parse(worker.read_text())
        helper = next(
            node
            for node in tree.body
            if isinstance(node, ast.FunctionDef)
            and node.name == "effective_generation_provider"
        )
        namespace = {
            "_ai_config": {
                "provider": "cloud",
                "remote_content_consent": "true",
                "cloud_api_url": "https://opencode.ai/zen/v1/",
                "cloud_model": "nemotron-3-super-free",
            }
        }
        exec(
            compile(ast.Module(body=[helper], type_ignores=[]), str(worker), "exec"),
            namespace,
        )
        self.assertEqual(namespace["effective_generation_provider"](), "opencode-zen")
        namespace["_ai_config"]["remote_content_consent"] = "false"
        self.assertEqual(namespace["effective_generation_provider"](), "unconfigured")

    def test_changed_key_revision_invalidates_saved_validation(self):
        self.save()
        set_setting(self.session, "ai_key_revision", "rotated")
        self.session.commit()
        self.assertEqual(saved_test_status(self.session, self.values())[0], "untested")

    def test_changed_model_invalidates_home_and_settings_consistently(self):
        self.save()
        set_setting(self.session, "ai_model", "other-model")
        self.session.commit()
        self.assertEqual(_cloud_status(_ai_config(self.session)), "configured")
        with patch.object(settings, "SessionLocal", self.factory):
            self.assertEqual(settings.get_ai_status(None)["state"], "configured")

    def test_changed_endpoint_is_not_connected(self):
        self.save()
        set_setting(self.session, "ai_api_url", "https://other.example/v1")
        self.session.commit()
        self.assertEqual(saved_test_status(self.session, self.values())[0], "untested")

    def test_privacy_disabled_is_not_reported_connected(self):
        self.save()
        set_setting(self.session, "remote_content_consent", "false")
        self.session.commit()
        self.assertEqual(_cloud_status(_ai_config(self.session)), "disabled")

    def record_legacy(self, saved, status, minutes):
        values = self.values()
        for key, value in {
            "ai_last_test_url": self.configuration().endpoint_url,
            "ai_last_test_model": "big-pickle",
            "ai_last_test_key_revision": values["ai_key_revision"],
            "ai_last_test_method": "chat_completions",
            "ai_last_test_status": status,
            "ai_last_test_at": (
                saved.validated_at + timedelta(minutes=minutes)
            ).isoformat(),
        }.items():
            set_setting(self.session, key, value)
        self.session.commit()

    def test_newer_failed_test_is_not_hidden_by_v2_validation(self):
        saved = self.save()
        self.record_legacy(saved, "failed", 1)
        self.assertEqual(saved_test_status(self.session, self.values())[0], "failed")

    def test_older_failed_test_does_not_override_new_validation(self):
        saved = self.save()
        self.record_legacy(saved, "failed", -1)
        self.assertEqual(saved_test_status(self.session, self.values())[0], "connected")

    def test_legacy_model_mismatch_no_longer_marks_home_connected(self):
        saved = self.save()
        self.record_legacy(saved, "connected", 1)
        set_setting(self.session, "ai_model", "other-model")
        self.session.commit()
        self.assertEqual(saved_test_status(self.session, self.values())[0], "untested")

    def test_zen_catalog_has_chat_but_not_embedding_capability(self):
        zen = next(x for x in provider_catalog() if x["id"] == "opencode-zen")
        self.assertEqual(zen["url"], "https://opencode.ai/zen/v1")
        self.assertIn("chat", zen["capabilities"])
        self.assertNotIn("embeddings", zen["capabilities"])

    def test_zen_cannot_be_selected_for_embedding(self):
        payload = self.configuration().model_dump()
        payload["embedding"] = {"provider_id": "opencode-zen", "model_id": "big-pickle"}
        with self.assertRaisesRegex(ValidationError, "choose another cloud"):
            AIConfiguration.model_validate(payload)

    def test_zen_filters_other_wire_protocols_from_catalog(self):
        response = MagicMock()
        response.status = 200
        response.read.return_value = json.dumps(
            {
                "data": [
                    {"id": name}
                    for name in [
                        "big-pickle",
                        "glm-5",
                        "claude-opus-4-6",
                        "gpt-5",
                        "gemini-3-flash",
                        "muse-spark-1.3",
                        "qwen3.7-plus",
                        "ling-3.0-flash-fin-free",
                    ]
                ]
            }
        ).encode()
        response.__enter__.return_value = response
        with patch.object(
            routes.urllib.request, "urlopen", return_value=response
        ) as request:
            result = routes._fetch_models(
                "opencode-zen", "https://opencode.ai/zen/v1", "fixture-key"
            )
        self.assertEqual(result, ["big-pickle", "glm-5", "ling-3.0-flash-fin-free"])
        self.assertEqual(
            request.call_args.args[0].full_url, "https://opencode.ai/zen/v1/models"
        )
        self.assertEqual(
            request.call_args.args[0].get_header("User-agent"), "BerryBrain/1.4.8"
        )

    def test_zen_setup_probe_identifies_client(self):
        response = MagicMock()
        response.__enter__.return_value = response
        response.read.return_value = b'{"choices":[{"message":{"content":"OK"}}]}'
        with patch.object(
            routes.urllib.request, "urlopen", return_value=response
        ) as request:
            routes._probe_model_capability(
                provider_id="opencode-zen",
                endpoint="https://opencode.ai/zen/v1",
                api_key="fixture-key",
                model="big-pickle",
                capability="chat",
            )
        self.assertEqual(
            request.call_args.args[0].get_header("User-agent"), "BerryBrain/1.4.8"
        )

    def test_cloud_judge_gateway_identifies_client(self):
        from berrybrain_api.ai_gateway import _cloud_json

        response = MagicMock()
        response.__enter__.return_value = response
        response.read.return_value = (
            b'{"choices":[{"message":{"content":"{\\"probe\\":true}"}}]}'
        )
        with patch.object(
            routes.urllib.request, "urlopen", return_value=response
        ) as request:
            result = _cloud_json(
                {
                    "cloud_api_url": "https://opencode.ai/zen/v1",
                    "cloud_api_key": "fixture-key",
                    "cloud_model": "big-pickle",
                },
                "probe",
                "probe",
                1,
                1,
            )
        self.assertTrue(result["probe"])
        self.assertEqual(
            request.call_args.args[0].get_header("User-agent"), "BerryBrain/1.4.8"
        )

    def test_catalog_error_reports_status_without_exposing_response_or_key(self):
        for code in (401, 403, 429, 500):
            error = routes.urllib.error.HTTPError(
                "https://example.invalid/secret",
                code,
                "secret-response",
                {},
                None,
            )
            message = routes._model_catalog_error(error)
            self.assertIn(f"HTTP {code}", message)
            self.assertNotIn("secret", message)

    def test_capability_error_preserves_reason_but_redacts_credentials(self):
        payload = {
            "error": {"message": "Invalid API key fixture-key for test@example.com"}
        }
        error = routes.urllib.error.HTTPError(
            "https://example.invalid",
            400,
            "bad",
            {},
            io.BytesIO(json.dumps(payload).encode()),
        )
        with patch.object(routes.urllib.request, "urlopen", side_effect=error):
            result = routes._probe_model_capability(
                provider_id="opencode-zen",
                endpoint="https://opencode.ai/zen/v1",
                api_key="fixture-key",
                model="nemotron-3-ultra-free",
                capability="chat",
            )
        self.assertFalse(result["available"])
        self.assertEqual(result["status"], 400)
        self.assertIn("Invalid API key", result["reason"])
        self.assertNotIn("fixture-key", result["reason"])
        self.assertNotIn("test@example.com", result["reason"])
        self.assertNotIn("does not support", result["reason"])

    def test_capability_error_discards_html_and_limits_message(self):
        for body in (b"<html>secret</html>", b"null", b"[]"):
            error = routes.urllib.error.HTTPError(
                "https://example.invalid", 400, "bad", {}, io.BytesIO(body)
            )
            self.assertEqual(
                routes._capability_http_error(error, ""),
                "Provider rejected the validation request (HTTP 400).",
            )
        body = json.dumps({"message": "x" * 5000}).encode()
        error = routes.urllib.error.HTTPError(
            "https://example.invalid", 400, "bad", {}, io.BytesIO(body)
        )
        self.assertLess(len(routes._capability_http_error(error, "")), 500)

    def test_zen_unsupported_probe_fails_before_network(self):
        for model, capability in [("gpt-5", "chat"), ("big-pickle", "embeddings")]:
            result = routes._probe_model_capability(
                provider_id="opencode-zen",
                endpoint="https://opencode.ai/zen/v1",
                api_key="fixture-key",
                model=model,
                capability=capability,
            )
            self.assertFalse(result["available"])

    def test_committee_valid_distinct_models_save(self):
        self.save()
        result = self.mode(self.slots())
        self.assertEqual(result["mode"], "committee")
        self.assertEqual(len(result["committee"]), 3)

    def test_committee_trims_names(self):
        self.save()
        slots = self.slots()
        slots[0]["model"] = "  glm-5  "
        self.assertEqual(self.mode(slots)["committee"][0]["model"], "glm-5")

    def test_committee_reports_duplicate_generator_missing_and_stale_provider(self):
        self.save()
        cases = [
            ("duplicate", lambda x: x[1].update(model="GLM-5")),
            ("generator", lambda x: x[1].update(model=" BIG-PICKLE ")),
            ("choose a model", lambda x: x[1].update(model="")),
            ("active provider", lambda x: x[1].update(provider="old-provider")),
        ]
        for expected, mutate in cases:
            with self.subTest(expected=expected):
                slots = self.slots()
                mutate(slots)
                result = self.mode(slots)
                self.assertEqual(result["status"], "error")
                self.assertIn(expected, result["message"])
                self.assertIn("Judge 2", result["message"])

    def test_committee_duplicate_slot_id_is_rejected(self):
        self.save()
        slots = self.slots()
        slots[1]["slot"] = slots[0]["slot"]
        self.assertEqual(len(eligible_committee_slots(slots)), 2)
        self.assertIn("duplicate slot", self.mode(slots)["message"])

    def test_committee_missing_slots_explains_requested_count(self):
        self.save()
        self.assertIn("Judge 3: choose a model", self.mode(self.slots()[:2])["message"])
        self.assertEqual(self.mode(self.slots()[:2], size=2)["mode"], "committee")

    def test_defaults_uses_saved_generator_not_stale_browser_value(self):
        self.save()
        with (
            patch.object(judge, "SessionLocal", self.factory),
            patch.object(
                routes,
                "_fetch_models",
                return_value=["big-pickle", "glm-5", "kimi-k2.5"],
            ),
            patch.object(
                routes,
                "_probe_judge_models",
                side_effect=lambda *args, **kwargs: args[3],
            ) as probe,
        ):
            result = judge.get_judge_defaults(
                judge.JudgeDefaultsRequest(
                    provider="opencode-zen",
                    models=[],
                    generator_model="stale-browser-value",
                    primary_judge_model="stale-primary",
                    committee_size=2,
                )
            )
        self.assertNotIn("big-pickle", probe.call_args.args[3])
        self.assertTrue(result["ready"])


if __name__ == "__main__":
    unittest.main(verbosity=1)
