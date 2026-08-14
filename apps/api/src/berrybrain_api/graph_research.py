from __future__ import annotations

import hashlib
import ipaddress
from datetime import UTC, datetime
from urllib.parse import urlparse

from fastapi import HTTPException
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from berrybrain_api.artifact_state import accepted_node_clause
from berrybrain_api.jobs import create_job
from berrybrain_api.models import (
    GraphNodeRecord,
    GraphResearchResultRecord,
    GraphResearchRunRecord,
)
from berrybrain_api.services import searxng_search

MAX_RESEARCH_QUERIES = 20
MAX_RESULTS_PER_QUERY = 5


def create_research_run(
    session: Session, graph_version: int = 0
) -> GraphResearchRunRecord:
    active = session.execute(
        select(GraphResearchRunRecord).where(
            GraphResearchRunRecord.status.in_(["pending", "running"])
        )
    ).scalar_one_or_none()
    if active is not None:
        return active
    run = GraphResearchRunRecord(status="pending", graph_version=graph_version)
    session.add(run)
    session.flush()
    create_job(
        session,
        "RESEARCH_GRAPH",
        {
            "research_run_id": run.id,
            "idempotency_key": f"research-graph:{run.id}:{graph_version}",
        },
        max_attempts=2,
        autocommit=False,
    )
    session.commit()
    session.refresh(run)
    return run


def execute_research_run(
    session: Session,
    run_id: int,
    searxng_url: str,
) -> GraphResearchRunRecord:
    run = session.get(GraphResearchRunRecord, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Research run not found")
    if run.status == "cancelled":
        return run
    run.status = "running"
    run.updated_at = datetime.now(UTC)
    candidates = list(
        session.execute(
            select(GraphNodeRecord)
            .where(accepted_node_clause(include_provisional=True))
            .where(
                or_(
                    GraphNodeRecord.semantic_state.in_(
                        ["failed", "stale", "needs_review"]
                    ),
                    GraphNodeRecord.confidence < 0.65,
                    GraphNodeRecord.validation_status.in_(
                        ["unvalidated", "needs_review", "conflict_found"]
                    ),
                )
            )
            .order_by(GraphNodeRecord.confidence.asc(), GraphNodeRecord.id.asc())
            .limit(MAX_RESEARCH_QUERIES)
        ).scalars()
    )
    planned: list[tuple[GraphNodeRecord, str]] = []
    seen_queries: set[str] = set()
    for node in candidates:
        query = " ".join((node.label or node.title or "").split()).strip()
        normalized = query.casefold()
        if not query or normalized in seen_queries:
            continue
        seen_queries.add(normalized)
        planned.append((node, query))
    run.planned_queries = len(planned)
    session.commit()
    for index, (node, query) in enumerate(planned, start=1):
        session.refresh(run)
        if run.status == "cancelled":
            return run
        for item in searxng_search(
            query,
            searxng_url,
            max_results=MAX_RESULTS_PER_QUERY,
        ):
            source_url = str(item.get("url") or "").strip()
            if not safe_evidence_url(source_url):
                continue
            source_hash = hashlib.sha256(source_url.encode("utf-8")).hexdigest()
            duplicate = session.execute(
                select(GraphResearchResultRecord).where(
                    GraphResearchResultRecord.source_hash == source_hash,
                    GraphResearchResultRecord.node_id == node.id,
                )
            ).scalar_one_or_none()
            if duplicate is not None:
                continue
            session.add(
                GraphResearchResultRecord(
                    run_id=run.id,
                    node_id=node.id,
                    query=query,
                    source_url=source_url,
                    source_hash=source_hash,
                    title=str(item.get("title") or "")[:500],
                    evidence=str(item.get("content") or "")[:2000],
                    status="suggested",
                )
            )
        node.semantic_state = "stale"
        node.color_id = "pending"
        run.completed_queries = index
        run.progress = round(index / max(1, len(planned)) * 100)
        run.updated_at = datetime.now(UTC)
        session.commit()
    run.status = "completed"
    run.progress = 100
    run.completed_at = datetime.now(UTC)
    run.updated_at = datetime.now(UTC)
    session.commit()
    from berrybrain_api.semantic_enrichment import queue_node_enrichment

    for node, _ in planned:
        has_results = session.execute(
            select(GraphResearchResultRecord.id).where(
                GraphResearchResultRecord.run_id == run.id,
                GraphResearchResultRecord.node_id == node.id,
            )
        ).first()
        if has_results:
            queue_node_enrichment(session, node)
    session.refresh(run)
    return run


def cancel_research_run(session: Session, run_id: int) -> GraphResearchRunRecord:
    run = session.get(GraphResearchRunRecord, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Research run not found")
    if run.status not in {"completed", "cancelled"}:
        run.status = "cancelled"
        run.updated_at = datetime.now(UTC)
        session.commit()
        session.refresh(run)
    return run


def serialize_research_run(run: GraphResearchRunRecord) -> dict[str, object]:
    return {
        "id": run.id,
        "status": run.status,
        "graphVersion": run.graph_version,
        "progress": run.progress,
        "plannedQueries": run.planned_queries,
        "completedQueries": run.completed_queries,
        "error": run.error,
        "createdAt": run.created_at.isoformat(),
        "updatedAt": run.updated_at.isoformat(),
        "completedAt": run.completed_at.isoformat() if run.completed_at else None,
    }


def serialize_research_result(
    item: GraphResearchResultRecord,
) -> dict[str, object]:
    return {
        "id": item.id,
        "runId": item.run_id,
        "nodeId": item.node_id,
        "query": item.query,
        "sourceUrl": item.source_url,
        "sourceHash": item.source_hash,
        "title": item.title,
        "evidence": item.evidence,
        "status": item.status,
        "createdAt": item.created_at.isoformat(),
    }


def safe_evidence_url(value: str) -> bool:
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return False
    hostname = parsed.hostname.casefold()
    if hostname == "localhost" or hostname.endswith(".localhost"):
        return False
    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        return True
    return not (
        address.is_private
        or address.is_loopback
        or address.is_link_local
        or address.is_multicast
        or address.is_reserved
    )
