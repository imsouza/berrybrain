from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from berrybrain_api.automation_logs import create_automation_log
from berrybrain_api.models import JobRecord

PENDING = "pending"
RUNNING = "running"
COMPLETED = "completed"
FAILED = "failed"
PARSE_NOTE = "PARSE_NOTE"
CLASSIFY_NOTE = "CLASSIFY_NOTE"
ASSIMILATE_NOTE = "ASSIMILATE_NOTE"
GENERATE_EMBEDDING = "GENERATE_EMBEDDING"
FIND_CONNECTIONS = "FIND_CONNECTIONS"
GENERATE_INSIGHTS = "GENERATE_INSIGHTS"
GENERATE_NOTE_TITLE = "GENERATE_NOTE_TITLE"
EXPAND_KNOWLEDGE_GRAPH = "EXPAND_KNOWLEDGE_GRAPH"
EXTRACT_CONCEPTS = "EXTRACT_CONCEPTS"
EXTRACT_CONTEXT = "EXTRACT_CONTEXT"
EXTRACT_ENTITIES = "EXTRACT_ENTITIES"
DETECT_TOPICS = "DETECT_TOPICS"
GENERATE_NODE_SUMMARY = "GENERATE_NODE_SUMMARY"
GENERATE_INFERRED_CONNECTIONS = "GENERATE_INFERRED_CONNECTIONS"
GENERATE_GRAPH_INSIGHTS = "GENERATE_GRAPH_INSIGHTS"
UPDATE_GRAPH_CLUSTERS = "UPDATE_GRAPH_CLUSTERS"
UPDATE_GRAPH_STATS = "UPDATE_GRAPH_STATS"
EXPAND_CONCEPT_TO_NOTE = "EXPAND_CONCEPT_TO_NOTE"
ENRICH_GRAPH_NODE = "ENRICH_GRAPH_NODE"
VALIDATE_GRAPH_NODE_WITH_WEB = "VALIDATE_GRAPH_NODE_WITH_WEB"
REASON_GRAPH_CONNECTION = "REASON_GRAPH_CONNECTION"
GENERATE_GRAPH_GAPS = "GENERATE_GRAPH_GAPS"
PRUNE_LOW_VALUE_GRAPH_NODES = "PRUNE_LOW_VALUE_GRAPH_NODES"
MERGE_DUPLICATE_GRAPH_NODES = "MERGE_DUPLICATE_GRAPH_NODES"
UPDATE_GRAPH_QUALITY = "UPDATE_GRAPH_QUALITY"
PROCESS_ATTACHMENT = "PROCESS_ATTACHMENT"
NOTE_PIPELINE_ORDER = [
    PARSE_NOTE,
    CLASSIFY_NOTE,
    ASSIMILATE_NOTE,
    EXTRACT_CONCEPTS,
    EXTRACT_ENTITIES,
    DETECT_TOPICS,
    EXTRACT_CONTEXT,
    GENERATE_EMBEDDING,
    FIND_CONNECTIONS,
    EXPAND_KNOWLEDGE_GRAPH,
    ENRICH_GRAPH_NODE,
    GENERATE_INFERRED_CONNECTIONS,
    EXPAND_CONCEPT_TO_NOTE,
    GENERATE_GRAPH_INSIGHTS,
    UPDATE_GRAPH_STATS,
    GENERATE_NOTE_TITLE,
]
NOTE_PIPELINE_RANK = {
    job_type: rank for rank, job_type in enumerate(NOTE_PIPELINE_ORDER)
}
GRAPH_MUTATION_JOB_TYPES = {
    EXPAND_KNOWLEDGE_GRAPH,
    ENRICH_GRAPH_NODE,
    GENERATE_INFERRED_CONNECTIONS,
    EXPAND_CONCEPT_TO_NOTE,
    GENERATE_GRAPH_INSIGHTS,
    UPDATE_GRAPH_STATS,
    REASON_GRAPH_CONNECTION,
    GENERATE_GRAPH_GAPS,
    PRUNE_LOW_VALUE_GRAPH_NODES,
    MERGE_DUPLICATE_GRAPH_NODES,
    UPDATE_GRAPH_QUALITY,
    PROCESS_ATTACHMENT,
}


def create_job(
    session: Session,
    job_type: str,
    payload: dict[str, Any],
    max_attempts: int = 3,
) -> JobRecord:
    job = JobRecord(
        type=job_type,
        payload=compact_json(payload),
        status=PENDING,
        max_attempts=max_attempts,
    )
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


def enqueue_note_changed_jobs(
    session: Session,
    note_path: str,
    event_type: str,
    content_hash: str,
) -> list[JobRecord]:
    if event_type == "NOTE_DELETED":
        return []

    pipeline = [
        (PARSE_NOTE, 3),
        (CLASSIFY_NOTE, 2),
        (ASSIMILATE_NOTE, 2),
        (EXTRACT_CONCEPTS, 2),
        (EXTRACT_ENTITIES, 2),
        (DETECT_TOPICS, 2),
        (EXTRACT_CONTEXT, 2),
        (GENERATE_EMBEDDING, 2),
        (FIND_CONNECTIONS, 2),
        (EXPAND_KNOWLEDGE_GRAPH, 2),
        (GENERATE_INFERRED_CONNECTIONS, 2),
        (EXPAND_CONCEPT_TO_NOTE, 2),
        (GENERATE_GRAPH_INSIGHTS, 2),
        (UPDATE_GRAPH_STATS, 1),
    ]
    if _needs_generated_title(note_path):
        pipeline.append((GENERATE_NOTE_TITLE, 2))

    jobs: list[JobRecord] = []

    for job_type, max_attempts in pipeline:
        existing = (
            session.execute(
                select(JobRecord).where(
                    JobRecord.type == job_type,
                    JobRecord.status.in_([PENDING, RUNNING]),
                    JobRecord.payload.like(f'%"note_path":"{note_path}"%'),
                    JobRecord.payload.like(f'%"content_hash":"{content_hash}"%'),
                )
            )
            .scalars()
            .first()
        )

        if existing is not None:
            continue

        payload = {
            "content_hash": content_hash,
            "event_type": event_type,
            "note_path": note_path,
        }
        job = create_job(session, job_type, payload, max_attempts=max_attempts)
        jobs.append(job)
        create_automation_log(
            session,
            action_type="ENQUEUE_JOB",
            target_type="note",
            target_id=note_path,
            description=f"Criou job {job_type} para {event_type}",
            before_state={},
            after_state={"job_id": job.id, "job_type": job_type, "payload": payload},
            reversible=False,
        )

    return jobs


def _needs_generated_title(note_path: str) -> bool:
    filename = note_path.rsplit("/", 1)[-1].lower()
    return filename.startswith("rascunho") or filename.startswith("nota-sem-titulo")


def claim_next_job(session: Session, stale_after_minutes: int = 30) -> JobRecord | None:
    recover_stale_running_jobs(session, stale_after_minutes)

    candidates = list(
        session.execute(
            select(JobRecord)
            .where(
                JobRecord.status == PENDING,
                JobRecord.attempts < JobRecord.max_attempts,
            )
            .order_by(JobRecord.created_at.asc(), JobRecord.id.asc())
            .limit(50)
        ).scalars()
    )
    job = next(
        (
            candidate
            for candidate in candidates
            if _job_dependencies_satisfied(session, candidate)
        ),
        None,
    )
    if job is None:
        return None

    job.status = RUNNING
    job.attempts += 1
    job.started_at = utc_now()
    session.commit()
    session.refresh(job)
    return job


def recover_stale_running_jobs(session: Session, stale_after_minutes: int = 30) -> int:
    cutoff = utc_now() - timedelta(minutes=stale_after_minutes)
    stale_count = 0
    running_jobs = session.execute(
        select(JobRecord).where(JobRecord.status == RUNNING)
    ).scalars()

    for job in running_jobs:
        if job.started_at and normalize_utc(job.started_at) <= cutoff:
            if job.attempts >= job.max_attempts:
                job.status = FAILED
                job.completed_at = utc_now()
                job.error_message = "Stale running job exhausted attempts"
            else:
                job.status = PENDING
                job.error_message = "Recovered stale running job"
            job.started_at = None
            stale_count += 1
            create_automation_log(
                session,
                action_type="RECOVER_STALE_JOB",
                target_type="job",
                target_id=str(job.id),
                description=f"Recuperou job stale {job.type} como {job.status}",
                before_state={},
                after_state={
                    "job_id": job.id,
                    "job_type": job.type,
                    "status": job.status,
                    "attempts": job.attempts,
                    "max_attempts": job.max_attempts,
                },
                reversible=False,
            )

    if stale_count:
        session.commit()

    return stale_count


def _job_dependencies_satisfied(session: Session, job: JobRecord) -> bool:
    if job.type in GRAPH_MUTATION_JOB_TYPES:
        running_same_type = session.execute(
            select(JobRecord).where(
                JobRecord.id != job.id,
                JobRecord.type == job.type,
                JobRecord.status == RUNNING,
            )
        ).scalar_one_or_none()
        if running_same_type is not None:
            return False

    payload = parse_json(job.payload)
    if not isinstance(payload, dict):
        return True
    note_path = payload.get("note_path")
    content_hash = payload.get("content_hash")
    if not note_path or job.type not in NOTE_PIPELINE_RANK:
        return True

    rank = NOTE_PIPELINE_RANK[job.type]
    blocking_types = set(NOTE_PIPELINE_ORDER[:rank])
    if not blocking_types:
        return True

    query = select(JobRecord).where(
        JobRecord.id != job.id,
        JobRecord.type.in_(blocking_types),
        JobRecord.status.in_([PENDING, RUNNING]),
        JobRecord.payload.like(f'%"note_path":"{note_path}"%'),
    )
    if content_hash:
        query = query.where(
            JobRecord.payload.like(f'%"content_hash":"{content_hash}"%')
        )

    return session.execute(query.limit(1)).scalar_one_or_none() is None


def complete_job(session: Session, job_id: int) -> JobRecord:
    job = get_job_or_404(session, job_id)
    job.status = COMPLETED
    job.error_message = None
    job.completed_at = utc_now()
    session.commit()
    session.refresh(job)
    return job


def fail_job(session: Session, job_id: int, error_message: str) -> JobRecord:
    job = get_job_or_404(session, job_id)
    job.error_message = error_message
    job.completed_at = utc_now()

    if job.attempts >= job.max_attempts:
        job.status = FAILED
    else:
        job.status = PENDING
        job.started_at = None

    session.commit()
    session.refresh(job)
    return job


def list_jobs(
    session: Session, status: str | None = None, limit: int = 50
) -> list[JobRecord]:
    query = (
        select(JobRecord)
        .order_by(JobRecord.created_at.desc(), JobRecord.id.desc())
        .limit(limit)
    )
    if status:
        query = (
            select(JobRecord)
            .where(JobRecord.status == status)
            .order_by(JobRecord.created_at.desc(), JobRecord.id.desc())
            .limit(limit)
        )
    return list(session.execute(query).scalars())


def serialize_job(job: JobRecord) -> dict[str, Any]:
    return {
        "id": job.id,
        "type": job.type,
        "status": job.status,
        "payload": parse_json(job.payload),
        "attempts": job.attempts,
        "max_attempts": job.max_attempts,
        "error_message": job.error_message,
        "created_at": serialize_datetime(job.created_at),
        "started_at": serialize_datetime(job.started_at),
        "completed_at": serialize_datetime(job.completed_at),
    }


def get_job_or_404(session: Session, job_id: int) -> JobRecord:
    job = session.get(JobRecord, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


def compact_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def parse_json(value: str) -> Any:
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return {}


def serialize_datetime(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def utc_now() -> datetime:
    return datetime.now(UTC)


def normalize_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def should_generate_note_title(note_path: str) -> bool:
    name = note_path.rsplit("/", 1)[-1].removesuffix(".md")
    return (
        name == "rascunho" or name.startswith("rascunho-") or name == "nota-sem-titulo"
    )
