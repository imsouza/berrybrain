import json
import unittest

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from berrybrain_api.database import Base
from berrybrain_api.models import (
    GraphEdgeRecord,
    GraphNodeRecord,
    SemanticProfileRecord,
)
from berrybrain_api.schema_migrations import (
    CURRENT_SCHEMA_VERSION,
    IncompatibleSchemaError,
    apply_schema_migrations,
    assert_schema_compatible,
    downgrade_schema,
    get_schema_version,
    schema_diagnostic,
)


class SchemaMigrationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite:///:memory:")

    def tearDown(self) -> None:
        self.engine.dispose()

    def test_v25_fails_interrupted_flow_turns_and_serializes_new_ones(self) -> None:
        with self.engine.begin() as connection:
            connection.execute(
                text(
                    "CREATE TABLE schema_migrations (version INTEGER PRIMARY KEY, "
                    "name TEXT, description TEXT, applied_at TEXT)"
                )
            )
            connection.execute(
                text("INSERT INTO schema_migrations (version) VALUES (24)")
            )
            connection.execute(
                text(
                    "CREATE TABLE ask_turns (id INTEGER PRIMARY KEY, "
                    "session_id TEXT NOT NULL, role TEXT NOT NULL, status TEXT NOT NULL)"
                )
            )
            connection.execute(
                text(
                    "INSERT INTO ask_turns (id, session_id, role, status) VALUES "
                    "(1, 'flow-a', 'user', 'processing'), "
                    "(2, 'flow-a', 'user', 'processing'), "
                    "(3, 'flow-a', 'assistant', 'completed')"
                )
            )

        # Startup runs create_all before migrations; an existing table must not
        # receive the unique index until its interrupted turns are normalized.
        Base.metadata.create_all(self.engine)
        self.assertEqual(
            apply_schema_migrations(self.engine)["toVersion"],
            CURRENT_SCHEMA_VERSION,
        )
        with self.engine.connect() as connection:
            statuses = (
                connection.execute(text("SELECT status FROM ask_turns ORDER BY id"))
                .scalars()
                .all()
            )
        self.assertEqual(statuses, ["failed", "failed", "completed"])
        self.assertTrue(
            any(
                index["name"] == "ux_ask_turns_processing_user_per_session"
                and index["unique"]
                for index in inspect(self.engine).get_indexes("ask_turns")
            )
        )
        with self.assertRaises(IntegrityError), self.engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO ask_turns (id, session_id, role, status) VALUES "
                    "(4, 'flow-a', 'user', 'processing'), "
                    "(5, 'flow-a', 'user', 'processing')"
                )
            )
        self.assertEqual(apply_schema_migrations(self.engine)["applied"], [])

    def test_v21_indexes_evaluations_for_home_backlog(self) -> None:
        with self.engine.begin() as connection:
            connection.execute(
                text(
                    "CREATE TABLE schema_migrations (version INTEGER PRIMARY KEY, "
                    "name TEXT, description TEXT, applied_at TEXT)"
                )
            )
            connection.execute(
                text("INSERT INTO schema_migrations (version) VALUES (20)")
            )
            connection.execute(
                text(
                    "CREATE TABLE artifact_evaluations (id INTEGER PRIMARY KEY, "
                    "artifact_type TEXT, artifact_id INTEGER)"
                )
            )
        self.assertEqual(
            apply_schema_migrations(self.engine)["toVersion"],
            CURRENT_SCHEMA_VERSION,
        )
        indexes = inspect(self.engine).get_indexes("artifact_evaluations")
        self.assertTrue(
            any(
                index["name"] == "ix_artifact_evaluations_type_id"
                and index["column_names"] == ["artifact_type", "artifact_id"]
                for index in indexes
            )
        )

    def test_v22_backfills_and_indexes_legacy_graph_labels(self) -> None:
        Base.metadata.create_all(self.engine)
        with Session(self.engine) as session:
            session.add(
                GraphNodeRecord(
                    type="concept",
                    label="Distributed-Systems",
                    title="Distributed Systems",
                    canonical_label="",
                )
            )
            session.commit()
        with self.engine.begin() as connection:
            connection.execute(
                text("DROP INDEX IF EXISTS ix_graph_nodes_type_canonical_label")
            )
            connection.execute(
                text(
                    "CREATE TABLE schema_migrations (version INTEGER PRIMARY KEY, "
                    "name TEXT, description TEXT, applied_at TEXT)"
                )
            )
            connection.execute(
                text("INSERT INTO schema_migrations (version) VALUES (21)")
            )
        result = apply_schema_migrations(self.engine)
        self.assertEqual(result["toVersion"], CURRENT_SCHEMA_VERSION)
        with self.engine.connect() as connection:
            self.assertEqual(
                connection.scalar(text("SELECT canonical_label FROM graph_nodes")),
                "distributed systems",
            )
        indexes = inspect(self.engine).get_indexes("graph_nodes")
        self.assertTrue(
            any(
                index["name"] == "ix_graph_nodes_type_canonical_label"
                and index["column_names"] == ["type", "canonical_label"]
                for index in indexes
            )
        )
        self.assertEqual(apply_schema_migrations(self.engine)["applied"], [])

    def test_v23_registers_default_vault_and_preserves_existing_notes(self) -> None:
        with self.engine.begin() as connection:
            connection.execute(
                text(
                    "CREATE TABLE schema_migrations (version INTEGER PRIMARY KEY, "
                    "name TEXT, description TEXT, applied_at TEXT)"
                )
            )
            connection.execute(
                text("INSERT INTO schema_migrations (version) VALUES (22)")
            )
            connection.execute(
                text("CREATE TABLE notes (id INTEGER PRIMARY KEY, path TEXT NOT NULL)")
            )
            connection.execute(
                text("INSERT INTO notes (id, path) VALUES (1, 'inbox/old.md')")
            )
        result = apply_schema_migrations(self.engine)
        self.assertEqual(result["toVersion"], CURRENT_SCHEMA_VERSION)
        with self.engine.connect() as connection:
            self.assertEqual(
                connection.scalar(text("SELECT vault_id FROM notes WHERE id = 1")),
                "default",
            )
            self.assertEqual(
                connection.scalar(text("SELECT path FROM vaults WHERE id = 'default'")),
                "",
            )
        self.assertEqual(apply_schema_migrations(self.engine)["applied"], [])

    def test_v19_backfills_only_matching_ask_note_identity(self) -> None:
        matching_id = "77e26341-aaa0-4ceb-9d5f-ffe12e2029c0"
        replaced_id = "6a00c132-cf90-481d-a979-ab3abb57db11"
        with self.engine.begin() as connection:
            connection.execute(
                text(
                    "CREATE TABLE schema_migrations (version INTEGER PRIMARY KEY, "
                    "name TEXT NOT NULL, description TEXT NOT NULL, applied_at TEXT NOT NULL)"
                )
            )
            connection.execute(
                text(
                    "CREATE TABLE ask_action_plans (id TEXT PRIMARY KEY, "
                    "result_path TEXT, arguments_json TEXT)"
                )
            )
            connection.execute(
                text(
                    "CREATE TABLE notes (id INTEGER PRIMARY KEY, path TEXT, "
                    "stable_id TEXT, content TEXT)"
                )
            )
            connection.execute(
                text(
                    "INSERT INTO schema_migrations (version, name, description, applied_at) "
                    "VALUES (:version, 'old', '', 'now')"
                ),
                [{"version": version} for version in range(1, 19)],
            )
            for index, plan_id in enumerate((matching_id, replaced_id), start=1):
                path = f"study/draft--ask-{plan_id[:12]}.md"
                connection.execute(
                    text(
                        "INSERT INTO ask_action_plans (id, result_path, arguments_json) "
                        "VALUES (:id, :path, :arguments)"
                    ),
                    {
                        "id": plan_id,
                        "path": path,
                        "arguments": json.dumps({"content": "# Original"}),
                    },
                )
                connection.execute(
                    text(
                        "INSERT INTO notes (id, path, stable_id, content) "
                        "VALUES (:id, :path, :stable_id, :content)"
                    ),
                    {
                        "id": index,
                        "path": path,
                        "stable_id": f"stable-{index}",
                        "content": "# Original" if index == 1 else "# Replacement",
                    },
                )
        apply_schema_migrations(self.engine)
        with self.engine.connect() as connection:
            rows = (
                connection.execute(
                    text(
                        "SELECT id, result_note_id, result_note_stable_id, execution_attempts "
                        "FROM ask_action_plans ORDER BY id"
                    )
                )
                .mappings()
                .all()
            )
        bound = {
            row["id"]: (row["result_note_id"], row["result_note_stable_id"])
            for row in rows
        }
        self.assertEqual(bound[matching_id], (1, "stable-1"))
        self.assertEqual(bound[replaced_id], (0, ""))
        self.assertTrue(all(row["execution_attempts"] == 0 for row in rows))

    def test_v18_existing_notes_default_to_eligible(self) -> None:
        with self.engine.begin() as connection:
            connection.execute(
                text("CREATE TABLE notes (id INTEGER PRIMARY KEY, path TEXT)")
            )
            connection.execute(
                text("INSERT INTO notes (id, path) VALUES (1, 'study/old.md')")
            )
        apply_schema_migrations(self.engine)
        columns = {item["name"] for item in inspect(self.engine).get_columns("notes")}
        self.assertIn("evidence_status", columns)
        with self.engine.connect() as connection:
            self.assertEqual(
                connection.scalar(
                    text("SELECT evidence_status FROM notes WHERE id = 1")
                ),
                "eligible",
            )

    def test_v16_adds_fallback_provenance_to_existing_tables(self) -> None:
        with self.engine.begin() as connection:
            connection.execute(
                text(
                    "CREATE TABLE schema_migrations ("
                    "version INTEGER PRIMARY KEY, name TEXT NOT NULL, "
                    "description TEXT NOT NULL, applied_at TEXT NOT NULL)"
                )
            )
            connection.execute(text("CREATE TABLE ask_turns (id INTEGER PRIMARY KEY)"))
            connection.execute(
                text("CREATE TABLE graph_inferences (id INTEGER PRIMARY KEY)")
            )
            connection.execute(
                text(
                    "INSERT INTO schema_migrations "
                    "(version, name, description, applied_at) "
                    "VALUES (:version, :name, '', 'now')"
                ),
                [
                    {"version": version, "name": f"migration-{version}"}
                    for version in range(1, 16)
                ],
            )
        result = apply_schema_migrations(self.engine)
        self.assertEqual(result["toVersion"], CURRENT_SCHEMA_VERSION)
        for table in ("ask_turns", "graph_inferences"):
            columns = {item["name"] for item in inspect(self.engine).get_columns(table)}
            self.assertIn("fallback_used", columns)
            self.assertIn("fallback_reason", columns)
        self.assertEqual(apply_schema_migrations(self.engine)["applied"], [])
        self.assertIn("ask_action_plans", inspect(self.engine).get_table_names())

    def test_upgrade_and_compatible_downgrade_are_versioned(self) -> None:
        result = apply_schema_migrations(self.engine)
        self.assertEqual(result["fromVersion"], 0)
        self.assertEqual(result["toVersion"], CURRENT_SCHEMA_VERSION)
        self.assertEqual(
            [item["version"] for item in result["applied"]],
            list(range(1, CURRENT_SCHEMA_VERSION + 1)),
        )

        downgraded = downgrade_schema(self.engine, CURRENT_SCHEMA_VERSION - 1)
        self.assertEqual(downgraded["toVersion"], CURRENT_SCHEMA_VERSION - 1)
        upgraded = apply_schema_migrations(self.engine)
        self.assertEqual(upgraded["toVersion"], CURRENT_SCHEMA_VERSION)
        self.assertTrue(schema_diagnostic(self.engine)["compatible"])
        inspector = inspect(self.engine)
        self.assertIn("model_invocations", inspector.get_table_names())
        columns = {item["name"] for item in inspector.get_columns("model_invocations")}
        self.assertIn("prompt_version", columns)
        self.assertNotIn("prompt", columns)
        self.assertIn("worker_inbox", inspector.get_table_names())

    def test_v13_normalizes_unsupported_legacy_ui_font(self) -> None:
        Base.metadata.create_all(self.engine)
        with self.engine.begin() as connection:
            connection.execute(
                text(
                    "CREATE TABLE schema_migrations ("
                    "version INTEGER PRIMARY KEY, name TEXT NOT NULL, "
                    "description TEXT NOT NULL, applied_at TEXT NOT NULL)"
                )
            )
            connection.execute(
                text(
                    "INSERT INTO schema_migrations "
                    "(version, name, description, applied_at) "
                    "VALUES (:version, :name, '', 'now')"
                ),
                [
                    {"version": version, "name": f"migration-{version}"}
                    for version in range(1, 13)
                ],
            )
            connection.execute(
                text(
                    "INSERT INTO settings (key, value, updated_at) "
                    "VALUES ('ui_font', 'roboto', CURRENT_TIMESTAMP)"
                )
            )

        result = apply_schema_migrations(self.engine)

        self.assertEqual(result["toVersion"], CURRENT_SCHEMA_VERSION)
        with self.engine.connect() as connection:
            value = connection.execute(
                text("SELECT value FROM settings WHERE key = 'ui_font'")
            ).scalar_one()
        self.assertEqual(value, "inter")

    def test_v12_backfills_identity_archives_orphans_and_guards_edges(self) -> None:
        Base.metadata.create_all(self.engine)
        with self.engine.begin() as connection:
            connection.execute(
                text(
                    "CREATE TABLE schema_migrations ("
                    "version INTEGER PRIMARY KEY, name TEXT NOT NULL, "
                    "description TEXT NOT NULL, applied_at TEXT NOT NULL)"
                )
            )
            connection.execute(
                text(
                    "INSERT INTO schema_migrations "
                    "(version, name, description, applied_at) "
                    "VALUES (:version, :name, '', 'now')"
                ),
                [
                    {"version": version, "name": f"migration-{version}"}
                    for version in range(1, 12)
                ],
            )
        with Session(self.engine) as session:
            node = GraphNodeRecord(type="concept", label="Time series")
            session.add(node)
            session.flush()
            node.stable_id = ""
            node.iri = ""
            session.add(
                SemanticProfileRecord(
                    node_id=999_999,
                    source_fingerprint="orphan-profile",
                )
            )
            session.commit()
            node_id = node.id

        result = apply_schema_migrations(self.engine)
        self.assertEqual(result["toVersion"], CURRENT_SCHEMA_VERSION)
        with Session(self.engine) as session:
            migrated_node = session.get(GraphNodeRecord, node_id)
            assert migrated_node is not None
            self.assertEqual(len(migrated_node.stable_id), 36)
            self.assertEqual(
                migrated_node.iri,
                f"urn:berrybrain:graph-node:{migrated_node.stable_id}",
            )
            self.assertEqual(session.query(SemanticProfileRecord).count(), 0)
            archived = session.execute(
                text(
                    "SELECT COUNT(*) FROM schema_migration_archive "
                    "WHERE table_name = 'semantic_profiles'"
                )
            ).scalar_one()
            self.assertEqual(archived, 1)
            session.add(
                GraphEdgeRecord(
                    source_node_id=migrated_node.id,
                    target_node_id=999_999,
                    type="related",
                )
            )
            with self.assertRaises(IntegrityError):
                session.flush()

    def test_v5_upgrade_adds_claim_token_and_worker_inbox(self) -> None:
        with self.engine.begin() as connection:
            connection.execute(
                text(
                    "CREATE TABLE jobs ("
                    "id INTEGER PRIMARY KEY, status TEXT NOT NULL, attempts INTEGER NOT NULL)"
                )
            )
            connection.execute(
                text(
                    "CREATE TABLE schema_migrations ("
                    "version INTEGER PRIMARY KEY, name TEXT NOT NULL, "
                    "description TEXT NOT NULL, applied_at TEXT NOT NULL)"
                )
            )
            for version in range(1, 6):
                connection.execute(
                    text(
                        "INSERT INTO schema_migrations "
                        "(version, name, description, applied_at) "
                        "VALUES (:version, :name, '', 'now')"
                    ),
                    {"version": version, "name": f"migration-{version}"},
                )

        result = apply_schema_migrations(self.engine)
        inspector = inspect(self.engine)

        self.assertEqual(result["fromVersion"], 5)
        self.assertEqual(result["toVersion"], CURRENT_SCHEMA_VERSION)
        self.assertIn(
            "claim_token",
            {column["name"] for column in inspector.get_columns("jobs")},
        )
        self.assertIn("worker_inbox", inspector.get_table_names())

    def test_v10_upgrade_adds_note_connection_confidence_intervals(self) -> None:
        with self.engine.begin() as connection:
            connection.execute(
                text(
                    "CREATE TABLE connections (id INTEGER PRIMARY KEY, confidence INTEGER)"
                )
            )
            connection.execute(
                text("CREATE TABLE concepts (id INTEGER PRIMARY KEY, confidence FLOAT)")
            )
            connection.execute(
                text(
                    "CREATE TABLE graph_inferences "
                    "(id INTEGER PRIMARY KEY, confidence FLOAT)"
                )
            )
            connection.execute(
                text(
                    "CREATE TABLE schema_migrations ("
                    "version INTEGER PRIMARY KEY, name TEXT NOT NULL, "
                    "description TEXT NOT NULL, applied_at TEXT NOT NULL)"
                )
            )
            for version in range(1, 10):
                connection.execute(
                    text(
                        "INSERT INTO schema_migrations "
                        "(version, name, description, applied_at) "
                        "VALUES (:version, :name, '', 'now')"
                    ),
                    {"version": version, "name": f"migration-{version}"},
                )

        result = apply_schema_migrations(self.engine)
        connection_columns = {
            item["name"] for item in inspect(self.engine).get_columns("connections")
        }
        concept_columns = {
            item["name"] for item in inspect(self.engine).get_columns("concepts")
        }
        inference_columns = {
            item["name"]
            for item in inspect(self.engine).get_columns("graph_inferences")
        }

        self.assertEqual(result["fromVersion"], 9)
        self.assertEqual(result["toVersion"], CURRENT_SCHEMA_VERSION)
        self.assertIn("confidence_lower", connection_columns)
        self.assertIn("confidence_upper", connection_columns)
        self.assertIn("confidence_sample_size", connection_columns)
        self.assertIn("confidence_method", connection_columns)
        self.assertIn("confidence_lower", concept_columns)
        self.assertIn("confidence_method", concept_columns)
        self.assertIn("confidence_lower", inference_columns)
        self.assertIn("confidence_method", inference_columns)

    def test_v11_upgrade_adds_contextual_graph_feedback(self) -> None:
        with self.engine.begin() as connection:
            connection.execute(
                text(
                    "CREATE TABLE schema_migrations ("
                    "version INTEGER PRIMARY KEY, name TEXT NOT NULL, "
                    "description TEXT NOT NULL, applied_at TEXT NOT NULL)"
                )
            )
            for version in range(1, 11):
                connection.execute(
                    text(
                        "INSERT INTO schema_migrations "
                        "(version, name, description, applied_at) "
                        "VALUES (:version, :name, '', 'now')"
                    ),
                    {"version": version, "name": f"migration-{version}"},
                )

        result = apply_schema_migrations(self.engine)
        inspector = inspect(self.engine)

        self.assertEqual(result["fromVersion"], 10)
        self.assertEqual(result["toVersion"], CURRENT_SCHEMA_VERSION)
        self.assertIn("graph_feedback", inspector.get_table_names())
        self.assertTrue(
            {
                "artifact_kind",
                "artifact_key",
                "context_key",
                "action",
                "active",
            }.issubset(
                {column["name"] for column in inspector.get_columns("graph_feedback")}
            )
        )

    def test_newer_database_is_blocked_before_startup(self) -> None:
        apply_schema_migrations(self.engine)
        with self.engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO schema_migrations "
                    "(version, name, description, applied_at) "
                    "VALUES (:version, 'future', '', 'now')"
                ),
                {"version": CURRENT_SCHEMA_VERSION + 1},
            )

        with self.assertRaises(IncompatibleSchemaError):
            assert_schema_compatible(self.engine)
        self.assertEqual(get_schema_version(self.engine), CURRENT_SCHEMA_VERSION + 1)


if __name__ == "__main__":
    unittest.main()
