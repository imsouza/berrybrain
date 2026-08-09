import sqlite3
import tempfile
import unittest
from pathlib import Path

from sqlalchemy import create_engine, event

from berrybrain_api.database import (
    _configure_sqlite_connection,
    _configure_sqlite_journal,
)


class DatabaseRuntimeTest(unittest.TestCase):
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
