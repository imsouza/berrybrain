from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any
from urllib.parse import quote_plus

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
    prompt_version: str = "v1",
    reasoning: str = "",
    source_context: str = "",
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
        prompt_version=prompt_version,
        reasoning=reasoning,
        source_context=source_context,
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
    description = getattr(insight, "description", "") or ""
    provider = (getattr(insight, "provider", "") or "").lower()
    model = (getattr(insight, "model", "") or "").lower()
    insight_type = (getattr(insight, "type", "") or "").lower()
    if insight_type in {
        "system_diagnostic",
        "pipeline_bottleneck",
        "provider_issue",
        "job_backlog",
        "worker_status",
    }:
        return False
    evidence = _parse_json_list(getattr(insight, "evidence", "[]"))
    combined = " ".join(
        [
            title,
            description,
            getattr(insight, "why_it_matters", "") or "",
            getattr(insight, "suggested_action", "") or "",
            getattr(insight, "graph_impact", "") or "",
            " ".join(str(item) for item in evidence),
        ]
    ).lower()
    if any(
        term in combined
        for term in (
            "explainedconnections",
            "graphnotes",
            "jobsbytype",
            "generate_note_title",
            "enrich_graph_node",
            "semanticstate",
            "raw json",
            "pipeline bottleneck",
            "jobrecord",
            "pendingjobs",
            "activejobs",
            "failedjobs",
        )
    ):
        return False
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
    has_cognitive_fields = all(
        [
            (getattr(insight, "why_it_matters", "") or "").strip(),
            (getattr(insight, "suggested_action", "") or "").strip(),
            (getattr(insight, "graph_impact", "") or "").strip(),
        ]
    )
    if provider in {"nvidia-nim", "cloud", "ai"}:
        if len(evidence) < 2 or not has_cognitive_fields:
            return False
        if title.strip() == description.strip():
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
                    "aiSummary": getattr(node, "ai_summary", ""),
                    "aiContext": getattr(node, "ai_context", ""),
                    "sourceEvidence": getattr(node, "source_evidence", ""),
                    "learningValue": getattr(node, "learning_value", ""),
                    "sourceQuality": getattr(node, "source_quality", ""),
                    "validationStatus": getattr(
                        node, "validation_status", "unvalidated"
                    ),
                    "provider": getattr(node, "provider", ""),
                    "model": getattr(node, "model", ""),
                    "promptVersion": getattr(node, "prompt_version", ""),
                    "generatedAt": getattr(node, "generated_at", None).isoformat()
                    if getattr(node, "generated_at", None)
                    else None,
                    "path": metadata.get("path", ""),
                    "folder": metadata.get("folder", ""),
                    "metadata": metadata,
                }
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
    from berrybrain_api.models import GraphEdgeRecord, GraphNodeRecord

    node = session.get(GraphNodeRecord, node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")

    query = node.label or node.title or ""
    if not query:
        return {"node_id": node_id, "status": "no_query", "results": []}

    results = searxng_search(query, searxng_url)
    if not results:
        node.validation_status = "unvalidated"
        node.updated_at = datetime.now(UTC)
        session.commit()
        return {"node_id": node_id, "status": "no_results", "web_results": 0}

    web_node_ids = []
    edge_types_created = []

    for r in results:
        url = r.get("url", "")
        if not url:
            continue
        web_node = (
            session.execute(
                select(GraphNodeRecord).where(
                    GraphNodeRecord.type == "web_source",
                    GraphNodeRecord.source_evidence == url,
                )
            )
            .scalars()
            .first()
        )
        if web_node is None:
            web_node = GraphNodeRecord(
                type="web_source",
                label=r["title"][:255] or url[:255],
                title=r["title"][:255],
                summary=r.get("content", "")[:2000],
                source="web",
                source_id=0,
                status="suggested",
                confidence=0.6,
                created_by="system",
                created_by_model="searxng",
                provider="searxng",
                source_evidence=url,
                source_quality="web_validated",
                graph_metadata=json.dumps({"url": url}, ensure_ascii=False),
            )
            session.add(web_node)
            session.flush()

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

        edge = (
            session.execute(
                select(GraphEdgeRecord).where(
                    GraphEdgeRecord.source_node_id == node.id,
                    GraphEdgeRecord.target_node_id == web_node.id,
                    GraphEdgeRecord.type == edge_type,
                )
            )
            .scalars()
            .first()
        )
        if edge is None:
            edge = GraphEdgeRecord(
                source_node_id=node.id,
                target_node_id=web_node.id,
                type=edge_type,
            )
            session.add(edge)
            session.flush()
        edge.label = f"Web: {r['title'][:100]}"
        edge.reason = (
            f'Web source "{r["title"][:120] or url}" was found for "{query}" '
            f"and classified as {edge_type.replace('_', ' ')}."
        )
        edge.evidence = json.dumps([url], ensure_ascii=False)
        edge.confidence = min(0.95, 0.5 + overlap * 0.4)
        edge.status = "suggested"
        edge.created_by = "system"
        edge.created_by_model = "searxng"
        edge.provider = "searxng"
        web_node_ids.append(web_node.id)
        edge_types_created.append(edge_type)

    # Determine validation status
    has_supports = "source_supports" in edge_types_created
    has_contradicts = "source_contradicts" in edge_types_created

    if has_contradicts:
        node.validation_status = "conflict_found"
    elif has_supports:
        node.validation_status = "validated"
    else:
        node.validation_status = "needs_review"

    node.updated_at = datetime.now(UTC)
    session.commit()

    return {
        "node_id": node_id,
        "validation_status": node.validation_status,
        "web_results": len(results),
        "web_nodes_created": len(web_node_ids),
        "edge_types": edge_types_created,
    }


# ---------------------------------------------------------------------------
# Graph quality report
# ---------------------------------------------------------------------------


def graph_quality_report(session: Session) -> dict:
    """Generate a quality report for the knowledge graph."""
    from sqlalchemy import func

    total_nodes = session.query(func.count(GraphNodeRecord.id)).scalar() or 0
    total_edges = session.query(func.count(GraphEdgeRecord.id)).scalar() or 0

    nodes_with_summary = (
        session.query(func.count(GraphNodeRecord.id))
        .filter(GraphNodeRecord.summary.isnot(None), GraphNodeRecord.summary != "")
        .scalar()
        or 0
    )

    nodes_with_evidence = (
        session.query(func.count(GraphNodeRecord.id))
        .filter(
            GraphNodeRecord.source_evidence.isnot(None),
            GraphNodeRecord.source_evidence != "",
        )
        .scalar()
        or 0
    )

    nodes_with_ai_context = (
        session.query(func.count(GraphNodeRecord.id))
        .filter(
            GraphNodeRecord.ai_context.isnot(None), GraphNodeRecord.ai_context != ""
        )
        .scalar()
        or 0
    )
    visible_nodes = total_nodes - (
        session.query(func.count(GraphNodeRecord.id))
        .filter(GraphNodeRecord.status == "ignored")
        .scalar()
        or 0
    )
    visible_nodes_with_summary = (
        session.query(func.count(GraphNodeRecord.id))
        .filter(
            GraphNodeRecord.status != "ignored",
            GraphNodeRecord.summary.isnot(None),
            GraphNodeRecord.summary != "",
        )
        .scalar()
        or 0
    )
    visible_nodes_with_evidence = (
        session.query(func.count(GraphNodeRecord.id))
        .filter(
            GraphNodeRecord.status != "ignored",
            GraphNodeRecord.source_evidence.isnot(None),
            GraphNodeRecord.source_evidence != "",
        )
        .scalar()
        or 0
    )
    visible_nodes_with_ai_context = (
        session.query(func.count(GraphNodeRecord.id))
        .filter(
            GraphNodeRecord.status != "ignored",
            GraphNodeRecord.ai_context.isnot(None),
            GraphNodeRecord.ai_context != "",
        )
        .scalar()
        or 0
    )

    confirmed_nodes = (
        session.query(func.count(GraphNodeRecord.id))
        .filter(GraphNodeRecord.status == "confirmed")
        .scalar()
        or 0
    )

    ignored_nodes = (
        session.query(func.count(GraphNodeRecord.id))
        .filter(GraphNodeRecord.status == "ignored")
        .scalar()
        or 0
    )

    confirmed_edges = (
        session.query(func.count(GraphEdgeRecord.id))
        .filter(GraphEdgeRecord.status == "confirmed")
        .scalar()
        or 0
    )

    ignored_edges = (
        session.query(func.count(GraphEdgeRecord.id))
        .filter(GraphEdgeRecord.status == "ignored")
        .scalar()
        or 0
    )

    nodes_with_reason = (
        session.query(func.count(GraphEdgeRecord.id))
        .filter(GraphEdgeRecord.reason.isnot(None), GraphEdgeRecord.reason != "")
        .scalar()
        or 0
    )

    return {
        "total_nodes": total_nodes,
        "total_edges": total_edges,
        "coverage": {
            "nodes_with_summary": nodes_with_summary,
            "nodes_with_evidence": nodes_with_evidence,
            "nodes_with_ai_context": nodes_with_ai_context,
            "pct_with_summary": round(nodes_with_summary / total_nodes * 100, 1)
            if total_nodes
            else 0,
            "pct_with_evidence": round(nodes_with_evidence / total_nodes * 100, 1)
            if total_nodes
            else 0,
            "pct_with_ai_context": round(nodes_with_ai_context / total_nodes * 100, 1)
            if total_nodes
            else 0,
        },
        "visibleCoverage": {
            "visible_nodes": visible_nodes,
            "nodes_with_summary": visible_nodes_with_summary,
            "nodes_with_evidence": visible_nodes_with_evidence,
            "nodes_with_ai_context": visible_nodes_with_ai_context,
            "pct_with_summary": round(
                visible_nodes_with_summary / visible_nodes * 100, 1
            )
            if visible_nodes
            else 0,
            "pct_with_evidence": round(
                visible_nodes_with_evidence / visible_nodes * 100, 1
            )
            if visible_nodes
            else 0,
            "pct_with_ai_context": round(
                visible_nodes_with_ai_context / visible_nodes * 100, 1
            )
            if visible_nodes
            else 0,
        },
        "status": {
            "confirmed_nodes": confirmed_nodes,
            "ignored_nodes": ignored_nodes,
            "pending_nodes": total_nodes - confirmed_nodes - ignored_nodes,
            "confirmed_edges": confirmed_edges,
            "ignored_edges": ignored_edges,
            "pending_edges": total_edges - confirmed_edges - ignored_edges,
        },
        "edges_with_reason": nodes_with_reason,
        "pct_edges_with_reason": round(nodes_with_reason / total_edges * 100, 1)
        if total_edges
        else 0,
    }


def _filter_nodes_by_view(nodes: list[dict], view: str) -> list[dict]:
    """Filter nodes based on view parameter.

    Default (empty view): hide headings, topics without context, system nodes without enrichment.
    Views:
    - enriched: nodes with aiContext or aiSummary
    - raw: nodes without aiContext (system/content-based)
    - validated: nodes with validationStatus=validated
    - needs_review: nodes with validationStatus=needs_review or conflict_found
    - hidden: nodes with status=ignored or type=heading
    """
    view_lower = view.lower()

    if view_lower == "enriched":
        return [n for n in nodes if n.get("aiContext") or n.get("aiSummary")]

    if view_lower == "raw":
        return [n for n in nodes if not n.get("aiContext") and not n.get("aiSummary")]

    if view_lower == "validated":
        return [n for n in nodes if n.get("validationStatus") == "validated"]

    if view_lower == "needs_review":
        return [
            n
            for n in nodes
            if n.get("validationStatus") in ("needs_review", "conflict_found")
        ]

    if view_lower == "hidden":
        return [
            n
            for n in nodes
            if n.get("status") == "ignored" or n.get("type") == "heading"
        ]

    # Default Brain View: hide low-quality nodes
    return [
        n
        for n in nodes
        if not (
            n.get("type") == "heading"
            or n.get("status") == "ignored"
            or (
                n.get("type") in ("topico", "topic")
                and not n.get("aiContext")
                and not n.get("aiSummary")
            )
            or (
                n.get("source") in ("content", "system")
                and not n.get("aiContext")
                and not n.get("aiSummary")
                and not n.get("sourceEvidence")
            )
        )
    ]
