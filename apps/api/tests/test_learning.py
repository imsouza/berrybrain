import unittest

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from berrybrain_api.database import Base
from berrybrain_api.graph_feedback import node_artifact_key, record_feedback
from berrybrain_api.learning import build_learning_guidance, record_learning_event
from berrybrain_api.models import LearningEventRecord


class LearningPolicyTest(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)

    def tearDown(self) -> None:
        self.engine.dispose()

    def test_graph_feedback_creates_a_durable_learning_signal(self) -> None:
        with Session(self.engine) as session:
            key = node_artifact_key("concept", "Skip")
            record_feedback(
                session,
                artifact_kind="node",
                artifact_key=key,
                source_note_ids=[4, 9],
                action="deleted",
                original_payload={"type": "concept", "label": "Skip"},
            )
            session.commit()

            event = session.scalar(select(LearningEventRecord))
            assert event is not None
            self.assertEqual(event.action, "deleted")
            self.assertEqual(event.signal, -1.0)
            guidance = build_learning_guidance(
                session, source_note_ids=[9, 4], target_type="graph_node"
            )
            self.assertEqual(guidance["negativePatterns"][0]["artifactKey"], key)
            self.assertEqual(guidance["recentSignals"][0]["eventId"], event.event_id)

    def test_correction_is_preferred_but_does_not_bypass_validation(self) -> None:
        with Session(self.engine) as session:
            key = node_artifact_key("concept", "Forecast")
            record_feedback(
                session,
                artifact_kind="node",
                artifact_key=key,
                source_note_ids=[7],
                action="corrected",
                original_payload={"type": "concept", "label": "Forecast"},
                replacement_payload={
                    "type": "concept",
                    "label": "Probabilistic forecasting",
                },
            )
            session.commit()

            guidance = build_learning_guidance(session, source_note_ids=[7])
            self.assertEqual(
                guidance["corrections"][0]["replacement"]["label"],
                "Probabilistic forecasting",
            )
            self.assertTrue(
                any(
                    "validation" in instruction
                    for instruction in guidance["instructions"]
                )
            )

    def test_learning_signal_rejects_out_of_range_values(self) -> None:
        with Session(self.engine) as session, self.assertRaises(ValueError):
            record_learning_event(
                session,
                event_type="test.invalid",
                target_type="system",
                target_key="invalid",
                action="invalid",
                signal=1.1,
            )

    def test_guidance_uses_overlapping_context_and_latest_user_decision(self) -> None:
        with Session(self.engine) as session:
            for action in ("downvoted", "upvoted"):
                record_learning_event(
                    session,
                    event_type=f"ask.answer.{action}",
                    target_type="ask_answer",
                    target_key="ask:session:turn:8",
                    action=action,
                    source_note_ids=[4, 9],
                    before_state={"answer": "A grounded answer"},
                )
                session.flush()
            record_learning_event(
                session,
                event_type="ask.answer.downvoted",
                target_type="ask_answer",
                target_key="ask:other:turn:2",
                action="downvoted",
                source_note_ids=[77],
                before_state={"answer": "Unrelated context"},
            )
            session.commit()

            guidance = build_learning_guidance(
                session, source_note_ids=[9], target_type="ask_answer"
            )

        self.assertEqual(len(guidance["recentSignals"]), 1)
        self.assertEqual(guidance["recentSignals"][0]["action"], "upvoted")
        self.assertEqual(len(guidance["positivePatterns"]), 1)
        self.assertEqual(guidance["negativePatterns"], [])

    def test_corrections_and_annotations_are_exposed_as_scoped_context(self) -> None:
        with Session(self.engine) as session:
            record_learning_event(
                session,
                event_type="ask.answer.corrected",
                target_type="ask_answer",
                target_key="ask:session:turn:3",
                action="corrected",
                source_note_ids=[12],
                before_state={"answer": "The old answer"},
                after_state={
                    "correction": "The evidence supports the corrected answer."
                },
            )
            record_learning_event(
                session,
                event_type="graph.node.annotated",
                target_type="graph_node",
                target_key="node:concept:forecasting",
                action="annotated",
                source_note_ids=[12],
                after_state={"userNotes": "Use the probabilistic interpretation."},
            )
            session.commit()

            ask_guidance = build_learning_guidance(
                session, source_note_ids=[12], target_type="ask_answer"
            )
            node_guidance = build_learning_guidance(
                session, source_note_ids=[12], target_type="graph_node"
            )

        self.assertEqual(
            ask_guidance["corrections"][0]["replacement"]["correction"],
            "The evidence supports the corrected answer.",
        )
        self.assertEqual(
            node_guidance["annotations"][0]["after"]["userNotes"],
            "Use the probabilistic interpretation.",
        )


if __name__ == "__main__":
    unittest.main()
