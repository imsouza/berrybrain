from __future__ import annotations

import json
from typing import Any

from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import Session

from berrybrain_api.artifact_state import accepted_edge_clause, accepted_node_clause
from berrybrain_api.jobs import COMPLETED
from berrybrain_api.models import (
    EmbeddingRecord,
    GeneratedMetadataRecord,
    GraphEdgeRecord,
    GraphNodeRecord,
    JobRecord,
    NoteRecord,
)

ASSIMILATION_JOB_TYPES = {
    "ASSIMILATE_NOTE",
    "EXTRACT_CONCEPTS",
    "EXTRACT_ENTITIES",
    "DETECT_TOPICS",
    "EXTRACT_CONTEXT",
    "GENERATE_EMBEDDING",
    "FIND_CONNECTIONS",
    "EXPAND_KNOWLEDGE_GRAPH",
    "GENERATE_INFERRED_CONNECTIONS",
    "EXPAND_CONCEPT_TO_NOTE",
    "GENERATE_GRAPH_INSIGHTS",
    "UPDATE_GRAPH_STATS",
}


def _payload(raw: str | None) -> dict[str, Any]:
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def note_assimilation_map(
    session: Session,
    notes: list[NoteRecord],
    jobs: list[JobRecord] | None = None,
) -> dict[int, dict[str, Any]]:
    """Return per-note assimilation state based on durable knowledge signals.

    A note can be "synced" before the cognitive pipeline has actually produced
    useful graph/metadata output. Conversely, older rows may miss
    last_processed_at even though they already have graph nodes and edges. This
    helper uses the generated artifacts themselves as the source of truth.
    """

    if not notes:
        return {}

    note_ids = {note.id for note in notes}
    note_hash_by_id = {note.id: note.content_hash for note in notes}
    note_by_id = {note.id: note for note in notes}
    note_by_path = {note.path: note for note in notes}

    metadata_note_ids: set[int] = set()
    for row in session.execute(
        select(
            GeneratedMetadataRecord.note_id,
            GeneratedMetadataRecord.content_hash,
        ).where(GeneratedMetadataRecord.note_id.in_(note_ids))
    ).all():
        if row.content_hash and row.content_hash != note_hash_by_id.get(row.note_id):
            continue
        metadata_note_ids.add(row.note_id)

    embedding_note_ids: set[int] = set()
    for row in session.execute(
        select(EmbeddingRecord.note_id, EmbeddingRecord.content_hash).where(
            EmbeddingRecord.note_id.in_(note_ids)
        )
    ).all():
        if row.content_hash and row.content_hash != note_hash_by_id.get(row.note_id):
            continue
        embedding_note_ids.add(row.note_id)

    note_node_ids: dict[int, int] = {}
    for node in session.execute(
        select(GraphNodeRecord.id, GraphNodeRecord.source_id).where(
            GraphNodeRecord.type == "note",
            GraphNodeRecord.source_id.in_(note_ids),
            accepted_node_clause(),
        )
    ).all():
        note_node_ids[node.id] = node.source_id

    connected_note_ids: set[int] = set()
    if note_node_ids:
        for edge in session.execute(
            select(
                GraphEdgeRecord.source_node_id,
                GraphEdgeRecord.target_node_id,
            ).where(accepted_edge_clause())
        ).all():
            source_note_id = note_node_ids.get(edge.source_node_id)
            target_note_id = note_node_ids.get(edge.target_node_id)
            if source_note_id:
                connected_note_ids.add(source_note_id)
            if target_note_id:
                connected_note_ids.add(target_note_id)

    completed_job_note_ids: set[int] = set()
    if jobs is None:
        valid_payload = case(
            (func.json_valid(JobRecord.payload), JobRecord.payload), else_="{}"
        )
        effective_hash = case(
            (JobRecord.content_hash != "", JobRecord.content_hash),
            else_=func.coalesce(func.json_extract(valid_payload, "$.content_hash"), ""),
        )
        # Resolve current note identity/hash in SQL. Return one ID per note,
        # not every historical job and its potentially large JSON payload.
        structured = (
            select(NoteRecord.id)
            .join(JobRecord, JobRecord.note_id == NoteRecord.id)
            .where(
                NoteRecord.id.in_(note_ids),
                JobRecord.status == COMPLETED,
                JobRecord.type.in_(ASSIMILATION_JOB_TYPES),
                or_(effective_hash == "", effective_hash == NoteRecord.content_hash),
            )
            .distinct()
        )
        completed_job_note_ids.update(session.scalars(structured))
        # Pre-structured legacy jobs still identify notes by path in JSON.
        # CASE protects malformed old payloads from SQLite json_extract errors.
        legacy_path = case(
            (JobRecord.note_path != "", JobRecord.note_path),
            else_=func.json_extract(valid_payload, "$.note_path"),
        )
        completed_job_note_ids.update(
            session.execute(
                select(NoteRecord.id)
                .join(JobRecord, legacy_path == NoteRecord.path)
                .where(
                    NoteRecord.id.in_(note_ids),
                    JobRecord.note_id == 0,
                    JobRecord.status == COMPLETED,
                    JobRecord.type.in_(ASSIMILATION_JOB_TYPES),
                    or_(
                        effective_hash == "", effective_hash == NoteRecord.content_hash
                    ),
                )
                .distinct()
            ).scalars()
        )
    for job in jobs or []:
        if job.status != COMPLETED or job.type not in ASSIMILATION_JOB_TYPES:
            continue
        payload = _payload(job.payload)
        job_note_id = getattr(job, "note_id", 0)
        note = note_by_id.get(job_note_id)
        if note is None and not job_note_id:
            note = note_by_path.get(
                str(getattr(job, "note_path", "") or payload.get("note_path") or "")
            )
        if not note:
            continue
        content_hash = str(
            getattr(job, "content_hash", "") or payload.get("content_hash") or ""
        )
        if content_hash and content_hash != note.content_hash:
            continue
        completed_job_note_ids.add(note.id)

    result: dict[int, dict[str, Any]] = {}
    for note in notes:
        has_content = bool((note.content or "").strip())
        signals = {
            "status": note.status in {"processed", "assimilated"},
            "metadata": note.id in metadata_note_ids,
            "embedding": note.id in embedding_note_ids,
            "connectedGraphNode": note.id in connected_note_ids,
            "completedPipelineJob": note.id in completed_job_note_ids,
        }
        result[note.id] = {
            "assimilated": has_content and any(signals.values()),
            "signals": signals,
        }
    return result
