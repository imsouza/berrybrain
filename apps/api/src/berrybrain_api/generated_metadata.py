from __future__ import annotations

import json
from typing import Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from berrybrain_api.models import GeneratedMetadataRecord, NoteRecord


def upsert_generated_metadata(
    session: Session,
    note_id: int,
    generation_type: str,
    content: dict[str, Any],
    content_hash: str,
    model_used: str | None = None,
) -> GeneratedMetadataRecord:
    note = session.get(NoteRecord, note_id)
    if (
        note is not None
        and note.content_hash
        and content_hash
        and note.content_hash != content_hash
    ):
        existing_stale = session.execute(
            select(GeneratedMetadataRecord).where(
                GeneratedMetadataRecord.note_id == note_id,
                GeneratedMetadataRecord.generation_type == generation_type,
            )
        ).scalar_one_or_none()
        if existing_stale is not None:
            return existing_stale
        raise HTTPException(
            status_code=409,
            detail="Generated metadata is stale for current note content",
        )

    existing = session.execute(
        select(GeneratedMetadataRecord).where(
            GeneratedMetadataRecord.note_id == note_id,
            GeneratedMetadataRecord.generation_type == generation_type,
        )
    ).scalar_one_or_none()

    if existing:
        if existing.content_hash == content_hash:
            return existing
        existing.content = compact_json(content)
        existing.content_hash = content_hash
        existing.model_used = model_used
    else:
        existing = GeneratedMetadataRecord(
            note_id=note_id,
            generation_type=generation_type,
            content=compact_json(content),
            content_hash=content_hash,
            model_used=model_used,
        )
        session.add(existing)

    session.commit()
    session.refresh(existing)
    return existing


def get_generated_metadata(
    session: Session,
    note_id: int,
    generation_type: str | None = None,
) -> list[GeneratedMetadataRecord]:
    query = select(GeneratedMetadataRecord).where(
        GeneratedMetadataRecord.note_id == note_id
    )
    if generation_type:
        query = query.where(GeneratedMetadataRecord.generation_type == generation_type)
    return list(session.execute(query).scalars())


def get_generated_metadata_or_404(
    session: Session,
    note_id: int,
    generation_type: str,
) -> GeneratedMetadataRecord:
    record = session.execute(
        select(GeneratedMetadataRecord).where(
            GeneratedMetadataRecord.note_id == note_id,
            GeneratedMetadataRecord.generation_type == generation_type,
        )
    ).scalar_one_or_none()
    if record is None:
        raise HTTPException(status_code=404, detail="Generated metadata not found")
    return record


def delete_generated_metadata(
    session: Session,
    note_id: int,
    generation_type: str | None = None,
) -> int:
    query = select(GeneratedMetadataRecord).where(
        GeneratedMetadataRecord.note_id == note_id
    )
    if generation_type:
        query = query.where(GeneratedMetadataRecord.generation_type == generation_type)

    records = list(session.execute(query).scalars())
    count = len(records)
    for record in records:
        session.delete(record)
    session.commit()
    return count


def is_stale(
    session: Session,
    note_id: int,
    current_hash: str,
) -> list[str]:
    records = get_generated_metadata(session, note_id)
    return [r.generation_type for r in records if r.content_hash != current_hash]


def resolve_note_id(session: Session, note_path: str) -> int:
    note = session.execute(
        select(NoteRecord).where(NoteRecord.path == note_path)
    ).scalar_one_or_none()
    if note is None:
        raise HTTPException(status_code=404, detail="Note not found")
    return note.id


def serialize_generated_metadata(record: GeneratedMetadataRecord) -> dict[str, Any]:
    return {
        "id": record.id,
        "note_id": record.note_id,
        "generation_type": record.generation_type,
        "content": parse_json(record.content),
        "content_hash": record.content_hash,
        "model_used": record.model_used,
        "created_at": record.created_at.isoformat() if record.created_at else None,
    }


def compact_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def parse_json(value: str) -> Any:
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return {}
