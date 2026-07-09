from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from berrybrain_api.models import (
    ConceptRecord,
    ConnectionRecord,
    EmbeddingRecord,
    GraphEdgeRecord,
    GraphNodeRecord,
    InsightRecord,
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
    "review_opportunity",
}

VALID_REVIEW_RESULTS = {"correct", "wrong", "hard"}


def create_connection(
    session: Session,
    source_note_id: int,
    target_note_id: int,
    connection_type: str,
    confidence: int = 0,
    reason: str = "",
    created_by: str = "system",
    evidence: list[str] | None = None,
    provider: str = "",
    model: str = "",
    prompt_version: str = "",
    status: str = "suggested",
) -> ConnectionRecord:
    conn = ConnectionRecord(
        source_note_id=source_note_id,
        target_note_id=target_note_id,
        connection_type=connection_type,
        confidence=confidence,
        reason=reason,
        evidence=json.dumps(evidence or [], ensure_ascii=False),
        created_by=created_by,
        provider=provider,
        model=model,
        prompt_version=prompt_version,
        status=status,
    )
    session.add(conn)
    session.commit()
    session.refresh(conn)
    return conn


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


def create_insight(
    session: Session,
    insight_type: str,
    title: str,
    description: str = "",
    related_notes: list[int] | None = None,
    priority: int = 0,
    why_it_matters: str = "",
    evidence: list[str] | None = None,
    suggested_action: str = "",
    graph_impact: str = "",
    confidence: float = 0.5,
    status: str = "suggested",
    provider: str = "",
    model: str = "",
) -> InsightRecord:
    insight = InsightRecord(
        type=insight_type,
        title=title,
        description=description,
        related_notes=json.dumps(related_notes or [], ensure_ascii=False),
        priority=priority,
        why_it_matters=why_it_matters,
        evidence=json.dumps(evidence or [], ensure_ascii=False),
        suggested_action=suggested_action,
        graph_impact=graph_impact,
        confidence=confidence,
        status=status,
        provider=provider,
        model=model,
    )
    session.add(insight)
    session.commit()
    session.refresh(insight)
    return insight


def get_active_insights(
    session: Session,
    limit: int = 20,
) -> list[InsightRecord]:
    insights = list(
        session.execute(
            select(InsightRecord)
            .where(InsightRecord.dismissed_at.is_(None))
            .order_by(InsightRecord.priority.desc(), InsightRecord.created_at.desc())
            .limit(limit * 3)
        ).scalars()
    )
    return [insight for insight in insights if _is_visible_insight(insight)][:limit]


def _is_visible_insight(insight: InsightRecord) -> bool:
    title = insight.title or ""
    provider = (getattr(insight, "provider", "") or "").lower()
    model = (getattr(insight, "model", "") or "").lower()
    legacy_prefixes = (
        "Nó central no grafo:",
        "No central no grafo:",
        "Conceito recorrente:",
        "Lacuna detectada:",
    )
    if title.startswith(legacy_prefixes) and provider in {
        "",
        "system",
        "deterministic",
    }:
        return False
    if model == "graph-insight.v1" and provider in {"", "system", "deterministic"}:
        return False
    return True


def dismiss_insight(session: Session, insight_id: int) -> InsightRecord:
    insight = session.get(InsightRecord, insight_id)
    if insight is None:
        raise HTTPException(status_code=404, detail="Insight not found")
    insight.dismissed_at = datetime.now(UTC)
    session.commit()
    session.refresh(insight)
    return insight


def serialize_insight(insight: InsightRecord) -> dict[str, Any]:
    try:
        related = json.loads(insight.related_notes)
    except json.JSONDecodeError:
        related = []
    return {
        "id": insight.id,
        "type": insight.type,
        "title": insight.title,
        "description": insight.description,
        "relatedNotes": related,
        "priority": insight.priority,
        "whyItMatters": getattr(insight, "why_it_matters", ""),
        "evidence": _parse_json_list(getattr(insight, "evidence", "[]")),
        "suggestedAction": getattr(insight, "suggested_action", ""),
        "graphImpact": getattr(insight, "graph_impact", ""),
        "confidence": getattr(insight, "confidence", 0.5),
        "status": getattr(insight, "status", "suggested"),
        "provider": getattr(insight, "provider", ""),
        "model": getattr(insight, "model", ""),
        "promptVersion": getattr(insight, "prompt_version", "v1"),
        "reasoning": getattr(insight, "reasoning", ""),
        "sourceContext": getattr(insight, "source_context", ""),
        "appliedAt": insight.applied_at.isoformat() if insight.applied_at else None,
        "ignoredAt": insight.ignored_at.isoformat() if insight.ignored_at else None,
        "createdAt": insight.created_at.isoformat() if insight.created_at else None,
        "updatedAt": insight.updated_at.isoformat()
        if getattr(insight, "updated_at", None)
        else None,
        "dismissedAt": insight.dismissed_at.isoformat()
        if insight.dismissed_at
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


def resolve_note_id(session: Session, note_path: str) -> int:
    note = session.execute(
        select(NoteRecord).where(NoteRecord.path == note_path)
    ).scalar_one_or_none()
    if note is None:
        raise HTTPException(status_code=404, detail="Note not found")
    return note.id


def build_graph(
    session: Session,
    max_depth: int = 2,
) -> dict[str, list[dict]]:
    from berrybrain_api.second_brain import _merge_duplicate_nodes

    _merge_duplicate_nodes(session)

    graph_nodes = list(session.execute(select(GraphNodeRecord)).scalars())
    if graph_nodes:
        graph_edges = list(
            session.execute(
                select(GraphEdgeRecord).where(GraphEdgeRecord.status != "ignored")
            ).scalars()
        )
        node_ids = {node.id: f"{node.type}_{node.id}" for node in graph_nodes}
        nodes = []
        for node in graph_nodes:
            metadata = _parse_json_dict(getattr(node, "graph_metadata", "{}"))
            nodes.append(
                {
                    "id": node_ids[node.id],
                    "recordId": node.id,
                    "label": node.label,
                    "title": getattr(node, "title", "") or node.label,
                    "summary": getattr(node, "summary", ""),
                    "aiNotes": getattr(node, "ai_notes", ""),
                    "userNotes": getattr(node, "user_notes", ""),
                    "type": node.type,
                    "source": getattr(node, "source", ""),
                    "sourceId": node.source_id,
                    "sourceNoteIds": _parse_json_list(
                        getattr(node, "source_note_ids", "[]")
                    ),
                    "status": getattr(node, "status", "suggested"),
                    "confidence": getattr(node, "confidence", 0.5),
                    "createdBy": getattr(node, "created_by", "system"),
                    "createdByModel": getattr(node, "created_by_model", ""),
                    "path": metadata.get("path", ""),
                    "folder": metadata.get("folder", ""),
                    "metadata": metadata,
                }
            )

        edges = []
        degrees: dict[str, int] = {node["id"]: 0 for node in nodes}
        for edge in graph_edges:
            source = node_ids.get(edge.source_node_id)
            target = node_ids.get(edge.target_node_id)
            if source is None or target is None:
                continue
            edges.append(
                {
                    "id": edge.id,
                    "source": source,
                    "target": target,
                    "type": edge.type,
                    "label": getattr(edge, "label", ""),
                    "confidence": edge.confidence,
                    "reason": edge.reason,
                    "evidence": _parse_json_list(getattr(edge, "evidence", "[]")),
                    "aiNotes": getattr(edge, "ai_notes", ""),
                    "userNotes": getattr(edge, "user_notes", ""),
                    "sourceNoteIds": _parse_json_list(
                        getattr(edge, "source_note_ids", "[]")
                    ),
                    "createdBy": edge.created_by,
                    "provider": getattr(edge, "provider", ""),
                    "model": getattr(edge, "model", ""),
                    "status": getattr(edge, "status", "suggested"),
                }
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

    node_ids = {n["id"] for n in nodes}
    degrees: dict[str, int] = {n["id"]: 0 for n in nodes}
    for edge in edges:
        degrees[edge["source"]] = degrees.get(edge["source"], 0) + 1
        degrees[edge["target"]] = degrees.get(edge["target"], 0) + 1

    for node in nodes:
        node["connectionsCount"] = degrees.get(node["id"], 0)

    orphan_count = 0
    for node_id, deg in degrees.items():
        if deg == 0:
            orphan_count += 1

    central = sorted(degrees.items(), key=lambda x: x[1], reverse=True)[:5]

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

    node_map: dict[str, int] = {}
    for note in notes:
        existing = session.execute(
            select(GraphNodeRecord).where(
                GraphNodeRecord.type == "note",
                GraphNodeRecord.source_id == note.id,
            )
        ).scalar_one_or_none()
        if existing:
            existing.label = note.title
            node_map[f"note_{note.id}"] = existing.id
        else:
            node = GraphNodeRecord(
                type="note",
                label=note.title,
                source_id=note.id,
                graph_metadata=json.dumps(
                    {
                        "path": note.path,
                        "folder": note.path.split("/")[0]
                        if "/" in note.path
                        else "inbox",
                    }
                ),
            )
            session.add(node)
            session.flush()
            node_map[f"note_{note.id}"] = node.id

    concepts = list(session.execute(select(ConceptRecord)).scalars())
    for c in concepts:
        existing = session.execute(
            select(GraphNodeRecord).where(
                GraphNodeRecord.type == "concept",
                GraphNodeRecord.source_id == c.id,
            )
        ).scalar_one_or_none()
        if existing is None:
            cross = session.execute(
                select(GraphNodeRecord).where(
                    GraphNodeRecord.type != "note",
                    GraphNodeRecord.type != "insight",
                    GraphNodeRecord.label == c.name,
                )
            ).scalar_one_or_none()
            if cross is None:
                from berrybrain_api.second_brain import normalize_concept_name

                all_nodes = session.execute(
                    select(GraphNodeRecord).where(
                        GraphNodeRecord.type != "note",
                        GraphNodeRecord.type != "insight",
                    )
                ).scalars()
                norm = normalize_concept_name(c.name)
                cross = next(
                    (
                        n
                        for n in all_nodes
                        if normalize_concept_name(n.label or "") == norm
                    ),
                    None,
                )
            existing = cross
        if existing:
            existing.label = c.name or existing.label
            node_map[f"concept_{c.id}"] = existing.id
        else:
            node = GraphNodeRecord(
                type="concept",
                label=c.name,
                source_id=c.id,
                graph_metadata=json.dumps({"description": c.description}),
            )
            session.add(node)
            session.flush()
            node_map[f"concept_{c.id}"] = node.id

    conns = list(session.execute(select(ConnectionRecord)).scalars())
    edges_added = 0
    for conn in conns:
        src_key = f"note_{conn.source_note_id}"
        tgt_key = f"note_{conn.target_note_id}"
        if src_key not in node_map or tgt_key not in node_map:
            continue
        existing = session.execute(
            select(GraphEdgeRecord).where(
                GraphEdgeRecord.source_node_id == node_map[src_key],
                GraphEdgeRecord.target_node_id == node_map[tgt_key],
                GraphEdgeRecord.type == conn.connection_type,
            )
        ).scalar_one_or_none()
        if not existing:
            edge = GraphEdgeRecord(
                source_node_id=node_map[src_key],
                target_node_id=node_map[tgt_key],
                type=conn.connection_type,
                confidence=conn.confidence / 100 if conn.confidence else 0.5,
                reason=conn.reason,
                created_by=conn.created_by,
            )
            session.add(edge)
            edges_added += 1

    session.commit()
    return {"nodes": len(node_map), "edges_added": edges_added}


def store_embedding(
    session: Session,
    note_id: int,
    content_hash: str,
    vector: list[float],
    model: str,
) -> EmbeddingRecord:
    import json

    existing = session.execute(
        select(EmbeddingRecord).where(
            EmbeddingRecord.note_id == note_id,
            EmbeddingRecord.content_hash == content_hash,
        )
    ).scalar_one_or_none()

    if existing:
        existing.vector = json.dumps(vector)
        existing.model = model
        existing.created_at = datetime.now(UTC)
    else:
        existing = EmbeddingRecord(
            note_id=note_id,
            content_hash=content_hash,
            vector=json.dumps(vector),
            model=model,
        )
        session.add(existing)

    session.commit()
    return existing


def find_similar_notes(
    session: Session,
    vector: list[float],
    exclude_note_id: int | None = None,
    limit: int = 10,
) -> list[dict[str, Any]]:
    import json

    embeddings = list(session.execute(select(EmbeddingRecord)).scalars())
    results = []
    for emb in embeddings:
        if exclude_note_id and emb.note_id == exclude_note_id:
            continue
        try:
            v = json.loads(emb.vector)
        except (json.JSONDecodeError, TypeError):
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
    notes = dict(
        session.execute(
            select(NoteRecord.id, NoteRecord.title, NoteRecord.path).where(
                NoteRecord.id.in_(note_ids)
            )
        ).all()
    )

    return [
        {
            "note_id": nid,
            "title": notes.get(nid, ("?", "?"))[0],
            "path": notes.get(nid, ("?", "?"))[1],
            "similarity": round(sim, 4),
        }
        for nid, sim in results[:limit]
    ]
