from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from berrybrain_api.jobs import (
    EXPAND_KNOWLEDGE_GRAPH,
    FIND_CONNECTIONS,
    PARSE_NOTE,
    UPDATE_GRAPH_STATS,
    affected_job_types_for_note_update,
    enqueue_note_changed_jobs,
)
from berrybrain_api.models import NoteRecord
from berrybrain_api.sync import remove_note_record, sync_note_record
from berrybrain_api.vault import content_hash, ensure_vault


def scan_vault(session: Session, vault_path: Path) -> dict[str, int]:
    ensure_vault(vault_path)

    result = {
        "created": 0,
        "moved": 0,
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
            move_candidates = [
                candidate
                for old_path, candidate in existing_records.items()
                if old_path not in seen_paths
                and not Path(vault_path, old_path).exists()
                and candidate.content_hash == current_hash
            ]
            if len(move_candidates) == 1:
                moved = move_candidates[0]
                old_path = moved.path
                moved.path = relative_path
                moved.slug = path.stem
                session.flush()
                record = sync_note_record(session, vault_path, relative_path)
                jobs = enqueue_note_changed_jobs(
                    session,
                    record.path,
                    "NOTE_MOVED",
                    record.content_hash,
                    affected_job_types={
                        PARSE_NOTE,
                        FIND_CONNECTIONS,
                        EXPAND_KNOWLEDGE_GRAPH,
                        UPDATE_GRAPH_STATS,
                    },
                )
                seen_paths.add(old_path)
                result["moved"] += 1
                result["jobs_created"] += len(jobs)
                continue
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
            previous_content = existing.content
            record = sync_note_record(session, vault_path, relative_path)
            affected_job_types = affected_job_types_for_note_update(
                previous_content, path.read_text(encoding="utf-8"), record.path
            )
            jobs = enqueue_note_changed_jobs(
                session,
                record.path,
                "NOTE_UPDATED",
                record.content_hash,
                affected_job_types=affected_job_types,
            )
            result["updated"] += 1
            result["jobs_created"] += len(jobs)
            continue

        result["unchanged"] += 1

    for note_path in sorted(set(existing_records) - seen_paths):
        jobs_created = remove_note_record(session, note_path)
        result["deleted"] += 1
        result["jobs_created"] += jobs_created

    return result


def _relative_note_path(path: Path, vault_path: Path) -> str:
    try:
        return path.resolve().relative_to(vault_path.resolve()).as_posix()
    except ValueError:
        relative = os.path.relpath(os.path.normpath(path), os.path.normpath(vault_path))
        return Path(relative).as_posix()
