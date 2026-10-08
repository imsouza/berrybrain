"""Product-only regressions: isolated SQLite, no providers or research tests."""

import json
import unittest
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import patch

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from berrybrain_api.automation_logs import (
    list_automation_logs,
    serialize_automation_log,
)
from berrybrain_api.database import Base
from berrybrain_api.model_invocation_service import (
    finish_model_invocation,
    start_model_invocation,
)
from berrybrain_api.models import (
    AutomationLogRecord,
    JobRecord,
    ModelInvocationRecord,
    NotificationRecord,
)
from berrybrain_api.provider_alerts import model_availability_alerts
from berrybrain_api.routers import automation, jobs


class ActivityObservabilityTest(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.sessions = sessionmaker(bind=self.engine)
        self.session = self.sessions()

    def tearDown(self):
        self.session.close()
        self.engine.dispose()

    def test_compact_log_does_not_read_snapshots_or_sort_history(self):
        for index in range(8):
            self.session.add(
                AutomationLogRecord(
                    action_type="test",
                    target_type="system",
                    target_id=str(index),
                    before_state=json.dumps({"private": "x" * 10000}),
                    after_state="{}",
                    description="Authorization: Bearer secret-test-token",
                )
            )
        self.session.commit()
        statements = []
        event.listen(
            self.engine,
            "before_cursor_execute",
            lambda c, u, s, p, x, m: statements.append(s),
        )
        rows = list_automation_logs(self.session, 3, compact=True)
        payload = [serialize_automation_log(row, compact=True) for row in rows]
        self.assertEqual([row["id"] for row in payload], [8, 7, 6])
        self.assertNotIn("before_state", payload[0])
        self.assertNotIn("secret-test-token", json.dumps(payload))
        self.assertEqual(len(statements), 1)
        self.assertNotIn("automation_logs.before_state", statements[0])
        self.assertNotIn("ORDER BY automation_logs.created_at", statements[0])
        older = list_automation_logs(self.session, 3, before_id=6, compact=True)
        self.assertEqual([row.id for row in older], [5, 4, 3])

    def test_export_excludes_note_snapshots_and_has_download_headers(self):
        self.session.add(
            AutomationLogRecord(
                action_type="edit",
                target_type="note",
                target_id="1",
                before_state='{"note": "PRIVATE NOTE"}',
                after_state="{}",
            )
        )
        self.session.commit()
        with patch.object(automation, "SessionLocal", self.sessions):
            response = automation.export_logs(limit=10)
        self.assertNotIn("PRIVATE NOTE", bytes(response.body).decode())
        self.assertIn("attachment", response.headers["Content-Disposition"])
        self.assertEqual(response.headers["Cache-Control"], "no-store")

    def test_old_failures_visible_beyond_latest_successful_jobs(self):
        self.session.add_all(
            [
                JobRecord(type="TEST", status="dead_letter"),
                JobRecord(type="TEST", status="failed"),
            ]
        )
        self.session.add_all(
            JobRecord(type="TEST", status="completed") for _ in range(60)
        )
        self.session.commit()
        with patch.object(jobs, "SessionLocal", self.sessions):
            first = jobs.list_jobs_endpoint(
                status="failed", limit=1, include_dead_letter=True, include_counts=True
            )
            second = jobs.list_jobs_endpoint(
                status="failed",
                limit=1,
                include_dead_letter=True,
                before_id=first["nextCursor"],
            )
        self.assertEqual(first["counts"]["failed"], 2)
        self.assertEqual(first["counts"]["total"], 62)
        self.assertEqual(first["jobs"][0]["status"], "failed")
        self.assertEqual(second["jobs"][0]["status"], "dead_letter")
        self.assertIsNone(second["nextCursor"])

    def test_availability_alert_clears_after_recovery_and_ignores_rate_limit(self):
        slot = SimpleNamespace(
            provider_id="nvidia_nim", model_id="vendor/model", enabled=True
        )
        config = SimpleNamespace(
            main=slot,
            embedding=slot,
            judge=slot,
            hipporag=slot,
            validated_at=None,
            mode="cloud",
        )

        def record(status, message=""):
            self.session.add(
                ModelInvocationRecord(
                    capability="generation",
                    provider="cloud",
                    model="vendor/model",
                    status=status,
                    error_message=message,
                )
            )
            self.session.commit()

        with patch(
            "berrybrain_api.provider_alerts.load_configuration", return_value=config
        ):
            record("failed", "HTTP 404 model not found")
            self.assertEqual(len(model_availability_alerts(self.session)), 1)
            record("completed")
            self.assertEqual(model_availability_alerts(self.session), [])
            record("failed", "HTTP 429 rate limit")
            self.assertEqual(model_availability_alerts(self.session), [])
            record("failed", "model no longer available")
            config.validated_at = datetime.now(UTC) + timedelta(seconds=1)
            self.assertEqual(model_availability_alerts(self.session), [])

    def test_unavailable_model_notification_is_deduplicated_per_model(self):
        for model in ("model-a", "model-a", "model-b"):
            handle = start_model_invocation(
                self.session,
                capability="chat",
                provider="cloud",
                model=model,
                prompt_version="test",
                remote=True,
                input_units=1,
            )
            finish_model_invocation(
                handle,
                status="failed",
                latency_ms=1,
                error=RuntimeError("HTTP 404 model not found"),
            )
        self.assertEqual(self.session.query(NotificationRecord).count(), 2)
        self.assertEqual(
            self.session.query(ModelInvocationRecord)
            .filter_by(status="failed")
            .count(),
            3,
        )

    def test_notification_failure_does_not_lose_invocation_completion(self):
        handle = start_model_invocation(
            self.session,
            capability="chat",
            provider="cloud",
            model="model-a",
            prompt_version="test",
            remote=True,
            input_units=1,
        )
        with patch(
            "berrybrain_api.notification_service.create_notification",
            side_effect=RuntimeError("notification failed"),
        ):
            finish_model_invocation(
                handle,
                status="failed",
                latency_ms=1,
                error=RuntimeError("HTTP 404 model not found"),
            )
        self.assertEqual(
            self.session.query(ModelInvocationRecord).one().status, "failed"
        )


if __name__ == "__main__":
    unittest.main()
