from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from berrybrain_api.models import JobAttemptRecord, JobRecord, ModelInvocationRecord

CURRENT_JOB_PAYLOAD_VERSION = 1

JOB_STAGES = (
    "claimed",
    "payload_validating",
    "dependencies_checking",
    "context_loading",
    "provider_resolving",
    "model_calling",
    "response_validating",
    "artifact_persisting",
    "judge_evaluating",
    "completed",
)

NOTE_JOB_TYPES = {
    "PARSE_NOTE",
    "CLASSIFY_NOTE",
    "ASSIMILATE_NOTE",
    "GENERATE_EMBEDDING",
    "FIND_CONNECTIONS",
    "GENERATE_INSIGHTS",
    "GENERATE_NOTE_TITLE",
    "EXPAND_KNOWLEDGE_GRAPH",
    "EXTRACT_CONCEPTS",
    "EXTRACT_CONTEXT",
    "EXTRACT_ENTITIES",
    "DETECT_TOPICS",
    "GENERATE_NODE_SUMMARY",
    "GENERATE_INFERRED_CONNECTIONS",
    "GENERATE_GRAPH_INSIGHTS",
    "UPDATE_GRAPH_CLUSTERS",
    "UPDATE_GRAPH_STATS",
    "EXPAND_CONCEPT_TO_NOTE",
    "ENRICH_GRAPH_NODE",
    "VALIDATE_GRAPH_NODE_WITH_WEB",
    "REASON_GRAPH_CONNECTION",
    "GENERATE_GRAPH_GAPS",
    "PRUNE_LOW_VALUE_GRAPH_NODES",
    "MERGE_DUPLICATE_GRAPH_NODES",
    "UPDATE_GRAPH_QUALITY",
    "PROCESS_ATTACHMENT",
    "CREATE_NOTE_FROM_INSIGHT",
    "CREATE_REVIEW_FROM_INSIGHT",
}


@dataclass(frozen=True)
class JobPayloadContract:
    current_version: int = CURRENT_JOB_PAYLOAD_VERSION
    required_fields: tuple[str, ...] = ()


JOB_PAYLOAD_REGISTRY: dict[str, JobPayloadContract] = {
    job_type: JobPayloadContract() for job_type in NOTE_JOB_TYPES
}
JOB_PAYLOAD_REGISTRY.update(
    {
        "ENRICH_GRAPH_NODE": JobPayloadContract(required_fields=("node_id",)),
        "JUDGE_ARTIFACT": JobPayloadContract(
            required_fields=(
                "artifact_type",
                "artifact_id",
                "artifact_version",
                "judge_config_version",
            )
        ),
        "RESEARCH_GRAPH": JobPayloadContract(required_fields=("research_run_id",)),
        "ENRICH_GRAPH_DELTA": JobPayloadContract(required_fields=("graph_version",)),
    }
)


class JobPayloadError(ValueError):
    def __init__(self, code: str, detail: str):
        super().__init__(detail)
        self.code = code
        self.retryable = False


def judge_artifact_payload(
    session: Session,
    artifact_type: str,
    artifact_id: int,
    artifact_version: str,
) -> dict[str, Any]:
    from berrybrain_api.ai_configuration import load_configuration

    configuration = load_configuration(session)
    judge_config_version = (
        configuration.configuration_fingerprint
        if configuration
        else "configuration-required"
    )
    version = artifact_version or "1"
    return {
        "artifact_type": artifact_type,
        "artifact_id": artifact_id,
        "artifact_version": version,
        "judge_config_version": judge_config_version,
        "idempotency_key": (
            f"judge:{artifact_type}:{artifact_id}:{version}:{judge_config_version}"
        ),
    }


def validate_job_payload(job_type: str, payload: dict[str, Any]) -> int:
    contract = JOB_PAYLOAD_REGISTRY.get(job_type)
    if contract is None:
        raise JobPayloadError(
            "unsupported_job_type", f"Unsupported job type: {job_type}"
        )
    raw_version = payload.get("payload_schema_version", CURRENT_JOB_PAYLOAD_VERSION)
    try:
        version = int(raw_version)
    except (TypeError, ValueError) as exc:
        raise JobPayloadError(
            "invalid_payload_version", "payload_schema_version must be an integer"
        ) from exc
    if version != contract.current_version:
        raise JobPayloadError(
            "unsupported_payload_version",
            f"{job_type} payload version {version} is not supported",
        )
    missing = [name for name in contract.required_fields if not payload.get(name)]
    if missing:
        raise JobPayloadError(
            "invalid_payload",
            f"{job_type} requires: {', '.join(missing)}",
        )
    return version


def begin_job_attempt(session: Session, job: JobRecord) -> JobAttemptRecord:
    payload = _json_object(job.payload)
    existing = session.execute(
        select(JobAttemptRecord).where(
            JobAttemptRecord.job_id == job.id,
            JobAttemptRecord.attempt == job.attempts,
            JobAttemptRecord.finished_at.is_(None),
        )
    ).scalar_one_or_none()
    if existing is not None:
        return existing
    attempt = JobAttemptRecord(
        job_id=job.id,
        job_type=job.type,
        payload_schema_version=job.payload_schema_version,
        run_id=job.pipeline_run_id,
        dependency_ids=json.dumps(payload.get("depends_on") or []),
        note_id=job.note_id,
        note_version=str(payload.get("note_version") or ""),
        content_hash=job.content_hash,
        artifact_id=str(payload.get("artifact_id") or ""),
        artifact_version=str(payload.get("artifact_version") or ""),
        attempt=job.attempts,
        stage="claimed",
    )
    session.add(attempt)
    session.flush()
    return attempt


def update_job_attempt(
    session: Session,
    job: JobRecord,
    *,
    stage: str | None = None,
    active_ai_mode: str | None = None,
    provider: str | None = None,
    model: str | None = None,
    model_call_id: str | None = None,
) -> JobAttemptRecord:
    attempt = begin_job_attempt(session, job)
    if stage is not None:
        if stage not in JOB_STAGES:
            raise ValueError(f"Unknown job stage: {stage}")
        attempt.stage = stage
    if active_ai_mode is not None:
        attempt.active_ai_mode = active_ai_mode[:20]
    if provider is not None:
        attempt.resolved_provider = provider[:80]
    if model is not None:
        attempt.resolved_model = model[:160]
    if model_call_id is not None:
        attempt.model_call_started = True
        attempt.model_call_id = model_call_id[:128]
    session.flush()
    return attempt


def finish_job_attempt(
    session: Session,
    job: JobRecord,
    *,
    success: bool,
    error_class: str = "",
    error_code: str = "",
    retryability: str = "unknown",
    dead_letter_reason: str = "",
) -> JobAttemptRecord:
    attempt = begin_job_attempt(session, job)
    now = datetime.now(UTC)
    started = attempt.started_at
    if started.tzinfo is None:
        started = started.replace(tzinfo=UTC)
    attempt.finished_at = now
    attempt.duration_ms = max(0, int((now - started).total_seconds() * 1000))
    attempt.stage = "completed" if success else attempt.stage
    attempt.error_class = error_class[:120]
    attempt.error_code = error_code[:80]
    attempt.retryability = retryability[:30]
    attempt.dead_letter_reason = dead_letter_reason[:4000]
    session.flush()
    return attempt


def canonical_job_counts(session: Session) -> dict[str, int]:
    rows = dict(
        session.execute(
            select(JobRecord.status, func.count(JobRecord.id)).group_by(
                JobRecord.status
            )
        ).all()
    )
    attempt_errors = session.scalar(
        select(func.count(JobAttemptRecord.id)).where(JobAttemptRecord.error_code != "")
    )
    api_model_calls = session.scalar(select(func.count(ModelInvocationRecord.id))) or 0
    worker_model_calls = (
        session.scalar(
            select(func.count(JobAttemptRecord.id)).where(
                JobAttemptRecord.model_call_started.is_(True)
            )
        )
        or 0
    )
    return {
        "total_jobs": sum(int(value) for value in rows.values()),
        "pending": int(rows.get("pending", 0)),
        "active": int(rows.get("running", 0)),
        "completed": int(rows.get("completed", 0)),
        "failed_retryable": int(rows.get("failed", 0)),
        "failed_permanent": 0,
        "dead_letter": int(rows.get("dead_letter", 0)),
        "cancelled": int(rows.get("cancelled", 0)),
        "attempt_errors": int(attempt_errors or 0),
        "model_calls": int(api_model_calls) + int(worker_model_calls),
    }


def serialize_attempt(attempt: JobAttemptRecord) -> dict[str, Any]:
    return {
        "id": attempt.id,
        "jobId": attempt.job_id,
        "jobType": attempt.job_type,
        "payloadSchemaVersion": attempt.payload_schema_version,
        "runId": attempt.run_id,
        "dependencyIds": _json_list(attempt.dependency_ids),
        "noteId": attempt.note_id,
        "noteVersion": attempt.note_version,
        "contentHash": attempt.content_hash,
        "artifactId": attempt.artifact_id,
        "artifactVersion": attempt.artifact_version,
        "activeAiMode": attempt.active_ai_mode,
        "resolvedProvider": attempt.resolved_provider,
        "resolvedModel": attempt.resolved_model,
        "stage": attempt.stage,
        "attempt": attempt.attempt,
        "modelCallStarted": attempt.model_call_started,
        "modelCallId": attempt.model_call_id,
        "errorClass": attempt.error_class,
        "errorCode": attempt.error_code,
        "retryability": attempt.retryability,
        "deadLetterReason": attempt.dead_letter_reason,
        "startedAt": _iso(attempt.started_at),
        "finishedAt": _iso(attempt.finished_at),
        "durationMs": attempt.duration_ms,
    }


def _json_object(raw: str) -> dict[str, Any]:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}


def _json_list(raw: str) -> list[Any]:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return []
    return value if isinstance(value, list) else []


def _iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")
