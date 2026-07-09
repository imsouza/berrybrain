import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from berrybrain_api.database import Base
from berrybrain_api.models import ConceptRecord, ConnectionRecord, NoteRecord


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
                name="observabilidade",
                normalized_name="observabilidade",
                description="Monitoramento de sistemas.",
            )
        )
        self.session.commit()

        from berrybrain_api.home_summary import list_detected_concepts

        concepts = list_detected_concepts(self.session, limit=5)

        self.assertEqual(concepts[0]["name"], "observabilidade")
        self.assertEqual(concepts[0]["normalizedName"], "observabilidade")
        self.assertEqual(concepts[0]["frequency"], 1)

    def test_recent_connections_list_resolves_source_and_target_notes(self) -> None:
        source = NoteRecord(
            title="Observabilidade",
            slug="observabilidade",
            path="estudos/observabilidade.md",
            content_hash="a",
        )
        target = NoteRecord(
            title="Edge Computing",
            slug="edge-computing",
            path="estudos/edge-computing.md",
            content_hash="b",
        )
        self.session.add_all([source, target])
        self.session.flush()
        self.session.add(
            ConnectionRecord(
                source_note_id=source.id,
                target_note_id=target.id,
                connection_type="semantic",
                confidence=82,
                reason="Ambas tratam de sistemas descentralizados.",
                created_by="ai",
            )
        )
        self.session.commit()

        from berrybrain_api.home_summary import list_recent_connections

        connections = list_recent_connections(self.session, limit=5)

        self.assertEqual(connections[0]["type"], "semantic")
        self.assertEqual(connections[0]["confidencePercent"], 82)
        self.assertEqual(connections[0]["source"]["title"], "Observabilidade")
        self.assertEqual(connections[0]["target"]["title"], "Edge Computing")


if __name__ == "__main__":
    unittest.main()
