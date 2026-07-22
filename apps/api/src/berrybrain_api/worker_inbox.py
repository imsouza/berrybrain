from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from berrybrain_api.models import JobRecord, WorkerInboxRecord


def consume_worker_message(
    session: Session,
    job: JobRecord,
    message_type: str,
    claim_token: str = "",
) -> bool:
    token = claim_token or job.claim_token or f"legacy-attempt-{job.attempts}"
    message_id = worker_message_id(job.id, token, message_type)
    existing = session.execute(
        select(WorkerInboxRecord.id).where(WorkerInboxRecord.message_id == message_id)
    ).scalar_one_or_none()
    if existing is not None:
        return False

    try:
        with session.begin_nested():
            session.add(
                WorkerInboxRecord(
                    message_id=message_id,
                    job_id=job.id,
                    message_type=message_type,
                    claim_token=token,
                    status="processed",
                )
            )
            session.flush()
    except IntegrityError:
        return False
    return True


def worker_message_processed(
    session: Session,
    job: JobRecord,
    message_type: str,
    claim_token: str = "",
) -> bool:
    token = claim_token or job.claim_token or f"legacy-attempt-{job.attempts}"
    return (
        session.execute(
            select(WorkerInboxRecord.id).where(
                WorkerInboxRecord.message_id
                == worker_message_id(job.id, token, message_type)
            )
        ).scalar_one_or_none()
        is not None
    )


def worker_message_id(job_id: int, claim_token: str, message_type: str) -> str:
    return f"job:{job_id}:{claim_token}:{message_type}"
