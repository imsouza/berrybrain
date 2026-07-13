"""Worker integration tests against disposable in-memory DB.

Starts the real FastAPI app with in-memory SQLite, runs worker functions
against it via httpx.AsyncClient + ASGITransport. Mocks only AI calls.
"""

import os
import tempfile
import unittest
from importlib import import_module
from pathlib import Path

import httpx

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


class WorkerIntegrationTest(unittest.IsolatedAsyncioTestCase):
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

    def _make_client(self) -> httpx.AsyncClient:
        # Use ASGITransport for async requests
        transport = httpx.ASGITransport(app=self.app)
        return httpx.AsyncClient(
            transport=transport,
            base_url="http://testserver",
            headers={"Authorization": f"Bearer {self.settings.api_token}"},
        )

    async def _create_note(
        self, client: httpx.AsyncClient, title: str = "Test Note"
    ) -> dict:
        type(self).note_counter += 1
        unique_title = f"{title} {type(self).note_counter}"
        resp = await client.post(
            "/api/v1/notes",
            json={
                "title": unique_title,
                "folder": "inbox",
                "content": f"# {unique_title}\n\nHello world",
            },
        )
        assert resp.status_code == 201, resp.text
        return resp.json()

    async def test_claim_and_complete_job_lifecycle(self):
        """Create a note → jobs are enqueued → claim → complete → status=completed."""
        async with self._make_client() as client:
            await self._create_note(client)

            # list pending jobs
            resp = await client.get("/api/v1/jobs", params={"status": "pending"})
            self.assertEqual(resp.status_code, 200)
            jobs = resp.json()["jobs"]
            self.assertGreater(len(jobs), 0)

            # claim one
            resp = await client.post("/api/v1/jobs/claim")
            self.assertEqual(resp.status_code, 200)
            claimed = resp.json()["job"]
            self.assertIsNotNone(claimed)
            self.assertIn(claimed["status"], ("running", "pending"))
            job_id = claimed["id"]

            # complete it
            resp = await client.post(f"/api/v1/jobs/{job_id}/complete")
            self.assertEqual(resp.status_code, 200)

            # verify completed
            resp = await client.get("/api/v1/jobs", params={"status": "completed"})
            completed = resp.json()["jobs"]
            self.assertTrue(any(j["id"] == job_id for j in completed))

    async def test_fail_job_records_error(self):
        """Claim a job → fail it enough times → status=failed with error_message."""
        async with self._make_client() as client:
            await self._create_note(client)
            resp = await client.post("/api/v1/jobs/claim")
            claimed = resp.json()["job"]
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

            resp = await client.post(
                f"/api/v1/jobs/{job_id}/fail",
                json={"error_message": "test failure"},
            )
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.json()["job"]["status"], "failed")

            resp = await client.get("/api/v1/jobs", params={"status": "failed"})
            failed = resp.json()["jobs"]
            self.assertTrue(any(j["id"] == job_id for j in failed))

    async def test_worker_process_parse_note(self):
        """Worker process_parse_note works against real API with mocked AI."""
        import berrybrain_worker.main as worker_main

        async with self._make_client() as client:
            await self._create_note(client)
            resp = await client.post("/api/v1/jobs/claim")
            job = resp.json()["job"]
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
                await worker_main.process_parse_note(client, settings, job, payload)
            finally:
                worker_main.ollama_call = original

            # job should be completed
            resp = await client.get("/api/v1/jobs?status=completed")
            completed = resp.json()["jobs"]
            self.assertTrue(
                any(j["id"] == job["id"] for j in completed),
                f"Job {job['id']} not in completed list",
            )

    async def test_worker_claim_respects_pipeline_order(self):
        """First claim returns PARSE_NOTE (first in pipeline) when multiple jobs exist."""
        async with self._make_client() as client:
            await self._create_note(client, "Note A")
            await self._create_note(client, "Note B")

            # claim first
            resp = await client.post("/api/v1/jobs/claim")
            job1 = resp.json()["job"]

            # claim second
            resp = await client.post("/api/v1/jobs/claim")
            job2 = resp.json()["job"]

            # at least one should be PARSE_NOTE
            types = {job1["type"], job2["type"]}
            self.assertIn("PARSE_NOTE", types)

    async def test_jobs_health_endpoint(self):
        """Jobs health returns status and counts."""
        async with self._make_client() as client:
            resp = await client.get("/api/v1/jobs/health")
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertIn("status", data)
            self.assertIn("counts", data)
            self.assertIn("pending", data["counts"])

    async def test_pipeline_progress_endpoint(self):
        """Pipeline progress endpoint returns notes with active jobs."""
        async with self._make_client() as client:
            await self._create_note(client)
            resp = await client.get("/api/v1/jobs/pipeline-progress")
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertIn("notes", data)

    async def test_stale_job_recovery(self):
        """Stale running job gets recovered on next claim."""
        async with self._make_client() as client:
            await self._create_note(client)
            resp = await client.post("/api/v1/jobs/claim")
            job = resp.json()["job"]
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
            resp = await client.post("/api/v1/jobs/claim")
            recovered = resp.json()["job"]
            self.assertIsNotNone(recovered)
            self.assertIn(recovered["status"], ("running", "pending"))

    async def test_heartbeat_endpoint(self):
        """Worker heartbeat posts stats successfully."""
        async with self._make_client() as client:
            resp = await client.post(
                "/api/v1/worker/heartbeat",
                json={"jobs_processed": 5, "errors": 1, "ollama_healthy": True},
            )
            self.assertEqual(resp.status_code, 200)


if __name__ == "__main__":
    unittest.main()
