import tempfile
import unittest
from pathlib import Path

from fastapi import HTTPException
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from berrybrain_api.database import Base
from berrybrain_api.generated_metadata import upsert_generated_metadata
from berrybrain_api.models import NoteRecord
from berrybrain_api.sync import sync_note_record
from berrybrain_api.vault import (
    create_note,
    extract_internal_links,
    parse_markdown_note,
    resolve_note_path,
)


class VaultMetadataTest(unittest.TestCase):
    def test_parse_markdown_note_extracts_frontmatter_body_and_links(self) -> None:
        content = """---
note_type: aula
language: pt-BR
tags:
  - python
aliases: [IA local, machine learning]
---
# IA local

Conecta [[Machine Learning|ML]] com [[estudos/Ollama]].
"""

        metadata = parse_markdown_note(content)

        self.assertEqual(metadata.frontmatter["note_type"], "aula")
        self.assertEqual(metadata.frontmatter["language"], "pt-BR")
        self.assertEqual(metadata.frontmatter["tags"], ["python"])
        self.assertEqual(
            metadata.frontmatter["aliases"], ["IA local", "machine learning"]
        )
        self.assertTrue(metadata.body.startswith("# IA local"))
        self.assertEqual(metadata.links, ["Machine Learning", "estudos/Ollama"])

    def test_extract_internal_links_ignores_duplicates_and_headings(self) -> None:
        content = "Veja [[Nota]], [[Nota#Secao]] e [[Outra Nota|alias]]."

        self.assertEqual(extract_internal_links(content), ["Nota", "Outra Nota"])

    def test_sync_note_record_upserts_markdown_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            vault_path = Path(temp_dir) / "vault"
            note_path = vault_path / "inbox" / "ia-local.md"
            note_path.parent.mkdir(parents=True)
            note_path.write_text(
                "---\nnote_type: aula\nlanguage: pt-BR\n---\n# IA Local\n\nLink [[Ollama]].\n",
                encoding="utf-8",
            )

            engine = create_engine(
                "sqlite:///:memory:", connect_args={"check_same_thread": False}
            )
            Base.metadata.create_all(bind=engine)
            session = sessionmaker(bind=engine)()

            record = sync_note_record(session, vault_path, "inbox/ia-local.md")

            loaded = session.execute(
                select(NoteRecord).where(NoteRecord.path == "inbox/ia-local.md")
            ).scalar_one()
            self.assertEqual(record.id, loaded.id)
            self.assertEqual(loaded.title, "IA Local")
            self.assertEqual(loaded.slug, "ia-local")
            self.assertEqual(loaded.note_type, "aula")
            self.assertEqual(loaded.language, "pt-BR")
            self.assertTrue(loaded.content_hash)
            self.assertEqual(
                loaded.frontmatter, '{"language":"pt-BR","note_type":"aula"}'
            )
            self.assertEqual(loaded.links, '["Ollama"]')

    def test_generated_metadata_rejects_stale_content_hash(self) -> None:
        engine = create_engine(
            "sqlite:///:memory:", connect_args={"check_same_thread": False}
        )
        Base.metadata.create_all(bind=engine)
        session = sessionmaker(bind=engine)()
        note = NoteRecord(
            path="inbox/a.md",
            title="A",
            slug="a",
            content="# A",
            content_hash="current",
        )
        session.add(note)
        session.commit()
        session.refresh(note)

        with self.assertRaises(Exception):
            upsert_generated_metadata(
                session,
                note.id,
                "summary",
                {"summary": "old"},
                "old",
                "model",
            )

        stored = upsert_generated_metadata(
            session,
            note.id,
            "summary",
            {"summary": "current"},
            "current",
            "model",
        )
        self.assertEqual(stored.content_hash, "current")

    def test_create_note_allows_empty_title_with_incremental_draft_slug(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            vault_path = Path(temp_dir) / "vault"

            first = create_note(vault_path, "", "inbox", "")
            second = create_note(vault_path, "", "inbox", "")

            self.assertEqual(first["path"], "inbox/rascunho.md")
            self.assertEqual(second["path"], "inbox/rascunho-2.md")
            self.assertTrue((vault_path / "inbox" / "rascunho.md").exists())
            self.assertTrue((vault_path / "inbox" / "rascunho-2.md").exists())

    def test_resolve_note_path_rejects_paths_outside_vault(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            vault_path = Path(temp_dir) / "vault"

            for unsafe_path in (
                "../outside.md",
                "inbox/../../outside.md",
                "/tmp/outside.md",
                "inbox\\outside.md",
            ):
                with self.subTest(path=unsafe_path), self.assertRaises(HTTPException):
                    resolve_note_path(vault_path, unsafe_path)

    def test_resolve_note_path_rejects_symlink_escape(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            vault_path = root / "vault"
            inbox = vault_path / "inbox"
            inbox.mkdir(parents=True)
            outside = root / "outside.md"
            outside.write_text("outside", encoding="utf-8")
            (inbox / "linked.md").symlink_to(outside)

            with self.assertRaises(HTTPException):
                resolve_note_path(vault_path, "inbox/linked.md")


if __name__ == "__main__":
    unittest.main()
