from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import select

from berrybrain_api.config import get_settings
from berrybrain_api.database import SessionLocal
from berrybrain_api.filesystem import serialized_vault
from berrybrain_api.jobs import PENDING, RUNNING, SUPERSEDED, enqueue_note_changed_jobs
from berrybrain_api.models import JobRecord, NoteAttachmentRecord, NoteRecord
from berrybrain_api.sync import sync_note_record

router = APIRouter(prefix="/api/v1/folders", tags=["folders"])


class CreateFolderRequest(BaseModel):
    name: str
    parent_path: str = ""


def _safe_relative_path(path: str) -> Path:
    candidate = Path(path.strip("/"))
    if candidate.is_absolute() or ".." in candidate.parts:
        raise HTTPException(status_code=400, detail="Invalid folder path")
    return candidate


def _resolve_folder(vault_path: Path, folder_path: str) -> Path:
    relative = _safe_relative_path(folder_path)
    full_path = (vault_path / relative).resolve()
    vault_root = vault_path.resolve()
    if vault_root not in full_path.parents and full_path != vault_root:
        raise HTTPException(status_code=400, detail="Invalid folder path")
    return full_path


def _folder_payload(vault_path: Path, item: Path) -> dict:
    md_files = list(item.glob("*.md"))
    children = [
        child
        for child in item.iterdir()
        if child.is_dir() and not child.name.startswith(".")
    ]
    relative = str(item.relative_to(vault_path))
    return {
        "name": item.name,
        "path": relative,
        "parent_path": str(item.parent.relative_to(vault_path))
        if item.parent != vault_path
        else "",
        "depth": 0 if relative == "." else len(Path(relative).parts) - 1,
        "note_count": len(md_files),
        "total_note_count": len(list(item.rglob("*.md"))),
        "has_subfolders": bool(children),
    }


def _list_folders(vault_path: Path) -> list[dict]:
    folders: list[dict] = []
    for item in sorted(vault_path.rglob("*")):
        if item.is_dir() and not item.name.startswith("."):
            folders.append(_folder_payload(vault_path, item))
    return folders


@router.get("")
def list_folders() -> dict:
    settings = get_settings()
    return {"folders": _list_folders(settings.vault_path)}


@router.post("", status_code=201)
@serialized_vault
def create_folder(payload: CreateFolderRequest) -> dict:
    settings = get_settings()
    vault_path = settings.vault_path
    parent = (
        _resolve_folder(vault_path, payload.parent_path)
        if payload.parent_path
        else vault_path
    )
    if not parent.exists() or not parent.is_dir():
        raise HTTPException(status_code=404, detail="Parent folder not found")
    folder_name = payload.name.strip().strip("/")
    if (
        not folder_name
        or "/" in folder_name
        or "\\" in folder_name
        or folder_name in {".", ".."}
    ):
        raise HTTPException(status_code=400, detail="Invalid folder name")
    folder_path = parent / folder_name

    if folder_path.exists():
        raise HTTPException(status_code=400, detail="Folder already exists")

    folder_path.mkdir(parents=True)
    return _folder_payload(vault_path, folder_path)


@router.put("/{folder_path:path}")
@serialized_vault
def rename_folder(folder_path: str, payload: dict) -> dict:
    settings = get_settings()
    full_path = _resolve_folder(settings.vault_path, folder_path)
    root = settings.vault_path.resolve()
    if full_path == root:
        raise HTTPException(status_code=400, detail="Cannot rename the vault root")

    if not full_path.exists() or not full_path.is_dir():
        raise HTTPException(status_code=404, detail="Folder not found")

    new_name = str(payload.get("name") or "").strip().strip("/")
    if not new_name or "/" in new_name or "\\" in new_name or new_name in {".", ".."}:
        raise HTTPException(status_code=400, detail="New name required")

    new_path = (full_path.parent / new_name).resolve()
    if root not in new_path.parents:
        raise HTTPException(status_code=400, detail="Invalid target folder")
    if new_path.exists():
        raise HTTPException(
            status_code=400, detail="Folder with new name already exists"
        )

    old_prefix = full_path.relative_to(root).as_posix() + "/"
    new_prefix = new_path.relative_to(root).as_posix() + "/"
    with SessionLocal() as session:
        records = [
            row
            for row in session.scalars(select(NoteRecord))
            if row.path.startswith(old_prefix)
        ]
        moves = {row.path: new_prefix + row.path[len(old_prefix) :] for row in records}
        moved_ids = {row.id for row in records}
        full_path.rename(new_path)
        try:
            for row in records:
                row.path = moves[row.path]
            for attachment in session.scalars(
                select(NoteAttachmentRecord).where(
                    NoteAttachmentRecord.note_id.in_(moved_ids)
                )
            ):
                if attachment.note_path in moves:
                    attachment.note_path = moves[attachment.note_path]
            for job in session.scalars(
                select(JobRecord).where(
                    JobRecord.note_id.in_(moved_ids),
                    JobRecord.status.in_([PENDING, RUNNING]),
                )
            ):
                job.status = SUPERSEDED
                job.error_message = "Superseded by folder rename"
                job.claim_token = ""
                job.claimed_by = ""
                job.lease_expires_at = None
            # Commit the entire identity mapping before a scan can observe it.
            session.commit()
        except Exception:
            session.rollback()
            new_path.rename(full_path)
            raise
        from berrybrain_api.routers.notes import _update_internal_links

        for old_note_path, new_note_path in moves.items():
            record = sync_note_record(session, root, new_note_path)
            enqueue_note_changed_jobs(
                session, record.path, "NOTE_MOVED", record.content_hash
            )
            _update_internal_links(session, old_note_path, new_note_path)
    return {"name": new_name, "path": new_path.relative_to(root).as_posix()}


@router.delete("/{folder_path:path}")
@serialized_vault
def delete_folder(folder_path: str) -> dict:
    settings = get_settings()
    full_path = _resolve_folder(settings.vault_path, folder_path)
    if full_path == settings.vault_path.resolve():
        raise HTTPException(status_code=400, detail="Cannot delete the vault root")

    if not full_path.exists() or not full_path.is_dir():
        raise HTTPException(status_code=404, detail="Folder not found")

    if any(f.is_file() for f in full_path.rglob("*")):
        raise HTTPException(status_code=400, detail="Cannot delete folder with notes")

    full_path.rmdir()
    return {"message": f"Folder {folder_path} deleted"}
