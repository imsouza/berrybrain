from __future__ import annotations

from typing import Any

from sqlalchemy import and_, or_

from berrybrain_api.models import GraphEdgeRecord, GraphNodeRecord

INACTIVE_LIFECYCLE_STATUSES = frozenset(
    {"ignored", "archived", "stale", "deleted", "superseded"}
)
FAILED_QUALITY_STATUSES = frozenset({"rejected", "insufficient_evidence"})
PROVISIONAL_QUALITY_STATUSES = frozenset({"pending", "review"})
ACCEPTED_QUALITY_STATUSES = frozenset({"passed"})
SOURCE_NODE_TYPES = frozenset({"note", "vault"})
USER_CREATORS = frozenset({"user", "manual"})
USER_CONFIRMED_STATUSES = frozenset({"confirmed", "accepted", "applied"})
DETERMINISTIC_EDGE_TYPES = frozenset({"attached_to", "derived_from", "references"})


def processable_node_clause():
    """Return graph nodes that still belong to the current semantic graph."""
    return and_(
        GraphNodeRecord.semantic_status == "active",
        GraphNodeRecord.status.not_in(INACTIVE_LIFECYCLE_STATUSES),
    )


def processable_edge_clause():
    """Return graph edges that still belong to the current semantic graph."""
    return and_(
        GraphEdgeRecord.semantic_status == "active",
        GraphEdgeRecord.status.not_in(INACTIVE_LIFECYCLE_STATUSES),
    )


def accepted_node_clause(*, include_provisional: bool = False):
    base = processable_node_clause()
    if include_provisional:
        return and_(
            base,
            GraphNodeRecord.quality_gate_status.not_in(FAILED_QUALITY_STATUSES),
        )
    return and_(
        base,
        GraphNodeRecord.quality_gate_status.not_in(FAILED_QUALITY_STATUSES),
        or_(
            GraphNodeRecord.quality_gate_status.in_(ACCEPTED_QUALITY_STATUSES),
            GraphNodeRecord.status.in_(USER_CONFIRMED_STATUSES),
            GraphNodeRecord.type.in_(SOURCE_NODE_TYPES),
            GraphNodeRecord.created_by.in_(USER_CREATORS),
        ),
    )


def accepted_edge_clause(*, include_provisional: bool = False):
    base = processable_edge_clause()
    if include_provisional:
        return and_(
            base,
            GraphEdgeRecord.quality_gate_status.not_in(FAILED_QUALITY_STATUSES),
        )
    return and_(
        base,
        GraphEdgeRecord.quality_gate_status.not_in(FAILED_QUALITY_STATUSES),
        or_(
            GraphEdgeRecord.quality_gate_status.in_(ACCEPTED_QUALITY_STATUSES),
            GraphEdgeRecord.status.in_(USER_CONFIRMED_STATUSES),
            GraphEdgeRecord.created_by.in_(USER_CREATORS),
            and_(
                GraphEdgeRecord.created_by == "system",
                GraphEdgeRecord.type.in_(DETERMINISTIC_EDGE_TYPES),
            ),
        ),
    )


def apply_quality_verdict(artifact: Any, verdict: str) -> None:
    """Keep semantic visibility synchronized with an enforcing quality verdict."""
    normalized = str(verdict or "pending").strip().casefold()
    artifact.quality_gate_status = normalized
    if not hasattr(artifact, "semantic_status"):
        return
    artifact.semantic_status = (
        "quarantined" if normalized in FAILED_QUALITY_STATUSES else "active"
    )


def is_default_visible_node(node: Any) -> bool:
    if getattr(node, "semantic_status", "") != "active":
        return False
    if getattr(node, "status", "") in INACTIVE_LIFECYCLE_STATUSES:
        return False
    quality = getattr(node, "quality_gate_status", "pending")
    if quality in FAILED_QUALITY_STATUSES:
        return False
    return (
        quality in ACCEPTED_QUALITY_STATUSES
        or getattr(node, "status", "") in USER_CONFIRMED_STATUSES
        or getattr(node, "type", "") in SOURCE_NODE_TYPES
        or getattr(node, "created_by", "") in USER_CREATORS
    )


def is_default_visible_edge(edge: Any) -> bool:
    if getattr(edge, "semantic_status", "") != "active":
        return False
    if getattr(edge, "status", "") in INACTIVE_LIFECYCLE_STATUSES:
        return False
    quality = getattr(edge, "quality_gate_status", "pending")
    if quality in FAILED_QUALITY_STATUSES:
        return False
    return (
        quality in ACCEPTED_QUALITY_STATUSES
        or getattr(edge, "status", "") in USER_CONFIRMED_STATUSES
        or getattr(edge, "created_by", "") in USER_CREATORS
        or (
            getattr(edge, "created_by", "") == "system"
            and getattr(edge, "type", "") in DETERMINISTIC_EDGE_TYPES
        )
    )
