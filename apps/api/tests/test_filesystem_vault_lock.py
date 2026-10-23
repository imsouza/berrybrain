"""The vault lock must live on a mount shared by API and worker containers."""

import fcntl
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from berrybrain_api.filesystem import _vault_lock_path, vault_lock


class VaultLockPlacementTest(unittest.TestCase):
    def test_configured_shared_directory_holds_the_actual_lock(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            vault = root / "workspace" / "vault"
            vault.mkdir(parents=True)
            shared = root / "shared-data" / "locks"
            with patch.dict(os.environ, {"BERRYBRAIN_VAULT_LOCK_DIR": str(shared)}):
                lock_path = _vault_lock_path(vault.resolve())
                self.assertEqual(lock_path.parent, shared.resolve())
                with vault_lock(vault):
                    self.assertTrue(lock_path.is_file())
                    with (
                        lock_path.open("a+b") as contender,
                        self.assertRaises(BlockingIOError),
                    ):
                        fcntl.flock(contender, fcntl.LOCK_EX | fcntl.LOCK_NB)
                with lock_path.open("a+b") as contender:
                    fcntl.flock(contender, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    fcntl.flock(contender, fcntl.LOCK_UN)
                self.assertFalse((vault.parent / ".vault.berrybrain.lock").exists())

    def test_default_keeps_existing_lock_location_for_non_container_installs(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            vault = Path(directory) / "vault"
            vault.mkdir()
            with (
                patch.dict(os.environ, {"BERRYBRAIN_VAULT_LOCK_DIR": ""}),
                vault_lock(vault),
            ):
                self.assertTrue((vault.parent / ".vault.berrybrain.lock").is_file())
