import unittest

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from berrybrain_api.database import Base
from berrybrain_api.models import (
    GraphEdgeRecord,
    GraphNodeRecord,
    InsightRecord,
    JobRecord,
)
from berrybrain_api.routers.maintenance import (
    _cleanup_duplicate_jobs,
    _cleanup_legacy_insights,
    _validate_graph,
)


class MaintenanceTest(unittest.TestCase):
    def setUp(self) -> None:
        engine = create_engine(
            "sqlite:///:memory:", connect_args={"check_same_thread": False}
        )
        Base.metadata.create_all(bind=engine)
        self.session = sessionmaker(bind=engine)()

    def tearDown(self) -> None:
        self.session.close()

    def test_cleanup_legacy_insights_archives_system_diagnostics(self) -> None:
        insight = InsightRecord(
            type="system_diagnostic",
            title="Pipeline Bottleneck in Note Titling Prevents Graph Connectivity",
            description="jobsByType.GENERATE_NOTE_TITLE backlog",
            evidence='["semantic_data", "graphSummary"]',
            status="suggested",
        )
        self.session.add(insight)
        self.session.commit()
        node = GraphNodeRecord(
            type="insight",
            label=insight.title,
            title=insight.title,
            source="insight",
            source_id=insight.id,
            ai_context="This is a pipeline bottleneck diagnostic.",
            status="suggested",
        )
        note = GraphNodeRecord(type="note", label="Rascunho", status="confirmed")
        self.session.add_all([node, note])
        self.session.commit()
        edge = GraphEdgeRecord(
            source_node_id=node.id,
            target_node_id=note.id,
            type="insight_evidence",
            reason="semantic_data",
            evidence='["semantic_data"]',
            status="confirmed",
        )
        self.session.add(edge)
        self.session.commit()

        result = _cleanup_legacy_insights(self.session)

        self.assertEqual(result["archivedInsights"], 1)
        self.assertEqual(result["ignoredInsightNodes"], 1)
        self.assertEqual(result["ignoredEdges"], 1)
        self.session.refresh(insight)
        self.session.refresh(node)
        self.session.refresh(edge)
        self.assertEqual(insight.status, "archived")
        self.assertEqual(node.status, "ignored")
        self.assertEqual(edge.status, "ignored")

    def test_validate_graph_handles_orphan_self_and_duplicate_edges(self) -> None:
        a = GraphNodeRecord(type="note", label="A", status="confirmed")
        b = GraphNodeRecord(type="note", label="B", status="confirmed")
        self.session.add_all([a, b])
        self.session.commit()
        self.session.add_all(
            [
                GraphEdgeRecord(
                    source_node_id=a.id, target_node_id=9999, type="related"
                ),
                GraphEdgeRecord(
                    source_node_id=a.id, target_node_id=a.id, type="related"
                ),
                GraphEdgeRecord(
                    source_node_id=a.id, target_node_id=b.id, type="related"
                ),
                GraphEdgeRecord(
                    source_node_id=b.id, target_node_id=a.id, type="related"
                ),
            ]
        )
        self.session.commit()

        result = _validate_graph(self.session)
        edges = list(self.session.execute(select(GraphEdgeRecord)).scalars())

        self.assertEqual(result["deletedOrphanEdges"], 1)
        self.assertEqual(result["ignoredSelfEdges"], 1)
        self.assertEqual(result["ignoredDuplicateEdges"], 1)
        self.assertEqual(len(edges), 3)
        self.assertEqual(sum(1 for edge in edges if edge.status == "ignored"), 2)

    def test_duplicate_active_jobs_are_marked_failed(self) -> None:
        payload = '{"note_path":"inbox/a.md","content_hash":"abc"}'
        self.session.add_all(
            [
                JobRecord(type="PARSE_NOTE", payload=payload, status="pending"),
                JobRecord(type="PARSE_NOTE", payload=payload, status="pending"),
            ]
        )
        self.session.commit()

        result = _cleanup_duplicate_jobs(self.session)
        jobs = list(self.session.execute(select(JobRecord)).scalars())

        self.assertEqual(result["duplicateJobsMarkedFailed"], 1)
        self.assertEqual(sum(1 for job in jobs if job.status == "failed"), 1)


if __name__ == "__main__":
    unittest.main()
