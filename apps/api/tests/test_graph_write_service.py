import json
import unittest

from fastapi import HTTPException
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

import berrybrain_api.models  # noqa: F401
from berrybrain_api.database import Base
from berrybrain_api.graph_write_service import GraphWriteService
from berrybrain_api.models import AutomationLogRecord, GraphEdgeRecord, GraphNodeRecord


class GraphWriteServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite://")
        Base.metadata.create_all(self.engine)
        self.session = sessionmaker(bind=self.engine)()
        self.writer = GraphWriteService(self.session)
        self.left = self.writer.upsert_node(
            node_type="conceito",
            label="Distributed Systems",
            source_note_ids=[1],
        )
        self.right = self.writer.upsert_node(
            node_type="concept",
            label="Observability",
            source_note_ids=[2],
        )

    def tearDown(self) -> None:
        self.session.close()
        self.engine.dispose()

    def test_node_normalization_and_deduplication(self) -> None:
        duplicate = self.writer.upsert_node(
            node_type="concept",
            label="  distributed-systems  ",
            source_note_ids=[3],
        )
        self.assertEqual(duplicate.id, self.left.id)
        self.assertEqual(json.loads(duplicate.source_note_ids), [1, 3])

    def test_edge_normalization_and_symmetric_deduplication(self) -> None:
        first = self.writer.upsert_edge(
            source_node_id=self.left.id,
            target_node_id=self.right.id,
            edge_type="semantic_similarity",
            reason="Both concepts describe operating distributed software.",
            evidence=["note:1", "note:2"],
            confidence=0.8,
            source_note_ids=[1, 2],
        )
        duplicate = self.writer.upsert_edge(
            source_node_id=self.right.id,
            target_node_id=self.left.id,
            edge_type="shared_concept",
            reason="The same relationship was found from the opposite direction.",
            evidence=["note:2"],
            confidence=0.9,
            source_note_ids=[1, 2],
        )
        edges = list(self.session.execute(select(GraphEdgeRecord)).scalars())
        self.assertEqual(first.id, duplicate.id)
        self.assertEqual(len(edges), 1)
        self.assertEqual(duplicate.type, "semantic_relation")
        self.assertEqual(duplicate.confidence, 0.9)

    def test_ai_edge_requires_traceable_chunk_evidence(self) -> None:
        with self.assertRaises(HTTPException) as raised:
            self.writer.upsert_edge(
                source_node_id=self.left.id,
                target_node_id=self.right.id,
                edge_type="semantic_relation",
                reason="Model inferred a relationship.",
                evidence=["unstructured"],
                confidence=0.8,
                source_note_ids=[1, 2],
                created_by="ai",
                provider="nvidia-nim",
                model="qwen",
                prompt_version="graph.v1",
                pipeline_run_id="run-1",
            )
        self.assertEqual(raised.exception.status_code, 422)

        edge = self.writer.upsert_edge(
            source_node_id=self.left.id,
            target_node_id=self.right.id,
            edge_type="semantic_relation",
            reason="Both chunks discuss telemetry in distributed services.",
            evidence=[
                {
                    "sourceNoteId": 1,
                    "targetNoteId": 2,
                    "sourceChunkId": 10,
                    "targetChunkId": 20,
                    "startLine": 2,
                    "endLine": 5,
                    "excerpt": "Telemetry explains behavior across services.",
                    "hash": "sha256:test",
                }
            ],
            confidence=0.84,
            source_note_ids=[1, 2],
            created_by="ai",
            provider="nvidia-nim",
            model="qwen",
            prompt_version="graph.v1",
            pipeline_run_id="run-1",
        )
        self.assertEqual(edge.provider, "nvidia-nim")
        self.assertIn("pipeline_run_id", edge.ai_notes)

    def test_invalid_nodes_edges_and_ai_provenance_are_rejected(self) -> None:
        with self.assertRaises(HTTPException) as invalid_node:
            self.writer.upsert_node(node_type="unknown", label="Unsupported")
        self.assertEqual(invalid_node.exception.status_code, 422)

        valid = {
            "source_node_id": self.left.id,
            "target_node_id": self.right.id,
            "edge_type": "related",
            "reason": "A traceable relationship.",
            "evidence": ["note:1"],
            "confidence": 0.8,
        }
        invalid_cases = (
            ({"edge_type": "unknown"}, 422),
            ({"target_node_id": self.left.id}, 422),
            ({"status": "unknown"}, 422),
            ({"reason": ""}, 422),
            ({"evidence": []}, 422),
            ({"target_node_id": 9999}, 404),
        )
        for changes, status_code in invalid_cases:
            with self.subTest(changes=changes):
                with self.assertRaises(HTTPException) as raised:
                    self.writer.upsert_edge(**(valid | changes))
                self.assertEqual(raised.exception.status_code, status_code)

        ai = valid | {
            "created_by": "ai",
            "evidence": [
                {
                    "sourceNoteId": 1,
                    "targetNoteId": 2,
                    "sourceChunkId": 10,
                    "targetChunkId": 20,
                    "startLine": 1,
                    "endLine": 2,
                    "excerpt": "Evidence",
                    "hash": "sha256:test",
                }
            ],
        }
        for changes in (
            {"source_note_ids": []},
            {"source_note_ids": [1, 2]},
        ):
            with self.subTest(ai_changes=changes):
                with self.assertRaises(HTTPException) as raised:
                    self.writer.upsert_edge(**(ai | changes))
                self.assertEqual(raised.exception.status_code, 422)

    def test_status_change_and_undo_are_persistent(self) -> None:
        edge = self.writer.upsert_edge(
            source_node_id=self.left.id,
            target_node_id=self.right.id,
            edge_type="explicit_link",
            reason="The source note links to the target note.",
            evidence=["[[Observability]]"],
            confidence=1.0,
            source_note_ids=[1, 2],
            status="suggested",
        )
        changed = self.writer.set_edge_status(edge.id, "ignored")
        mutation_id = changed.mutation_log_id
        self.assertEqual(changed.status, "ignored")

        mutation = self.writer.undo(mutation_id)
        restored = self.session.get(GraphEdgeRecord, edge.id)
        self.assertIsNotNone(restored)
        self.assertEqual(restored.status, "suggested")
        self.assertIsNotNone(mutation.reverted_at)
        self.assertIsNotNone(mutation.reverted_by_log_id)

    def test_graph_panel_mutations_validate_persist_and_delete_safely(self) -> None:
        edge = self.writer.upsert_edge(
            source_node_id=self.left.id,
            target_node_id=self.right.id,
            edge_type="related",
            reason="A user-reviewable relationship.",
            evidence=["note:1"],
            confidence=0.7,
        )

        node = self.writer.set_node_status(self.left.id, "confirmed")
        self.assertEqual(node.status, "confirmed")
        self.assertEqual(
            self.writer.set_node_user_notes(node.id, "My interpretation").user_notes,
            "My interpretation",
        )
        enriched = self.writer.update_node_enrichment(
            node.id,
            {
                "ai_summary": "A grounded summary.",
                "provider": "deterministic",
                "ignored": "not allowed",
            },
        )
        self.assertEqual(enriched.ai_summary, "A grounded summary.")
        self.assertEqual(
            self.writer.set_edge_user_notes(edge.id, "Reviewed evidence").user_notes,
            "Reviewed evidence",
        )

        invalid_calls = (
            lambda: self.writer.set_node_status(9999, "confirmed"),
            lambda: self.writer.set_node_status(node.id, "unknown"),
            lambda: self.writer.set_edge_status(9999, "confirmed"),
            lambda: self.writer.set_edge_status(edge.id, "unknown"),
            lambda: self.writer.set_node_user_notes(9999, "missing"),
            lambda: self.writer.set_edge_user_notes(9999, "missing"),
            lambda: self.writer.update_node_enrichment(9999, {"ai_summary": "x"}),
            lambda: self.writer.update_node_enrichment(node.id, {"ignored": "x"}),
        )
        for call in invalid_calls:
            with self.subTest(call=call):
                with self.assertRaises(HTTPException):
                    call()

        note = self.writer.upsert_node(
            node_type="note",
            label="Vault source",
            source_note_ids=[10],
        )
        with self.assertRaises(HTTPException) as protected_note:
            self.writer.delete_node(note.id)
        self.assertEqual(protected_note.exception.status_code, 409)

        self.assertTrue(self.writer.delete_edge(edge.id, reason="Reviewed removal"))
        self.assertFalse(self.writer.delete_edge(edge.id))
        deleted = self.writer.delete_node(self.right.id)
        self.assertEqual(deleted.id, self.right.id)
        with self.assertRaises(HTTPException):
            self.writer.delete_node(9999)

    def test_manual_evidence_and_type_changes_are_versioned(self) -> None:
        edge = self.writer.upsert_edge(
            source_node_id=self.left.id,
            target_node_id=self.right.id,
            edge_type="related",
            reason="Initial relationship.",
            evidence=["note:1"],
            confidence=0.6,
        )
        edge = self.writer.add_manual_evidence(
            edge.id, "A concrete user observation", 1
        )
        evidence = json.loads(edge.evidence)
        self.assertEqual(evidence[-1]["kind"], "manual")
        edge = self.writer.update_edge_type(edge.id, "prerequisite")
        self.assertEqual(edge.type, "prerequisite")
        reversible_logs = list(
            self.session.execute(
                select(AutomationLogRecord).where(AutomationLogRecord.reversible == 1)
            ).scalars()
        )
        self.assertGreaterEqual(len(reversible_logs), 2)

    def test_node_merge_and_split_restore_edges(self) -> None:
        duplicate = self.writer.upsert_node(
            node_type="concept",
            label="Telemetry",
            source_note_ids=[3],
        )
        edge = self.writer.upsert_edge(
            source_node_id=duplicate.id,
            target_node_id=self.right.id,
            edge_type="prerequisite",
            reason="Telemetry is required to reason about observability.",
            evidence=["note:3"],
            confidence=0.8,
        )
        survivor, mutation = self.writer.merge_nodes(self.left.id, duplicate.id)
        self.session.refresh(edge)
        self.session.refresh(duplicate)
        self.assertEqual(edge.source_node_id, survivor.id)
        self.assertEqual(duplicate.status, "archived")

        self.writer.undo(mutation.id)
        self.session.refresh(edge)
        self.session.refresh(duplicate)
        self.assertEqual(edge.source_node_id, duplicate.id)
        self.assertEqual(duplicate.status, "suggested")

    def test_maintenance_deduplicates_legacy_nodes_and_edges(self) -> None:
        legacy = GraphNodeRecord(type="conceito", label="Distributed_Systems")
        self.session.add(legacy)
        self.session.flush()
        self.session.add_all(
            [
                GraphEdgeRecord(
                    source_node_id=legacy.id,
                    target_node_id=self.right.id,
                    type="shared_concept",
                    reason="Legacy relationship",
                    evidence='["note:1"]',
                ),
                GraphEdgeRecord(
                    source_node_id=self.right.id,
                    target_node_id=self.left.id,
                    type="semantic_similarity",
                    reason="Equivalent reverse relationship",
                    evidence='["note:2"]',
                ),
            ]
        )
        self.session.commit()

        merged = self.writer.deduplicate_nodes()
        nodes = list(self.session.execute(select(GraphNodeRecord)).scalars())
        edges = list(self.session.execute(select(GraphEdgeRecord)).scalars())

        self.assertEqual(merged, 1)
        self.assertEqual(len(nodes), 2)
        self.assertEqual(len(edges), 1)
        self.assertEqual(edges[0].type, "semantic_relation")
        self.assertEqual(set(json.loads(edges[0].evidence)), {"note:1", "note:2"})


if __name__ == "__main__":
    unittest.main()
