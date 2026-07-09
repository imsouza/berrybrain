import tempfile
import unittest
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from berrybrain_api.database import Base
from berrybrain_api.vault_watcher import VaultWatcher


class VaultWatcherTest(unittest.TestCase):
    def test_run_once_scans_vault_with_session_factory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            vault_path = Path(temp_dir) / "vault"
            note_path = vault_path / "inbox" / "watcher.md"
            note_path.parent.mkdir(parents=True)
            note_path.write_text("# Watcher\n", encoding="utf-8")

            engine = create_engine(
                "sqlite:///:memory:", connect_args={"check_same_thread": False}
            )
            Base.metadata.create_all(bind=engine)
            session_factory = sessionmaker(bind=engine)
            watcher = VaultWatcher(
                vault_path=vault_path,
                session_factory=session_factory,
                interval_seconds=30,
            )

            first = watcher.run_once()
            second = watcher.run_once()

            self.assertEqual(first["created"], 1)
            self.assertEqual(first["jobs_created"], 14)
            self.assertEqual(second["unchanged"], 1)
            self.assertEqual(second["jobs_created"], 0)


if __name__ == "__main__":
    unittest.main()
