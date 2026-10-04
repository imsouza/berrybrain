"""Small, current job projections; lifetime counters stay SQL aggregates."""

from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from berrybrain_api.jobs import CANCEL_REQUESTED, COMPLETED, PENDING, RUNNING
from berrybrain_api.models import JobRecord

HISTORY_SAMPLE_PER_TYPE = 200


@dataclass
class HomeJobSnapshot:
    status_counts: Counter[str]
    type_counts: Counter[str]
    completed_by_type: Counter[str]
    active_by_type: Counter[str]
    completed_today: int
    last_completed_at: datetime | None
    running: list[Any]
    pending: list[Any]
    recent_completed: list[Any]


def home_job_snapshot(session: Session, now: datetime) -> HomeJobSnapshot:
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    rows = session.execute(
        select(
            JobRecord.status,
            JobRecord.type,
            func.count().label("total"),
            func.sum(
                case(
                    (
                        (JobRecord.completed_at >= start)
                        & (JobRecord.completed_at < start + timedelta(days=1)),
                        1,
                    ),
                    else_=0,
                )
            ).label("today"),
            func.max(JobRecord.completed_at).label("last_completed"),
        ).group_by(JobRecord.status, JobRecord.type)
    ).all()
    counts: Counter[str] = Counter()
    types: Counter[str] = Counter()
    completed_types: Counter[str] = Counter()
    active_types: Counter[str] = Counter()
    completed_today = 0
    last_completed = None
    for row in rows:
        counts[row.status] += row.total
        types[row.type] += row.total
        if row.status == COMPLETED:
            completed_types[row.type] += row.total
            completed_today += row.today
        if row.status in {RUNNING, CANCEL_REQUESTED, PENDING}:
            active_types[row.type] += row.total
        if row.last_completed is not None:
            last_completed = max(
                last_completed or row.last_completed, row.last_completed
            )

    fields = (
        JobRecord.id,
        JobRecord.type,
        JobRecord.status,
        JobRecord.payload,
        JobRecord.created_at,
        JobRecord.started_at,
        JobRecord.completed_at,
    )
    # Running rows are needed for elapsed-time estimates. Queue totals above
    # remain exact; only the oldest pending row is needed for the current label.
    running = list(
        session.execute(
            select(*fields)
            .where(JobRecord.status.in_([RUNNING, CANCEL_REQUESTED]))
            .order_by(JobRecord.started_at, JobRecord.id)
        ).all()
    )
    pending = list(
        session.execute(
            select(*fields)
            .where(JobRecord.status == PENDING)
            .order_by(JobRecord.created_at, JobRecord.id)
            .limit(1)
        ).all()
    )
    recent = list(
        session.execute(
            select(*fields)
            .where(JobRecord.status == COMPLETED)
            .order_by(JobRecord.completed_at.desc(), JobRecord.id.desc())
            .limit(8)
        ).all()
    )
    return HomeJobSnapshot(
        counts,
        types,
        completed_types,
        active_types,
        completed_today,
        last_completed,
        running,
        pending,
        recent,
    )


def recent_duration_samples(session: Session, job_types: Counter[str]) -> list[Any]:
    """Bounded per-type samples, without historical payloads or error messages."""
    result = []
    for job_type in sorted(job_types):
        result.extend(
            session.execute(
                select(
                    JobRecord.type,
                    JobRecord.status,
                    JobRecord.started_at,
                    JobRecord.completed_at,
                )
                .where(
                    JobRecord.type == job_type,
                    JobRecord.status == COMPLETED,
                    JobRecord.started_at.is_not(None),
                    JobRecord.completed_at > JobRecord.started_at,
                )
                .order_by(JobRecord.completed_at.desc())
                .limit(HISTORY_SAMPLE_PER_TYPE)
            ).all()
        )
    return result
