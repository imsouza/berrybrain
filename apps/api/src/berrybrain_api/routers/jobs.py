from fastapi import APIRouter
from pydantic import BaseModel

from berrybrain_api.database import SessionLocal
from berrybrain_api.jobs import (
    COMPLETED,
    FAILED,
    NOTE_PIPELINE_ORDER,
    NOTE_PIPELINE_RANK,
    PENDING,
    RUNNING,
    claim_next_job,
    complete_job,
    create_job,
    fail_job,
    list_jobs,
    normalize_utc,
    parse_json,
    recover_stale_running_jobs,
    renew_job_lease,
    serialize_job,
    utc_now,
)
from berrybrain_api.models import JobRecord
from sqlalchemy import func, select

router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])


class FailJobRequest(BaseModel):
    error_message: str = ""


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
                .where(JobRecord.status == FAILED)
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
        has_failed_history = bool(status_counts.get(FAILED, 0))
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
                "failed": status_counts.get(FAILED, 0),
                "completed": status_counts.get("completed", 0),
            },
            "hasFailedHistory": has_failed_history,
            "staleRunning": [serialize_job(job) for job in stale[:20]],
            "failedByType": type_failures,
        }


@router.get("/pipeline-progress")
def pipeline_progress_endpoint() -> dict:
    """Per-note pipeline progress for active/recent jobs."""
    total_steps = len(NOTE_PIPELINE_ORDER)
    with SessionLocal() as session:
        jobs = list(
            session.execute(
                select(JobRecord)
                .where(JobRecord.status.in_([PENDING, RUNNING, COMPLETED]))
                .order_by(JobRecord.created_at.desc())
                .limit(500)
            ).scalars()
        )
    by_note: dict[str, dict[str, str]] = {}
    for job in jobs:
        note_path = parse_json(job.payload).get("note_path", "")
        if not note_path or job.type not in NOTE_PIPELINE_RANK:
            continue
        if note_path not in by_note:
            by_note[note_path] = {}
        prev = by_note[note_path].get(job.type)
        if prev == COMPLETED:
            continue
        by_note[note_path][job.type] = job.status
    result = []
    for note_path, statuses in by_note.items():
        completed = sum(1 for s in statuses.values() if s == COMPLETED)
        running_type = next((t for t, s in statuses.items() if s == RUNNING), None)
        result.append(
            {
                "notePath": note_path,
                "completed": completed,
                "total": total_steps,
                "percent": round(completed / total_steps * 100),
                "currentStep": running_type.replace("_", " ").title()
                if running_type
                else None,
            }
        )
    result.sort(key=lambda x: x["completed"], reverse=True)
    return {"notes": result}


@router.post("/{job_id}/complete")
def complete_job_endpoint(job_id: int) -> dict:
    with SessionLocal() as session:
        job = complete_job(session, job_id)
        return {"job": serialize_job(job)}


@router.post("/{job_id}/fail")
def fail_job_endpoint(job_id: int, payload: FailJobRequest) -> dict:
    with SessionLocal() as session:
        job = fail_job(session, job_id, payload.error_message)
        return {"job": serialize_job(job)}
