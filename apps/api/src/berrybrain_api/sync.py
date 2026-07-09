from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from berrybrain_api.models import NoteRecord
from berrybrain_api.vault import parse_markdown_note, resolve_note_path


def sync_note_record(session: Session, vault_path: Path, note_path: str) -> NoteRecord:
    path = resolve_note_path(vault_path, note_path)
    content = path.read_text(encoding="utf-8")
    metadata = parse_markdown_note(content)
    relative_path = path.relative_to(vault_path.resolve()).as_posix()
    title = title_from_markdown(metadata.body) or path.stem.replace("-", " ").title()

    record = session.execute(
        select(NoteRecord).where(NoteRecord.path == relative_path)
    ).scalar_one_or_none()
    if record is None:
        record = NoteRecord(path=relative_path, slug=path.stem, title=title)
        session.add(record)

    record.title = title
    record.slug = path.stem
    record.content = content
    record.content_hash = metadata.content_hash
    record.frontmatter = compact_json(metadata.frontmatter)
    record.links = compact_json(metadata.links)
    record.language = string_frontmatter(metadata.frontmatter, "language", "pt-BR")
    record.note_type = string_frontmatter(metadata.frontmatter, "note_type", "note")
    record.status = "synced"

    session.commit()
    session.refresh(record)
    return record


def remove_note_record(session: Session, note_path: str) -> None:
    from berrybrain_api.models import (
        ConnectionRecord,
        EmbeddingRecord,
        GeneratedMetadataRecord,
        GraphEdgeRecord,
        GraphNodeRecord,
    )

    record = session.execute(
        select(NoteRecord).where(NoteRecord.path == note_path)
    ).scalar_one_or_none()
    if record is None:
        return

    note_id = record.id

    for conn in session.execute(
        select(ConnectionRecord).where(
            (ConnectionRecord.source_note_id == note_id)
            | (ConnectionRecord.target_note_id == note_id)
        )
    ).scalars():
        session.delete(conn)

    for gm in session.execute(
        select(GeneratedMetadataRecord).where(
            GeneratedMetadataRecord.note_id == note_id
        )
    ).scalars():
        session.delete(gm)

    for emb in session.execute(
        select(EmbeddingRecord).where(EmbeddingRecord.note_id == note_id)
    ).scalars():
        session.delete(emb)

    for node in session.execute(
        select(GraphNodeRecord).where(GraphNodeRecord.source_id == note_id)
    ).scalars():
        for edge in session.execute(
            select(GraphEdgeRecord).where(
                (GraphEdgeRecord.source_node_id == node.id)
                | (GraphEdgeRecord.target_node_id == node.id)
            )
        ).scalars():
            session.delete(edge)
        session.delete(node)

    session.delete(record)
    session.commit()


def title_from_markdown(body: str) -> str | None:
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip() or None
    return None


def string_frontmatter(
    frontmatter: dict[str, str | list[str]], key: str, default: str
) -> str:
    value = frontmatter.get(key)
    return value if isinstance(value, str) and value else default


def compact_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
