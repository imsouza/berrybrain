import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import berrybrain_api.models  # noqa: F401
from berrybrain_api.database import Base
from berrybrain_api.models import (
    ConceptRecord,
    ConnectionRecord,
    GraphEdgeRecord,
    GraphNodeRecord,
    NoteRecord,
)
from berrybrain_api.services import (
    build_graph,
    graph_quality_report,
    sync_knowledge_graph,
)


class GraphQualityReportTest(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite://")
        Base.metadata.create_all(self.engine)
        self.session = sessionmaker(bind=self.engine)()

    def tearDown(self) -> None:
        self.session.close()
        self.engine.dispose()

    def test_report_detects_structural_quality_problems(self) -> None:
        hub = GraphNodeRecord(type="concept", label="Hub", created_by="system")
        duplicate_a = GraphNodeRecord(type="concept", label="Telemetry")
        duplicate_b = GraphNodeRecord(type="concept", label=" telemetry ")
        generic = GraphNodeRecord(type="topic", label="General")
        cluster = GraphNodeRecord(type="cluster", label="Unstable cluster")
        leaves = [
            GraphNodeRecord(type="concept", label=f"Leaf {index}") for index in range(9)
        ]
        for node in [hub, duplicate_a, duplicate_b, generic, cluster, *leaves]:
            node.quality_gate_status = "passed"
        self.session.add_all([hub, duplicate_a, duplicate_b, generic, cluster, *leaves])
        self.session.flush()
        for leaf in leaves:
            self.session.add(
                GraphEdgeRecord(
                    source_node_id=hub.id,
                    target_node_id=leaf.id,
                    type="semantic_relation",
                    reason="Fixture relation",
                    evidence='["fixture"]',
                    quality_gate_status="passed",
                )
            )
        self.session.add_all(
            [
                GraphEdgeRecord(
                    source_node_id=duplicate_a.id,
                    target_node_id=duplicate_b.id,
                    type="shared_concept",
                    reason="",
                    evidence="[]",
                    quality_gate_status="passed",
                ),
                GraphEdgeRecord(
                    source_node_id=duplicate_b.id,
                    target_node_id=duplicate_a.id,
                    type="semantic_similarity",
                    reason="Duplicate direction",
                    evidence='["fixture"]',
                    quality_gate_status="passed",
                ),
            ]
        )
        self.session.commit()

        report = graph_quality_report(self.session)

        self.assertGreaterEqual(report["issueCounts"]["orphans"], 2)
        self.assertEqual(report["issueCounts"]["duplicateNodes"], 1)
        self.assertEqual(report["issueCounts"]["duplicateEdges"], 1)
        self.assertEqual(report["issueCounts"]["artificialHubs"], 1)
        self.assertEqual(report["issueCounts"]["genericNodes"], 1)
        self.assertEqual(report["issueCounts"]["edgesWithoutEvidence"], 1)
        self.assertEqual(report["issueCounts"]["unstableClusters"], 1)
        self.assertEqual(len(report["issues"]["mergeSuggestions"]), 1)

    def test_graph_projection_is_read_only(self) -> None:
        self.session.add_all(
            [
                GraphNodeRecord(
                    type="concept", label="Duplicate", quality_gate_status="passed"
                ),
                GraphNodeRecord(
                    type="concept", label=" duplicate ", quality_gate_status="passed"
                ),
            ]
        )
        self.session.commit()

        projected = build_graph(self.session)

        self.assertEqual(projected["stats"]["node_count"], 2)
        self.assertEqual(self.session.query(GraphNodeRecord).count(), 2)

    def test_semantic_audit_preserves_zero_but_invalidates_retyped_measurements(self):
        from berrybrain_api.confidence import persist_judge_confidence
        from berrybrain_api.graph_semantic_service import audit_graph_semantics

        source = GraphNodeRecord(type="concept", label="Telemetry")
        target = GraphNodeRecord(type="concept", label="Observability")
        self.session.add_all([source, target])
        self.session.flush()
        edge = GraphEdgeRecord(
            source_node_id=source.id, target_node_id=target.id, type="related"
        )
        self.session.add(edge)
        self.session.flush()
        persist_judge_confidence(source, 0.0)
        persist_judge_confidence(edge, 0.8)
        self.session.commit()

        audit_graph_semantics(self.session, apply=True)
        self.assertEqual(source.confidence, 0.0)
        self.assertEqual(source.confidence_sample_size, 1)
        self.assertEqual(edge.confidence, 0.8)

        edge.type = "semantic_relation"
        self.session.commit()
        audit_graph_semantics(self.session, apply=True)
        self.assertEqual(edge.type, "related")
        self.assertEqual(edge.confidence_sample_size, 0)

    def test_legacy_projection_and_sync_preserve_relationship_evidence(self) -> None:
        source = NoteRecord(
            title="Source note",
            slug="source-note",
            path="research/source.md",
            content="Source evidence.",
            content_hash="source-v1",
            status="active",
        )
        target = NoteRecord(
            title="Target note",
            slug="target-note",
            path="target.md",
            content="Target evidence.",
            content_hash="target-v1",
            status="active",
        )
        orphan = NoteRecord(
            title="Orphan note",
            slug="orphan-note",
            path="orphan.md",
            content="Unconnected evidence.",
            content_hash="orphan-v1",
            status="active",
        )
        self.session.add_all([source, target, orphan])
        self.session.flush()
        self.session.add(
            ConnectionRecord(
                source_note_id=source.id,
                target_note_id=target.id,
                connection_type="supports",
                confidence=80,
                reason="The source supports the target.",
                evidence='["source excerpt"]',
                created_by="ai",
                status="confirmed",
            )
        )
        self.session.add(
            ConceptRecord(
                name="Trace context",
                normalized_name="trace context",
                description="Context propagated through a request.",
                related_note_ids=f"[{source.id}]",
                source_evidence='["source excerpt"]',
                confidence=0.8,
                status="confirmed",
            )
        )
        self.session.commit()

        fallback = build_graph(self.session)
        self.assertEqual(fallback["stats"]["node_count"], 3)
        self.assertEqual(fallback["stats"]["edge_count"], 1)
        self.assertEqual(fallback["stats"]["orphan_count"], 1)
        self.assertEqual(fallback["nodes"][0]["folder"], "research")
        self.assertEqual(fallback["edges"][0]["type"], "supports")

        synced = sync_knowledge_graph(self.session)
        self.assertEqual(synced, {"nodes": 4, "edges_added": 1})
        projection = build_graph(self.session)
        self.assertEqual(projection["stats"]["node_count"], 4)
        self.assertEqual(projection["stats"]["edge_count"], 1)
        edge = self.session.query(GraphEdgeRecord).one()
        self.assertEqual(edge.type, "supports")
        self.assertEqual(edge.status, "confirmed")
        # Legacy scalars without observations must not become new model evidence.
        self.assertEqual(edge.confidence_sample_size, 0)
        self.assertEqual(edge.confidence_method, "unavailable")
        self.assertIn("source excerpt", edge.evidence)


if __name__ == "__main__":
    unittest.main()
