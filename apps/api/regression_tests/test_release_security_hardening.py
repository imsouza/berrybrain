import hashlib
import hmac
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import HTTPException

from berrybrain_api.routers import folders
from berrybrain_api.security import token_hash


class FolderBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.base = Path(self.directory.name)
        self.vault = self.base / "vault"
        self.vault.mkdir()
        self.outside = self.base / "vault-other"
        self.outside.mkdir()

    def test_nested_unicode_path_stays_inside_vault(self):
        self.assertEqual(
            folders._resolve_folder(self.vault, "Ciência/Notas"),
            self.vault / "Ciência" / "Notas",
        )

    def test_absolute_traversal_windows_and_nul_paths_are_rejected(self):
        for value in (
            "../vault-other",
            "notes/../../vault-other",
            str(self.outside),
            "C:/outside",
            r"C:\outside",
            r"notes\..\outside",
            "notes\x00invalid",
        ):
            with self.subTest(value=repr(value)):
                with self.assertRaises(HTTPException) as caught:
                    folders._resolve_folder(self.vault, value)
                self.assertEqual(caught.exception.status_code, 400)

    def test_symlink_to_sibling_prefix_is_rejected(self):
        (self.vault / "escape").symlink_to(self.outside, target_is_directory=True)
        with self.assertRaises(HTTPException) as caught:
            folders._resolve_folder(self.vault, "escape/new-folder")
        self.assertEqual(caught.exception.status_code, 400)
        self.assertEqual(list(self.outside.iterdir()), [])

    def test_symlinked_vault_root_remains_supported(self):
        alias = self.base / "vault-alias"
        alias.symlink_to(self.vault, target_is_directory=True)
        (self.vault / "parent").mkdir()
        settings = SimpleNamespace(vault_path=alias)
        with patch.object(folders, "get_settings", return_value=settings):
            result = folders.create_folder.__wrapped__(
                folders.CreateFolderRequest(name="child", parent_path="parent")
            )
        self.assertEqual(result["path"], "parent/child")
        self.assertTrue((self.vault / "parent" / "child").is_dir())

    def test_create_rejects_dangling_symlink_outside_vault(self):
        target = self.outside / "missing"
        (self.vault / "new-folder").symlink_to(target, target_is_directory=True)
        settings = SimpleNamespace(vault_path=self.vault)
        with (
            patch.object(folders, "get_settings", return_value=settings),
            self.assertRaises(HTTPException) as caught,
        ):
            folders.create_folder.__wrapped__(
                folders.CreateFolderRequest(name="new-folder")
            )
        self.assertEqual(caught.exception.status_code, 400)
        self.assertFalse(target.exists())


class TokenDigestCompatibilityTests(unittest.TestCase):
    def test_hmac_api_keeps_existing_token_hashes_valid(self):
        token = "opaque-integration-token"
        secret = "test-only-hmac-key"
        expected = hmac.new(secret.encode(), token.encode(), hashlib.sha256).hexdigest()
        self.assertEqual(token_hash(token, secret), expected)
        self.assertNotEqual(token_hash(token, secret), token_hash(token, secret + "2"))


if __name__ == "__main__":
    unittest.main()
