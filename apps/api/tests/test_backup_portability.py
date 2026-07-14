import json
import shutil
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from zipfile import ZipFile

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from berrybrain_api.backup import create_backup, export_full, restore_backup
from berrybrain_api.database import Base
from berrybrain_api.models import (
    AttachmentExtractionRecord,
    NoteAttachmentRecord,
    NoteRecord,
)


class BackupPortabilityTest(unittest.TestCase):
    def test_full_export_contains_attachment_file_and_extraction_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            root_path = Path(root)
            vault = root_path / "vault"
            backup_path = root_path / "backups"
            attachment_path = vault / ".attachments/source/evidence.txt"
            attachment_path.parent.mkdir(parents=True)
            attachment_path.write_text("Traceable evidence", encoding="utf-8")
            (vault / "source.md").write_text("# Source", encoding="utf-8")

            engine = create_engine("sqlite:///:memory:")
            Base.metadata.create_all(engine)
            session_factory = sessionmaker(bind=engine)
            with session_factory() as session:
                note = NoteRecord(
                    title="Source",
                    slug="source",
                    path="source.md",
                    content="# Source",
                    content_hash="hash",
                )
                session.add(note)
                session.flush()
                attachment = NoteAttachmentRecord(
                    note_id=note.id,
                    note_path=note.path,
                    filename="evidence.txt",
                    stored_path=".attachments/source/evidence.txt",
                    mime_type="text/plain",
                    declared_mime_type="text/plain",
                    checksum="a" * 64,
                    category="other",
                    size_bytes=18,
                )
                session.add(attachment)
                session.flush()
                session.add(
                    AttachmentExtractionRecord(
                        attachment_id=attachment.id,
                        status="completed",
                        extractor="attachment-text.v1",
                        location_metadata='{"kind":"characters"}',
                        progress=100,
                    )
                )
                session.commit()

            settings = SimpleNamespace(
                vault_path=vault,
                backup_path=backup_path,
                database_url="sqlite:///missing.db",
            )
            with (
                patch("berrybrain_api.backup.SessionLocal", session_factory),
                patch("berrybrain_api.backup.get_settings", return_value=settings),
            ):
                archive = export_full()

            with ZipFile(archive) as zipped:
                self.assertIn("vault/source.md", zipped.namelist())
                self.assertIn(
                    "vault/.attachments/source/evidence.txt", zipped.namelist()
                )
                self.assertIn("portable/insights.jsonl", zipped.namelist())
                self.assertIn("portable/settings.json", zipped.namelist())
                self.assertIn("portable/knowledge-graph.graphml", zipped.namelist())
                manifest = json.loads(
                    zipped.read("metadata/attachments.json").decode("utf-8")
                )
            self.assertEqual(manifest[0]["checksum"], "a" * 64)
            self.assertEqual(manifest[0]["extraction"]["status"], "completed")
            self.assertEqual(
                manifest[0]["extraction"]["locationMetadata"]["kind"],
                "characters",
            )

    def test_restore_into_empty_vault_verifies_checksums_and_reports_results(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as root:
            root_path = Path(root)
            vault = root_path / "vault"
            vault.mkdir()
            (vault / "source.md").write_text("# Restorable", encoding="utf-8")
            database_path = root_path / "berrybrain.db"
            engine = create_engine(f"sqlite:///{database_path}")
            Base.metadata.create_all(engine)
            session_factory = sessionmaker(bind=engine)
            settings = SimpleNamespace(
                vault_path=vault,
                backup_path=root_path / "backups",
                database_url=f"sqlite:///{database_path}",
            )

            with (
                patch("berrybrain_api.backup.SessionLocal", session_factory),
                patch("berrybrain_api.backup.get_settings", return_value=settings),
            ):
                backup = create_backup()
                shutil.rmtree(vault)
                vault.mkdir()
                restored = restore_backup(str(backup["id"]))

                self.assertEqual(restored["verification"]["status"], "verified")
                self.assertEqual(restored["restoredFiles"], 1)
                self.assertEqual(
                    (vault / "source.md").read_text(encoding="utf-8"),
                    "# Restorable",
                )

                backed_up_note = Path(str(backup["path"])) / "vault/source.md"
                backed_up_note.write_text("corrupted", encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "mismatch"):
                    restore_backup(str(backup["id"]))


if __name__ == "__main__":
    unittest.main()
