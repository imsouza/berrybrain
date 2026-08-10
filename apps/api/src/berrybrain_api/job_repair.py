from __future__ import annotations

from collections import defaultdict
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from berrybrain_api.job_contracts import JobPayloadError, validate_job_payload
from berrybrain_api.jobs import canonicalize_job_note_reference, parse_json
from berrybrain_api.models import (
    ConnectionRecord,
    GraphEdgeRecord,
    GraphNodeRecord,
    InsightRecord,
    JobRecord,
)


def inspect_legacy_jobs(session: Session) -> dict[str, Any]:
    jobs = list(
        session.execute(
            select(JobRecord).order_by(JobRecord.created_at.asc(), JobRecord.id.asc())
        ).scalars()
    )
    report: dict[str, list[dict[str, Any]]] = {
        "migratable": [],
        "reprocessable": [],
        "irrecoverable": [],
        "duplicates": [],
    }
    active_keys: dict[str, list[JobRecord]] = defaultdict(list)
    for job in jobs:
        payload = parse_json(job.payload)
        try:
            version = validate_job_payload(job.type, payload)
        except JobPayloadError as exc:
            report["irrecoverable"].append(_item(job, exc.code))
            continue
        semantic_source_issue = _semantic_source_issue(session, job, payload)
        if semantic_source_issue:
            report["irrecoverable"].append(_item(job, semantic_source_issue))
            continue
        migration_reason = (
            "payload_version_backfill" if job.payload_schema_version != version else ""
        )
        if job.status in {"pending", "running", "failed", "dead_letter"}:
            note_reference_issue = _note_reference_issue(session, job, payload)
            if note_reference_issue in {"note_missing", "content_changed"}:
                report["irrecoverable"].append(
                    _item(
                        job,
                        "note_missing"
                        if note_reference_issue == "note_missing"
                        else "note_content_changed",
                    )
                )
                continue
            if note_reference_issue == "path_changed":
                migration_reason = "note_path_refresh"
        if migration_reason:
            report["migratable"].append(_item(job, migration_reason))
        if job.type == "JUDGE_ARTIFACT" and not _artifact_exists(session, payload):
            report["irrecoverable"].append(_item(job, "artifact_missing"))
            continue
        if job.status in {"failed", "dead_letter"}:
            report["reprocessable"].append(_item(job, "valid_failed_job"))
        if job.idempotency_key and job.status in {"pending", "running"}:
            active_keys[job.idempotency_key].append(job)
    for duplicate_jobs in active_keys.values():
        if len(duplicate_jobs) > 1:
            report["duplicates"].extend(
                _item(job, "duplicate_active_idempotency_key")
                for job in duplicate_jobs[1:]
            )
    return {
        **report,
        "counts": {key: len(value) for key, value in report.items()},
        "total": len(jobs),
    }


def repair_legacy_jobs(
    session: Session,
    *,
    dry_run: bool,
    batch_size: int = 100,
) -> dict[str, Any]:
    report = inspect_legacy_jobs(session)
    if dry_run:
        return {"dryRun": True, "changed": 0, **report}
    changed = 0
    duplicate_ids = {int(item["id"]) for item in report["duplicates"]}
    irrecoverable = {
        int(item["id"]): str(item["reason"]) for item in report["irrecoverable"]
    }
    reprocessable_ids = {int(item["id"]) for item in report["reprocessable"]}
    migratable_ids = {int(item["id"]) for item in report["migratable"]}
    target_ids = list(
        duplicate_ids | set(irrecoverable) | reprocessable_ids | migratable_ids
    )[: max(1, min(batch_size, 1000))]
    for job in session.execute(
        select(JobRecord).where(JobRecord.id.in_(target_ids))
    ).scalars():
        if job.id in duplicate_ids:
            job.status = "superseded"
            job.error_message = "Superseded by canonical active job."
        elif job.id in irrecoverable:
            job.status = "dead_letter"
            job.error_message = irrecoverable[job.id]
        elif job.id in reprocessable_ids:
            job.status = "pending"
            job.attempts = 0
            job.error_message = None
            job.completed_at = None
        if job.id in migratable_ids:
            canonicalize_job_note_reference(session, job)
            job.payload_schema_version = validate_job_payload(
                job.type, parse_json(job.payload)
            )
        changed += 1
    session.commit()
    return {"dryRun": False, "changed": changed, **inspect_legacy_jobs(session)}


def _artifact_exists(session: Session, payload: dict[str, Any]) -> bool:
    artifact_type = str(payload.get("artifact_type") or "")
    try:
        artifact_id = int(payload.get("artifact_id") or 0)
    except (TypeError, ValueError):
        return False
    model = {
        "node": GraphNodeRecord,
        "edge": GraphEdgeRecord,
        "insight": InsightRecord,
        "connection": ConnectionRecord,
    }.get(artifact_type)
    return bool(model and session.get(model, artifact_id))


def _semantic_source_issue(
    session: Session, job: JobRecord, payload: dict[str, Any]
) -> str:
    if job.type != "ENRICH_GRAPH_NODE":
        return ""
    try:
        node_id = int(payload.get("node_id") or 0)
    except (TypeError, ValueError):
        return "graph_node_missing"
    node = session.get(GraphNodeRecord, node_id)
    if node is None:
        return "graph_node_missing"
    from berrybrain_api.semantic_enrichment import source_fingerprint

    if str(payload.get("source_fingerprint") or "") != source_fingerprint(
        session, node
    ):
        return "semantic_source_changed"
    return ""


def _note_reference_issue(
    session: Session, job: JobRecord, payload: dict[str, Any]
) -> str:
    try:
        note_id = int(job.note_id or payload.get("note_id") or 0)
    except (TypeError, ValueError):
        return ""
    if not note_id:
        return ""
    from berrybrain_api.models import NoteRecord

    note = session.get(NoteRecord, note_id)
    if note is None:
        return "note_missing"
    content_hash = str(job.content_hash or payload.get("content_hash") or "")
    if content_hash and note.content_hash and content_hash != note.content_hash:
        return "content_changed"
    note_path = str(job.note_path or payload.get("note_path") or "")
    return "path_changed" if note_path and note.path != note_path else ""


def _item(job: JobRecord, reason: str) -> dict[str, Any]:
    return {
        "id": job.id,
        "type": job.type,
        "status": job.status,
        "reason": reason,
    }
