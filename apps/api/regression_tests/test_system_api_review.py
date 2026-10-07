"""System/API regressions; execute with scripts/check-system.py in isolation."""

import json
import tempfile
import unittest
from contextlib import ExitStack
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from starlette.requests import Request

from berrybrain_api import main
from berrybrain_api.config import Settings
from berrybrain_api.database import Base
from berrybrain_api.models import (
    ConnectionRecord,
    GeneratedMetadataRecord,
    GraphEdgeRecord,
    GraphNodeRecord,
    JobRecord,
    NoteAttachmentRecord,
    NoteRecord,
    UserRecord,
)
from berrybrain_api.routers import graph, notes, security_tokens
from berrybrain_api.search import init_fts
from berrybrain_api.security import (
    create_user_session,
    issue_service_token,
    revoke_service_token,
    verify_service_token,
)


class SystemApiReviewTest(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.temporary = self.stack.enter_context(tempfile.TemporaryDirectory())
        root = Path(self.temporary)
        self.cfg = Settings(
            _env_file=None,
            vault_path=root / "vault",
            database_url=f"sqlite:///{root / 'system.db'}",
            api_token="worker-original-token",
            session_secret="product-integration-secret-32-bytes",
            vault_watcher_enabled=False,
            enable_default_owner=False,
        )
        self.engine = create_engine(
            self.cfg.database_url, connect_args={"check_same_thread": False}
        )
        self.stack.callback(self.engine.dispose)
        Base.metadata.create_all(self.engine)
        self.factory = sessionmaker(bind=self.engine)
        with self.factory() as session:
            init_fts(session)
        self.stack.enter_context(patch.object(main, "settings", self.cfg))
        self.stack.enter_context(
            patch("berrybrain_api.config.get_settings", return_value=self.cfg)
        )
        for module in (main, graph, notes, security_tokens):
            self.stack.enter_context(patch.object(module, "SessionLocal", self.factory))
            self.stack.enter_context(
                patch.object(module, "get_settings", return_value=self.cfg)
            )
        self.client = TestClient(
            main.app, headers={"Authorization": "Bearer worker-original-token"}
        )
        self.stack.callback(self.client.close)

    def create_note(self, title="Test API", content="# Test\nAuthor-owned content"):
        response = self.client.post(
            "/api/v1/notes", json={"title": title, "content": content}
        )
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    def browser_owner(self):
        with self.factory() as session:
            user = UserRecord(
                email=self.cfg.admin_email, email_verified=True, password_hash="unused"
            )
            session.add(user)
            session.commit()
            request = Request(
                {"type": "http", "headers": [], "client": ("127.0.0.1", 8000)}
            )
            raw, csrf, _ = create_user_session(session, self.cfg, request, user)
            user_id = user.id
        self.client.headers.pop("Authorization", None)
        self.client.cookies.set(self.cfg.session_cookie_name, raw)
        self.client.cookies.set(self.cfg.csrf_cookie_name, csrf)
        self.client.headers["X-CSRF-Token"] = csrf
        return user_id

    def test_external_client_note_crud_uses_hash_conflict_and_identity(self):
        original = self.create_note()
        path = "/api/v1/notes/" + original["path"]
        self.assertEqual(self.client.get(path).json()["stableId"], original["stableId"])
        updated = self.client.put(
            path,
            json={
                "content": "# Changed",
                "base_content_hash": original["content_hash"],
            },
        )
        self.assertEqual(updated.status_code, 200, updated.text)
        self.assertEqual(updated.json()["id"], original["id"])
        conflict = self.client.put(
            path,
            json={
                "content": "# Lost edit",
                "base_content_hash": original["content_hash"],
            },
        )
        self.assertEqual(conflict.status_code, 409)
        self.assertEqual(self.client.get(path).json()["content"], "# Changed")
        self.assertEqual(self.client.delete(path).status_code, 200)
        self.assertEqual(self.client.get(path).status_code, 404)

    def test_notes_pagination_preserves_legacy_list_and_rejects_bad_limits(self):
        self.create_note("One")
        self.create_note("Two")
        first = self.client.get("/api/v1/notes?limit=1").json()
        second = self.client.get("/api/v1/notes?limit=1&offset=1").json()
        self.assertEqual(first["total"], 2)
        self.assertEqual(first["nextOffset"], 1)
        self.assertIsNone(second["nextOffset"])
        self.assertNotEqual(first["notes"][0]["path"], second["notes"][0]["path"])
        self.assertEqual(len(self.client.get("/api/v1/notes").json()["notes"]), 2)
        for query in ("limit=-1", "limit=201", "offset=-1"):
            self.assertEqual(self.client.get("/api/v1/notes?" + query).status_code, 422)

    def test_openapi_advertises_real_auth_and_typed_core_responses(self):
        self.client.headers.pop("Authorization")
        schema = self.client.get("/api/v1/openapi.json").json()
        self.assertEqual(schema["servers"], [{"url": "../.."}])
        read = schema["paths"]["/api/v1/notes"]["get"]
        self.assertIn({"ServiceBearer": []}, read["security"])
        create = schema["paths"]["/api/v1/notes"]["post"]
        self.assertIn({"BrowserSession": [], "CSRFHeader": []}, create["security"])
        self.assertIn(
            "$ref", read["responses"]["200"]["content"]["application/json"]["schema"]
        )
        self.assertEqual(schema["paths"]["/api/v1/auth/login"]["post"]["security"], [])
        self.assertNotIn(
            {"ServiceBearer": []},
            schema["paths"]["/api/v1/security/service-tokens"]["post"]["security"],
        )
        self.assertNotIn(
            {"ServiceBearer": []},
            schema["paths"]["/api/v1/ai/configuration"]["put"]["security"],
        )
        docs = self.client.get("/api/v1/docs")
        self.assertEqual(docs.status_code, 200)
        self.assertIn("./openapi.json", docs.text)
        self.assertIn(
            "https://cdn.jsdelivr.net", docs.headers["content-security-policy"]
        )

    def test_private_judge_and_prefix_lookalikes_are_not_exempt(self):
        self.client.headers.pop("Authorization")
        for path in (
            "/api/v1/judge/mode",
            "/api/v1/judge/scorecard",
            "/health-private",
            "/api/v1/auth-private",
        ):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 401, path)
            self.assertEqual(response.headers["www-authenticate"], "Bearer")
        self.assertEqual(self.client.get("/api/v1").status_code, 200)

    def test_chunked_or_underreported_body_is_rejected_before_writes(self):
        self.cfg.max_request_body_bytes = 96
        payload = json.dumps({"title": "Large", "content": "x" * 100}).encode()
        for headers in (
            {"Content-Type": "application/json"},
            {"Content-Type": "application/json", "Content-Length": "1"},
        ):
            response = self.client.post(
                "/api/v1/notes",
                content=iter([payload[:70], payload[70:]]),
                headers=headers,
            )
            self.assertEqual(response.status_code, 413, response.text)
        with self.factory() as session:
            self.assertEqual(session.query(NoteRecord).count(), 0)
        invalid_length = self.client.post(
            "/api/v1/notes", content=b"{}", headers={"Content-Length": "9" * 5000}
        )
        self.assertEqual(invalid_length.status_code, 400)

    def test_validation_does_not_echo_secret_input(self):
        secret = "sensitive-note-body"
        response = self.client.put(
            "/api/v1/notes/inbox/missing.md",
            json={"content": secret, "base_content_hash": secret},
        )
        self.assertEqual(response.status_code, 422)
        self.assertNotIn(secret, response.text)

    def test_new_integration_token_keeps_worker_valid_and_revokes_independently(self):
        self.browser_owner()
        response = self.client.post(
            "/api/v1/security/service-tokens",
            json={"name": "Writer app", "expires_in_days": 30},
        )
        self.assertEqual(response.status_code, 201, response.text)
        issued = response.json()
        with self.factory() as session:
            self.assertTrue(verify_service_token(session, self.cfg, self.cfg.api_token))
            self.assertTrue(verify_service_token(session, self.cfg, issued["token"]))
            revoke_service_token(session, issued["record"]["id"])
            self.assertFalse(verify_service_token(session, self.cfg, issued["token"]))
            self.assertTrue(verify_service_token(session, self.cfg, self.cfg.api_token))

    def test_integration_token_issuance_requires_owner_session_and_csrf(self):
        payload = {"name": "Writer app"}
        self.assertEqual(
            self.client.post(
                "/api/v1/security/service-tokens", json=payload
            ).status_code,
            401,
        )
        self.browser_owner()
        self.client.headers.pop("X-CSRF-Token")
        self.assertEqual(
            self.client.post(
                "/api/v1/security/service-tokens", json=payload
            ).status_code,
            403,
        )

    def test_expired_active_integration_token_is_not_accepted(self):
        with self.factory() as session:
            raw, record = issue_service_token(session, self.cfg, name="Expired")
            record.expires_at = datetime.now(UTC) - timedelta(seconds=1)
            session.commit()
            self.assertFalse(verify_service_token(session, self.cfg, raw))
            self.assertEqual(
                security_tokens._serialize_token(record)["status"], "expired"
            )

    def test_locked_user_existing_session_is_rejected(self):
        user_id = self.browser_owner()
        with self.factory() as session:
            session.get(UserRecord, user_id).locked_until = datetime.now(
                UTC
            ) + timedelta(hours=1)
            session.commit()
        self.assertEqual(self.client.get("/api/v1/notes").status_code, 401)

    def test_audit_with_failed_job_reports_type(self):
        with self.factory() as session:
            session.add(
                JobRecord(
                    type="PARSE_NOTE", status="failed", error_message="test failure"
                )
            )
            session.commit()
        response = self.client.get("/api/v1/system/audit")
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["failed_by_type"], {"PARSE_NOTE": 1})

    def test_metadata_unscoped_and_scoped_queries_honor_limit(self):
        first, second = self.create_note("One"), self.create_note("Two")
        with self.factory() as session:
            for item in (first, second):
                session.add(
                    GeneratedMetadataRecord(
                        note_id=item["id"],
                        generation_type="summary",
                        content="{}",
                        content_hash=item["content_hash"],
                    )
                )
            session.add(
                GeneratedMetadataRecord(
                    note_id=first["id"],
                    generation_type="keywords",
                    content="{}",
                    content_hash=first["content_hash"],
                )
            )
            session.commit()
        response = self.client.get("/api/v1/metadata/summary?limit=1")
        self.assertEqual(len(response.json()["metadata"]), 1)
        scoped = self.client.get(
            "/api/v1/metadata", params={"note_path": first["path"], "limit": 1}
        )
        self.assertEqual(len(scoped.json()["metadata"]), 1)
        self.assertEqual(self.client.get("/api/v1/metadata?limit=-1").status_code, 422)

    def test_search_typed_response_preserves_evidence(self):
        self.create_note(content="# Computation\nAlgorithms and computation.")
        with patch.object(main, "generate_query_embedding", return_value=None):
            response = self.client.get("/api/v1/search?q=computation")
        self.assertEqual(response.status_code, 200, response.text)
        self.assertTrue(response.json()["results"])
        self.assertIsInstance(response.json()["results"][0]["evidence"], list)
        self.assertEqual(response.headers["cache-control"], "no-store")

    def test_organization_preserves_attachment_and_note_identity(self):
        first, second = self.create_note("One"), self.create_note("Two")
        with self.factory() as session:
            session.add(
                GraphNodeRecord(
                    type="topic",
                    label="Mathematics",
                    confidence=0.9,
                    quality_gate_status="passed",
                    source_note_ids=json.dumps([first["id"], second["id"]]),
                )
            )
            attachment = NoteAttachmentRecord(
                note_id=first["id"],
                note_path=first["path"],
                filename="proof.txt",
                stored_path=".attachments/proof.txt",
                mime_type="text/plain",
                size_bytes=5,
            )
            session.add(attachment)
            session.commit()
            attachment_id = attachment.id
        response = self.client.post("/api/v1/notes/" + first["path"] + "/organize")
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["status"], "organized")
        new_path = response.json()["path"]
        with self.factory() as session:
            self.assertEqual(session.get(NoteRecord, first["id"]).path, new_path)
            self.assertEqual(
                session.get(NoteRecord, first["id"]).stable_id, first["stableId"]
            )
            self.assertEqual(
                session.get(NoteAttachmentRecord, attachment_id).note_path, new_path
            )

    def test_note_status_matches_identity_and_counts_dead_letter(self):
        item = self.create_note("Status")
        with self.factory() as session:
            session.add(
                JobRecord(
                    type="PARSE_NOTE",
                    note_id=item["id"],
                    note_path=item["path"],
                    payload=json.dumps({"note_path": item["path"]}, indent=2),
                    status="dead_letter",
                )
            )
            session.commit()
        response = self.client.get("/api/v1/notes/" + item["path"] + "/status")
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["failed"], 1)

    def test_search_excludes_rejected_connection_expansion_and_backlinks(self):
        seed = self.create_note(
            "Algorithms", "# Algorithms\nUniquecomputing algorithms"
        )
        unrelated = self.create_note("Garden", "# Garden\nFlowers")
        with self.factory() as session:
            session.add(
                ConnectionRecord(
                    source_note_id=seed["id"],
                    target_note_id=unrelated["id"],
                    connection_type="related",
                    quality_gate_status="rejected",
                    reason="Rejected inference",
                )
            )
            session.commit()
        with patch.object(main, "generate_query_embedding", return_value=None):
            response = self.client.get("/api/v1/search?q=Uniquecomputing")
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual([r["id"] for r in response.json()["results"]], [seed["id"]])

    def test_graph_edges_cannot_expose_rejected_endpoints(self):
        with self.factory() as session:
            visible = GraphNodeRecord(
                type="concept", label="Visible", quality_gate_status="passed"
            )
            rejected = GraphNodeRecord(
                type="concept", label="Rejected", quality_gate_status="rejected"
            )
            session.add_all([visible, rejected])
            session.flush()
            session.add(
                GraphEdgeRecord(
                    source_node_id=visible.id,
                    target_node_id=rejected.id,
                    type="related",
                    quality_gate_status="passed",
                )
            )
            session.commit()
        self.assertEqual(len(self.client.get("/api/v1/graph/nodes").json()["nodes"]), 1)
        for suffix in ("", "?includeProvisional=true"):
            response = self.client.get("/api/v1/graph/edges" + suffix)
            self.assertEqual(response.status_code, 200, response.text)
            self.assertEqual(response.json()["edges"], [])


if __name__ == "__main__":
    unittest.main()
