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
    elif record.content_hash and record.content_hash != metadata.content_hash:
        from berrybrain_api.jobs import (
            EXPAND_KNOWLEDGE_GRAPH,
            affected_job_types_for_note_update,
        )

        affected_job_types = affected_job_types_for_note_update(
            record.content, content, relative_path
        )
        if EXPAND_KNOWLEDGE_GRAPH in affected_job_types:
            _detach_note_graph_provenance(session, record.id, delete_note_node=False)

    record.title = title
    record.slug = path.stem
    record.content = content
    record.content_hash = metadata.content_hash
    record.frontmatter = compact_json(metadata.frontmatter)
    record.links = compact_json(metadata.links)
    record.language = string_frontmatter(metadata.frontmatter, "language", "und")
    record.note_type = string_frontmatter(metadata.frontmatter, "note_type", "note")
    record.status = "synced"

    session.flush()
    from berrybrain_api.graph_expansion import sync_note_graph_node

    sync_note_graph_node(session, record)
    session.commit()
    session.refresh(record)
    return record


def remove_note_record(session: Session, note_path: str) -> int:
    from berrybrain_api.models import (
        ConnectionRecord,
        EmbeddingRecord,
        GeneratedMetadataRecord,
    )

    record = session.execute(
        select(NoteRecord).where(NoteRecord.path == note_path)
    ).scalar_one_or_none()
    if record is None:
        return 0

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

    _detach_note_graph_provenance(session, note_id, delete_note_node=True)

    session.delete(record)
    session.commit()
    from berrybrain_api.jobs import enqueue_note_deleted_jobs

    return len(enqueue_note_deleted_jobs(session, note_path, note_id))


def _detach_note_graph_provenance(
    session: Session, note_id: int, *, delete_note_node: bool
) -> None:
    from berrybrain_api.graph_write_service import (
        recalculate_edge_confidence,
        recalculate_node_confidence,
    )
    from berrybrain_api.models import GraphEdgeRecord, GraphNodeRecord

    nodes = list(session.execute(select(GraphNodeRecord)).scalars())
    node_ids_to_delete = {
        node.id
        for node in nodes
        if delete_note_node and node.type == "note" and node.source_id == note_id
    }

    for node in nodes:
        if node.id in node_ids_to_delete or node.type == "note":
            continue
        source_ids = _integer_list(node.source_note_ids)
        if note_id not in source_ids:
            continue
        remaining = sorted(source_ids - {note_id})
        if not remaining:
            node_ids_to_delete.add(node.id)
            continue
        node.source_note_ids = compact_json(remaining)
        recalculate_node_confidence(node)

    for edge in list(session.execute(select(GraphEdgeRecord)).scalars()):
        if (
            edge.source_node_id in node_ids_to_delete
            or edge.target_node_id in node_ids_to_delete
        ):
            session.delete(edge)
            continue
        source_ids = _integer_list(edge.source_note_ids)
        if note_id not in source_ids:
            continue
        remaining = sorted(source_ids - {note_id})
        if not remaining:
            session.delete(edge)
            continue
        edge.source_note_ids = compact_json(remaining)
        recalculate_edge_confidence(edge)

    for node in nodes:
        if node.id in node_ids_to_delete:
            session.delete(node)


def _integer_list(raw: str | None) -> set[int]:
    try:
        values = json.loads(raw or "[]")
    except (TypeError, json.JSONDecodeError):
        return set()
    if not isinstance(values, list):
        return set()
    result: set[int] = set()
    for value in values:
        try:
            result.add(int(value))
        except (TypeError, ValueError):
            continue
    return result


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
