"""Durable, narrowly scoped deletion of binaries whose DB owners were removed."""

import json
import logging
from pathlib import Path
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from berrybrain_api.filesystem import serialized_vault
from berrybrain_api.models import NoteAttachmentRecord, SettingRecord

PREFIX = "internal.attachment_cleanup."


def queue_attachment_cleanup(
    session: Session, attachments: list[NoteAttachmentRecord]
) -> None:
    if attachments:
        session.add(
            SettingRecord(
                key=PREFIX + uuid4().hex,
                value=json.dumps({"paths": [item.stored_path for item in attachments]}),
            )
        )


@serialized_vault
def drain_attachment_cleanup(session: Session, vault_path: Path) -> dict[str, int]:
    root = vault_path.resolve()
    attachment_root = (root / ".attachments").resolve()
    if root not in attachment_root.parents:
        raise ValueError("Attachment storage is outside the vault")
    pending = list(
        session.scalars(
            select(SettingRecord)
            .where(SettingRecord.key.startswith(PREFIX, autoescape=True))
            .limit(100)
        )
    )
    completed = 0
    for task in pending:
        try:
            paths = json.loads(task.value)["paths"]
            if not isinstance(paths, list) or not all(
                isinstance(value, str) for value in paths
            ):
                raise ValueError("Invalid attachment cleanup payload")
            for relative in paths:
                target = (root / relative).resolve()
                if attachment_root not in target.parents:
                    raise ValueError(
                        "Attachment cleanup target is outside attachment storage"
                    )
                # A restore/reassignment may make the binary owned again. Never
                # remove a file still referenced by current authoritative state.
                owner = session.scalar(
                    select(NoteAttachmentRecord.id)
                    .where(NoteAttachmentRecord.stored_path == relative)
                    .limit(1)
                )
                if owner is None:
                    target.unlink(missing_ok=True)
            session.delete(task)
            session.commit()
            completed += 1
        except (OSError, ValueError, KeyError, TypeError):
            session.rollback()
            logging.warning(
                "Attachment cleanup remains queued; filesystem cleanup was not completed"
            )
    return {"completed": completed, "pending": len(pending) - completed}
