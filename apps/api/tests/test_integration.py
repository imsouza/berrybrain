import base64
import os
import tempfile
import unittest
from importlib import import_module
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ["BERRYBRAIN_VAULT_WATCHER_ENABLED"] = "false"


SESSIONLOCAL_MODULES = (
    "berrybrain_api.main",
    "berrybrain_api.backup",
    "berrybrain_api.security",
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
        resp = self.client.post(
            "/api/v1/insights/from-inference",
            json={
                "question": "How do Docker and shell connect?",
                "inference": {
                    "status": "answered",
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
                },
            },
        )

        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "created")
        self.assertEqual(
            data["insight"]["title"], "Inference: How do Docker and shell connect?"
        )

    def test_10c_attachment_security_deduplication_and_cleanup(self):
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

    def test_10c_cognitive_review_lifecycle(self):
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

    def test_11_graph(self):
        resp = self.client.get("/api/v1/graph")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("nodes", resp.json())

        rebuild = self.client.post("/api/v1/graph/rebuild", params={"dry_run": True})
        self.assertEqual(rebuild.status_code, 200)
        self.assertTrue(rebuild.json()["dryRun"])
        self.assertIn("summary", rebuild.json())

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
            main_module.generate_query_embedding = lambda config, text: [0.1, 0.2]
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
        resp = self.client.put(
            "/api/v1/settings/test.key",
            json={"value": "42"},
        )
        self.assertEqual(resp.status_code, 200)

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

        recovered = self.client.post("/api/v1/jobs/recover-stale")
        self.assertEqual(recovered.status_code, 200)
        self.assertIn("recovered", recovered.json())

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
