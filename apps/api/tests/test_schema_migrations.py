import unittest

from sqlalchemy import create_engine, inspect, text

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
