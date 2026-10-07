"""Cooperative, cross-process vault transactions and crash-safe file writes.

Locks are outside the vault, so a restore can replace its contents without
replacing the inode on which other processes are waiting. External editors that
ignore advisory locks still require the normal version-conflict checks.
"""

from __future__ import annotations

import fcntl
import inspect
import os
import tempfile
import threading
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from functools import wraps
from pathlib import Path
from typing import ParamSpec, TypeVar

_registry_guard = threading.Lock()
_locks: dict[str, threading.RLock] = {}
_held = threading.local()
P = ParamSpec("P")
T = TypeVar("T")


@contextmanager
def vault_lock(vault_path: Path) -> Iterator[None]:
    root = vault_path.resolve()
    key = str(root)
    with _registry_guard:
        lock = _locks.setdefault(key, threading.RLock())
    with lock:
        held = getattr(_held, "roots", set())
        if key in held:
            yield
            return
        root.parent.mkdir(parents=True, exist_ok=True)
        lock_path = root.parent / f".{root.name}.berrybrain.lock"
        with lock_path.open("a+b") as handle:
            fcntl.flock(handle, fcntl.LOCK_EX)
            recovery_root = root / ".berrybrain-restore"
            if recovery_root.is_symlink() or (
                recovery_root.exists() and any(recovery_root.iterdir())
            ):
                from fastapi import HTTPException

                raise HTTPException(
                    503, "Interrupted restore requires recovery before vault access."
                )
            _held.roots = held | {key}
            try:
                yield
            finally:
                _held.roots = held
                fcntl.flock(handle, fcntl.LOCK_UN)


def serialized_vault(function: Callable[P, T]) -> Callable[P, T]:
    signature = inspect.signature(function, eval_str=True)

    @wraps(function)
    def guarded(*args: P.args, **kwargs: P.kwargs) -> T:
        vault_path = signature.bind(*args, **kwargs).arguments.get("vault_path")
        if vault_path is None:
            from berrybrain_api.config import get_settings

            vault_path = get_settings().vault_path
        with vault_lock(Path(vault_path)):
            return function(*args, **kwargs)

    # FastAPI must resolve postponed annotations in the original module, not in
    # this wrapper's globals.
    guarded.__signature__ = signature  # type: ignore[attr-defined]
    return guarded


def atomic_write_text(path: Path, content: str, *, overwrite: bool = True) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=".berrybrain-write-",
            delete=False,
        ) as stream:
            temporary = Path(stream.name)
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        if path.exists():
            os.chmod(temporary, path.stat().st_mode & 0o777)
        if overwrite:
            os.replace(temporary, path)
        else:
            # Unlike replace(), link() cannot overwrite a concurrently created file.
            os.link(temporary, path)
        descriptor = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
