from fastapi import APIRouter, Header
from pydantic import BaseModel

from berrybrain_api.database import SessionLocal
from berrybrain_api.jobs import (
    CANCELLED,
    CANCEL_REQUESTED,
    COMPLETED,
    DEAD_LETTER,
    FAILED,
    PENDING,
    RUNNING,
    SUPERSEDED,
    acknowledge_job_cancellation,
    claim_next_job,
    calculate_pipeline_progress,
    complete_job,
    create_job,
    fail_job,
    list_jobs,
    normalize_utc,
    recover_stale_running_jobs,
    request_job_cancellation,
    renew_job_lease,
    retry_job,
    serialize_job,
    utc_now,
)
from berrybrain_api.models import JobRecord
from berrybrain_api.modules.jobs.domain import (
    QueueJobSnapshot,
    QueueSloPolicy,
    evaluate_queue_slo,
)
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
def renew_job_lease_endpoint(
    job_id: int,
    lease_minutes: int = 30,
    claim_token: str = Header(default="", alias="X-BerryBrain-Claim-Token"),
) -> dict:
    with SessionLocal() as session:
        job = renew_job_lease(
            session,
            job_id,
            lease_minutes=max(1, lease_minutes),
            claim_token=claim_token,
        )
        return {"job": serialize_job(job)}


@router.post("/{job_id}/retry")
def retry_job_endpoint(job_id: int) -> dict:
    with SessionLocal() as session:
        job = retry_job(session, job_id)
        return {"job": serialize_job(job)}


@router.get("/health")
def jobs_health_endpoint(stale_after_minutes: int = 30) -> dict:
    cutoff = utc_now()
    with SessionLocal() as session:
        status_counts: dict[str, int] = {
            str(status): int(count)
            for status, count in session.execute(
                select(JobRecord.status, func.count()).group_by(JobRecord.status)
            ).all()
        }
        type_failures: dict[str, int] = {
            str(job_type): int(count)
            for job_type, count in session.execute(
                select(JobRecord.type, func.count())
                .where(JobRecord.status.in_([FAILED, DEAD_LETTER]))
                .group_by(JobRecord.type)
            ).all()
        }
        running = list(
            session.execute(
                select(JobRecord).where(
                    JobRecord.status.in_([RUNNING, CANCEL_REQUESTED])
                )
            ).scalars()
        )
        slo_jobs = list(
            session.execute(
                select(JobRecord).where(
                    JobRecord.status.in_(
                        [PENDING, RUNNING, CANCEL_REQUESTED, DEAD_LETTER]
                    )
                )
            ).scalars()
        )
        queue_slo = evaluate_queue_slo(
            [
                QueueJobSnapshot(
                    status=job.status,
                    created_at=job.created_at,
                    started_at=job.started_at,
                )
                for job in slo_jobs
            ],
            now=cutoff,
            policy=QueueSloPolicy(
                running_breach_seconds=max(1, stale_after_minutes) * 60
            ),
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
        return {
            "status": "degraded"
            if queue_slo.status == "breached"
            else (
                "at_risk"
                if queue_slo.status == "at_risk"
                else "processing"
                if has_active_work
                else ("ok_with_history" if has_failed_history else "ok")
            ),
            "counts": {
                "pending": status_counts.get(PENDING, 0),
                "running": status_counts.get(RUNNING, 0),
                "cancel_requested": status_counts.get(CANCEL_REQUESTED, 0),
                "cancelled": status_counts.get(CANCELLED, 0),
                "failed": failed_count,
                "dead_letter": status_counts.get(DEAD_LETTER, 0),
                "completed": status_counts.get("completed", 0),
            },
            "hasFailedHistory": has_failed_history,
            "staleRunning": [serialize_job(job) for job in stale[:20]],
            "failedByType": type_failures,
            "slo": queue_slo.to_dict(),
        }


@router.get("/pipeline-progress")
def pipeline_progress_endpoint() -> dict:
    """Per-note pipeline progress for active/recent jobs."""
    with SessionLocal() as session:
        jobs = list(
            session.execute(
                select(JobRecord)
                .where(
                    JobRecord.status.in_(
                        [
                            PENDING,
                            RUNNING,
                            CANCEL_REQUESTED,
                            CANCELLED,
                            COMPLETED,
                            FAILED,
                            DEAD_LETTER,
                            SUPERSEDED,
                        ]
                    )
                )
                .order_by(JobRecord.created_at.desc())
                .limit(500)
            ).scalars()
        )
    return {"notes": calculate_pipeline_progress(jobs)}


@router.post("/{job_id}/complete")
def complete_job_endpoint(
    job_id: int,
    claim_token: str = Header(default="", alias="X-BerryBrain-Claim-Token"),
) -> dict:
    with SessionLocal() as session:
        job = complete_job(session, job_id, claim_token=claim_token)
        return {"job": serialize_job(job)}


@router.get("/{job_id}/cancellation")
def job_cancellation_endpoint(job_id: int) -> dict:
    with SessionLocal() as session:
        job = session.get(JobRecord, job_id)
        if job is None:
            return {"cancelRequested": False, "missing": True}
        return {
            "cancelRequested": job.status == CANCEL_REQUESTED,
            "status": job.status,
        }


@router.post("/{job_id}/cancel")
def cancel_job_endpoint(job_id: int) -> dict:
    with SessionLocal() as session:
        job = request_job_cancellation(session, job_id)
        return {"job": serialize_job(job)}


@router.post("/{job_id}/cancelled")
def acknowledge_job_cancellation_endpoint(
    job_id: int,
    claim_token: str = Header(default="", alias="X-BerryBrain-Claim-Token"),
) -> dict:
    with SessionLocal() as session:
        job = acknowledge_job_cancellation(session, job_id, claim_token=claim_token)
        return {"job": serialize_job(job)}


@router.post("/{job_id}/fail")
def fail_job_endpoint(
    job_id: int,
    payload: FailJobRequest,
    claim_token: str = Header(default="", alias="X-BerryBrain-Claim-Token"),
) -> dict:
    with SessionLocal() as session:
        job = fail_job(session, job_id, payload.error_message, claim_token=claim_token)
        return {"job": serialize_job(job)}
