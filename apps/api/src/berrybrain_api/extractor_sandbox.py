from __future__ import annotations

import ctypes
import os
import resource
from collections.abc import Callable
from pathlib import Path
from typing import Any

PR_SET_NO_NEW_PRIVS = 38
DEFAULT_MEMORY_LIMIT_BYTES = 2 * 1024 * 1024 * 1024
DEFAULT_FILE_LIMIT_BYTES = 256 * 1024 * 1024


def sandboxed_subprocess_kwargs(
    executable: str,
    work_dir: str | Path,
    timeout_seconds: int,
) -> dict[str, Any]:
    resolved_work_dir = Path(work_dir).resolve()
    executable_dir = str(Path(executable).resolve().parent)
    return {
        "capture_output": True,
        "text": True,
        "timeout": timeout_seconds,
        "check": False,
        "cwd": str(resolved_work_dir),
        "env": {
            "HOME": str(resolved_work_dir),
            "LANG": "C.UTF-8",
            "LC_ALL": "C.UTF-8",
            "PATH": f"{executable_dir}:/usr/local/bin:/usr/bin:/bin",
            "HF_HUB_OFFLINE": "1",
            "TOKENIZERS_PARALLELISM": "false",
        },
        "close_fds": True,
        "start_new_session": True,
        "preexec_fn": _sandbox_preexec(timeout_seconds),
    }


def _sandbox_preexec(timeout_seconds: int) -> Callable[[], None]:
    cpu_limit = max(10, timeout_seconds + 5)

    def apply_limits() -> None:
        _set_no_new_privileges()
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
        resource.setrlimit(resource.RLIMIT_CPU, (cpu_limit, cpu_limit))
        resource.setrlimit(
            resource.RLIMIT_AS,
            (DEFAULT_MEMORY_LIMIT_BYTES, DEFAULT_MEMORY_LIMIT_BYTES),
        )
        resource.setrlimit(
            resource.RLIMIT_FSIZE,
            (DEFAULT_FILE_LIMIT_BYTES, DEFAULT_FILE_LIMIT_BYTES),
        )
        resource.setrlimit(resource.RLIMIT_NOFILE, (64, 64))
        if hasattr(resource, "RLIMIT_NPROC"):
            resource.setrlimit(resource.RLIMIT_NPROC, (32, 32))

    return apply_limits


def _set_no_new_privileges() -> None:
    libc = ctypes.CDLL(None, use_errno=True)
    if libc.prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) != 0:
        errno = ctypes.get_errno()
        raise OSError(errno, os.strerror(errno))
