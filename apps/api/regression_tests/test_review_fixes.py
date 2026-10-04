"""Product-only regressions. No benchmark, provider, production DB or vault.

Run this module directly in a separate process; it sets an empty project root
before importing application configuration. It deliberately is not TCC evidence.
"""

import asyncio
import atexit
import importlib.util
import os
import shutil
import sqlite3
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

_sandbox = tempfile.TemporaryDirectory(prefix="berrybrain-regression-")
atexit.register(_sandbox.cleanup)
os.environ.update(
    {
        "BERRYBRAIN_PROJECT_ROOT": _sandbox.name,
        "BERRYBRAIN_DATABASE_URL": f"sqlite:///{_sandbox.name}/import-only.db",
        "BERRYBRAIN_VAULT_PATH": f"{_sandbox.name}/vault",
        "BERRYBRAIN_VAULT_WATCHER_ENABLED": "false",
        "BERRYBRAIN_ENABLE_DEFAULT_OWNER": "false",
        "BERRYBRAIN_LOG_PATH": f"{_sandbox.name}/logs",
    }
)

from fastapi import HTTPException  # noqa: E402
from sqlalchemy import create_engine, select, update  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402

from berrybrain_api import backup, config, vault, vector_store  # noqa: E402
from berrybrain_api.attachment_cleanup import (  # noqa: E402
    drain_attachment_cleanup,
    queue_attachment_cleanup,
)
from berrybrain_api.cognitive_query import _validated_citations  # noqa: E402
from berrybrain_api.database import Base  # noqa: E402
from berrybrain_api.filesystem import atomic_write_text, vault_lock  # noqa: E402
from berrybrain_api.jobs import complete_job, lock_worker_claim  # noqa: E402
from berrybrain_api.models import (  # noqa: E402
    JobRecord,
    NoteAttachmentRecord,
    NoteRecord,
)
from berrybrain_api.runtime_guard import (  # noqa: E402
    MaintenanceUnavailable,
    database_lease,
    exclusive_database_access,
    install_database_guard,
    restore_marker,
)
from berrybrain_api.vector_cleanup import (  # noqa: E402
    drain_vector_cleanup,
    queue_vector_cleanup,
    register_collection,
)

# Build the empty schema once; each test still receives its own on-disk database.
_schema_path = Path(_sandbox.name) / "empty-schema.db"
_schema_engine = create_engine(f"sqlite:///{_schema_path}")
Base.metadata.create_all(_schema_engine)
_schema_engine.dispose()


class ReviewRegressions(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=_sandbox.name)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.vault = self.root / "vault"
        self.vault.mkdir()
        self.db = self.root / "test.db"
        shutil.copyfile(_schema_path, self.db)
        self.engine = create_engine(f"sqlite:///{self.db}")
        self.addCleanup(self.engine.dispose)
        self.session = Session(self.engine)
        self.addCleanup(self.session.close)
        self.settings = config.Settings(
            _env_file=None, vault_path=self.vault, database_url=f"sqlite:///{self.db}"
        )
        patcher = patch(
            "berrybrain_api.config.get_settings", return_value=self.settings
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        network = patch(
            "socket.create_connection",
            side_effect=AssertionError("Network forbidden in product regression"),
        )
        network.start()
        self.addCleanup(network.stop)

    def note(self, content="# Current\ncanonical text", path="inbox/current.md"):
        target = self.vault / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)
        note = NoteRecord(
            title="Current",
            slug=target.stem,
            path=path,
            content=content,
            content_hash=vault.parse_markdown_note(content).content_hash,
        )
        self.session.add(note)
        self.session.commit()
        return note

    def job(self, note=None):
        job = JobRecord(
            type="GENERATE_EMBEDDING",
            status="running",
            claim_token="valid",
            attempts=1,
            lease_expires_at=datetime.now(UTC) + timedelta(minutes=10),
        )
        if note:
            job.note_id, job.note_path, job.content_hash = (
                note.id,
                note.path,
                note.content_hash,
            )
        self.session.add(job)
        self.session.commit()
        return job

    def test_atomic_create_never_overwrites(self):
        target = self.vault / "existing.md"
        atomic_write_text(target, "original", overwrite=False)
        with self.assertRaises(FileExistsError):
            atomic_write_text(target, "lost", overwrite=False)
        self.assertEqual(target.read_text(), "original")
        self.assertEqual(list(self.vault.glob(".berrybrain-write-*")), [])

    def test_compare_and_swap_only_one_writer_wins(self):
        item = self.note()
        old_hash = item.content_hash
        barrier = threading.Barrier(2)

        def write(content):
            barrier.wait()
            try:
                vault.update_note(
                    self.vault, item.path, content, expected_content_hash=old_hash
                )
                return 200
            except HTTPException as error:
                return error.status_code

        with ThreadPoolExecutor(2) as pool:
            self.assertEqual(sorted(pool.map(write, ["new A", "new B"])), [200, 409])

    def test_nested_rename_preserves_parent(self):
        note = self.note(path="projects/deep/original.md")
        result = vault.rename_note(self.vault, note.path, "New name")
        self.assertEqual(result["path"], "projects/deep/new-name.md")
        self.assertFalse((self.vault / note.path).exists())

    def test_folder_root_cannot_be_deleted_or_renamed(self):
        from berrybrain_api.routers import folders

        with patch.object(folders, "get_settings", return_value=self.settings):
            for operation in (
                lambda: folders.delete_folder("."),
                lambda: folders.rename_folder(".", {"name": "x"}),
            ):
                with self.assertRaises(HTTPException) as failure:
                    operation()
                self.assertEqual(failure.exception.status_code, 400)
        self.assertTrue(self.vault.exists())

    def test_folder_rename_preserves_duplicate_content_identities(self):
        from berrybrain_api.routers import folders, notes

        first = self.note(path="projects/old/a.md")
        second = self.note(path="projects/old/b.md")
        expected = {first.id: first.stable_id, second.id: second.stable_id}
        self.session.close()
        with (
            patch.object(folders, "get_settings", return_value=self.settings),
            patch.object(notes, "get_settings", return_value=self.settings),
            patch.object(folders, "SessionLocal", sessionmaker(self.engine)),
        ):
            folders.rename_folder("projects/old", {"name": "new"})
        rows = list(self.session.scalars(select(NoteRecord)))
        self.assertEqual({row.id: row.stable_id for row in rows}, expected)
        self.assertEqual(
            {row.path for row in rows}, {"projects/new/a.md", "projects/new/b.md"}
        )

    def test_attachment_chunk_ids_are_uuid(self):
        from uuid import UUID

        identity = vector_store._stable_attachment_chunk_id(12, 3)
        self.assertEqual(str(UUID(identity)), identity)
        self.assertEqual(identity, vector_store._stable_attachment_chunk_id(12, 3))

    def test_overlapping_chunks_share_text(self):
        self.assertEqual(
            vector_store.chunk_markdown("abcdefghijklmnop", 8, 3),
            ["abcdefgh", "fghijklm", "klmnop"],
        )

    def test_invalid_overlap_rejected(self):
        with self.assertRaises(ValueError):
            vector_store.chunk_markdown("text", 8, 8)

    def test_embedding_input_roles_are_distinct(self):
        configuration = {"embedding_provider": "cloud", "embedding_model": "test"}
        with patch.object(
            vector_store, "generate_query_embedding", return_value=[1.0, 0.0]
        ) as embed:
            vector_store._generate_chunk_embedding(configuration, "passage")
            self.assertEqual(embed.call_args.kwargs["input_type"], "passage")
            vector_store._generate_chunk_embedding(
                configuration, "question", input_type="query"
            )
            self.assertEqual(embed.call_args.kwargs["input_type"], "query")

    def test_chroma_v2_default_and_explicit_legacy(self):
        self.assertEqual(
            vector_store._chroma_collections_url({"chroma_url": "http://chroma"}),
            "http://chroma/api/v2/tenants/default_tenant/databases/default_database/collections",
        )
        self.assertEqual(
            vector_store._chroma_collections_url({"chroma_url": "http://old/api/v1"}),
            "http://old/api/v1/collections",
        )

    def test_citations_reject_unknown_and_fabricated_quotes(self):
        source = {
            "evidenceId": "e1",
            "text": "A genuine quotation",
            "metadata": {"noteId": 7, "path": "real.md"},
        }
        self.assertEqual(_validated_citations(["invented"], [source]), [])
        self.assertEqual(_validated_citations([], [source]), [])
        self.assertEqual(
            _validated_citations(
                [{"evidenceId": "e1", "quote": "fabricated"}], [source]
            ),
            [],
        )

    def test_citations_use_server_metadata_not_model_metadata(self):
        source = {
            "evidenceId": "e1",
            "text": "genuine",
            "metadata": {"noteId": 7, "path": "real.md"},
        }
        result = _validated_citations(
            [{"evidenceId": "e1", "path": "fake.md", "noteId": 999}], [source]
        )
        self.assertEqual((result[0]["path"], result[0]["noteId"]), ("real.md", 7))

    def test_external_evidence_rejects_old_schema_and_stale_content(self):
        note = self.note()
        evidence = vector_store.RetrievalEvidence(
            "knowledge_base", note.title, "canonical text", 1.0, {"noteId": note.id}
        )
        self.assertEqual(
            vector_store.validate_external_evidence(self.session, [evidence]), []
        )
        evidence.metadata.update(
            noteStableId=note.stable_id, contentHash=note.content_hash
        )
        self.assertEqual(
            len(vector_store.validate_external_evidence(self.session, [evidence])), 1
        )
        (self.vault / note.path).write_text("# Changed elsewhere")
        self.assertEqual(
            vector_store.validate_external_evidence(self.session, [evidence]), []
        )

    def test_worker_claim_requires_nonempty_current_token(self):
        job = self.job()
        for token in ("", "wrong"):
            with self.assertRaises(HTTPException):
                lock_worker_claim(self.session, job, token)
            self.session.rollback()
        lock_worker_claim(self.session, job, "valid")

    def test_worker_claim_rejects_stale_note_version(self):
        note = self.note()
        job = self.job(note)
        note.content_hash = "newer-version"
        self.session.commit()
        with self.assertRaises(HTTPException):
            lock_worker_claim(self.session, job, "valid")

    def test_worker_claim_checks_database_not_stale_orm(self):
        job = self.job()
        identity = job.id
        self.session.commit()
        _ = job.status
        with Session(self.engine) as other:
            other.execute(
                update(JobRecord)
                .where(JobRecord.id == identity)
                .values(status="superseded", claim_token="")
            )
            other.commit()
        with self.assertRaises(HTTPException):
            lock_worker_claim(self.session, job, "valid")

    def test_expired_worker_lease_rejected(self):
        job = self.job()
        job.lease_expires_at = datetime.now(UTC) - timedelta(seconds=1)
        self.session.commit()
        with self.assertRaises(HTTPException):
            lock_worker_claim(self.session, job, "valid")

    def test_completed_job_accepts_only_legitimate_duplicate_message(self):
        job = self.job()
        identity = job.id
        self.assertEqual(
            complete_job(self.session, identity, "valid").status, "completed"
        )
        self.assertEqual(
            complete_job(self.session, identity, "valid").status, "completed"
        )
        with self.assertRaises(HTTPException):
            complete_job(self.session, identity, "wrong")

    def test_superseded_job_cannot_be_completed(self):
        job = self.job()
        job.status = "superseded"
        self.session.commit()
        with self.assertRaises(HTTPException):
            complete_job(self.session, job.id, "valid")
        self.session.rollback()
        self.assertEqual(job.status, "superseded")

    def test_database_lease_blocks_restore_before_changes(self):
        with database_lease(self.db):
            with (
                self.assertRaises(HTTPException) as failure,
                exclusive_database_access(self.db, timeout=0),
            ):
                self.fail("Exclusive access granted despite active reader")
            self.assertEqual(failure.exception.status_code, 409)

    def test_guard_applies_to_sqlalchemy_checkouts(self):
        install_database_guard(self.engine)
        with (
            self.engine.connect(),
            self.assertRaises(HTTPException),
            exclusive_database_access(self.db, timeout=0),
        ):
            self.fail("Guarded connection was ignored")

    def test_interrupted_restore_fails_closed(self):
        restore_marker(self.db).write_text('{"phase":"prepared"}')
        with self.assertRaises(MaintenanceUnavailable), database_lease(self.db):
            self.fail("Pending restore ignored")
        (self.vault / ".berrybrain-restore" / "restore-pending").mkdir(parents=True)
        with self.assertRaises(HTTPException), vault_lock(self.vault):
            self.fail("Partial vault exposed")

    def prepare_restore(self):
        self.session.close()
        self.engine.dispose()
        (self.vault / "old.md").write_text("old vault")
        staged_vault = self.root / "staged"
        staged_vault.mkdir()
        (staged_vault / "new.md").write_text("new vault")
        staged_db = self.root / "staged.db"
        with closing(sqlite3.connect(staged_db)) as connection:
            connection.execute("create table proof(value text)")
            connection.execute("insert into proof values ('new database')")
            connection.commit()
        return staged_vault, staged_db

    def test_restore_preserves_mount_root_and_commits_database(self):
        staged_vault, staged_db = self.prepare_restore()
        inode = self.vault.stat().st_ino
        with patch.object(backup, "_dispose_database_engines"):
            backup._commit_prepared_restore(
                database_path=self.db,
                staged_database=staged_db,
                vault_path=self.vault,
                staged_vault=staged_vault,
                restore_id="regression",
            )
        self.assertEqual(self.vault.stat().st_ino, inode)
        self.assertFalse((self.vault / "old.md").exists())
        self.assertEqual((self.vault / "new.md").read_text(), "new vault")
        with closing(sqlite3.connect(self.db)) as connection:
            self.assertEqual(
                connection.execute("select value from proof").fetchone()[0],
                "new database",
            )
        self.assertFalse(restore_marker(self.db).exists())
        self.assertEqual(list((self.vault / ".berrybrain-restore").iterdir()), [])

    def test_restore_rolls_back_vault_on_database_failure(self):
        staged_vault, staged_db = self.prepare_restore()
        original_copy = backup._copy_sqlite_snapshot

        def fail_install(source, target):
            if source == staged_db:
                raise OSError("injected install failure")
            return original_copy(source, target)

        with (
            patch.object(backup, "_dispose_database_engines"),
            patch.object(backup, "_copy_sqlite_snapshot", side_effect=fail_install),
            self.assertRaises(OSError),
        ):
            backup._commit_prepared_restore(
                database_path=self.db,
                staged_database=staged_db,
                vault_path=self.vault,
                staged_vault=staged_vault,
                restore_id="failure",
            )
        self.assertEqual((self.vault / "old.md").read_text(), "old vault")
        self.assertFalse((self.vault / "new.md").exists())
        self.assertFalse(restore_marker(self.db).exists())

    def attachment(self):
        note = self.note()
        target = self.vault / ".attachments" / "test.bin"
        target.parent.mkdir()
        target.write_bytes(b"test")
        item = NoteAttachmentRecord(
            note_id=note.id,
            note_path=note.path,
            filename="test.bin",
            stored_path=".attachments/test.bin",
        )
        self.session.add(item)
        self.session.commit()
        return item, target

    def test_attachment_cleanup_is_post_commit_and_idempotent(self):
        item, target = self.attachment()
        queue_attachment_cleanup(self.session, [item])
        self.session.delete(item)
        self.assertTrue(target.exists())
        self.session.commit()
        self.assertEqual(
            drain_attachment_cleanup(self.session, self.vault)["completed"], 1
        )
        self.assertFalse(target.exists())
        self.assertEqual(
            drain_attachment_cleanup(self.session, self.vault)["completed"], 0
        )

    def test_attachment_cleanup_preserves_current_owner(self):
        item, target = self.attachment()
        queue_attachment_cleanup(self.session, [item])
        self.session.commit()
        drain_attachment_cleanup(self.session, self.vault)
        self.assertTrue(target.exists())

    def test_vector_cleanup_rollback_does_not_reach_network(self):
        note = self.note()
        register_collection(self.session, "qdrant", "http://fake", "test")
        self.session.commit()
        queue_vector_cleanup(self.session, note)
        self.session.rollback()
        with patch.object(vector_store, "_http_json") as request:
            self.assertEqual(drain_vector_cleanup(self.session)["completed"], 0)
            request.assert_not_called()

    def test_vector_cleanup_failed_request_remains_queued_and_retries_scoped(self):
        note = self.note()
        register_collection(self.session, "qdrant", "http://fake", "test")
        self.session.commit()
        queue_vector_cleanup(self.session, note)
        self.session.commit()
        with patch.object(vector_store, "_http_json", side_effect=OSError("offline")):
            self.assertEqual(drain_vector_cleanup(self.session)["pending"], 1)
        with patch.object(vector_store, "_http_json", return_value={}) as request:
            self.assertEqual(drain_vector_cleanup(self.session)["completed"], 1)
            match = {
                item["key"]: item["match"]["value"]
                for item in request.call_args.args[2]["filter"]["must"]
            }
            self.assertEqual(match["note_stable_id"], note.stable_id)
            self.assertEqual(match["content_hash"], note.content_hash)
            self.assertEqual(match["source"], "berrybrain")

    def test_authenticated_browser_mutation_requires_csrf_globally(self):
        import httpx

        from berrybrain_api import main

        async def request():
            with (
                patch.object(main, "SessionLocal", sessionmaker(self.engine)),
                patch.object(
                    main, "get_session_user", return_value=(object(), object())
                ),
                patch.object(
                    main,
                    "assert_csrf",
                    side_effect=HTTPException(403, "CSRF token required"),
                ),
            ):
                async with httpx.AsyncClient(
                    transport=httpx.ASGITransport(app=main.app),
                    base_url="http://testserver",
                    cookies={main.settings.session_cookie_name: "mock-session"},
                ) as client:
                    response = await client.post(
                        "/api/v1/notes", json={"content": "must not write"}
                    )
                    self.assertEqual(response.status_code, 403)
                    self.assertEqual(response.json()["detail"], "CSRF token required")

        asyncio.run(request())
        self.assertEqual(list(self.vault.rglob("*.md")), [])

    def test_worker_urls_preserve_reserved_characters(self):
        import httpx

        source = (
            Path(__file__).resolve().parents[2]
            / "worker/src/berrybrain_worker/api_client.py"
        )
        spec = importlib.util.spec_from_file_location(
            "review_worker_api_client", source
        )
        worker = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(worker)
        requests = []

        def handle(request):
            requests.append(request)
            return httpx.Response(200, json={})

        note_path = "inbox/ação #1 ? & +.md"

        async def request():
            async with httpx.AsyncClient(
                transport=httpx.MockTransport(handle)
            ) as client:
                await worker.fetch_note(client, "http://api", note_path)
                await worker.upsert_metadata(
                    client,
                    "http://api",
                    note_path,
                    "insights/scope",
                    {},
                    "hash",
                    "mock",
                )

        asyncio.run(request())
        self.assertEqual(requests[0].url.path, "/api/v1/notes/" + note_path)
        self.assertEqual(requests[0].url.query, b"")
        self.assertEqual(requests[0].url.fragment, "")
        self.assertEqual(requests[1].url.params["note_path"], note_path)
        self.assertEqual(requests[1].url.path, "/api/v1/metadata/insights/scope")


if __name__ == "__main__":
    unittest.main(verbosity=2)
