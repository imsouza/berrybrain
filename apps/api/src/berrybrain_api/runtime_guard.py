"""Cross-process maintenance barrier for SQLite connection lifetimes."""

from __future__ import annotations

import fcntl
import threading
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import BinaryIO

from fastapi import HTTPException
from sqlalchemy import event
from sqlalchemy.engine import Engine

_installation_lock = threading.Lock()
_exclusive = threading.local()


class MaintenanceUnavailable(HTTPException):
    def __init__(self) -> None:
        super().__init__(
            503,
            "Database maintenance in progress; retry after it completes.",
            headers={"Retry-After": "5"},
        )


def _lock_file(database_path: Path, suffix: str) -> BinaryIO:
    path = database_path.resolve()
    return (path.parent / f".{path.name}.{suffix}.lock").open("a+b")


def restore_marker(database_path: Path) -> Path:
    path = database_path.resolve()
    return path.parent / f".{path.name}.restore-pending.json"


def acquire_database_lease(database_path: Path) -> BinaryIO | None:
    if str(database_path.resolve()) in getattr(_exclusive, "paths", set()):
        return None
    with _lock_file(database_path, "maintenance") as intent:
        lease = None
        try:
            fcntl.flock(intent, fcntl.LOCK_SH | fcntl.LOCK_NB)
            if restore_marker(database_path).exists():
                raise MaintenanceUnavailable()
            lease = _lock_file(database_path, "connections")
            fcntl.flock(lease, fcntl.LOCK_SH | fcntl.LOCK_NB)
            return lease
        except BlockingIOError as exc:
            if lease is not None:
                lease.close()
            raise MaintenanceUnavailable() from exc


@contextmanager
def database_lease(database_path: Path) -> Iterator[None]:
    lease = acquire_database_lease(database_path)
    try:
        yield
    finally:
        if lease is not None:
            lease.close()


@contextmanager
def exclusive_database_access(
    database_path: Path, timeout: float = 30.0
) -> Iterator[None]:
    key = str(database_path.resolve())
    held = getattr(_exclusive, "paths", set())
    if key in held:
        yield
        return
    with (
        _lock_file(database_path, "maintenance") as intent,
        _lock_file(database_path, "connections") as connections,
    ):
        try:
            fcntl.flock(intent, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise MaintenanceUnavailable() from exc
        deadline = time.monotonic() + timeout
        while True:
            try:
                fcntl.flock(connections, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError as exc:
                if time.monotonic() >= deadline:
                    raise HTTPException(
                        409,
                        "Active database operations did not drain; restore made no changes.",
                    ) from exc
                time.sleep(0.05)
        _exclusive.paths = held | {key}
        try:
            yield
        finally:
            _exclusive.paths = held


def install_database_guard(engine: Engine) -> None:
    if (
        engine.dialect.name != "sqlite"
        or not engine.url.database
        or engine.url.database == ":memory:"
    ):
        return
    with _installation_lock:
        if getattr(engine, "_berrybrain_maintenance_guard", False):
            return
        path = Path(engine.url.database)

        def checkout(_connection, record, _proxy):
            record.info["berrybrain_database_lease"] = acquire_database_lease(path)

        def release(_connection, record, *_args):
            lease = record.info.pop("berrybrain_database_lease", None)
            if lease is not None:
                lease.close()

        event.listen(engine, "checkout", checkout)
        event.listen(engine, "checkin", release)
        event.listen(engine, "invalidate", release)
        engine._berrybrain_maintenance_guard = True  # type: ignore[attr-defined]
