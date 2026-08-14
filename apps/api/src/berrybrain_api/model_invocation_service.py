from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Literal

from sqlalchemy import select
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.orm import Session, sessionmaker

from berrybrain_api.models import ModelInvocationRecord
from berrybrain_api.redaction import redact_text

InvocationStatus = Literal["running", "completed", "failed", "cancelled"]


@dataclass(frozen=True)
class ModelInvocationHandle:
    invocation_id: int
    bind: Engine | Connection


def start_model_invocation(
    session: Session | None,
    *,
    capability: str,
    provider: str,
    model: str,
    prompt_version: str,
    remote: bool,
    input_units: int,
    correlation_id: str = "",
) -> ModelInvocationHandle | None:
    if session is None:
        return None
    bind = session.get_bind()
    try:
        with _ledger_session(bind) as ledger:
            record = ModelInvocationRecord(
                capability=capability[:80],
                provider=provider[:80],
                model=model[:160],
                prompt_version=prompt_version[:80],
                status="running",
                remote=remote,
                input_units=max(0, input_units),
                correlation_id=correlation_id[:128],
                started_at=datetime.now(UTC),
            )
            ledger.add(record)
            ledger.commit()
            ledger.refresh(record)
            return ModelInvocationHandle(record.id, bind)
    except Exception:
        # Observability must never make a cognitive operation unavailable.
        return None


def finish_model_invocation(
    handle: ModelInvocationHandle | None,
    *,
    status: InvocationStatus,
    latency_ms: int,
    output_units: int = 0,
    attempt_count: int = 1,
    error: BaseException | None = None,
) -> None:
    if handle is None:
        return
    try:
        with _ledger_session(handle.bind) as ledger:
            record = ledger.get(ModelInvocationRecord, handle.invocation_id)
            if record is None:
                return
            record.status = status
            record.latency_ms = max(0, latency_ms)
            record.output_units = max(0, output_units)
            record.attempt_count = max(1, attempt_count)
            record.completed_at = datetime.now(UTC)
            if error is not None:
                record.error_class = type(error).__name__[:120]
                record.error_message = _safe_error_message(error)
            ledger.commit()
    except Exception:
        return


def reconcile_stale_model_invocations(
    session: Session, *, stale_after_minutes: int = 30
) -> int:
    cutoff = datetime.now(UTC) - timedelta(minutes=max(1, stale_after_minutes))
    records = list(
        session.execute(
            select(ModelInvocationRecord).where(
                ModelInvocationRecord.status == "running",
                ModelInvocationRecord.started_at < cutoff,
            )
        ).scalars()
    )
    completed_at = datetime.now(UTC)
    for record in records:
        record.status = "failed"
        record.error_class = "StaleModelInvocation"
        record.error_message = (
            "The model invocation exceeded its execution lease and was reconciled."
        )
        record.completed_at = completed_at
        started_at = record.started_at.replace(tzinfo=UTC)
        record.latency_ms = max(
            0, int((completed_at - started_at).total_seconds() * 1000)
        )
    return len(records)


def _ledger_session(bind: Engine | Connection) -> Session:
    factory = sessionmaker(bind=bind, autoflush=False, expire_on_commit=False)
    return factory()


def _safe_error_message(error: BaseException) -> str:
    name = type(error).__name__
    if name == "GraphAIUnavailable":
        return redact_text(str(error))[:1000]
    if name in {"TimeoutError", "CancelledError"}:
        return "Model request timed out or was cancelled."
    if name in {"JSONDecodeError", "ValueError", "KeyError"}:
        return "The model returned an invalid structured response."
    if name == "HTTPError" and hasattr(error, "code"):
        return f"The provider returned HTTP {getattr(error, 'code', 'error')}."
    return "The model invocation failed. See the error class and provider logs."
