import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from berrybrain_api.extractor_sandbox import (
    DEFAULT_FILE_LIMIT_BYTES,
    DEFAULT_MEMORY_LIMIT_BYTES,
    _sandbox_preexec,
    _set_no_new_privileges,
    sandboxed_subprocess_kwargs,
)


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

    @patch("berrybrain_api.extractor_sandbox._set_no_new_privileges")
    @patch("berrybrain_api.extractor_sandbox.resource.setrlimit")
    def test_preexec_applies_cpu_memory_file_and_process_limits(
        self, setrlimit: MagicMock, no_new_privileges: MagicMock
    ) -> None:
        _sandbox_preexec(2)()

        no_new_privileges.assert_called_once_with()
        calls = {call.args[0]: call.args[1] for call in setrlimit.call_args_list}
        import resource

        self.assertEqual(calls[resource.RLIMIT_CORE], (0, 0))
        self.assertEqual(calls[resource.RLIMIT_CPU], (10, 10))
        self.assertEqual(
            calls[resource.RLIMIT_AS],
            (DEFAULT_MEMORY_LIMIT_BYTES, DEFAULT_MEMORY_LIMIT_BYTES),
        )
        self.assertEqual(
            calls[resource.RLIMIT_FSIZE],
            (DEFAULT_FILE_LIMIT_BYTES, DEFAULT_FILE_LIMIT_BYTES),
        )
        self.assertEqual(calls[resource.RLIMIT_NOFILE], (64, 64))
        if hasattr(resource, "RLIMIT_NPROC"):
            self.assertEqual(calls[resource.RLIMIT_NPROC], (32, 32))

    @patch("berrybrain_api.extractor_sandbox.ctypes.CDLL")
    def test_no_new_privileges_success_and_kernel_error(self, cdll: MagicMock) -> None:
        libc = cdll.return_value
        libc.prctl.return_value = 0
        _set_no_new_privileges()
        libc.prctl.assert_called_once()

        libc.prctl.return_value = -1
        with patch("berrybrain_api.extractor_sandbox.ctypes.get_errno", return_value=1):
            with self.assertRaises(PermissionError):
                _set_no_new_privileges()


if __name__ == "__main__":
    unittest.main()
