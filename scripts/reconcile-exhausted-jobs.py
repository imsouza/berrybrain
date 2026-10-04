"""Inspect explicitly selected exhausted pending jobs; --apply repairs state only.

Run inside the configured API environment. No model calls, retries or deletions.
"""

import argparse
import json

from berrybrain_api.automation_logs import create_automation_log
from berrybrain_api.database import SessionLocal
from berrybrain_api.jobs import DEAD_LETTER, PENDING, normalize_utc, utc_now
from berrybrain_api.models import JobRecord
from sqlalchemy import or_, update
from sqlalchemy.orm import Session


def reconcile_job(session: Session, job_id: int, *, apply: bool = False) -> dict:
    job = session.get(JobRecord, job_id)
    result = {"jobId": job_id, "applied": False, "eligible": False}
    if job is None:
        return {**result, "reason": "not_found"}
    result.update(
        status=job.status, attempts=job.attempts, maxAttempts=job.max_attempts
    )
    now = utc_now()
    if (
        job.status != PENDING
        or job.max_attempts < 1
        or job.attempts < job.max_attempts
        or (job.lease_expires_at and normalize_utc(job.lease_expires_at) > now)
    ):
        return {**result, "reason": "not_exhausted_pending_or_live_lease"}
    result["eligible"] = True
    if not apply:
        return {**result, "reason": "dry_run"}

    # Recheck in the write itself: an owner may have retried/cancelled the job
    # since the inspection. Never overwrite that concurrent decision.
    changed = session.execute(
        update(JobRecord)
        .where(
            JobRecord.id == job_id,
            JobRecord.status == PENDING,
            JobRecord.attempts == job.attempts,
            JobRecord.max_attempts == job.max_attempts,
            or_(
                JobRecord.lease_expires_at.is_(None), JobRecord.lease_expires_at <= now
            ),
        )
        .values(
            status=DEAD_LETTER,
            completed_at=job.completed_at or now,
            error_message=job.error_message
            or "Legacy pending job exhausted its retry budget",
            claimed_by="",
            claim_token="",
            lease_expires_at=None,
        )
        .execution_options(synchronize_session=False)
    )
    if changed.rowcount != 1:
        session.rollback()
        return {**result, "reason": "concurrent_change"}
    create_automation_log(
        session,
        action_type="RECONCILE_EXHAUSTED_JOB",
        target_type="job",
        target_id=str(job_id),
        description="Marked exhausted pending job as dead_letter without re-execution",
        before_state={
            "status": PENDING,
            "attempts": job.attempts,
            "max_attempts": job.max_attempts,
        },
        after_state={"status": DEAD_LETTER},
        reversible=False,
    )
    session.commit()
    return {**result, "applied": True, "status": DEAD_LETTER, "reason": "reconciled"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--job-id", type=int, action="append", required=True)
    parser.add_argument(
        "--apply", action="store_true", help="Apply audited state reconciliation"
    )
    args = parser.parse_args()
    if any(value < 1 for value in args.job_id):
        parser.error("Job IDs must be positive")
    results = []
    for job_id in dict.fromkeys(args.job_id):
        with SessionLocal() as session:
            results.append(reconcile_job(session, job_id, apply=args.apply))
    print(json.dumps({"dryRun": not args.apply, "jobs": results}))


if __name__ == "__main__":
    main()
