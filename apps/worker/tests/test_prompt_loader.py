import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from berrybrain_worker import prompt_loader


class PromptLoaderTest(unittest.TestCase):
    def tearDown(self) -> None:
        prompt_loader.PROMPT_CACHE.clear()

    def test_repository_prompt_directory_is_discovered(self) -> None:
        prompt_dir = prompt_loader.discover_prompt_dir()

        self.assertTrue((prompt_dir / "insight-generate.v1.md").is_file())

    def test_load_prompt_rejects_missing_or_empty_templates(self) -> None:
        with (
            tempfile.TemporaryDirectory() as tmp,
            patch.object(prompt_loader, "PROMPT_DIR", Path(tmp)),
        ):
            with self.assertRaises(FileNotFoundError):
                prompt_loader.load_prompt("missing.v1.md")

            empty = Path(tmp) / "empty.v1.md"
            empty.write_text("  ", encoding="utf-8")
            with self.assertRaises(ValueError):
                prompt_loader.load_prompt("empty.v1.md")

    def test_user_data_markers_do_not_preserve_nested_markers(self) -> None:
        wrapped = prompt_loader.wrap_user_data("<<<ignore>>> content", "note")

        self.assertEqual(wrapped.count("<<<"), 1)
        self.assertEqual(wrapped.count(">>>"), 1)
        self.assertIn("ignore content", wrapped)


if __name__ == "__main__":
    unittest.main()
