import unittest
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from berrybrain_api.database import Base
from berrybrain_api.services import (
    find_similar_chunk_notes,
    find_similar_chunks_by_vector,
    store_embedding,
)
from berrybrain_api.jobs import (
    CANCELLED,
    CANCEL_REQUESTED,
    COMPLETED,
    DEAD_LETTER,
    FAILED,
    NOTE_CHANGED_PIPELINE_ORDER,
    PARSE_NOTE,
    PENDING,
    SUPERSEDED,
    UPDATE_GRAPH_STATS,
    acknowledge_job_cancellation,
    affected_job_types_for_note_update,
    calculate_pipeline_progress,
    claim_next_job,
    complete_job,
    create_job,
    enqueue_note_changed_jobs,
    fail_job,
    list_jobs,
    normalize_utc,
    parse_json,
    renew_job_lease,
    request_job_cancellation,
    retry_job,
    serialize_job,
    serialize_datetime,
    should_generate_note_title,
    utc_now,
)
from berrybrain_api.models import (
    AutomationLogRecord,
    ChunkRecord,
    JobRecord,
    NoteRecord,
    WorkerInboxRecord,
)


class JobServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine(
            "sqlite:///:memory:", connect_args={"check_same_thread": False}
        )
        Base.metadata.create_all(bind=self.engine)
        self.session = sessionmaker(bind=self.engine)()

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
        self.assertIsNotNone(claimed.lease_expires_at)
        self.assertEqual(claimed.claimed_by, "api-worker")

    def test_pending_and_running_jobs_cancel_without_retry(self) -> None:
        pending = create_job(self.session, "PARSE_NOTE", {"note_path": "pending.md"})
        cancelled = request_job_cancellation(self.session, pending.id)
        self.assertEqual(cancelled.status, CANCELLED)
        self.assertIsNotNone(cancelled.completed_at)
        self.assertIsNone(claim_next_job(self.session))

        running = create_job(self.session, "PARSE_NOTE", {"note_path": "running.md"})
        claimed = claim_next_job(self.session)
        self.assertEqual(claimed.id, running.id)
        requested = request_job_cancellation(self.session, running.id)
        self.assertEqual(requested.status, CANCEL_REQUESTED)

        failed = fail_job(self.session, running.id, "provider timeout")
        self.assertEqual(failed.status, CANCELLED)
        self.assertIsNone(failed.error_message)
        self.assertEqual(
            acknowledge_job_cancellation(self.session, running.id).status, CANCELLED
        )
        actions = set(
            self.session.execute(select(AutomationLogRecord.action_type)).scalars()
        )
        self.assertIn("CANCEL_JOB", actions)
        self.assertIn("JOB_CANCELLED", actions)

    def test_completion_cannot_override_requested_cancellation(self) -> None:
        job = create_job(self.session, "PARSE_NOTE", {"note_path": "cancel.md"})
        claim_next_job(self.session)
        request_job_cancellation(self.session, job.id)

        with self.assertRaises(HTTPException) as conflict:
            complete_job(self.session, job.id)
        self.assertEqual(conflict.exception.status_code, 409)
        self.assertEqual(self.session.get(JobRecord, job.id).status, CANCEL_REQUESTED)

        acknowledged = acknowledge_job_cancellation(self.session, job.id)
        self.assertEqual(acknowledged.status, CANCELLED)

    def test_job_boundary_helpers_fail_closed_and_normalize_dates(self) -> None:
        self.assertEqual(parse_json("not-json"), {})
        self.assertIsNone(serialize_datetime(None))
        naive = datetime(2026, 1, 2, 3, 4, 5)
        self.assertEqual(normalize_utc(naive).tzinfo, UTC)
        self.assertTrue(serialize_datetime(naive).endswith("Z"))
        self.assertTrue(should_generate_note_title("inbox/rascunho.md"))
        self.assertTrue(should_generate_note_title("inbox/rascunho-2.md"))
        self.assertTrue(should_generate_note_title("inbox/nota-sem-titulo.md"))
        self.assertFalse(should_generate_note_title("notes/docker.md"))

        with self.assertRaises(HTTPException) as missing:
            renew_job_lease(self.session, 999)
        self.assertEqual(missing.exception.status_code, 404)

        pending = create_job(self.session, "PARSE_NOTE", {"note_path": "pending.md"})
        with self.assertRaises(HTTPException) as not_running:
            renew_job_lease(self.session, pending.id)
        self.assertEqual(not_running.exception.status_code, 409)

    def test_create_job_dedupes_active_idempotency_key(self) -> None:
        payload = {
            "content_hash": "hash-a",
            "note_path": "inbox/idempotent.md",
        }

        first = create_job(self.session, "PARSE_NOTE", payload)
        second = create_job(self.session, "PARSE_NOTE", payload)

        self.assertEqual(second.id, first.id)
        self.assertEqual(len(list_jobs(self.session)), 1)

    def test_running_job_is_not_recovered_before_lease_expires(self) -> None:
        job = create_job(self.session, "PARSE_NOTE", {"note_path": "inbox/a.md"})
        claimed = claim_next_job(self.session, lease_minutes=30)

        self.assertIsNone(claim_next_job(self.session, stale_after_minutes=0))
        self.session.refresh(claimed)
        self.assertEqual(claimed.status, "running")
        self.assertEqual(claimed.id, job.id)

    def test_expired_lease_is_recovered_and_claimed_again(self) -> None:
        job = create_job(self.session, "PARSE_NOTE", {"note_path": "inbox/a.md"})
        claimed = claim_next_job(self.session, lease_minutes=30)
        claimed.lease_expires_at = utc_now() - timedelta(minutes=1)
        self.session.commit()

        recovered = claim_next_job(self.session)

        self.assertIsNotNone(recovered)
        self.assertEqual(recovered.id, job.id)
        self.assertEqual(recovered.status, "running")
        self.assertEqual(recovered.attempts, 2)

    def test_running_job_recovers_after_new_database_session(self) -> None:
        job = create_job(self.session, "PARSE_NOTE", {"note_path": "restart.md"})
        claimed = claim_next_job(self.session, lease_minutes=30)
        self.assertEqual(claimed.id, job.id)
        self.session.close()

        restarted_session = sessionmaker(bind=self.engine)()
        try:
            stored = restarted_session.get(JobRecord, job.id)
            stored.lease_expires_at = utc_now() - timedelta(minutes=1)
            restarted_session.commit()

            recovered = claim_next_job(restarted_session)

            self.assertIsNotNone(recovered)
            self.assertEqual(recovered.id, job.id)
            self.assertEqual(recovered.status, "running")
            self.assertEqual(recovered.attempts, 2)
        finally:
            restarted_session.close()

    def test_worker_crash_recovery_across_note_pipeline_stages(self) -> None:
        for index, job_type in enumerate(NOTE_CHANGED_PIPELINE_ORDER):
            job = create_job(
                self.session,
                job_type,
                {
                    "content_hash": f"hash-{index}",
                    "note_path": f"inbox/crash-{index}.md",
                },
                max_attempts=3,
            )
            job.status = "running"
            job.attempts = 1
            job.lease_expires_at = utc_now() - timedelta(minutes=1)
            self.session.commit()

            recovered = claim_next_job(self.session)

            self.assertIsNotNone(recovered)
            self.assertEqual(recovered.id, job.id)
            self.assertEqual(recovered.type, job_type)
            self.assertEqual(recovered.status, "running")
            self.assertEqual(recovered.attempts, 2)
            complete_job(self.session, recovered.id)

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
        self.assertEqual(job.status, DEAD_LETTER)
        self.assertEqual(job.error_message, "Stale running job exhausted attempts")

    def test_stale_cancel_request_finishes_without_replay(self) -> None:
        job = create_job(
            self.session, "ASSIMILATE_NOTE", {"note_path": "cancel-stale.md"}
        )
        claim_next_job(self.session)
        request_job_cancellation(self.session, job.id)
        job = self.session.get(JobRecord, job.id)
        job.lease_expires_at = utc_now() - timedelta(minutes=1)
        self.session.commit()

        self.assertIsNone(claim_next_job(self.session))
        self.session.refresh(job)
        self.assertEqual(job.status, CANCELLED)
        self.assertIsNotNone(job.completed_at)

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
        self.assertEqual(failed.status, DEAD_LETTER)
        self.assertEqual(failed.error_message, "boom")
        self.assertIsNotNone(failed.completed_at)

    def test_completed_job_is_not_claimed_or_requeued_by_duplicate_complete(
        self,
    ) -> None:
        job = create_job(self.session, "PARSE_NOTE", {"note_path": "dup.md"})
        claimed = claim_next_job(self.session)

        claim_token = claimed.claim_token
        first_complete = complete_job(self.session, claimed.id, claim_token=claim_token)
        completed_at = first_complete.completed_at
        second_complete = complete_job(
            self.session, claimed.id, claim_token=claim_token
        )

        self.assertEqual(first_complete.id, job.id)
        self.assertEqual(second_complete.status, "completed")
        self.assertEqual(second_complete.completed_at, completed_at)
        inbox = self.session.execute(select(WorkerInboxRecord)).scalars().all()
        self.assertEqual(len(inbox), 1)
        self.assertEqual(inbox[0].message_type, "complete")
        self.assertIsNone(claim_next_job(self.session))

    def test_stale_worker_token_cannot_complete_new_claim(self) -> None:
        job = create_job(
            self.session,
            "PARSE_NOTE",
            {"note_path": "claim-token.md"},
            max_attempts=3,
        )
        first_claim = claim_next_job(self.session)
        first_token = first_claim.claim_token
        first_claim.lease_expires_at = utc_now() - timedelta(minutes=1)
        self.session.commit()

        second_claim = claim_next_job(self.session)
        second_token = second_claim.claim_token
        self.assertNotEqual(first_token, second_token)

        with self.assertRaises(HTTPException) as stale:
            complete_job(self.session, job.id, claim_token=first_token)
        self.assertEqual(stale.exception.status_code, 409)

        completed = complete_job(self.session, job.id, claim_token=second_token)
        self.assertEqual(completed.status, COMPLETED)
        inbox = self.session.execute(select(WorkerInboxRecord)).scalars().all()
        self.assertEqual(len(inbox), 1)
        self.assertEqual(inbox[0].claim_token, second_token)

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

        self.assertEqual(failed.status, DEAD_LETTER)
        self.assertEqual(failed.attempts, 2)

    def test_retry_dead_letter_job_resets_for_manual_retry(self) -> None:
        job = create_job(
            self.session, "PARSE_NOTE", {"note_path": "retry.md"}, max_attempts=1
        )
        job.status = "running"
        job.attempts = 1
        self.session.commit()
        failed = fail_job(self.session, job.id, "final error")

        retried = retry_job(self.session, failed.id)

        self.assertEqual(retried.status, PENDING)
        self.assertEqual(retried.attempts, 0)
        self.assertIsNone(retried.error_message)
        retry_logs = (
            self.session.query(AutomationLogRecord)
            .filter(AutomationLogRecord.action_type == "RETRY_JOB")
            .all()
        )
        self.assertEqual(len(retry_logs), 1)
        self.assertEqual(retry_logs[0].target_id, str(job.id))

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

    def test_pipeline_progress_uses_stages_actually_queued(self) -> None:
        jobs = enqueue_note_changed_jobs(
            self.session,
            note_path="inbox/complete.md",
            event_type="NOTE_UPDATED",
            content_hash="progress-hash",
        )
        for job in jobs:
            job.status = "completed"
        self.session.commit()

        progress = calculate_pipeline_progress(jobs)

        self.assertEqual(len(progress), 1)
        self.assertEqual(progress[0]["total"], len({job.type for job in jobs}))
        self.assertEqual(progress[0]["completed"], progress[0]["total"])
        self.assertEqual(progress[0]["percent"], 100)

    def test_pipeline_progress_does_not_mix_old_completed_run_with_current_failure(
        self,
    ) -> None:
        old_jobs = enqueue_note_changed_jobs(
            self.session,
            note_path="inbox/current.md",
            event_type="NOTE_UPDATED",
            content_hash="old-hash",
        )
        for job in old_jobs:
            job.status = COMPLETED
        self.session.commit()
        current_jobs = enqueue_note_changed_jobs(
            self.session,
            note_path="inbox/current.md",
            event_type="NOTE_UPDATED",
            content_hash="current-hash",
        )
        current_jobs[0].status = FAILED
        current_jobs[0].error_message = "Provider unavailable"
        self.session.commit()

        progress = calculate_pipeline_progress(list(reversed(old_jobs + current_jobs)))[
            0
        ]

        self.assertEqual(progress["pipelineRunId"], "current-hash")
        self.assertEqual(progress["state"], "failed")
        self.assertEqual(progress["completed"], 0)
        self.assertEqual(progress["errors"][0]["message"], "Provider unavailable")
        self.assertIn("note is saved", progress["errors"][0]["impact"])

    def test_enqueue_note_changed_jobs_is_idempotent_by_type_path_and_hash(
        self,
    ) -> None:
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
        old_active = [
            job
            for job in first
            if job.status in {PENDING, "running"} and job.content_hash == "hash-a"
        ]
        self.assertEqual(old_active, [])
        self.assertTrue(all(job.status == SUPERSEDED for job in first))

    def test_enqueue_note_changed_jobs_can_limit_to_affected_stages(self) -> None:
        jobs = enqueue_note_changed_jobs(
            self.session,
            note_path="inbox/formatting.md",
            event_type="NOTE_UPDATED",
            content_hash="hash-format",
            affected_job_types={PARSE_NOTE, UPDATE_GRAPH_STATS},
        )

        self.assertEqual([job.type for job in jobs], [PARSE_NOTE, UPDATE_GRAPH_STATS])
        self.assertEqual(jobs[0].payload.count("affected_job_types"), 1)

    def test_partial_pipeline_dedupe_prevents_duplicate_jobs(self) -> None:
        affected = {PARSE_NOTE, UPDATE_GRAPH_STATS}
        first = enqueue_note_changed_jobs(
            self.session,
            note_path="inbox/partial.md",
            event_type="NOTE_UPDATED",
            content_hash="hash-partial",
            affected_job_types=affected,
        )
        second = enqueue_note_changed_jobs(
            self.session,
            note_path="inbox/partial.md",
            event_type="NOTE_UPDATED",
            content_hash="hash-partial",
            affected_job_types=affected,
        )

        self.assertEqual(len(first), 2)
        self.assertEqual(second, [])

    def test_affected_job_types_detects_whitespace_only_update(self) -> None:
        affected = affected_job_types_for_note_update(
            "# Title\n\nsame words", "# Title\nsame   words\n", "inbox/a.md"
        )

        self.assertEqual(affected, {PARSE_NOTE, UPDATE_GRAPH_STATS})

    def test_affected_job_types_detects_frontmatter_only_update(self) -> None:
        affected = affected_job_types_for_note_update(
            "---\ntags: a\n---\n# Title\nBody",
            "---\ntags: b\n---\n# Title\nBody",
            "inbox/a.md",
        )

        self.assertIn("ASSIMILATE_NOTE", affected)
        self.assertIn("EXPAND_KNOWLEDGE_GRAPH", affected)
        self.assertNotIn("GENERATE_EMBEDDING", affected)

    def test_affected_job_types_detects_body_update_as_full_pipeline(self) -> None:
        affected = affected_job_types_for_note_update(
            "# Title\nOld body", "# Title\nNew body", "inbox/rascunho.md"
        )

        self.assertIn("GENERATE_EMBEDDING", affected)
        self.assertIn("GENERATE_NOTE_TITLE", affected)

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

    def test_two_workers_do_not_claim_same_job(self) -> None:
        create_job(self.session, "PARSE_NOTE", {"note_path": "concurrent.md"})
        worker_a = sessionmaker(bind=self.engine)()
        worker_b = sessionmaker(bind=self.engine)()
        try:
            first = claim_next_job(worker_a, claimed_by="worker-a")
            second = claim_next_job(worker_b, claimed_by="worker-b")

            self.assertIsNotNone(first)
            self.assertEqual(first.claimed_by, "worker-a")
            self.assertIsNone(second)
        finally:
            worker_a.close()
            worker_b.close()

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

    def test_store_embedding_creates_chunk_record(self) -> None:
        embedding = store_embedding(
            self.session,
            note_id=123,
            content_hash="hash-chunk",
            vector=[0.1, 0.2, 0.3],
            model="embedding-model",
            provider="ollama",
            chunk_index=1,
            chunk_text="Docker uses Linux namespaces.",
            heading_path="Docker / Runtime",
            start_line=4,
            end_line=8,
            token_count=4,
        )

        chunk = (
            self.session.query(ChunkRecord)
            .filter(ChunkRecord.note_id == 123, ChunkRecord.chunk_index == 1)
            .one()
        )
        self.assertEqual(chunk.embedding_id, embedding.id)
        self.assertEqual(chunk.heading_path, "Docker / Runtime")
        self.assertEqual(embedding.vector_dimensions, 3)
        self.assertIsNotNone(embedding.vector_blob)
        self.assertGreater(len(embedding.vector_blob or b""), 0)
        self.assertEqual(embedding.provider, "ollama")

    def test_store_embedding_invalidates_old_note_hash_chunks(self) -> None:
        store_embedding(
            self.session,
            note_id=123,
            content_hash="old-hash",
            vector=[0.1],
            model="embedding-model",
            chunk_index=0,
            chunk_text="old text",
        )
        store_embedding(
            self.session,
            note_id=123,
            content_hash="new-hash",
            vector=[0.2],
            model="embedding-model",
            chunk_index=0,
            chunk_text="new text",
        )

        chunks = (
            self.session.query(ChunkRecord).filter(ChunkRecord.note_id == 123).all()
        )
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0].content_hash, "new-hash")

    def test_find_similar_chunk_notes_groups_and_excludes_source(self) -> None:
        self.session.add_all(
            [
                NoteRecord(id=1, title="Source", slug="source", path="source.md"),
                NoteRecord(id=2, title="Target A", slug="a", path="a.md"),
                NoteRecord(id=3, title="Target B", slug="b", path="b.md"),
            ]
        )
        self.session.commit()
        store_embedding(
            self.session,
            note_id=1,
            content_hash="h1",
            vector=[1.0, 0.0],
            model="m",
            chunk_index=0,
            chunk_text="source",
        )
        store_embedding(
            self.session,
            note_id=2,
            content_hash="h2",
            vector=[0.9, 0.1],
            model="m",
            chunk_index=0,
            chunk_text="best target chunk",
        )
        store_embedding(
            self.session,
            note_id=2,
            content_hash="h2",
            vector=[0.8, 0.2],
            model="m",
            chunk_index=1,
            chunk_text="second target chunk",
        )
        store_embedding(
            self.session,
            note_id=3,
            content_hash="h3",
            vector=[0.0, 1.0],
            model="m",
            chunk_index=0,
            chunk_text="weak target chunk",
        )

        results = find_similar_chunk_notes(self.session, source_note_id=1, limit=10)

        self.assertEqual([item["note_id"] for item in results], [2, 3])
        self.assertEqual(results[0]["evidence"]["text"], "best target chunk")

    def test_find_similar_chunks_by_query_vector(self) -> None:
        self.session.add(
            NoteRecord(
                id=4,
                title="Vector Target",
                slug="vector",
                path="vector.md",
                content_hash="hv",
            )
        )
        self.session.commit()
        store_embedding(
            self.session,
            note_id=4,
            content_hash="hv",
            vector=[1.0, 0.0],
            model="m",
            chunk_index=0,
            chunk_text="semantic target without lexical query",
        )

        results = find_similar_chunks_by_vector(self.session, [0.95, 0.05], limit=5)

        self.assertEqual(results[0]["id"], 4)
        self.assertEqual(results[0]["source"], "vector_chunk")
        self.assertGreater(results[0]["similarity"], 0.9)


if __name__ == "__main__":
    unittest.main()
