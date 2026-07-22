import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

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

    def test_start_is_idempotent_and_stop_joins_background_thread(self) -> None:
        session_factory = MagicMock()
        watcher = VaultWatcher(Path("/tmp/vault"), session_factory, 0)
        self.assertEqual(watcher.interval_seconds, 1)
        thread = MagicMock()
        thread.is_alive.return_value = True
        with patch(
            "berrybrain_api.vault_watcher.Thread", return_value=thread
        ) as factory:
            watcher.start()
            watcher.start()
            watcher.stop()

        factory.assert_called_once()
        thread.start.assert_called_once_with()
        thread.join.assert_called_once_with(timeout=5)
        self.assertTrue(watcher._stop_event.is_set())

    def test_loop_reports_scan_error_then_waits(self) -> None:
        watcher = VaultWatcher(Path("/tmp/vault"), MagicMock(), 3)
        watcher._stop_event = MagicMock()
        watcher._stop_event.is_set.side_effect = [False, True]
        with (
            patch.object(watcher, "run_once", side_effect=RuntimeError("scan failed")),
            patch("builtins.print") as output,
        ):
            watcher._run_loop()

        output.assert_called_once_with("BerryBrain vault watcher error: scan failed")
        watcher._stop_event.wait.assert_called_once_with(3)


if __name__ == "__main__":
    unittest.main()
