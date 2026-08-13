import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from berrybrain_api.database import Base
from berrybrain_api.models import ConceptRecord, ConnectionRecord, NoteRecord
from berrybrain_api.services import audit_connection_confidence, create_connection


class HomeListServicesTest(unittest.TestCase):
    def setUp(self) -> None:
        engine = create_engine(
            "sqlite:///:memory:", connect_args={"check_same_thread": False}
        )
        Base.metadata.create_all(bind=engine)
        self.session = sessionmaker(bind=engine)()

    def tearDown(self) -> None:
        self.session.close()

    def test_detected_concepts_list_uses_real_concept_records(self) -> None:
        self.session.add(
            ConceptRecord(
                name="observability",
                normalized_name="observability",
                description="Monitoring of distributed systems.",
            )
        )
        self.session.commit()

        from berrybrain_api.home_summary import list_detected_concepts

        concepts = list_detected_concepts(self.session, limit=5)

        self.assertEqual(concepts[0]["name"], "observability")
        self.assertEqual(concepts[0]["normalizedName"], "observability")
        self.assertEqual(concepts[0]["frequency"], 1)

    def test_recent_connections_list_resolves_source_and_target_notes(self) -> None:
        source = NoteRecord(
            title="Observability",
            slug="observability",
            path="study/observability.md",
            content_hash="a",
        )
        target = NoteRecord(
            title="Edge Computing",
            slug="edge-computing",
            path="study/edge-computing.md",
            content_hash="b",
        )
        self.session.add_all([source, target])
        self.session.flush()
        connection = create_connection(
            self.session,
            source_note_id=source.id,
            target_note_id=target.id,
            connection_type="semantic",
            reason="Both cover decentralized systems.",
            evidence=["Decentralized systems use edge nodes."],
            created_by="system",
        )

        from berrybrain_api.home_summary import list_recent_connections

        connections = list_recent_connections(self.session, limit=5)

        self.assertEqual(connections[0]["type"], "semantic")
        self.assertEqual(connections[0]["confidencePercent"], connection.confidence)
        interval = connections[0]["confidenceInterval"]
        self.assertEqual(interval["sampleSize"], 2)
        self.assertEqual(interval["method"], "jeffreys-wilson-evidence-v2")
        self.assertLess(interval["lower"], interval["score"])
        self.assertGreater(interval["upper"], interval["score"])
        self.assertEqual(connections[0]["source"]["title"], "Observability")
        self.assertEqual(connections[0]["target"]["title"], "Edge Computing")

    def test_legacy_connection_confidence_backfill_is_calculated_and_idempotent(
        self,
    ) -> None:
        connection = ConnectionRecord(
            source_note_id=1,
            target_note_id=2,
            connection_type="semantic",
            confidence=91,
            reason="Both notes cover distributed tracing.",
            evidence='["Distributed tracing links service spans."]',
            created_by="ai",
        )
        self.session.add(connection)
        self.session.commit()

        preview = audit_connection_confidence(self.session)
        applied = audit_connection_confidence(self.session, apply=True)
        self.session.commit()
        repeated = audit_connection_confidence(self.session, apply=True)

        self.assertEqual(preview["pending"], 1)
        self.assertEqual(applied["recalculated"], 1)
        self.assertEqual(connection.confidence_method, "jeffreys-wilson-evidence-v2")
        self.assertEqual(connection.confidence_sample_size, 2)
        self.assertIsNotNone(connection.confidence_updated_at)
        self.assertNotEqual(connection.confidence, 91)
        self.assertEqual(repeated["pending"], 0)
        self.assertEqual(repeated["recalculated"], 0)


if __name__ == "__main__":
    unittest.main()
