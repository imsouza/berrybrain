import importlib.util
import unittest
from datetime import timedelta
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from berrybrain_api.database import Base
from berrybrain_api.jobs import utc_now
from berrybrain_api.models import AutomationLogRecord, JobAttemptRecord, JobRecord

spec = importlib.util.spec_from_file_location(
    "reconcile_exhausted_jobs",
    Path(__file__).resolve().parents[3] / "scripts" / "reconcile-exhausted-jobs.py",
)
maintenance = importlib.util.module_from_spec(spec)
spec.loader.exec_module(maintenance)


class ExhaustedJobReconciliationTest(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.session = Session(self.engine)
        self.job = JobRecord(
            type="JUDGE_ARTIFACT",
            status="pending",
            attempts=2,
            max_attempts=2,
            error_message="Preserved old diagnostic",
        )
        self.session.add(self.job)
        self.session.commit()

    def tearDown(self):
        self.session.close()
        self.engine.dispose()

    def test_dry_run_does_not_write(self):
        result = maintenance.reconcile_job(self.session, self.job.id)
        self.assertTrue(result["eligible"])
        self.assertFalse(result["applied"])
        self.session.refresh(self.job)
        self.assertEqual(self.job.status, "pending")
        self.assertEqual(self.session.scalars(select(AutomationLogRecord)).all(), [])

    def test_apply_preserves_history_and_audits_once_without_new_attempt(self):
        self.session.add(
            JobAttemptRecord(
                job_id=self.job.id,
                job_type=self.job.type,
                attempt=2,
                error_code="old_failure",
            )
        )
        self.session.commit()
        result = maintenance.reconcile_job(self.session, self.job.id, apply=True)
        self.assertTrue(result["applied"])
        self.session.refresh(self.job)
        self.assertEqual(self.job.status, "dead_letter")
        self.assertEqual(self.job.attempts, 2)
        self.assertEqual(self.job.error_message, "Preserved old diagnostic")
        self.assertEqual(len(self.session.scalars(select(JobAttemptRecord)).all()), 1)
        again = maintenance.reconcile_job(self.session, self.job.id, apply=True)
        self.assertFalse(again["applied"])
        logs = self.session.scalars(select(AutomationLogRecord)).all()
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].action_type, "RECONCILE_EXHAUSTED_JOB")

    def test_does_not_change_active_retryable_or_leased_work(self):
        for status, attempts, lease in [
            ("running", 2, None),
            ("pending", 1, None),
            ("pending", 2, utc_now() + timedelta(minutes=10)),
            ("completed", 2, None),
        ]:
            with self.subTest(status=status, attempts=attempts, lease=lease):
                self.job.status = status
                self.job.attempts = attempts
                self.job.lease_expires_at = lease
                self.session.commit()
                result = maintenance.reconcile_job(
                    self.session, self.job.id, apply=True
                )
                self.assertFalse(result["eligible"])
                self.assertFalse(result["applied"])
                self.session.refresh(self.job)
                self.assertEqual(self.job.status, status)

    def test_missing_job_is_not_created(self):
        result = maintenance.reconcile_job(self.session, 9999, apply=True)
        self.assertEqual(result["reason"], "not_found")
        self.assertIsNone(self.session.get(JobRecord, 9999))
