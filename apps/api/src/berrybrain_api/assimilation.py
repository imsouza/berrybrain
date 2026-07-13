from __future__ import annotations

import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

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
    note_by_path = {note.path: note for note in notes}

    metadata_note_ids: set[int] = set()
    for row in session.execute(
        select(GeneratedMetadataRecord).where(
            GeneratedMetadataRecord.note_id.in_(note_ids)
        )
    ).scalars():
        if row.content_hash and row.content_hash != note_hash_by_id.get(row.note_id):
            continue
        metadata_note_ids.add(row.note_id)

    embedding_note_ids: set[int] = set()
    for row in session.execute(
        select(EmbeddingRecord).where(EmbeddingRecord.note_id.in_(note_ids))
    ).scalars():
        if row.content_hash and row.content_hash != note_hash_by_id.get(row.note_id):
            continue
        embedding_note_ids.add(row.note_id)

    note_node_ids: dict[int, int] = {}
    for node in session.execute(
        select(GraphNodeRecord).where(
            GraphNodeRecord.type == "note",
            GraphNodeRecord.source_id.in_(note_ids),
            GraphNodeRecord.status != "ignored",
        )
    ).scalars():
        note_node_ids[node.id] = node.source_id

    connected_note_ids: set[int] = set()
    if note_node_ids:
        for edge in session.execute(
            select(GraphEdgeRecord).where(GraphEdgeRecord.status != "ignored")
        ).scalars():
            source_note_id = note_node_ids.get(edge.source_node_id)
            target_note_id = note_node_ids.get(edge.target_node_id)
            if source_note_id:
                connected_note_ids.add(source_note_id)
            if target_note_id:
                connected_note_ids.add(target_note_id)

    completed_job_note_ids: set[int] = set()
    if jobs is None:
        jobs = list(
            session.execute(
                select(JobRecord).where(
                    JobRecord.status == COMPLETED,
                    JobRecord.type.in_(ASSIMILATION_JOB_TYPES),
                )
            ).scalars()
        )
    for job in jobs:
        if job.status != COMPLETED or job.type not in ASSIMILATION_JOB_TYPES:
            continue
        payload = _payload(job.payload)
        note = note_by_path.get(str(payload.get("note_path") or ""))
        if not note:
            continue
        content_hash = str(payload.get("content_hash") or "")
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
