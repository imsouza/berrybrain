from __future__ import annotations

import json
import math

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from berrybrain_api.models import (
    GraphEdgeRecord,
    GraphNodeRecord,
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

    from berrybrain_api.graph_contracts import (
        SYMMETRIC_EDGE_TYPES,
        canonical_edge_type,
        normalize_graph_label,
    )
    from berrybrain_api.graph_write_service import has_traceable_ai_evidence

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
                n.get("type") == "topic"
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
