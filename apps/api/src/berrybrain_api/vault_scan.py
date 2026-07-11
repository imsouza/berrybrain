from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from berrybrain_api.jobs import enqueue_note_changed_jobs
from berrybrain_api.models import NoteRecord
from berrybrain_api.sync import remove_note_record, sync_note_record
from berrybrain_api.vault import content_hash, ensure_vault


def scan_vault(session: Session, vault_path: Path) -> dict[str, int]:
    ensure_vault(vault_path)

    result = {
        "created": 0,
        "updated": 0,
        "unchanged": 0,
        "deleted": 0,
        "jobs_created": 0,
    }
    existing_records = {
        record.path: record
        for record in session.execute(select(NoteRecord)).scalars().all()
    }
    seen_paths: set[str] = set()

    for path in sorted(vault_path.rglob("*.md")):
        if not path.is_file() or ".attachments" in path.parts:
            continue
        relative_path = _relative_note_path(path, vault_path)
        seen_paths.add(relative_path)
        current_hash = content_hash(path.read_text(encoding="utf-8"))
        existing = existing_records.get(relative_path)

        if existing is None:
            record = sync_note_record(session, vault_path, relative_path)
            jobs = enqueue_note_changed_jobs(
                session,
                record.path,
                "NOTE_CREATED",
                record.content_hash,
            )
            result["created"] += 1
            result["jobs_created"] += len(jobs)
            continue

        if existing.content_hash != current_hash:
            record = sync_note_record(session, vault_path, relative_path)
            jobs = enqueue_note_changed_jobs(
                session,
                record.path,
                "NOTE_UPDATED",
                record.content_hash,
            )
            result["updated"] += 1
            result["jobs_created"] += len(jobs)
            continue

        result["unchanged"] += 1

    for note_path in sorted(set(existing_records) - seen_paths):
        remove_note_record(session, note_path)
        jobs = enqueue_note_changed_jobs(session, note_path, "NOTE_DELETED", "")
        result["deleted"] += 1
        result["jobs_created"] += len(jobs)

    return result


def _relative_note_path(path: Path, vault_path: Path) -> str:
    try:
        return path.resolve().relative_to(vault_path.resolve()).as_posix()
    except ValueError:
        relative = os.path.relpath(os.path.normpath(path), os.path.normpath(vault_path))
        return Path(relative).as_posix()
