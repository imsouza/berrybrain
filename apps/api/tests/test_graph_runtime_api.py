import json
import unittest
from unittest.mock import patch

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from berrybrain_api.database import Base
from berrybrain_api.models import (
    ConnectionRecord,
    GraphEdgeRecord,
    GraphInferenceRecord,
    GraphNodeRecord,
    JobRecord,
    LearningEventRecord,
    NoteRecord,
)
from berrybrain_api.routers.graph import (
    InferenceFeedbackRequest,
    ReclusterRequest,
    delete_graph_node_endpoint,
    get_graph_delta,
    get_graph_edges_page,
    get_graph_nodes_page,
    recluster_graph,
    record_inference_feedback,
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
                    quality_gate_status="passed",
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

        self.assertEqual(len(delta["nodes"]), 3)
        self.assertEqual(len(delta["edgeIds"]), 1)
        self.assertTrue(delta["requiresEdgeRefresh"])
        self.assertFalse(delta["requiresFullRefresh"])
        self.assertEqual(delta["nodeCount"], 3)
        self.assertEqual(delta["edgeCount"], 1)
        self.assertGreater(delta["graphVersion"], 0)

    def test_inference_feedback_creates_learning_event(self) -> None:
        with self.factory() as session:
            source = GraphNodeRecord(
                type="concept",
                label="Forecasting",
                source_note_ids="[4,9]",
            )
            session.add(source)
            session.flush()
            inference = GraphInferenceRecord(
                question="What connects these notes?",
                answer="The accepted graph evidence links them.",
                status="answered",
                evidence=(
                    f'[{{"metadata":{{"sourceNoteIds":[4],"nodeId":{source.id}' + "}}]"
                ),
                related_nodes=f'["concept_{source.id}"]',
            )
            session.add(inference)
            session.commit()
            inference_id = inference.id
            result = record_inference_feedback(
                inference_id,
                InferenceFeedbackRequest(action="upvoted"),
                session,
            )
            event = session.query(LearningEventRecord).one()

        self.assertEqual(result["action"], "upvoted")
        self.assertEqual(event.target_key, f"graph-inference:{inference_id}")
        self.assertEqual(event.source_note_ids, "[4,9]")

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

    def test_explicit_empty_recluster_scope_never_expands_to_the_full_graph(
        self,
    ) -> None:
        with patch("berrybrain_api.routers.graph.SessionLocal", self.factory):
            preview = recluster_graph(ReclusterRequest(preview=True, scope_node_ids=[]))

        self.assertTrue(preview["scoped"])
        self.assertEqual(preview["scopeNodeIds"], [])
        self.assertEqual(preview["nodeCount"], 0)

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
        self.assertIn(("GENERATE_GRAPH_INSIGHTS",), job_types)
        self.assertIn(("SYNC_HIPPORAG_GRAPH",), job_types)
        self.assertEqual(result["impact"]["scope"], "incident_subgraph")
        self.assertIn("insights", result["jobs"])
        self.assertEqual(obsolete_statuses, {"superseded"})

    def test_delete_concept_invalidates_derived_note_relationships(self) -> None:
        with self.factory() as session:
            first_note = NoteRecord(title="First note", slug="first", path="first.md")
            second_note = NoteRecord(
                title="Second note", slug="second", path="second.md"
            )
            session.add_all([first_note, second_note])
            session.flush()
            first_node = GraphNodeRecord(
                type="note",
                label=first_note.title,
                source_id=first_note.id,
                source_note_ids=json.dumps([first_note.id]),
            )
            second_node = GraphNodeRecord(
                type="note",
                label=second_note.title,
                source_id=second_note.id,
                source_note_ids=json.dumps([second_note.id]),
            )
            concept = GraphNodeRecord(
                type="concept",
                label="Discarded bridge",
                source_note_ids=json.dumps([first_note.id, second_note.id]),
            )
            session.add_all([first_node, second_node, concept])
            session.flush()
            edge = GraphEdgeRecord(
                source_node_id=first_node.id,
                target_node_id=second_node.id,
                type="related",
                label="shared concept",
                reason=(
                    'The notes "First note" and "Second note" share the '
                    'concept "Discarded bridge".'
                ),
                evidence=json.dumps(["Discarded bridge"]),
                source_note_ids=json.dumps([first_note.id, second_note.id]),
                status="suggested",
                semantic_status="active",
                created_by="system",
            )
            connection = ConnectionRecord(
                source_note_id=first_note.id,
                target_note_id=second_note.id,
                connection_type="shared_concept",
                reason=edge.reason,
                evidence=edge.evidence,
                status="suggested",
            )
            session.add_all([edge, connection])
            session.commit()
            concept_id = concept.id
            edge_id = edge.id
            connection_id = connection.id

        with patch("berrybrain_api.routers.graph.SessionLocal", self.factory):
            result = delete_graph_node_endpoint(concept_id)

        with self.factory() as session:
            stale_edge = session.get(GraphEdgeRecord, edge_id)
            stale_connection = session.get(ConnectionRecord, connection_id)
            self.assertEqual(stale_edge.status, "stale")
            self.assertEqual(stale_edge.semantic_status, "quarantined")
            self.assertEqual(stale_connection.status, "stale")

        self.assertEqual(result["impact"]["invalidatedRelationships"], 2)


if __name__ == "__main__":
    unittest.main()
