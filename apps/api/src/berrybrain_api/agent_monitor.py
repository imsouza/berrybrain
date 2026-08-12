from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from berrybrain_api.ai_configuration import load_configuration
from berrybrain_api.job_contracts import judge_artifact_payload
from berrybrain_api.jobs import (
    GENERATE_GRAPH_INSIGHTS,
    PENDING,
    RUNNING,
    UPDATE_GRAPH_CLUSTERS,
    create_job,
    enqueue_job,
)
from berrybrain_api.models import (
    ArtifactEvaluationRecord,
    GraphNodeRecord,
    JobRecord,
    SettingRecord,
)
from berrybrain_api.semantic_enrichment import queue_node_enrichment


def ensure_agent_monitoring(session: Session) -> dict:
    """Schedule due cognitive maintenance from the worker heartbeat."""
    now = datetime.now(UTC)
    graph_exists = session.scalar(
        select(GraphNodeRecord.id)
        .where(
            GraphNodeRecord.status != "ignored",
            GraphNodeRecord.semantic_status == "active",
        )
        .limit(1)
    )
    if graph_exists is None:
        return {"status": "idle", "jobs": []}

    queued: list[dict] = []
    cluster_job = _ensure_due_job(
        session,
        UPDATE_GRAPH_CLUSTERS,
        now=now,
        interval=timedelta(hours=6),
        trigger="agent_monitor",
    )
    if cluster_job is not None:
        queued.append({"type": cluster_job.type, "id": cluster_job.id})

    configuration = load_configuration(session)
    if configuration is None or not configuration.validated_at:
        return {"status": "monitoring", "jobs": queued, "ai": "not_configured"}

    insight_hours = _bounded_int(
        _setting_value(session, "insights_auto_interval_hours", "24"),
        minimum=1,
        maximum=168,
        fallback=24,
    )
    insight_job = _ensure_due_job(
        session,
        GENERATE_GRAPH_INSIGHTS,
        now=now,
        interval=timedelta(hours=insight_hours),
        trigger="agent_monitor",
    )
    if insight_job is not None:
        queued.append({"type": insight_job.type, "id": insight_job.id})

    evaluated_node_ids = set(
        session.execute(
            select(ArtifactEvaluationRecord.artifact_id).where(
                ArtifactEvaluationRecord.artifact_type == "node"
            )
        ).scalars()
    )
    judge_candidates = list(
        session.execute(
            select(GraphNodeRecord)
            .where(
                GraphNodeRecord.created_by == "ai",
                GraphNodeRecord.status != "ignored",
                GraphNodeRecord.semantic_status == "active",
                GraphNodeRecord.id.not_in(evaluated_node_ids),
            )
            .order_by(GraphNodeRecord.updated_at.asc(), GraphNodeRecord.id.asc())
            .limit(3)
        ).scalars()
    )
    for node in judge_candidates:
        job = enqueue_job(
            session,
            "JUDGE_ARTIFACT",
            judge_artifact_payload(
                session,
                "node",
                node.id,
                str((node.updated_at or now).timestamp()),
            ),
            priority=20,
            max_attempts=2,
        )
        queued.append({"type": job.type, "id": job.id, "nodeId": node.id})

    candidates = list(
        session.execute(
            select(GraphNodeRecord)
            .where(
                GraphNodeRecord.type != "note",
                GraphNodeRecord.status != "ignored",
                GraphNodeRecord.semantic_status == "active",
                (
                    GraphNodeRecord.semantic_state.in_(["pending", "stale"])
                    | (GraphNodeRecord.ai_summary == "")
                ),
            )
            .order_by(GraphNodeRecord.updated_at.asc(), GraphNodeRecord.id.asc())
            .limit(3)
        ).scalars()
    )
    for node in candidates:
        job, created = queue_node_enrichment(
            session,
            node,
            configuration=configuration,
        )
        if created:
            queued.append({"type": job.type, "id": job.id, "nodeId": node.id})

    return {"status": "monitoring", "jobs": queued, "ai": "active"}


def _ensure_due_job(
    session: Session,
    job_type: str,
    *,
    now: datetime,
    interval: timedelta,
    trigger: str,
) -> JobRecord | None:
    active = (
        session.execute(
            select(JobRecord).where(
                JobRecord.type == job_type,
                JobRecord.status.in_([PENDING, RUNNING]),
            )
        )
        .scalars()
        .first()
    )
    if active is not None:
        return None
    latest = session.execute(
        select(JobRecord)
        .where(JobRecord.type == job_type)
        .order_by(JobRecord.created_at.desc())
        .limit(1)
    ).scalar_one_or_none()
    if latest is not None and latest.created_at is not None:
        latest_at = latest.created_at
        if latest_at.tzinfo is None:
            latest_at = latest_at.replace(tzinfo=UTC)
        if now - latest_at < interval:
            return None
    interval_seconds = max(1, int(interval.total_seconds()))
    slot = int(now.timestamp() // interval_seconds)
    return create_job(
        session,
        job_type,
        {
            "trigger": trigger,
            "idempotency_key": f"{trigger}:{job_type.lower()}:{slot}",
        },
        max_attempts=2,
    )


def _setting_value(session: Session, key: str, default: str) -> str:
    row = session.execute(
        select(SettingRecord).where(SettingRecord.key == key)
    ).scalar_one_or_none()
    return row.value if row and row.value != "" else default


def _bounded_int(
    raw: str,
    *,
    minimum: int,
    maximum: int,
    fallback: int,
) -> int:
    try:
        return max(minimum, min(maximum, int(raw)))
    except ValueError:
        return fallback
