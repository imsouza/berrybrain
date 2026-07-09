from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from berrybrain_api.config import get_settings
from berrybrain_api.database import SessionLocal
from berrybrain_api.jobs import enqueue_note_changed_jobs
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
        PARSE_NOTE: "Analisar",
        CLASSIFY_NOTE: "Classificar",
        ASSIMILATE_NOTE: "Assimilar",
        GENERATE_EMBEDDING: "Embedding",
        FIND_CONNECTIONS: "Conexoes",
        EXPAND_KNOWLEDGE_GRAPH: "Expandir grafo",
        GENERATE_INSIGHTS: "Insights",
        GENERATE_NOTE_TITLE: "Titulo",
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


@router.get("/{note_path:path}")
def read_note_endpoint(note_path: str) -> dict:
    from sqlalchemy import select
    from berrybrain_api.models import NoteRecord

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
