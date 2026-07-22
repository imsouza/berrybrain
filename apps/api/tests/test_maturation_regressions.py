import json
import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from berrybrain_api.database import Base
from berrybrain_api.generated_metadata import upsert_generated_metadata
from berrybrain_api.home_summary import build_home_summary
from berrybrain_api.models import (
    GraphEdgeRecord,
    GraphNodeRecord,
    InsightRecord,
    NoteRecord,
)
from berrybrain_api.second_brain import (
    _extract_content_concepts,
    expand_knowledge_graph,
)
from berrybrain_api.services import build_graph, get_active_insights


class MaturationRegressionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine(
            "sqlite:///:memory:", connect_args={"check_same_thread": False}
        )
        Base.metadata.create_all(bind=self.engine)
        self.session = sessionmaker(bind=self.engine)()

    def tearDown(self) -> None:
        self.session.close()
        self.engine.dispose()

    def test_concept_extraction_does_not_cross_markdown_lines(self) -> None:
        note = NoteRecord(
            title="Temporal Source Alpha",
            content=(
                "# Temporal Source Alpha\n\n"
                "## Temporal Coupling Fixture\n\n"
                "This paragraph starts on another line."
            ),
        )

        concepts = _extract_content_concepts(note)

        self.assertIn("Temporal Coupling Fixture", concepts)
        self.assertNotIn("Temporal Coupling Fixture This", concepts)

    def test_realistic_vault_builds_explainable_graph_edges(self) -> None:
        notes = [
            (
                "Docker Essentials",
                "permanentes/docker.md",
                ["docker", "containers", "linux"],
            ),
            (
                "Linux Shell Scripting",
                "permanentes/linux.md",
                ["linux", "automation", "shell"],
            ),
            (
                "Python Async Patterns",
                "inbox/python-async.md",
                ["python", "async", "automation"],
            ),
            (
                "Kubernetes Basics",
                "permanentes/kubernetes.md",
                ["kubernetes", "containers", "orchestration"],
            ),
            (
                "Observability Signals",
                "permanentes/observability.md",
                ["observability", "metrics", "traces"],
            ),
            (
                "Edge Computing",
                "permanentes/edge.md",
                ["edge computing", "latency", "distributed systems"],
            ),
            (
                "RAG Embeddings",
                "permanentes/rag.md",
                ["rag", "embeddings", "retrieval"],
            ),
            (
                "Vector Databases",
                "permanentes/vector-db.md",
                ["embeddings", "retrieval", "vector database"],
            ),
            ("NVIDIA NIM", "permanentes/nim.md", ["nvidia nim", "llm", "inference"]),
            (
                "Knowledge Graphs",
                "permanentes/kg.md",
                ["knowledge graph", "entities", "connections"],
            ),
        ]
        for title, path, concepts in notes:
            note = NoteRecord(
                title=title,
                slug=path.removesuffix(".md").split("/")[-1],
                path=path,
                content=f"# {title}\n\n" + " ".join(concepts),
                content_hash=path,
            )
            self.session.add(note)
            self.session.flush()
            upsert_generated_metadata(
                self.session,
                note.id,
                "concepts",
                {"concepts": concepts},
                note.content_hash,
                model_used="test-fixture",
            )
        self.session.commit()

        result = expand_knowledge_graph(self.session)
        graph = build_graph(self.session)

        self.assertEqual(result["notes"], 10)
        self.assertGreaterEqual(graph["stats"]["node_count"], 10)
        self.assertGreaterEqual(graph["stats"]["edge_count"], 8)
        for edge in graph["edges"]:
            self.assertTrue(edge["reason"])
            self.assertTrue(edge["evidence"])
            self.assertIsNotNone(edge["confidence"])
            self.assertTrue(edge["status"])
            self.assertTrue(edge["provider"])
            self.assertTrue(edge["model"])
        for node in self.session.query(GraphNodeRecord).all():
            self.assertTrue(node.ai_summary, node.label)
            self.assertTrue(node.ai_context, node.label)
            self.assertTrue(node.source_evidence, node.label)
            self.assertTrue(node.provider, node.label)
            self.assertTrue(node.model, node.label)
            self.assertTrue(node.prompt_version, node.label)

    def test_technical_insights_are_hidden_from_home_insights_and_graph(self) -> None:
        source_notes = [
            NoteRecord(
                title="Docker Essentials",
                slug="docker-essentials",
                path="docker.md",
                content_hash="docker",
            ),
            NoteRecord(
                title="Linux Shell Scripting",
                slug="linux-shell-scripting",
                path="shell.md",
                content_hash="shell",
            ),
        ]
        self.session.add_all(source_notes)
        self.session.flush()
        technical = InsightRecord(
            type="system_diagnostic",
            title="Pipeline Bottleneck in GENERATE_NOTE_TITLE",
            description="jobsByType.GENERATE_NOTE_TITLE backlog from raw JSON.",
            evidence=json.dumps(["semantic_data", "graphSummary"]),
            status="suggested",
            priority=10,
        )
        knowledge = InsightRecord(
            type="hypothesis",
            title="Docker and shell form an automation foundation",
            description="Docker and shell scripting reinforce local automation workflows.",
            why_it_matters="This helps decide which practical systems notes should be studied together.",
            suggested_action="Create a bridge note about Docker plus shell automation.",
            graph_impact="Connects Docker and Linux Shell notes through a learning insight.",
            related_notes=json.dumps([note.id for note in source_notes]),
            evidence=json.dumps(["Docker Essentials", "Linux Shell Scripting"]),
            status="suggested",
            priority=8,
            confidence=0.84,
            provider="nvidia-nim",
            model="qwen/qwen3.5-397b-a17b",
        )
        self.session.add_all([technical, knowledge])
        self.session.commit()
        node = GraphNodeRecord(
            type="insight",
            label=technical.title,
            title=technical.title,
            summary=technical.description,
            source="insight",
            source_id=technical.id,
            source_evidence=json.dumps(["semantic_data", "graphSummary"]),
            status="suggested",
        )
        note = GraphNodeRecord(
            type="note", label="Docker Essentials", status="confirmed"
        )
        self.session.add_all([node, note])
        self.session.commit()
        self.session.add(
            GraphEdgeRecord(
                source_node_id=node.id,
                target_node_id=note.id,
                type="insight_evidence",
                reason="Technical diagnostic evidence.",
                evidence=json.dumps(["semantic_data"]),
                status="confirmed",
            )
        )
        self.session.commit()

        active = get_active_insights(self.session)
        home = build_home_summary(self.session)
        graph = build_graph(self.session)

        self.assertEqual([item.title for item in active], [knowledge.title])
        self.assertEqual(
            [item["title"] for item in home["recentInsights"]],
            [knowledge.title],
        )
        self.assertNotIn(technical.title, [node["title"] for node in graph["nodes"]])
        self.assertFalse(graph["edges"])

    def test_reviewed_insight_status_is_mapped_to_graph_status(self) -> None:
        note = NoteRecord(
            title="Distributed tracing",
            slug="distributed-tracing",
            path="distributed-tracing.md",
            content="Distributed tracing connects spans across services.",
            content_hash="distributed-tracing-v1",
        )
        self.session.add(note)
        self.session.flush()
        insight = InsightRecord(
            type="hypothesis",
            title="Tracing exposes cross-service latency",
            description="Distributed tracing reveals latency that local logs cannot explain.",
            why_it_matters="It supports diagnosing system-wide performance failures.",
            suggested_action="Compare traces with service-level logs.",
            graph_impact="Connects tracing evidence to the distributed systems note.",
            related_notes=json.dumps([note.id]),
            evidence=json.dumps(["Distributed tracing", "cross-service latency"]),
            status="accepted",
            priority=8,
            confidence=0.86,
            provider="deterministic",
            model="regression-fixture",
        )
        self.session.add(insight)
        self.session.commit()

        expand_knowledge_graph(self.session)

        graph_node = (
            self.session.query(GraphNodeRecord)
            .filter_by(type="insight", source="insight", source_id=insight.id)
            .one()
        )
        self.assertEqual(graph_node.status, "confirmed")
        self.assertTrue(
            self.session.query(GraphEdgeRecord)
            .filter_by(source_node_id=graph_node.id)
            .count()
        )


if __name__ == "__main__":
    unittest.main()
