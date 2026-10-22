"""Safety regressions for the one-off pre-deployment backup wrapper."""

import importlib.util
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from sqlalchemy import create_engine

from berrybrain_api.database import Base
from berrybrain_api.schema_migrations import apply_schema_migrations


def _preflight_module():
    script = (
        Path(__file__).resolve().parents[3]
        / "scripts/maintenance/backup-active-preflight.py"
    )
    spec = importlib.util.spec_from_file_location("backup_active_preflight", script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ActiveBackupPreflightTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.database = self.root / "sqlite" / "berrybrain.db"
        self.database.parent.mkdir()
        self.vault = self.root / "vault"
        self.vault.mkdir()
        (self.vault / "note.md").write_text("# Note\n", encoding="utf-8")
        self.backups = self.root / "backups"
        self.backups.mkdir()
        self.settings = SimpleNamespace(
            database_url=f"sqlite:///{self.database}",
            vault_path=self.vault,
            backup_path=self.backups,
        )
        engine = create_engine(f"sqlite:///{self.database}")
        Base.metadata.create_all(engine)
        apply_schema_migrations(engine)
        engine.dispose()
        self.preflight = _preflight_module()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _configured(self):
        return (
            patch("berrybrain_api.backup.get_settings", return_value=self.settings),
            patch("berrybrain_api.config.get_settings", return_value=self.settings),
        )

    def test_publishes_only_verified_complete_backup(self) -> None:
        backup_settings, vault_settings = self._configured()
        with backup_settings, vault_settings:
            result = self.preflight.create_preflight_backup(
                self.database, self.vault, self.backups
            )

        published = self.backups / result["id"]
        self.assertTrue(published.is_dir())
        self.assertTrue((published / "manifest.json").is_file())
        self.assertTrue((published / "berrybrain.db").is_file())
        self.assertEqual((published / "vault" / "note.md").read_text(), "# Note\n")
        self.assertEqual(result["notes"], 0)
        self.assertEqual(result["verifiedFiles"] > 0, True)
        self.assertEqual(list(self.backups.glob(".*.incomplete")), [])

    def test_failed_partial_snapshot_is_not_published(self) -> None:
        def fail_after_partial_write(_source, destination, **_kwargs):
            destination.write_bytes(b"partial")
            raise TimeoutError("simulated interrupted backup")

        backup_settings, vault_settings = self._configured()
        with (
            backup_settings,
            vault_settings,
            patch.object(
                self.preflight,
                "_snapshot_one_pass",
                side_effect=fail_after_partial_write,
            ),
            self.assertRaisesRegex(TimeoutError, "simulated interrupted backup"),
        ):
            self.preflight.create_preflight_backup(
                self.database, self.vault, self.backups
            )

        self.assertEqual(list(self.backups.iterdir()), [])

    def test_wrong_configured_path_is_rejected_before_writing(self) -> None:
        backup_settings, vault_settings = self._configured()
        with (
            backup_settings,
            vault_settings,
            self.assertRaisesRegex(ValueError, "differs from preflight"),
        ):
            self.preflight.create_preflight_backup(
                self.database, self.vault, self.root / "wrong-backups"
            )
        self.assertEqual(list(self.backups.iterdir()), [])
