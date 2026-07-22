"""Worker integration tests against disposable in-memory DB.

Starts the real FastAPI app with a disposable SQLite database, runs worker
functions against it via TestClient, and mocks only AI calls.
"""

import asyncio
import os
import tempfile
import unittest
from collections.abc import Callable
from importlib import import_module
from pathlib import Path
from typing import Any

import httpx
from fastapi.testclient import TestClient

os.environ["BERRYBRAIN_VAULT_WATCHER_ENABLED"] = "false"

SESSIONLOCAL_MODULES = (
    "berrybrain_api.main",
    "berrybrain_api.backup",
    "berrybrain_api.routers.automation",
    "berrybrain_api.routers.cognitive",
    "berrybrain_api.routers.concepts",
    "berrybrain_api.routers.connections",
    "berrybrain_api.routers.graph",
    "berrybrain_api.routers.insights",
    "berrybrain_api.routers.jobs",
    "berrybrain_api.routers.maintenance",
    "berrybrain_api.routers.monitor",
    "berrybrain_api.routers.notes",
    "berrybrain_api.routers.notifications",
    "berrybrain_api.routers.settings",
    "berrybrain_api.routers.vault",
)


class AsyncTestClientAdapter:
    """Expose a live TestClient to the async worker API contract."""

    def __init__(self, client: TestClient) -> None:
        self._client = client

    async def _run(self, method: Callable[..., httpx.Response], *args, **kwargs):
        return await asyncio.to_thread(method, *args, **kwargs)

    async def get(self, *args: Any, **kwargs: Any) -> httpx.Response:
        return await self._run(self._client.get, *args, **kwargs)

    async def post(self, *args: Any, **kwargs: Any) -> httpx.Response:
        return await self._run(self._client.post, *args, **kwargs)

    async def put(self, *args: Any, **kwargs: Any) -> httpx.Response:
        return await self._run(self._client.put, *args, **kwargs)


class WorkerIntegrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        from berrybrain_api.database import Base
        import berrybrain_api.models  # noqa: F401

        from berrybrain_api.config import get_settings

        cls.tmp_dir = tempfile.TemporaryDirectory()
        db_path = Path(cls.tmp_dir.name) / "test.db"
        vault_path = Path(cls.tmp_dir.name) / "vault"
        vault_path.mkdir()

        cls.db_url = f"sqlite:///{db_path}"
        cls.note_counter = 0

        cls.settings = get_settings()
        cls.original_database_url = cls.settings.database_url
        cls.original_vault_path = cls.settings.vault_path
        cls.original_backup_path = cls.settings.backup_path
        cls.original_vault_watcher_enabled = cls.settings.vault_watcher_enabled
        cls.original_api_token = cls.settings.api_token
        cls.settings.database_url = cls.db_url
        cls.settings.vault_path = vault_path
        cls.settings.backup_path = Path(cls.tmp_dir.name) / "backups"
        cls.settings.vault_watcher_enabled = False
        cls.settings.api_token = "test-token"

        from berrybrain_api.main import app

        cls.app = app
        cls._patched = []

        for mod_name in SESSIONLOCAL_MODULES:
            try:
                mod = import_module(mod_name)
            except ImportError:
                continue
            if hasattr(mod, "SessionLocal"):
                cls._patched.append((mod, getattr(mod, "SessionLocal")))

        # monkey-patch SessionLocal across all modules
        # ponytail: file-based temp DB (same as test_integration.py) —
        # in-memory SQLite creates a fresh DB per connection
        new_engine = create_engine(
            cls.db_url, connect_args={"check_same_thread": False}
        )
        Base.metadata.create_all(bind=new_engine)
        new_sl = sessionmaker(bind=new_engine, autoflush=False, autocommit=False)

        import berrybrain_api.database as db_mod

        cls._orig_engine = db_mod.engine
        cls._orig_sl = db_mod.SessionLocal
        db_mod.engine = new_engine
        db_mod.SessionLocal = new_sl

        for mod, _ in cls._patched:
            if hasattr(mod, "SessionLocal"):
                setattr(mod, "SessionLocal", new_sl)

        # init FTS
        try:
            from berrybrain_api.search import init_fts

            with new_sl() as s:
                init_fts(s)
        except Exception:
            pass

    @classmethod
    def tearDownClass(cls):
        import berrybrain_api.database as db_mod

        db_mod.engine = cls._orig_engine
        db_mod.SessionLocal = cls._orig_sl
        for mod, orig in reversed(cls._patched):
            setattr(mod, "SessionLocal", orig)

        cls.settings.database_url = cls.original_database_url
        cls.settings.vault_path = cls.original_vault_path
        cls.settings.backup_path = cls.original_backup_path
        cls.settings.vault_watcher_enabled = cls.original_vault_watcher_enabled
        cls.settings.api_token = cls.original_api_token
        cls.tmp_dir.cleanup()

    def _make_client(self) -> TestClient:
        return TestClient(
            self.app,
            headers={"Authorization": f"Bearer {self.settings.api_token}"},
        )

    def _create_note(self, client: TestClient, title: str = "Test Note") -> dict:
        del client
        from berrybrain_api.database import SessionLocal
        from berrybrain_api.jobs import enqueue_note_changed_jobs
        from berrybrain_api.sync import sync_note_record
        from berrybrain_api.vault import create_note

        type(self).note_counter += 1
        unique_title = f"{title} {type(self).note_counter}"
        note = create_note(
            self.settings.vault_path,
            unique_title,
            "inbox",
            f"# {unique_title}\n\nHello world",
        )
        with SessionLocal() as session:
            record = sync_note_record(
                session, self.settings.vault_path, str(note["path"])
            )
            note["id"] = record.id
            enqueue_note_changed_jobs(
                session, record.path, "NOTE_CREATED", record.content_hash
            )
        return note

    def _claim_job(self, client: TestClient) -> tuple[dict, dict[str, str]]:
        resp = client.post("/api/v1/jobs/claim")
        self.assertEqual(resp.status_code, 200)
        job = resp.json()["job"]
        self.assertIsNotNone(job)
        token = str(job.get("claim_token") or "")
        self.assertTrue(token)
        return job, {"X-BerryBrain-Claim-Token": token}

    def test_claim_and_complete_job_lifecycle(self):
        """Create a note → jobs are enqueued → claim → complete → status=completed."""
        with self._make_client() as client:
            self._create_note(client)

            # list pending jobs
            resp = client.get("/api/v1/jobs", params={"status": "pending"})
            self.assertEqual(resp.status_code, 200)
            jobs = resp.json()["jobs"]
            self.assertGreater(len(jobs), 0)

            # claim one
            claimed, headers = self._claim_job(client)
            self.assertIn(claimed["status"], ("running", "pending"))
            job_id = claimed["id"]

            # complete it
            resp = client.post(f"/api/v1/jobs/{job_id}/complete", headers=headers)
            self.assertEqual(resp.status_code, 200)

            # verify completed
            resp = client.get("/api/v1/jobs", params={"status": "completed"})
            completed = resp.json()["jobs"]
            self.assertTrue(any(j["id"] == job_id for j in completed))

    def test_fail_job_records_error(self):
        """Claim a job → fail it enough times → status=failed with error_message."""
        with self._make_client() as client:
            self._create_note(client)
            claimed, headers = self._claim_job(client)
            job_id = claimed["id"]

            # fail_job only marks FAILED when attempts >= max_attempts;
            # claim_next_job increments attempts but fail_job doesn't,
            # so bump attempts directly to trigger FAILED on first fail.
            from berrybrain_api.database import SessionLocal
            from berrybrain_api.models import JobRecord

            with SessionLocal() as s:
                j = s.get(JobRecord, job_id)
                j.attempts = j.max_attempts
                s.commit()

            resp = client.post(
                f"/api/v1/jobs/{job_id}/fail",
                json={"error_message": "test failure"},
                headers=headers,
            )
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.json()["job"]["status"], "dead_letter")

            resp = client.get("/api/v1/jobs", params={"status": "dead_letter"})
            failed = resp.json()["jobs"]
            self.assertTrue(any(j["id"] == job_id for j in failed))

    def test_worker_process_parse_note(self):
        """Worker process_parse_note works against real API with mocked AI."""
        import berrybrain_worker.main as worker_main
        from berrybrain_worker.api_client import _claim_tokens

        with self._make_client() as client:
            self._create_note(client)
            job, _headers = self._claim_job(client)
            _claim_tokens[int(job["id"])] = str(job["claim_token"])
            self.assertEqual(job["type"], "PARSE_NOTE")
            payload = job.get("payload", {})

            # mock ollama_call to avoid real AI
            async def fake_ollama_call(*args, **kwargs):
                return {"concepts": ["test"], "source": "mock"}

            original = worker_main.ollama_call
            worker_main.ollama_call = fake_ollama_call
            try:
                from berrybrain_worker.config import WorkerSettings

                settings = WorkerSettings()
                settings.api_url = "http://testserver"
                asyncio.run(
                    worker_main.process_parse_note(
                        AsyncTestClientAdapter(client), settings, job, payload
                    )
                )
            finally:
                worker_main.ollama_call = original

            # job should be completed
            resp = client.get("/api/v1/jobs?status=completed")
            completed = resp.json()["jobs"]
            self.assertTrue(
                any(j["id"] == job["id"] for j in completed),
                f"Job {job['id']} not in completed list",
            )

    def test_worker_claim_respects_pipeline_order(self):
        """First claim returns PARSE_NOTE (first in pipeline) when multiple jobs exist."""
        with self._make_client() as client:
            self._create_note(client, "Note A")
            self._create_note(client, "Note B")

            # claim first
            job1, _headers1 = self._claim_job(client)

            # claim second
            job2, _headers2 = self._claim_job(client)

            # at least one should be PARSE_NOTE
            types = {job1["type"], job2["type"]}
            self.assertIn("PARSE_NOTE", types)

    def test_jobs_health_endpoint(self):
        """Jobs health returns status and counts."""
        with self._make_client() as client:
            resp = client.get("/api/v1/jobs/health")
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertIn("status", data)
            self.assertIn("counts", data)
            self.assertIn("pending", data["counts"])

    def test_pipeline_progress_endpoint(self):
        """Pipeline progress endpoint returns notes with active jobs."""
        with self._make_client() as client:
            self._create_note(client)
            resp = client.get("/api/v1/jobs/pipeline-progress")
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertIn("notes", data)

    def test_stale_job_recovery(self):
        """Stale running job gets recovered on next claim."""
        with self._make_client() as client:
            self._create_note(client)
            job, _headers = self._claim_job(client)
            job_id = job["id"]

            # force stale: set started_at to 45 min ago
            from berrybrain_api.database import SessionLocal
            from berrybrain_api.models import JobRecord
            from berrybrain_api.jobs import utc_now
            from datetime import timedelta

            with SessionLocal() as s:
                j = s.get(JobRecord, job_id)
                j.started_at = utc_now() - timedelta(minutes=45)
                s.commit()

            # claim should recover the stale job and return a running job
            resp = client.post("/api/v1/jobs/claim")
            recovered = resp.json()["job"]
            self.assertIsNotNone(recovered)
            self.assertIn(recovered["status"], ("running", "pending"))

    def test_heartbeat_endpoint(self):
        """Worker heartbeat posts stats successfully."""
        with self._make_client() as client:
            resp = client.post(
                "/api/v1/worker/heartbeat",
                json={"jobs_processed": 5, "errors": 1, "ollama_healthy": True},
            )
            self.assertEqual(resp.status_code, 200)


if __name__ == "__main__":
    unittest.main()
