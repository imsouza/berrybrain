import json
import unittest
from unittest.mock import patch

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from berrybrain_api.database import Base
from berrybrain_api.models import GraphEdgeRecord, GraphNodeRecord, JobRecord
from berrybrain_api.routers.graph import (
    ReclusterRequest,
    delete_graph_node_endpoint,
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

    def test_delete_node_schedules_graph_recalculation(self) -> None:
        with self.factory() as session:
            target = GraphNodeRecord(
                type="concept",
                label="Disposable concept",
                semantic_status="active",
            )
            session.add(target)
            session.flush()
            target_id = target.id
            session.add_all(
                [
                    JobRecord(
                        type="ENRICH_GRAPH_NODE",
                        status="dead_letter",
                        payload=json.dumps({"node_id": target_id}),
                        max_attempts=2,
                    ),
                    JobRecord(
                        type="JUDGE_ARTIFACT",
                        status="dead_letter",
                        payload=json.dumps(
                            {"artifact_type": "node", "artifact_id": target_id}
                        ),
                        max_attempts=2,
                    ),
                ]
            )
            session.commit()

        with patch("berrybrain_api.routers.graph.SessionLocal", self.factory):
            result = delete_graph_node_endpoint(target_id)

        with self.factory() as session:
            job_types = set(session.query(JobRecord.type).all())
            obsolete_statuses = {
                job.status
                for job in session.query(JobRecord)
                .filter(JobRecord.type.in_(("ENRICH_GRAPH_NODE", "JUDGE_ARTIFACT")))
                .all()
            }
            self.assertIsNone(session.get(GraphNodeRecord, target_id))

        self.assertEqual(result["status"], "deleted")
        self.assertIn(("UPDATE_GRAPH_STATS",), job_types)
        self.assertIn(("UPDATE_GRAPH_CLUSTERS",), job_types)
        self.assertIn(("SYNC_HIPPORAG_GRAPH",), job_types)
        self.assertEqual(obsolete_statuses, {"superseded"})


if __name__ == "__main__":
    unittest.main()
