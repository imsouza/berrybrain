import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from berrybrain_api.attachment_processing import (
    _extract_image_ocr,
    _extract_pdf_text,
    _transcribe_faster_whisper,
    _transcribe_media,
    process_attachment,
)
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

        with patch(
            "berrybrain_api.attachment_processing._resolve_local_executable",
            return_value=None,
        ):
            result = process_attachment(self.session, self.vault, attachment.id)

        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["progress"], 100)
        self.assertEqual(result["stage"], "completed")
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
            .filter(GraphEdgeRecord.type == "derived_from")
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
        self.assertTrue(
            any(item.metadata.get("kind") == "attachment_text" for item in retrieval)
        )

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

        with patch(
            "berrybrain_api.attachment_processing._resolve_local_executable",
            return_value=None,
        ):
            result = process_attachment(self.session, self.vault, attachment.id)

        self.assertEqual(result["status"], "waiting_ocr")
        self.assertEqual(result["progress"], 25)
        attachment_node = (
            self.session.query(GraphNodeRecord)
            .filter(GraphNodeRecord.type == "attachment")
            .one()
        )
        self.assertIn("waiting_ocr", attachment_node.ai_context)

    def test_image_ocr_records_confidence_and_word_locations(self) -> None:
        tsv = (
            "level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\tleft\ttop\twidth\theight\tconf\ttext\n"
            "5\t1\t1\t1\t1\t1\t10\t20\t80\t20\t91.5\tKnowledge\n"
            "5\t1\t1\t1\t1\t2\t95\t20\t50\t20\t88.5\tgraph\n"
        )
        completed = SimpleNamespace(returncode=0, stdout=tsv, stderr="")
        with (
            patch(
                "berrybrain_api.attachment_processing._resolve_local_executable",
                return_value="/usr/bin/tesseract",
            ),
            patch(
                "berrybrain_api.attachment_processing.subprocess.run",
                return_value=completed,
            ),
        ):
            result = _extract_image_ocr(
                self.vault / "capture.png", "tesseract", "eng", 30
            )

        text, status, _, locations, confidence, extractor, provider, _ = result
        self.assertEqual(status, "completed")
        self.assertEqual(text, "Knowledge graph")
        self.assertAlmostEqual(confidence, 0.9)
        self.assertEqual(extractor, "tesseract")
        self.assertEqual(provider, "local")
        self.assertEqual(locations["kind"], "ocr_words")
        self.assertEqual(locations["words"][0]["box"]["left"], 10)

    def test_audio_transcription_records_timestamps(self) -> None:
        def fake_run(args, **_kwargs):
            output_dir = Path(args[args.index("--output_dir") + 1])
            (output_dir / "meeting.json").write_text(
                '{"language":"en","segments":['
                '{"start":0.0,"end":1.25,"text":"Graph evidence"},'
                '{"start":1.25,"end":2.5,"text":"supports recall"}]}'
            )
            return SimpleNamespace(returncode=0, stdout="", stderr="")

        with (
            patch(
                "berrybrain_api.attachment_processing._resolve_local_executable",
                return_value="/usr/bin/whisper",
            ),
            patch(
                "berrybrain_api.attachment_processing.subprocess.run",
                side_effect=fake_run,
            ),
        ):
            result = _transcribe_media(
                self.vault / "meeting.mp3", "whisper", "base", 30
            )

        text, status, _, locations, confidence, extractor, provider, model = result
        self.assertEqual(status, "completed")
        self.assertIn("supports recall", text)
        self.assertEqual(confidence, 0.8)
        self.assertEqual(extractor, "whisper-cli")
        self.assertEqual(provider, "local")
        self.assertEqual(model, "base")
        self.assertEqual(locations["kind"], "media_timestamps")
        self.assertEqual(locations["segments"][1]["start"], 1.25)

    def test_faster_whisper_records_confidence_and_timestamps(self) -> None:
        completed = SimpleNamespace(
            returncode=0,
            stdout=(
                '{"language":"en","language_probability":0.98,'
                '"confidence":0.87,"segments":['
                '{"start":0.0,"end":1.5,"text":"Docker namespaces",'
                '"confidence":0.87}]}'
            ),
            stderr="",
        )
        with patch(
            "berrybrain_api.attachment_processing.subprocess.run",
            return_value=completed,
        ):
            result = _transcribe_faster_whisper(
                self.vault / "knowledge.wav", "/models/tiny.en", 30
            )

        text, status, _, locations, confidence, extractor, provider, model = result
        self.assertEqual(status, "completed")
        self.assertEqual(text, "Docker namespaces")
        self.assertEqual(confidence, 0.87)
        self.assertEqual(extractor, "faster-whisper")
        self.assertEqual(provider, "local")
        self.assertEqual(model, "/models/tiny.en")
        self.assertEqual(locations["segments"][0]["start"], 0.0)

    def test_pdf_extraction_records_page_locations_and_encryption(self) -> None:
        pdf_path = self.vault / "fixture.pdf"
        pdf_path.write_bytes(b"%PDF-fixture")

        class Page:
            def __init__(self, text: str):
                self.text = text

            def extract_text(self) -> str:
                return self.text

        reader = SimpleNamespace(
            is_encrypted=False,
            pages=[Page("First page evidence"), Page("Second page evidence")],
        )
        with patch.dict(
            sys.modules, {"pypdf": SimpleNamespace(PdfReader=lambda _: reader)}
        ):
            text, status, error, locations = _extract_pdf_text(pdf_path)

        self.assertEqual(status, "completed")
        self.assertEqual(error, "")
        self.assertIn("[Page 1]", text)
        self.assertEqual(locations["kind"], "pdf_pages")
        self.assertEqual([item["page"] for item in locations["pages"]], [1, 2])

        encrypted_reader = SimpleNamespace(is_encrypted=True, pages=[])
        with patch.dict(
            sys.modules,
            {"pypdf": SimpleNamespace(PdfReader=lambda _: encrypted_reader)},
        ):
            _, encrypted_status, encrypted_error, _ = _extract_pdf_text(pdf_path)
        self.assertEqual(encrypted_status, "encrypted")
        self.assertIn("Encrypted", encrypted_error)


if __name__ == "__main__":
    unittest.main()
