"""Product-only tests for human-approved Ask note writes."""

import json
import tempfile
import unittest
from contextlib import ExitStack
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from starlette.requests import Request

from berrybrain_api import main
from berrybrain_api.ask_references import capture_ask_references
from berrybrain_api.cognitive_query import (
    _evidence_source_snapshot,
    _retrieve_lexical_kb,
)
from berrybrain_api.config import Settings
from berrybrain_api.database import Base
from berrybrain_api.graph_expansion import expand_knowledge_graph, sync_note_graph_node
from berrybrain_api.jobs import claim_next_job, create_job, enqueue_note_changed_jobs
from berrybrain_api.models import (
    AskActionPlanRecord,
    AutomationLogRecord,
    GraphNodeRecord,
    JobRecord,
    NoteRecord,
    UserRecord,
    VaultRecord,
)
from berrybrain_api.routers import ask_actions
from berrybrain_api.routers import folders as folders_router
from berrybrain_api.routers import notes as notes_router
from berrybrain_api.routers import vault as vault_router
from berrybrain_api.security import create_user_session, issue_service_token
from berrybrain_api.sync import sync_note_record
from berrybrain_api.vault import planned_ask_vault_path, read_note


class AskActionPlanTests(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        root = Path(self.stack.enter_context(tempfile.TemporaryDirectory()))
        self.cfg = Settings(
            _env_file=None,
            vault_path=root / "vault",
            database_url=f"sqlite:///{root / 'ask-actions.db'}",
            session_secret="ask-actions-integration-secret-32-bytes",
            vault_watcher_enabled=False,
            enable_default_owner=False,
        )
        engine = create_engine(
            self.cfg.database_url, connect_args={"check_same_thread": False}
        )
        self.stack.callback(engine.dispose)
        Base.metadata.create_all(engine)
        self.sessions = sessionmaker(bind=engine)
        self.stack.enter_context(patch.object(main, "settings", self.cfg))
        self.stack.enter_context(
            patch("berrybrain_api.config.get_settings", return_value=self.cfg)
        )
        for module in (main, ask_actions, folders_router, notes_router, vault_router):
            self.stack.enter_context(
                patch.object(module, "SessionLocal", self.sessions)
            )
            self.stack.enter_context(
                patch.object(module, "get_settings", return_value=self.cfg)
            )
        self.client = TestClient(main.app)
        self.stack.callback(self.client.close)
        self._login("owner@example.test")

    def _login(self, email):
        with self.sessions() as session:
            user = UserRecord(email=email, email_verified=True, password_hash="unused")
            session.add(user)
            session.commit()
            request = Request(
                {"type": "http", "headers": [], "client": ("127.0.0.1", 8000)}
            )
            raw, csrf, _ = create_user_session(session, self.cfg, request, user)
        self.client.cookies.set(self.cfg.session_cookie_name, raw)
        self.client.cookies.set(self.cfg.csrf_cookie_name, csrf)
        self.client.headers["X-CSRF-Token"] = csrf

    def _new_session_for_existing_user(self, email="owner@example.test"):
        with self.sessions() as session:
            user = session.scalar(select(UserRecord).where(UserRecord.email == email))
            request = Request(
                {"type": "http", "headers": [], "client": ("127.0.0.1", 8000)}
            )
            raw, csrf, _ = create_user_session(session, self.cfg, request, user)
        self.client.cookies.set(self.cfg.session_cookie_name, raw)
        self.client.cookies.set(self.cfg.csrf_cookie_name, csrf)
        self.client.headers["X-CSRF-Token"] = csrf

    def _propose(self):
        response = self.client.post(
            "/api/v1/ask/action-plans",
            json={
                "title": "Article draft",
                "folder": "study",
                "content": "# Article draft\n\nGrounded draft.",
            },
        )
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    def _review_payload(self):
        with self.sessions() as session:
            content_hash = session.scalar(select(NoteRecord)).content_hash
        return {"reviewed": True, "content_hash": content_hash}

    def test_capabilities_distinguish_browser_from_service_token(self):
        browser = self.client.get("/api/v1/ask/action-plans/capabilities")
        self.assertEqual(browser.status_code, 200, browser.text)
        self.assertEqual(browser.json()["availableActions"], ["create_note"])
        self.assertEqual(browser.json()["workspaceModel"], "shared")
        self.assertTrue(browser.json()["requiresCsrfForWrites"])
        self.assertFalse(browser.json()["createsIndependentVault"])
        self.assertTrue(browser.json()["canCreateNamedVaultWithNote"])
        self.assertTrue(browser.json()["canTargetExistingNamedVault"])

        with self.sessions() as session:
            token, _ = issue_service_token(session, self.cfg, name="external-reader")
        service_client = TestClient(
            main.app, headers={"Authorization": f"Bearer {token}"}
        )
        self.stack.callback(service_client.close)
        service = service_client.get("/api/v1/ask/action-plans/capabilities")
        self.assertEqual(service.status_code, 200, service.text)
        self.assertEqual(service.json()["supportedActions"], ["create_note"])
        self.assertEqual(service.json()["availableActions"], [])
        self.assertFalse(service.json()["serviceTokenCanApprove"])
        denied = service_client.post(
            "/api/v1/ask/action-plans",
            json={"title": "No", "content": "Denied"},
        )
        self.assertEqual(denied.status_code, 401)

        anonymous = TestClient(main.app)
        self.stack.callback(anonymous.close)
        self.assertEqual(
            anonymous.get("/api/v1/ask/action-plans/capabilities").status_code,
            401,
        )

    def test_approved_named_vault_is_physical_and_note_identity_is_stable(self):
        proposed = self.client.post(
            "/api/v1/ask/action-plans",
            json={
                "title": "Feira de ciências",
                "folder": "study",
                "content": "# Feira de ciências\n\nUma proposta verificável.",
                "new_vault_name": "Projetos da feira",
            },
        )
        self.assertEqual(proposed.status_code, 201, proposed.text)
        plan = proposed.json()
        self.assertEqual(plan["arguments"]["newVaultName"], "Projetos da feira")
        with self.sessions() as session:
            self.assertEqual(session.query(VaultRecord).count(), 0)
            self.assertEqual(session.query(NoteRecord).count(), 0)
        self.assertEqual(list(self.cfg.vault_path.rglob("*.md")), [])

        url = f"/api/v1/ask/action-plans/{plan['id']}/approve"
        wrong = self.client.post(url, json={"arguments_hash": "0" * 64})
        self.assertEqual(wrong.status_code, 409)
        approved = self.client.post(
            url, json={"arguments_hash": plan["argumentsHash"]}
        )
        self.assertEqual(approved.status_code, 200, approved.text)
        result = approved.json()
        self.assertEqual(result["vaultId"], plan["id"])
        self.assertTrue(result["resultPath"].startswith("vaults/projetos-da-feira--ask-"))
        self.assertEqual(result["evidenceStatus"], "draft")
        self.assertTrue((self.cfg.vault_path / result["resultPath"]).is_file())
        with self.sessions() as session:
            vault = session.get(VaultRecord, plan["id"])
            note = session.scalar(select(NoteRecord))
            self.assertIsNotNone(vault)
            self.assertEqual(note.vault_id, vault.id)
            self.assertEqual(vault.name, "Projetos da feira")
            self.assertEqual(note.evidence_status, "draft")
            self.assertEqual(session.query(GraphNodeRecord).count(), 0)

        namespaces = self.client.get("/api/v1/vault/namespaces")
        self.assertEqual(namespaces.status_code, 200, namespaces.text)
        self.assertEqual(namespaces.json()["workspaceModel"], "shared")
        self.assertIn(plan["id"], [item["id"] for item in namespaces.json()["vaults"]])
        self.assertEqual(
            self.client.get(f"/api/v1/notes/{result['resultPath']}").json()["vaultId"],
            plan["id"],
        )
        replay = self.client.post(url, json={"arguments_hash": plan["argumentsHash"]})
        self.assertEqual(replay.status_code, 200, replay.text)
        self.assertEqual(len(list(self.cfg.vault_path.rglob("*.md"))), 1)
        second = self.client.post(
            "/api/v1/notes",
            json={
                "title": "Experimento",
                "folder": "inbox",
                "content": "# Experimento\n\nMedições.",
                "vault_id": plan["id"],
            },
        )
        self.assertEqual(second.status_code, 201, second.text)
        self.assertEqual(second.json()["vaultId"], plan["id"])
        self.assertTrue(second.json()["path"].startswith(vault.path + "/inbox/"))
        page = self.client.get(f"/api/v1/notes?vault_id={plan['id']}&limit=10")
        self.assertEqual(page.status_code, 200, page.text)
        self.assertEqual(page.json()["total"], 2)
        self.assertTrue(all(item["vaultId"] == plan["id"] for item in page.json()["notes"]))
        self.assertEqual(self.client.get("/api/v1/notes?vault_id=default").json()["total"], 0)
        folder_tree = self.client.get("/api/v1/folders")
        self.assertEqual(folder_tree.status_code, 200, folder_tree.text)
        protected = {
            item["path"]
            for item in folder_tree.json()["folders"]
            if item.get("protected")
        }
        self.assertIn("vaults", protected)
        self.assertIn(vault.path, protected)
        named_folder = next(
            item for item in folder_tree.json()["folders"] if item["path"] == vault.path
        )
        self.assertEqual(named_folder["name"], "Projetos da feira")
        self.assertEqual(named_folder["kind"], "vault")
        for target in ("vaults", vault.path):
            renamed = self.client.put(
                f"/api/v1/folders/{target}", json={"name": "renamed"}
            )
            self.assertEqual(renamed.status_code, 409, renamed.text)
            deleted = self.client.delete(f"/api/v1/folders/{target}")
            self.assertEqual(deleted.status_code, 409, deleted.text)
        with self.sessions() as session:
            second_note = session.scalar(
                select(NoteRecord).where(NoteRecord.path == second.json()["path"])
            )
            node = sync_note_graph_node(session, second_note)
            self.assertEqual(node.vault_id, plan["id"])
        unknown = self.client.post(
            "/api/v1/notes",
            json={"title": "No", "content": "No", "vault_id": str(uuid4())},
        )
        self.assertEqual(unknown.status_code, 404)
        next_plan = self.client.post(
            "/api/v1/ask/action-plans",
            json={
                "title": "Resultados",
                "folder": "study",
                "content": "# Resultados\n\nRascunho posterior.",
                "vault_id": plan["id"],
            },
        )
        self.assertEqual(next_plan.status_code, 201, next_plan.text)
        self.assertEqual(next_plan.json()["arguments"]["targetVaultId"], plan["id"])
        approved_next = self.client.post(
            f"/api/v1/ask/action-plans/{next_plan.json()['id']}/approve",
            json={"arguments_hash": next_plan.json()["argumentsHash"]},
        )
        self.assertEqual(approved_next.status_code, 200, approved_next.text)
        self.assertEqual(approved_next.json()["vaultId"], plan["id"])
        self.assertTrue(
            approved_next.json()["resultPath"].startswith(vault.path + "/study/")
        )

    def test_named_vault_rejects_unsafe_names_before_proposal(self):
        for name in ("../escape", "", "bad\\name", "bad\x00name", "bad:name"):
            response = self.client.post(
                "/api/v1/ask/action-plans",
                json={
                    "title": "Draft",
                    "folder": "study",
                    "content": "# Draft",
                    "new_vault_name": name,
                },
            )
            self.assertEqual(response.status_code, 422, (name, response.text))
        with self.sessions() as session:
            self.assertEqual(session.query(AskActionPlanRecord).count(), 0)

    def test_named_vault_does_not_claim_existing_unregistered_directory(self):
        response = self.client.post(
            "/api/v1/ask/action-plans",
            json={
                "title": "Draft",
                "folder": "study",
                "content": "# Draft",
                "new_vault_name": "Occupied",
            },
        )
        self.assertEqual(response.status_code, 201, response.text)
        plan = response.json()
        directory = self.cfg.vault_path / planned_ask_vault_path("Occupied", plan["id"])
        directory.mkdir(parents=True)
        (directory / "readme.txt").write_text("owner data", encoding="utf-8")
        approved = self.client.post(
            f"/api/v1/ask/action-plans/{plan['id']}/approve",
            json={"arguments_hash": plan["argumentsHash"]},
        )
        self.assertEqual(approved.status_code, 409, approved.text)
        self.assertEqual((directory / "readme.txt").read_text(), "owner data")
        self.assertEqual(list(directory.rglob("*.md")), [])
        with self.sessions() as session:
            self.assertIsNone(session.get(VaultRecord, plan["id"]))

    def test_proposal_is_read_only_and_approval_creates_one_note(self):
        plan = self._propose()
        with self.sessions() as session:
            self.assertEqual(session.query(NoteRecord).count(), 0)
        self.assertEqual(list(self.cfg.vault_path.rglob("*.md")), [])
        url = f"/api/v1/ask/action-plans/{plan['id']}/approve"
        wrong_hash = self.client.post(url, json={"arguments_hash": "0" * 64})
        self.assertEqual(wrong_hash.status_code, 409)
        self.assertEqual(list(self.cfg.vault_path.rglob("*.md")), [])
        approved = self.client.post(url, json={"arguments_hash": plan["argumentsHash"]})
        self.assertEqual(approved.status_code, 200, approved.text)
        self.assertEqual(approved.json()["status"], "completed")
        note_path = approved.json()["resultPath"]
        self.assertEqual(
            (self.cfg.vault_path / note_path).read_text(), plan["arguments"]["content"]
        )
        replay = self.client.post(url, json={"arguments_hash": plan["argumentsHash"]})
        self.assertEqual(replay.status_code, 200, replay.text)
        self.assertEqual(replay.json()["resultPath"], note_path)
        self.assertEqual(len(list(self.cfg.vault_path.rglob("*.md"))), 1)
        with self.sessions() as session:
            self.assertEqual(session.query(NoteRecord).count(), 1)
            note = session.scalar(select(NoteRecord))
            self.assertEqual(note.evidence_status, "draft")
            self.assertEqual(session.query(GraphNodeRecord).count(), 0)
            self.assertEqual(session.query(JobRecord).count(), 0)
            self.assertEqual(_retrieve_lexical_kb(session, "Grounded draft"), [])
            self.assertIsNone(
                _evidence_source_snapshot(
                    session,
                    [
                        {
                            "source": "knowledge_base",
                            "metadata": {"noteId": note.id},
                        }
                    ],
                )
            )
            self.assertEqual(
                enqueue_note_changed_jobs(
                    session, note.path, "NOTE_CREATED", note.content_hash
                ),
                [],
            )
            bypass_job = create_job(
                session,
                "GENERATE_EMBEDDING",
                {
                    "note_id": note.id,
                    "note_path": note.path,
                    "content_hash": note.content_hash,
                },
            )
            self.assertIsNone(claim_next_job(session))
            session.refresh(bypass_job)
            self.assertEqual(bypass_job.status, "superseded")
            self.assertEqual(
                capture_ask_references(
                    session,
                    [
                        {
                            "citationStatus": "source_verified",
                            "evidenceId": "forged-draft",
                            "metadata": {"noteId": note.id},
                        }
                    ],
                ),
                [],
            )
            expand_knowledge_graph(session)
            self.assertEqual(session.query(GraphNodeRecord).count(), 0)

    def test_review_releases_draft_once_and_requires_explicit_acknowledgement(self):
        plan = self._propose()
        approved = self.client.post(
            f"/api/v1/ask/action-plans/{plan['id']}/approve",
            json={"arguments_hash": plan["argumentsHash"]},
        )
        self.assertEqual(approved.status_code, 200, approved.text)
        self.assertEqual(approved.json()["evidenceStatus"], "draft")
        url = f"/api/v1/ask/action-plans/{plan['id']}/review-draft"
        self.assertEqual(
            self.client.post(url, json={"reviewed": False}).status_code, 422
        )
        released = self.client.post(url, json=self._review_payload())
        self.assertEqual(released.status_code, 200, released.text)
        self.assertEqual(released.json()["evidenceStatus"], "eligible")
        with self.sessions() as session:
            note = session.scalar(select(NoteRecord))
            self.assertEqual(note.evidence_status, "eligible")
            self.assertEqual(session.query(GraphNodeRecord).count(), 1)
            self.assertGreater(session.query(JobRecord).count(), 0)
            self.assertTrue(_retrieve_lexical_kb(session, "Grounded draft"))
            job_count = session.query(JobRecord).count()
            self.assertEqual(
                session.query(AutomationLogRecord)
                .filter(AutomationLogRecord.action_type == "REVIEW_ASK_DRAFT")
                .count(),
                1,
            )
        replay = self.client.post(url, json=self._review_payload())
        self.assertEqual(replay.status_code, 200, replay.text)
        with self.sessions() as session:
            self.assertEqual(session.query(JobRecord).count(), job_count)
            self.assertEqual(
                session.query(AutomationLogRecord)
                .filter(AutomationLogRecord.action_type == "REVIEW_ASK_DRAFT")
                .count(),
                1,
            )

    def test_review_requires_current_hash_and_can_release_edited_draft(self):
        plan = self._propose()
        approved = self.client.post(
            f"/api/v1/ask/action-plans/{plan['id']}/approve",
            json={"arguments_hash": plan["argumentsHash"]},
        )
        note_path = approved.json()["resultPath"]
        old_payload = self._review_payload()
        (self.cfg.vault_path / note_path).write_text(
            "User edited this", encoding="utf-8"
        )
        response = self.client.post(
            f"/api/v1/ask/action-plans/{plan['id']}/review-draft",
            json=old_payload,
        )
        self.assertEqual(response.status_code, 409, response.text)
        with self.sessions() as session:
            self.assertEqual(
                session.scalar(select(NoteRecord)).evidence_status, "draft"
            )
            self.assertEqual(session.query(JobRecord).count(), 0)
        current_hash = read_note(self.cfg.vault_path, note_path)["content_hash"]
        released = self.client.post(
            f"/api/v1/ask/action-plans/{plan['id']}/review-draft",
            json={"reviewed": True, "content_hash": current_hash},
        )
        self.assertEqual(released.status_code, 200, released.text)
        with self.sessions() as session:
            note = session.scalar(select(NoteRecord))
            self.assertEqual(note.content, "User edited this")
            self.assertEqual(note.evidence_status, "eligible")

    def test_review_refuses_content_changed_during_database_sync(self):
        plan = self._propose()
        approved = self.client.post(
            f"/api/v1/ask/action-plans/{plan['id']}/approve",
            json={"arguments_hash": plan["argumentsHash"]},
        )
        self.assertEqual(approved.status_code, 200, approved.text)
        relative = approved.json()["resultPath"]
        path = self.cfg.vault_path / relative
        path.write_text("First user edit", encoding="utf-8")
        approved_hash = read_note(self.cfg.vault_path, relative)["content_hash"]
        original_sync = ask_actions.sync_note_record

        def edit_during_sync(session, vault_path, note_path, **kwargs):
            (vault_path / note_path).write_text("Second user edit", encoding="utf-8")
            return original_sync(session, vault_path, note_path, **kwargs)

        with patch.object(ask_actions, "sync_note_record", side_effect=edit_during_sync):
            response = self.client.post(
                f"/api/v1/ask/action-plans/{plan['id']}/review-draft",
                json={"reviewed": True, "content_hash": approved_hash},
            )
        self.assertEqual(response.status_code, 409, response.text)
        with self.sessions() as session:
            note = session.scalar(select(NoteRecord))
            self.assertEqual(note.evidence_status, "draft")
            self.assertEqual(note.content, "Second user edit")
            self.assertEqual(session.query(JobRecord).count(), 0)
        current_hash = read_note(self.cfg.vault_path, relative)["content_hash"]
        released = self.client.post(
            f"/api/v1/ask/action-plans/{plan['id']}/review-draft",
            json={"reviewed": True, "content_hash": current_hash},
        )
        self.assertEqual(released.status_code, 200, released.text)

    def test_review_reports_missing_saved_file_as_conflict(self):
        plan = self._propose()
        approved = self.client.post(
            f"/api/v1/ask/action-plans/{plan['id']}/approve",
            json={"arguments_hash": plan["argumentsHash"]},
        )
        self.assertEqual(approved.status_code, 200, approved.text)
        payload = self._review_payload()
        (self.cfg.vault_path / approved.json()["resultPath"]).unlink()
        response = self.client.post(
            f"/api/v1/ask/action-plans/{plan['id']}/review-draft",
            json=payload,
        )
        self.assertEqual(response.status_code, 409, response.text)
        with self.sessions() as session:
            self.assertEqual(session.scalar(select(NoteRecord)).evidence_status, "draft")

    def test_review_requires_same_user_and_csrf(self):
        plan = self._propose()
        approved = self.client.post(
            f"/api/v1/ask/action-plans/{plan['id']}/approve",
            json={"arguments_hash": plan["argumentsHash"]},
        )
        self.assertEqual(approved.status_code, 200, approved.text)
        url = f"/api/v1/ask/action-plans/{plan['id']}/review-draft"
        with self.sessions() as session:
            token, _ = issue_service_token(session, self.cfg, name="external-reader")
        service_client = TestClient(
            main.app, headers={"Authorization": f"Bearer {token}"}
        )
        self.stack.callback(service_client.close)
        self.assertEqual(
            service_client.post(url, json=self._review_payload()).status_code, 401
        )
        self.client.headers.pop("X-CSRF-Token")
        self.assertEqual(
            self.client.post(url, json=self._review_payload()).status_code, 403
        )
        self._login("different@example.test")
        self.assertEqual(
            self.client.get("/api/v1/ask/action-plans/reviewable").json(), []
        )
        self.assertEqual(
            self.client.get(f"/api/v1/ask/action-plans/{plan['id']}").status_code,
            404,
        )
        self.assertEqual(
            self.client.post(url, json=self._review_payload()).status_code, 404
        )
        with self.sessions() as session:
            self.assertEqual(
                session.scalar(select(NoteRecord)).evidence_status, "draft"
            )

    def test_saved_draft_can_be_found_and_reviewed_after_same_user_relogin(self):
        plan = self._propose()
        approved = self.client.post(
            f"/api/v1/ask/action-plans/{plan['id']}/approve",
            json={"arguments_hash": plan["argumentsHash"]},
        )
        self.assertEqual(approved.status_code, 200, approved.text)
        self._new_session_for_existing_user()
        listed = self.client.get("/api/v1/ask/action-plans/reviewable")
        self.assertEqual(listed.status_code, 200, listed.text)
        self.assertEqual([item["id"] for item in listed.json()], [plan["id"]])
        self.assertEqual(listed.json()[0]["resultPath"], approved.json()["resultPath"])
        fetched = self.client.get(f"/api/v1/ask/action-plans/{plan['id']}")
        self.assertEqual(fetched.status_code, 200, fetched.text)
        self.assertEqual(fetched.json()["evidenceStatus"], "draft")
        csrf = self.client.headers.pop("X-CSRF-Token")
        self.assertEqual(
            self.client.get("/api/v1/ask/action-plans/reviewable").status_code,
            200,
        )
        self.assertEqual(
            self.client.post(
                f"/api/v1/ask/action-plans/{plan['id']}/review-draft",
                json=self._review_payload(),
            ).status_code,
            403,
        )
        self.client.headers["X-CSRF-Token"] = csrf
        released = self.client.post(
            f"/api/v1/ask/action-plans/{plan['id']}/review-draft",
            json=self._review_payload(),
        )
        self.assertEqual(released.status_code, 200, released.text)
        self.assertEqual(released.json()["evidenceStatus"], "eligible")
        self.assertEqual(
            self.client.get("/api/v1/ask/action-plans/reviewable").json(), []
        )

    def test_unapproved_plan_remains_bound_to_original_session(self):
        plan = self._propose()
        self._new_session_for_existing_user()
        self.assertEqual(
            self.client.get(f"/api/v1/ask/action-plans/{plan['id']}").status_code,
            404,
        )
        self.assertEqual(
            self.client.post(
                f"/api/v1/ask/action-plans/{plan['id']}/approve",
                json={"arguments_hash": plan["argumentsHash"]},
            ).status_code,
            404,
        )
        self.assertEqual(
            self.client.get("/api/v1/ask/action-plans/reviewable").json(), []
        )

    def test_reviewable_drafts_are_paginated_without_losing_older_items(self):
        base = self._propose()
        with self.sessions() as session:
            owner_plan = session.get(AskActionPlanRecord, base["id"])
            now = datetime.now(UTC)
            for index in range(25):
                note = NoteRecord(
                    title=f"Draft {index}",
                    slug=f"draft-{index}",
                    path=f"study/draft-{index}.md",
                    content=f"# Draft {index}",
                    evidence_status="draft",
                )
                session.add(note)
                session.flush()
                session.add(
                    AskActionPlanRecord(
                        id=str(uuid4()),
                        user_id=owner_plan.user_id,
                        session_id=owner_plan.session_id,
                        action="create_note",
                        arguments_json=json.dumps(
                            {
                                "title": f"Draft {index}",
                                "folder": "study",
                                "content": f"# Draft {index}",
                            }
                        ),
                        arguments_hash="0" * 64,
                        status="completed",
                        result_path=note.path,
                        result_note_id=note.id,
                        result_note_stable_id=note.stable_id,
                        created_at=now + timedelta(seconds=index),
                        expires_at=now + timedelta(minutes=15),
                    )
                )
            session.commit()
        first = self.client.get("/api/v1/ask/action-plans/reviewable?limit=20&offset=0")
        second = self.client.get(
            "/api/v1/ask/action-plans/reviewable?limit=20&offset=20"
        )
        self.assertEqual(first.status_code, 200, first.text)
        self.assertEqual(second.status_code, 200, second.text)
        self.assertEqual(len(first.json()), 20)
        self.assertEqual(len(second.json()), 5)
        ids = [item["id"] for item in first.json() + second.json()]
        self.assertEqual(len(set(ids)), 25)
        self.assertEqual(first.json()[0]["title"], "Draft 24")
        self.assertEqual(second.json()[-1]["title"], "Draft 0")
        self.assertEqual(
            self.client.get(
                "/api/v1/ask/action-plans/reviewable?limit=101"
            ).status_code,
            422,
        )

    def test_renamed_and_moved_draft_resolves_by_stable_identity(self):
        plan = self._propose()
        approved = self.client.post(
            f"/api/v1/ask/action-plans/{plan['id']}/approve",
            json={"arguments_hash": plan["argumentsHash"]},
        )
        self.assertEqual(approved.status_code, 200, approved.text)
        old_path = approved.json()["resultPath"]
        with self.sessions() as session:
            original = session.scalar(select(NoteRecord))
            original_id, stable_id = original.id, original.stable_id
        renamed = self.client.put(
            f"/api/v1/notes/{old_path}/rename",
            json={"title": "Reviewed draft"},
        )
        self.assertEqual(renamed.status_code, 200, renamed.text)
        renamed_path = renamed.json()["path"]
        moved = self.client.put(
            f"/api/v1/notes/{renamed_path}/move",
            json={"folder": "permanent"},
        )
        self.assertEqual(moved.status_code, 200, moved.text)
        current_path = moved.json()["path"]
        self.assertNotEqual(current_path, old_path)
        refreshed = self.client.get(f"/api/v1/ask/action-plans/{plan['id']}")
        self.assertEqual(refreshed.status_code, 200, refreshed.text)
        self.assertEqual(refreshed.json()["resultPath"], current_path)
        self.assertEqual(refreshed.json()["evidenceStatus"], "draft")
        with self.sessions() as session:
            note = session.get(NoteRecord, original_id)
            self.assertEqual(note.stable_id, stable_id)
            self.assertEqual(note.path, current_path)
            self.assertEqual(session.query(JobRecord).count(), 0)
        released = self.client.post(
            f"/api/v1/ask/action-plans/{plan['id']}/review-draft",
            json=self._review_payload(),
        )
        self.assertEqual(released.status_code, 200, released.text)
        self.assertEqual(released.json()["resultPath"], current_path)
        self.assertEqual(released.json()["evidenceStatus"], "eligible")

    def test_deleted_draft_cannot_be_replaced_at_old_path(self):
        plan = self._propose()
        approved = self.client.post(
            f"/api/v1/ask/action-plans/{plan['id']}/approve",
            json={"arguments_hash": plan["argumentsHash"]},
        )
        self.assertEqual(approved.status_code, 200, approved.text)
        old_path = approved.json()["resultPath"]
        stale_payload = self._review_payload()
        with self.sessions() as session:
            original_stable_id = session.scalar(select(NoteRecord)).stable_id
        deleted = self.client.delete(f"/api/v1/notes/{old_path}")
        self.assertEqual(deleted.status_code, 200, deleted.text)
        replacement = self.cfg.vault_path / old_path
        replacement.write_text(plan["arguments"]["content"], encoding="utf-8")
        with self.sessions() as session:
            replacement_record = sync_note_record(
                session, self.cfg.vault_path, old_path
            )
            self.assertNotEqual(replacement_record.stable_id, original_stable_id)
        refreshed = self.client.get(f"/api/v1/ask/action-plans/{plan['id']}")
        self.assertIsNone(refreshed.json()["resultPath"])
        rejected = self.client.post(
            f"/api/v1/ask/action-plans/{plan['id']}/review-draft",
            json=stale_payload,
        )
        self.assertEqual(rejected.status_code, 409, rejected.text)

    def test_session_change_and_service_token_cannot_approve(self):
        plan = self._propose()
        with self.sessions() as session:
            token, _ = issue_service_token(session, self.cfg, name="external-reader")
        service_client = TestClient(
            main.app, headers={"Authorization": f"Bearer {token}"}
        )
        self.stack.callback(service_client.close)
        service_response = service_client.post(
            f"/api/v1/ask/action-plans/{plan['id']}/approve",
            json={"arguments_hash": plan["argumentsHash"]},
        )
        self.assertEqual(service_response.status_code, 401, service_response.text)
        self.client.headers.pop("X-CSRF-Token")
        no_csrf = self.client.post(
            f"/api/v1/ask/action-plans/{plan['id']}/approve",
            json={"arguments_hash": plan["argumentsHash"]},
        )
        self.assertEqual(no_csrf.status_code, 403, no_csrf.text)
        self._login("different@example.test")
        response = self.client.post(
            f"/api/v1/ask/action-plans/{plan['id']}/approve",
            json={"arguments_hash": plan["argumentsHash"]},
        )
        self.assertEqual(response.status_code, 404, response.text)
        self.assertEqual(list(self.cfg.vault_path.rglob("*.md")), [])

    def test_cancel_and_invalid_folder_do_not_write(self):
        invalid = self.client.post(
            "/api/v1/ask/action-plans",
            json={"title": "Bad", "folder": "../../outside", "content": "text"},
        )
        self.assertEqual(invalid.status_code, 422)
        plan = self._propose()
        cancelled = self.client.post(f"/api/v1/ask/action-plans/{plan['id']}/cancel")
        self.assertEqual(cancelled.json()["status"], "cancelled")
        rejected = self.client.post(
            f"/api/v1/ask/action-plans/{plan['id']}/approve",
            json={"arguments_hash": plan["argumentsHash"]},
        )
        self.assertEqual(rejected.status_code, 409)
        with self.sessions() as session:
            self.assertEqual(
                session.scalar(select(AskActionPlanRecord).limit(1)).status, "cancelled"
            )
        self.assertEqual(list(self.cfg.vault_path.rglob("*.md")), [])

    def test_proposal_request_key_is_idempotent_and_immutable(self):
        request_key = str(uuid4())
        payload = {
            "title": "Draft",
            "folder": "study",
            "content": "# Draft",
            "request_key": request_key,
        }
        first = self.client.post("/api/v1/ask/action-plans", json=payload)
        self.assertEqual(first.status_code, 201, first.text)
        replay = self.client.post("/api/v1/ask/action-plans", json=payload)
        self.assertEqual(replay.status_code, 201, replay.text)
        self.assertEqual(replay.json()["id"], first.json()["id"])
        conflict = self.client.post(
            "/api/v1/ask/action-plans", json={**payload, "content": "Changed"}
        )
        self.assertEqual(conflict.status_code, 409, conflict.text)
        with self.sessions() as session:
            self.assertEqual(session.query(AskActionPlanRecord).count(), 1)

    def test_action_plan_contract_is_exposed_in_openapi(self):
        schema = main.app.openapi()
        created = schema["paths"]["/api/v1/ask/action-plans"]["post"]
        self.assertEqual(
            created["responses"]["201"]["content"]["application/json"]["schema"][
                "$ref"
            ],
            "#/components/schemas/ActionPlanResponse",
        )
        self.assertIn("/api/v1/ask/action-plans/{plan_id}/approve", schema["paths"])
        self.assertIn("/api/v1/ask/action-plans/reviewable", schema["paths"])

    def test_occupied_path_is_not_overwritten(self):
        plan = self._propose()
        path = (
            self.cfg.vault_path / "study" / f"article-draft--ask-{plan['id'][:12]}.md"
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("Existing user content", encoding="utf-8")
        response = self.client.post(
            f"/api/v1/ask/action-plans/{plan['id']}/approve",
            json={"arguments_hash": plan["argumentsHash"]},
        )
        self.assertEqual(response.status_code, 409, response.text)
        self.assertEqual(path.read_text(encoding="utf-8"), "Existing user content")

    def test_stale_execution_resumes_existing_identical_write(self):
        plan = self._propose()
        path = (
            self.cfg.vault_path / "study" / f"article-draft--ask-{plan['id'][:12]}.md"
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(plan["arguments"]["content"], encoding="utf-8")
        with self.sessions() as session:
            record = session.get(AskActionPlanRecord, plan["id"])
            record.status = "executing"
            record.approved_at = datetime.now(UTC) - timedelta(minutes=3)
            record.expires_at = datetime.now(UTC) - timedelta(minutes=1)
            session.commit()
        response = self.client.post(
            f"/api/v1/ask/action-plans/{plan['id']}/approve",
            json={"arguments_hash": plan["argumentsHash"]},
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["status"], "completed")
        self.assertEqual(len(list(self.cfg.vault_path.rglob("*.md"))), 1)

    def test_interrupted_write_resumes_once_without_duplicate_note(self):
        plan = self._propose()
        with (
            patch.object(ask_actions, "sync_note_record", side_effect=RuntimeError("temporary sync failure")),
            self.assertRaises(RuntimeError),
        ):
            self.client.post(
                f"/api/v1/ask/action-plans/{plan['id']}/approve",
                json={"arguments_hash": plan["argumentsHash"]},
            )
        with self.sessions() as session:
            stored = session.get(AskActionPlanRecord, plan["id"])
            self.assertEqual((stored.status, stored.execution_attempts), ("executing", 1))
            stored.approved_at = datetime.now(UTC) - timedelta(minutes=3)
            session.commit()
        response = self.client.post(
            f"/api/v1/ask/action-plans/{plan['id']}/approve",
            json={"arguments_hash": plan["argumentsHash"]},
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual((response.json()["status"], response.json()["attempts"]), ("completed", 2))
        self.assertEqual(len(list(self.cfg.vault_path.rglob("*.md"))), 1)

    def test_second_unknown_failure_stops_automatic_retries(self):
        plan = self._propose()
        for attempt in range(2):
            with (
                patch.object(ask_actions, "sync_note_record", side_effect=RuntimeError("persistent sync failure")),
                self.assertRaises(RuntimeError),
            ):
                self.client.post(
                    f"/api/v1/ask/action-plans/{plan['id']}/approve",
                    json={"arguments_hash": plan["argumentsHash"]},
                )
            if attempt == 0:
                with self.sessions() as session:
                    stored = session.get(AskActionPlanRecord, plan["id"])
                    stored.approved_at = datetime.now(UTC) - timedelta(minutes=3)
                    session.commit()
        stored = self.client.get(f"/api/v1/ask/action-plans/{plan['id']}")
        self.assertEqual(stored.status_code, 200, stored.text)
        self.assertEqual((stored.json()["status"], stored.json()["attempts"]), ("failed", 2))
        self.assertEqual(stored.json()["errorCode"], "execution_attempts_exhausted")
        self.assertEqual(
            stored.json()["recoveryPath"],
            f"study/article-draft--ask-{plan['id'][:12]}.md",
        )
        replay = self.client.post(
            f"/api/v1/ask/action-plans/{plan['id']}/approve",
            json={"arguments_hash": plan["argumentsHash"]},
        )
        self.assertEqual(replay.status_code, 409, replay.text)
        self.assertEqual(len(list(self.cfg.vault_path.rglob("*.md"))), 1)
        self._new_session_for_existing_user()
        recovered = self.client.post(f"/api/v1/ask/action-plans/{plan['id']}/reconcile")
        self.assertEqual(recovered.status_code, 200, recovered.text)
        self.assertEqual(recovered.json()["status"], "partial")
        self.assertEqual(recovered.json()["evidenceStatus"], "draft")
        self.assertEqual(
            self.client.post(f"/api/v1/ask/action-plans/{plan['id']}/reconcile").json()["id"],
            plan["id"],
        )
        with self.sessions() as session:
            self.assertEqual(session.query(NoteRecord).count(), 1)

    def test_reconciliation_requires_review_of_changed_orphaned_file(self):
        plan = self._propose()
        relative = f"study/article-draft--ask-{plan['id'][:12]}.md"
        path = self.cfg.vault_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("Another editor changed this", encoding="utf-8")
        with self.sessions() as session:
            stored = session.get(AskActionPlanRecord, plan["id"])
            stored.status = "failed"
            stored.execution_attempts = 2
            session.commit()
        result = self.client.post(f"/api/v1/ask/action-plans/{plan['id']}/reconcile")
        self.assertEqual(result.status_code, 409, result.text)
        self.assertEqual(path.read_text(encoding="utf-8"), "Another editor changed this")
        visible = self.client.get(f"/api/v1/ask/action-plans/{plan['id']}").json()
        self.assertIsNone(visible["recoveryPath"])
        self.assertEqual(visible["orphanPath"], relative)
        wrong_hash = self.client.post(
            f"/api/v1/ask/action-plans/{plan['id']}/reconcile",
            json={"reviewed": True, "content_hash": "0" * 64},
        )
        self.assertEqual(wrong_hash.status_code, 409, wrong_hash.text)
        content_hash = read_note(self.cfg.vault_path, relative)["content_hash"]
        recovered = self.client.post(
            f"/api/v1/ask/action-plans/{plan['id']}/reconcile",
            json={"reviewed": True, "content_hash": content_hash},
        )
        self.assertEqual(recovered.status_code, 200, recovered.text)
        self.assertEqual(recovered.json()["status"], "partial")
        self.assertEqual(recovered.json()["evidenceStatus"], "draft")
        self.assertEqual(recovered.json()["errorCode"], "recovered_changed_file")
        self.assertEqual(path.read_text(encoding="utf-8"), "Another editor changed this")
        with self.sessions() as session:
            self.assertEqual(session.query(GraphNodeRecord).count(), 0)
            self.assertEqual(
                session.query(AutomationLogRecord)
                .filter(AutomationLogRecord.action_type == "RECONCILE_ASK_DRAFT")
                .count(),
                1,
            )

    def test_reconciliation_refuses_edit_during_sync_then_recovers_current_file(self):
        plan = self._propose()
        relative = f"study/article-draft--ask-{plan['id'][:12]}.md"
        path = self.cfg.vault_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(plan["arguments"]["content"], encoding="utf-8")
        with self.sessions() as session:
            stored = session.get(AskActionPlanRecord, plan["id"])
            stored.status = "failed"
            session.commit()
        original_sync = ask_actions.sync_note_record

        def edit_during_sync(session, vault_path, note_path, **kwargs):
            (vault_path / note_path).write_text("Changed during recovery", encoding="utf-8")
            return original_sync(session, vault_path, note_path, **kwargs)

        with patch.object(ask_actions, "sync_note_record", side_effect=edit_during_sync):
            rejected = self.client.post(f"/api/v1/ask/action-plans/{plan['id']}/reconcile")
        self.assertEqual(rejected.status_code, 409, rejected.text)
        with self.sessions() as session:
            self.assertEqual(session.get(AskActionPlanRecord, plan["id"]).status, "failed")
            self.assertEqual(session.scalar(select(NoteRecord)).evidence_status, "draft")
        visible = self.client.get(f"/api/v1/ask/action-plans/{plan['id']}").json()
        self.assertIsNone(visible["recoveryPath"])
        self.assertEqual(visible["orphanPath"], relative)
        current_hash = read_note(self.cfg.vault_path, relative)["content_hash"]
        recovered = self.client.post(
            f"/api/v1/ask/action-plans/{plan['id']}/reconcile",
            json={"reviewed": True, "content_hash": current_hash},
        )
        self.assertEqual(recovered.status_code, 200, recovered.text)
        self.assertEqual(recovered.json()["evidenceStatus"], "draft")

    def test_reconciliation_refuses_symlink_to_another_note(self):
        plan = self._propose()
        relative = f"study/article-draft--ask-{plan['id'][:12]}.md"
        target = self.cfg.vault_path / "study" / "other.md"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(plan["arguments"]["content"], encoding="utf-8")
        (self.cfg.vault_path / relative).symlink_to(target)
        with self.sessions() as session:
            stored = session.get(AskActionPlanRecord, plan["id"])
            stored.status = "failed"
            session.commit()
        visible = self.client.get(f"/api/v1/ask/action-plans/{plan['id']}").json()
        self.assertIsNone(visible["orphanPath"])
        self.assertIsNone(visible["recoveryPath"])
        result = self.client.post(f"/api/v1/ask/action-plans/{plan['id']}/reconcile")
        self.assertEqual(result.status_code, 409, result.text)
        self.assertEqual(target.read_text(encoding="utf-8"), plan["arguments"]["content"])

    def test_failed_plans_are_paginated_and_reopen_only_for_same_user(self):
        plans = [self._propose() for _ in range(3)]
        relative = f"study/article-draft--ask-{plans[0]['id'][:12]}.md"
        path = self.cfg.vault_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("Edited after save failure", encoding="utf-8")
        with self.sessions() as session:
            for plan in plans:
                stored = session.get(AskActionPlanRecord, plan["id"])
                stored.status = "failed"
                stored.approved_at = datetime.now(UTC)
                stored.error_code = "execution_attempts_exhausted"
            session.commit()
        first = self.client.get("/api/v1/ask/action-plans/failed?limit=2&offset=0")
        second = self.client.get("/api/v1/ask/action-plans/failed?limit=2&offset=2")
        self.assertEqual(first.status_code, 200, first.text)
        self.assertEqual(second.status_code, 200, second.text)
        rows = first.json() + second.json()
        self.assertEqual(len(rows), 3)
        self.assertEqual({row["id"] for row in rows}, {plan["id"] for plan in plans})
        self.assertEqual(next(row for row in rows if row["id"] == plans[0]["id"])["orphanPath"], relative)
        self.assertNotIn("content", json.dumps(rows))
        self._login("other@example.test")
        self.assertEqual(self.client.get("/api/v1/ask/action-plans/failed").json(), [])
        self.assertEqual(
            self.client.get(f"/api/v1/ask/action-plans/{plans[0]['id']}").status_code,
            404,
        )
        self._new_session_for_existing_user()
        self.assertEqual(
            self.client.get(f"/api/v1/ask/action-plans/{plans[0]['id']}").status_code,
            200,
        )
        content_hash = read_note(self.cfg.vault_path, relative)["content_hash"]
        recovered = self.client.post(
            f"/api/v1/ask/action-plans/{plans[0]['id']}/reconcile",
            json={"reviewed": True, "content_hash": content_hash},
        )
        self.assertEqual(recovered.status_code, 200, recovered.text)
        self.assertEqual(recovered.json()["evidenceStatus"], "draft")
        remaining = self.client.get("/api/v1/ask/action-plans/failed").json()
        self.assertEqual(len(remaining), 2)

    def test_scanner_recognizes_crashed_ask_write_as_draft(self):
        plan = self._propose()
        relative = f"study/article-draft--ask-{plan['id'][:12]}.md"
        path = self.cfg.vault_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(plan["arguments"]["content"], encoding="utf-8")
        with self.sessions() as session:
            stored_plan = session.get(AskActionPlanRecord, plan["id"])
            stored_plan.status = "executing"
            session.commit()
            note = sync_note_record(session, self.cfg.vault_path, relative)
            self.assertEqual(note.evidence_status, "draft")
            self.assertEqual(session.query(GraphNodeRecord).count(), 0)

    def test_scanner_keeps_failed_plan_file_uncitable(self):
        plan = self._propose()
        relative = f"study/article-draft--ask-{plan['id'][:12]}.md"
        path = self.cfg.vault_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(plan["arguments"]["content"], encoding="utf-8")
        with self.sessions() as session:
            stored = session.get(AskActionPlanRecord, plan["id"])
            stored.status = "failed"
            session.commit()
            note = sync_note_record(session, self.cfg.vault_path, relative)
            self.assertEqual(note.evidence_status, "draft")
            self.assertEqual(session.query(GraphNodeRecord).count(), 0)

    def test_scanner_keeps_edited_interrupted_ask_file_uncitable(self):
        plan = self._propose()
        relative = f"study/article-draft--ask-{plan['id'][:12]}.md"
        path = self.cfg.vault_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("Changed after the interrupted write", encoding="utf-8")
        with self.sessions() as session:
            stored = session.get(AskActionPlanRecord, plan["id"])
            stored.status = "failed"
            session.commit()
            note = sync_note_record(session, self.cfg.vault_path, relative)
            self.assertEqual(note.evidence_status, "draft")
            self.assertEqual(session.query(GraphNodeRecord).count(), 0)

    def test_scanner_revokes_legacy_eligible_interrupted_ask_file(self):
        plan = self._propose()
        relative = f"study/article-draft--ask-{plan['id'][:12]}.md"
        path = self.cfg.vault_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("Changed after the interrupted write", encoding="utf-8")
        with self.sessions() as session:
            note = sync_note_record(session, self.cfg.vault_path, relative)
            self.assertEqual(note.evidence_status, "eligible")
            self.assertGreater(session.query(GraphNodeRecord).count(), 0)
            stored = session.get(AskActionPlanRecord, plan["id"])
            stored.status = "failed"
            session.commit()
            note = sync_note_record(session, self.cfg.vault_path, relative)
            self.assertEqual(note.evidence_status, "draft")
            self.assertEqual(session.query(GraphNodeRecord).count(), 0)

    def test_concurrent_note_edit_is_preserved_before_indexing(self):
        plan = self._propose()
        original_sync = ask_actions.sync_note_record

        def edit_then_sync(session, vault_path, note_path, **kwargs):
            (vault_path / note_path).write_text(
                "User changed this note", encoding="utf-8"
            )
            return original_sync(session, vault_path, note_path, **kwargs)

        with patch.object(ask_actions, "sync_note_record", side_effect=edit_then_sync):
            response = self.client.post(
                f"/api/v1/ask/action-plans/{plan['id']}/approve",
                json={"arguments_hash": plan["argumentsHash"]},
            )
        self.assertEqual(response.status_code, 409, response.text)
        with self.sessions() as session:
            record = session.scalar(select(NoteRecord))
            self.assertEqual(record.content, "User changed this note")
            self.assertEqual(
                session.get(AskActionPlanRecord, plan["id"]).status, "partial"
            )
        visible = self.client.get(f"/api/v1/ask/action-plans/{plan['id']}")
        self.assertEqual(visible.status_code, 200, visible.text)
        self.assertEqual(visible.json()["resultPath"], record.path)
        self.assertEqual(visible.json()["evidenceStatus"], "draft")
        reviewed = self.client.post(
            f"/api/v1/ask/action-plans/{plan['id']}/review-draft",
            json={"reviewed": True, "content_hash": record.content_hash},
        )
        self.assertEqual(reviewed.status_code, 200, reviewed.text)
        self.assertEqual(reviewed.json()["status"], "completed")
        self.assertEqual(reviewed.json()["evidenceStatus"], "eligible")


if __name__ == "__main__":
    unittest.main()
