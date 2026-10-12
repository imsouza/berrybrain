import json
import unittest
from datetime import timedelta
from unittest.mock import patch

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from berrybrain_api.database import Base
from berrybrain_api.job_recovery import (
    STATE_KEY,
    recover_exhausted_jobs,
    transient_failure,
)
from berrybrain_api.jobs import recover_stale_running_jobs, utc_now
from berrybrain_api.models import (
    AutomationLogRecord,
    GraphNodeRecord,
    JobAttemptRecord,
    JobRecord,
    NoteRecord,
    SettingRecord,
)


class AutonomousRecoveryTest(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.session = sessionmaker(bind=self.engine)()

    def tearDown(self):
        self.session.close()
        self.engine.dispose()

    def job(self, **values):
        params = dict(
            type="UPDATE_GRAPH_STATS",
            status="dead_letter",
            attempts=2,
            max_attempts=2,
            payload="{}",
            error_message="Stale running job exhausted attempts",
            completed_at=utc_now() - timedelta(hours=5),
        )
        params.update(values)
        job = JobRecord(**params)
        self.session.add(job)
        self.session.commit()
        return job

    def test_retry_preserves_identity_attempts_and_error(self):
        job = self.job()
        result = recover_exhausted_jobs(self.session)
        self.assertEqual(result["recovered"], 1)
        self.assertEqual(
            (job.status, job.attempts, job.max_attempts), ("pending", 2, 3)
        )
        self.assertIn("Stale", job.error_message)
        self.assertEqual(json.loads(job.payload)["_automatic_recovery"]["count"], 1)
        self.assertEqual(
            len(list(self.session.scalars(select(AutomationLogRecord)))), 1
        )

    def test_expired_lease_closes_attempt_without_claiming_success(self):
        job = self.job(
            status="running",
            started_at=utc_now() - timedelta(hours=1),
            completed_at=None,
        )
        attempt = JobAttemptRecord(
            job_id=job.id,
            job_type=job.type,
            attempt=2,
            stage="context_loading",
            started_at=job.started_at,
        )
        self.session.add(attempt)
        self.session.commit()
        self.assertEqual(recover_stale_running_jobs(self.session), 1)
        self.assertEqual(job.status, "dead_letter")
        self.assertIsNotNone(attempt.finished_at)
        self.assertEqual(attempt.error_code, "lease_expired")
        self.assertEqual(attempt.stage, "context_loading")

    def test_cooldown_and_durable_scan_limit(self):
        job = self.job(completed_at=utc_now())
        self.assertEqual(recover_exhausted_jobs(self.session)["recovered"], 0)
        job.completed_at = utc_now() - timedelta(hours=1)
        self.session.commit()
        self.assertEqual(recover_exhausted_jobs(self.session)["recovered"], 0)

    def test_another_session_observes_global_admission_cooldown(self):
        self.job()
        other = self.job(type="UPDATE_GRAPH_CLUSTERS")
        start = utc_now()
        with patch("berrybrain_api.job_recovery.utc_now", return_value=start):
            self.assertEqual(recover_exhausted_jobs(self.session)["recovered"], 1)
        with (
            sessionmaker(bind=self.engine)() as second,
            patch(
                "berrybrain_api.job_recovery.utc_now",
                return_value=start + timedelta(minutes=2),
            ),
        ):
            self.assertEqual(recover_exhausted_jobs(second)["recovered"], 0)
        self.session.refresh(other)
        self.assertEqual(other.status, "pending")

    def test_three_recovery_cycles_are_a_hard_limit(self):
        job = self.job()
        start = utc_now()
        for index in range(4):
            with patch(
                "berrybrain_api.job_recovery.utc_now",
                return_value=start + timedelta(hours=index * 4),
            ):
                result = recover_exhausted_jobs(self.session)
            self.assertEqual(result["recovered"], int(index < 3))
            if index < 3:
                job.attempts += 1
                job.status = "dead_letter"
                job.completed_at = start + timedelta(hours=index * 4)
                self.session.commit()
        self.assertEqual(job.attempts, 5)

    def test_old_stats_are_superseded_not_completed_or_replayed(self):
        old = self.job()
        self.job(status="completed")
        result = recover_exhausted_jobs(self.session)
        self.assertEqual(result, {"recovered": 0, "superseded": 1})
        self.assertEqual(old.status, "superseded")
        self.assertIn("Stale", old.error_message)

    def test_permanent_errors_never_recover(self):
        job = self.job(error_message="HTTP 401 invalid API key after timeout")
        self.assertEqual(recover_exhausted_jobs(self.session)["recovered"], 0)
        self.assertEqual(job.status, "dead_letter")

    def test_partial_stats_do_not_cover_global_failure(self):
        old = self.job()
        self.job(status="completed", payload='{"affected_node_ids":[3]}')
        self.assertEqual(
            recover_exhausted_jobs(self.session), {"recovered": 1, "superseded": 0}
        )
        self.assertEqual(old.status, "pending")

    def test_periodic_stats_keys_do_not_prevent_scope_supersession(self):
        old = self.job(payload='{"idempotency_key":"stats:old","trigger":"periodic"}')
        self.job(
            status="completed",
            payload='{"idempotency_key":"stats:new","trigger":"periodic"}',
        )
        self.assertEqual(
            recover_exhausted_jobs(self.session), {"recovered": 0, "superseded": 1}
        )
        self.assertEqual(old.status, "superseded")

    def test_superset_stats_cover_partial_failure(self):
        old = self.job(payload='{"scope_node_ids":[3]}')
        self.job(status="completed", payload='{"affected_node_ids":[3,4]}')
        self.assertEqual(recover_exhausted_jobs(self.session)["superseded"], 1)
        self.assertEqual(old.status, "superseded")

    def test_legacy_note_stats_do_not_cover_global_failure(self):
        old = self.job()
        self.job(status="completed", payload='{"note_path":"a.md"}')
        self.assertEqual(recover_exhausted_jobs(self.session)["superseded"], 0)
        self.assertEqual(old.status, "pending")

    def test_pending_stats_do_not_hide_an_unresolved_failure(self):
        old = self.job()
        self.job(status="pending")
        recover_exhausted_jobs(self.session)
        self.assertEqual(old.status, "dead_letter")

    def test_structured_permanent_class_prevents_recovery(self):
        job = self.job()
        self.session.add(
            JobAttemptRecord(
                job_id=job.id, job_type=job.type, error_class="permanent_job_error"
            )
        )
        self.session.commit()
        self.assertEqual(recover_exhausted_jobs(self.session)["recovered"], 0)

    def test_judge_uses_timestamp_version_not_graph_revision(self):
        node = GraphNodeRecord(type="concept", label="Current concept")
        self.session.add(node)
        self.session.commit()
        job = self.job(
            type="JUDGE_ARTIFACT",
            payload=json.dumps(
                {
                    "artifact_type": "node",
                    "artifact_id": node.id,
                    "artifact_version": str(
                        node.updated_at.replace(tzinfo=utc_now().tzinfo).timestamp()
                    ),
                    "judge_config_version": "configuration-required",
                }
            ),
        )
        with patch(
            "berrybrain_api.ai_configuration.load_configuration", return_value=None
        ):
            result = recover_exhausted_jobs(self.session)
        self.assertEqual(result, {"recovered": 1, "superseded": 0})
        self.assertEqual(job.status, "pending")

    def test_changed_judge_artifact_is_superseded(self):
        node = GraphNodeRecord(type="concept", label="Changed concept")
        self.session.add(node)
        self.session.commit()
        job = self.job(
            type="JUDGE_ARTIFACT",
            payload=json.dumps(
                {
                    "artifact_type": "node",
                    "artifact_id": node.id,
                    "artifact_version": "1",
                    "judge_config_version": "configuration-required",
                }
            ),
        )
        self.assertEqual(recover_exhausted_jobs(self.session)["superseded"], 1)
        self.assertEqual(job.status, "superseded")

    def test_queue_pressure_defers_recovery(self):
        old = self.job()
        for _ in range(4):
            self.job(status="pending", type="PARSE_NOTE")
        self.assertEqual(recover_exhausted_jobs(self.session)["recovered"], 0)
        self.assertEqual(old.status, "dead_letter")

    def test_cancelled_and_unsafe_jobs_are_not_recovered(self):
        self.job(status="cancelled")
        unsafe = self.job(type="CREATE_NOTE_FROM_INSIGHT", payload='{"insight_id":1}')
        self.assertEqual(recover_exhausted_jobs(self.session)["recovered"], 0)
        self.assertEqual(unsafe.status, "dead_letter")

    def test_missing_source_is_superseded(self):
        job = self.job(
            type="EXPAND_KNOWLEDGE_GRAPH",
            payload='{"note_path":"gone.md","content_hash":"old"}',
        )
        recover_exhausted_jobs(self.session)
        self.assertEqual(job.status, "superseded")

    def test_changed_source_is_not_replayed(self):
        note = NoteRecord(path="a.md", title="A", slug="a", content_hash="new")
        self.session.add(note)
        self.session.commit()
        job = self.job(
            type="EXPAND_KNOWLEDGE_GRAPH",
            note_id=note.id,
            payload=json.dumps(
                {"note_id": note.id, "note_path": "a.md", "content_hash": "old"}
            ),
        )
        recover_exhausted_jobs(self.session)
        self.assertEqual(job.status, "superseded")

    def test_unversioned_source_requires_manual_review(self):
        self.session.add(
            NoteRecord(path="a.md", title="A", slug="a", content_hash="current")
        )
        self.session.commit()
        job = self.job(type="EXPAND_KNOWLEDGE_GRAPH", payload='{"note_path":"a.md"}')
        recover_exhausted_jobs(self.session)
        self.assertEqual(job.status, "dead_letter")

    def test_one_retry_per_cycle_and_queue_pressure(self):
        jobs = [
            self.job(type=kind)
            for kind in ["UPDATE_GRAPH_STATS", "UPDATE_GRAPH_CLUSTERS"]
        ]
        self.assertEqual(recover_exhausted_jobs(self.session)["recovered"], 1)
        self.assertEqual(sum(job.status == "pending" for job in jobs), 1)

    def test_full_scan_rotates_past_permanent_failures(self):
        target = self.job()
        for _ in range(50):
            self.job(type="UNKNOWN")
        now = utc_now()
        with patch("berrybrain_api.job_recovery.utc_now", return_value=now):
            self.assertEqual(recover_exhausted_jobs(self.session)["recovered"], 0)
        with patch(
            "berrybrain_api.job_recovery.utc_now",
            return_value=now + timedelta(minutes=2),
        ):
            self.assertEqual(recover_exhausted_jobs(self.session)["recovered"], 1)
        self.assertEqual(target.status, "pending")

    def test_disabled_supervisor_has_no_effect(self):
        self.session.add(
            SettingRecord(key="automatic_job_recovery_enabled", value="false")
        )
        self.session.commit()
        job = self.job()
        self.assertEqual(recover_exhausted_jobs(self.session)["recovered"], 0)
        self.assertEqual(job.status, "dead_letter")
        self.assertIsNone(
            self.session.scalar(
                select(SettingRecord).where(SettingRecord.key == STATE_KEY)
            )
        )

    def test_unknown_failure_is_not_assumed_transient(self):
        self.assertFalse(transient_failure("Unexpected internal error"))
        self.assertTrue(transient_failure("Service returned HTTP 503"))


if __name__ == "__main__":
    unittest.main()
