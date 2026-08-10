import unittest
from unittest.mock import patch

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from berrybrain_api.database import Base
from berrybrain_api.models import GraphEdgeRecord, GraphNodeRecord
from berrybrain_api.routers.graph import (
    ReclusterRequest,
    get_graph_delta,
    get_graph_edges_page,
    get_graph_nodes_page,
    recluster_graph,
)


class GraphRuntimeApiTest(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine(
            "sqlite:///:memory:", connect_args={"check_same_thread": False}
        )
        Base.metadata.create_all(bind=self.engine)
        self.factory = sessionmaker(bind=self.engine)
        with self.factory() as session:
            nodes = [
                GraphNodeRecord(type="note", label=f"Note {index}")
                for index in range(3)
            ]
            nodes.append(
                GraphNodeRecord(type="concept", label="Ignored", status="ignored")
            )
            session.add_all(nodes)
            session.flush()
            session.add(
                GraphEdgeRecord(
                    source_node_id=nodes[0].id,
                    target_node_id=nodes[1].id,
                    type="related",
                    label="Related",
                )
            )
            session.commit()

    def tearDown(self) -> None:
        self.engine.dispose()

    def test_nodes_and_edges_are_paginated_without_ignored_records(self) -> None:
        with patch(
            "berrybrain_api.routers.graph.SessionLocal",
            self.factory,
        ):
            first = get_graph_nodes_page(cursor=0, limit=2, types="note")
            second = get_graph_nodes_page(
                cursor=first["nextCursor"],
                limit=2,
                types="note",
            )
            edges = get_graph_edges_page(cursor=0, limit=10, node_ids="")

        self.assertEqual(len(first["nodes"]), 2)
        self.assertIsNotNone(first["nextCursor"])
        self.assertEqual(len(second["nodes"]), 1)
        self.assertIsNone(second["nextCursor"])
        self.assertEqual(len(edges["edges"]), 1)
        self.assertTrue(edges["edges"][0]["source"].startswith("note_"))

    def test_delta_returns_records_newer_than_requested_version(self) -> None:
        with patch("berrybrain_api.routers.graph.SessionLocal", self.factory):
            delta = get_graph_delta(since_version=0)

        self.assertEqual(len(delta["nodes"]), 4)
        self.assertEqual(len(delta["edgeIds"]), 1)
        self.assertTrue(delta["requiresEdgeRefresh"])
        self.assertFalse(delta["requiresFullRefresh"])
        self.assertEqual(delta["nodeCount"], 4)
        self.assertEqual(delta["edgeCount"], 1)
        self.assertGreater(delta["graphVersion"], 0)

    def test_recluster_requires_matching_preview_token(self) -> None:
        with patch("berrybrain_api.routers.graph.SessionLocal", self.factory):
            preview = recluster_graph(ReclusterRequest(preview=True))
            with self.assertRaisesRegex(HTTPException, "Graph changed"):
                recluster_graph(ReclusterRequest(preview=False, preview_token="stale"))
            applied = recluster_graph(
                ReclusterRequest(
                    preview=False,
                    preview_token=preview["previewToken"],
                )
            )

        self.assertTrue(applied["applied"])


if __name__ == "__main__":
    unittest.main()
