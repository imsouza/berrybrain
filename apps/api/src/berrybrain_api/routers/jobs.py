from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import func, select

from berrybrain_api.database import SessionLocal
from berrybrain_api.job_contracts import (
    canonical_job_counts,
    serialize_attempt,
    update_job_attempt,
)
from berrybrain_api.jobs import (
    COMPLETED,
    DEAD_LETTER,
    FAILED,
    PENDING,
    RUNNING,
    SUPERSEDED,
    calculate_pipeline_progress,
    claim_next_job,
    complete_job,
    create_job,
    fail_job,
    list_jobs,
    normalize_utc,
    recover_stale_running_jobs,
    renew_job_lease,
    request_job_cancellation,
    retry_job,
    serialize_job,
    utc_now,
)
from berrybrain_api.models import (
    GraphNodeRecord,
    JobAttemptRecord,
    JobRecord,
    NoteRecord,
)

router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])


class FailJobRequest(BaseModel):
    error_message: str = ""
    stage: str = ""
    error_class: str = "job_execution_error"
    error_code: str = "job_failed"
    retryability: str = ""


class UpdateAttemptRequest(BaseModel):
    stage: str | None = None
    active_ai_mode: str | None = None
    provider: str | None = None
    model: str | None = None
    model_call_id: str | None = None


@router.get("")
def list_jobs_endpoint(status: str | None = None, limit: int = 50) -> dict:
    with SessionLocal() as session:
        jobs = list_jobs(session, status=status, limit=min(limit, 200))
        return {"jobs": [serialize_job(j) for j in jobs]}


class CreateJobRequest(BaseModel):
    type: str
    payload: dict = {}


@router.post("", status_code=201)
def create_job_endpoint(req: CreateJobRequest) -> dict:
    with SessionLocal() as session:
        job = create_job(session, req.type, req.payload)
        return {"job": serialize_job(job)}


@router.post("/claim")
def claim_job_endpoint() -> dict:
    with SessionLocal() as session:
        job = claim_next_job(session)
        if job is None:
            return {"job": None}
        return {"job": serialize_job(job)}


@router.post("/recover-stale")
def recover_stale_endpoint(stale_after_minutes: int = 30) -> dict:
    with SessionLocal() as session:
        recovered = recover_stale_running_jobs(
            session, stale_after_minutes=max(1, stale_after_minutes)
        )
        return {"recovered": recovered}


@router.post("/{job_id}/renew-lease")
def renew_job_lease_endpoint(job_id: int, lease_minutes: int = 30) -> dict:
    with SessionLocal() as session:
        job = renew_job_lease(session, job_id, lease_minutes=max(1, lease_minutes))
        return {"job": serialize_job(job)}


@router.post("/{job_id}/retry")
def retry_job_endpoint(job_id: int) -> dict:
    with SessionLocal() as session:
        job = retry_job(session, job_id)
        return {"job": serialize_job(job)}


@router.post("/{job_id}/cancel")
def cancel_job_endpoint(job_id: int) -> dict:
    with SessionLocal() as session:
        job = request_job_cancellation(session, job_id)
        return {"job": serialize_job(job)}


@router.get("/{job_id}/cancellation")
def job_cancellation_endpoint(job_id: int) -> dict:
    with SessionLocal() as session:
        job = session.get(JobRecord, job_id)
        if job is None:
            return {"status": "not_found", "cancelRequested": False}
        return {
            "status": job.status,
            "cancelRequested": job.status == "cancel_requested",
            "job": serialize_job(job),
        }


@router.get("/health")
def jobs_health_endpoint(stale_after_minutes: int = 30) -> dict:
    cutoff = utc_now()
    with SessionLocal() as session:
        status_counts = dict(
            session.execute(
                select(JobRecord.status, func.count()).group_by(JobRecord.status)
            ).all()
        )
        type_failures = dict(
            session.execute(
                select(JobRecord.type, func.count())
                .where(JobRecord.status.in_([FAILED, DEAD_LETTER]))
                .group_by(JobRecord.type)
            ).all()
        )
        running = list(
            session.execute(
                select(JobRecord).where(JobRecord.status == RUNNING)
            ).scalars()
        )
        stale = [
            job
            for job in running
            if job.started_at
            and (cutoff - normalize_utc(job.started_at)).total_seconds()
            > max(1, stale_after_minutes) * 60
        ]
        has_active_work = bool(
            stale or status_counts.get(PENDING, 0) or status_counts.get(RUNNING, 0)
        )
        failed_count = status_counts.get(FAILED, 0) + status_counts.get(DEAD_LETTER, 0)
        has_failed_history = bool(failed_count)
        pending_count = int(status_counts.get(PENDING, 0) or 0)
        running_count = int(status_counts.get(RUNNING, 0) or 0)
        slo_status = (
            "breached" if stale else ("at_risk" if pending_count else "healthy")
        )
        return {
            "status": "degraded"
            if stale
            else (
                "processing"
                if has_active_work
                else ("ok_with_history" if has_failed_history else "ok")
            ),
            "counts": {
                "pending": status_counts.get(PENDING, 0),
                "running": status_counts.get(RUNNING, 0),
                "failed": failed_count,
                "dead_letter": status_counts.get(DEAD_LETTER, 0),
                "completed": status_counts.get("completed", 0),
            },
            "hasFailedHistory": has_failed_history,
            "staleRunning": [serialize_job(job) for job in stale[:20]],
            "failedByType": type_failures,
            "slo": {
                "status": slo_status,
                "pending": pending_count,
                "running": running_count,
                "staleRunning": len(stale),
                "policy": {
                    "pendingBreachSeconds": 1800,
                    "runningLeaseMinutes": max(1, stale_after_minutes),
                },
            },
            "canonicalCounts": canonical_job_counts(session),
        }


@router.get("/{job_id}/attempts")
def job_attempts_endpoint(job_id: int) -> dict:
    with SessionLocal() as session:
        attempts = list(
            session.execute(
                select(JobAttemptRecord)
                .where(JobAttemptRecord.job_id == job_id)
                .order_by(JobAttemptRecord.attempt.asc(), JobAttemptRecord.id.asc())
            ).scalars()
        )
        return {"attempts": [serialize_attempt(item) for item in attempts]}


@router.get("/pipeline-progress")
def pipeline_progress_endpoint() -> dict:
    """Per-note pipeline progress for active/recent jobs."""
    with SessionLocal() as session:
        jobs = list(
            session.execute(
                select(JobRecord)
                .where(
                    JobRecord.status.in_(
                        [PENDING, RUNNING, COMPLETED, FAILED, DEAD_LETTER, SUPERSEDED]
                    )
                )
                .order_by(JobRecord.created_at.desc())
                .limit(500)
            ).scalars()
        )
        note_paths_by_id = {
            note.id: note.path for note in session.execute(select(NoteRecord)).scalars()
        }
        graph_note_ids = {
            int(node.source_id)
            for node in session.execute(
                select(GraphNodeRecord).where(
                    GraphNodeRecord.type == "note",
                    GraphNodeRecord.status != "ignored",
                )
            ).scalars()
            if node.source_id is not None
        }
    return {
        "notes": calculate_pipeline_progress(
            jobs,
            note_paths_by_id=note_paths_by_id,
            graph_note_ids=graph_note_ids,
        )
    }


@router.post("/{job_id}/complete")
def complete_job_endpoint(job_id: int) -> dict:
    with SessionLocal() as session:
        job = complete_job(session, job_id)
        return {"job": serialize_job(job)}


@router.post("/{job_id}/fail")
def fail_job_endpoint(job_id: int, payload: FailJobRequest) -> dict:
    with SessionLocal() as session:
        job = fail_job(
            session,
            job_id,
            payload.error_message,
            stage=payload.stage,
            error_class=payload.error_class,
            error_code=payload.error_code,
            retryability=payload.retryability,
        )
        return {"job": serialize_job(job)}


@router.patch("/{job_id}/attempt")
def update_job_attempt_endpoint(job_id: int, payload: UpdateAttemptRequest) -> dict:
    with SessionLocal() as session:
        job = session.get(JobRecord, job_id)
        if job is None:
            return {"status": "not_found"}
        attempt = update_job_attempt(
            session,
            job,
            stage=payload.stage,
            active_ai_mode=payload.active_ai_mode,
            provider=payload.provider,
            model=payload.model,
            model_call_id=payload.model_call_id,
        )
        session.commit()
        return {"attempt": serialize_attempt(attempt)}


@router.get("/trace/{note_path:path}")
def trace_note_jobs_endpoint(note_path: str) -> dict:
    with SessionLocal() as session:
        jobs = list(
            session.execute(
                select(JobRecord)
                .where(JobRecord.note_path == note_path)
                .order_by(JobRecord.created_at.desc())
            ).scalars()
        )
        return {"jobs": [serialize_job(j) for j in jobs]}
