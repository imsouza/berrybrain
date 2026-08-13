from __future__ import annotations

import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from berrybrain_api.database import Base
from berrybrain_api.graph_invalidation import (
    collect_node_deletion_impact,
    invalidate_dependent_insights,
)
from berrybrain_api.graph_write_service import GraphWriteService
from berrybrain_api.models import (
    GraphEdgeRecord,
    GraphNodeRecord,
    InsightRecord,
    SemanticClusterAssignmentRecord,
    SemanticProfileRecord,
)


class GraphInvalidationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.session = sessionmaker(bind=self.engine)()

    def tearDown(self) -> None:
        self.session.close()
        self.engine.dispose()

    def test_node_deletion_invalidates_incident_insight_and_blocks_regeneration(self):
        insight = InsightRecord(
            type="new_connection",
            title="Unrelated sources share Skip",
            description="An invalid relationship created from navigation text.",
            related_notes="[1, 2]",
            evidence='["Skip to content", "Skip to main content"]',
            status="suggested",
        )
        self.session.add(insight)
        self.session.flush()
        source = GraphNodeRecord(
            type="concept",
            label="Skip",
            source_note_ids="[1, 2]",
            source_evidence='["Skip to content", "Skip to main content"]',
            cluster_id=7,
        )
        neighbor = GraphNodeRecord(
            type="concept",
            label="Modern game patch",
            source_note_ids="[2]",
            source_evidence='["Modern game patch"]',
            cluster_id=7,
        )
        insight_node = GraphNodeRecord(
            type="insight",
            label=insight.title,
            source="insight",
            source_id=insight.id,
            source_note_ids="[1, 2]",
            source_evidence=insight.evidence,
            cluster_id=7,
        )
        self.session.add_all([source, neighbor, insight_node])
        self.session.flush()
        self.session.add_all(
            [
                GraphEdgeRecord(
                    source_node_id=source.id,
                    target_node_id=neighbor.id,
                    type="related",
                    source_note_ids="[1, 2]",
                ),
                GraphEdgeRecord(
                    source_node_id=insight_node.id,
                    target_node_id=source.id,
                    type="derived_from",
                    source_note_ids="[1, 2]",
                ),
                SemanticClusterAssignmentRecord(
                    node_id=source.id,
                    cluster_id=7,
                ),
                SemanticProfileRecord(
                    node_id=source.id,
                    source_fingerprint="skip-source",
                    profile_json="{}",
                ),
            ]
        )
        self.session.commit()
        source_id = source.id
        neighbor_id = neighbor.id
        insight_node_id = insight_node.id

        impact = collect_node_deletion_impact(self.session, source)
        invalidated = invalidate_dependent_insights(
            self.session,
            impact,
            primary_node_id=source.id,
        )
        GraphWriteService(self.session, autocommit=False).delete_node(
            source.id,
            user_decision=True,
        )
        self.session.commit()

        self.assertEqual(invalidated, 1)
        self.assertIn(neighbor_id, impact.cluster_scope_node_ids)
        self.assertNotIn(insight_node_id, impact.cluster_scope_node_ids)
        self.assertEqual(impact.incident_edge_count, 2)
        self.assertIsNone(self.session.get(GraphNodeRecord, source_id))
        self.assertIsNone(self.session.get(GraphNodeRecord, insight_node_id))
        self.assertIsNotNone(self.session.get(GraphNodeRecord, neighbor_id))
        self.assertEqual(self.session.get(InsightRecord, insight.id).status, "expired")
        self.assertIsNone(
            self.session.query(SemanticClusterAssignmentRecord)
            .filter_by(node_id=source_id)
            .one_or_none()
        )
        self.assertIsNone(
            self.session.query(SemanticProfileRecord)
            .filter_by(node_id=source_id)
            .one_or_none()
        )

        regenerated = GraphWriteService(self.session).upsert_node(
            node_type="concept",
            label="Skip",
            source="concept_extraction",
            source_note_ids=[1, 2],
            source_evidence=["Skip to content", "Skip to main content"],
            status="suggested",
        )
        self.assertEqual(regenerated.status, "ignored")
        self.assertEqual(regenerated.semantic_status, "quarantined")


if __name__ == "__main__":
    unittest.main()
