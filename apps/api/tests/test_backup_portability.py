import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from zipfile import ZipFile

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

from berrybrain_api.backup import (
    _create_manifest,
    _is_sensitive_setting,
    _json_object,
    _resolve_backup_path,
    _verify_manifest,
    create_backup,
    delete_backup,
    export_full,
    restore_backup,
)
from berrybrain_api.database import Base
from berrybrain_api.models import (
    AttachmentExtractionRecord,
    ModelInvocationRecord,
    NoteAttachmentRecord,
    NoteRecord,
)
from berrybrain_api.schema_migrations import (
    CURRENT_SCHEMA_VERSION,
    apply_schema_migrations,
    get_schema_version,
)


class BackupPortabilityTest(unittest.TestCase):
    def test_backup_paths_and_legacy_manifests_fail_safely(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            root_path = Path(root)
            settings = SimpleNamespace(
                backup_path=root_path / "backups",
                database_url=f"sqlite:///{root_path / 'berrybrain.db'}",
                vault_path=root_path / "vault",
            )
            with patch("berrybrain_api.backup.get_settings", return_value=settings):
                for unsafe_id in ("", "other", "../backup-escape", "backup\\escape"):
                    with self.assertRaisesRegex(Exception, "Invalid backup id"):
                        _resolve_backup_path(unsafe_id)

                legacy = settings.backup_path / "backup-legacy"
                legacy.mkdir(parents=True)
                self.assertEqual(
                    _verify_manifest(legacy)["status"], "legacy_unverified"
                )

                (legacy / "manifest.json").write_text("not-json", encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "manifest is invalid"):
                    _verify_manifest(legacy)

                (legacy / "manifest.json").write_text(
                    json.dumps({"files": {}}), encoding="utf-8"
                )
                with self.assertRaisesRegex(ValueError, "file list is invalid"):
                    _verify_manifest(legacy)

                with self.assertRaises(FileNotFoundError):
                    restore_backup("backup-missing")
                with self.assertRaises(FileNotFoundError):
                    delete_backup("backup-missing")

    def test_manifest_rejects_tampering_and_unsafe_entries(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            backup = Path(root)
            source = backup / "vault" / "note.md"
            source.parent.mkdir()
            source.write_text("original", encoding="utf-8")
            manifest = _create_manifest(backup)
            (backup / "manifest.json").write_text(
                json.dumps(manifest), encoding="utf-8"
            )
            self.assertEqual(_verify_manifest(backup)["status"], "verified")

            source.write_text("tampered", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "checksum mismatch"):
                _verify_manifest(backup)

            manifest["files"] = [{"path": "../escape", "sizeBytes": 0, "sha256": ""}]
            (backup / "manifest.json").write_text(
                json.dumps(manifest), encoding="utf-8"
            )
            with self.assertRaisesRegex(ValueError, "unsafe path"):
                _verify_manifest(backup)

    def test_backup_metadata_helpers_omit_secrets_and_invalid_json(self) -> None:
        self.assertTrue(_is_sensitive_setting("graph_ai_api_key"))
        self.assertTrue(_is_sensitive_setting("service_token"))
        self.assertFalse(_is_sensitive_setting("theme"))
        self.assertEqual(_json_object('{"page": 2}'), {"page": 2})
        self.assertEqual(_json_object("[]"), {})
        self.assertEqual(_json_object("invalid"), {})

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
                session.add(
                    ModelInvocationRecord(
                        capability="graph_inference",
                        provider="local",
                        model="qwen",
                        prompt_version="backup-test.v1",
                        status="completed",
                        latency_ms=10,
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
                patch("berrybrain_api.backup.database_engine", engine),
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
                invocation_payload = zipped.read(
                    "portable/model_invocations.jsonl"
                ).decode("utf-8")
                manifest = json.loads(
                    zipped.read("metadata/attachments.json").decode("utf-8")
                )
            self.assertEqual(manifest[0]["checksum"], "a" * 64)
            self.assertIn("backup-test.v1", invocation_payload)
            invocation = json.loads(invocation_payload)
            self.assertNotIn("prompt", invocation)
            self.assertNotIn("content", invocation)
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
                patch("berrybrain_api.backup.database_engine", engine),
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

    def test_restore_upgrades_v4_to_current_and_replaces_live_vault(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            root_path = Path(root)
            vault = root_path / "vault"
            vault.mkdir()
            (vault / "original.md").write_text("# Original", encoding="utf-8")
            database_path = root_path / "berrybrain.db"
            engine = create_engine(f"sqlite:///{database_path}")
            Base.metadata.create_all(engine)
            apply_schema_migrations(engine)
            session_factory = sessionmaker(bind=engine)
            with session_factory() as session:
                session.add(
                    NoteRecord(
                        title="Original",
                        slug="original",
                        path="original.md",
                        content="# Original",
                        content_hash="original",
                    )
                )
                session.commit()
            settings = SimpleNamespace(
                vault_path=vault,
                backup_path=root_path / "backups",
                database_url=f"sqlite:///{database_path}",
            )
            with (
                patch("berrybrain_api.backup.SessionLocal", session_factory),
                patch("berrybrain_api.backup.get_settings", return_value=settings),
                patch("berrybrain_api.backup.database_engine", engine),
            ):
                backup = create_backup()
                backup_path = Path(str(backup["path"]))
                backup_database = backup_path / database_path.name
                with create_engine(
                    f"sqlite:///{backup_database}"
                ).begin() as connection:
                    connection.execute(
                        text("DELETE FROM schema_migrations WHERE version >= 5")
                    )
                    connection.execute(text("DROP TABLE model_invocations"))
                    connection.execute(text("DROP TABLE worker_inbox"))
                    connection.execute(text("ALTER TABLE jobs DROP COLUMN claim_token"))
                metadata_path = backup_path / "metadata.json"
                metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
                metadata["schemaVersion"] = 4
                metadata_path.write_text(
                    json.dumps(metadata, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
                (backup_path / "manifest.json").write_text(
                    json.dumps(_create_manifest(backup_path), indent=2),
                    encoding="utf-8",
                )

                with engine.begin() as connection:
                    connection.execute(text("UPDATE notes SET title = 'Live only'"))
                (vault / "live-only.md").write_text("# Live", encoding="utf-8")
                restored = restore_backup(str(backup["id"]))

            verification_engine = create_engine(f"sqlite:///{database_path}")
            try:
                self.assertEqual(
                    get_schema_version(verification_engine), CURRENT_SCHEMA_VERSION
                )
                self.assertIn(
                    "model_invocations", inspect(verification_engine).get_table_names()
                )
                self.assertIn(
                    "worker_inbox", inspect(verification_engine).get_table_names()
                )
                self.assertIn(
                    "claim_token",
                    {
                        column["name"]
                        for column in inspect(verification_engine).get_columns("jobs")
                    },
                )
                with verification_engine.connect() as connection:
                    title = connection.execute(
                        text("SELECT title FROM notes")
                    ).scalar_one()
                self.assertEqual(title, "Original")
            finally:
                verification_engine.dispose()
            self.assertEqual(restored["migration"]["fromVersion"], 4)
            self.assertEqual(restored["migration"]["toVersion"], CURRENT_SCHEMA_VERSION)
            self.assertTrue((vault / "original.md").exists())
            self.assertFalse((vault / "live-only.md").exists())

    def test_restore_rolls_back_vault_when_database_swap_fails(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            root_path = Path(root)
            vault = root_path / "vault"
            vault.mkdir()
            (vault / "backup.md").write_text("# Backup", encoding="utf-8")
            database_path = root_path / "berrybrain.db"
            engine = create_engine(f"sqlite:///{database_path}")
            Base.metadata.create_all(engine)
            apply_schema_migrations(engine)
            session_factory = sessionmaker(bind=engine)
            settings = SimpleNamespace(
                vault_path=vault,
                backup_path=root_path / "backups",
                database_url=f"sqlite:///{database_path}",
            )
            with (
                patch("berrybrain_api.backup.SessionLocal", session_factory),
                patch("berrybrain_api.backup.get_settings", return_value=settings),
                patch("berrybrain_api.backup.database_engine", engine),
            ):
                backup = create_backup()
                (vault / "live-only.md").write_text("# Keep me", encoding="utf-8")
                real_replace = os.replace

                def fail_database_swap(source, destination):
                    if (
                        Path(destination) == database_path
                        and ".restore-" in Path(source).name
                    ):
                        raise OSError("simulated database swap failure")
                    return real_replace(source, destination)

                with patch(
                    "berrybrain_api.backup.os.replace", side_effect=fail_database_swap
                ):
                    with self.assertRaisesRegex(OSError, "simulated"):
                        restore_backup(str(backup["id"]))

            self.assertTrue((vault / "live-only.md").exists())
            self.assertTrue((vault / "backup.md").exists())
            leftovers = [
                path
                for path in root_path.iterdir()
                if ".restore-" in path.name or ".rollback-" in path.name
            ]
            self.assertEqual(leftovers, [])


if __name__ == "__main__":
    unittest.main()
