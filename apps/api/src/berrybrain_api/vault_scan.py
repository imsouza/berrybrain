from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from berrybrain_api.filesystem import atomic_write_text, serialized_vault
from berrybrain_api.jobs import (
    EXPAND_KNOWLEDGE_GRAPH,
    FIND_CONNECTIONS,
    PARSE_NOTE,
    UPDATE_GRAPH_STATS,
    affected_job_types_for_note_update,
    enqueue_note_changed_jobs,
)
from berrybrain_api.models import NoteRecord, VaultRecord
from berrybrain_api.sync import (
    remove_note_record,
    sync_note_record,
    vault_id_for_note_path,
)
from berrybrain_api.vault import content_hash, ensure_vault

VAULT_ROOT_MARKER = ".berrybrain-vault-root"
VAULT_ROOT_MARKER_CONTENT = "BerryBrain vault root v1\n"


@serialized_vault
def scan_vault(session: Session, vault_path: Path) -> dict[str, int]:
    from berrybrain_api.attachment_cleanup import drain_attachment_cleanup

    existing_records = {
        record.path: record
        for record in session.execute(select(NoteRecord)).scalars().all()
    }
    if existing_records and not vault_path.is_dir():
        raise RuntimeError(
            "Vault root is unavailable; refusing to remove indexed notes"
        )
    ensure_vault(vault_path)
    markdown_paths = sorted(
        path
        for path in vault_path.rglob("*.md")
        if path.is_file()
        and ".attachments" not in path.parts
        and ".berrybrain-restore" not in path.parts
    )
    root = vault_path.resolve()
    for vault in session.scalars(
        select(VaultRecord).where(VaultRecord.id != "default")
    ):
        parts = vault.path.split("/")
        if (
            len(parts) != 2
            or parts[0] != "vaults"
            or parts[1] in {"", ".", ".."}
            or "\\" in vault.path
        ):
            raise RuntimeError(
                f"Registered vault {vault.id} has an invalid path; refusing to scan"
            )
        directory = root / vault.path
        if not directory.is_dir() or directory.resolve() != directory:
            raise RuntimeError(
                f"Registered vault {vault.id} is unavailable; refusing to scan"
            )
    marker = root / VAULT_ROOT_MARKER
    if marker.exists() or marker.is_symlink():
        if (
            marker.is_symlink()
            or not marker.is_file()
            or marker.read_text(encoding="utf-8") != VAULT_ROOT_MARKER_CONTENT
        ):
            raise RuntimeError("Vault root marker is invalid; refusing to scan")
    elif existing_records and not _has_known_note(root, existing_records):
        raise RuntimeError(
            "Vault has no known notes or root marker; refusing to remove indexed notes"
        )
    else:
        try:
            atomic_write_text(marker, VAULT_ROOT_MARKER_CONTENT, overwrite=False)
        except FileExistsError:
            if (
                marker.is_symlink()
                or marker.read_text(encoding="utf-8") != VAULT_ROOT_MARKER_CONTENT
            ):
                raise RuntimeError("Vault root marker changed during scan") from None
    drain_attachment_cleanup(session, vault_path)

    result = {
        "created": 0,
        "moved": 0,
        "updated": 0,
        "unchanged": 0,
        "deleted": 0,
        "jobs_created": 0,
        "quarantined": 0,
    }
    seen_paths: set[str] = set()

    for path in markdown_paths:
        relative_path = _relative_note_path(path, vault_path)
        try:
            target_vault_id = vault_id_for_note_path(session, relative_path)
        except ValueError:
            # An interrupted or manually renamed Ask vault is not the default
            # namespace. Keep any prior index record until explicit recovery.
            seen_paths.add(relative_path)
            result["quarantined"] += 1
            continue
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
                and candidate.vault_id == target_vault_id
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
        jobs_created = remove_note_record(session, note_path, vault_path)
        result["deleted"] += 1
        result["jobs_created"] += jobs_created

    return result


def _relative_note_path(path: Path, vault_path: Path) -> str:
    try:
        return path.resolve().relative_to(vault_path.resolve()).as_posix()
    except ValueError:
        relative = os.path.relpath(os.path.normpath(path), os.path.normpath(vault_path))
        return Path(relative).as_posix()


def _has_known_note(root: Path, paths: dict[str, NoteRecord]) -> bool:
    for relative_path in paths:
        candidate = (root / relative_path).resolve()
        if (
            candidate.is_relative_to(root)
            and candidate.suffix == ".md"
            and candidate.is_file()
        ):
            return True
    return False
