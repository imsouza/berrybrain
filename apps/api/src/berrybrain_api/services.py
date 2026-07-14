from __future__ import annotations

import json
import hashlib
import math
import re
import struct
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from berrybrain_api.models import (
    ChunkRecord,
    ConceptRecord,
    ConnectionRecord,
    EmbeddingRecord,
    GraphEdgeRecord,
    GraphNodeRecord,
    InsightRecord,
    NoteRecord,
)
from berrybrain_api.graph_write_service import GraphWriteService

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
    related = related_notes or []
    source_evidence = evidence or []
    diagnostic_types = {
        "system_diagnostic",
        "pipeline_bottleneck",
        "provider_issue",
        "job_backlog",
        "worker_status",
    }
    if insight_type not in diagnostic_types:
        missing = []
        if not source_evidence:
            missing.append("evidence")
        if not why_it_matters.strip():
            missing.append("why_it_matters")
        if not suggested_action.strip():
            missing.append("suggested_action")
        if not graph_impact.strip():
            missing.append("graph_impact")
        if missing:
            raise HTTPException(
                status_code=422,
                detail="Knowledge insight is incomplete: " + ", ".join(missing),
            )
    fingerprint = insight_fingerprint(
        insight_type,
        title,
        related,
        source_evidence,
    )
    existing = session.execute(
        select(InsightRecord).where(
            InsightRecord.fingerprint == fingerprint,
            InsightRecord.status.not_in(("dismissed", "expired")),
        )
    ).scalar_one_or_none()
    quality_score = score_insight_quality(
        title=title,
        description=description,
        why_it_matters=why_it_matters,
        evidence=source_evidence,
        suggested_action=suggested_action,
        graph_impact=graph_impact,
        confidence=confidence,
    )
    adjusted_priority = max(0, priority - (2 if quality_score < 0.5 else 0))
    adjusted_confidence = min(confidence, max(0.2, quality_score + 0.15))
    now = datetime.now(UTC)
    if existing is not None:
        existing.title = title
        existing.description = description
        existing.related_notes = json.dumps(related, ensure_ascii=False)
        existing.priority = max(existing.priority, adjusted_priority)
        existing.why_it_matters = why_it_matters
        existing.evidence = json.dumps(source_evidence, ensure_ascii=False)
        existing.suggested_action = suggested_action
        existing.graph_impact = graph_impact
        existing.confidence = max(existing.confidence, adjusted_confidence)
        existing.provider = provider or existing.provider
        existing.model = model or existing.model
        existing.prompt_version = prompt_version or existing.prompt_version
        existing.reasoning = reasoning or existing.reasoning
        existing.source_context = source_context or existing.source_context
        existing.quality_score = max(existing.quality_score, quality_score)
        existing.last_recalculated_at = now
        existing.expires_at = now + timedelta(days=30)
        existing.updated_at = now
        session.commit()
        session.refresh(existing)
        return existing

    insight = InsightRecord(
        type=insight_type,
        title=title,
        description=description,
        related_notes=json.dumps(related, ensure_ascii=False),
        priority=adjusted_priority,
        why_it_matters=why_it_matters,
        evidence=json.dumps(source_evidence, ensure_ascii=False),
        suggested_action=suggested_action,
        graph_impact=graph_impact,
        confidence=adjusted_confidence,
        status=status,
        provider=provider,
        model=model,
        prompt_version=prompt_version,
        reasoning=reasoning,
        source_context=source_context,
        fingerprint=fingerprint,
        quality_score=quality_score,
        expires_at=now + timedelta(days=30),
        last_recalculated_at=now,
    )
    session.add(insight)
    session.commit()
    session.refresh(insight)
    return insight


def insight_fingerprint(
    insight_type: str,
    title: str,
    related_notes: list[int],
    evidence: list[Any],
) -> str:
    normalized_evidence = sorted(
        {
            json.dumps(item, ensure_ascii=False, sort_keys=True).strip().lower()
            for item in evidence
            if str(item).strip()
        }
    )
    title_tokens = sorted(
        {
            token
            for token in re.findall(r"[\w-]+", title.lower(), flags=re.UNICODE)
            if len(token) > 2
        }
    )
    payload = {
        "type": insight_type.strip().lower(),
        "notes": sorted(set(related_notes)),
        "evidence": normalized_evidence,
        "title": [] if normalized_evidence else title_tokens,
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()


def score_insight_quality(
    *,
    title: str,
    description: str,
    why_it_matters: str,
    evidence: list[Any],
    suggested_action: str,
    graph_impact: str,
    confidence: float,
) -> float:
    score = 0.0
    score += 0.15 if len(title.strip()) >= 12 else 0.03
    score += 0.15 if len(description.strip()) >= 50 else 0.04
    score += 0.15 if len(why_it_matters.strip()) >= 30 else 0.0
    score += 0.20 if len(evidence) >= 2 else (0.10 if evidence else 0.0)
    score += 0.10 if len(suggested_action.strip()) >= 15 else 0.0
    score += 0.10 if len(graph_impact.strip()) >= 15 else 0.0
    score += 0.15 * max(0.0, min(1.0, confidence))
    generic = {
        "connection found",
        "new insight",
        "interesting concept",
        "knowledge gap",
        "related notes",
    }
    if title.strip().lower() in generic:
        score -= 0.40
    return round(max(0.0, min(1.0, score)), 4)


def migrate_legacy_insights(session: Session) -> dict[str, int]:
    """Archive unsupported legacy insights and backfill metadata on grounded ones."""
    now = datetime.now(UTC)
    archived = 0
    upgraded = 0
    for insight in session.execute(select(InsightRecord)).scalars():
        if insight.status in {"archived", "dismissed", "expired"}:
            continue
        evidence = _parse_json_list(insight.evidence)
        related_notes = [
            int(value)
            for value in _parse_json_list(insight.related_notes)
            if str(value).isdigit()
        ]
        has_cognitive_fields = all(
            str(value or "").strip()
            for value in (
                insight.description,
                insight.why_it_matters,
                insight.suggested_action,
                insight.graph_impact,
            )
        )
        if (
            not evidence
            or not related_notes
            or not has_cognitive_fields
            or not _is_visible_insight(insight)
        ):
            insight.status = "archived"
            insight.dismissed_at = insight.dismissed_at or now
            insight.updated_at = now
            archived += 1
            continue
        fingerprint = insight_fingerprint(
            insight.type,
            insight.title,
            related_notes,
            evidence,
        )
        quality = score_insight_quality(
            title=insight.title,
            description=insight.description,
            why_it_matters=insight.why_it_matters,
            evidence=evidence,
            suggested_action=insight.suggested_action,
            graph_impact=insight.graph_impact,
            confidence=insight.confidence,
        )
        changed = False
        if not insight.fingerprint:
            insight.fingerprint = fingerprint
            changed = True
        if not insight.quality_score:
            insight.quality_score = quality
            changed = True
        if insight.expires_at is None and insight.status in {"suggested", "reviewed"}:
            insight.expires_at = now + timedelta(days=30)
            changed = True
        if changed:
            insight.last_recalculated_at = now
            insight.updated_at = now
            upgraded += 1
    if archived or upgraded:
        session.commit()
    return {"archived": archived, "upgraded": upgraded}


def get_active_insights(
    session: Session,
    limit: int = 20,
) -> list[InsightRecord]:
    migrate_legacy_insights(session)
    now = datetime.now(UTC)
    expired = list(
        session.execute(
            select(InsightRecord).where(
                InsightRecord.expires_at.is_not(None),
                InsightRecord.expires_at <= now,
                InsightRecord.status.in_(("suggested", "reviewed")),
            )
        ).scalars()
    )
    for insight in expired:
        insight.status = "expired"
        insight.updated_at = now
    if expired:
        session.commit()
    insights = list(
        session.execute(
            select(InsightRecord)
            .where(InsightRecord.dismissed_at.is_(None))
            .where(
                InsightRecord.status.not_in(
                    ("expired", "archived", "dismissed", "ignored")
                )
            )
            .order_by(
                InsightRecord.feedback_score.desc(),
                InsightRecord.quality_score.desc(),
                InsightRecord.priority.desc(),
                InsightRecord.created_at.desc(),
            )
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
    insight.ignored_at = datetime.now(UTC)
    insight.status = "dismissed"
    insight.feedback_score -= 1
    insight.updated_at = datetime.now(UTC)
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
        "fingerprint": getattr(insight, "fingerprint", ""),
        "qualityScore": getattr(insight, "quality_score", 0.0),
        "feedbackScore": getattr(insight, "feedback_score", 0),
        "expiresAt": insight.expires_at.isoformat()
        if getattr(insight, "expires_at", None)
        else None,
        "lastRecalculatedAt": insight.last_recalculated_at.isoformat()
        if getattr(insight, "last_recalculated_at", None)
        else None,
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
            confidence=1.0,
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
            confidence=conn.confidence / 100 if conn.confidence else 0.5,
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
                confidence=0.6,
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
            source_node_id=node.id,
            target_node_id=web_node.id,
            edge_type=edge_type,
            label=f"Web: {r['title'][:100]}",
            reason=(
                f'Web source "{r["title"][:120] or url}" was found for "{query}" '
                f"and classified as {edge_type.replace('_', ' ')}."
            ),
            evidence=[url],
            confidence=min(0.95, 0.5 + overlap * 0.4),
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

    visible_node_rows = list(
        session.execute(
            select(GraphNodeRecord).where(
                GraphNodeRecord.status.not_in(("ignored", "archived"))
            )
        ).scalars()
    )
    visible_edge_rows = list(
        session.execute(
            select(GraphEdgeRecord).where(
                GraphEdgeRecord.status.not_in(("ignored", "archived"))
            )
        ).scalars()
    )
    degree = {node.id: 0 for node in visible_node_rows}
    for edge in visible_edge_rows:
        if edge.source_node_id in degree:
            degree[edge.source_node_id] += 1
        if edge.target_node_id in degree:
            degree[edge.target_node_id] += 1

    from berrybrain_api.graph_write_service import (
        SYMMETRIC_EDGE_TYPES,
        canonical_edge_type,
        has_traceable_ai_evidence,
        normalize_graph_label,
    )

    node_groups: dict[tuple[str, str], list[GraphNodeRecord]] = {}
    for node in visible_node_rows:
        key = (node.type, normalize_graph_label(node.label or ""))
        if key[1]:
            node_groups.setdefault(key, []).append(node)
    duplicate_nodes = [
        {
            "type": key[0],
            "normalizedLabel": key[1],
            "nodeIds": [node.id for node in group],
            "labels": [node.label for node in group],
        }
        for key, group in node_groups.items()
        if len(group) > 1
    ]

    edge_groups: dict[tuple[int, int, str], list[GraphEdgeRecord]] = {}
    for edge in visible_edge_rows:
        try:
            edge_type = canonical_edge_type(edge.type)
        except HTTPException:
            edge_type = edge.type
        source_id, target_id = edge.source_node_id, edge.target_node_id
        if edge_type in SYMMETRIC_EDGE_TYPES and source_id > target_id:
            source_id, target_id = target_id, source_id
        edge_groups.setdefault((source_id, target_id, edge_type), []).append(edge)
    duplicate_edges = [
        {
            "sourceNodeId": key[0],
            "targetNodeId": key[1],
            "type": key[2],
            "edgeIds": [edge.id for edge in group],
        }
        for key, group in edge_groups.items()
        if len(group) > 1
    ]

    generic_labels = {
        "general",
        "misc",
        "notes",
        "other",
        "rascunho",
        "study",
        "topic",
        "untitled",
    }
    generic_nodes = [
        {"id": node.id, "label": node.label, "type": node.type}
        for node in visible_node_rows
        if len(normalize_graph_label(node.label or "")) < 3
        or normalize_graph_label(node.label or "") in generic_labels
    ]
    orphan_nodes = [
        {"id": node.id, "label": node.label, "type": node.type}
        for node in visible_node_rows
        if degree.get(node.id, 0) == 0
    ]
    hub_threshold = max(8, math.ceil(max(1, len(visible_node_rows)) * 0.25))
    artificial_hubs = [
        {
            "id": node.id,
            "label": node.label,
            "type": node.type,
            "degree": degree.get(node.id, 0),
            "threshold": hub_threshold,
        }
        for node in visible_node_rows
        if degree.get(node.id, 0) > hub_threshold
        and (node.created_by in {"system", "ai"} or node.type != "note")
    ]
    edges_without_evidence = []
    for edge in visible_edge_rows:
        try:
            evidence = json.loads(edge.evidence or "[]")
        except (json.JSONDecodeError, TypeError):
            evidence = []
        if not edge.reason.strip() or not isinstance(evidence, list) or not evidence:
            edges_without_evidence.append(
                {
                    "id": edge.id,
                    "sourceNodeId": edge.source_node_id,
                    "targetNodeId": edge.target_node_id,
                    "type": edge.type,
                    "missingReason": not edge.reason.strip(),
                    "missingEvidence": not evidence,
                }
            )
    ai_edges_without_traceable_evidence = [
        {
            "id": edge.id,
            "sourceNodeId": edge.source_node_id,
            "targetNodeId": edge.target_node_id,
            "type": edge.type,
        }
        for edge in visible_edge_rows
        if edge.created_by == "ai" and not has_traceable_ai_evidence(edge)
    ]
    unstable_clusters = [
        {"id": node.id, "label": node.label, "degree": degree.get(node.id, 0)}
        for node in visible_node_rows
        if node.type == "cluster" and degree.get(node.id, 0) < 2
    ]

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
        "issues": {
            "orphans": orphan_nodes,
            "duplicateNodes": duplicate_nodes,
            "duplicateEdges": duplicate_edges,
            "artificialHubs": artificial_hubs,
            "genericNodes": generic_nodes,
            "edgesWithoutEvidence": edges_without_evidence,
            "aiEdgesWithoutTraceableEvidence": ai_edges_without_traceable_evidence,
            "unstableClusters": unstable_clusters,
            "mergeSuggestions": duplicate_nodes,
        },
        "issueCounts": {
            "orphans": len(orphan_nodes),
            "duplicateNodes": len(duplicate_nodes),
            "duplicateEdges": len(duplicate_edges),
            "artificialHubs": len(artificial_hubs),
            "genericNodes": len(generic_nodes),
            "edgesWithoutEvidence": len(edges_without_evidence),
            "aiEdgesWithoutTraceableEvidence": len(ai_edges_without_traceable_evidence),
            "unstableClusters": len(unstable_clusters),
        },
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
