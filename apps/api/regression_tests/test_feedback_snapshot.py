"""Isolated product checks for the graph confidence read optimization."""

import json
import unittest

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session

from berrybrain_api.database import Base
from berrybrain_api.graph_feedback import (
    context_key,
    feedback_snapshot,
    resolve_feedback,
)
from berrybrain_api.models import GraphFeedbackRecord


class FeedbackSnapshotTest(unittest.TestCase):
    def test_snapshot_preserves_exact_overlap_and_latest_precedence(self):
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        with Session(engine) as session:
            for ids, action, active in [
                ([1], "confirmed", True),
                ([1, 2], "ignored", True),
                ([3], "corrected", True),
                ([1], "deleted", False),
            ]:
                session.add(
                    GraphFeedbackRecord(
                        artifact_kind="node",
                        artifact_key="node:concept:test",
                        context_key=context_key(ids),
                        source_note_ids=json.dumps(ids),
                        action=action,
                        active=active,
                        original_payload="{}",
                        replacement_payload="{}",
                    )
                )
            session.commit()
            contexts = [[1], [1, 2], [2, 3], [4], []]

            def decisions():
                return [
                    resolve_feedback(
                        session,
                        artifact_kind="node",
                        artifact_key="node:concept:test",
                        source_note_ids=ids,
                    )
                    for ids in contexts
                ]

            expected = decisions()
            statements = []
            event.listen(
                engine,
                "before_cursor_execute",
                lambda c, u, sql, p, x, m: statements.append(sql),
            )
            with feedback_snapshot(session):
                for _ in range(20):
                    self.assertEqual(decisions(), expected)
            self.assertEqual(
                len(statements), 1, "Repeated artifact checks must not issue N+1 reads"
            )
            self.assertEqual(expected[0].action, "confirmed")
            self.assertEqual(expected[1].action, "ignored")
            self.assertEqual(expected[2].action, "corrected")
            self.assertIsNone(expected[3])
            self.assertIsNone(expected[4])
            before = len(statements)
            self.assertEqual(decisions(), expected)
            self.assertGreater(
                len(statements), before, "Snapshot must not leak past its operation"
            )
        engine.dispose()


if __name__ == "__main__":
    unittest.main()
