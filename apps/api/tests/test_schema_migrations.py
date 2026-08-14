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
        self.assertEqual(result["toVersion"], 12)
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
