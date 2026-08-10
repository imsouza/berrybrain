import sqlite3
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import sessionmaker

from berrybrain_api import database
from berrybrain_api.database import (
    _configure_sqlite_connection,
    _configure_sqlite_journal,
)
from berrybrain_api.models import ProfileRecord, UserRecord


class DatabaseRuntimeTest(unittest.TestCase):
    def test_database_initialization_is_idempotent(self) -> None:
        engine = create_engine(
            "sqlite:///:memory:", connect_args={"check_same_thread": False}
        )
        event.listen(engine, "connect", _configure_sqlite_connection)
        sessions = sessionmaker(bind=engine, autoflush=False, autocommit=False)

        with (
            patch.object(database, "engine", engine),
            patch.object(database, "SessionLocal", sessions),
            patch.object(
                database,
                "get_settings",
                return_value=SimpleNamespace(enable_default_owner=False),
            ),
        ):
            database.init_database()
            database.init_database()

        with sessions() as session:
            profiles = session.scalars(select(ProfileRecord)).all()
        self.assertEqual([profile.slug for profile in profiles], ["default"])
        engine.dispose()

    def test_parent_setup_skips_non_file_databases(self) -> None:
        database._ensure_sqlite_parent("postgresql://localhost/berrybrain")
        database._ensure_sqlite_parent("sqlite:///:memory:")

    def test_default_owner_guards_unsafe_configuration(self) -> None:
        production = SimpleNamespace(
            enable_default_owner=True,
            environment="production",
        )
        missing_password = SimpleNamespace(
            enable_default_owner=True,
            environment="test",
            default_owner_password="",
        )
        with (
            patch.object(database, "get_settings", return_value=production),
            self.assertRaisesRegex(RuntimeError, "forbidden"),
        ):
            database.ensure_default_owner()
        with (
            patch.object(database, "get_settings", return_value=missing_password),
            self.assertRaisesRegex(RuntimeError, "DEFAULT_OWNER_PASSWORD"),
        ):
            database.ensure_default_owner()

    def test_default_owner_creation_is_idempotent(self) -> None:
        engine = create_engine("sqlite:///:memory:")
        database.Base.metadata.create_all(engine)
        sessions = sessionmaker(bind=engine, autoflush=False, autocommit=False)
        settings = SimpleNamespace(
            enable_default_owner=True,
            environment="test",
            default_owner_password="StrongPass123!",
            admin_email="owner@example.com",
            session_secret="release-test-secret-with-32-bytes",
            default_owner_force_password_reset=False,
        )

        with (
            patch.object(database, "SessionLocal", sessions),
            patch.object(database, "get_settings", return_value=settings),
        ):
            database.ensure_default_owner()
            database.ensure_default_owner()

        with sessions() as session:
            owners = session.scalars(select(UserRecord)).all()
        self.assertEqual([owner.email for owner in owners], ["owner@example.com"])
        engine.dispose()

    def test_non_sqlite_engine_skips_journal_configuration(self) -> None:
        engine = Mock()
        engine.dialect.name = "postgresql"

        _configure_sqlite_journal(engine)

        engine.connect.assert_not_called()

    def test_default_sqlite_engine_accepts_journal_configuration(self) -> None:
        engine = create_engine("sqlite:///:memory:")
        with patch("berrybrain_api.database.engine", engine):
            _configure_sqlite_journal()
        engine.dispose()

    def test_sqlite_uses_wal_and_waits_for_short_write_contention(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            database_path = Path(root) / "runtime.db"
            engine = create_engine(
                f"sqlite:///{database_path}",
                connect_args={"check_same_thread": False, "timeout": 30},
            )
            event.listen(engine, "connect", _configure_sqlite_connection)

            _configure_sqlite_journal(engine)

            with engine.connect() as connection:
                journal_mode = connection.exec_driver_sql(
                    "PRAGMA journal_mode"
                ).scalar_one()
                busy_timeout = connection.exec_driver_sql(
                    "PRAGMA busy_timeout"
                ).scalar_one()
                foreign_keys = connection.exec_driver_sql(
                    "PRAGMA foreign_keys"
                ).scalar_one()

            self.assertEqual(journal_mode, "wal")
            self.assertEqual(busy_timeout, 30_000)
            self.assertEqual(foreign_keys, 1)
            engine.dispose()

    def test_connection_configuration_supports_raw_sqlite(self) -> None:
        connection = sqlite3.connect(":memory:")
        try:
            _configure_sqlite_connection(connection)
            self.assertEqual(
                connection.execute("PRAGMA busy_timeout").fetchone()[0], 30_000
            )
            self.assertEqual(connection.execute("PRAGMA foreign_keys").fetchone()[0], 1)
        finally:
            connection.close()


if __name__ == "__main__":
    unittest.main()
