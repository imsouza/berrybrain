import tempfile
import unittest
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from berrybrain_api.attachment_processing import process_attachment
from berrybrain_api.cognitive_layer import index_knowledge_base, retrieve_kb
from berrybrain_api.database import Base
from berrybrain_api.models import (
    AttachmentExtractionRecord,
    GeneratedMetadataRecord,
    GraphEdgeRecord,
    GraphNodeRecord,
    NoteAttachmentRecord,
    NoteRecord,
)


class AttachmentProcessingTest(unittest.TestCase):
    def setUp(self) -> None:
        engine = create_engine(
            "sqlite:///:memory:", connect_args={"check_same_thread": False}
        )
        Base.metadata.create_all(bind=engine)
        self.session = sessionmaker(bind=engine)()
        self.tmp = tempfile.TemporaryDirectory()
        self.vault = Path(self.tmp.name)

    def tearDown(self) -> None:
        self.session.close()
        self.tmp.cleanup()

    def test_text_attachment_becomes_extraction_and_graph_source(self) -> None:
        note = NoteRecord(
            title="Docker Operations",
            slug="docker-operations",
            path="inbox/docker-operations.md",
            content="# Docker Operations\n\nNotes about containers.",
            content_hash="note-hash",
        )
        self.session.add(note)
        self.session.flush()
        stored_path = ".attachments/docker-operations/runbook.txt"
        file_path = self.vault / stored_path
        file_path.parent.mkdir(parents=True)
        file_path.write_text(
            "Docker runbooks describe container rollout, shell automation, and rollback.",
            encoding="utf-8",
        )
        attachment = NoteAttachmentRecord(
            note_id=note.id,
            note_path=note.path,
            filename="runbook.txt",
            stored_path=stored_path,
            mime_type="text/plain",
            category="other",
            size_bytes=file_path.stat().st_size,
        )
        self.session.add(attachment)
        self.session.commit()

        result = process_attachment(self.session, self.vault, attachment.id)

        self.assertEqual(result["status"], "completed")
        extraction = self.session.query(AttachmentExtractionRecord).one()
        self.assertIn("container rollout", extraction.extracted_text)
        attachment_node = (
            self.session.query(GraphNodeRecord)
            .filter(GraphNodeRecord.type == "attachment")
            .one()
        )
        self.assertEqual(attachment_node.label, "runbook.txt")
        self.assertTrue(attachment_node.ai_context)
        edge = (
            self.session.query(GraphEdgeRecord)
            .filter(GraphEdgeRecord.type == "attachment_related")
            .one()
        )
        self.assertTrue(edge.reason)
        self.assertTrue(edge.evidence)
        self.assertEqual(edge.provider, "deterministic")
        metadata = self.session.query(GeneratedMetadataRecord).one()
        self.assertEqual(metadata.generation_type, f"attachment_text_{attachment.id}")
        index_result = index_knowledge_base(self.session)
        self.assertEqual(index_result["attachmentChunks"], 1)
        retrieval = retrieve_kb(self.session, "rollback container rollout")
        self.assertTrue(any(item.metadata.get("kind") == "attachment_text" for item in retrieval))

    def test_image_attachment_gets_future_ocr_status(self) -> None:
        note = NoteRecord(
            title="Whiteboard Capture",
            slug="whiteboard-capture",
            path="inbox/whiteboard.md",
            content="# Whiteboard Capture",
            content_hash="note-hash",
        )
        self.session.add(note)
        self.session.flush()
        stored_path = ".attachments/whiteboard/capture.png"
        file_path = self.vault / stored_path
        file_path.parent.mkdir(parents=True)
        file_path.write_bytes(b"not-a-real-png")
        attachment = NoteAttachmentRecord(
            note_id=note.id,
            note_path=note.path,
            filename="capture.png",
            stored_path=stored_path,
            mime_type="image/png",
            category="image",
            size_bytes=file_path.stat().st_size,
        )
        self.session.add(attachment)
        self.session.commit()

        result = process_attachment(self.session, self.vault, attachment.id)

        self.assertEqual(result["status"], "waiting_ocr")
        attachment_node = (
            self.session.query(GraphNodeRecord)
            .filter(GraphNodeRecord.type == "attachment")
            .one()
        )
        self.assertIn("waiting_ocr", attachment_node.ai_context)


if __name__ == "__main__":
    unittest.main()
