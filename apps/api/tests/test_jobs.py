import unittest
from datetime import timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from berrybrain_api.database import Base
from berrybrain_api.jobs import (
    PENDING,
    FAILED,
    claim_next_job,
    complete_job,
    create_job,
    enqueue_note_changed_jobs,
    fail_job,
    list_jobs,
    serialize_job,
    utc_now,
)


class JobServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        engine = create_engine(
            "sqlite:///:memory:", connect_args={"check_same_thread": False}
        )
        Base.metadata.create_all(bind=engine)
        self.session = sessionmaker(bind=engine)()

    def tearDown(self) -> None:
        self.session.close()

    def test_create_and_claim_job_transitions_to_running(self) -> None:
        job = create_job(self.session, "PARSE_NOTE", {"note_path": "inbox/a.md"})

        claimed = claim_next_job(self.session)

        self.assertIsNotNone(claimed)
        self.assertEqual(claimed.id, job.id)
        self.assertEqual(claimed.status, "running")
        self.assertEqual(claimed.attempts, 1)
        self.assertIsNotNone(claimed.started_at)

    def test_claim_next_job_returns_none_when_queue_is_empty(self) -> None:
        self.assertIsNone(claim_next_job(self.session))

    def test_claim_recovers_stale_running_job(self) -> None:
        job = create_job(self.session, "ASSIMILATE_NOTE", {"note_path": "stale.md"})
        job.status = "running"
        job.started_at = utc_now() - timedelta(minutes=45)
        self.session.commit()

        claimed = claim_next_job(self.session)

        self.assertIsNotNone(claimed)
        self.assertEqual(claimed.id, job.id)
        self.assertEqual(claimed.status, "running")
        self.assertEqual(claimed.attempts, 1)

    def test_claim_marks_exhausted_stale_running_job_failed(self) -> None:
        job = create_job(
            self.session, "ASSIMILATE_NOTE", {"note_path": "stale.md"}, max_attempts=2
        )
        job.status = "running"
        job.attempts = 2
        job.started_at = utc_now() - timedelta(minutes=45)
        self.session.commit()

        self.assertIsNone(claim_next_job(self.session))
        self.session.refresh(job)
        self.assertEqual(job.status, FAILED)
        self.assertEqual(job.error_message, "Stale running job exhausted attempts")

    def test_claim_skips_jobs_with_exhausted_attempts(self) -> None:
        exhausted = create_job(
            self.session, "PARSE_NOTE", {"note_path": "a.md"}, max_attempts=2
        )
        exhausted.attempts = 2
        exhausted.status = PENDING
        self.session.commit()

        self.assertIsNone(claim_next_job(self.session))

    def test_complete_and_fail_job_set_terminal_statuses(self) -> None:
        completed_job = create_job(
            self.session, "PARSE_NOTE", {"note_path": "inbox/a.md"}
        )
        failed_job = create_job(
            self.session, "PARSE_NOTE", {"note_path": "inbox/b.md"}, max_attempts=1
        )
        failed_job.attempts = 1
        failed_job.status = "running"
        self.session.commit()

        completed = complete_job(self.session, completed_job.id)
        failed = fail_job(self.session, failed_job.id, "boom")

        self.assertEqual(completed.status, "completed")
        self.assertIsNotNone(completed.completed_at)
        self.assertEqual(failed.status, FAILED)
        self.assertEqual(failed.error_message, "boom")
        self.assertIsNotNone(failed.completed_at)

    def test_fail_with_retries_resets_to_pending(self) -> None:
        job = create_job(
            self.session, "PARSE_NOTE", {"note_path": "c.md"}, max_attempts=3
        )
        job.attempts = 2
        job.status = "running"
        self.session.commit()

        failed = fail_job(self.session, job.id, "temporary error")

        self.assertEqual(failed.status, PENDING)
        self.assertEqual(failed.attempts, 2)
        self.assertEqual(failed.error_message, "temporary error")

    def test_fail_exhausts_on_last_attempt(self) -> None:
        job = create_job(
            self.session, "PARSE_NOTE", {"note_path": "d.md"}, max_attempts=2
        )
        job.attempts = 2
        job.status = "running"
        self.session.commit()

        failed = fail_job(self.session, job.id, "final error")

        self.assertEqual(failed.status, FAILED)
        self.assertEqual(failed.attempts, 2)

    def test_enqueue_note_changed_job_uses_parse_note_payload(self) -> None:
        jobs = enqueue_note_changed_jobs(
            self.session,
            note_path="inbox/a.md",
            event_type="NOTE_UPDATED",
            content_hash="abc",
        )

        self.assertEqual(len(jobs), 14)
        self.assertIn("EXPAND_KNOWLEDGE_GRAPH", [job.type for job in jobs])
        self.assertEqual(jobs[0].type, "PARSE_NOTE")
        self.assertEqual(jobs[0].status, PENDING)
        self.assertIn("content_hash", jobs[0].payload)

    def test_enqueue_note_changed_jobs_adds_title_job_for_drafts_only(self) -> None:
        draft_jobs = enqueue_note_changed_jobs(
            self.session,
            note_path="inbox/rascunho.md",
            event_type="NOTE_CREATED",
            content_hash="abc",
        )
        normal_jobs = enqueue_note_changed_jobs(
            self.session,
            note_path="inbox/edge-computing.md",
            event_type="NOTE_CREATED",
            content_hash="def",
        )

        self.assertIn("GENERATE_NOTE_TITLE", [job.type for job in draft_jobs])
        self.assertNotIn("GENERATE_NOTE_TITLE", [job.type for job in normal_jobs])

    def test_enqueue_note_changed_jobs_is_idempotent_by_type_path_and_hash(self) -> None:
        first = enqueue_note_changed_jobs(
            self.session,
            note_path="inbox/reprocess.md",
            event_type="NOTE_UPDATED",
            content_hash="hash-a",
        )
        second = enqueue_note_changed_jobs(
            self.session,
            note_path="inbox/reprocess.md",
            event_type="NOTE_UPDATED",
            content_hash="hash-a",
        )
        third = enqueue_note_changed_jobs(
            self.session,
            note_path="inbox/reprocess.md",
            event_type="NOTE_UPDATED",
            content_hash="hash-b",
        )

        self.assertEqual(len(first), 14)
        self.assertEqual(second, [])
        self.assertEqual(len(third), 14)
        self.assertTrue(all('"content_hash":"hash-b"' in job.payload for job in third))

    def test_claim_respects_note_pipeline_order(self) -> None:
        jobs = enqueue_note_changed_jobs(
            self.session,
            note_path="inbox/ordered.md",
            event_type="NOTE_CREATED",
            content_hash="abc",
        )

        first = claim_next_job(self.session)
        self.assertEqual(first.type, "PARSE_NOTE")

        self.assertIsNone(claim_next_job(self.session))

        complete_job(self.session, first.id)
        second = claim_next_job(self.session)
        self.assertEqual(second.type, "CLASSIFY_NOTE")
        self.assertEqual(second.payload, jobs[1].payload)

    def test_claim_serializes_graph_mutation_jobs(self) -> None:
        create_job(
            self.session,
            "EXPAND_KNOWLEDGE_GRAPH",
            {"note_path": "a.md", "content_hash": "a"},
        )
        create_job(
            self.session,
            "EXPAND_KNOWLEDGE_GRAPH",
            {"note_path": "b.md", "content_hash": "b"},
        )

        first = claim_next_job(self.session)
        second = claim_next_job(self.session)

        self.assertEqual(first.type, "EXPAND_KNOWLEDGE_GRAPH")
        self.assertIsNone(second)

    def test_list_jobs_orders_newest_first_and_serializes_payload(self) -> None:
        first = create_job(self.session, "PARSE_NOTE", {"note_path": "inbox/a.md"})
        second = create_job(self.session, "PARSE_NOTE", {"note_path": "inbox/b.md"})

        jobs = list_jobs(self.session)
        serialized = serialize_job(second)

        self.assertEqual([job.id for job in jobs], [second.id, first.id])
        self.assertEqual(serialized["payload"], {"note_path": "inbox/b.md"})
        self.assertEqual(serialized["status"], PENDING)

    def test_serialize_job_includes_max_attempts(self) -> None:
        job = create_job(self.session, "PARSE_NOTE", {"k": "v"}, max_attempts=5)
        result = serialize_job(job)

        self.assertEqual(result["max_attempts"], 5)


if __name__ == "__main__":
    unittest.main()
