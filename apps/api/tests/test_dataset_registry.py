import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from benchmarks.dataset_registry import verify_dataset


class DatasetRegistryTest(unittest.TestCase):
    def test_verifies_installed_file_checksum(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data = root / "corpus.jsonl"
            data.write_text('{"id":"1","text":"evidence"}\n', encoding="utf-8")
            checksum = hashlib.sha256(data.read_bytes()).hexdigest()
            manifest = root / "manifest.json"
            manifest.write_text(
                json.dumps(
                    {
                        "schemaVersion": "berrybrain-dataset.v1",
                        "id": "test",
                        "source": "local test",
                        "license": "test-only",
                        "version": "1",
                        "files": [{"path": data.name, "sha256": checksum}],
                    }
                ),
                encoding="utf-8",
            )
            status = verify_dataset(manifest, root)
            self.assertTrue(status[0].installed)
            self.assertTrue(status[0].valid)

    def test_reports_missing_file_without_substitution(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = root / "manifest.json"
            manifest.write_text(
                json.dumps(
                    {
                        "schemaVersion": "berrybrain-dataset.v1",
                        "id": "missing",
                        "source": "upstream",
                        "license": "declared upstream",
                        "version": "1",
                        "files": [{"path": "missing.jsonl", "sha256": "abc"}],
                    }
                ),
                encoding="utf-8",
            )
            status = verify_dataset(manifest, root)
            self.assertFalse(status[0].installed)
            self.assertFalse(status[0].valid)


if __name__ == "__main__":
    unittest.main()
