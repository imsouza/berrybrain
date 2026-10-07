"""Product regressions for 1.4.9; temporary SQLite, no providers or benchmarks."""

import json
import unittest
from collections import Counter
from datetime import timedelta
from unittest.mock import patch

from sqlalchemy import create_engine, event, inspect, select, text
from sqlalchemy.orm import sessionmaker

from berrybrain_api.assimilation import note_assimilation_map
from berrybrain_api.database import Base
from berrybrain_api.home_summary import build_home_summary
from berrybrain_api.job_summary import (
    HISTORY_SAMPLE_PER_TYPE,
    home_job_snapshot,
    recent_duration_samples,
)
from berrybrain_api.jobs import utc_now
from berrybrain_api.models import JobAttemptRecord, JobRecord, NoteRecord
from berrybrain_api.routers.jobs import jobs_health_endpoint
from berrybrain_api.schema_migrations import apply_schema_migrations, downgrade_schema


class ReleaseJobDiagnosticsTest(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.sessions = sessionmaker(bind=self.engine)
        self.session = self.sessions()
        self.now = utc_now()

    def tearDown(self):
        self.session.close()
        self.engine.dispose()

    def job(self, status="completed", **fields):
        defaults = {
            "type": "GENERATE_EMBEDDING",
            "status": status,
            "created_at": self.now - timedelta(minutes=2),
        }
        defaults.update(fields)
        job = JobRecord(**defaults)
        self.session.add(job)
        return job

    def health(self):
        self.session.commit()
        with patch("berrybrain_api.routers.jobs.SessionLocal", self.sessions):
            return jobs_health_endpoint()

    def test_home_counts_entire_history_but_loads_bounded_payloads(self):
        for _ in range(HISTORY_SAMPLE_PER_TYPE + 15):
            self.job(started_at=self.now - timedelta(seconds=10), completed_at=self.now)
        for _ in range(12):
            self.job("pending")
        self.job("dead_letter")
        self.job("failed")
        self.job("cancel_requested", started_at=self.now)
        self.session.commit()
        statements = []

        def capture(_conn, _cursor, statement, _params, _context, _many):
            statements.append(statement)

        event.listen(self.engine, "before_cursor_execute", capture)
        summary = build_home_summary(self.session)
        self.assertEqual(summary["progress"]["completed"], HISTORY_SAMPLE_PER_TYPE + 15)
        self.assertEqual(
            summary["stats"]["jobs"]["completedToday"], HISTORY_SAMPLE_PER_TYPE + 15
        )
        self.assertEqual(summary["progress"]["pending"], 12)
        self.assertEqual(summary["progress"]["active"], 1)
        self.assertEqual(summary["progress"]["failed"], 2)
        self.assertEqual(summary["legacyStats"]["failedJobs"], 2)
        self.assertEqual(
            summary["stats"]["jobs"]["total"], HISTORY_SAMPLE_PER_TYPE + 30
        )
        self.assertEqual(len(summary["recentlyCompleted"]), 8)
        # No historical SELECT of raw payloads without a limit. Running rows
        # are intentionally current and needed for elapsed-time estimates.
        payload_selects = [s for s in statements if "jobs.payload," in s]
        self.assertEqual(len(payload_selects), 3)
        self.assertEqual(sum("LIMIT" in s for s in payload_selects), 2)
        self.assertTrue(all("WHERE jobs.status" in s for s in payload_selects))
        self.assertTrue(
            any(item["title"] == "2 jobs failed" for item in summary["needsAttention"])
        )

    def test_duration_sample_is_bounded_per_type_without_changing_totals(self):
        for index in range(HISTORY_SAMPLE_PER_TYPE + 20):
            end = self.now - timedelta(minutes=index)
            self.job(started_at=end - timedelta(seconds=10), completed_at=end)
        self.session.commit()
        samples = recent_duration_samples(self.session, Counter(GENERATE_EMBEDDING=1))
        self.assertEqual(len(samples), HISTORY_SAMPLE_PER_TYPE)
        self.assertFalse(hasattr(samples[0], "payload"))
        snapshot = home_job_snapshot(self.session, self.now)
        self.assertEqual(
            snapshot.status_counts["completed"], HISTORY_SAMPLE_PER_TYPE + 20
        )

    def test_long_running_job_with_renewed_lease_is_not_stale(self):
        self.job(
            "running",
            started_at=self.now - timedelta(hours=2),
            lease_expires_at=self.now + timedelta(minutes=10),
        )
        result = self.health()
        self.assertEqual(result["status"], "processing")
        self.assertEqual(result["staleRunning"], [])
        self.assertEqual(result["slo"]["status"], "healthy")

    def test_expired_lease_is_stale_even_with_recent_start(self):
        self.job(
            "running",
            started_at=self.now - timedelta(minutes=2),
            lease_expires_at=self.now - timedelta(seconds=1),
        )
        result = self.health()
        self.assertEqual(result["status"], "degraded")
        self.assertEqual(result["slo"]["staleRunning"], 1)

    def test_legacy_start_time_is_used_only_without_lease(self):
        self.job("running", started_at=self.now - timedelta(hours=1))
        self.assertEqual(self.health()["slo"]["staleRunning"], 1)

    def test_cancel_requested_remains_active_until_acknowledged(self):
        self.job(
            "cancel_requested",
            started_at=self.now,
            lease_expires_at=self.now + timedelta(minutes=10),
        )
        result = self.health()
        self.assertEqual(result["counts"]["running"], 1)
        self.assertEqual(result["counts"]["cancel_requested"], 1)
        self.assertEqual(result["canonicalCounts"]["active"], 1)
        self.assertEqual(result["status"], "processing")

    def test_overdue_pending_job_breaches_the_declared_slo(self):
        self.job("pending", created_at=self.now - timedelta(hours=1))
        result = self.health()
        self.assertEqual(result["slo"]["status"], "breached")
        self.assertGreaterEqual(result["slo"]["oldestPendingAgeSeconds"], 3600)
        self.assertEqual(result["status"], "degraded")

    def test_assimilation_uses_stable_note_identity_and_current_hash(self):
        note = NoteRecord(
            title="Moved",
            slug="moved",
            path="new/moved.md",
            content="Current note",
            content_hash="current",
        )
        self.session.add(note)
        self.session.flush()
        job = self.job(
            note_id=note.id,
            note_path="old/moved.md",
            content_hash="current",
            payload=json.dumps(
                {"note_path": "old/moved.md", "content_hash": "current"}
            ),
        )
        self.session.commit()
        self.assertTrue(
            note_assimilation_map(self.session, [note])[note.id]["assimilated"]
        )
        self.assertTrue(
            note_assimilation_map(self.session, [note], [job])[note.id]["assimilated"]
        )
        job.content_hash = "stale"
        self.session.commit()
        self.assertFalse(
            note_assimilation_map(self.session, [note])[note.id]["assimilated"]
        )

    def test_legacy_assimilation_checks_hash_and_ignores_malformed_payload(self):
        note = NoteRecord(
            title="Legacy",
            slug="legacy",
            path="legacy.md",
            content="Current note",
            content_hash="current",
        )
        self.session.add(note)
        self.job(payload="broken json")
        job = self.job(
            payload=json.dumps({"note_path": "legacy.md", "content_hash": "stale"})
        )
        self.session.commit()
        self.assertFalse(
            note_assimilation_map(self.session, [note])[note.id]["assimilated"]
        )
        job.payload = json.dumps({"note_path": "legacy.md", "content_hash": "current"})
        self.session.commit()
        self.assertTrue(
            note_assimilation_map(self.session, [note])[note.id]["assimilated"]
        )
        # Partial migration must not hide a stale hash still stored in JSON.
        job.note_id = note.id
        job.payload = json.dumps({"content_hash": "stale"})
        self.session.commit()
        self.assertFalse(
            note_assimilation_map(self.session, [note])[note.id]["assimilated"]
        )

    def test_v14_adds_covering_indexes_without_changing_history(self):
        job = self.job()
        self.session.flush()
        self.session.add(
            JobAttemptRecord(job_id=job.id, job_type=job.type, error_code="timeout")
        )
        self.session.commit()
        apply_schema_migrations(self.engine)
        downgrade_schema(self.engine, 13)
        names = [
            "ix_jobs_status_type_completed",
            "ix_jobs_status_completed",
            "ix_jobs_status_created",
            "ix_job_attempts_error_code",
            "ix_job_attempts_model_call_started",
        ]
        with self.engine.begin() as connection:
            for name in names:
                connection.execute(text(f"DROP INDEX {name}"))
        result = apply_schema_migrations(self.engine)
        self.assertEqual(result["fromVersion"], 13)
        self.assertEqual(result["toVersion"], 14)
        indexes = {
            item["name"]
            for table in ("jobs", "job_attempts")
            for item in inspect(self.engine).get_indexes(table)
        }
        self.assertTrue(set(names) <= indexes)
        self.assertEqual(len(self.session.scalars(select(JobRecord)).all()), 1)
        self.assertEqual(len(self.session.scalars(select(JobAttemptRecord)).all()), 1)
        with self.engine.connect() as connection:
            plan = connection.execute(
                text(
                    "EXPLAIN QUERY PLAN SELECT count(id) FROM job_attempts WHERE error_code != ''"
                )
            ).all()
        self.assertTrue(
            any("COVERING INDEX ix_job_attempts_error_code" in str(row) for row in plan)
        )
        self.assertEqual(apply_schema_migrations(self.engine)["applied"], [])
