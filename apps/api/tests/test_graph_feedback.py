import json
import unittest

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from berrybrain_api.database import Base
from berrybrain_api.graph_write_service import GraphWriteService
from berrybrain_api.models import GraphFeedbackRecord, GraphNodeRecord


class GraphFeedbackTest(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite://")
        Base.metadata.create_all(self.engine)
        self.session = sessionmaker(bind=self.engine)()
        self.writer = GraphWriteService(self.session)

    def tearDown(self) -> None:
        self.session.close()
        self.engine.dispose()

    def test_deleted_generated_node_is_suppressed_in_the_same_context(self) -> None:
        node = self.writer.upsert_node(
            node_type="concept",
            label="Ambiguous Navigation Term",
            source_note_ids=[3, 4],
            created_by="system",
        )

        self.writer.delete_node(node.id, user_decision=True)
        self.session.expire_all()
        self.writer = GraphWriteService(self.session)
        regenerated = self.writer.upsert_node(
            node_type="concept",
            label="Ambiguous Navigation Term",
            source_note_ids=[3, 4],
            created_by="system",
        )

        self.assertEqual(regenerated.status, "ignored")
        self.assertEqual(regenerated.semantic_status, "quarantined")
        self.session.commit()
        self.session.expire_all()
        persisted = self.session.get(GraphNodeRecord, regenerated.id)
        self.assertIsNotNone(persisted)
        self.assertEqual(persisted.status, "ignored")
        self.assertEqual(persisted.semantic_status, "quarantined")
        feedback = self.session.execute(
            select(GraphFeedbackRecord).where(GraphFeedbackRecord.active.is_(True))
        ).scalar_one()
        self.assertEqual(feedback.action, "deleted")
        self.assertEqual(json.loads(feedback.source_note_ids), [3, 4])

    def test_negative_feedback_is_context_scoped(self) -> None:
        node = self.writer.upsert_node(
            node_type="concept",
            label="Contextual Term",
            source_note_ids=[1, 2],
        )
        self.writer.delete_node(node.id, user_decision=True)

        other_context = self.writer.upsert_node(
            node_type="concept",
            label="Contextual Term",
            source_note_ids=[9],
        )

        self.assertEqual(other_context.status, "suggested")
        self.assertEqual(other_context.semantic_status, "active")

    def test_negative_feedback_survives_a_changed_overlapping_source_scope(
        self,
    ) -> None:
        node = self.writer.upsert_node(
            node_type="concept",
            label="Navigation Artifact",
            source_note_ids=[1, 2],
        )
        self.writer.delete_node(node.id, user_decision=True)

        regenerated = self.writer.upsert_node(
            node_type="concept",
            label="Navigation Artifact",
            source_note_ids=[2, 3],
            created_by="system",
        )

        self.assertEqual(regenerated.status, "ignored")
        self.assertEqual(regenerated.semantic_status, "quarantined")

    def test_correction_maps_the_old_candidate_to_the_user_identity(self) -> None:
        node = self.writer.upsert_node(
            node_type="concept",
            label="Distributed Systems",
            summary="Distributed architecture coordinates independent services.",
            source_note_ids=[7],
        )
        corrected = self.writer.update_node_fields(
            node.id,
            label="Distributed Architecture",
            user_decision=True,
        )

        regenerated = self.writer.upsert_node(
            node_type="concept",
            label="Distributed Systems",
            source_note_ids=[7],
            created_by="system",
        )

        self.assertEqual(regenerated.id, corrected.id)
        self.assertEqual(regenerated.label, "Distributed Architecture")
        self.assertEqual(
            self.session.query(GraphNodeRecord).filter_by(type="concept").count(), 1
        )
        feedback = self.session.execute(
            select(GraphFeedbackRecord).where(
                GraphFeedbackRecord.action == "corrected",
                GraphFeedbackRecord.active.is_(True),
            )
        ).scalar_one()
        self.assertIn("Distributed Architecture", feedback.replacement_payload)

    def test_confirmation_is_an_auditable_confidence_signal(self) -> None:
        node = self.writer.upsert_node(
            node_type="concept",
            label="Temporal Forecasting",
            source_note_ids=[11],
            source_evidence=["Temporal forecasting estimates future observations."],
        )

        confirmed = self.writer.set_node_status(
            node.id, "confirmed", user_decision=True
        )

        factors = json.loads(confirmed.confidence_factors)
        self.assertTrue(any(item.startswith("human-feedback:") for item in factors))
        self.assertEqual(confirmed.status, "confirmed")

    def test_ignored_edge_stays_hidden_when_generated_again(self) -> None:
        source = self.writer.upsert_node(
            node_type="concept", label="Poetry Analysis", source_note_ids=[3]
        )
        target = self.writer.upsert_node(
            node_type="concept", label="Game Patch", source_note_ids=[4]
        )
        edge = self.writer.upsert_edge(
            source_node_id=source.id,
            target_node_id=target.id,
            edge_type="related",
            reason="A candidate relationship for human review.",
            evidence=["source:3", "source:4"],
            source_note_ids=[3, 4],
        )
        self.writer.set_edge_status(edge.id, "ignored", user_decision=True)

        regenerated = self.writer.upsert_edge(
            source_node_id=source.id,
            target_node_id=target.id,
            edge_type="related",
            reason="The generator proposed the same relationship again.",
            evidence=["source:3", "source:4"],
            source_note_ids=[3, 4],
        )

        self.assertEqual(regenerated.status, "ignored")
        self.assertEqual(regenerated.semantic_status, "quarantined")


if __name__ == "__main__":
    unittest.main()
