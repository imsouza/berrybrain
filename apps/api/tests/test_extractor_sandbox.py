import tempfile
import unittest
from pathlib import Path

from berrybrain_api.extractor_sandbox import sandboxed_subprocess_kwargs


class ExtractorSandboxTest(unittest.TestCase):
    def test_subprocess_policy_is_bounded_and_uses_minimal_environment(self) -> None:
        with tempfile.TemporaryDirectory() as work_dir:
            kwargs = sandboxed_subprocess_kwargs(
                "/usr/bin/tesseract",
                work_dir,
                30,
            )

        self.assertEqual(kwargs["cwd"], str(Path(work_dir).resolve()))
        self.assertEqual(kwargs["timeout"], 30)
        self.assertTrue(kwargs["close_fds"])
        self.assertTrue(kwargs["start_new_session"])
        self.assertFalse(kwargs["check"])
        self.assertNotIn("PYTHONPATH", kwargs["env"])
        self.assertNotIn("BERRYBRAIN_API_TOKEN", kwargs["env"])
        self.assertEqual(kwargs["env"]["HOME"], str(Path(work_dir).resolve()))
        self.assertTrue(callable(kwargs["preexec_fn"]))


if __name__ == "__main__":
    unittest.main()
