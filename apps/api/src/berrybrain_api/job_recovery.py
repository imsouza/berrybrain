"""Bounded, deterministic recovery of exhausted jobs; never a bulk replay."""

from __future__ import annotations

import json
import math
from datetime import timedelta

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from berrybrain_api.automation_logs import create_automation_log
from berrybrain_api.job_contracts import JobPayloadError, validate_job_payload
from berrybrain_api.job_repair import _semantic_source_issue
from berrybrain_api.jobs import canonicalize_job_note_reference, normalize_utc, utc_now
from berrybrain_api.models import (
    ConnectionRecord,
    GraphEdgeRecord,
    GraphNodeRecord,
    InsightRecord,
    JobAttemptRecord,
    JobRecord,
    NoteRecord,
    SettingRecord,
)

STATE_KEY = "internal_job_recovery_state"
GLOBAL_TYPES = {"UPDATE_GRAPH_STATS", "UPDATE_GRAPH_CLUSTERS", "UPDATE_GRAPH_QUALITY"}
SAFE_TYPES = GLOBAL_TYPES | {
    "PARSE_NOTE",
    "CLASSIFY_NOTE",
    "ASSIMILATE_NOTE",
    "GENERATE_EMBEDDING",
    "FIND_CONNECTIONS",
    "EXTRACT_CONCEPTS",
    "EXTRACT_ENTITIES",
    "EXTRACT_CONTEXT",
    "DETECT_TOPICS",
    "EXPAND_KNOWLEDGE_GRAPH",
    "GENERATE_INFERRED_CONNECTIONS",
    "ENRICH_GRAPH_NODE",
    "JUDGE_ARTIFACT",
}
DELAYS = (300, 1800, 7200)


def transient_failure(message: str) -> bool:
    text = (message or "").lower()
    # Permanent provider/data errors take precedence over incidental timeout text.
    if any(
        part in text
        for part in (
            "http 400",
            "http 401",
            "http 403",
            "http 404",
            "invalid api key",
            "unauthorized",
            "not available",
            "not supported",
            "does not provide",
            "insufficient",
            "quota",
            "invalid or no longer supported",
            "permission",
        )
    ):
        return False
    return any(
        part in text
        for part in (
            "stale running",
            "timed out",
            "timeout",
            "could not reach",
            "connectivity",
            "connection error",
            "connection reset",
            "circuit",
            "temporarily",
            "http 408",
            "http 429",
            "http 500",
            "http 502",
            "http 503",
            "http 504",
        )
    )


def _source_state(session: Session, job: JobRecord, payload: dict) -> str:
    issue = _semantic_source_issue(session, job, payload)
    if issue:
        return issue
    if job.type == "JUDGE_ARTIFACT":
        model = {
            "node": GraphNodeRecord,
            "edge": GraphEdgeRecord,
            "insight": InsightRecord,
            "connection": ConnectionRecord,
        }.get(payload.get("artifact_type"))
        artifact = (
            session.get(model, int(payload.get("artifact_id") or 0)) if model else None
        )
        if artifact is None:
            return "artifact_missing"
        # Judge's queue contract uses updated_at timestamps, not the graph's
        # independent integer artifact_version counter.
        updated_at = getattr(artifact, "updated_at", None)
        version = float(payload.get("artifact_version", ""))
        if not updated_at or not math.isfinite(version):
            return "unverified_source"
        if abs(normalize_utc(updated_at).timestamp() - version) > 0.000001:
            return "artifact_changed"
        from berrybrain_api.ai_configuration import load_configuration

        configuration = load_configuration(session)
        fingerprint = (
            configuration.configuration_fingerprint
            if configuration
            else "configuration-required"
        )
        return (
            "configuration_changed"
            if payload.get("judge_config_version") != fingerprint
            else ""
        )
    note_id = int(job.note_id or payload.get("note_id") or 0)
    path = str(job.note_path or payload.get("note_path") or "")
    if not note_id and not path:
        return (
            ""
            if job.type in GLOBAL_TYPES or job.type == "ENRICH_GRAPH_NODE"
            else "unverified_source"
        )
    note = (
        session.get(NoteRecord, note_id)
        if note_id
        else session.scalar(select(NoteRecord).where(NoteRecord.path == path))
    )
    if note is None:
        return "note_missing"
    content_hash = str(job.content_hash or payload.get("content_hash") or "")
    if not content_hash:
        return "unverified_source"
    if content_hash != note.content_hash:
        return "content_changed"
    return canonicalize_job_note_reference(session, job) if note_id else ""


def _maintenance_covers(job_type: str, older: dict, newer: dict) -> bool:
    """Never replace a global failure with a scoped/legacy note update."""
    if newer.get("note_id") or newer.get("note_path"):
        return False
    ignored = {"_automatic_recovery", "payload_schema_version"}
    old = {key: value for key, value in older.items() if key not in ignored}
    new = {key: value for key, value in newer.items() if key not in ignored}
    if job_type != "UPDATE_GRAPH_STATS":
        return old == new
    old_nodes = old.pop("affected_node_ids", None) or old.get("scope_node_ids") or []
    new_nodes = new.pop("affected_node_ids", None) or new.get("scope_node_ids") or []
    old.pop("scope_node_ids", None)
    new.pop("scope_node_ids", None)
    if not isinstance(old_nodes, list) or not isinstance(new_nodes, list):
        return False
    if any(type(node) is not int for node in old_nodes + new_nodes):
        return False
    return old == new and (
        not new_nodes or bool(old_nodes) and set(old_nodes) <= set(new_nodes)
    )


def recover_exhausted_jobs(session: Session) -> dict[str, int]:
    """Run at most once/minute, scan 50 rows, admit one retry/5 minutes globally.

    CAS on a durable setting serializes supervisors. Recovery extends the same
    job by ONE attempt, at most three times, preserving attempt history and IDs.
    No LLM chooses retries. Unknown/permanent errors require human attention.
    """
    now = utc_now()
    disabled = session.scalar(
        select(SettingRecord.value).where(
            SettingRecord.key == "automatic_job_recovery_enabled"
        )
    )
    if disabled == "false":
        return {"recovered": 0, "superseded": 0}
    state = session.scalar(select(SettingRecord).where(SettingRecord.key == STATE_KEY))
    if state is None:
        try:
            with session.begin_nested():
                state = SettingRecord(key=STATE_KEY, value="{}")
                session.add(state)
                session.flush()
        except IntegrityError:
            return {"recovered": 0, "superseded": 0}
    old_value = state.value
    try:
        checkpoint = json.loads(old_value)
        due = float(checkpoint.get("next_scan", 0))
        cursor = int(checkpoint.get("cursor", 0))
        last_retry = float(checkpoint.get("last_retry", 0))
    except (ValueError, TypeError, AttributeError):
        due, cursor, last_retry = 0, 0, 0
    if now.timestamp() < due:
        return {"recovered": 0, "superseded": 0}
    locked = session.execute(
        update(SettingRecord)
        .where(
            SettingRecord.id == state.id,
            SettingRecord.value == old_value,
        )
        .values(value=json.dumps({"next_scan": now.timestamp() + 60}), updated_at=now)
    )
    if locked.rowcount != 1:
        session.rollback()
        return {"recovered": 0, "superseded": 0}
    candidates = list(
        session.scalars(
            select(JobRecord)
            .where(
                JobRecord.status.in_(["failed", "dead_letter"]),
                JobRecord.id < cursor if cursor else True,
            )
            .order_by(JobRecord.id.desc())
            .limit(50)
        )
    )
    result = {"recovered": 0, "superseded": 0}
    for job in candidates:
        cursor = job.id
        if job.type not in SAFE_TYPES:
            continue
        ended = job.completed_at or job.created_at
        if ended is None or normalize_utc(ended) + timedelta(seconds=DELAYS[0]) > now:
            continue
        try:
            payload = json.loads(job.payload)
            validate_job_payload(job.type, payload)
            issue = _source_state(session, job, payload)
            metadata = payload.get("_automatic_recovery", {})
            count = int(metadata.get("count", 0))
        except (ValueError, TypeError, AttributeError, JobPayloadError):
            continue
        obsolete = issue in {
            "note_missing",
            "content_changed",
            "duplicate_reference",
            "artifact_missing",
            "artifact_changed",
            "graph_node_missing",
            "semantic_source_changed",
        }
        covered_by_active = False
        # A later global snapshot covers old maintenance failures. Do not replay
        # hundreds of obsolete hourly statistics jobs or label them completed.
        if job.type in GLOBAL_TYPES and not (
            job.note_id
            or payload.get("note_id")
            or job.note_path
            or payload.get("note_path")
        ):
            replacements = session.scalars(
                select(JobRecord)
                .where(
                    JobRecord.type == job.type,
                    JobRecord.id > job.id,
                    JobRecord.status.in_(["completed", "pending", "running"]),
                    JobRecord.note_id == 0,
                    JobRecord.note_path == "",
                )
                .order_by(JobRecord.id.desc())
                .limit(10)
            )
            for replacement in replacements:
                try:
                    replacement_payload = json.loads(replacement.payload)
                    validate_job_payload(job.type, replacement_payload)
                    if _maintenance_covers(job.type, payload, replacement_payload):
                        if replacement.status == "completed":
                            obsolete = True
                            break
                        covered_by_active = True
                except (ValueError, TypeError, AttributeError):
                    continue
        elif job.idempotency_key:
            replacement = session.scalar(
                select(JobRecord.id)
                .where(
                    JobRecord.id != job.id,
                    JobRecord.idempotency_key == job.idempotency_key,
                    JobRecord.status.in_(["completed", "pending", "running"]),
                )
                .limit(1)
            )
            obsolete = obsolete or replacement is not None
        if obsolete:
            old_status = job.status
            job.status = "superseded"
            result["superseded"] += 1
            action, reason = "AUTO_SUPERSEDE_JOB", issue or "covered_by_newer_job"
        else:
            if covered_by_active:
                continue
            if (
                issue not in {"", "unchanged", "refreshed"}
                or count < 0
                or count >= len(DELAYS)
            ):
                continue
            if not transient_failure(job.error_message or ""):
                continue
            latest_attempt = session.scalar(
                select(JobAttemptRecord)
                .where(JobAttemptRecord.job_id == job.id)
                .order_by(JobAttemptRecord.id.desc())
                .limit(1)
            )
            if latest_attempt and latest_attempt.error_class == "permanent_job_error":
                continue
            ended = job.completed_at or job.created_at
            if (
                ended is None
                or normalize_utc(ended) + timedelta(seconds=DELAYS[count]) > now
            ):
                continue
            if result["recovered"] or now.timestamp() - last_retry < 300:
                continue
            # Preserve room for foreground ingestion instead of flooding workers.
            active = list(
                session.scalars(
                    select(JobRecord.id)
                    .where(JobRecord.status.in_(["pending", "running"]))
                    .limit(4)
                )
            )
            if len(active) >= 4:
                continue
            old_status = job.status
            current_payload = json.loads(job.payload)  # includes canonicalized path
            current_payload["_automatic_recovery"] = {
                "count": count + 1,
                "scheduledAt": now.isoformat(),
            }
            job.payload = json.dumps(current_payload, ensure_ascii=False)
            job.status = "pending"
            job.max_attempts = job.attempts + 1
            job.started_at = job.completed_at = job.lease_expires_at = None
            job.claimed_by = job.claim_token = ""
            result["recovered"] += 1
            last_retry = now.timestamp()
            action, reason = "AUTO_RECOVER_JOB", "transient_failure"
        create_automation_log(
            session,
            action_type=action,
            target_type="job",
            target_id=str(job.id),
            description=f"{action}: {job.type} ({reason})",
            before_state={"status": old_status, "error_message": job.error_message},
            after_state={
                "status": job.status,
                "reason": reason,
                "attempts": job.attempts,
                "max_attempts": job.max_attempts,
            },
            reversible=False,
        )
    state.value = json.dumps(
        {
            "next_scan": now.timestamp() + 60,
            "cursor": cursor if len(candidates) == 50 else 0,
            "last_retry": last_retry,
        }
    )
    session.commit()
    return result
