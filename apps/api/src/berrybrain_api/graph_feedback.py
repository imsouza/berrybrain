from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from berrybrain_api.graph_contracts import (
    SYMMETRIC_EDGE_TYPES,
    canonical_edge_type,
    canonical_node_type,
    normalize_graph_label,
)
from berrybrain_api.models import GraphEdgeRecord, GraphFeedbackRecord, GraphNodeRecord

NEGATIVE_ACTIONS = frozenset({"ignored", "deleted"})
POSITIVE_ACTIONS = frozenset({"confirmed", "corrected", "restored"})


@dataclass(frozen=True)
class FeedbackDecision:
    action: str
    replacement: dict[str, Any]
    record_id: int

    @property
    def suppresses(self) -> bool:
        return self.action in NEGATIVE_ACTIONS


def normalized_note_ids(values: list[int] | tuple[int, ...] | set[int]) -> list[int]:
    return sorted({int(value) for value in values if int(value) > 0})


def context_key(source_note_ids: list[int] | tuple[int, ...] | set[int]) -> str:
    normalized = normalized_note_ids(source_note_ids)
    material = json.dumps(normalized, separators=(",", ":"))
    return hashlib.sha256(material.encode()).hexdigest()


def node_artifact_key(node_type: str, label: str) -> str:
    return f"node:{canonical_node_type(node_type)}:{normalize_graph_label(label)}"


def edge_artifact_key(
    source_node: GraphNodeRecord,
    target_node: GraphNodeRecord,
    edge_type: str,
) -> str:
    canonical_type = canonical_edge_type(edge_type)
    endpoints = [
        node_artifact_key(source_node.type, source_node.label),
        node_artifact_key(target_node.type, target_node.label),
    ]
    if canonical_type in SYMMETRIC_EDGE_TYPES:
        endpoints.sort()
    return f"edge:{canonical_type}:{endpoints[0]}->{endpoints[1]}"


def node_source_note_ids(node: GraphNodeRecord) -> list[int]:
    return _integer_list(node.source_note_ids)


def edge_source_note_ids(edge: GraphEdgeRecord) -> list[int]:
    return _integer_list(edge.source_note_ids)


def record_feedback(
    session: Session,
    *,
    artifact_kind: str,
    artifact_key: str,
    source_note_ids: list[int],
    action: str,
    original_payload: dict[str, Any],
    replacement_payload: dict[str, Any] | None = None,
) -> GraphFeedbackRecord:
    if artifact_kind not in {"node", "edge"}:
        raise ValueError("Graph feedback artifact kind must be node or edge")
    if action not in NEGATIVE_ACTIONS | POSITIVE_ACTIONS:
        raise ValueError(f"Unsupported graph feedback action: {action}")
    normalized_ids = normalized_note_ids(source_note_ids)
    key = context_key(normalized_ids)
    previous = session.execute(
        select(GraphFeedbackRecord).where(
            GraphFeedbackRecord.artifact_kind == artifact_kind,
            GraphFeedbackRecord.artifact_key == artifact_key,
            GraphFeedbackRecord.context_key == key,
            GraphFeedbackRecord.active.is_(True),
        )
    ).scalars()
    now = datetime.now(UTC)
    for item in previous:
        item.active = False
        item.updated_at = now
    feedback = GraphFeedbackRecord(
        artifact_kind=artifact_kind,
        artifact_key=artifact_key,
        context_key=key,
        action=action,
        source_note_ids=_json_dump(normalized_ids),
        original_payload=_json_dump(original_payload),
        replacement_payload=_json_dump(replacement_payload or {}),
        active=True,
        created_at=now,
        updated_at=now,
    )
    session.add(feedback)
    session.flush()
    from berrybrain_api.learning import record_learning_event

    record_learning_event(
        session,
        event_type=f"graph.{artifact_kind}.{action}",
        target_type=f"graph_{artifact_kind}",
        target_key=artifact_key,
        action=action,
        source_note_ids=normalized_ids,
        before_state=original_payload,
        after_state=replacement_payload or {},
        actor_type="user",
        origin="graph",
    )
    return feedback


def resolve_feedback(
    session: Session,
    *,
    artifact_kind: str,
    artifact_key: str,
    source_note_ids: list[int],
) -> FeedbackDecision | None:
    normalized_ids = normalized_note_ids(source_note_ids)
    row = session.execute(
        select(GraphFeedbackRecord)
        .where(
            GraphFeedbackRecord.artifact_kind == artifact_kind,
            GraphFeedbackRecord.artifact_key == artifact_key,
            GraphFeedbackRecord.context_key == context_key(normalized_ids),
            GraphFeedbackRecord.active.is_(True),
        )
        .order_by(GraphFeedbackRecord.id.desc())
        .limit(1)
    ).scalar_one_or_none()
    if row is None and normalized_ids:
        incoming_ids = set(normalized_ids)
        candidates = session.execute(
            select(GraphFeedbackRecord)
            .where(
                GraphFeedbackRecord.artifact_kind == artifact_kind,
                GraphFeedbackRecord.artifact_key == artifact_key,
                GraphFeedbackRecord.active.is_(True),
            )
            .order_by(GraphFeedbackRecord.id.desc())
        ).scalars()
        row = next(
            (
                candidate
                for candidate in candidates
                if incoming_ids & set(_integer_list(candidate.source_note_ids))
            ),
            None,
        )
    if row is None:
        return None
    return FeedbackDecision(
        action=row.action,
        replacement=_json_object(row.replacement_payload),
        record_id=row.id,
    )


def _integer_list(raw: str | None) -> list[int]:
    try:
        values = json.loads(raw or "[]")
    except (TypeError, json.JSONDecodeError):
        return []
    if not isinstance(values, list):
        return []
    return normalized_note_ids(
        [int(value) for value in values if str(value).strip().isdigit()]
    )


def _json_object(raw: str) -> dict[str, Any]:
    try:
        value = json.loads(raw or "{}")
    except (TypeError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _json_dump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
