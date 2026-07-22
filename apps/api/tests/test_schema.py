import unittest

from sqlalchemy import create_engine, inspect

from berrybrain_api import models  # noqa: F401
from berrybrain_api.database import Base


class SchemaTest(unittest.TestCase):
    def test_initial_data_model_tables_exist(self) -> None:
        engine = create_engine(
            "sqlite:///:memory:", connect_args={"check_same_thread": False}
        )
        Base.metadata.create_all(bind=engine)
        inspector = inspect(engine)

        expected_tables = {
            "automation_logs",
            "concepts",
            "connections",
            "graph_inferences",
            "insights",
            "jobs",
            "note_attachments",
            "attachment_extractions",
            "notes",
            "profiles",
            "settings",
            "security_audit_events",
            "tags",
            "users",
            "user_sessions",
            "auth_otps",
            "login_attempts",
        }

        self.assertTrue(expected_tables.issubset(set(inspector.get_table_names())))

    def test_initial_data_model_required_columns_exist(self) -> None:
        engine = create_engine(
            "sqlite:///:memory:", connect_args={"check_same_thread": False}
        )
        Base.metadata.create_all(bind=engine)
        inspector = inspect(engine)

        required_columns = {
            "connections": {
                "source_note_id",
                "target_note_id",
                "connection_type",
                "confidence",
                "reason",
                "created_by",
            },
            "insights": {
                "type",
                "title",
                "description",
                "related_notes",
                "priority",
                "dismissed_at",
            },
            "graph_inferences": {
                "question",
                "answer",
                "status",
                "confidence",
                "routes",
                "evidence",
                "related_nodes",
                "provider",
                "model",
                "prompt_version",
                "insight_id",
            },
            "automation_logs": {
                "action_type",
                "target_type",
                "target_id",
                "before_state",
                "after_state",
                "reversible",
            },
            "settings": {"key", "value", "updated_at"},
            "attachment_extractions": {
                "attachment_id",
                "status",
                "extracted_text",
                "summary",
                "provider",
                "model",
                "confidence",
                "error",
            },
            "users": {
                "email",
                "password_hash",
                "email_verified",
                "two_factor_enabled",
                "locked_until",
                "force_password_reset",
            },
            "profiles": {"name", "slug", "vault_subpath", "source", "status"},
            "user_sessions": {
                "user_id",
                "session_hash",
                "csrf_token_hash",
                "expires_at",
                "revoked_at",
            },
            "auth_otps": {
                "email",
                "purpose",
                "code_hash",
                "challenge_token_hash",
                "attempts",
                "expires_at",
                "used_at",
            },
            "security_audit_events": {
                "actor_email",
                "action",
                "target_type",
                "target_id",
                "metadata",
            },
        }

        for table_name, columns in required_columns.items():
            existing = {column["name"] for column in inspector.get_columns(table_name)}
            self.assertTrue(columns.issubset(existing), table_name)

    def test_second_brain_traceability_columns_exist(self) -> None:
        engine = create_engine(
            "sqlite:///:memory:", connect_args={"check_same_thread": False}
        )
        Base.metadata.create_all(bind=engine)
        inspector = inspect(engine)

        required_columns = {
            "concepts": {
                "frequency",
                "related_note_ids",
                "confidence",
                "status",
                "provider",
                "model",
                "source_evidence",
            },
            "connections": {
                "evidence",
                "ai_notes",
                "user_notes",
                "provider",
                "model",
                "prompt_version",
                "status",
            },
            "insights": {
                "why_it_matters",
                "evidence",
                "suggested_action",
                "graph_impact",
                "confidence",
                "status",
                "provider",
                "model",
            },
            "graph_nodes": {
                "title",
                "summary",
                "ai_notes",
                "user_notes",
                "source",
                "source_note_ids",
                "confidence",
                "created_by",
                "created_by_model",
                "status",
            },
            "graph_edges": {
                "label",
                "evidence",
                "ai_notes",
                "user_notes",
                "source_note_ids",
                "provider",
                "model",
                "prompt_version",
                "status",
            },
        }

        for table_name, columns in required_columns.items():
            existing = {column["name"] for column in inspector.get_columns(table_name)}
            self.assertTrue(columns.issubset(existing), table_name)


if __name__ == "__main__":
    unittest.main()
