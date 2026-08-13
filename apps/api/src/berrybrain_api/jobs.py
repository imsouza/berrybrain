from __future__ import annotations

import json
import re
import statistics
from datetime import UTC, datetime, timedelta
from typing import Any, cast
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.orm import Session

from berrybrain_api.automation_logs import create_automation_log
from berrybrain_api.job_contracts import (
    begin_job_attempt,
    finish_job_attempt,
    update_job_attempt,
    validate_job_payload,
)
from berrybrain_api.models import JobRecord, NoteRecord
from berrybrain_api.redaction import redact_text
from berrybrain_api.worker_inbox import (
    consume_worker_message,
    worker_message_processed,
)

PENDING = "pending"
RUNNING = "running"
COMPLETED = "completed"
FAILED = "failed"
DEAD_LETTER = "dead_letter"
SUPERSEDED = "superseded"
CANCEL_REQUESTED = "cancel_requested"
CANCELLED = "cancelled"
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
ORGANIZE_VAULT = "ORGANIZE_VAULT"
PROCESS_ATTACHMENT = "PROCESS_ATTACHMENT"
CREATE_NOTE_FROM_INSIGHT = "CREATE_NOTE_FROM_INSIGHT"
SYNC_HIPPORAG_GRAPH = "SYNC_HIPPORAG_GRAPH"
RESEARCH_GRAPH = "RESEARCH_GRAPH"
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
    ORGANIZE_VAULT,
]
NOTE_PIPELINE_RANK = {
    job_type: rank for rank, job_type in enumerate(NOTE_PIPELINE_ORDER)
}


def calculate_pipeline_progress(
    jobs: list[JobRecord],
    *,
    note_paths_by_id: dict[int, str] | None = None,
    graph_note_ids: set[int] | None = None,
) -> list[dict[str, object]]:
    """Calculate progress from the stages actually queued for each note."""
    note_paths_by_id = note_paths_by_id or {}
    graph_note_ids = graph_note_ids or set()
    duration_samples: dict[str, list[float]] = {}
    for job in jobs:
        duration = _completed_duration_seconds(job)
        if duration is not None:
            duration_samples.setdefault(job.type, []).append(duration)
    duration_medians = {
        job_type: statistics.median(samples)
        for job_type, samples in duration_samples.items()
        if samples
    }
    by_note: dict[str, dict[str, object]] = {}
    for job in jobs:
        payload = parse_json(job.payload)
        note_id = int(job.note_id or payload.get("note_id") or 0)
        note_path = note_paths_by_id.get(note_id) or str(
            job.note_path or payload.get("note_path", "")
        )
        if not note_path or job.type not in NOTE_PIPELINE_RANK:
            continue
        run_key = (
            job.pipeline_run_id
            or payload.get("pipeline_run_id")
            or job.content_hash
            or payload.get("content_hash")
            or f"legacy:{note_path}"
        )
        note_state = by_note.setdefault(
            note_path, {"runKey": run_key, "jobs": {}, "noteId": note_id}
        )
        if note_state["runKey"] != run_key:
            continue
        latest_jobs = note_state["jobs"]
        if isinstance(latest_jobs, dict) and job.type not in latest_jobs:
            latest_jobs[job.type] = job
    result: list[dict[str, object]] = []
    for note_path, note_state in by_note.items():
        latest_jobs = note_state["jobs"]
        if not isinstance(latest_jobs, dict):
            continue
        statuses = {job_type: job.status for job_type, job in latest_jobs.items()}
        total = len(latest_jobs)
        completed = sum(status == COMPLETED for status in statuses.values())
        failed_jobs = [
            job for job in latest_jobs.values() if job.status in {FAILED, DEAD_LETTER}
        ]
        running_type = next(
            (
                job_type
                for job_type in NOTE_PIPELINE_ORDER
                if statuses.get(job_type) == RUNNING
            ),
            None,
        )
        pending_type = next(
            (
                job_type
                for job_type in NOTE_PIPELINE_ORDER
                if statuses.get(job_type) == PENDING
            ),
            None,
        )
        if failed_jobs:
            state = "failed"
        elif running_type:
            state = "processing"
        elif pending_type:
            state = "waiting"
        elif total and completed == total:
            state = "completed"
        else:
            state = "degraded"
        current_step = running_type or pending_type
        estimated_remaining = _estimated_remaining_seconds(
            latest_jobs, duration_medians
        )
        oldest_created = min(
            (job.created_at for job in latest_jobs.values() if job.created_at),
            default=None,
        )
        elapsed_seconds = (
            max(0.0, (utc_now() - normalize_utc(oldest_created)).total_seconds())
            if oldest_created
            else 0.0
        )
        raw_note_id = note_state.get("noteId")
        note_id = int(raw_note_id) if isinstance(raw_note_id, int | str) else 0
        graph_visible = note_id in graph_note_ids
        graph_job_status = statuses.get(EXPAND_KNOWLEDGE_GRAPH)
        graph_state = (
            "degraded"
            if graph_job_status in {FAILED, DEAD_LETTER}
            else "ready"
            if graph_job_status == COMPLETED
            else "enriching"
            if graph_visible
            else "waiting"
        )
        result.append(
            {
                "notePath": note_path,
                "pipelineRunId": note_state["runKey"],
                "completed": completed,
                "total": total,
                "percent": round(completed / total * 100) if total else 0,
                "state": state,
                "currentStep": current_step.replace("_", " ").title()
                if current_step
                else None,
                "elapsedSeconds": round(elapsed_seconds),
                "estimatedRemainingSeconds": (
                    round(estimated_remaining)
                    if estimated_remaining is not None
                    else None
                ),
                "estimateSampleCount": sum(
                    len(duration_samples.get(job_type, []))
                    for job_type, status in statuses.items()
                    if status in {PENDING, RUNNING}
                ),
                "graphVisible": graph_visible,
                "graphState": graph_state,
                "errors": [_pipeline_error(job) for job in failed_jobs[:3]],
            }
        )
    result.sort(
        key=lambda item: (
            item["state"] == "completed",
            cast(int, item["percent"]),
        ),
        reverse=True,
    )
    return result


def _completed_duration_seconds(job: JobRecord) -> float | None:
    if job.status != COMPLETED or not job.started_at or not job.completed_at:
        return None
    duration = (
        normalize_utc(job.completed_at) - normalize_utc(job.started_at)
    ).total_seconds()
    return duration if duration >= 0 else None


def _estimated_remaining_seconds(
    jobs: dict[str, JobRecord], duration_medians: dict[str, float]
) -> float | None:
    estimates: list[float] = []
    now = utc_now()
    for job_type, job in jobs.items():
        if job.status not in {PENDING, RUNNING}:
            continue
        expected = duration_medians.get(job_type)
        if expected is None:
            continue
        if job.status == RUNNING and job.started_at:
            elapsed = max(0.0, (now - normalize_utc(job.started_at)).total_seconds())
            estimates.append(max(0.0, expected - elapsed))
        else:
            estimates.append(expected)
    return sum(estimates) if estimates else None


def _pipeline_error(job: JobRecord) -> dict[str, object]:
    impacts = {
        GENERATE_EMBEDDING: "The note is saved, but semantic search may not find this version yet.",
        FIND_CONNECTIONS: "The note is saved, but graph connections may be incomplete.",
        GENERATE_GRAPH_INSIGHTS: "The note is saved, but new knowledge insights are unavailable.",
        EXPAND_KNOWLEDGE_GRAPH: "The note is saved, but its graph neighborhood may be stale.",
    }
    return {
        "jobId": job.id,
        "type": job.type,
        "message": job.error_message or f"{job.type.replace('_', ' ').title()} failed.",
        "impact": impacts.get(
            job.type,
            "The note is saved, but this cognitive stage did not complete.",
        ),
        "action": "Retry this job in Monitor or review the configured provider.",
    }


NOTE_CHANGED_PIPELINE_ORDER = [
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
    GENERATE_INFERRED_CONNECTIONS,
    EXPAND_CONCEPT_TO_NOTE,
    GENERATE_GRAPH_INSIGHTS,
    UPDATE_GRAPH_STATS,
    GENERATE_NOTE_TITLE,
    ORGANIZE_VAULT,
]
NOTE_PIPELINE_ATTEMPTS = {
    PARSE_NOTE: 3,
    CLASSIFY_NOTE: 2,
    ASSIMILATE_NOTE: 2,
    EXTRACT_CONCEPTS: 2,
    EXTRACT_ENTITIES: 2,
    DETECT_TOPICS: 2,
    EXTRACT_CONTEXT: 2,
    GENERATE_EMBEDDING: 2,
    FIND_CONNECTIONS: 2,
    EXPAND_KNOWLEDGE_GRAPH: 2,
    GENERATE_INFERRED_CONNECTIONS: 2,
    EXPAND_CONCEPT_TO_NOTE: 2,
    GENERATE_GRAPH_INSIGHTS: 2,
    UPDATE_GRAPH_STATS: 1,
    GENERATE_NOTE_TITLE: 2,
    ORGANIZE_VAULT: 2,
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
    autocommit: bool = True,
) -> JobRecord:
    payload_schema_version = validate_job_payload(job_type, payload)
    note_path = str(payload.get("note_path") or "")
    note_id = int(payload.get("note_id") or 0)
    content_hash = str(payload.get("content_hash") or "")
    pipeline_run_id = str(payload.get("pipeline_run_id") or "")
    idempotency_key = str(
        payload.get("idempotency_key")
        or (
            f"{job_type}:{note_path}:{content_hash}"
            if note_path and content_hash
            else ""
        )
    )
    if idempotency_key:
        existing = (
            session.execute(
                select(JobRecord).where(
                    JobRecord.idempotency_key == idempotency_key,
                    JobRecord.status.in_([PENDING, RUNNING]),
                )
            )
            .scalars()
            .first()
        )
        if existing is not None:
            return existing
    job = JobRecord(
        type=job_type,
        payload=compact_json(payload),
        payload_schema_version=payload_schema_version,
        note_id=note_id,
        note_path=note_path,
        content_hash=content_hash,
        pipeline_run_id=pipeline_run_id,
        idempotency_key=idempotency_key,
        status=PENDING,
        max_attempts=max_attempts,
    )
    session.add(job)
    if autocommit:
        session.commit()
        session.refresh(job)
    else:
        session.flush()
    return job


def supersede_missing_graph_artifact_jobs(session: Session) -> int:
    """Retire graph AI work whose target was pruned or deleted."""
    from berrybrain_api.models import (
        ConnectionRecord,
        GraphEdgeRecord,
        GraphNodeRecord,
        InsightRecord,
    )

    model_by_type = {
        "node": GraphNodeRecord,
        "edge": GraphEdgeRecord,
        "connection": ConnectionRecord,
        "insight": InsightRecord,
    }
    candidates = list(
        session.execute(
            select(JobRecord).where(
                JobRecord.type.in_((ENRICH_GRAPH_NODE, "JUDGE_ARTIFACT")),
                JobRecord.status.in_((PENDING, RUNNING, FAILED, DEAD_LETTER)),
            )
        ).scalars()
    )
    superseded = 0
    for job in candidates:
        try:
            payload = json.loads(job.payload or "{}")
        except (TypeError, json.JSONDecodeError):
            continue
        artifact_type = (
            "node" if job.type == ENRICH_GRAPH_NODE else payload.get("artifact_type")
        )
        artifact_id = payload.get("node_id") or payload.get("artifact_id")
        model = model_by_type.get(str(artifact_type or ""))
        if model is None or not str(artifact_id or "").isdigit():
            continue
        if session.get(model, int(artifact_id)) is not None:
            continue
        job.status = SUPERSEDED
        job.error_message = "Superseded because the graph artifact no longer exists"
        job.claimed_by = ""
        job.claim_token = ""
        job.lease_expires_at = None
        superseded += 1
    from berrybrain_api.semantic_enrichment import source_fingerprint

    enrichment_jobs = [job for job in candidates if job.type == ENRICH_GRAPH_NODE]
    for job in enrichment_jobs:
        try:
            payload = json.loads(job.payload or "{}")
            node = session.get(GraphNodeRecord, int(payload.get("node_id") or 0))
        except (TypeError, ValueError, json.JSONDecodeError):
            continue
        if node is None or job.status == SUPERSEDED:
            continue
        if str(payload.get("source_fingerprint") or "") == source_fingerprint(
            session, node
        ):
            continue
        job.status = SUPERSEDED
        job.error_message = "Superseded because the graph artifact changed"
        job.claimed_by = ""
        job.claim_token = ""
        job.lease_expires_at = None
        superseded += 1
    judge_jobs = [job for job in candidates if job.type == "JUDGE_ARTIFACT"]
    for job in judge_jobs:
        try:
            payload = json.loads(job.payload or "{}")
            artifact_type = str(payload.get("artifact_type") or "")
            model = model_by_type.get(artifact_type)
            artifact = (
                session.get(model, int(payload.get("artifact_id") or 0))
                if model is not None
                else None
            )
            queued_version = float(payload.get("artifact_version") or 0)
        except (TypeError, ValueError, json.JSONDecodeError):
            continue
        if artifact is None or job.status == SUPERSEDED:
            continue
        updated_at = getattr(artifact, "updated_at", None)
        if updated_at and updated_at.tzinfo is None:
            updated_at = updated_at.replace(tzinfo=UTC)
        current_version = updated_at.timestamp() if updated_at else 0
        if queued_version and abs(current_version - queued_version) <= 0.000001:
            continue
        job.status = SUPERSEDED
        job.error_message = "Superseded because the graph artifact changed"
        job.claimed_by = ""
        job.claim_token = ""
        job.lease_expires_at = None
        superseded += 1
    if superseded:
        session.flush()
    return superseded


def enqueue_job(
    session: Session,
    job_type: str,
    payload: dict[str, Any],
    *,
    priority: int = 0,
    max_attempts: int = 3,
    autocommit: bool = True,
) -> JobRecord:
    queued_payload = dict(payload)
    if priority:
        queued_payload.setdefault("priority", priority)
    return create_job(
        session,
        job_type,
        queued_payload,
        max_attempts=max_attempts,
        autocommit=autocommit,
    )


def enqueue_note_changed_jobs(
    session: Session,
    note_path: str,
    event_type: str,
    content_hash: str,
    affected_job_types: set[str] | None = None,
) -> list[JobRecord]:
    if event_type == "NOTE_DELETED":
        return enqueue_note_deleted_jobs(session, note_path, 0)

    pipeline_types = list(NOTE_CHANGED_PIPELINE_ORDER)
    if not _needs_generated_title(note_path):
        pipeline_types = [
            job_type for job_type in pipeline_types if job_type != GENERATE_NOTE_TITLE
        ]
    if affected_job_types is not None:
        pipeline_types = [
            job_type for job_type in pipeline_types if job_type in affected_job_types
        ]
    pipeline = [
        (job_type, NOTE_PIPELINE_ATTEMPTS.get(job_type, 2))
        for job_type in pipeline_types
    ]

    jobs: list[JobRecord] = []
    note = session.execute(
        select(NoteRecord).where(NoteRecord.path == note_path)
    ).scalar_one_or_none()
    note_id = note.id if note is not None else 0
    superseded = list(
        session.execute(
            select(JobRecord).where(
                JobRecord.note_path == note_path,
                JobRecord.content_hash != content_hash,
                JobRecord.status.in_([PENDING, RUNNING]),
            )
        ).scalars()
    )
    for old_job in superseded:
        old_job.status = SUPERSEDED
        old_job.error_message = "Superseded by newer note content"
        old_job.claimed_by = ""
        old_job.lease_expires_at = None

    for job_type, max_attempts in pipeline:
        existing = (
            session.execute(
                select(JobRecord).where(
                    JobRecord.type == job_type,
                    JobRecord.status.in_([PENDING, RUNNING]),
                    JobRecord.note_path == note_path,
                    JobRecord.content_hash == content_hash,
                )
            )
            .scalars()
            .first()
        )

        if existing is not None:
            continue

        payload = {
            "affected_job_types": sorted(affected_job_types)
            if affected_job_types is not None
            else "full",
            "content_hash": content_hash,
            "event_type": event_type,
            "note_id": note_id,
            "note_path": note_path,
        }
        job = create_job(session, job_type, payload, max_attempts=max_attempts)
        jobs.append(job)
        create_automation_log(
            session,
            action_type="ENQUEUE_JOB",
            target_type="note",
            target_id=note_path,
            description=f"Created {job_type} job for {event_type}",
            before_state={},
            after_state={"job_id": job.id, "job_type": job_type, "payload": payload},
            reversible=False,
        )

    return jobs


def enqueue_note_deleted_jobs(
    session: Session, note_path: str, note_id: int
) -> list[JobRecord]:
    pipeline = (
        EXPAND_KNOWLEDGE_GRAPH,
        GENERATE_GRAPH_INSIGHTS,
        UPDATE_GRAPH_CLUSTERS,
        UPDATE_GRAPH_STATS,
        SYNC_HIPPORAG_GRAPH,
    )
    jobs: list[JobRecord] = []
    for job_type in pipeline:
        payload = {
            "deleted_note_id": note_id,
            "deleted_note_path": note_path,
            "event_type": "NOTE_DELETED",
            "idempotency_key": f"note-deleted:{note_id}:{note_path}:{job_type}",
        }
        jobs.append(
            create_job(
                session,
                job_type,
                payload,
                max_attempts=NOTE_PIPELINE_ATTEMPTS.get(job_type, 2),
            )
        )
    return jobs


def _needs_generated_title(note_path: str) -> bool:
    filename = note_path.rsplit("/", 1)[-1].lower()
    return filename.startswith("untitled-note")


def affected_job_types_for_note_update(
    old_content: str, new_content: str, note_path: str
) -> set[str]:
    if old_content == new_content:
        return set()

    old_body = _markdown_body(old_content)
    new_body = _markdown_body(new_content)

    if _normalized_text(old_content) == _normalized_text(new_content):
        return {PARSE_NOTE, UPDATE_GRAPH_STATS}

    if old_body == new_body:
        return {
            PARSE_NOTE,
            ASSIMILATE_NOTE,
            EXTRACT_CONTEXT,
            EXPAND_KNOWLEDGE_GRAPH,
            GENERATE_GRAPH_INSIGHTS,
            UPDATE_GRAPH_STATS,
        }

    affected = set(NOTE_CHANGED_PIPELINE_ORDER)
    if not _needs_generated_title(note_path):
        affected.discard(GENERATE_NOTE_TITLE)
    return affected


def _markdown_body(content: str) -> str:
    match = re.match(r"^---\s*\n.*?\n---\s*\n", content or "", re.DOTALL)
    if match:
        return content[match.end() :]
    return content or ""


def _normalized_text(content: str) -> str:
    return " ".join((content or "").split())


def claim_next_job(
    session: Session,
    stale_after_minutes: int = 30,
    claimed_by: str = "api-worker",
    lease_minutes: int = 30,
) -> JobRecord | None:
    recover_stale_running_jobs(session, stale_after_minutes)

    candidates = list(
        session.execute(
            select(JobRecord)
            .where(
                JobRecord.status == PENDING,
                JobRecord.attempts < JobRecord.max_attempts,
            )
            .order_by(JobRecord.created_at.asc(), JobRecord.id.asc())
            .limit(500)
        ).scalars()
    )
    eligible: list[JobRecord] = []
    references_changed = False
    for candidate in candidates:
        reference_status = canonicalize_job_note_reference(session, candidate)
        if reference_status in {"note_missing", "content_changed"}:
            candidate.status = SUPERSEDED
            candidate.error_message = (
                "Superseded because the source note no longer exists"
                if reference_status == "note_missing"
                else "Superseded by newer note content"
            )
            references_changed = True
            continue
        if reference_status == "refreshed":
            references_changed = True
        if _job_dependencies_satisfied(session, candidate):
            eligible.append(candidate)
    job = eligible[0] if eligible else None
    if job is None:
        if references_changed:
            session.commit()
        return None

    now = utc_now()
    lease_expires_at = now + timedelta(minutes=lease_minutes)
    result = cast(
        CursorResult[Any],
        session.execute(
            update(JobRecord)
            .where(
                JobRecord.id == job.id,
                JobRecord.status == PENDING,
                JobRecord.attempts < JobRecord.max_attempts,
            )
            .values(
                status=RUNNING,
                attempts=JobRecord.attempts + 1,
                started_at=now,
                lease_expires_at=lease_expires_at,
                claimed_by=claimed_by[:120],
                claim_token=uuid4().hex,
            )
        ),
    )
    if result.rowcount != 1:
        session.rollback()
        return None
    session.commit()
    claimed = session.get(JobRecord, job.id)
    if claimed is not None:
        begin_job_attempt(session, claimed)
        session.commit()
    return claimed


def canonicalize_job_note_reference(session: Session, job: JobRecord) -> str:
    """Refresh a queued note path without processing newer note content."""
    payload = parse_json(job.payload)
    if not isinstance(payload, dict):
        return "unchanged"
    try:
        note_id = int(job.note_id or payload.get("note_id") or 0)
    except (TypeError, ValueError):
        return "unchanged"
    if not note_id:
        return "unchanged"
    note = session.get(NoteRecord, note_id)
    if note is None:
        return "note_missing"
    content_hash = str(job.content_hash or payload.get("content_hash") or "")
    if content_hash and note.content_hash and content_hash != note.content_hash:
        return "content_changed"
    old_path = str(job.note_path or payload.get("note_path") or "")
    if not note.path or note.path == old_path:
        return "unchanged"
    payload["note_id"] = note.id
    payload["note_path"] = note.path
    job.note_id = note.id
    job.note_path = note.path
    job.payload = compact_json(payload)
    old_default_key = (
        f"{job.type}:{old_path}:{content_hash}" if old_path and content_hash else ""
    )
    if old_default_key and job.idempotency_key == old_default_key:
        job.idempotency_key = f"{job.type}:{note.path}:{content_hash}"
    return "refreshed"


def recover_stale_running_jobs(session: Session, stale_after_minutes: int = 30) -> int:
    cutoff = utc_now() - timedelta(minutes=stale_after_minutes)
    stale_count = 0
    running_jobs = session.execute(
        select(JobRecord).where(JobRecord.status.in_([RUNNING, CANCEL_REQUESTED]))
    ).scalars()

    for job in running_jobs:
        lease_expired = (
            job.lease_expires_at and normalize_utc(job.lease_expires_at) <= utc_now()
        )
        legacy_started_expired = (
            job.lease_expires_at is None
            and job.started_at
            and normalize_utc(job.started_at) <= cutoff
        )
        if lease_expired or legacy_started_expired:
            if job.status == CANCEL_REQUESTED:
                job.status = CANCELLED
                job.completed_at = utc_now()
                job.error_message = None
            elif job.attempts >= job.max_attempts:
                job.status = DEAD_LETTER
                job.completed_at = utc_now()
                job.error_message = "Stale running job exhausted attempts"
            else:
                job.status = PENDING
                job.error_message = "Recovered stale running job"
            job.started_at = None
            job.lease_expires_at = None
            job.claimed_by = ""
            job.claim_token = ""
            stale_count += 1
            create_automation_log(
                session,
                action_type="RECOVER_STALE_JOB",
                target_type="job",
                target_id=str(job.id),
                description=f"Recovered stale {job.type} job as {job.status}",
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
    note_path = job.note_path
    content_hash = job.content_hash
    if not note_path and isinstance(payload, dict):
        note_path = str(payload.get("note_path") or "")
        content_hash = str(payload.get("content_hash") or "")
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
        JobRecord.note_path == note_path,
    )
    if content_hash:
        query = query.where(JobRecord.content_hash == content_hash)

    return session.execute(query.limit(1)).scalar_one_or_none() is None


def renew_job_lease(
    session: Session,
    job_id: int,
    lease_minutes: int = 30,
    claim_token: str = "",
) -> JobRecord:
    job = get_job_or_404(session, job_id)
    _validate_claim_token(job, claim_token)
    if job.status != RUNNING:
        raise HTTPException(status_code=409, detail="Job is not running")
    job.lease_expires_at = utc_now() + timedelta(minutes=lease_minutes)
    session.commit()
    session.refresh(job)
    return job


def request_job_cancellation(session: Session, job_id: int) -> JobRecord:
    job = get_job_or_404(session, job_id)
    if job.status in {CANCEL_REQUESTED, CANCELLED}:
        return job
    if job.status not in {PENDING, RUNNING}:
        raise HTTPException(status_code=409, detail="Job can no longer be cancelled")

    previous_status = job.status
    job.status = CANCELLED if previous_status == PENDING else CANCEL_REQUESTED
    job.error_message = None
    if job.status == CANCELLED:
        job.completed_at = utc_now()
        job.claimed_by = ""
        job.claim_token = ""
        job.lease_expires_at = None
    create_automation_log(
        session,
        action_type="CANCEL_JOB",
        target_type="job",
        target_id=str(job.id),
        description=f"Cancellation requested for job {job.type}",
        before_state={"status": previous_status},
        after_state={"status": job.status},
        reversible=False,
        autocommit=False,
    )
    session.commit()
    session.refresh(job)
    return job


def acknowledge_job_cancellation(
    session: Session, job_id: int, claim_token: str = ""
) -> JobRecord:
    job = get_job_or_404(session, job_id)
    if job.status == CANCELLED:
        return job
    if job.status != CANCEL_REQUESTED:
        raise HTTPException(
            status_code=409, detail="Job cancellation was not requested"
        )
    if worker_message_processed(session, job, "cancelled", claim_token):
        return job
    _validate_claim_token(job, claim_token)
    if not consume_worker_message(session, job, "cancelled", claim_token):
        return job
    job.status = CANCELLED
    job.error_message = None
    job.claimed_by = ""
    job.claim_token = ""
    job.lease_expires_at = None
    job.completed_at = utc_now()
    create_automation_log(
        session,
        action_type="JOB_CANCELLED",
        target_type="job",
        target_id=str(job.id),
        description=f"Cancelled job {job.type}",
        before_state={"status": CANCEL_REQUESTED},
        after_state={"status": CANCELLED},
        reversible=False,
        autocommit=False,
    )
    session.commit()
    session.refresh(job)
    return job


def complete_job(session: Session, job_id: int, claim_token: str = "") -> JobRecord:
    job = get_job_or_404(session, job_id)
    if job.status == CANCEL_REQUESTED:
        raise HTTPException(status_code=409, detail="Job cancellation requested")
    if job.status == CANCELLED:
        return job
    if worker_message_processed(session, job, "complete", claim_token):
        return job
    _validate_claim_token(job, claim_token)
    if not consume_worker_message(session, job, "complete", claim_token):
        return job
    job.status = COMPLETED
    job.error_message = None
    job.claimed_by = ""
    job.claim_token = ""
    job.lease_expires_at = None
    job.completed_at = utc_now()
    finish_job_attempt(session, job, success=True, retryability="none")
    session.commit()
    session.refresh(job)
    return job


def fail_job(
    session: Session,
    job_id: int,
    error_message: str,
    claim_token: str = "",
    *,
    stage: str = "",
    error_class: str = "job_execution_error",
    error_code: str = "job_failed",
    retryability: str = "",
) -> JobRecord:
    job = get_job_or_404(session, job_id)
    if job.status in {CANCEL_REQUESTED, CANCELLED}:
        return acknowledge_job_cancellation(session, job_id, claim_token)
    if worker_message_processed(session, job, "fail", claim_token):
        return job
    _validate_claim_token(job, claim_token)
    if not consume_worker_message(session, job, "fail", claim_token):
        return job
    job.error_message = redact_text(error_message)[:4000]
    job.completed_at = utc_now()
    if stage:
        update_job_attempt(session, job, stage=stage)

    if job.attempts >= job.max_attempts:
        job.status = DEAD_LETTER
        job.claimed_by = ""
        job.claim_token = ""
        job.lease_expires_at = None
        finish_job_attempt(
            session,
            job,
            success=False,
            error_class=error_class,
            error_code=error_code,
            retryability=retryability or "permanent",
            dead_letter_reason=job.error_message or "",
        )
    else:
        job.status = PENDING
        job.started_at = None
        job.claimed_by = ""
        job.claim_token = ""
        job.lease_expires_at = None
        finish_job_attempt(
            session,
            job,
            success=False,
            error_class=error_class,
            error_code=error_code,
            retryability=retryability or "retryable",
        )

    if job.status == DEAD_LETTER:
        from berrybrain_api.notification_service import create_notification

        create_notification(
            session,
            notification_type="job_failed",
            title="Job needs attention",
            description=job.error_message
            or "A background job exhausted its retry budget.",
            action="Open Monitor",
            action_url="/brain?monitor=open",
            related_job_id=job.id,
        )

    session.commit()
    session.refresh(job)
    return job


def retry_job(session: Session, job_id: int) -> JobRecord:
    job = get_job_or_404(session, job_id)
    if job.status not in {FAILED, DEAD_LETTER}:
        raise HTTPException(status_code=409, detail="Only failed jobs can be retried")
    previous_status = job.status
    previous_error = job.error_message
    job.status = PENDING
    job.attempts = 0
    job.error_message = None
    job.started_at = None
    job.completed_at = None
    job.claimed_by = ""
    job.claim_token = ""
    job.lease_expires_at = None
    create_automation_log(
        session,
        action_type="RETRY_JOB",
        target_type="job",
        target_id=str(job.id),
        description=f"Retried job {job.type}",
        before_state={"status": previous_status, "error_message": previous_error},
        after_state={"status": PENDING, "attempts": 0},
        reversible=False,
    )
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
        "payload_schema_version": job.payload_schema_version,
        "note_id": job.note_id,
        "note_path": job.note_path,
        "content_hash": job.content_hash,
        "pipeline_run_id": job.pipeline_run_id,
        "idempotency_key": job.idempotency_key,
        "attempts": job.attempts,
        "max_attempts": job.max_attempts,
        "error_message": job.error_message,
        "claimed_by": job.claimed_by,
        "claim_token": job.claim_token,
        "created_at": serialize_datetime(job.created_at),
        "started_at": serialize_datetime(job.started_at),
        "lease_expires_at": serialize_datetime(job.lease_expires_at),
        "completed_at": serialize_datetime(job.completed_at),
    }


def get_job_or_404(session: Session, job_id: int) -> JobRecord:
    job = session.get(JobRecord, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


def _validate_claim_token(job: JobRecord, claim_token: str) -> None:
    if claim_token and claim_token != job.claim_token:
        raise HTTPException(status_code=409, detail="Job claim token is stale")


def compact_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def parse_json(value: str) -> Any:
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return {}


def serialize_datetime(value: datetime | None) -> str | None:
    if value is None:
        return None
    return normalize_utc(value).isoformat().replace("+00:00", "Z")


def utc_now() -> datetime:
    return datetime.now(UTC)


def normalize_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def should_generate_note_title(note_path: str) -> bool:
    name = note_path.rsplit("/", 1)[-1].removesuffix(".md")
    return name == "untitled-note" or name.startswith("untitled-note-")
