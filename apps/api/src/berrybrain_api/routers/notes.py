import base64
import re
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import select

from berrybrain_api.attachment_processing import process_attachment, serialize_extraction
from berrybrain_api.config import get_settings
from berrybrain_api.database import SessionLocal
from berrybrain_api.jobs import PROCESS_ATTACHMENT, create_job, enqueue_note_changed_jobs
from berrybrain_api.models import (
    AttachmentExtractionRecord,
    NoteAttachmentRecord,
    NoteRecord,
    SettingRecord,
)
from berrybrain_api.sync import remove_note_record, sync_note_record
from berrybrain_api.vault import (
    create_note,
    delete_note,
    list_markdown_notes,
    read_note,
    rename_note,
    resolve_note_path,
    update_note,
)


class ClipRequest(BaseModel):
    url: str
    title: str
    content: str


router = APIRouter(prefix="/api/v1/notes", tags=["notes"])


class CreateNoteRequest(BaseModel):
    title: str | None = Field(default=None, max_length=160)
    folder: str = "inbox"
    content: str = ""


class UpdateNoteRequest(BaseModel):
    content: str


class RenameNoteRequest(BaseModel):
    title: str = Field(min_length=1, max_length=160)


class AttachmentUploadRequest(BaseModel):
    filename: str = Field(min_length=1, max_length=255)
    mime_type: str = ""
    size_bytes: int = Field(ge=0)
    content_base64: str = Field(min_length=1)


ATTACHMENT_DEFAULT_LIMITS_MB = {
    "image": 10,
    "video": 200,
    "audio": 50,
    "other": 25,
}


def _attachment_category(mime_type: str, filename: str) -> str:
    lowered = (mime_type or "").lower()
    if lowered.startswith("image/"):
        return "image"
    if lowered.startswith("video/"):
        return "video"
    if lowered.startswith("audio/"):
        return "audio"
    suffix = Path(filename).suffix.lower()
    if suffix in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp", ".tiff"}:
        return "image"
    if suffix in {".mp4", ".mov", ".mkv", ".webm", ".avi"}:
        return "video"
    if suffix in {".mp3", ".wav", ".ogg", ".m4a", ".flac"}:
        return "audio"
    return "other"


def _safe_filename(filename: str) -> str:
    name = Path(filename).name.strip() or "attachment"
    name = re.sub(r"[^A-Za-z0-9._ -]+", "-", name)
    return name[:180] or "attachment"


def _setting_int(session, key: str, default: int) -> int:
    value = session.execute(select(SettingRecord.value).where(SettingRecord.key == key)).scalar_one_or_none()
    try:
        parsed = int(str(value or default))
    except (TypeError, ValueError):
        parsed = default
    return max(1, parsed)


def _attachment_limit_mb(session, category: str) -> int:
    return _setting_int(
        session,
        f"attachment_{category}_limit_mb",
        ATTACHMENT_DEFAULT_LIMITS_MB.get(category, ATTACHMENT_DEFAULT_LIMITS_MB["other"]),
    )


def _serialize_attachment(
    record: NoteAttachmentRecord, extraction: AttachmentExtractionRecord | None = None
) -> dict:
    return {
        "id": record.id,
        "noteId": record.note_id,
        "notePath": record.note_path,
        "filename": record.filename,
        "mimeType": record.mime_type,
        "category": record.category,
        "sizeBytes": record.size_bytes,
        "downloadUrl": f"/api/v1/notes/attachments/{record.id}/download",
        "extraction": serialize_extraction(extraction),
        "createdAt": record.created_at.isoformat() if record.created_at else None,
    }


@router.get("")
def list_notes() -> dict:
    settings = get_settings()
    return {"notes": list_markdown_notes(settings.vault_path)}


@router.post("", status_code=201)
def create_note_endpoint(payload: CreateNoteRequest) -> dict:
    settings = get_settings()
    note = create_note(
        settings.vault_path, payload.title or "", payload.folder, payload.content
    )
    with SessionLocal() as session:
        record = sync_note_record(session, settings.vault_path, str(note["path"]))
        note["id"] = record.id
        enqueue_note_changed_jobs(
            session, record.path, "NOTE_CREATED", record.content_hash
        )
    return note


@router.get("/{note_path:path}/status")
def get_note_processing_status(note_path: str) -> dict:
    from berrybrain_api.jobs import (
        PARSE_NOTE,
        CLASSIFY_NOTE,
        ASSIMILATE_NOTE,
        GENERATE_EMBEDDING,
        FIND_CONNECTIONS,
        GENERATE_INSIGHTS,
        GENERATE_NOTE_TITLE,
        EXPAND_KNOWLEDGE_GRAPH,
    )

    pipeline_order = [
        PARSE_NOTE,
        CLASSIFY_NOTE,
        ASSIMILATE_NOTE,
        GENERATE_EMBEDDING,
        FIND_CONNECTIONS,
        EXPAND_KNOWLEDGE_GRAPH,
        GENERATE_INSIGHTS,
        GENERATE_NOTE_TITLE,
    ]
    pipeline_labels = {
        PARSE_NOTE: "Parse",
        CLASSIFY_NOTE: "Classify",
        ASSIMILATE_NOTE: "Assimilate",
        GENERATE_EMBEDDING: "Embedding",
        FIND_CONNECTIONS: "Connections",
        EXPAND_KNOWLEDGE_GRAPH: "Expand graph",
        GENERATE_INSIGHTS: "Insights",
        GENERATE_NOTE_TITLE: "Title",
    }

    with SessionLocal() as session:
        from sqlalchemy import select
        from berrybrain_api.models import JobRecord

        jobs = list(
            session.execute(
                select(JobRecord)
                .where(JobRecord.payload.like(f'%"note_path":"{note_path}"%'))
                .order_by(JobRecord.created_at.desc())
            ).scalars()
        )

    latest: dict[str, dict] = {}
    for j in jobs:
        jt = j.type
        if jt not in latest:
            latest[jt] = {
                "type": jt,
                "label": pipeline_labels.get(jt, jt),
                "status": j.status,
                "error": j.error_message,
                "attempts": j.attempts,
                "id": j.id,
            }

    steps = []
    for jt in pipeline_order:
        if jt in latest:
            steps.append(latest[jt])
        else:
            steps.append(
                {
                    "type": jt,
                    "label": pipeline_labels.get(jt, jt),
                    "status": "pending",
                    "error": None,
                    "attempts": 0,
                    "id": None,
                }
            )

    completed_count = sum(1 for s in steps if s["status"] == "completed")
    running_count = sum(1 for s in steps if s["status"] == "running")
    failed_count = sum(1 for s in steps if s["status"] == "failed")

    return {
        "steps": steps,
        "completed": completed_count,
        "total": len(steps),
        "running": running_count,
        "failed": failed_count,
    }


@router.get("/attachments/{attachment_id}/download")
def download_attachment(attachment_id: int):
    settings = get_settings()
    with SessionLocal() as session:
        record = session.get(NoteAttachmentRecord, attachment_id)
        if record is None:
            raise HTTPException(status_code=404, detail="Attachment not found")
        path = (Path(settings.vault_path) / record.stored_path).resolve()
        vault_root = Path(settings.vault_path).resolve()
        if vault_root not in path.parents and path != vault_root:
            raise HTTPException(status_code=400, detail="Invalid attachment path")
        if not path.exists():
            raise HTTPException(status_code=404, detail="Attachment file not found")
        return FileResponse(
            path,
            media_type=record.mime_type or "application/octet-stream",
            filename=record.filename,
        )


@router.get("/attachments/{attachment_id}/extraction")
def get_attachment_extraction(attachment_id: int) -> dict:
    with SessionLocal() as session:
        record = session.get(NoteAttachmentRecord, attachment_id)
        if record is None:
            raise HTTPException(status_code=404, detail="Attachment not found")
        extraction = session.execute(
            select(AttachmentExtractionRecord).where(
                AttachmentExtractionRecord.attachment_id == attachment_id
            )
        ).scalar_one_or_none()
        return {"extraction": serialize_extraction(extraction)}


@router.post("/attachments/{attachment_id}/process")
def process_attachment_endpoint(attachment_id: int) -> dict:
    settings = get_settings()
    with SessionLocal() as session:
        try:
            result = process_attachment(session, settings.vault_path, attachment_id)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return {"extraction": result}


@router.post("/attachments/{attachment_id}/reprocess")
def reprocess_attachment(attachment_id: int) -> dict:
    with SessionLocal() as session:
        record = session.get(NoteAttachmentRecord, attachment_id)
        if record is None:
            raise HTTPException(status_code=404, detail="Attachment not found")
        job = create_job(
            session,
            PROCESS_ATTACHMENT,
            {
                "attachment_id": record.id,
                "note_path": record.note_path,
                "filename": record.filename,
            },
            max_attempts=2,
        )
        return {"status": "queued", "jobId": job.id, "attachmentId": record.id}


@router.delete("/attachments/{attachment_id}")
def delete_attachment(attachment_id: int) -> dict:
    settings = get_settings()
    with SessionLocal() as session:
        record = session.get(NoteAttachmentRecord, attachment_id)
        if record is None:
            raise HTTPException(status_code=404, detail="Attachment not found")
        path = (Path(settings.vault_path) / record.stored_path).resolve()
        vault_root = Path(settings.vault_path).resolve()
        if vault_root in path.parents and path.exists():
            path.unlink()
        session.delete(record)
        session.commit()
    return {"status": "deleted", "id": attachment_id}


@router.get("/{note_path:path}/attachments")
def list_note_attachments(note_path: str) -> dict:
    settings = get_settings()
    with SessionLocal() as session:
        record = sync_note_record(session, settings.vault_path, note_path)
        attachments = list(
            session.execute(
                select(NoteAttachmentRecord)
                .where(NoteAttachmentRecord.note_id == record.id)
                .order_by(NoteAttachmentRecord.created_at.desc())
            ).scalars()
        )
        extraction_by_attachment_id = {
            item.attachment_id: item
            for item in session.execute(
                select(AttachmentExtractionRecord).where(
                    AttachmentExtractionRecord.attachment_id.in_(
                        [attachment.id for attachment in attachments] or [-1]
                    )
                )
            ).scalars()
        }
        return {
            "attachments": [
                _serialize_attachment(item, extraction_by_attachment_id.get(item.id))
                for item in attachments
            ]
        }


@router.post("/{note_path:path}/attachments", status_code=201)
def upload_note_attachment(note_path: str, payload: AttachmentUploadRequest) -> dict:
    settings = get_settings()
    vault_root = Path(settings.vault_path).resolve()
    filename = _safe_filename(payload.filename)
    category = _attachment_category(payload.mime_type, filename)
    with SessionLocal() as session:
        limit_mb = _attachment_limit_mb(session, category)
        limit_bytes = limit_mb * 1024 * 1024
        if payload.size_bytes > limit_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"{category.capitalize()} attachments are limited to {limit_mb} MB.",
            )
        try:
            content = base64.b64decode(payload.content_base64, validate=True)
        except Exception as exc:
            raise HTTPException(status_code=400, detail="Invalid attachment data") from exc
        if len(content) != payload.size_bytes:
            raise HTTPException(status_code=400, detail="Attachment size mismatch")
        if len(content) > limit_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"{category.capitalize()} attachments are limited to {limit_mb} MB.",
            )

        note = sync_note_record(session, settings.vault_path, note_path)
        note_dir = re.sub(r"[^A-Za-z0-9._-]+", "-", note.path.replace("/", "-"))[:120]
        attachment_dir = vault_root / ".attachments" / note_dir
        attachment_dir.mkdir(parents=True, exist_ok=True)
        stored_name = f"{uuid4().hex}-{filename}"
        file_path = (attachment_dir / stored_name).resolve()
        if vault_root not in file_path.parents:
            raise HTTPException(status_code=400, detail="Invalid attachment path")
        file_path.write_bytes(content)
        attachment = NoteAttachmentRecord(
            note_id=note.id,
            note_path=note.path,
            filename=filename,
            stored_path=str(file_path.relative_to(vault_root)),
            mime_type=payload.mime_type or "application/octet-stream",
            category=category,
            size_bytes=len(content),
        )
        session.add(attachment)
        session.commit()
        session.refresh(attachment)
        job = create_job(
            session,
            PROCESS_ATTACHMENT,
            {
                "attachment_id": attachment.id,
                "note_path": attachment.note_path,
                "filename": attachment.filename,
            },
            max_attempts=2,
        )
        return {
            "attachment": _serialize_attachment(attachment),
            "processingJobId": job.id,
        }


@router.get("/{note_path:path}")
def read_note_endpoint(note_path: str) -> dict:
    settings = get_settings()
    note = read_note(settings.vault_path, note_path)
    with SessionLocal() as session:
        record = session.execute(
            select(NoteRecord).where(NoteRecord.path == str(note["path"]))
        ).scalar_one_or_none()
        if record:
            note["id"] = record.id
    return note


@router.put("/{note_path:path}")
def update_note_endpoint(note_path: str, payload: UpdateNoteRequest) -> dict:
    settings = get_settings()
    note = update_note(settings.vault_path, note_path, payload.content)
    with SessionLocal() as session:
        record = sync_note_record(session, settings.vault_path, note_path)
        enqueue_note_changed_jobs(
            session, record.path, "NOTE_UPDATED", record.content_hash
        )
    return note


@router.post("/{note_path:path}/reprocess")
def reprocess_note_endpoint(note_path: str) -> dict:
    settings = get_settings()
    with SessionLocal() as session:
        record = sync_note_record(session, settings.vault_path, note_path)
        queued_note_path = record.path
        jobs = enqueue_note_changed_jobs(
            session, record.path, "NOTE_UPDATED", record.content_hash
        )
    return {"status": "queued", "jobsCreated": len(jobs), "notePath": queued_note_path}


@router.delete("/{note_path:path}")
def delete_note_endpoint(note_path: str) -> dict:
    settings = get_settings()
    result = delete_note(settings.vault_path, note_path)
    with SessionLocal() as session:
        remove_note_record(session, note_path)
    return result


@router.put("/{note_path:path}/rename")
def rename_note_endpoint(note_path: str, payload: RenameNoteRequest) -> dict:
    from sqlalchemy import select

    from berrybrain_api.models import NoteRecord

    settings = get_settings()
    result = rename_note(settings.vault_path, note_path, payload.title)
    with SessionLocal() as session:
        record = session.execute(
            select(NoteRecord).where(NoteRecord.path == note_path)
        ).scalar_one_or_none()
        if record is not None:
            new_path = str(result["path"])
            record.path = new_path
            record.title = payload.title
            session.commit()
            _update_internal_links(session, note_path, new_path)
        else:
            sync_note_record(session, settings.vault_path, str(result["path"]))
    return result


def _update_internal_links(session, old_path: str, new_path: str) -> None:
    from sqlalchemy import select

    from berrybrain_api.models import NoteRecord
    from berrybrain_api.vault import resolve_note_path

    if old_path == new_path:
        return

    settings = get_settings()
    rows = session.execute(select(NoteRecord)).scalars().all()
    old_ref = f"[[{old_path}]]"
    new_ref = f"[[{new_path}]]"
    for row in rows:
        if old_ref not in (row.content or ""):
            continue
        row.content = row.content.replace(old_ref, new_ref)
        abs_path = resolve_note_path(settings.vault_path, row.path)
        if abs_path.exists():
            abs_path.write_text(row.content, encoding="utf-8")
    session.commit()


@router.get("/{note_path:path}/download")
def download_note_endpoint(note_path: str):
    settings = get_settings()
    path = resolve_note_path(settings.vault_path, note_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Note not found")
    return FileResponse(path, filename=path.name, media_type="text/markdown")


@router.post("/clip")
def clip_web_content(payload: ClipRequest):
    from datetime import datetime

    settings = get_settings()
    now = datetime.utcnow().isoformat()
    markdown = f"# {payload.title}\n\n> Fonte: {payload.url}\n> Clipped: {now}\n\n{payload.content}"
    result = create_note(settings.vault_path, payload.title, markdown, folder="inbox")
    with SessionLocal() as session:
        sync_note_record(session, settings.vault_path, str(result["path"]))
        enqueue_note_changed_jobs(
            session,
            str(result["path"]),
            "NOTE_CREATED",
            result["content_hash"],
        )
    return result
