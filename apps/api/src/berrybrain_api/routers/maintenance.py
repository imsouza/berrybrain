from __future__ import annotations

import json
from collections import defaultdict
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import select

from berrybrain_api.automation_logs import create_automation_log
from berrybrain_api.cognitive_layer import index_knowledge_base
from berrybrain_api.config import get_settings
from berrybrain_api.database import SessionLocal
from berrybrain_api.jobs import enqueue_note_changed_jobs
from berrybrain_api.models import (
    GraphEdgeRecord,
    GraphNodeRecord,
    InsightRecord,
    JobRecord,
    NoteRecord,
)
from berrybrain_api.second_brain import expand_knowledge_graph
from berrybrain_api.security import require_admin
from berrybrain_api.vault_scan import scan_vault

# ponytail: destructive system-wide ops, admin only
router = APIRouter(
    prefix="/api/v1/maintenance",
    tags=["maintenance"],
    dependencies=[Depends(require_admin)],
)

TECHNICAL_TERMS = (
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


def _parse_list(raw: str | None) -> list[Any]:
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return []
    return parsed if isinstance(parsed, list) else []


def _contains_technical_terms(*values: Any) -> bool:
    text = " ".join(str(value or "") for value in values).lower()
    return any(term in text for term in TECHNICAL_TERMS)


def _is_technical_insight(insight: InsightRecord) -> bool:
    if (insight.type or "").lower() in {
        "system_diagnostic",
        "pipeline_bottleneck",
        "provider_issue",
        "job_backlog",
        "worker_status",
    }:
        return True
    return _contains_technical_terms(
        insight.title,
        insight.description,
        insight.why_it_matters,
        insight.suggested_action,
        insight.graph_impact,
        insight.evidence,
        insight.source_context,
    )


def _is_technical_graph_node(node: GraphNodeRecord) -> bool:
    if (node.type or "").lower() != "insight":
        return False
    return _contains_technical_terms(
        node.label,
        node.title,
        node.summary,
        node.ai_summary,
        node.ai_context,
        node.source_evidence,
        node.graph_metadata,
    )


def _cleanup_legacy_insights(session) -> dict[str, int]:
    archived_insights = 0
    ignored_nodes = 0
    ignored_edges = 0
    now = datetime.now(UTC)

    for insight in session.execute(select(InsightRecord)).scalars():
        if not _is_technical_insight(insight):
            continue
        if insight.status != "archived" or insight.dismissed_at is None:
            insight.status = "archived"
            insight.dismissed_at = insight.dismissed_at or now
            archived_insights += 1

    technical_node_ids: set[int] = set()
    for node in session.execute(select(GraphNodeRecord)).scalars():
        if not _is_technical_graph_node(node):
            continue
        technical_node_ids.add(node.id)
        if node.status != "ignored":
            node.status = "ignored"
            ignored_nodes += 1

    if technical_node_ids:
        for edge in session.execute(select(GraphEdgeRecord)).scalars():
            if (
                edge.source_node_id in technical_node_ids
                or edge.target_node_id in technical_node_ids
            ):
                if edge.status != "ignored":
                    edge.status = "ignored"
                    ignored_edges += 1

    session.commit()
    return {
        "archivedInsights": archived_insights,
        "ignoredInsightNodes": ignored_nodes,
        "ignoredEdges": ignored_edges,
    }


def _validate_graph(session) -> dict[str, int]:
    node_ids = set(session.execute(select(GraphNodeRecord.id)).scalars())
    deleted_orphan_edges = 0
    ignored_self_edges = 0
    ignored_duplicate_edges = 0
    seen_edges: set[tuple[int, int, str]] = set()

    for edge in session.execute(select(GraphEdgeRecord)).scalars():
        if edge.source_node_id not in node_ids or edge.target_node_id not in node_ids:
            session.delete(edge)
            deleted_orphan_edges += 1
            continue
        if edge.source_node_id == edge.target_node_id:
            if edge.status != "ignored":
                edge.status = "ignored"
                ignored_self_edges += 1
            continue
        key = (
            min(edge.source_node_id, edge.target_node_id),
            max(edge.source_node_id, edge.target_node_id),
            edge.type,
        )
        if key in seen_edges:
            if edge.status != "ignored":
                edge.status = "ignored"
                ignored_duplicate_edges += 1
            continue
        seen_edges.add(key)

    session.commit()
    return {
        "deletedOrphanEdges": deleted_orphan_edges,
        "ignoredSelfEdges": ignored_self_edges,
        "ignoredDuplicateEdges": ignored_duplicate_edges,
    }


def _cleanup_duplicate_jobs(session) -> dict[str, int]:
    active_jobs = list(
        session.execute(
            select(JobRecord).where(JobRecord.status.in_(("pending", "running")))
        ).scalars()
    )
    grouped: dict[tuple[str, str], list[JobRecord]] = defaultdict(list)
    for job in active_jobs:
        grouped[(job.type, job.payload or "{}")].append(job)

    marked_failed = 0
    for jobs in grouped.values():
        if len(jobs) <= 1:
            continue
        jobs.sort(key=lambda item: (item.created_at, item.id))
        for duplicate in jobs[1:]:
            duplicate.status = "failed"
            duplicate.error_message = "Duplicate active job cleaned by maintenance."
            duplicate.completed_at = datetime.now(UTC)
            marked_failed += 1

    session.commit()
    return {"duplicateJobsMarkedFailed": marked_failed}


@router.post("/cleanup-legacy-insights")
def cleanup_legacy_insights() -> dict:
    with SessionLocal() as session:
        result = _cleanup_legacy_insights(session)
        create_automation_log(
            session,
            "MAINTENANCE_CLEANUP_LEGACY_INSIGHTS",
            "maintenance",
            "legacy-insights",
            "Archived technical/system insights and hid their graph nodes.",
            {},
            result,
            False,
        )
        return {"status": "ok", **result}


@router.post("/validate-graph")
def validate_graph_consistency() -> dict:
    with SessionLocal() as session:
        cleanup = _cleanup_legacy_insights(session)
        graph = _validate_graph(session)
        jobs = _cleanup_duplicate_jobs(session)
        result = {**cleanup, **graph, **jobs}
        create_automation_log(
            session,
            "MAINTENANCE_VALIDATE_GRAPH",
            "maintenance",
            "graph",
            "Validated graph consistency and cleaned duplicate active jobs.",
            {},
            result,
            False,
        )
        return {"status": "ok", **result}


@router.post("/reindex-knowledge-base")
def reindex_knowledge_base() -> dict:
    with SessionLocal() as session:
        result = index_knowledge_base(session)
        create_automation_log(
            session,
            "MAINTENANCE_REINDEX_KB",
            "maintenance",
            "knowledge-base",
            "Reindexed the BerryBrain Knowledge Base.",
            {},
            result,
            False,
        )
        return result


@router.post("/rebuild-brain")
def rebuild_second_brain() -> dict:
    settings = get_settings()
    with SessionLocal() as session:
        cleanup = _cleanup_legacy_insights(session)
        scan = scan_vault(session, settings.vault_path)
        queued = 0
        for note in session.execute(select(NoteRecord)).scalars():
            jobs = enqueue_note_changed_jobs(
                session,
                note.path,
                "NOTE_UPDATED",
                note.content_hash,
            )
            queued += len(jobs)
        graph = expand_knowledge_graph(session)
        kb = index_knowledge_base(session)
        validation = _validate_graph(session)
        duplicate_jobs = _cleanup_duplicate_jobs(session)
        result = {
            "status": "queued",
            "cleanup": cleanup,
            "scan": scan,
            "jobsQueued": queued,
            "graph": graph,
            "knowledgeBase": kb,
            "validation": validation,
            "jobs": duplicate_jobs,
        }
        create_automation_log(
            session,
            "MAINTENANCE_REBUILD_SECOND_BRAIN",
            "maintenance",
            "second-brain",
            "Queued a full BerryBrain rebuild from vault notes and current settings.",
            {},
            result,
            False,
        )
        return result
