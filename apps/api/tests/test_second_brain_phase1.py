import json
import asyncio
import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from berrybrain_api.database import Base
from berrybrain_api.generated_metadata import upsert_generated_metadata
from berrybrain_api.models import (
    ConceptRecord,
    ConnectionRecord,
    GraphEdgeRecord,
    GraphNodeRecord,
    InsightRecord,
    NoteRecord,
)


class SecondBrainPhase1Test(unittest.TestCase):
    def setUp(self) -> None:
        engine = create_engine(
            "sqlite:///:memory:", connect_args={"check_same_thread": False}
        )
        Base.metadata.create_all(bind=engine)
        self.session = sessionmaker(bind=engine)()

    def tearDown(self) -> None:
        self.session.close()

    def test_expand_knowledge_graph_persists_explainable_nodes_and_edges(self) -> None:
        source = NoteRecord(
            title="Observabilidade em Sistemas Distribuidos",
            slug="observabilidade",
            path="estudos/observabilidade.md",
            content_hash="hash-a",
            links=json.dumps(["Edge Computing"]),
        )
        target = NoteRecord(
            title="Edge Computing",
            slug="edge-computing",
            path="estudos/edge-computing.md",
            content_hash="hash-b",
        )
        self.session.add_all([source, target])
        self.session.flush()

        upsert_generated_metadata(
            self.session,
            source.id,
            "concepts",
            {
                "concepts": [
                    "observabilidade",
                    "sistemas distribuidos",
                    "logs metricas traces",
                ]
            },
            "hash-a",
            model_used="nvidia/nemotron",
        )
        upsert_generated_metadata(
            self.session,
            target.id,
            "concepts",
            {"concepts": ["sistemas distribuidos"]},
            "hash-b",
            model_used="nvidia/nemotron",
        )

        from berrybrain_api.second_brain import expand_knowledge_graph

        result = expand_knowledge_graph(self.session)

        concepts = self.session.query(ConceptRecord).all()
        nodes = self.session.query(GraphNodeRecord).all()
        edges = self.session.query(GraphEdgeRecord).all()
        connections = self.session.query(ConnectionRecord).all()
        backlink = next(c for c in connections if c.connection_type == "backlink")

        self.assertGreaterEqual(result["concepts"], 3)
        self.assertTrue(any(c.name == "observabilidade" for c in concepts))
        self.assertTrue(any(n.type == "concept" for n in nodes))
        self.assertTrue(any(e.type == "shared_concept" for e in edges))
        self.assertTrue(any(c.connection_type == "shared_concept" for c in connections))
        self.assertEqual(backlink.status, "confirmed")
        self.assertIn("Edge Computing", backlink.evidence)

    def test_graph_inference_uses_evidence_and_refuses_unsupported_claims(self) -> None:
        note_a = NoteRecord(
            title="Observabilidade",
            slug="observabilidade",
            path="obs.md",
            content_hash="a",
        )
        note_b = NoteRecord(
            title="Edge Computing",
            slug="edge",
            path="edge.md",
            content_hash="b",
        )
        self.session.add_all([note_a, note_b])
        self.session.flush()
        self.session.add(
            ConnectionRecord(
                source_note_id=note_a.id,
                target_note_id=note_b.id,
                connection_type="semantic_similarity",
                confidence=84,
                reason="Ambas tratam de sistemas descentralizados e monitoramento.",
                evidence=json.dumps(["Observabilidade", "Edge Computing"]),
                created_by="ai",
                provider="nvidia-nim",
                model="nvidia/nemotron",
            )
        )
        self.session.commit()

        from berrybrain_api.second_brain import infer_from_graph

        supported = infer_from_graph(
            self.session, "o que edge computing tem a ver com observabilidade?"
        )
        unsupported = infer_from_graph(self.session, "qual relacao com culinaria?")

        self.assertEqual(supported["status"], "answered")
        self.assertGreaterEqual(len(supported["evidence"]), 1)
        self.assertIn("Observabilidade", supported["relatedNodes"])
        self.assertEqual(unsupported["status"], "insufficient_evidence")

    def test_connection_status_can_be_confirmed_and_ignored(self) -> None:
        note_a = NoteRecord(
            title="A",
            slug="a",
            path="a.md",
            content_hash="a",
        )
        note_b = NoteRecord(
            title="B",
            slug="b",
            path="b.md",
            content_hash="b",
        )
        self.session.add_all([note_a, note_b])
        self.session.flush()
        connection = ConnectionRecord(
            source_note_id=note_a.id,
            target_note_id=note_b.id,
            connection_type="shared_concept",
            reason="Compartilham um conceito real.",
            evidence=json.dumps(["conceito"]),
            status="suggested",
        )
        self.session.add(connection)
        self.session.commit()

        from berrybrain_api.services import set_connection_status

        confirmed = set_connection_status(self.session, connection.id, "confirmed")
        confirmed_status = confirmed.status
        ignored = set_connection_status(self.session, connection.id, "ignored")

        self.assertEqual(confirmed_status, "confirmed")
        self.assertEqual(ignored.status, "ignored")

    def test_graph_inference_calls_configured_ai_with_graph_context(self) -> None:
        note = NoteRecord(
            title="Regressão Linear",
            slug="regressao-linear",
            path="regressao.md",
            content_hash="r",
        )
        self.session.add(note)
        self.session.flush()
        node = GraphNodeRecord(
            type="note",
            label="Regressão Linear",
            title="Regressão Linear",
            summary="Nota sobre regressão linear e modelos estatísticos.",
            source_id=note.id,
            source_note_ids=json.dumps([note.id]),
            status="confirmed",
        )
        self.session.add(node)
        self.session.commit()

        from berrybrain_api import second_brain

        called = {}

        async def fake_generate(config, prompt, system, timeout=90):
            called["prompt"] = prompt
            return {
                "status": "answered",
                "answer": "Regressão Linear aparece como nó do grafo.",
                "evidence": ["Regressão Linear"],
                "relatedNodes": ["Regressão Linear"],
                "suggestions": [],
            }

        original = second_brain.generate_graph_answer
        second_brain.generate_graph_answer = fake_generate
        try:
            result = asyncio.run(
                second_brain.infer_from_graph_with_ai(
                    self.session, "quais notas falam desse modelo estatístico?"
                )
            )
        finally:
            second_brain.generate_graph_answer = original

        self.assertEqual(result["status"], "answered")
        self.assertIn("graphContext", called["prompt"])
        self.assertIn("Regressão Linear", called["prompt"])

    def test_expand_generates_graph_insights_and_manual_node_notes(self) -> None:
        note_a = NoteRecord(title="ML A", slug="ml-a", path="ml-a.md", content_hash="a")
        note_b = NoteRecord(title="ML B", slug="ml-b", path="ml-b.md", content_hash="b")
        self.session.add_all([note_a, note_b])
        self.session.flush()
        upsert_generated_metadata(
            self.session,
            note_a.id,
            "concepts",
            {"concepts": ["machine learning"]},
            "a",
            model_used="test-model",
        )
        upsert_generated_metadata(
            self.session,
            note_b.id,
            "concepts",
            {"concepts": ["machine learning"]},
            "b",
            model_used="test-model",
        )

        self.session.add(
            InsightRecord(
                type="hypothesis",
                title="Machine learning notes can become a study path",
                description=(
                    "ML A and ML B both discuss machine learning and can be "
                    "organized as a connected study path instead of isolated notes."
                ),
                why_it_matters=(
                    "This helps the learner consolidate repeated concepts and decide "
                    "which note should become the central entry point."
                ),
                suggested_action=(
                    "Create a permanent machine learning overview note that links ML A "
                    "and ML B."
                ),
                graph_impact=(
                    "Adds an insight node connected to both source notes and clarifies "
                    "their shared learning context."
                ),
                related_notes=json.dumps([note_a.id, note_b.id]),
                evidence=json.dumps(
                    [
                        "ML A mentions machine learning.",
                        "ML B mentions machine learning.",
                    ]
                ),
                confidence=0.8,
                status="suggested",
                provider="nvidia-nim",
                model="qwen/qwen3.5",
            )
        )
        self.session.commit()

        from berrybrain_api.second_brain import (
            expand_knowledge_graph,
            set_node_user_notes,
        )

        result = expand_knowledge_graph(self.session)
        node = self.session.query(GraphNodeRecord).filter_by(type="insight").first()
        updated = set_node_user_notes(self.session, node.id, "Minha nota manual")

        self.assertEqual(result["insights"], 0)
        self.assertIsNotNone(node)
        self.assertEqual(node.created_by_model, "qwen/qwen3.5")
        self.assertEqual(updated.user_notes, "Minha nota manual")

    def test_expand_ignores_generic_note_type_and_path_slug_topics(self) -> None:
        note = NoteRecord(
            title="Docker Essentials",
            slug="docker-essentials",
            path="permanentes/docker-essentials.md",
            content_hash="docker",
        )
        self.session.add(note)
        self.session.flush()
        upsert_generated_metadata(
            self.session,
            note.id,
            "classification",
            {
                "note_type": "study",
                "topics": ["permanentes/docker-essentials", "containers"],
                "tags": ["docker-essentials"],
            },
            "docker",
            model_used="qwen3:14b",
        )

        from berrybrain_api.second_brain import expand_knowledge_graph

        expand_knowledge_graph(self.session)
        topics = [
            node.label
            for node in self.session.query(GraphNodeRecord)
            .filter_by(type="topico")
            .all()
        ]

        self.assertEqual(topics, ["containers"])

    def test_expand_merges_duplicate_note_nodes_by_source_id(self) -> None:
        note = NoteRecord(
            title="Python Async Patterns",
            slug="python-async-patterns",
            path="inbox/python-async-patterns.md",
            content_hash="a",
        )
        self.session.add(note)
        self.session.flush()
        n1 = GraphNodeRecord(type="note", label=note.title, source_id=note.id)
        n2 = GraphNodeRecord(type="note", label=note.title, source_id=note.id)
        concept = GraphNodeRecord(type="concept", label="Async", source_id=99)
        self.session.add_all([n1, n2, concept])
        self.session.flush()
        self.session.add_all(
            [
                GraphEdgeRecord(
                    source_node_id=n1.id,
                    target_node_id=concept.id,
                    type="shared_concept",
                    reason="A",
                    evidence=json.dumps(["A"]),
                ),
                GraphEdgeRecord(
                    source_node_id=n2.id,
                    target_node_id=concept.id,
                    type="shared_concept",
                    reason="B",
                    evidence=json.dumps(["B"]),
                ),
            ]
        )
        self.session.commit()

        from berrybrain_api.second_brain import expand_knowledge_graph

        expand_knowledge_graph(self.session)

        note_nodes = self.session.query(GraphNodeRecord).filter_by(type="note").all()
        edges = self.session.query(GraphEdgeRecord).all()
        edge_keys = [
            (edge.source_node_id, edge.target_node_id, edge.type) for edge in edges
        ]

        self.assertEqual(len(note_nodes), 1)
        self.assertEqual(len(edge_keys), len(set(edge_keys)))
        self.assertTrue(
            any(
                edge.source_node_id == note_nodes[0].id
                and edge.target_node_id == concept.id
                and edge.type == "shared_concept"
                for edge in edges
            )
        )

    def test_expand_does_not_duplicate_note_title_slug_and_path_as_concepts(
        self,
    ) -> None:
        note = NoteRecord(
            title="Docker Essentials",
            slug="docker-essentials",
            path="permanentes/docker-essentials.md",
            content_hash="docker",
            links=json.dumps(["permanentes/docker-essentials"]),
        )
        self.session.add(note)
        self.session.flush()
        upsert_generated_metadata(
            self.session,
            note.id,
            "classification",
            {
                "concepts": ["docker essentials"],
                "topics": ["docker essentials"],
                "tags": ["docker-essentials"],
            },
            "docker",
            model_used="gemma3:4b",
        )
        upsert_generated_metadata(
            self.session,
            note.id,
            "concepts",
            {"concepts": ["docker-essentials"]},
            "docker",
            model_used="qwen/qwen3.5-397b-a17b",
        )

        from berrybrain_api.second_brain import expand_knowledge_graph

        expand_knowledge_graph(self.session)

        docker_concepts = [
            n
            for n in self.session.query(GraphNodeRecord).filter_by(type="concept").all()
            if "docker" in n.label.lower()
        ]
        note_nodes = self.session.query(GraphNodeRecord).filter_by(type="note").all()
        duplicate_title_nodes = [
            n
            for n in self.session.query(GraphNodeRecord).all()
            if n.type != "note" and n.label.lower() == "docker essentials"
        ]

        self.assertEqual(len(note_nodes), 1)
        self.assertEqual(docker_concepts, [])
        self.assertEqual(duplicate_title_nodes, [])


if __name__ == "__main__":
    unittest.main()
