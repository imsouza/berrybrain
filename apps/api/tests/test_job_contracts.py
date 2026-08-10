import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from berrybrain_api.database import Base
from berrybrain_api.job_contracts import (
    JobPayloadError,
    canonical_job_counts,
    serialize_attempt,
    update_job_attempt,
    validate_job_payload,
)
from berrybrain_api.jobs import claim_next_job, complete_job, create_job, fail_job
from berrybrain_api.models import JobAttemptRecord


class JobContractsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine(
            "sqlite:///:memory:", connect_args={"check_same_thread": False}
        )
        Base.metadata.create_all(bind=self.engine)
        self.session = sessionmaker(bind=self.engine)()

    def tearDown(self) -> None:
        self.session.close()
        self.engine.dispose()

    def test_unknown_job_type_is_rejected_before_enqueue(self) -> None:
        with self.assertRaises(JobPayloadError) as error:
            create_job(self.session, "UNKNOWN_JOB", {})

        self.assertEqual(error.exception.code, "unsupported_job_type")

    def test_judge_artifact_requires_committed_artifact_identity(self) -> None:
        with self.assertRaises(JobPayloadError) as error:
            validate_job_payload("JUDGE_ARTIFACT", {"artifact_type": "insight"})

        self.assertEqual(error.exception.code, "invalid_payload")

    def test_attempt_is_created_on_claim_and_completed_separately(self) -> None:
        job = create_job(self.session, "PARSE_NOTE", {"note_path": "inbox/a.md"})

        claimed = claim_next_job(self.session)
        self.assertEqual(claimed.id, job.id)
        complete_job(self.session, job.id, claimed.claim_token)

        recorded = self.session.query(JobAttemptRecord).one()
        payload = serialize_attempt(recorded)
        self.assertEqual(payload["stage"], "completed")
        self.assertEqual(payload["attempt"], 1)
        self.assertIsNotNone(payload["finishedAt"])

    def test_canonical_counts_do_not_mix_jobs_and_attempts(self) -> None:
        first = create_job(self.session, "PARSE_NOTE", {"note_path": "a.md"})
        claimed = claim_next_job(self.session)
        fail_job(self.session, first.id, "temporary", claimed.claim_token)
        create_job(self.session, "PARSE_NOTE", {"note_path": "b.md"})

        counts = canonical_job_counts(self.session)

        self.assertEqual(counts["total_jobs"], 2)
        self.assertEqual(counts["attempt_errors"], 1)
        self.assertEqual(counts["pending"], 2)

    def test_canonical_counts_include_worker_model_calls(self) -> None:
        create_job(self.session, "PARSE_NOTE", {"note_path": "model.md"})
        claimed = claim_next_job(self.session)
        update_job_attempt(
            self.session,
            claimed,
            stage="model_calling",
            provider="cloud",
            model="test-model",
            model_call_id="call-1",
        )
        self.session.commit()

        self.assertEqual(canonical_job_counts(self.session)["model_calls"], 1)
