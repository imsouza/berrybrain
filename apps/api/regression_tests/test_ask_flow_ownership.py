"""Flow sessions must not be shared by guessing their identifiers."""

import tempfile
import unittest
from contextlib import ExitStack
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from starlette.requests import Request

from berrybrain_api import main
from berrybrain_api.config import Settings
from berrybrain_api.database import Base
from berrybrain_api.models import (
    AskSessionRecord,
    GraphNodeRecord,
    NoteRecord,
    UserRecord,
)
from berrybrain_api.routers import ask
from berrybrain_api.schema_migrations import (
    CURRENT_SCHEMA_VERSION,
    apply_schema_migrations,
)
from berrybrain_api.security import create_user_session, issue_service_token


class AskFlowOwnershipTests(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        root = Path(self.stack.enter_context(tempfile.TemporaryDirectory()))
        self.settings = Settings(
            _env_file=None,
            vault_path=root / "vault",
            database_url=f"sqlite:///{root / 'flow.db'}",
            session_secret="flow-ownership-integration-secret-32-bytes",
            vault_watcher_enabled=False,
            enable_default_owner=False,
        )
        engine = create_engine(
            self.settings.database_url, connect_args={"check_same_thread": False}
        )
        self.stack.callback(engine.dispose)
        Base.metadata.create_all(engine)
        self.sessions = sessionmaker(bind=engine)
        self.stack.enter_context(patch.object(main, "settings", self.settings))
        self.stack.enter_context(patch.object(main, "SessionLocal", self.sessions))
        self.stack.enter_context(patch.object(ask, "SessionLocal", self.sessions))
        self.stack.enter_context(
            patch.object(ask, "get_settings", return_value=self.settings)
        )
        self.stack.enter_context(
            patch(
                "berrybrain_api.ask_flow.load_configuration",
                return_value=SimpleNamespace(
                    validated_at=datetime.now(UTC),
                    configuration_fingerprint="configured-model",
                ),
            )
        )
        self.client = TestClient(main.app)
        self.stack.callback(self.client.close)

    def _login(self, email: str) -> int:
        with self.sessions() as session:
            user = UserRecord(email=email, email_verified=True, password_hash="unused")
            session.add(user)
            session.commit()
            request = Request(
                {"type": "http", "headers": [], "client": ("127.0.0.1", 8000)}
            )
            raw, csrf, _ = create_user_session(session, self.settings, request, user)
            user_id = user.id
        self.client.cookies.set(self.settings.session_cookie_name, raw)
        self.client.cookies.set(self.settings.csrf_cookie_name, csrf)
        self.client.headers["X-CSRF-Token"] = csrf
        return user_id

    def test_only_owner_can_read_or_mutate_flow(self):
        owner_id = self._login("owner@example.test")
        created = self.client.post("/api/v1/ask/sessions", json={})
        self.assertEqual(created.status_code, 201, created.text)
        flow_id = created.json()["session"]["id"]
        with self.sessions() as session:
            self.assertEqual(
                session.get(AskSessionRecord, flow_id).owner_user_id, owner_id
            )

        self._login("other@example.test")
        self.assertEqual(
            self.client.get(f"/api/v1/ask/sessions/{flow_id}").status_code, 404
        )
        for suffix in ("turns", "cancel", "close", "insight"):
            response = self.client.post(
                f"/api/v1/ask/sessions/{flow_id}/{suffix}",
                json={"content": "test"} if suffix == "turns" else None,
            )
            self.assertEqual(response.status_code, 404, (suffix, response.text))
        feedback = self.client.post(
            f"/api/v1/ask/sessions/{flow_id}/turns/1/feedback",
            json={"action": "upvoted"},
        )
        self.assertEqual(feedback.status_code, 404, feedback.text)

    def test_unowned_legacy_flow_is_not_claimed_and_service_token_cannot_impersonate(
        self,
    ):
        self._login("owner@example.test")
        with self.sessions() as session:
            session.add(AskSessionRecord(id="legacy-flow", owner_user_id=None))
            token, _ = issue_service_token(session, self.settings, name="external")
            session.commit()
        self.assertEqual(
            self.client.get("/api/v1/ask/sessions/legacy-flow").status_code, 404
        )
        self.client.cookies.clear()
        self.client.headers.pop("X-CSRF-Token")
        self.client.headers["Authorization"] = f"Bearer {token}"
        response = self.client.post("/api/v1/ask/sessions", json={})
        self.assertEqual(response.status_code, 401, response.text)

    def test_multi_turn_http_returns_current_verified_links(self):
        self._login("owner@example.test")
        with self.sessions() as session:
            note = NoteRecord(
                title="Projeto da feira",
                slug="projeto-da-feira",
                path="Feira/Projeto.md",
                content="# Projeto da feira\nExperimento com grafos.\n",
                content_hash="version-one",
            )
            node = GraphNodeRecord(
                type="concept",
                label="Grafos",
                title="Grafos",
                status="confirmed",
                quality_gate_status="passed",
                semantic_status="active",
            )
            session.add_all([note, node])
            session.commit()
            note_id, node_id = note.id, node.id

        created = self.client.post("/api/v1/ask/sessions", json={})
        self.assertEqual(created.status_code, 201, created.text)
        flow_id = created.json()["session"]["id"]
        first_answer = AsyncMock(
            return_value={
                "status": "answered",
                "answer": "Use o projeto e o conceito de grafos.",
                "evidence": [
                    {
                        "evidenceId": "note-evidence",
                        "metadata": {"noteId": note_id},
                        "citationStatus": "source_verified",
                    },
                    {
                        "evidenceId": "node-evidence",
                        "metadata": {"nodeId": node_id},
                        "citationStatus": "source_verified",
                    },
                ],
            }
        )
        with patch("berrybrain_api.ask_flow.answer_cognitive_query", first_answer):
            first = self.client.post(
                f"/api/v1/ask/sessions/{flow_id}/turns",
                json={"content": "Quais notas ajudam no artigo?"},
            )
        self.assertEqual(first.status_code, 200, first.text)
        self.assertEqual(first_answer.await_count, 1)
        self.assertEqual(
            {ref["kind"] for ref in first.json()["assistantTurn"]["references"]},
            {"note", "graph_node"},
        )

        with patch(
            "berrybrain_api.ask_flow.answer_cognitive_query", new_callable=AsyncMock
        ) as model:
            linked = self.client.post(
                f"/api/v1/ask/sessions/{flow_id}/turns",
                json={"content": "Consegue linkar as notas para mim?"},
            )
            model.assert_not_awaited()
        self.assertEqual(linked.status_code, 200, linked.text)
        content = linked.json()["assistantTurn"]["content"]
        self.assertIn(f"bbref:resolved:note:{note_id}", content)
        self.assertIn(f"bbref:resolved:graph_node:{node_id}", content)

        with self.sessions() as session:
            session.delete(session.get(NoteRecord, note_id))
            session.commit()
        with patch(
            "berrybrain_api.ask_flow.answer_cognitive_query", new_callable=AsyncMock
        ) as model:
            after_delete = self.client.post(
                f"/api/v1/ask/sessions/{flow_id}/turns",
                json={"content": "Consegue linkar as notas agora?"},
            )
            model.assert_not_awaited()
        self.assertEqual(after_delete.status_code, 200, after_delete.text)
        current = after_delete.json()["assistantTurn"]
        self.assertNotIn(f"bbref:resolved:note:{note_id}", current["content"])
        self.assertIn(f"bbref:resolved:graph_node:{node_id}", current["content"])
        self.assertEqual([ref["kind"] for ref in current["references"]], ["graph_node"])

    def test_migration_adds_owner_without_assigning_legacy_history(self):
        root = Path(self.stack.enter_context(tempfile.TemporaryDirectory()))
        engine = create_engine(f"sqlite:///{root / 'legacy.db'}")
        self.stack.callback(engine.dispose)
        with engine.begin() as connection:
            connection.execute(
                text("CREATE TABLE ask_sessions (id VARCHAR(64) PRIMARY KEY)")
            )
            connection.execute(
                text("INSERT INTO ask_sessions (id) VALUES ('old-flow')")
            )
            connection.execute(
                text(
                    "CREATE TABLE schema_migrations (version INTEGER PRIMARY KEY, "
                    "name VARCHAR(120), description TEXT, applied_at DATETIME)"
                )
            )
            connection.execute(
                text("INSERT INTO schema_migrations (version) VALUES (20)")
            )
        self.assertEqual(
            apply_schema_migrations(engine)["toVersion"], CURRENT_SCHEMA_VERSION
        )
        self.assertIn(
            "owner_user_id",
            {column["name"] for column in inspect(engine).get_columns("ask_sessions")},
        )
        with engine.connect() as connection:
            self.assertIsNone(
                connection.execute(
                    text("SELECT owner_user_id FROM ask_sessions WHERE id = 'old-flow'")
                ).scalar_one()
            )

    def test_migration_claims_legacy_flow_only_for_unambiguous_single_user(self):
        for user_count, expected_owner in ((1, 1), (2, None)):
            with self.subTest(user_count=user_count):
                root = Path(self.stack.enter_context(tempfile.TemporaryDirectory()))
                engine = create_engine(f"sqlite:///{root / 'legacy.db'}")
                self.stack.callback(engine.dispose)
                with engine.begin() as connection:
                    connection.execute(
                        text("CREATE TABLE users (id INTEGER PRIMARY KEY)")
                    )
                    connection.execute(
                        text("CREATE TABLE ask_sessions (id VARCHAR(64) PRIMARY KEY)")
                    )
                    connection.execute(
                        text("INSERT INTO ask_sessions (id) VALUES ('old-flow')")
                    )
                    for user_id in range(1, user_count + 1):
                        connection.execute(
                            text("INSERT INTO users (id) VALUES (:user_id)"),
                            {"user_id": user_id},
                        )
                    connection.execute(
                        text(
                            "CREATE TABLE schema_migrations (version INTEGER PRIMARY KEY, "
                            "name VARCHAR(120), description TEXT, applied_at DATETIME)"
                        )
                    )
                    connection.execute(
                        text("INSERT INTO schema_migrations (version) VALUES (20)")
                    )
                self.assertEqual(
                    apply_schema_migrations(engine)["toVersion"],
                    CURRENT_SCHEMA_VERSION,
                )
                with engine.connect() as connection:
                    owner = connection.execute(
                        text(
                            "SELECT owner_user_id FROM ask_sessions WHERE id = 'old-flow'"
                        )
                    ).scalar_one()
                self.assertEqual(owner, expected_owner)


if __name__ == "__main__":
    unittest.main()
