from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from berrybrain_api.confidence import (
    ConfidenceSignal,
    estimate_confidence,
    persist_confidence,
)
from berrybrain_api.graph_contracts import canonical_edge_type, canonical_node_type
from berrybrain_api.graph_ontology import (
    canonical_label,
    ontology_class,
    ontology_property,
    validate_edge_types,
    validate_node_name,
)
from berrybrain_api.models import (
    GraphEdgeRecord,
    GraphNodeRecord,
    GraphSemanticCandidateRecord,
)


def audit_graph_semantics(session: Session, *, apply: bool = False) -> dict[str, Any]:
    nodes = list(
        session.execute(select(GraphNodeRecord).order_by(GraphNodeRecord.id)).scalars()
    )
    edges = list(
        session.execute(select(GraphEdgeRecord).order_by(GraphEdgeRecord.id)).scalars()
    )
    node_by_id = {node.id: node for node in nodes}
    invalid_node_ids: set[int] = set()
    result: dict[str, Any] = {
        "apply": apply,
        "nodes": {"active": 0, "quarantined": 0},
        "edges": {"active": 0, "quarantined": 0, "retyped": 0, "reversed": 0},
        "issues": [],
    }

    for node in nodes:
        try:
            node_type = canonical_node_type(node.type)
            issues = validate_node_name(node_type, node.label)
        except HTTPException as exc:
            node_type = node.type
            issues = [str(exc.detail)]
        if issues:
            invalid_node_ids.add(node.id)
            result["nodes"]["quarantined"] += 1
            result["issues"].append({"kind": "node", "id": node.id, "issues": issues})
            if apply:
                node.semantic_status = "quarantined"
                _record_candidate(
                    session,
                    "node",
                    node.id,
                    node_type,
                    node.label,
                    issues,
                    _node_payload(node),
                )
            continue
        result["nodes"]["active"] += 1
        if apply:
            node.type = node_type
            node.semantic_status = "active"
            node.ontology_class = ontology_class(node_type)
            node.canonical_label = canonical_label(node.label).casefold()
            signals = [
                ConfidenceSignal(1.0, f"source-note:{note_id}")
                for note_id in _json_list(node.source_note_ids)
                if isinstance(note_id, int)
            ]
            if node.quality_score > 0:
                signals.append(
                    ConfidenceSignal(node.quality_score, "judge:quality-score")
                )
            persist_confidence(node, estimate_confidence(signals))

    for edge in edges:
        source = node_by_id.get(edge.source_node_id)
        target = node_by_id.get(edge.target_node_id)
        if source is None or target is None:
            issues = ["Edge endpoint is missing."]
            edge_type = edge.type
            reverse = False
        else:
            edge_type, reverse = _infer_edge_contract(edge, source, target)
            if reverse:
                source, target = target, source
            issues = validate_edge_types(
                edge_type,
                canonical_node_type(source.type),
                canonical_node_type(target.type),
            )
            if (
                source.id in invalid_node_ids
                or target.id in invalid_node_ids
                or source.semantic_status != "active"
                or target.semantic_status != "active"
            ):
                issues.append("Edge references a quarantined node.")
        if issues:
            result["edges"]["quarantined"] += 1
            result["issues"].append({"kind": "edge", "id": edge.id, "issues": issues})
            if apply:
                edge.semantic_status = "quarantined"
                _record_candidate(
                    session,
                    "edge",
                    edge.id,
                    edge_type,
                    edge.label,
                    issues,
                    _edge_payload(edge),
                )
            continue
        result["edges"]["active"] += 1
        result["edges"]["retyped"] += int(edge.type != edge_type)
        result["edges"]["reversed"] += int(reverse)
        if apply:
            if reverse:
                edge.source_node_id, edge.target_node_id = (
                    edge.target_node_id,
                    edge.source_node_id,
                )
            edge.type = edge_type
            edge.semantic_status = "active"
            edge.ontology_property = ontology_property(edge_type)
            signals = [
                ConfidenceSignal(1.0, f"edge-evidence:{index}:{_stable_evidence(item)}")
                for index, item in enumerate(_json_list(edge.evidence))
            ]
            if edge.quality_score > 0:
                signals.append(
                    ConfidenceSignal(edge.quality_score, "judge:quality-score")
                )
            persist_confidence(edge, estimate_confidence(signals))

    from berrybrain_api.services import audit_knowledge_confidence

    if apply:
        from berrybrain_api.graph_write_service import GraphWriteService

        result["edges"]["deduplicated"] = GraphWriteService(
            session, autocommit=False
        ).deduplicate_edges()
        result["knowledgeConfidence"] = audit_knowledge_confidence(session, apply=True)
        session.commit()
    else:
        result["knowledgeConfidence"] = audit_knowledge_confidence(session, apply=False)
    return result


def list_semantic_candidates(
    session: Session, status: str = "pending"
) -> list[dict[str, Any]]:
    records = list(
        session.execute(
            select(GraphSemanticCandidateRecord)
            .where(GraphSemanticCandidateRecord.status == status)
            .order_by(GraphSemanticCandidateRecord.id.desc())
        ).scalars()
    )
    return [
        {
            "id": item.id,
            "kind": item.candidate_kind,
            "sourceRecordId": item.source_record_id,
            "proposedType": item.proposed_type,
            "proposedLabel": item.proposed_label,
            "reason": item.reason,
            "payload": _json_object(item.payload_json),
            "status": item.status,
        }
        for item in records
    ]


def quarantine_generated_candidate(
    session: Session,
    *,
    kind: str,
    proposed_type: str,
    proposed_label: str,
    issues: list[str],
    payload: dict[str, Any],
) -> None:
    session.add(
        GraphSemanticCandidateRecord(
            candidate_kind=kind,
            proposed_type=proposed_type,
            proposed_label=proposed_label,
            reason=" ".join(issues),
            payload_json=json.dumps(payload, ensure_ascii=False),
        )
    )


def resolve_semantic_candidate(
    session: Session, candidate_id: int, action: str
) -> dict[str, Any]:
    candidate = session.get(GraphSemanticCandidateRecord, candidate_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail="Semantic candidate not found")
    if action not in {"approve", "reject"}:
        raise HTTPException(status_code=422, detail="Action must be approve or reject")
    candidate.status = "approved" if action == "approve" else "rejected"
    if action == "approve" and candidate.source_record_id:
        target = (
            session.get(GraphNodeRecord, candidate.source_record_id)
            if candidate.candidate_kind == "node"
            else session.get(GraphEdgeRecord, candidate.source_record_id)
        )
        if target is not None:
            target.semantic_status = "active"
            target.updated_at = datetime.now(UTC)
    candidate.updated_at = datetime.now(UTC)
    session.commit()
    return {"id": candidate.id, "status": candidate.status}


def _infer_edge_contract(
    edge: GraphEdgeRecord, source: GraphNodeRecord, target: GraphNodeRecord
) -> tuple[str, bool]:
    source_type = canonical_node_type(source.type)
    target_type = canonical_node_type(target.type)
    raw = edge.type.strip().lower()
    reason = f"{edge.label} {edge.reason}".casefold()
    if raw in {"semantic_relation", "shared_concept", "shared_context", "related"}:
        if source_type == "note" and target_type in {
            "concept",
            "entity",
            "topic",
            "context",
        }:
            return "mentions", False
        if target_type == "note" and source_type in {
            "concept",
            "entity",
            "topic",
            "context",
        }:
            return "mentions", True
        if source_type in {"concept", "entity", "topic", "context"} and target_type in {
            "concept",
            "entity",
            "topic",
            "context",
        }:
            return "related", False
        if source_type == "note" and target_type == "note" and "backlink" in reason:
            return "references", False
        return "related", False
    return canonical_edge_type(raw), False


def _record_candidate(
    session: Session,
    kind: str,
    source_id: int,
    proposed_type: str,
    proposed_label: str,
    issues: list[str],
    payload: dict[str, Any],
) -> None:
    existing = session.execute(
        select(GraphSemanticCandidateRecord).where(
            GraphSemanticCandidateRecord.candidate_kind == kind,
            GraphSemanticCandidateRecord.source_record_id == source_id,
            GraphSemanticCandidateRecord.status == "pending",
        )
    ).scalar_one_or_none()
    if existing is not None:
        existing.reason = " ".join(issues)
        existing.payload_json = json.dumps(payload, ensure_ascii=False)
        return
    session.add(
        GraphSemanticCandidateRecord(
            candidate_kind=kind,
            source_record_id=source_id,
            proposed_type=proposed_type,
            proposed_label=proposed_label,
            reason=" ".join(issues),
            payload_json=json.dumps(payload, ensure_ascii=False),
        )
    )


def _json_list(raw: str) -> list[Any]:
    try:
        parsed = json.loads(raw or "[]")
    except (TypeError, json.JSONDecodeError):
        return []
    return parsed if isinstance(parsed, list) else []


def _json_object(raw: str) -> dict[str, Any]:
    try:
        parsed = json.loads(raw or "{}")
    except (TypeError, json.JSONDecodeError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _stable_evidence(item: Any) -> str:
    payload = json.dumps(item, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def _node_payload(node: GraphNodeRecord) -> dict[str, Any]:
    return {"type": node.type, "label": node.label, "summary": node.summary}


def _edge_payload(edge: GraphEdgeRecord) -> dict[str, Any]:
    return {
        "type": edge.type,
        "sourceNodeId": edge.source_node_id,
        "targetNodeId": edge.target_node_id,
        "reason": edge.reason,
    }
