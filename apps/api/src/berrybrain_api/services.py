from __future__ import annotations

import json
import struct
from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from berrybrain_api.confidence import (
    estimate_connection_confidence,
    persist_confidence,
    persist_percentage_confidence,
    serialize_percentage_confidence,
)
from berrybrain_api.graph_quality import (
    _filter_nodes_by_view,
    graph_quality_report,  # noqa: F401
)
from berrybrain_api.graph_write_service import GraphWriteService
from berrybrain_api.insight_service import (  # noqa: F401
    _is_visible_insight,
    create_insight,
    dismiss_insight,
    get_active_insights,
    insight_fingerprint,
    migrate_legacy_insights,
    score_insight_quality,
    serialize_insight,
)
from berrybrain_api.models import (
    ChunkRecord,
    ConceptRecord,
    ConnectionRecord,
    EmbeddingRecord,
    GraphEdgeRecord,
    GraphInferenceRecord,
    GraphNodeRecord,
    NoteRecord,
)

VALID_CONNECTION_TYPES = {
    "backlink",
    "semantic_similarity",
    "shared_concept",
    "semantic",
    "prerequisite",
    "related",
    "duplicate",
    "contrast",
    "example",
    "application",
}

VALID_INSIGHT_TYPES = {
    "knowledge_gap",
    "weak_note",
    "isolated_concept",
    "duplicate_content",
    "study_path",
}


def create_connection(
    session: Session,
    source_note_id: int,
    target_note_id: int,
    connection_type: str,
    confidence: int | float | None = None,
    reason: str = "",
    created_by: str = "system",
    evidence: list[str] | None = None,
    provider: str = "",
    model: str = "",
    prompt_version: str = "",
    status: str = "suggested",
) -> ConnectionRecord:
    evidence_items = evidence or []
    conn = ConnectionRecord(
        source_note_id=source_note_id,
        target_note_id=target_note_id,
        connection_type=connection_type,
        confidence=0,
        reason=reason,
        evidence=json.dumps(evidence_items, ensure_ascii=False),
        created_by=created_by,
        provider=provider,
        model=model,
        prompt_version=prompt_version,
        status=status,
    )
    model_source = (
        ":".join(part for part in (provider, model, prompt_version, created_by) if part)
        or "connection-model"
    )
    persist_percentage_confidence(
        conn,
        estimate_connection_confidence(
            reason=reason,
            evidence=evidence_items,
            model_score=confidence,
            model_source=model_source,
        ),
    )
    session.add(conn)
    session.flush()
    if provider:
        from berrybrain_api.job_contracts import judge_artifact_payload
        from berrybrain_api.jobs import enqueue_job

        enqueue_job(
            session,
            "JUDGE_ARTIFACT",
            judge_artifact_payload(
                session,
                "connection",
                conn.id,
                str(conn.updated_at.timestamp()),
            ),
            priority=20,
        )
    session.commit()
    session.refresh(conn)
    return conn


def audit_connection_confidence(
    session: Session, *, apply: bool = False
) -> dict[str, int]:
    """Find and optionally recalculate migrated note-connection confidence."""
    connections = list(
        session.execute(
            select(ConnectionRecord).order_by(ConnectionRecord.id)
        ).scalars()
    )
    pending = [
        connection
        for connection in connections
        if connection.confidence_updated_at is None
    ]
    result = {
        "examined": len(connections),
        "pending": len(pending),
        "recalculated": 0,
        "available": 0,
        "unavailable": 0,
    }
    if not apply:
        return result

    for connection in pending:
        estimate = estimate_connection_confidence(
            reason=connection.reason,
            evidence=_parse_json_list(connection.evidence),
        )
        persist_percentage_confidence(connection, estimate)
        result["recalculated"] += 1
        availability = "available" if estimate.score is not None else "unavailable"
        result[availability] += 1
    return result


def audit_knowledge_confidence(
    session: Session, *, apply: bool = False
) -> dict[str, dict[str, int]]:
    """Audit all migrated knowledge records that now require confidence intervals."""
    result = {
        "connections": audit_connection_confidence(session, apply=apply),
        "concepts": _audit_float_confidence_records(
            list(
                session.execute(
                    select(ConceptRecord).order_by(ConceptRecord.id)
                ).scalars()
            ),
            apply=apply,
            reason=lambda item: item.description or item.name,
            evidence=lambda item: _parse_json_list(item.source_evidence)
            + [
                {"sourceNoteId": note_id}
                for note_id in _parse_json_list(item.related_note_ids)
            ],
        ),
        "graphInferences": _audit_float_confidence_records(
            list(
                session.execute(
                    select(GraphInferenceRecord).order_by(GraphInferenceRecord.id)
                ).scalars()
            ),
            apply=apply,
            reason=lambda item: item.answer,
            evidence=lambda item: _parse_json_list(item.evidence),
        ),
    }
    return result


def _audit_float_confidence_records(
    records: list[Any],
    *,
    apply: bool,
    reason: Any,
    evidence: Any,
) -> dict[str, int]:
    pending = [record for record in records if record.confidence_updated_at is None]
    result = {
        "examined": len(records),
        "pending": len(pending),
        "recalculated": 0,
        "available": 0,
        "unavailable": 0,
    }
    if not apply:
        return result
    for record in pending:
        estimate = estimate_connection_confidence(
            reason=reason(record),
            evidence=evidence(record),
        )
        persist_confidence(record, estimate)
        result["recalculated"] += 1
        availability = "available" if estimate.score is not None else "unavailable"
        result[availability] += 1
    return result


def get_connections_for_note(
    session: Session,
    note_id: int,
) -> list[ConnectionRecord]:
    return list(
        session.execute(
            select(ConnectionRecord)
            .where(
                (ConnectionRecord.source_note_id == note_id)
                | (ConnectionRecord.target_note_id == note_id)
            )
            .order_by(ConnectionRecord.confidence.desc())
        ).scalars()
    )


def set_connection_status(
    session: Session,
    connection_id: int,
    status: str,
) -> ConnectionRecord:
    conn = session.get(ConnectionRecord, connection_id)
    if conn is None:
        raise HTTPException(status_code=404, detail="Connection not found")
    conn.status = status
    conn.updated_at = datetime.now(UTC)
    session.commit()
    session.refresh(conn)
    return conn


def delete_connections_for_note(session: Session, note_id: int) -> int:
    conns = get_connections_for_note(session, note_id)
    for conn in conns:
        session.delete(conn)
    session.commit()
    return len(conns)


def serialize_connection(
    session: Session,
    conn: ConnectionRecord,
) -> dict[str, Any]:
    source_note = session.get(NoteRecord, conn.source_note_id)
    target_note = session.get(NoteRecord, conn.target_note_id)
    return {
        "id": conn.id,
        "source_note": {
            "id": source_note.id,
            "title": source_note.title,
            "path": source_note.path,
        }
        if source_note
        else None,
        "target_note": {
            "id": target_note.id,
            "title": target_note.title,
            "path": target_note.path,
        }
        if target_note
        else None,
        "connection_type": conn.connection_type,
        "confidence": conn.confidence,
        "confidenceInterval": serialize_percentage_confidence(conn),
        "reason": conn.reason,
        "evidence": _parse_json_list(getattr(conn, "evidence", "[]")),
        "ai_notes": getattr(conn, "ai_notes", ""),
        "created_by": conn.created_by,
        "provider": getattr(conn, "provider", ""),
        "model": getattr(conn, "model", ""),
        "prompt_version": getattr(conn, "prompt_version", ""),
        "status": getattr(conn, "status", "suggested"),
        "created_at": conn.created_at.isoformat() if conn.created_at else None,
        "updated_at": conn.updated_at.isoformat()
        if getattr(conn, "updated_at", None)
        else None,
    }


def _parse_json_list(value: str) -> list[Any]:
    try:
        parsed = json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return []
    return parsed if isinstance(parsed, list) else []


def _parse_json_dict(value: str) -> dict[str, Any]:
    try:
        parsed = json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _compact_confidence(target: Any) -> dict[str, Any] | None:
    sample_size = int(getattr(target, "confidence_sample_size", 0) or 0)
    if sample_size <= 0:
        return None
    return {
        "score": getattr(target, "confidence", None),
        "lower": getattr(target, "confidence_lower", None),
        "upper": getattr(target, "confidence_upper", None),
        "sampleSize": sample_size,
        "method": getattr(target, "confidence_method", "unavailable") or "unavailable",
    }


def _prune_empty_projection(
    payload: dict[str, Any], *, preserve: frozenset[str]
) -> dict[str, Any]:
    return {
        key: value
        for key, value in payload.items()
        if key in preserve or value not in (None, "", [], {})
    }


_NODE_PROJECTION_REQUIRED = frozenset(
    {
        "id",
        "recordId",
        "label",
        "title",
        "summary",
        "type",
        "status",
        "confidence",
        "confidenceInterval",
        "semanticState",
        "semanticStatus",
    }
)
_EDGE_PROJECTION_REQUIRED = frozenset(
    {
        "id",
        "source",
        "target",
        "type",
        "confidence",
        "confidenceInterval",
        "semanticStatus",
        "reason",
        "status",
    }
)


def resolve_note_id(session: Session, note_path: str) -> int:
    note = session.execute(
        select(NoteRecord).where(NoteRecord.path == note_path)
    ).scalar_one_or_none()
    if note is None:
        raise HTTPException(status_code=404, detail="Note not found")
    return note.id


def _is_system_diagnostic_graph_node(node: GraphNodeRecord) -> bool:
    if (getattr(node, "type", "") or "").lower() != "insight":
        return False
    combined = " ".join(
        [
            getattr(node, "label", "") or "",
            getattr(node, "title", "") or "",
            getattr(node, "summary", "") or "",
            getattr(node, "ai_summary", "") or "",
            getattr(node, "ai_context", "") or "",
            getattr(node, "source_evidence", "") or "",
            getattr(node, "graph_metadata", "") or "",
        ]
    ).lower()
    return any(
        term in combined
        for term in (
            "pipeline bottleneck",
            "jobsbytype",
            "generate_note_title",
            "enrich_graph_node",
            "semantic_data",
            "semanticstate",
            "graphsummary",
            "raw json",
            "worker",
            "provider",
            "backlog",
            "queue",
        )
    )


def build_graph(
    session: Session,
    max_depth: int = 2,
    view: str = "",
) -> dict[str, Any]:
    graph_nodes = list(
        session.execute(
            select(GraphNodeRecord.__table__).where(
                GraphNodeRecord.semantic_status == "active"
            )
        ).all()
    )
    if graph_nodes:
        graph_edges = list(
            session.execute(
                select(GraphEdgeRecord.__table__).where(
                    GraphEdgeRecord.status != "ignored",
                    GraphEdgeRecord.semantic_status == "active",
                )
            ).all()
        )
        graph_nodes = [
            node for node in graph_nodes if not _is_system_diagnostic_graph_node(node)
        ]
        if view.lower() != "hidden":
            graph_nodes = [
                node
                for node in graph_nodes
                if getattr(node, "status", "suggested") != "ignored"
            ]
        node_ids = {node.id: f"{node.type}_{node.id}" for node in graph_nodes}
        nodes = []
        for node in graph_nodes:
            metadata = _parse_json_dict(getattr(node, "graph_metadata", "{}"))
            nodes.append(
                _prune_empty_projection(
                    {
                        "id": node_ids[node.id],
                        "recordId": node.id,
                        "label": node.label,
                        "title": getattr(node, "title", "") or node.label,
                        "summary": getattr(node, "summary", ""),
                        "type": node.type,
                        "source": getattr(node, "source", ""),
                        "sourceId": node.source_id,
                        "status": getattr(node, "status", "suggested"),
                        "confidence": (
                            node.confidence if node.confidence_sample_size else None
                        ),
                        "confidenceInterval": _compact_confidence(node),
                        "createdBy": getattr(node, "created_by", "system"),
                        "aiSummary": getattr(node, "ai_summary", ""),
                        "aiContext": getattr(node, "ai_context", ""),
                        "sourceEvidence": getattr(node, "source_evidence", ""),
                        "validationStatus": getattr(
                            node, "validation_status", "unvalidated"
                        ),
                        "semanticState": getattr(node, "semantic_state", "pending"),
                        "clusterId": getattr(node, "cluster_id", None),
                        "colorId": getattr(node, "color_id", "pending"),
                        "colorConfidence": getattr(node, "color_confidence", 0.0),
                        "path": metadata.get("path", ""),
                        "folder": metadata.get("folder", ""),
                    },
                    preserve=_NODE_PROJECTION_REQUIRED,
                )
            )

        if view:
            nodes = _filter_nodes_by_view(nodes, view)

        visible_node_ids = {node["id"] for node in nodes}
        edges = []
        degrees: dict[str, int] = {node["id"]: 0 for node in nodes}
        for edge in graph_edges:
            source = node_ids.get(edge.source_node_id)
            target = node_ids.get(edge.target_node_id)
            if source is None or target is None:
                continue
            if source not in visible_node_ids or target not in visible_node_ids:
                continue
            edges.append(
                _prune_empty_projection(
                    {
                        "id": edge.id,
                        "source": source,
                        "target": target,
                        "type": edge.type,
                        "label": getattr(edge, "label", ""),
                        "confidence": (
                            edge.confidence if edge.confidence_sample_size else None
                        ),
                        "confidenceInterval": _compact_confidence(edge),
                        "reason": edge.reason,
                        "evidence": _parse_json_list(getattr(edge, "evidence", "[]")),
                        "provider": getattr(edge, "provider", ""),
                        "model": getattr(edge, "model", ""),
                        "status": getattr(edge, "status", "suggested"),
                    },
                    preserve=_EDGE_PROJECTION_REQUIRED,
                )
            )
            degrees[source] = degrees.get(source, 0) + 1
            degrees[target] = degrees.get(target, 0) + 1

        for node in nodes:
            node["connectionsCount"] = degrees.get(node["id"], 0)
        central = sorted(degrees.items(), key=lambda x: x[1], reverse=True)[:5]
        return {
            "nodes": nodes,
            "edges": edges,
            "stats": {
                "node_count": len(nodes),
                "edge_count": len(edges),
                "orphan_count": sum(1 for deg in degrees.values() if deg == 0),
                "central_nodes": [
                    {"id": nid, "degree": deg} for nid, deg in central if deg > 0
                ],
            },
        }

    notes = list(session.execute(select(NoteRecord)).scalars())
    conns = list(session.execute(select(ConnectionRecord)).scalars())

    nodes = []
    seen_ids = set()

    for note in notes:
        if note.id in seen_ids:
            continue
        seen_ids.add(note.id)
        nodes.append(
            {
                "id": f"note_{note.id}",
                "label": note.title,
                "type": "note",
                "path": note.path,
                "folder": note.path.split("/")[0] if "/" in note.path else "inbox",
                "status": note.status,
            }
        )

    edges = []
    for conn in conns:
        edges.append(
            {
                "source": f"note_{conn.source_note_id}",
                "target": f"note_{conn.target_note_id}",
                "type": conn.connection_type,
                "confidence": conn.confidence,
                "reason": conn.reason,
            }
        )

    fallback_degrees: dict[str, int] = {n["id"]: 0 for n in nodes}
    for edge in edges:
        fallback_degrees[edge["source"]] = fallback_degrees.get(edge["source"], 0) + 1
        fallback_degrees[edge["target"]] = fallback_degrees.get(edge["target"], 0) + 1

    for node in nodes:
        node["connectionsCount"] = fallback_degrees.get(node["id"], 0)

    orphan_count = 0
    for _node_id, deg in fallback_degrees.items():
        if deg == 0:
            orphan_count += 1

    central = sorted(fallback_degrees.items(), key=lambda x: x[1], reverse=True)[:5]

    return {
        "nodes": nodes,
        "edges": edges,
        "stats": {
            "node_count": len(nodes),
            "edge_count": len(edges),
            "orphan_count": orphan_count,
            "central_nodes": [
                {"id": nid, "degree": deg} for nid, deg in central if deg > 0
            ],
        },
    }


def sync_knowledge_graph(session: Session) -> dict[str, int]:
    notes = list(session.execute(select(NoteRecord)).scalars())
    writer = GraphWriteService(session, autocommit=False)

    node_map: dict[str, int] = {}
    for note in notes:
        node = writer.upsert_node(
            node_type="note",
            label=note.title,
            title=note.title,
            summary=f"Vault note: {note.path}",
            source="note",
            source_id=note.id,
            source_note_ids=[note.id],
            source_evidence=[note.path, note.title],
            status="confirmed",
            graph_metadata={
                "path": note.path,
                "folder": note.path.split("/")[0] if "/" in note.path else "inbox",
            },
        )
        node_map[f"note_{note.id}"] = node.id

    concepts = list(session.execute(select(ConceptRecord)).scalars())
    for c in concepts:
        node = writer.upsert_node(
            node_type="concept",
            label=c.name,
            title=c.name,
            summary=c.description,
            source="concept_extraction",
            source_id=c.id,
            source_note_ids=[
                int(value)
                for value in _parse_json_list(c.related_note_ids)
                if str(value).isdigit()
            ],
            source_evidence=_parse_json_list(c.source_evidence),
            status=c.status if c.status in {"suggested", "confirmed"} else "suggested",
            confidence=c.confidence,
            created_by=c.extracted_by,
            model=c.model,
            provider=c.provider,
            graph_metadata={"description": c.description},
        )
        node_map[f"concept_{c.id}"] = node.id

    conns = list(session.execute(select(ConnectionRecord)).scalars())
    edges_added = 0
    for conn in conns:
        src_key = f"note_{conn.source_note_id}"
        tgt_key = f"note_{conn.target_note_id}"
        if src_key not in node_map or tgt_key not in node_map:
            continue
        evidence = _parse_json_list(conn.evidence)
        writer.upsert_edge(
            source_node_id=node_map[src_key],
            target_node_id=node_map[tgt_key],
            edge_type=conn.connection_type,
            reason=conn.reason or "Persisted relationship between the source notes.",
            evidence=evidence or [f"notes:{conn.source_note_id},{conn.target_note_id}"],
            confidence=conn.confidence / 100 if conn.confidence > 0 else None,
            source_note_ids=[conn.source_note_id, conn.target_note_id],
            created_by="legacy_ai" if conn.created_by == "ai" else conn.created_by,
            model=conn.model,
            provider=conn.provider,
            prompt_version=conn.prompt_version,
            status=conn.status
            if conn.status in {"suggested", "confirmed", "ignored"}
            else "suggested",
        )
        edges_added += 1

    session.commit()
    return {"nodes": len(node_map), "edges_added": edges_added}


def store_embedding(
    session: Session,
    note_id: int,
    content_hash: str,
    vector: list[float],
    model: str,
    chunk_index: int = -1,
    chunk_text: str = "",
    heading_path: str = "",
    start_line: int = 0,
    end_line: int = 0,
    token_count: int = 0,
    provider: str = "",
) -> EmbeddingRecord:
    vector_blob = encode_vector_blob(vector)
    if content_hash:
        for old_chunk in session.execute(
            select(ChunkRecord).where(
                ChunkRecord.note_id == note_id,
                ChunkRecord.content_hash != content_hash,
            )
        ).scalars():
            session.delete(old_chunk)
        for old_embedding in session.execute(
            select(EmbeddingRecord).where(
                EmbeddingRecord.note_id == note_id,
                EmbeddingRecord.content_hash != content_hash,
            )
        ).scalars():
            session.delete(old_embedding)
        session.flush()

    existing = session.execute(
        select(EmbeddingRecord).where(
            EmbeddingRecord.note_id == note_id,
            EmbeddingRecord.content_hash == content_hash,
            EmbeddingRecord.chunk_index == chunk_index,
        )
    ).scalar_one_or_none()

    if existing:
        existing.vector = json.dumps(vector)
        existing.vector_blob = vector_blob
        existing.model = model
        existing.provider = provider
        existing.vector_dimensions = len(vector)
        existing.created_at = datetime.now(UTC)
    else:
        existing = EmbeddingRecord(
            note_id=note_id,
            content_hash=content_hash,
            chunk_index=chunk_index,
            vector=json.dumps(vector),
            vector_blob=vector_blob,
            model=model,
            provider=provider,
            vector_dimensions=len(vector),
        )
        session.add(existing)
        session.flush()

    if chunk_index >= 0:
        chunk = session.execute(
            select(ChunkRecord).where(
                ChunkRecord.note_id == note_id,
                ChunkRecord.content_hash == content_hash,
                ChunkRecord.chunk_index == chunk_index,
            )
        ).scalar_one_or_none()
        if chunk is None:
            chunk = ChunkRecord(
                note_id=note_id,
                note_version=content_hash,
                content_hash=content_hash,
                chunk_index=chunk_index,
            )
            session.add(chunk)
        chunk.heading_path = heading_path
        chunk.text = chunk_text
        chunk.token_count = token_count
        chunk.start_line = start_line
        chunk.end_line = end_line
        chunk.embedding_id = existing.id
        chunk.updated_at = datetime.now(UTC)

    session.commit()
    session.refresh(existing)
    return existing


def find_similar_notes(
    session: Session,
    vector: list[float],
    exclude_note_id: int | None = None,
    limit: int = 10,
) -> list[dict[str, Any]]:
    embeddings = list(session.execute(select(EmbeddingRecord)).scalars())
    results = []
    for emb in embeddings:
        if exclude_note_id and emb.note_id == exclude_note_id:
            continue
        try:
            v = decode_embedding_vector(emb)
        except (json.JSONDecodeError, TypeError, ValueError):
            continue
        if len(v) != len(vector):
            continue
        dot = sum(a * b for a, b in zip(vector, v))
        norm_a = sum(a * a for a in vector) ** 0.5
        norm_b = sum(a * a for a in v) ** 0.5
        if norm_a == 0 or norm_b == 0:
            continue
        sim = dot / (norm_a * norm_b)
        results.append((emb.note_id, sim))

    results.sort(key=lambda x: x[1], reverse=True)
    note_ids = [r[0] for r in results[:limit]]
    notes = {
        note_id: (title, path)
        for note_id, title, path in session.execute(
            select(NoteRecord.id, NoteRecord.title, NoteRecord.path).where(
                NoteRecord.id.in_(note_ids)
            )
        ).all()
    }

    return [
        {
            "note_id": nid,
            "title": notes.get(nid, ("?", "?"))[0],
            "path": notes.get(nid, ("?", "?"))[1],
            "similarity": round(sim, 4),
        }
        for nid, sim in results[:limit]
    ]


def find_similar_chunk_notes(
    session: Session,
    source_note_id: int,
    limit: int = 10,
) -> list[dict[str, Any]]:
    source_embeddings = list(
        session.execute(
            select(EmbeddingRecord).where(EmbeddingRecord.note_id == source_note_id)
        ).scalars()
    )
    if not source_embeddings:
        return []

    source_vectors = []
    for emb in source_embeddings:
        try:
            source_vectors.append(decode_embedding_vector(emb))
        except (json.JSONDecodeError, TypeError, ValueError):
            continue
    if not source_vectors:
        return []

    rows = session.execute(
        select(EmbeddingRecord, ChunkRecord, NoteRecord)
        .join(
            ChunkRecord,
            (ChunkRecord.note_id == EmbeddingRecord.note_id)
            & (ChunkRecord.content_hash == EmbeddingRecord.content_hash)
            & (ChunkRecord.chunk_index == EmbeddingRecord.chunk_index),
        )
        .join(NoteRecord, NoteRecord.id == EmbeddingRecord.note_id)
        .where(EmbeddingRecord.note_id != source_note_id)
    ).all()

    best_by_note: dict[int, dict[str, Any]] = {}
    for emb, chunk, note in rows:
        try:
            target_vector = decode_embedding_vector(emb)
        except (json.JSONDecodeError, TypeError, ValueError):
            continue
        similarities = [
            _cosine_similarity(source_vector, target_vector)
            for source_vector in source_vectors
            if len(source_vector) == len(target_vector)
        ]
        if not similarities:
            continue
        similarity = max(similarities)
        current = best_by_note.get(note.id)
        if current is not None and similarity <= current["similarity"]:
            continue
        best_by_note[note.id] = {
            "note_id": note.id,
            "title": note.title,
            "path": note.path,
            "similarity": round(similarity, 4),
            "updatedAt": note.updated_at.isoformat() if note.updated_at else None,
            "evidence": {
                "chunkIndex": chunk.chunk_index,
                "headingPath": chunk.heading_path,
                "startLine": chunk.start_line,
                "endLine": chunk.end_line,
                "text": chunk.text[:360],
            },
        }

    return sorted(
        best_by_note.values(), key=lambda item: item["similarity"], reverse=True
    )[:limit]


def find_similar_chunks_by_vector(
    session: Session,
    query_vector: list[float],
    limit: int = 10,
    min_similarity: float = 0.15,
) -> list[dict[str, Any]]:
    rows = session.execute(
        select(EmbeddingRecord, ChunkRecord, NoteRecord)
        .join(
            ChunkRecord,
            (ChunkRecord.note_id == EmbeddingRecord.note_id)
            & (ChunkRecord.content_hash == EmbeddingRecord.content_hash)
            & (ChunkRecord.chunk_index == EmbeddingRecord.chunk_index),
        )
        .join(NoteRecord, NoteRecord.id == EmbeddingRecord.note_id)
        .where(NoteRecord.content_hash == EmbeddingRecord.content_hash)
    ).all()

    best_by_note: dict[int, dict[str, Any]] = {}
    for emb, chunk, note in rows:
        try:
            vector = decode_embedding_vector(emb)
        except (json.JSONDecodeError, TypeError, ValueError):
            continue
        if len(vector) != len(query_vector):
            continue
        similarity = _cosine_similarity(query_vector, vector)
        if similarity < min_similarity:
            continue
        current = best_by_note.get(note.id)
        if current is not None and similarity <= current["similarity"]:
            continue
        best_by_note[note.id] = {
            "id": note.id,
            "title": note.title,
            "path": note.path,
            "score": round(1 - similarity, 4),
            "source": "vector_chunk",
            "snippet": chunk.text[:240].replace("\n", " ").strip(),
            "similarity": round(similarity, 4),
            "evidence": {
                "chunkIndex": chunk.chunk_index,
                "contentHash": chunk.content_hash,
                "noteVersion": chunk.note_version,
                "headingPath": chunk.heading_path,
                "startLine": chunk.start_line,
                "endLine": chunk.end_line,
                "text": chunk.text[:360],
            },
        }

    return sorted(best_by_note.values(), key=lambda item: item["score"])[:limit]


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    dot = sum(a * b for a, b in zip(left, right))
    norm_left = sum(a * a for a in left) ** 0.5
    norm_right = sum(a * a for a in right) ** 0.5
    if norm_left == 0 or norm_right == 0:
        return 0.0
    return dot / (norm_left * norm_right)


def encode_vector_blob(vector: list[float]) -> bytes:
    return struct.pack(f"<{len(vector)}f", *[float(value) for value in vector])


def decode_embedding_vector(embedding: EmbeddingRecord) -> list[float]:
    if embedding.vector_blob:
        if len(embedding.vector_blob) % 4 != 0:
            raise ValueError("Invalid vector blob length")
        dimensions = len(embedding.vector_blob) // 4
        return list(struct.unpack(f"<{dimensions}f", embedding.vector_blob))
    return json.loads(embedding.vector)


# ---------------------------------------------------------------------------
# SearxNG web search client
# ---------------------------------------------------------------------------


def searxng_search(query: str, searxng_url: str, max_results: int = 5) -> list[dict]:
    """Search via SearxNG instance. Returns list of {title, url, content}."""
    import httpx

    try:
        resp = httpx.get(
            f"{searxng_url}/search",
            params={"q": query, "format": "json", "categories": "general"},
            timeout=10.0,
        )
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results", [])[:max_results]
        return [
            {
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "content": r.get("content", ""),
            }
            for r in results
        ]
    except Exception:
        return []


def validate_node_with_web(
    session: Session,
    node_id: int,
    searxng_url: str,
) -> dict:
    """Validate a graph node against web sources via SearxNG.

    Creates web source nodes and edges (source_supports, source_contradicts, source_expands).
    Never overwrites local data without recording origin.
    """
    from berrybrain_api.models import GraphNodeRecord

    node = session.get(GraphNodeRecord, node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")

    query = node.label or node.title or ""
    if not query:
        return {"node_id": node_id, "status": "no_query", "results": []}

    writer = GraphWriteService(session, autocommit=False)
    results = searxng_search(query, searxng_url)
    if not results:
        writer.update_node_enrichment(node.id, {"validation_status": "unvalidated"})
        session.commit()
        return {"node_id": node_id, "status": "no_results", "web_results": 0}

    web_node_ids = []
    edge_types_created = []

    for r in results:
        url = r.get("url", "")
        if not url:
            continue
        web_node = next(
            (
                candidate
                for candidate in session.execute(
                    select(GraphNodeRecord).where(
                        GraphNodeRecord.type.in_(("source", "web_source"))
                    )
                ).scalars()
                if url in _parse_json_list(candidate.source_evidence)
                or candidate.source_evidence == url
            ),
            None,
        )
        if web_node is None:
            web_node = writer.upsert_node(
                node_type="source",
                label=r["title"][:255] or url[:255],
                title=r["title"][:255],
                summary=r.get("content", "")[:2000],
                source="web",
                source_id=0,
                status="suggested",
                created_by="system",
                model="searxng",
                provider="searxng",
                source_evidence=[url],
                source_quality="web_validated",
                graph_metadata={"url": url},
            )

        # Determine edge type based on content overlap
        web_content = (r.get("content", "") + " " + r.get("title", "")).lower()
        node_text = (node.label + " " + node.title + " " + node.summary).lower()
        words = set(node_text.split())
        web_words = set(web_content.split())
        overlap = len(words & web_words) / max(len(words), 1)

        if overlap > 0.3:
            edge_type = "source_supports"
        elif any(
            kw in web_content for kw in ["contradicts", "refutes", "incorrect", "false"]
        ):
            edge_type = "source_contradicts"
        else:
            edge_type = "source_expands"

        writer.upsert_edge(
            source_node_id=web_node.id,
            target_node_id=node.id,
            edge_type=edge_type,
            label=f"Web: {r['title'][:100]}",
            reason=(
                f'Web source "{r["title"][:120] or url}" was found for "{query}" '
                f"and classified as {edge_type.replace('_', ' ')}."
            ),
            evidence=[url],
            confidence=overlap,
            source_note_ids=[
                int(value)
                for value in _parse_json_list(node.source_note_ids)
                if str(value).isdigit()
            ],
            status="suggested",
            created_by="system",
            model="searxng",
            provider="searxng",
            prompt_version="web-validation.v1",
        )
        web_node_ids.append(web_node.id)
        edge_types_created.append(edge_type)

    # Determine validation status
    has_supports = "source_supports" in edge_types_created
    has_contradicts = "source_contradicts" in edge_types_created

    validation_status = (
        "conflict_found"
        if has_contradicts
        else "validated"
        if has_supports
        else "needs_review"
    )
    writer.update_node_enrichment(node.id, {"validation_status": validation_status})
    session.commit()

    return {
        "node_id": node_id,
        "validation_status": validation_status,
        "web_results": len(results),
        "web_nodes_created": len(web_node_ids),
        "edge_types": edge_types_created,
    }


# ---------------------------------------------------------------------------
# Graph quality report
# ---------------------------------------------------------------------------
