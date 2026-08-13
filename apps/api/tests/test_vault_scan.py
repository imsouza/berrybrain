import json
import tempfile
import unittest
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from berrybrain_api.database import Base
from berrybrain_api.graph_write_service import GraphWriteService
from berrybrain_api.models import (
    GraphEdgeRecord,
    GraphNodeRecord,
    JobRecord,
    NoteRecord,
)
from berrybrain_api.vault_scan import scan_vault


class VaultScanTest(unittest.TestCase):
    def setUp(self) -> None:
        engine = create_engine(
            "sqlite:///:memory:", connect_args={"check_same_thread": False}
        )
        Base.metadata.create_all(bind=engine)
        self.session = sessionmaker(bind=engine)()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.vault_path = Path(self.temp_dir.name) / "vault"
        (self.vault_path / "inbox").mkdir(parents=True)

    def tearDown(self) -> None:
        self.session.close()
        self.temp_dir.cleanup()

    def test_scan_vault_syncs_new_changed_and_deleted_notes(self) -> None:
        note_path = self.vault_path / "inbox" / "a.md"
        note_path.write_text("# A\n\nInitial.", encoding="utf-8")

        first = scan_vault(self.session, self.vault_path)
        second = scan_vault(self.session, self.vault_path)
        note_path.write_text("# A\n\nChanged with [[B]].", encoding="utf-8")
        third = scan_vault(self.session, self.vault_path)
        note_path.unlink()
        fourth = scan_vault(self.session, self.vault_path)

        self.assertEqual(first["created"], 1)
        self.assertEqual(first["jobs_created"], 15)
        self.assertEqual(second["unchanged"], 1)
        self.assertEqual(second["jobs_created"], 0)
        self.assertEqual(third["updated"], 1)
        self.assertEqual(third["jobs_created"], 15)
        self.assertEqual(fourth["deleted"], 1)
        self.assertEqual(fourth["jobs_created"], 5)

        remaining_notes = self.session.execute(select(NoteRecord)).scalars().all()
        jobs = (
            self.session.execute(select(JobRecord).order_by(JobRecord.id))
            .scalars()
            .all()
        )
        payloads = [json.loads(job.payload) for job in jobs]

        self.assertEqual(remaining_notes, [])
        event_types = [payload["event_type"] for payload in payloads]
        self.assertEqual(event_types.count("NOTE_CREATED"), 15)
        self.assertEqual(event_types.count("NOTE_UPDATED"), 15)
        self.assertEqual(event_types.count("NOTE_DELETED"), 5)

    def test_scan_preserves_note_identity_across_external_move(self) -> None:
        original = self.vault_path / "inbox" / "source.md"
        original.write_text("# Stable identity\n\nKnowledge.", encoding="utf-8")
        scan_vault(self.session, self.vault_path)
        note = self.session.execute(select(NoteRecord)).scalar_one()
        original_id = note.id

        destination_dir = self.vault_path / "archive"
        destination_dir.mkdir()
        original.rename(destination_dir / "renamed.md")
        result = scan_vault(self.session, self.vault_path)

        notes = list(self.session.execute(select(NoteRecord)).scalars())
        graph_nodes = list(
            self.session.execute(
                select(GraphNodeRecord).where(GraphNodeRecord.type == "note")
            ).scalars()
        )
        self.assertEqual(result["moved"], 1)
        self.assertEqual(result["jobs_created"], 4)
        self.assertEqual(len(notes), 1)
        self.assertEqual(notes[0].id, original_id)
        self.assertEqual(notes[0].path, "archive/renamed.md")
        self.assertEqual(len(graph_nodes), 1)
        self.assertEqual(graph_nodes[0].source_id, original_id)

    def test_edit_and_delete_detach_graph_provenance(self) -> None:
        first_path = self.vault_path / "inbox" / "first.md"
        second_path = self.vault_path / "inbox" / "second.md"
        first_path.write_text("# First\n\nTime series forecasting.", encoding="utf-8")
        second_path.write_text("# Second\n\nForecast evaluation.", encoding="utf-8")
        scan_vault(self.session, self.vault_path)
        notes = {
            note.path: note
            for note in self.session.execute(select(NoteRecord)).scalars()
        }
        first = notes["inbox/first.md"]
        second = notes["inbox/second.md"]

        writer = GraphWriteService(self.session)
        shared = writer.upsert_node(
            node_type="concept",
            label="Forecast evaluation",
            source_note_ids=[first.id, second.id],
        )
        peer = writer.upsert_node(
            node_type="concept",
            label="Temporal forecasting",
            source_note_ids=[first.id, second.id],
        )
        orphan = writer.upsert_node(
            node_type="concept",
            label="Legacy forecast method",
            source_note_ids=[first.id],
        )
        shared_edge = writer.upsert_edge(
            source_node_id=shared.id,
            target_node_id=peer.id,
            edge_type="semantic_similarity",
            reason="Both concepts describe forecast quality.",
            evidence=["first.md", "second.md"],
            source_note_ids=[first.id, second.id],
        )
        orphan_edge = writer.upsert_edge(
            source_node_id=shared.id,
            target_node_id=orphan.id,
            edge_type="semantic_similarity",
            reason="The legacy method is a forecasting approach.",
            evidence=["first.md"],
            source_note_ids=[first.id],
        )
        self.session.commit()

        first_path.write_text("# First revised\n\nCausal inference.", encoding="utf-8")
        scan_vault(self.session, self.vault_path)
        self.session.expire_all()

        edited_note = self.session.get(NoteRecord, first.id)
        canonical_note_nodes = list(
            self.session.execute(
                select(GraphNodeRecord).where(
                    GraphNodeRecord.type == "note",
                    GraphNodeRecord.source_id == first.id,
                )
            ).scalars()
        )
        retained_shared = self.session.get(GraphNodeRecord, shared.id)
        retained_edge = self.session.get(GraphEdgeRecord, shared_edge.id)
        self.assertEqual(edited_note.title, "First revised")
        self.assertEqual(len(canonical_note_nodes), 1)
        self.assertEqual(canonical_note_nodes[0].label, "First revised")
        self.assertEqual(json.loads(retained_shared.source_note_ids), [second.id])
        self.assertEqual(json.loads(retained_edge.source_note_ids), [second.id])
        self.assertEqual(retained_shared.confidence_sample_size, 1)
        self.assertIsNone(self.session.get(GraphNodeRecord, orphan.id))
        self.assertIsNone(self.session.get(GraphEdgeRecord, orphan_edge.id))

        second_path.unlink()
        deletion = scan_vault(self.session, self.vault_path)
        self.session.expire_all()
        self.assertEqual(deletion["deleted"], 1)
        self.assertEqual(deletion["jobs_created"], 5)
        self.assertIsNone(self.session.get(NoteRecord, second.id))
        self.assertIsNone(self.session.get(GraphNodeRecord, shared.id))
        self.assertIsNone(self.session.get(GraphEdgeRecord, shared_edge.id))

    def test_whitespace_only_edit_preserves_graph_provenance(self) -> None:
        note_path = self.vault_path / "inbox" / "formatting.md"
        note_path.write_text("# Formatting\n\nStable knowledge.", encoding="utf-8")
        scan_vault(self.session, self.vault_path)
        note = self.session.execute(select(NoteRecord)).scalar_one()
        node = GraphWriteService(self.session).upsert_node(
            node_type="concept",
            label="Stable knowledge",
            source_note_ids=[note.id],
        )
        self.session.commit()

        note_path.write_text("# Formatting\n\nStable   knowledge.\n", encoding="utf-8")
        result = scan_vault(self.session, self.vault_path)
        self.session.expire_all()

        self.assertEqual(result["updated"], 1)
        self.assertIsNotNone(self.session.get(GraphNodeRecord, node.id))
        self.assertEqual(
            json.loads(self.session.get(GraphNodeRecord, node.id).source_note_ids),
            [note.id],
        )


if __name__ == "__main__":
    unittest.main()
