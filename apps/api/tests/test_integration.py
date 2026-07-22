import base64
import os
import tempfile
import unittest
from importlib import import_module
from pathlib import Path
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ["BERRYBRAIN_VAULT_WATCHER_ENABLED"] = "false"


SESSIONLOCAL_MODULES = (
    "berrybrain_api.main",
    "berrybrain_api.backup",
    "berrybrain_api.security",
    "berrybrain_api.routers.automation",
    "berrybrain_api.routers.auth",
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
    "berrybrain_api.routers.reviews",
    "berrybrain_api.routers.settings",
    "berrybrain_api.routers.vault",
)


class IntegrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp_dir = tempfile.TemporaryDirectory()
        db_path = Path(cls.tmp_dir.name) / "test.db"
        vault_path = Path(cls.tmp_dir.name) / "vault"
        vault_path.mkdir()
        backup_path = Path(cls.tmp_dir.name) / "backups"

        cls.db_url = f"sqlite:///{db_path}"

        from berrybrain_api.config import get_settings
        from berrybrain_api.database import Base, SessionLocal, engine
        import berrybrain_api.models  # noqa: F401 — register all ORM models

        cls.settings = get_settings()
        cls.original_database_url = cls.settings.database_url
        cls.original_vault_path = cls.settings.vault_path
        cls.original_backup_path = cls.settings.backup_path
        cls.original_vault_watcher_enabled = cls.settings.vault_watcher_enabled
        cls.original_api_token = cls.settings.api_token
        cls.original_require_auth = cls.settings.require_auth
        cls.original_session_secure_cookie = cls.settings.session_secure_cookie
        cls.settings.database_url = cls.db_url
        cls.settings.vault_path = vault_path
        cls.settings.backup_path = backup_path
        cls.settings.vault_watcher_enabled = False
        cls.settings.api_token = "test-token"
        cls.settings.require_auth = False
        cls.settings.session_secure_cookie = False

        cls.original_engine = engine
        cls.original_session_local = SessionLocal
        new_engine = create_engine(
            cls.db_url, connect_args={"check_same_thread": False}
        )
        import berrybrain_api.database as db_mod

        db_mod.engine = new_engine
        new_session_local = sessionmaker(
            bind=new_engine, autoflush=False, autocommit=False
        )
        db_mod.SessionLocal = new_session_local
        cls.patched_sessionlocal_modules = []
        for module_name in SESSIONLOCAL_MODULES:
            try:
                module = import_module(module_name)
            except ImportError:
                continue
            if hasattr(module, "SessionLocal"):
                cls.patched_sessionlocal_modules.append(
                    (module, getattr(module, "SessionLocal"))
                )
                setattr(module, "SessionLocal", new_session_local)
        Base.metadata.create_all(bind=new_engine)
        from berrybrain_api.search import init_fts

        with db_mod.SessionLocal() as session:
            init_fts(session)

        from berrybrain_api.main import app

        cls.client = TestClient(
            app, headers={"Authorization": f"Bearer {cls.settings.api_token}"}
        )
        cls.admin_client = TestClient(
            app, headers={"Authorization": f"Bearer {cls.settings.api_token}"}
        )
        setup_resp = cls.admin_client.post(
            "/api/v1/setup/admin",
            json={
                "password": "StrongPass123",
                "display_name": "Integration Admin",
            },
        )
        if setup_resp.status_code not in (201, 409):
            raise AssertionError(setup_resp.text)

    @classmethod
    def tearDownClass(cls):
        import berrybrain_api.database as db_mod

        db_mod.engine = cls.original_engine
        db_mod.SessionLocal = cls.original_session_local
        for module, original in reversed(cls.patched_sessionlocal_modules):
            setattr(module, "SessionLocal", original)
        cls.client.close()
        cls.admin_client.close()
        cls.settings.database_url = cls.original_database_url
        cls.settings.vault_path = cls.original_vault_path
        cls.settings.backup_path = cls.original_backup_path
        cls.settings.vault_watcher_enabled = cls.original_vault_watcher_enabled
        cls.settings.api_token = cls.original_api_token
        cls.settings.require_auth = cls.original_require_auth
        cls.settings.session_secure_cookie = cls.original_session_secure_cookie
        cls.tmp_dir.cleanup()

    def test_01_health(self):
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "ok")
        self.assertTrue(resp.json()["schema"]["compatible"])

    def test_02_monitor_exposes_model_reliability_without_prompt_data(self):
        from berrybrain_api import database as db_mod
        from berrybrain_api.models import ModelInvocationRecord

        with db_mod.SessionLocal() as session:
            session.add(
                ModelInvocationRecord(
                    capability="graph_inference",
                    provider="test-provider",
                    model="test-model",
                    prompt_version="test.v1",
                    status="completed",
                    latency_ms=25,
                )
            )
            session.commit()

        response = self.client.get("/api/v1/monitor/stats")
        self.assertEqual(response.status_code, 200)
        reliability = response.json()["model_invocations"]
        self.assertGreaterEqual(reliability["completed"], 1)
        self.assertIn("test-provider", reliability["by_provider"])
        self.assertNotIn("prompt", str(reliability).lower())

    def test_02_status_empty(self):
        resp = self.client.get("/api/v1/status")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["app"], "berrybrain")
        self.assertEqual(data["notes"], 0)

    def test_03_create_note_and_jobs(self):
        resp = self.client.post(
            "/api/v1/notes",
            json={
                "title": "Integration Test",
                "folder": "inbox",
                "content": "# Test\n\nHello world",
            },
        )
        self.assertEqual(resp.status_code, 201)
        note = resp.json()
        self.assertIn("path", note)
        self.assertTrue(note["path"].endswith(".md"))

        resp2 = self.client.get("/api/v1/status")
        self.assertEqual(resp2.json()["notes"], 1)

        resp3 = self.client.get("/api/v1/jobs", params={"status": "pending"})
        self.assertGreater(len(resp3.json()["jobs"]), 0)

    def test_03b_create_note_without_title(self):
        resp = self.client.post(
            "/api/v1/notes",
            json={
                "folder": "inbox",
                "content": "Texto inicial criado direto pelo editor.",
            },
        )

        self.assertEqual(resp.status_code, 201)
        note = resp.json()
        self.assertEqual(note["path"], "inbox/rascunho.md")
        self.assertIn("Texto inicial", note["content"])

    def test_04_read_and_update_note(self):
        notes = self.client.get("/api/v1/notes").json()["notes"]
        self.assertGreater(len(notes), 0)
        path = notes[0]["path"]

        resp = self.client.get(f"/api/v1/notes/{path}")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Hello world", resp.json()["content"])
        initial_hash = resp.json()["content_hash"]

        resp2 = self.client.put(
            f"/api/v1/notes/{path}",
            json={
                "content": "# Updated\n\nUpdated content",
                "base_content_hash": initial_hash,
            },
        )
        self.assertEqual(resp2.status_code, 200)
        self.assertIn("Updated content", resp2.json()["content"])

        conflict = self.client.put(
            f"/api/v1/notes/{path}",
            json={
                "content": "# Stale overwrite",
                "base_content_hash": initial_hash,
            },
        )
        self.assertEqual(conflict.status_code, 409)
        self.assertEqual(conflict.json()["detail"]["code"], "note_content_conflict")
        self.assertEqual(
            conflict.json()["detail"]["currentContentHash"],
            resp2.json()["content_hash"],
        )
        latest = self.client.get(f"/api/v1/notes/{path}").json()
        self.assertIn("Updated content", latest["content"])

    def test_05_job_lifecycle(self):
        resp = self.client.post("/api/v1/jobs/claim")
        self.assertEqual(resp.status_code, 200)
        job = resp.json()["job"]
        self.assertIsNotNone(job)
        self.assertEqual(job["status"], "running")

        resp2 = self.client.post(f"/api/v1/jobs/{job['id']}/complete")
        self.assertEqual(resp2.status_code, 200)
        self.assertEqual(resp2.json()["job"]["status"], "completed")

    def test_05b_job_cancellation_contract(self):
        created = self.client.post(
            "/api/v1/jobs",
            json={
                "type": "UPDATE_GRAPH_STATS",
                "payload": {"idempotency_key": "integration-cancel-job"},
            },
        )
        self.assertEqual(created.status_code, 201)
        job_id = created.json()["job"]["id"]

        cancelled = self.client.post(f"/api/v1/jobs/{job_id}/cancel")
        self.assertEqual(cancelled.status_code, 200)
        self.assertEqual(cancelled.json()["job"]["status"], "cancelled")

        state = self.client.get(f"/api/v1/jobs/{job_id}/cancellation")
        self.assertEqual(state.status_code, 200)
        self.assertFalse(state.json()["cancelRequested"])
        self.assertEqual(state.json()["status"], "cancelled")

        completion = self.client.post(f"/api/v1/jobs/{job_id}/complete")
        self.assertEqual(completion.status_code, 200)
        self.assertEqual(completion.json()["job"]["status"], "cancelled")

    def test_06_job_fail_with_retry(self):
        resp = self.client.post("/api/v1/jobs/claim")
        job = resp.json()["job"]
        self.assertIsNotNone(job)

        resp2 = self.client.post(
            f"/api/v1/jobs/{job['id']}/fail",
            json={"error_message": "test error"},
        )
        self.assertEqual(resp2.status_code, 200)
        failed_job = resp2.json()["job"]
        self.assertEqual(failed_job["status"], "pending")

    def test_06b_embedding_batch_endpoint(self):
        resp = self.client.post(
            "/api/v1/embeddings/batch",
            json={
                "embeddings": [
                    {
                        "note_id": 999,
                        "content_hash": "batch-hash",
                        "vector": [0.1, 0.2],
                        "model": "test-embedding",
                        "provider": "test",
                        "chunk_index": 0,
                        "chunk_text": "First chunk",
                        "token_count": 2,
                    },
                    {
                        "note_id": 999,
                        "content_hash": "batch-hash",
                        "vector": [0.3, 0.4],
                        "model": "test-embedding",
                        "provider": "test",
                        "chunk_index": 1,
                        "chunk_text": "Second chunk",
                        "token_count": 2,
                    },
                ]
            },
        )

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["count"], 2)

    def test_07_scan_vault(self):
        resp = self.client.post("/api/v1/vault/scan")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("created", data)
        self.assertIn("updated", data)
        self.assertIn("unchanged", data)

    def test_08_connections(self):
        notes = self.client.get("/api/v1/notes").json()["notes"]
        path = notes[0]["path"]
        resp = self.client.get(f"/api/v1/connections/{path}")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("connections", resp.json())

    def test_08b_folder_lifecycle_and_path_validation(self):
        created = self.client.post("/api/v1/folders", json={"name": "research"})
        self.assertEqual(created.status_code, 201)
        child = self.client.post(
            "/api/v1/folders",
            json={"name": "reading", "parent_path": "research"},
        )
        self.assertEqual(child.status_code, 201)
        renamed = self.client.put(
            "/api/v1/folders/research/reading", json={"name": "sources"}
        )
        self.assertEqual(renamed.status_code, 200)
        folders = self.client.get("/api/v1/folders").json()["folders"]
        self.assertTrue(any(item["path"] == "research/sources" for item in folders))
        self.assertEqual(
            self.client.post("/api/v1/folders", json={"name": "../unsafe"}).status_code,
            400,
        )
        self.assertEqual(
            self.client.delete("/api/v1/folders/research/sources").status_code,
            200,
        )
        self.assertEqual(
            self.client.delete("/api/v1/folders/research").status_code,
            200,
        )

    def test_08c_connection_and_concept_actions_are_persistent(self):
        from berrybrain_api.database import SessionLocal
        from berrybrain_api.models import ConceptRecord

        notes = []
        for title in ("Connection Source", "Connection Target"):
            response = self.client.post(
                "/api/v1/notes",
                json={"title": title, "content": f"# {title}\n\nGrounded source."},
            )
            self.assertEqual(response.status_code, 201)
            notes.append(response.json())

        synced = self.client.post(
            "/api/v1/connections/sync",
            json={
                "note_path": notes[0]["path"],
                "connections": [
                    {
                        "target": notes[1]["path"],
                        "type": "application",
                        "confidence": 0.84,
                        "reason": "The target applies the source concept.",
                        "evidence": ["Grounded source"],
                        "provider": "deterministic",
                        "model": "integration",
                    },
                    {"target": "missing.md", "reason": "Ignored missing target"},
                ],
            },
        )
        self.assertEqual(synced.status_code, 200)
        self.assertEqual(synced.json()["connections_created"], 1)
        recent = self.client.get("/api/v1/connections").json()["connections"]
        connection = next(
            item
            for item in recent
            if item["source"]["id"] == notes[0]["id"]
            and item["target"]["id"] == notes[1]["id"]
        )
        connection_id = connection["id"]
        self.assertEqual(
            self.client.get(f"/api/v1/connections/id/{connection_id}").status_code,
            200,
        )
        confirmed = self.client.post(f"/api/v1/connections/id/{connection_id}/confirm")
        self.assertEqual(confirmed.json()["connection"]["status"], "confirmed")
        ignored = self.client.post(f"/api/v1/connections/id/{connection_id}/ignore")
        self.assertEqual(ignored.json()["connection"]["status"], "ignored")
        by_note = self.client.get(f"/api/v1/connections/{notes[0]['path']}")
        self.assertEqual(by_note.status_code, 200)
        self.assertTrue(by_note.json()["connections"])

        with SessionLocal() as session:
            concept = ConceptRecord(
                name="Integration Concept",
                normalized_name="integration concept",
                description="A concept grounded by the integration source.",
                frequency=1,
                related_note_ids=f"[{notes[0]['id']}]",
                source_evidence='["Grounded source"]',
                provider="deterministic",
                model="integration",
            )
            session.add(concept)
            session.commit()
            session.refresh(concept)
            concept_id = concept.id

        self.assertEqual(
            self.client.get(f"/api/v1/concepts/{concept_id}").status_code, 200
        )
        concept_note = self.client.post(f"/api/v1/concepts/{concept_id}/create-note")
        self.assertEqual(concept_note.status_code, 200)
        self.assertEqual(concept_note.json()["status"], "created")
        self.assertIn("permanentes/", concept_note.json()["note"]["path"])

    def test_09_flashcards_and_review_are_removed_from_public_api(self):
        notes = self.client.get("/api/v1/notes").json()["notes"]
        path = notes[0]["path"]

        write_resp = self.client.put(
            f"/api/v1/flashcards/{path}", json={"flashcards": []}
        )
        self.assertEqual(write_resp.status_code, 404)

        resp = self.client.get(f"/api/v1/flashcards/{path}")
        self.assertEqual(resp.status_code, 404)
        resp2 = self.client.get("/api/v1/review/today")
        self.assertEqual(resp2.status_code, 404)

    def test_10_insights(self):
        resp = self.client.get("/api/v1/insights")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("insights", resp.json())

    def test_10b_save_graph_inference_as_insight(self):
        canonical = {
            "status": "answered",
            "question": "How do Docker and shell connect?",
            "answer": "Docker and shell connect through local automation workflows.",
            "evidence": [
                "Docker Essentials mentions containers.",
                "Linux Shell Scripting mentions automation.",
            ],
            "relatedNodes": [],
            "confidence": 0.82,
            "provider": "test-provider",
            "model": "test-model",
            "routes": ["knowledge_graph"],
        }
        with patch(
            "berrybrain_api.routers.graph.answer_cognitive_query",
            new=AsyncMock(return_value=canonical),
        ):
            inference_response = self.client.post(
                "/api/v1/graph/infer",
                json={"question": canonical["question"]},
            )

        self.assertEqual(inference_response.status_code, 200)
        inference = inference_response.json()
        self.assertIsInstance(inference["inferenceId"], int)
        self.assertEqual(inference["answer"], canonical["answer"])

        resp = self.client.post(
            "/api/v1/insights/from-inference",
            json={"inferenceId": inference["inferenceId"]},
        )

        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "created")
        self.assertEqual(
            data["insight"]["title"], "Inference: How do Docker and shell connect?"
        )
        activity = self.client.get("/api/v1/automation-logs").json()["logs"]
        self.assertTrue(
            any(
                item["action_type"] == "INSIGHT_CREATED_FROM_INFERENCE"
                and item["target_id"] == str(data["insight"]["id"])
                for item in activity
            )
        )
        jobs = self.client.get("/api/v1/jobs?status=pending&limit=200").json()["jobs"]
        self.assertTrue(
            any(
                job["type"] == "EXPAND_KNOWLEDGE_GRAPH"
                and job["payload"].get("insight_id") == data["insight"]["id"]
                for job in jobs
            )
        )
        projection = self.client.post("/api/v1/graph/expand")
        self.assertEqual(projection.status_code, 200)
        graph = self.client.get("/api/v1/graph").json()
        self.assertTrue(
            any(
                node.get("type") == "insight"
                and node.get("sourceId") == data["insight"]["id"]
                for node in graph["nodes"]
            )
        )
        jobs = self.client.get("/api/v1/jobs", params={"limit": 100}).json()["jobs"]
        self.assertTrue(
            any(
                job["type"] == "EXPAND_KNOWLEDGE_GRAPH"
                and job["idempotency_key"] == f"insight-graph:{data['insight']['id']}"
                for job in jobs
            )
        )

        duplicate = self.client.post(
            "/api/v1/insights/from-inference",
            json={"inferenceId": inference["inferenceId"]},
        )
        self.assertEqual(duplicate.json()["status"], "existing")

    def test_10c_insufficient_inference_becomes_knowledge_gap(self):
        canonical = {
            "status": "insufficient_evidence",
            "question": "How does quantum gravity affect this vault?",
            "answer": "There is not enough evidence in your BerryBrain data to answer this.",
            "routes": ["knowledge_base", "knowledge_graph"],
            "evidence": [],
            "relatedNodes": [],
            "suggestions": ["Add relevant source notes."],
        }
        with patch(
            "berrybrain_api.routers.graph.answer_cognitive_query",
            new=AsyncMock(return_value=canonical),
        ):
            inference_response = self.client.post(
                "/api/v1/graph/infer", json={"question": canonical["question"]}
            )

        inference = inference_response.json()
        resp = self.client.post(
            "/api/v1/insights/from-inference",
            json={"inferenceId": inference["inferenceId"]},
        )
        self.assertEqual(resp.status_code, 200)
        insight = resp.json()["insight"]
        self.assertEqual(insight["type"], "knowledge_gap")
        self.assertIn("could not establish", insight["description"])
        self.assertTrue(insight["evidence"])

    def test_10d_provider_failure_cannot_be_saved_as_knowledge(self):
        canonical = {
            "status": "waiting_provider",
            "question": "What connects these notes?",
            "answer": "The provider is unavailable.",
            "routes": ["knowledge_graph"],
            "evidence": ["A note was retrieved."],
            "relatedNodes": [],
        }
        with patch(
            "berrybrain_api.routers.graph.answer_cognitive_query",
            new=AsyncMock(return_value=canonical),
        ):
            inference_response = self.client.post(
                "/api/v1/graph/infer", json={"question": canonical["question"]}
            )

        resp = self.client.post(
            "/api/v1/insights/from-inference",
            json={"inferenceId": inference_response.json()["inferenceId"]},
        )
        self.assertEqual(resp.status_code, 409)

    def test_10e_legacy_client_inference_is_not_trusted(self):
        canonical = {
            "status": "insufficient_evidence",
            "question": "Injected client claim",
            "answer": "No server evidence exists.",
            "routes": ["knowledge_graph"],
            "evidence": [],
            "relatedNodes": [],
        }
        with patch(
            "berrybrain_api.routers.insights.answer_cognitive_query",
            new=AsyncMock(return_value=canonical),
        ):
            resp = self.client.post(
                "/api/v1/insights/from-inference",
                json={
                    "question": canonical["question"],
                    "inference": {
                        "status": "answered",
                        "answer": "Untrusted fabricated answer",
                        "evidence": ["Fabricated evidence"],
                    },
                },
            )

        self.assertEqual(resp.status_code, 200)
        insight = resp.json()["insight"]
        self.assertEqual(insight["type"], "knowledge_gap")
        self.assertNotIn("fabricated", insight["description"].lower())

    def test_10f_attachment_security_deduplication_and_cleanup(self):
        created_note = self.client.post(
            "/api/v1/notes",
            json={"title": "Attachment source", "content": "# Attachment source"},
        )
        self.assertEqual(created_note.status_code, 201)
        note_path = created_note.json()["path"]
        content = b"Container rollout evidence from a text attachment."
        payload = {
            "filename": "evidence.txt",
            "mime_type": "image/png",
            "size_bytes": len(content),
            "content_base64": base64.b64encode(content).decode(),
        }

        first = self.client.post(f"/api/v1/notes/{note_path}/attachments", json=payload)
        self.assertEqual(first.status_code, 201)
        attachment = first.json()["attachment"]
        self.assertEqual(attachment["mimeType"], "text/plain")
        self.assertEqual(len(attachment["checksum"]), 64)

        duplicate = self.client.post(
            f"/api/v1/notes/{note_path}/attachments", json=payload
        )
        self.assertEqual(duplicate.status_code, 201)
        self.assertTrue(duplicate.json()["deduplicated"])
        self.assertEqual(duplicate.json()["attachment"]["id"], attachment["id"])
        self.assertIsNone(duplicate.json()["processingJobId"])

        traversal = self.client.post(
            f"/api/v1/notes/{note_path}/attachments",
            json={**payload, "filename": "../evidence.txt"},
        )
        self.assertEqual(traversal.status_code, 400)

        invalid_extractor = self.client.post(
            f"/api/v1/notes/attachments/{attachment['id']}/reprocess",
            json={"extractor": "shell-command"},
        )
        self.assertEqual(invalid_extractor.status_code, 400)
        reprocess = self.client.post(
            f"/api/v1/notes/attachments/{attachment['id']}/reprocess",
            json={"extractor": "attachment-text.v1"},
        )
        self.assertEqual(reprocess.status_code, 200)
        self.assertEqual(reprocess.json()["status"], "queued")

        processed = self.client.post(
            f"/api/v1/notes/attachments/{attachment['id']}/process",
            json={"extractor": "attachment-text.v1"},
        )
        self.assertEqual(processed.status_code, 200)
        self.assertEqual(processed.json()["extraction"]["status"], "completed")

        deleted = self.client.delete(f"/api/v1/notes/attachments/{attachment['id']}")
        self.assertEqual(deleted.status_code, 200)
        listed = self.client.get(f"/api/v1/notes/{note_path}/attachments")
        self.assertEqual(listed.json()["attachments"], [])

    def test_10g_cognitive_review_lifecycle(self):
        from berrybrain_api.database import SessionLocal
        from berrybrain_api.models import NoteRecord
        from berrybrain_api.services import create_insight

        with SessionLocal() as session:
            note = NoteRecord(
                title="Review Integration Source",
                slug="review-integration-source",
                path="inbox/review-integration-source.md",
                content="Grounded fixture",
                content_hash="review-integration-v1",
            )
            session.add(note)
            session.flush()
            evidence = {"sourceNoteId": note.id, "excerpt": "Grounded fixture"}
            insight = create_insight(
                session,
                "knowledge_gap",
                "Integration review source",
                "A grounded insight for the review lifecycle.",
                related_notes=[note.id],
                why_it_matters="The concept should be retrievable without rereading.",
                evidence=[evidence],
                suggested_action="Explain the concept from memory.",
                graph_impact="Reinforces an existing knowledge node.",
                confidence=0.85,
                provider="deterministic",
                model="integration",
            )
            insight_id = insight.id

        created = self.client.post(
            "/api/v1/reviews/from-insight",
            json={
                "source_insight_id": insight_id,
                "review_type": "explain",
                "prompt": "Explain the grounded integration concept.",
                "expected_points": ["Grounded fixture"],
                "evidence": [evidence],
            },
        )
        self.assertEqual(created.status_code, 201)
        review = created.json()["review"]
        self.assertEqual(review["status"], "active")

        due = self.client.get("/api/v1/reviews", params={"due": True})
        self.assertEqual(due.status_code, 200)
        self.assertTrue(
            any(item["id"] == review["id"] for item in due.json()["reviews"])
        )

        graded = self.client.post(
            f"/api/v1/reviews/{review['id']}/grade",
            json={"rating": "good", "perceived_difficulty": 3},
        )
        self.assertEqual(graded.status_code, 200)
        self.assertEqual(graded.json()["review"]["intervalDays"], 1)
        paused = self.client.post(f"/api/v1/reviews/{review['id']}/pause")
        self.assertEqual(paused.json()["review"]["status"], "paused")
        resumed = self.client.post(f"/api/v1/reviews/{review['id']}/resume")
        self.assertEqual(resumed.json()["review"]["status"], "active")
        deleted = self.client.delete(f"/api/v1/reviews/{review['id']}")
        self.assertEqual(deleted.json()["review"]["status"], "deleted")

    def test_10h_cognitive_maturity_report(self):
        response = self.client.get("/api/v1/cognitive/maturity")
        self.assertEqual(response.status_code, 200)
        report = response.json()
        self.assertIn("eligibleFor100Percent", report)
        self.assertIn("structuralReady", report)
        self.assertIn("metrics", report)
        self.assertIn("blockers", report)
        self.assertIn("measuredAt", report)

    def test_10h_cognitive_layer_public_contracts_use_persisted_data(self):
        status = self.client.get("/api/v1/cognitive/status")
        self.assertEqual(status.status_code, 200)
        self.assertIn("knowledgeBase", status.json())
        config = self.client.get("/api/v1/cognitive/config")
        self.assertEqual(config.status_code, 200)
        self.assertIn("kb_vector_store", config.json())

        indexed = self.client.post("/api/v1/cognitive/index")
        self.assertEqual(indexed.status_code, 200)
        self.assertEqual(indexed.json()["status"], "indexed")
        retrieved = self.client.post(
            "/api/v1/cognitive/retrieve",
            json={"question": "What does the current vault say about testing?"},
        )
        self.assertEqual(retrieved.status_code, 200)
        self.assertIn("knowledge_base", retrieved.json()["routes"])
        semantic = self.client.get("/api/v1/cognitive/semantic-data")
        self.assertEqual(semantic.status_code, 200)
        self.assertIn("notes", semantic.json())

        grounded = {
            "status": "answered",
            "answer": "The vault contains grounded integration evidence.",
            "evidence": [{"title": "Integration source"}],
            "relatedNodes": [],
        }
        with patch(
            "berrybrain_api.routers.cognitive.answer_cognitive_query",
            new=AsyncMock(return_value=grounded),
        ):
            query = self.client.post(
                "/api/v1/cognitive/query",
                json={"question": "Summarize the integration evidence."},
            )
        self.assertEqual(query.status_code, 200)
        self.assertEqual(query.json()["status"], "answered")

    def test_10i_insight_feedback_jobs_and_notifications_are_persistent(self):
        from berrybrain_api.database import SessionLocal
        from berrybrain_api.models import NoteRecord
        from berrybrain_api.services import create_insight

        with SessionLocal() as session:
            note = NoteRecord(
                title="Insight outcome source",
                slug="insight-outcome-source",
                path="inbox/insight-outcome-source.md",
                content="Grounded source used to measure insight outcomes.",
                content_hash="insight-outcome-source-v1",
            )
            session.add(note)
            session.flush()
            insight_ids = []
            for index in range(4):
                insight = create_insight(
                    session,
                    "hypothesis",
                    f"Actionable integration insight {index}",
                    "Two pieces of source knowledge support a concrete learning action.",
                    related_notes=[note.id],
                    why_it_matters="The relationship changes how the source should be studied.",
                    evidence=[
                        f"Source evidence A{index}",
                        f"Source evidence B{index}",
                    ],
                    suggested_action="Review the cited note and record the conclusion.",
                    graph_impact="Adds a grounded learning relationship.",
                    confidence=0.85,
                    provider="deterministic",
                    model="integration",
                )
                insight_ids.append(insight.id)

        applied = self.client.post(f"/api/v1/insights/{insight_ids[0]}/apply")
        self.assertEqual(applied.json()["status"], "accepted")
        ignored = self.client.post(f"/api/v1/insights/{insight_ids[1]}/ignore")
        self.assertEqual(ignored.json()["insight"]["status"], "dismissed")
        reviewed = self.client.post(f"/api/v1/insights/{insight_ids[2]}/reviewed")
        self.assertEqual(reviewed.json()["status"], "reviewed")
        converted = self.client.post(
            f"/api/v1/insights/{insight_ids[3]}/converted-to-note"
        )
        self.assertEqual(converted.json()["status"], "converted_to_note")
        self.assertEqual(
            self.client.post(f"/api/v1/insights/{insight_ids[0]}/create-note").json()[
                "status"
            ],
            "job_created",
        )
        self.assertEqual(
            self.client.post(f"/api/v1/insights/{insight_ids[0]}/create-review").json()[
                "status"
            ],
            "job_created",
        )
        self.assertEqual(
            self.client.post("/api/v1/insights/generate").json()["status"],
            "job_created",
        )

        notification = self.client.post(
            "/api/v1/notifications/generate-insight-notification",
            params={"insight_id": insight_ids[0]},
        )
        self.assertEqual(notification.json()["status"], "created")
        failed_job = self.client.post(
            "/api/v1/notifications/create-from-failed-job",
            params={"job_id": 999, "error_message": "Provider timeout"},
        )
        self.assertEqual(failed_job.json()["status"], "created")
        notifications = self.client.get("/api/v1/notifications").json()["notifications"]
        self.assertGreaterEqual(len(notifications), 2)
        self.assertTrue(
            all(
                item["title"] in {"Insight ready", "Job failed"}
                for item in notifications[:2]
            )
        )
        marked = self.client.post(
            f"/api/v1/notifications/{notifications[0]['id']}/read"
        )
        self.assertEqual(marked.json()["status"], "read")
        all_read = self.client.post("/api/v1/notifications/read-all")
        self.assertEqual(all_read.json()["status"], "marked_read")

    def test_11_graph(self):
        resp = self.client.get("/api/v1/graph")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("nodes", resp.json())

        rebuild = self.client.post("/api/v1/graph/rebuild", params={"dry_run": True})
        self.assertEqual(rebuild.status_code, 200)
        self.assertTrue(rebuild.json()["dryRun"])
        self.assertIn("summary", rebuild.json())

    def test_11a_clean_cognitive_pipeline_reaches_graph_insights_and_home(self):
        created_notes = []
        for title, detail in (
            (
                "Container Operations",
                "Docker containers use Linux commands for repeatable deployment.",
            ),
            (
                "Shell Runbooks",
                "Linux shell automation controls Docker container operations.",
            ),
        ):
            response = self.client.post(
                "/api/v1/notes",
                json={
                    "title": title,
                    "content": f"# {title}\n\n## Container automation\n\n{detail}",
                },
            )
            self.assertEqual(response.status_code, 201)
            created_notes.append(response.json())

        embeddings = self.client.post(
            "/api/v1/embeddings/batch",
            json={
                "embeddings": [
                    {
                        "note_id": note["id"],
                        "content_hash": note["content_hash"],
                        "vector": [0.2 + index * 0.01, 0.8],
                        "model": "clean-pipeline-fixture",
                        "provider": "deterministic",
                        "chunk_index": 0,
                        "chunk_text": note["content"],
                        "token_count": len(note["content"].split()),
                    }
                    for index, note in enumerate(created_notes)
                ]
            },
        )
        self.assertEqual(embeddings.status_code, 200)

        expanded = self.client.post("/api/v1/graph/expand")
        self.assertEqual(expanded.status_code, 200, expanded.text)
        graph = self.client.get("/api/v1/graph").json()
        concept_nodes = [
            node
            for node in graph["nodes"]
            if node["type"] == "concept" and node["label"].lower() == "docker"
        ]
        self.assertTrue(concept_nodes)
        concept_ids = {node["id"] for node in concept_nodes}
        concept_edges = [
            edge
            for edge in graph["edges"]
            if edge["source"] in concept_ids or edge["target"] in concept_ids
        ]
        self.assertGreaterEqual(len(concept_edges), 2)
        self.assertTrue(
            all(edge["reason"] and edge["evidence"] for edge in concept_edges)
        )

        insights = self.client.get("/api/v1/insights").json()["insights"]
        pipeline_insights = [
            insight for insight in insights if '"docker"' in insight["title"].lower()
        ]
        self.assertTrue(pipeline_insights)
        home = self.client.get("/api/v1/home/summary").json()
        self.assertTrue(
            any(
                '"docker"' in insight["title"].lower()
                for insight in home["recentInsights"]
            )
        )

    def test_11b_graph_mutations_are_persistent_and_reversible(self):
        from berrybrain_api.database import SessionLocal
        from berrybrain_api.graph_write_service import GraphWriteService

        with SessionLocal() as session:
            writer = GraphWriteService(session)
            left = writer.upsert_node(node_type="concept", label="Graph Action Left")
            right = writer.upsert_node(node_type="concept", label="Graph Action Right")
            merge_candidate = writer.upsert_node(
                node_type="concept", label="Graph Action Alias"
            )
            edge = writer.upsert_edge(
                source_node_id=left.id,
                target_node_id=right.id,
                edge_type="related",
                reason="Integration fixture relationship.",
                evidence=["integration fixture"],
                confidence=0.7,
            )
            edge_id = edge.id
            left_id = left.id
            right_id = right.id
            merge_candidate_id = merge_candidate.id

        confirmed = self.client.post(f"/api/v1/graph/connections/{edge_id}/confirm")
        self.assertEqual(confirmed.status_code, 200)
        self.assertEqual(confirmed.json()["status"], "confirmed")
        mutation_id = confirmed.json()["mutationLogId"]

        undone = self.client.post(f"/api/v1/graph/mutations/{mutation_id}/undo")
        self.assertEqual(undone.status_code, 200)
        self.assertEqual(undone.json()["status"], "undone")

        ignored = self.client.post(f"/api/v1/graph/connections/{edge_id}/ignore")
        self.assertEqual(ignored.json()["status"], "ignored")
        restored = self.client.post(f"/api/v1/graph/connections/{edge_id}/restore")
        self.assertEqual(restored.json()["status"], "suggested")

        changed = self.client.patch(
            f"/api/v1/graph/connections/{edge_id}/type",
            json={"type": "prerequisite"},
        )
        self.assertEqual(changed.json()["type"], "prerequisite")
        evidence = self.client.post(
            f"/api/v1/graph/connections/{edge_id}/evidence",
            json={"excerpt": "Manual integration evidence", "source_note_id": None},
        )
        self.assertEqual(evidence.status_code, 200)
        self.assertTrue(
            any(
                isinstance(item, dict) and item.get("kind") == "manual"
                for item in evidence.json()["evidence"]
            )
        )
        explanation = self.client.get(
            f"/api/v1/graph/connections/{edge_id}/explanation"
        )
        self.assertEqual(explanation.status_code, 200)
        self.assertEqual(explanation.json()["source"]["id"], left_id)
        self.assertEqual(explanation.json()["target"]["id"], right_id)

        merged = self.client.post(
            f"/api/v1/graph/nodes/{left_id}/merge/{merge_candidate_id}"
        )
        self.assertEqual(merged.status_code, 200)
        split = self.client.post(
            f"/api/v1/graph/merges/{merged.json()['mutationLogId']}/split"
        )
        self.assertEqual(split.status_code, 200)
        self.assertEqual(split.json()["status"], "split")

    def test_11c_graph_panel_actions_update_real_state(self):
        from berrybrain_api.database import SessionLocal
        from berrybrain_api.graph_write_service import GraphWriteService

        with SessionLocal() as session:
            writer = GraphWriteService(session)
            node = writer.upsert_node(
                node_type="concept",
                label="Panel action concept",
                source_evidence=["Integration evidence"],
            )
            target = writer.upsert_node(
                node_type="topic",
                label="Panel action topic",
                source_evidence=["Integration evidence"],
            )
            edge = writer.upsert_edge(
                source_node_id=node.id,
                target_node_id=target.id,
                edge_type="related",
                reason="The concept is studied within the topic.",
                evidence=["Integration evidence"],
                confidence=0.74,
            )
            node_id = node.id
            edge_id = edge.id

        confirmed = self.client.post(f"/api/v1/graph/nodes/{node_id}/confirm")
        self.assertEqual(confirmed.json()["status"], "confirmed")
        notes = self.client.put(
            f"/api/v1/graph/nodes/{node_id}/notes",
            json={"notes": "Manual context for this concept."},
        )
        self.assertEqual(notes.json()["userNotes"], "Manual context for this concept.")
        edge_notes = self.client.put(
            f"/api/v1/graph/connections/{edge_id}/notes",
            json={"notes": "This relationship was manually reviewed."},
        )
        self.assertEqual(
            edge_notes.json()["userNotes"],
            "This relationship was manually reviewed.",
        )

        enriched = self.client.post(
            f"/api/v1/graph/nodes/{node_id}/enrich",
            json={
                "ai_summary": "A concise grounded concept summary.",
                "ai_context": "This concept belongs to the integration fixture.",
                "source_evidence": '["Integration evidence"]',
                "learning_value": "high",
                "source_quality": "reviewed",
                "provider": "deterministic",
                "model": "integration",
            },
        )
        self.assertEqual(enriched.status_code, 200)
        summary = self.client.get(f"/api/v1/graph/nodes/{node_id}/summary")
        self.assertEqual(summary.status_code, 200)
        self.assertEqual(
            summary.json()["aiSummary"], "A concise grounded concept summary."
        )

        reprocessed = self.client.post(f"/api/v1/graph/nodes/{node_id}/reprocess")
        self.assertEqual(reprocessed.json()["status"], "queued")
        first_missing = self.client.post(
            "/api/v1/graph/enrich-missing", params={"limit": 50}
        )
        self.assertEqual(first_missing.status_code, 200)
        second_missing = self.client.post(
            "/api/v1/graph/enrich-missing", params={"limit": 50}
        )
        self.assertGreaterEqual(second_missing.json()["skipped"], 1)

        ai_result = {
            "ai_summary": "AI grounded summary.",
            "ai_context": "Grounded in the panel action fixture.",
            "learning_value": "high",
            "source_quality": "ai_enriched",
            "source_evidence": ["Integration evidence"],
        }
        with patch(
            "berrybrain_api.routers.graph.generate_graph_answer",
            new=AsyncMock(return_value=ai_result),
        ):
            ai_enriched = self.client.post(f"/api/v1/graph/nodes/{node_id}/enrich-ai")
        self.assertEqual(ai_enriched.status_code, 200, ai_enriched.text)
        self.assertEqual(ai_enriched.json()["aiSummary"], "AI grounded summary.")

        insight_result = {
            "title": "The panel concept operationalizes its topic",
            "description": "The reviewed relationship shows how the concept is applied inside the topic.",
            "why_it_matters": "It turns an abstract topic into a concrete study relationship.",
            "evidence": [
                "Integration evidence",
                "The concept is studied within the topic.",
            ],
            "suggested_action": "Create an example note for this relationship.",
            "graph_impact": "Adds a grounded connection insight.",
            "confidence": 0.81,
            "reasoning": "Both the manual evidence and edge reason support the conclusion.",
        }
        with patch(
            "berrybrain_api.routers.graph.generate_graph_answer",
            new=AsyncMock(return_value=insight_result),
        ):
            insight = self.client.post(
                f"/api/v1/graph/connections/{edge_id}/generate-insight"
            )
        self.assertEqual(insight.status_code, 200, insight.text)
        self.assertEqual(insight.json()["status"], "created")

        disabled_web = self.client.post(f"/api/v1/graph/nodes/{node_id}/validate-web")
        self.assertEqual(disabled_web.status_code, 403)
        quality = self.client.get("/api/v1/graph/quality-report")
        self.assertEqual(quality.status_code, 200)
        recalculated = self.client.post("/api/v1/graph/quality-report/recalculate")
        self.assertEqual(recalculated.json()["status"], "queued")

        ignored = self.client.post(f"/api/v1/graph/nodes/{node_id}/ignore")
        self.assertEqual(ignored.json()["status"], "ignored")

    def test_11d_note_updates_and_deletes_retire_stale_knowledge_everywhere(self):
        marker = "Temporal Coupling Fixture"
        notes = []
        for title in ("Temporal Source Alpha", "Temporal Source Beta"):
            created = self.client.post(
                "/api/v1/notes",
                json={
                    "title": title,
                    "folder": "inbox",
                    "content": (
                        f"# {title}\n\n## {marker}\n\n"
                        "This temporary relationship exists only for stale-data validation."
                    ),
                },
            )
            self.assertEqual(created.status_code, 201)
            notes.append(created.json())

        built = self.client.post("/api/v1/graph/expand")
        self.assertEqual(built.status_code, 200, built.text)
        graph = self.client.get("/api/v1/graph").json()
        self.assertTrue(
            any(
                node["type"] == "concept" and node["label"].lower() == marker.lower()
                for node in graph["nodes"]
            )
        )
        self.assertTrue(
            any(
                marker.lower() in item["title"].lower()
                for item in self.client.get("/api/v1/insights").json()["insights"]
            )
        )

        for note in notes:
            latest = self.client.get(f"/api/v1/notes/{note['path']}").json()
            updated = self.client.put(
                f"/api/v1/notes/{note['path']}",
                json={
                    "content": f"# {note['title']}\n\nThe temporary concept was removed.",
                    "base_content_hash": latest["content_hash"],
                },
            )
            self.assertEqual(updated.status_code, 200)

        rebuilt = self.client.post("/api/v1/graph/expand")
        self.assertEqual(rebuilt.status_code, 200, rebuilt.text)
        refreshed_graph = self.client.get("/api/v1/graph").json()
        self.assertFalse(
            any(
                node["label"].lower() == marker.lower()
                for node in refreshed_graph["nodes"]
            )
        )
        refreshed_insights = self.client.get("/api/v1/insights").json()["insights"]
        self.assertFalse(
            any(marker.lower() in item["title"].lower() for item in refreshed_insights)
        )
        search = self.client.get("/api/v1/search", params={"q": marker}).json()
        self.assertFalse(
            any(marker.lower() in str(item).lower() for item in search["results"])
        )

        for note in notes:
            deleted = self.client.delete(f"/api/v1/notes/{note['path']}")
            self.assertEqual(deleted.status_code, 200)
        final_rebuild = self.client.post("/api/v1/graph/expand")
        self.assertEqual(final_rebuild.status_code, 200, final_rebuild.text)
        final_graph = self.client.get("/api/v1/graph").json()
        self.assertFalse(
            any(
                node["label"] in {"Temporal Source Alpha", "Temporal Source Beta"}
                for node in final_graph["nodes"]
            )
        )

    def test_11e_clip_reprocess_download_and_rename_preserve_vault_links(self):
        clipped = self.client.post(
            "/api/v1/notes/clip",
            json={
                "url": "https://example.test/automation",
                "title": "Clipped Automation",
                "content": "Automation makes deployments repeatable.",
            },
        )
        self.assertEqual(clipped.status_code, 200, clipped.text)
        clipped_note = clipped.json()
        self.assertIn(
            "> Source: https://example.test/automation", clipped_note["content"]
        )

        reference = self.client.post(
            "/api/v1/notes",
            json={
                "title": "Clip Reference",
                "folder": "inbox",
                "content": f"# Clip Reference\n\n[[{clipped_note['path']}]]",
            },
        )
        self.assertEqual(reference.status_code, 201)
        reference_note = reference.json()

        processing = self.client.get(f"/api/v1/notes/{clipped_note['path']}/status")
        self.assertEqual(processing.status_code, 200)
        self.assertEqual(processing.json()["total"], 8)
        reprocessed = self.client.post(
            f"/api/v1/notes/{clipped_note['path']}/reprocess"
        )
        self.assertEqual(reprocessed.status_code, 200)
        self.assertEqual(reprocessed.json()["status"], "queued")
        downloaded = self.client.get(f"/api/v1/notes/{clipped_note['path']}/download")
        self.assertEqual(downloaded.status_code, 200)
        self.assertIn("Automation makes deployments repeatable", downloaded.text)

        renamed = self.client.put(
            f"/api/v1/notes/{clipped_note['path']}/rename",
            json={"title": "Clipped Automation Renamed"},
        )
        self.assertEqual(renamed.status_code, 200, renamed.text)
        new_path = renamed.json()["path"]
        self.assertNotEqual(new_path, clipped_note["path"])
        linked = self.client.get(f"/api/v1/notes/{reference_note['path']}").json()
        self.assertIn(f"[[{new_path}]]", linked["content"])
        self.assertNotIn(f"[[{clipped_note['path']}]]", linked["content"])

        self.assertEqual(
            self.client.delete(f"/api/v1/notes/{new_path}").status_code, 200
        )
        self.assertEqual(
            self.client.delete(f"/api/v1/notes/{reference_note['path']}").status_code,
            200,
        )

    def test_12_search(self):
        resp = self.client.get("/api/v1/search", params={"q": "Test"})
        self.assertEqual(resp.status_code, 200)
        self.assertIn("results", resp.json())

        body_resp = self.client.get("/api/v1/search", params={"q": "Updated content"})
        self.assertEqual(body_resp.status_code, 200)
        body_results = body_resp.json()["results"]
        self.assertTrue(
            any("Updated content" in item.get("snippet", "") for item in body_results)
        )
        note = self.client.get(f"/api/v1/notes/{body_results[0]['path']}").json()
        batch = self.client.post(
            "/api/v1/embeddings/batch",
            json={
                "embeddings": [
                    {
                        "note_id": note["id"],
                        "content_hash": note["content_hash"],
                        "vector": [0.1, 0.2],
                        "model": "test-embedding",
                        "provider": "test",
                        "chunk_index": 0,
                        "chunk_text": "retrieval-only hidden chunk evidence",
                        "heading_path": "Hidden Evidence",
                        "start_line": 10,
                        "end_line": 12,
                        "token_count": 4,
                    }
                ]
            },
        )
        self.assertEqual(batch.status_code, 200)
        chunk_resp = self.client.get(
            "/api/v1/search", params={"q": "retrieval-only hidden", "limit": 10}
        )
        self.assertEqual(chunk_resp.status_code, 200)
        chunk_results = chunk_resp.json()["results"]
        self.assertTrue(any(item.get("evidence") for item in chunk_results))

        import berrybrain_api.main as main_module

        original_generate_query_embedding = main_module.generate_query_embedding
        try:
            main_module.generate_query_embedding = lambda config, text, **kwargs: [
                0.1,
                0.2,
            ]
            vector_resp = self.client.get(
                "/api/v1/search", params={"q": "no lexical match here", "limit": 10}
            )
        finally:
            main_module.generate_query_embedding = original_generate_query_embedding
        self.assertEqual(vector_resp.status_code, 200)
        vector_results = vector_resp.json()["results"]
        self.assertLessEqual(len(vector_results), 10)
        self.assertTrue(
            any(item.get("evidence") for item in vector_results),
            vector_results,
        )
        self.assertTrue(
            any(item.get("source") == "vector_chunk" for item in vector_results),
            vector_results,
        )

        from berrybrain_api.database import SessionLocal
        from berrybrain_api.models import ConnectionRecord, NoteRecord

        source_note = self.client.get(f"/api/v1/notes/{body_results[0]['path']}").json()
        with SessionLocal() as session:
            connected = NoteRecord(
                title="Graph Expansion Only",
                slug="graph-expansion-only",
                path="inbox/graph-expansion-only.md",
                content="No lexical overlap.",
                content_hash="graph-only",
            )
            session.add(connected)
            session.flush()
            session.add(
                ConnectionRecord(
                    source_note_id=source_note["id"],
                    target_note_id=connected.id,
                    connection_type="semantic_similarity",
                    reason="Graph-only related note.",
                    confidence=80,
                    status="confirmed",
                )
            )
            session.commit()
        graph_resp = self.client.get(
            "/api/v1/search", params={"q": "Updated content", "limit": 20}
        )
        self.assertEqual(graph_resp.status_code, 200)
        self.assertTrue(
            any(item.get("source") == "graph" for item in graph_resp.json()["results"]),
            graph_resp.json()["results"],
        )

    def test_13_worker_heartbeat(self):
        resp = self.client.post(
            "/api/v1/worker/heartbeat", json={"jobs_processed": 5, "errors": 0}
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["worker"]["jobs_processed"], 5)

        resp2 = self.client.get("/api/v1/worker/status")
        self.assertEqual(resp2.status_code, 200)
        self.assertEqual(resp2.json()["worker"]["jobs_processed"], 5)
        self.assertTrue(resp2.json()["worker"]["last_heartbeat"].endswith("Z"))

    def test_14_settings(self):
        denied = self.client.put(
            "/api/v1/settings/test.key",
            json={"value": "42"},
        )
        self.assertEqual(denied.status_code, 401)

        from berrybrain_api.database import SessionLocal
        from berrybrain_api.settings_store import set_setting

        with SessionLocal() as session:
            set_setting(session, "test.key", "42")

        resp2 = self.client.get("/api/v1/settings/test.key")
        self.assertEqual(resp2.status_code, 200)
        self.assertEqual(resp2.json()["setting"]["value"], "42")

        resp3 = self.client.get("/api/v1/settings")
        self.assertGreater(len(resp3.json()["settings"]), 0)

    def test_15_generated_metadata(self):
        notes = self.client.get("/api/v1/notes").json()["notes"]
        path = notes[0]["path"]
        note = self.client.get(f"/api/v1/notes/{path}").json()

        resp = self.client.put(
            f"/api/v1/metadata/classification?note_path={path}",
            json={
                "content": {"note_type": "study"},
                "content_hash": note["content_hash"],
                "model_used": "qwen3",
            },
        )
        self.assertEqual(resp.status_code, 200)

        resp2 = self.client.get(f"/api/v1/metadata/classification?note_path={path}")
        self.assertEqual(resp2.status_code, 200)
        self.assertEqual(resp2.json()["metadata"][0]["content"]["note_type"], "study")

        resp3 = self.client.delete(f"/api/v1/metadata/classification?note_path={path}")
        self.assertEqual(resp3.status_code, 200)

    def test_16_automation_logs(self):
        resp = self.client.post(
            "/api/v1/automation-logs",
            json={"action_type": "test_action", "description": "integration test"},
        )
        self.assertEqual(resp.status_code, 201)

        resp2 = self.client.get("/api/v1/automation-logs", params={"limit": 5})
        self.assertEqual(resp2.status_code, 200)
        self.assertGreater(len(resp2.json()["logs"]), 0)

    def test_17_backup_and_restore(self):
        resp = self.admin_client.post("/api/v1/backups")
        self.assertEqual(resp.status_code, 201)
        backup = resp.json()["backup"]
        self.assertIn("id", backup)

        resp2 = self.admin_client.get("/api/v1/backups")
        self.assertEqual(resp2.status_code, 200)
        self.assertGreater(len(resp2.json()["backups"]), 0)

        resp3 = self.admin_client.post(f"/api/v1/backups/{backup['id']}/restore")
        self.assertEqual(resp3.status_code, 200)

        resp4 = self.admin_client.delete(f"/api/v1/backups/{backup['id']}")
        self.assertEqual(resp4.status_code, 200)
        self.assertEqual(resp4.json()["status"], "deleted")

    def test_18_delete_note(self):
        notes = self.client.get("/api/v1/notes").json()["notes"]
        path = notes[0]["path"]
        resp = self.client.delete(f"/api/v1/notes/{path}")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "deleted")

    def test_19_api_token_auth(self):
        from berrybrain_api.main import settings as app_settings

        previous_token = app_settings.api_token
        app_settings.api_token = "secret123"
        try:
            get_resp = self.client.get("/api/v1/notes")
            self.assertEqual(get_resp.status_code, 401)

            resp = self.client.post(
                "/api/v1/notes",
                json={"title": "Auth Test", "folder": "inbox"},
            )
            self.assertEqual(resp.status_code, 401)

            resp2 = self.client.post(
                "/api/v1/notes",
                json={"title": "Auth Test", "folder": "inbox"},
                headers={"Authorization": "Bearer secret123"},
            )
            self.assertEqual(resp2.status_code, 201)

            auth_get = self.client.get(
                "/api/v1/notes", headers={"Authorization": "Bearer secret123"}
            )
            self.assertEqual(auth_get.status_code, 200)

            path = resp2.json()["path"]
            self.client.delete(
                f"/api/v1/notes/{path}",
                headers={"Authorization": "Bearer secret123"},
            )
        finally:
            app_settings.api_token = previous_token

    def test_20_jobs_health_and_recover_stale(self):
        health = self.client.get("/api/v1/jobs/health")
        self.assertEqual(health.status_code, 200)
        self.assertIn("counts", health.json())
        self.assertIn("dead_letter", health.json()["counts"])
        self.assertIn(
            health.json()["slo"]["status"], {"healthy", "at_risk", "breached"}
        )
        self.assertEqual(health.json()["slo"]["policy"]["pendingBreachSeconds"], 1800)

        recovered = self.client.post("/api/v1/jobs/recover-stale")
        self.assertEqual(recovered.status_code, 200)
        self.assertIn("recovered", recovered.json())

    def test_20b_legacy_system_endpoints_are_safe_and_english(self):
        audit = self.client.get("/api/v1/system/audit")
        self.assertEqual(audit.status_code, 200, audit.text)
        self.assertIn("completion_rate_pct", audit.json())
        activity = self.client.get("/api/v1/activity").json()["activity"]
        self.assertFalse(any("falhou" in item["description"] for item in activity))
        reset = self.admin_client.post(
            "/api/v1/system/reset", json={"confirm": "berrybrain-reset-all"}
        )
        self.assertEqual(reset.status_code, 410)
        self.assertIn("Danger zone", reset.json()["detail"])

    def test_21_maintenance_contracts(self):
        cleanup = self.admin_client.post("/api/v1/maintenance/cleanup-legacy-insights")
        self.assertEqual(cleanup.status_code, 200)
        self.assertEqual(cleanup.json()["status"], "ok")
        self.assertIn("archivedInsights", cleanup.json())

        validation = self.admin_client.post("/api/v1/maintenance/validate-graph")
        self.assertEqual(validation.status_code, 200)
        self.assertEqual(validation.json()["status"], "ok")
        self.assertIn("deletedOrphanEdges", validation.json())
        self.assertIn("duplicateJobsMarkedFailed", validation.json())

        reindex = self.admin_client.post("/api/v1/maintenance/reindex-knowledge-base")
        self.assertEqual(reindex.status_code, 200)
        self.assertEqual(reindex.json()["status"], "indexed")
        self.assertIn("externalVectorStore", reindex.json())

        rebuild = self.admin_client.post("/api/v1/maintenance/rebuild-brain")
        self.assertEqual(rebuild.status_code, 200)
        self.assertEqual(rebuild.json()["status"], "queued")
        self.assertIn("knowledgeBase", rebuild.json())
        self.assertIn("validation", rebuild.json())


if __name__ == "__main__":
    unittest.main()
