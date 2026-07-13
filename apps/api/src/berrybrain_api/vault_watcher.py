from __future__ import annotations

from pathlib import Path
from threading import Event, Thread
from typing import Callable

from sqlalchemy.orm import Session

from berrybrain_api.vault_scan import scan_vault

SessionFactory = Callable[[], Session]


class VaultWatcher:
    def __init__(
        self,
        vault_path: Path,
        session_factory: SessionFactory,
        interval_seconds: int,
    ) -> None:
        self.vault_path = vault_path
        self.session_factory = session_factory
        self.interval_seconds = max(1, interval_seconds)
        self._stop_event = Event()
        self._thread: Thread | None = None

    def run_once(self) -> dict[str, int]:
        with self.session_factory() as session:
            return scan_vault(session, self.vault_path)

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return

        self._stop_event.clear()
        self._thread = Thread(
            target=self._run_loop, name="berrybrain-vault-watcher", daemon=True
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)

    def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                self.run_once()
            except Exception as exc:
                print(f"BerryBrain vault watcher error: {exc}")

            self._stop_event.wait(self.interval_seconds)
