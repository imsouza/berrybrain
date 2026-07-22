from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime


@dataclass(frozen=True, slots=True)
class QueueJobSnapshot:
    status: str
    created_at: datetime
    started_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class QueueSloPolicy:
    pending_warning_seconds: int = 10 * 60
    pending_breach_seconds: int = 30 * 60
    running_breach_seconds: int = 30 * 60


@dataclass(frozen=True, slots=True)
class QueueSloViolation:
    code: str
    severity: str
    message: str
    count: int


@dataclass(frozen=True, slots=True)
class QueueSloReport:
    status: str
    oldest_pending_age_seconds: int
    stale_running_count: int
    dead_letter_count: int
    violations: tuple[QueueSloViolation, ...]
    policy: QueueSloPolicy

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "oldestPendingAgeSeconds": self.oldest_pending_age_seconds,
            "staleRunningCount": self.stale_running_count,
            "deadLetterCount": self.dead_letter_count,
            "violations": [asdict(item) for item in self.violations],
            "policy": {
                "pendingWarningSeconds": self.policy.pending_warning_seconds,
                "pendingBreachSeconds": self.policy.pending_breach_seconds,
                "runningBreachSeconds": self.policy.running_breach_seconds,
            },
        }


def evaluate_queue_slo(
    jobs: list[QueueJobSnapshot],
    *,
    now: datetime | None = None,
    policy: QueueSloPolicy | None = None,
) -> QueueSloReport:
    measured_at = _utc(now or datetime.now(UTC))
    active_policy = policy or QueueSloPolicy()
    pending_ages = [
        max(0, int((measured_at - _utc(job.created_at)).total_seconds()))
        for job in jobs
        if job.status == "pending"
    ]
    oldest_pending = max(pending_ages, default=0)
    stale_running = sum(
        1
        for job in jobs
        if job.status in {"running", "cancel_requested"}
        and job.started_at is not None
        and (measured_at - _utc(job.started_at)).total_seconds()
        > active_policy.running_breach_seconds
    )
    dead_letters = sum(1 for job in jobs if job.status == "dead_letter")

    violations: list[QueueSloViolation] = []
    if dead_letters:
        violations.append(
            QueueSloViolation(
                code="dead_letters_present",
                severity="critical",
                message="Retry or inspect dead-letter jobs.",
                count=dead_letters,
            )
        )
    if stale_running:
        violations.append(
            QueueSloViolation(
                code="running_jobs_stale",
                severity="critical",
                message="Recover or cancel jobs that exceeded their running lease.",
                count=stale_running,
            )
        )
    if oldest_pending > active_policy.pending_breach_seconds:
        violations.append(
            QueueSloViolation(
                code="pending_age_breached",
                severity="critical",
                message="The oldest pending job exceeded the queue latency SLO.",
                count=sum(1 for job in jobs if job.status == "pending"),
            )
        )
    elif oldest_pending > active_policy.pending_warning_seconds:
        violations.append(
            QueueSloViolation(
                code="pending_age_warning",
                severity="warning",
                message="Pending jobs are approaching the queue latency SLO.",
                count=sum(1 for job in jobs if job.status == "pending"),
            )
        )

    status = (
        "breached"
        if any(v.severity == "critical" for v in violations)
        else ("at_risk" if violations else "healthy")
    )
    return QueueSloReport(
        status=status,
        oldest_pending_age_seconds=oldest_pending,
        stale_running_count=stale_running,
        dead_letter_count=dead_letters,
        violations=tuple(violations),
        policy=active_policy,
    )


def _utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)
