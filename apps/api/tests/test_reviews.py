import json
import unittest

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import berrybrain_api.models  # noqa: F401
from berrybrain_api.database import Base
from berrybrain_api.models import ChunkRecord, InsightRecord, NoteRecord
from berrybrain_api.review_service import (
    create_review_item,
    grade_review_item,
    mark_reviews_stale_for_note,
    set_review_status,
)


class ReviewServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        engine = create_engine("sqlite://")
        Base.metadata.create_all(engine)
        self.session = sessionmaker(bind=engine)()
        self.note = NoteRecord(
            title="Distributed Observability",
            slug="distributed-observability",
            path="notes/distributed-observability.md",
            content="Logs, metrics, and traces expose distributed behavior.",
            content_hash="hash-v1",
        )
        self.session.add(self.note)
        self.session.flush()
        self.session.add(
            ChunkRecord(
                id=10,
                note_id=self.note.id,
                note_version=self.note.content_hash,
                content_hash=self.note.content_hash,
                text=self.note.content,
                start_line=1,
                end_line=1,
            )
        )
        self.evidence = {
            "sourceNoteId": self.note.id,
            "targetNoteId": self.note.id,
            "sourceChunkId": 10,
            "targetChunkId": 10,
            "excerpt": "Logs, metrics, and traces expose distributed behavior.",
        }
        self.insight = InsightRecord(
            type="knowledge_gap",
            title="Telemetry signals form one diagnostic context",
            description="The note combines three complementary signals.",
            related_notes=json.dumps([self.note.id]),
            why_it_matters="Using the signals together improves failure diagnosis.",
            evidence=json.dumps([self.evidence]),
            suggested_action="Explain when each signal is useful.",
            graph_impact="Strengthens the observability concept.",
            confidence=0.85,
            provider="deterministic",
            model="fixture",
        )
        self.session.add(self.insight)
        self.session.commit()

    def tearDown(self) -> None:
        self.session.close()

    def create_item(self):
        return create_review_item(
            self.session,
            source_insight_id=self.insight.id,
            review_type="explain",
            prompt="Explain how logs, metrics, and traces complement each other.",
            expected_points=[
                "Logs expose distributed behavior",
                "Metrics expose distributed behavior",
                "Traces expose distributed behavior",
            ],
            evidence=[self.evidence],
        )

    def test_review_creation_is_grounded_and_idempotent(self) -> None:
        first = self.create_item()
        second = self.create_item()
        self.assertEqual(first.id, second.id)
        self.assertEqual(json.loads(first.source_note_ids), [self.note.id])
        self.assertEqual(json.loads(first.source_chunk_ids), [10])
        self.assertEqual(first.status, "active")
        self.assertEqual(self.insight.status, "converted_to_review")

    def test_sm2_ratings_update_schedule_and_keep_difficulty_separate(self) -> None:
        item = self.create_item()
        good = grade_review_item(self.session, item.id, "good", perceived_difficulty=4)
        self.assertEqual(good.interval_days, 1)
        self.assertEqual(good.repetitions, 1)
        self.assertEqual(good.perceived_difficulty, 4)
        self.assertEqual(good.last_performance, "good")

        easy = grade_review_item(self.session, item.id, "easy")
        self.assertEqual(easy.interval_days, 7)
        self.assertEqual(easy.repetitions, 2)
        self.assertEqual(easy.perceived_difficulty, 4)

        forgotten = grade_review_item(self.session, item.id, "forgot")
        self.assertEqual(forgotten.interval_days, 1)
        self.assertEqual(forgotten.repetitions, 0)
        self.assertEqual(forgotten.last_performance, "forgot")

    def test_pause_resume_delete_and_source_change(self) -> None:
        item = self.create_item()
        paused = set_review_status(self.session, item.id, "paused")
        self.assertEqual(paused.status, "paused")
        with self.assertRaises(HTTPException):
            grade_review_item(self.session, item.id, "good")
        resumed = set_review_status(self.session, item.id, "active")
        self.assertEqual(resumed.status, "active")

        stale_count = mark_reviews_stale_for_note(self.session, self.note.id, "hash-v2")
        self.session.commit()
        self.session.refresh(item)
        self.assertEqual(stale_count, 1)
        self.assertEqual(item.status, "stale")

        deleted = set_review_status(self.session, item.id, "deleted")
        self.assertEqual(deleted.status, "deleted")

    def test_low_value_or_untraceable_insights_are_rejected(self) -> None:
        self.insight.type = "system_diagnostic"
        self.session.commit()
        with self.assertRaises(HTTPException):
            self.create_item()
        self.insight.type = "knowledge_gap"
        self.session.commit()
        with self.assertRaises(HTTPException):
            create_review_item(
                self.session,
                source_insight_id=self.insight.id,
                review_type="explain",
                prompt="Unsupported prompt",
                expected_points=["Unsupported"],
                evidence=["invented evidence"],
            )

    def test_expected_points_must_be_supported_by_current_sources(self) -> None:
        with self.assertRaises(HTTPException) as raised:
            create_review_item(
                self.session,
                source_insight_id=self.insight.id,
                review_type="explain",
                prompt="Explain the source note.",
                expected_points=["Kubernetes schedules pods across a cluster"],
                evidence=[self.evidence],
            )
        self.assertEqual(raised.exception.status_code, 422)
        self.assertIn("not supported", raised.exception.detail)


if __name__ == "__main__":
    unittest.main()
