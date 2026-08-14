import json
import unittest

from rdflib import RDF, Graph, URIRef
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from berrybrain_api.database import Base
from berrybrain_api.models import GraphEdgeRecord, GraphNodeRecord
from berrybrain_api.ontology_service import (
    BB,
    build_knowledge_graph,
    serialize_knowledge_graph,
    validate_knowledge_graph,
)


class OntologyServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)

    def tearDown(self) -> None:
        self.engine.dispose()

    def test_export_uses_stable_iris_and_auditable_assertions(self) -> None:
        with Session(self.engine) as session:
            note = GraphNodeRecord(type="note", label="Forecast notes")
            topic = GraphNodeRecord(
                type="topic",
                label="Time series",
                created_by="ai",
                quality_gate_status="passed",
                ontology_class="bb:Topic",
            )
            session.add_all((note, topic))
            session.flush()
            edge = GraphEdgeRecord(
                source_node_id=note.id,
                target_node_id=topic.id,
                type="about",
                ontology_property="schema:about",
                quality_gate_status="passed",
            )
            session.add(edge)
            session.commit()

            graph = build_knowledge_graph(session)
            self.assertIn(
                (URIRef(topic.iri), RDF.type, BB.Topic),
                graph,
            )
            self.assertIn(
                (URIRef(edge.iri), RDF.type, BB.Assertion),
                graph,
            )
            payload = json.loads(serialize_knowledge_graph(session))
            self.assertEqual(payload["@context"]["bb"], str(BB))

    def test_valid_graph_conforms_to_shacl(self) -> None:
        with Session(self.engine) as session:
            note = GraphNodeRecord(type="note", label="Forecast notes")
            concept = GraphNodeRecord(
                type="concept",
                label="Autoregression",
                created_by="ai",
                quality_gate_status="passed",
            )
            session.add_all((note, concept))
            session.flush()
            session.add(
                GraphEdgeRecord(
                    source_node_id=note.id,
                    target_node_id=concept.id,
                    type="mentions",
                    quality_gate_status="passed",
                )
            )
            session.commit()

            result = validate_knowledge_graph(session)
            self.assertTrue(result["conforms"], result["violations"])
            self.assertEqual(result["violationCount"], 0)

    def test_insight_without_provenance_fails_shacl(self) -> None:
        with Session(self.engine) as session:
            session.add(
                GraphNodeRecord(
                    type="insight",
                    label="Demand rises after promotions",
                    created_by="ai",
                    quality_gate_status="passed",
                    ontology_class="bb:Insight",
                )
            )
            session.commit()

            result = validate_knowledge_graph(session)
            self.assertFalse(result["conforms"])
            self.assertTrue(
                any("derived-from" in item["message"] for item in result["violations"])
            )

    def test_turtle_round_trip_preserves_direct_relation(self) -> None:
        with Session(self.engine) as session:
            source = GraphNodeRecord(type="concept", label="ARIMA", created_by="user")
            target = GraphNodeRecord(
                type="concept", label="Exponential smoothing", created_by="user"
            )
            session.add_all((source, target))
            session.flush()
            edge = GraphEdgeRecord(
                source_node_id=source.id,
                target_node_id=target.id,
                type="contrasts_with",
                ontology_property="bb:contrastsWith",
                created_by="user",
            )
            session.add(edge)
            session.commit()

            exported = serialize_knowledge_graph(session, output_format="turtle")
            parsed = Graph().parse(data=exported, format="turtle")
            self.assertIn(
                (URIRef(source.iri), BB.contrastsWith, URIRef(target.iri)),
                parsed,
            )


if __name__ == "__main__":
    unittest.main()
