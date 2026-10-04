"""Retry committed cleanup intents even when the vault watcher is disabled."""

import logging
import threading
from pathlib import Path


class CleanupWorker:
    def __init__(self, session_factory, vault_path: Path) -> None:
        self.session_factory = session_factory
        self.vault_path = vault_path
        self.stop_event = threading.Event()
        self.thread = threading.Thread(
            target=self.run, name="berrybrain-cleanup", daemon=True
        )

    def start(self) -> None:
        self.thread.start()

    def stop(self) -> None:
        self.stop_event.set()
        self.thread.join(timeout=5)

    def run(self) -> None:
        from berrybrain_api.attachment_cleanup import drain_attachment_cleanup
        from berrybrain_api.vector_cleanup import drain_vector_cleanup

        while not self.stop_event.wait(30):
            try:
                with self.session_factory() as session:
                    drain_attachment_cleanup(session, self.vault_path)
                    drain_vector_cleanup(session)
            except Exception:
                logging.warning(
                    "Cleanup retry deferred; committed intents remain queued"
                )
