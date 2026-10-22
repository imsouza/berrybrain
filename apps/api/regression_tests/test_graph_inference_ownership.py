"""Persisted Ask answers cannot be reused by another browser or service token."""

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
from berrybrain_api.models import GraphInferenceRecord, UserRecord
from berrybrain_api.routers import ask, graph, insights
from berrybrain_api.schema_migrations import (
    CURRENT_SCHEMA_VERSION,
    apply_schema_migrations,
)
from berrybrain_api.security import create_user_session, issue_service_token


class GraphInferenceOwnershipTests(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        root = Path(self.stack.enter_context(tempfile.TemporaryDirectory()))
        self.settings = Settings(
            _env_file=None,
            vault_path=root / "vault",
            database_url=f"sqlite:///{root / 'inferences.db'}",
            session_secret="graph-inference-owner-test-secret-32-bytes",
            vault_watcher_enabled=False,
            enable_default_owner=False,
        )
        engine = create_engine(
            self.settings.database_url, connect_args={"check_same_thread": False}
        )
        self.stack.callback(engine.dispose)
        Base.metadata.create_all(engine)
        self.sessions = sessionmaker(bind=engine)
        for module in (main, ask, graph, insights):
            self.stack.enter_context(
                patch.object(module, "SessionLocal", self.sessions)
            )
        self.stack.enter_context(
            patch("berrybrain_api.database.SessionLocal", self.sessions)
        )
        self.stack.enter_context(patch.object(main, "settings", self.settings))
        for module in (ask, graph, insights):
            self.stack.enter_context(
                patch.object(module, "get_settings", return_value=self.settings)
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
        self.stack.enter_context(
            patch.object(
                graph,
                "answer_cognitive_query",
                new=AsyncMock(
                    return_value={
                        "status": "answered",
                        "answer": "Grounded in the owner's workspace.",
                        "evidence": [],
                        "provider": "test-provider",
                        "model": "test-model",
                    }
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

    def test_browser_answer_is_private_across_flow_feedback_and_insights(self):
        owner_id = self._login("owner@example.test")
        owner_cookie = self.client.cookies.get(self.settings.session_cookie_name)
        owner_csrf = self.client.cookies.get(self.settings.csrf_cookie_name)
        response = self.client.post(
            "/api/v1/graph/infer", json={"question": "Private question?"}
        )
        self.assertEqual(response.status_code, 200, response.text)
        inference_id = response.json()["inferenceId"]
        with self.sessions() as session:
            inference = session.get(GraphInferenceRecord, inference_id)
            self.assertEqual(inference.owner_user_id, owner_id)
            self.assertEqual(inference.access_scope, "browser")

        self._login("other@example.test")
        blocked = (
            self.client.post(
                "/api/v1/ask/sessions", json={"inference_id": inference_id}
            ),
            self.client.post(
                f"/api/v1/graph/inferences/{inference_id}/feedback",
                json={"action": "upvoted"},
            ),
            self.client.post(
                "/api/v1/insights/from-inference",
                json={"inferenceId": inference_id},
            ),
        )
        self.assertEqual([item.status_code for item in blocked], [404, 404, 404])

        self.client.cookies.clear()
        self.client.headers.pop("X-CSRF-Token")
        with self.sessions() as session:
            token, _ = issue_service_token(session, self.settings, name="external")
            session.commit()
        self.client.headers["Authorization"] = f"Bearer {token}"
        self.assertEqual(
            self.client.post(
                f"/api/v1/graph/inferences/{inference_id}/feedback",
                json={"action": "upvoted"},
            ).status_code,
            404,
        )
        service_answer = self.client.post(
            "/api/v1/graph/infer", json={"question": "Service question?"}
        )
        self.assertEqual(service_answer.status_code, 200, service_answer.text)
        service_inference_id = service_answer.json()["inferenceId"]
        with self.sessions() as session:
            inference = session.get(GraphInferenceRecord, service_inference_id)
            self.assertIsNone(inference.owner_user_id)
            self.assertEqual(inference.access_scope, "service")
        self.assertEqual(
            self.client.post(
                f"/api/v1/graph/inferences/{service_inference_id}/feedback",
                json={"action": "upvoted"},
            ).status_code,
            200,
        )
        self.client.headers.pop("Authorization")
        self.client.cookies.set(self.settings.session_cookie_name, owner_cookie)
        self.client.cookies.set(self.settings.csrf_cookie_name, owner_csrf)
        self.client.headers["X-CSRF-Token"] = owner_csrf
        self.assertEqual(
            self.client.post(
                "/api/v1/ask/sessions", json={"inference_id": inference_id}
            ).status_code,
            201,
        )
        self.assertEqual(
            self.client.post(
                f"/api/v1/graph/inferences/{service_inference_id}/feedback",
                json={"action": "upvoted"},
            ).status_code,
            404,
        )

    def test_v24_backfills_only_unambiguous_legacy_owner(self):
        for count, expected in ((1, 1), (2, None)):
            with self.subTest(user_count=count):
                root = Path(self.stack.enter_context(tempfile.TemporaryDirectory()))
                engine = create_engine(f"sqlite:///{root / 'legacy.db'}")
                self.stack.callback(engine.dispose)
                with engine.begin() as connection:
                    connection.execute(
                        text("CREATE TABLE users (id INTEGER PRIMARY KEY)")
                    )
                    connection.execute(
                        text("CREATE TABLE graph_inferences (id INTEGER PRIMARY KEY)")
                    )
                    connection.execute(
                        text("INSERT INTO graph_inferences (id) VALUES (7)")
                    )
                    for user_id in range(1, count + 1):
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
                        text("INSERT INTO schema_migrations (version) VALUES (23)")
                    )
                result = apply_schema_migrations(engine)
                self.assertEqual(result["toVersion"], CURRENT_SCHEMA_VERSION)
                self.assertIn(
                    "owner_user_id",
                    {
                        column["name"]
                        for column in inspect(engine).get_columns("graph_inferences")
                    },
                )
                with engine.connect() as connection:
                    owner, scope = connection.execute(
                        text(
                            "SELECT owner_user_id, access_scope FROM graph_inferences "
                            "WHERE id = 7"
                        )
                    ).one()
                    self.assertEqual(owner, expected)
                    self.assertEqual(
                        scope,
                        "browser" if expected is not None else "legacy_unassigned",
                    )

    def test_unassigned_legacy_answer_is_inaccessible_to_browser_and_service(self):
        self._login("owner@example.test")
        with self.sessions() as session:
            inference = GraphInferenceRecord(
                question="Old private question?",
                answer="Unknown owner",
                access_scope="legacy_unassigned",
            )
            session.add(inference)
            session.commit()
            inference_id = inference.id
            token, _ = issue_service_token(session, self.settings, name="external")
            session.commit()
        endpoint = f"/api/v1/graph/inferences/{inference_id}/feedback"
        self.assertEqual(
            self.client.post(endpoint, json={"action": "upvoted"}).status_code,
            404,
        )
        self.client.cookies.clear()
        self.client.headers.pop("X-CSRF-Token")
        self.client.headers["Authorization"] = f"Bearer {token}"
        self.assertEqual(
            self.client.post(endpoint, json={"action": "upvoted"}).status_code,
            404,
        )
