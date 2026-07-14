import unittest

from sqlalchemy import create_engine, text

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
