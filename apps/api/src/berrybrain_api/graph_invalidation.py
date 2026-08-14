from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from berrybrain_api.artifact_state import (
    processable_edge_clause,
    processable_node_clause,
)
from berrybrain_api.graph_write_service import GraphWriteService
from berrybrain_api.models import (
    ConnectionRecord,
    GraphEdgeRecord,
    GraphNodeRecord,
    InsightRecord,
)


@dataclass(frozen=True)
class NodeDeletionImpact:
    node_id: int
    source_note_ids: tuple[int, ...]
    neighbor_node_ids: tuple[int, ...]
    cluster_scope_node_ids: tuple[int, ...]
    dependent_insight_node_ids: tuple[int, ...]
    dependent_insight_record_ids: tuple[int, ...]
    dependent_edge_ids: tuple[int, ...]
    dependent_connection_ids: tuple[int, ...]
    incident_edge_count: int

    def to_dict(self) -> dict[str, object]:
        return {
            "sourceNoteIds": list(self.source_note_ids),
            "neighborNodeIds": list(self.neighbor_node_ids),
            "clusterScopeNodeIds": list(self.cluster_scope_node_ids),
            "dependentInsightNodeIds": list(self.dependent_insight_node_ids),
            "dependentInsightRecordIds": list(self.dependent_insight_record_ids),
            "dependentEdgeIds": list(self.dependent_edge_ids),
            "dependentConnectionIds": list(self.dependent_connection_ids),
            "incidentEdgeCount": self.incident_edge_count,
        }


def collect_node_deletion_impact(
    session: Session, node: GraphNodeRecord
) -> NodeDeletionImpact:
    incident_edges = list(
        session.execute(
            select(GraphEdgeRecord).where(
                or_(
                    GraphEdgeRecord.source_node_id == node.id,
                    GraphEdgeRecord.target_node_id == node.id,
                )
            )
        ).scalars()
    )
    neighbor_ids = {
        edge.target_node_id if edge.source_node_id == node.id else edge.source_node_id
        for edge in incident_edges
    }
    neighbors = {
        item.id: item
        for item in session.execute(
            select(GraphNodeRecord).where(GraphNodeRecord.id.in_(neighbor_ids))
        ).scalars()
    }
    dependent_insight_nodes = {
        item.id: item for item in neighbors.values() if item.type == "insight"
    }
    if node.type == "insight":
        dependent_insight_nodes[node.id] = node

    cluster_ids = {
        int(item.cluster_id)
        for item in [node, *neighbors.values()]
        if item.cluster_id is not None
    }
    cluster_scope = set(neighbor_ids)
    if cluster_ids:
        cluster_scope.update(
            session.execute(
                select(GraphNodeRecord.id).where(
                    GraphNodeRecord.cluster_id.in_(cluster_ids),
                    GraphNodeRecord.id != node.id,
                    processable_node_clause(),
                )
            ).scalars()
        )
    source_note_ids = _integer_json_values(node.source_note_ids)
    for edge in incident_edges:
        source_note_ids.update(_integer_json_values(edge.source_note_ids))
    normalized_label = node.label.strip().casefold()
    dependent_edge_ids: set[int] = set()
    dependent_connection_ids: set[int] = set()
    if node.type == "concept" and source_note_ids and normalized_label:
        for edge in session.execute(
            select(GraphEdgeRecord).where(
                GraphEdgeRecord.type == "related",
                GraphEdgeRecord.label == "shared concept",
                processable_edge_clause(),
            )
        ).scalars():
            if not (source_note_ids & _integer_json_values(edge.source_note_ids)):
                continue
            if _mentions_label(
                normalized_label, f"{edge.reason or ''} {edge.evidence or ''}"
            ):
                dependent_edge_ids.add(edge.id)
        for connection in session.execute(
            select(ConnectionRecord).where(
                ConnectionRecord.connection_type == "shared_concept",
                ConnectionRecord.status.not_in(("ignored", "archived", "stale")),
            )
        ).scalars():
            if source_note_ids.isdisjoint(
                {connection.source_note_id, connection.target_note_id}
            ):
                continue
            if _mentions_label(
                normalized_label,
                f"{connection.reason or ''} {connection.evidence or ''}",
            ):
                dependent_connection_ids.add(connection.id)
    if source_note_ids and normalized_label:
        for candidate in session.execute(
            select(GraphNodeRecord).where(
                GraphNodeRecord.type == "insight",
                GraphNodeRecord.id != node.id,
                processable_node_clause(),
            )
        ).scalars():
            if not (source_note_ids & _integer_json_values(candidate.source_note_ids)):
                continue
            same_affected_cluster = (
                candidate.cluster_id is not None
                and int(candidate.cluster_id) in cluster_ids
            )
            mentions_deleted_artifact = _mentions_label(
                normalized_label,
                " ".join(
                    (
                        candidate.label or "",
                        candidate.title or "",
                        candidate.summary or "",
                        candidate.source_evidence or "",
                    )
                ),
            )
            if same_affected_cluster or mentions_deleted_artifact:
                dependent_insight_nodes[candidate.id] = candidate
    cluster_scope.difference_update(dependent_insight_nodes)
    insight_record_ids = {
        int(item.source_id)
        for item in dependent_insight_nodes.values()
        if item.source_id is not None
    }
    for insight in session.execute(
        select(InsightRecord).where(
            InsightRecord.status.not_in(("ignored", "archived", "expired", "dismissed"))
        )
    ).scalars():
        if not (source_note_ids & _integer_json_values(insight.related_notes)):
            continue
        if _mentions_label(
            normalized_label,
            " ".join(
                (
                    insight.title or "",
                    insight.description or "",
                    insight.evidence or "",
                    insight.reasoning or "",
                )
            ),
        ):
            insight_record_ids.add(insight.id)
    return NodeDeletionImpact(
        node_id=node.id,
        source_note_ids=tuple(sorted(source_note_ids)),
        neighbor_node_ids=tuple(sorted(neighbor_ids)),
        cluster_scope_node_ids=tuple(sorted(cluster_scope)),
        dependent_insight_node_ids=tuple(sorted(dependent_insight_nodes)),
        dependent_insight_record_ids=tuple(sorted(insight_record_ids)),
        dependent_edge_ids=tuple(sorted(dependent_edge_ids)),
        dependent_connection_ids=tuple(sorted(dependent_connection_ids)),
        incident_edge_count=len(incident_edges),
    )


def invalidate_dependent_insights(
    session: Session,
    impact: NodeDeletionImpact,
    *,
    primary_node_id: int,
) -> int:
    now = datetime.now(UTC).replace(tzinfo=None)
    invalidated = 0
    for insight_id in impact.dependent_insight_record_ids:
        insight = session.get(InsightRecord, insight_id)
        if insight is None:
            continue
        insight.status = "expired"
        insight.expires_at = now
        insight.updated_at = now
        invalidated += 1

    writer = GraphWriteService(session, autocommit=False)
    for insight_node_id in impact.dependent_insight_node_ids:
        if insight_node_id == primary_node_id:
            continue
        if session.get(GraphNodeRecord, insight_node_id) is not None:
            writer.delete_node(insight_node_id, user_decision=True)
    session.flush()
    return invalidated


def invalidate_dependent_relationships(
    session: Session, impact: NodeDeletionImpact
) -> int:
    now = datetime.now(UTC).replace(tzinfo=None)
    invalidated = 0
    for edge_id in impact.dependent_edge_ids:
        edge = session.get(GraphEdgeRecord, edge_id)
        if edge is None:
            continue
        edge.status = "stale"
        edge.semantic_status = "quarantined"
        edge.updated_at = now
        invalidated += 1
    for connection_id in impact.dependent_connection_ids:
        connection = session.get(ConnectionRecord, connection_id)
        if connection is None:
            continue
        connection.status = "stale"
        connection.updated_at = now
        invalidated += 1
    session.flush()
    return invalidated


def _integer_json_values(raw: str | None) -> set[int]:
    try:
        values = json.loads(raw or "[]")
    except (TypeError, json.JSONDecodeError):
        return set()
    if not isinstance(values, list):
        return set()
    return {int(value) for value in values if str(value).isdigit()}


def _mentions_label(label: str, text: str) -> bool:
    return bool(
        label
        and re.search(
            rf"(?<!\w){re.escape(label)}(?!\w)",
            text.casefold(),
        )
    )
