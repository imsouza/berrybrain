import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import berrybrain_api.models  # noqa: F401
from berrybrain_api.database import Base
from berrybrain_api.models import GraphEdgeRecord, GraphNodeRecord
from berrybrain_api.services import build_graph, graph_quality_report


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
                ),
                GraphEdgeRecord(
                    source_node_id=duplicate_b.id,
                    target_node_id=duplicate_a.id,
                    type="semantic_similarity",
                    reason="Duplicate direction",
                    evidence='["fixture"]',
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
                GraphNodeRecord(type="concept", label="Duplicate"),
                GraphNodeRecord(type="concept", label=" duplicate "),
            ]
        )
        self.session.commit()

        projected = build_graph(self.session)

        self.assertEqual(projected["stats"]["node_count"], 2)
        self.assertEqual(self.session.query(GraphNodeRecord).count(), 2)


if __name__ == "__main__":
    unittest.main()
