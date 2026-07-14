from __future__ import annotations

import json
from collections import Counter
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from berrybrain_api.jobs import (
    COMPLETED,
    FAILED,
    PENDING,
    RUNNING,
    parse_json,
    serialize_datetime,
    utc_now,
)
from berrybrain_api.assimilation import note_assimilation_map
from berrybrain_api.models import (
    AutomationLogRecord,
    ConceptRecord,
    ConnectionRecord,
    EmbeddingRecord,
    GeneratedMetadataRecord,
    GraphEdgeRecord,
    GraphNodeRecord,
    InsightRecord,
    JobRecord,
    NoteRecord,
    ReviewItemRecord,
    SettingRecord,
    WorkerStatus,
)
from berrybrain_api.review_service import serialize_review
from berrybrain_api.provider_security import provider_credential_matches
from berrybrain_api.services import _is_visible_insight


JOB_LABELS = {
    "PARSE_NOTE": "Analyzing note",
    "CLASSIFY_NOTE": "Classifying note",
    "ASSIMILATE_NOTE": "Assimilating concepts",
    "EXTRACT_CONCEPTS": "Extracting concepts",
    "EXTRACT_ENTITIES": "Extracting entities",
    "DETECT_TOPICS": "Detecting topics",
    "EXTRACT_CONTEXT": "Detecting context",
    "GENERATE_EMBEDDING": "Generating embeddings",
    "FIND_CONNECTIONS": "Finding connections",
    "GENERATE_INSIGHTS": "Generating insights",
    "EXPAND_KNOWLEDGE_GRAPH": "Expanding graph",
    "GENERATE_INFERRED_CONNECTIONS": "Inferring connections",
    "EXPAND_CONCEPT_TO_NOTE": "Expanding concepts",
    "GENERATE_GRAPH_INSIGHTS": "Generating graph insights",
    "UPDATE_GRAPH_STATS": "Updating graph stats",
    "GENERATE_NOTE_TITLE": "Applying automatic title",
}

ACTIVITY_LABELS = {
    "PARSE_NOTE": "Note queued for analysis",
    "CLASSIFY_NOTE": "Classification queued",
    "ASSIMILATE_NOTE": "Note queued for assimilation",
    "EXTRACT_CONCEPTS": "Concept extraction queued",
    "EXTRACT_ENTITIES": "Entity extraction queued",
    "DETECT_TOPICS": "Topic detection queued",
    "EXTRACT_CONTEXT": "Context detection queued",
    "GENERATE_EMBEDDING": "Embedding queued",
    "FIND_CONNECTIONS": "Connections queued for analysis",
    "GENERATE_INSIGHTS": "Insights queued",
    "EXPAND_KNOWLEDGE_GRAPH": "Graph expansion queued",
    "GENERATE_NOTE_TITLE": "Automatic title queued",
}


def build_home_summary(session: Session) -> dict[str, Any]:
    now = utc_now()
    today = now.date()

    notes = list(session.execute(select(NoteRecord)).scalars())
    note_by_path = {note.path: note for note in notes}
    jobs = list(
        session.execute(
            select(JobRecord).order_by(JobRecord.created_at.desc(), JobRecord.id.desc())
        ).scalars()
    )
    worker = session.execute(
        select(WorkerStatus).order_by(WorkerStatus.id.desc()).limit(1)
    ).scalar_one_or_none()

    pending_jobs = [job for job in jobs if job.status == PENDING]
    running_jobs = [job for job in jobs if job.status == RUNNING]
    completed_jobs = [job for job in jobs if job.status == COMPLETED]
    failed_jobs = [job for job in jobs if job.status == FAILED]
    total_jobs = (
        len(pending_jobs) + len(running_jobs) + len(completed_jobs) + len(failed_jobs)
    )
    progress_percent = (
        round((len(completed_jobs) / total_jobs) * 100) if total_jobs else 100
    )

    ai_config = _ai_config(session)
    connections = list(session.execute(select(ConnectionRecord)).scalars())
    concepts = list(session.execute(select(ConceptRecord)).scalars())
    raw_insights = list(
        session.execute(
            select(InsightRecord)
            .where(InsightRecord.dismissed_at.is_(None))
            .order_by(InsightRecord.priority.desc(), InsightRecord.created_at.desc())
            .limit(30)
        ).scalars()
    )
    insights = [insight for insight in raw_insights if _is_visible_insight(insight)][:5]
    reviews = list(
        session.execute(
            select(ReviewItemRecord)
            .where(ReviewItemRecord.status == "active")
            .order_by(ReviewItemRecord.due_at.asc())
            .limit(20)
        ).scalars()
    )
    due_reviews = [
        review
        for review in reviews
        if review.due_at
        and (
            review.due_at.replace(tzinfo=UTC)
            if review.due_at.tzinfo is None
            else review.due_at
        )
        <= now
    ]
    embeddings = session.query(EmbeddingRecord).count()
    metadata_count = session.query(GeneratedMetadataRecord).count()

    recent_notes = [
        _serialize_note(note)
        for note in sorted(notes, key=lambda item: item.updated_at, reverse=True)[:6]
    ]
    note_types = dict(
        session.execute(
            select(NoteRecord.note_type, func.count()).group_by(NoteRecord.note_type)
        ).all()
    )
    recent_activity = [_serialize_activity(log) for log in _recent_logs(session, 8)]
    active_jobs = [
        _serialize_active_job(job, note_by_path, ai_config)
        for job in sorted(
            running_jobs, key=lambda item: item.started_at or item.created_at
        )[:8]
    ]
    recently_completed = [
        _serialize_completion(job, note_by_path)
        for job in sorted(
            completed_jobs,
            key=lambda item: item.completed_at or item.created_at,
            reverse=True,
        )[:8]
    ]
    recent_connections = list_recent_connections(session, limit=5)

    graph_summary = _graph_summary(session, notes, connections)
    assimilation = note_assimilation_map(session, notes, jobs)
    unassimilated = [
        note for note in notes if not assimilation.get(note.id, {}).get("assimilated")
    ]
    needs_attention = _needs_attention(
        worker=worker,
        failed_jobs=failed_jobs,
        unassimilated=unassimilated,
        insights=insights,
        ai_config=ai_config,
        now=now,
    )

    progress_state = _progress_state(worker, running_jobs, pending_jobs, failed_jobs)
    current_step = _current_step(running_jobs, pending_jobs)

    summary = {
        "status": {
            "worker": _worker_status(worker, now),
            "workerLastHeartbeat": serialize_datetime(worker.last_heartbeat)
            if worker
            else None,
            "ollama": "online" if worker and worker.ollama_healthy else "offline",
            "cloudProvider": _cloud_provider(ai_config),
            "cloudModel": ai_config.get("cloud_model") or "",
            "cloudStatus": _cloud_status(ai_config),
            "cloudConfigured": bool(ai_config.get("cloud_key_configured")),
            "cloudLastTestAt": ai_config.get("last_test_at") or None,
            "remoteContentConsent": ai_config.get("remote_content_consent") == "true",
            "pendingJobs": len(pending_jobs),
            "activeJobs": len(running_jobs),
            "lastProcessingAt": serialize_datetime(_last_processing_at(jobs, notes)),
        },
        "progress": {
            "mode": "determinate" if total_jobs else "determinate",
            "percent": progress_percent,
            "active": len(running_jobs),
            "pending": len(pending_jobs),
            "completed": len(completed_jobs),
            "failed": len(failed_jobs),
            "currentStep": current_step,
            "lastResult": _last_result(
                recently_completed, recent_connections, insights
            ),
            "status": progress_state,
        },
        "stats": {
            "notes": {
                "total": len(notes),
                "createdToday": sum(
                    1 for note in notes if _same_day(note.created_at, today)
                ),
                "unassimilated": len(unassimilated),
            },
            "connections": {
                "total": len(connections),
                "createdToday": sum(
                    1 for c in connections if _same_day(c.created_at, today)
                ),
                "averageConfidence": _average_confidence(connections),
            },
            "concepts": {
                "total": len(concepts),
                "newToday": sum(1 for c in concepts if _same_day(c.created_at, today)),
                "withoutPermanentNote": _concepts_without_notes(concepts, notes),
            },
            "study": {
                "dueReviews": len(due_reviews),
                "activeReviews": len(reviews),
                "suggestedReviews": sum(
                    1 for insight in insights if insight.type == "review_opportunity"
                ),
                "weakConcepts": sum(
                    1 for concept in concepts if concept.confidence < 0.6
                ),
                "openGaps": sum(
                    1 for insight in insights if insight.type == "knowledge_gap"
                ),
            },
            "jobs": {
                "pending": len(pending_jobs),
                "active": len(running_jobs),
                "failed": len(failed_jobs),
                "completedToday": sum(
                    1
                    for job in completed_jobs
                    if job.completed_at and _same_day(job.completed_at, today)
                ),
                "total": len(jobs),
            },
            "ai": {
                "provider": _cloud_provider(ai_config),
                "model": ai_config.get("cloud_model") or "",
                "metadata": metadata_count,
                "embeddings": embeddings,
                "jobsProcessed": worker.jobs_processed if worker else 0,
                "errors": worker.errors if worker else 0,
            },
        },
        "recentNotes": recent_notes,
        "dueReviews": [serialize_review(review) for review in due_reviews[:3]],
        "activeJobs": active_jobs,
        "recentlyCompleted": recently_completed,
        "recentActivity": recent_activity,
        "recentInsights": [_serialize_insight(insight) for insight in insights],
        "detectedConcepts": _detected_concepts(concepts, session, limit=8),
        "recentConnections": recent_connections,
        "graphSummary": graph_summary,
        "needsAttention": needs_attention,
        "jobsByType": {
            JOB_LABELS.get(job_type, job_type.replace("_", " ").title()): count
            for job_type, count in Counter(
                job.type for job in pending_jobs + running_jobs
            ).items()
        },
    }

    # Compatibility with the current web client while it migrates to the richer contract.
    summary["insights"] = summary["recentInsights"]
    summary["autopilot"] = {
        "worker": summary["status"]["worker"],
        "ollama": worker.ollama_healthy if worker else False,
        "processed": worker.jobs_processed if worker else 0,
        "errors": worker.errors if worker else 0,
        "pending": len(pending_jobs),
        "running": len(running_jobs),
        "activity": [
            {
                "action": item["action"],
                "desc": item["description"],
                "when": item["when"],
            }
            for item in recent_activity
        ],
    }
    summary["legacyStats"] = {
        "notes": len(notes),
        "connections": len(connections),
        "pendingJobs": len(pending_jobs),
        "runningJobs": len(running_jobs),
        "failedJobs": len(failed_jobs),
        "noteTypes": note_types,
    }
    return summary


def list_detected_concepts(session: Session, limit: int = 20) -> list[dict[str, Any]]:
    concepts = list(session.execute(select(ConceptRecord)).scalars())
    return _detected_concepts(concepts, session, limit=limit)


def list_recent_connections(session: Session, limit: int = 20) -> list[dict[str, Any]]:
    notes = list(session.execute(select(NoteRecord)).scalars())
    note_by_id = {note.id: note for note in notes}
    connections = list(
        session.execute(
            select(ConnectionRecord)
            .where(ConnectionRecord.status != "ignored")
            .order_by(ConnectionRecord.created_at.desc())
            .limit(limit)
        ).scalars()
    )
    return [_serialize_connection(connection, note_by_id) for connection in connections]


def _ai_config(session: Session) -> dict[str, str]:
    rows = session.execute(select(SettingRecord)).scalars()
    values = {row.key: row.value for row in rows}
    cloud_url = values.get("ai_api_url") or values.get("ai_custom_url", "")
    api_key = values.get("ai_api_key", "")
    test_matches = (
        values.get("ai_last_test_url", "").rstrip("/") == cloud_url.rstrip("/")
        and provider_credential_matches(
            values.get("ai_last_test_key_fingerprint", ""), api_key
        )
        and values.get("ai_last_test_method") == "chat_completions"
    )
    return {
        "provider": values.get("ai_provider", "local"),
        "cloud_api_url": cloud_url,
        "cloud_model": values.get("ai_model", ""),
        "cloud_key_configured": "true" if values.get("ai_api_key") else "",
        "remote_content_consent": values.get("remote_content_consent", "false"),
        "last_test_status": values.get("ai_last_test_status", "untested")
        if test_matches
        else "untested",
        "last_test_at": values.get("ai_last_test_at", ""),
    }


def _cloud_provider(config: dict[str, str]) -> str:
    if config.get("provider") != "cloud":
        return "local"
    url = (config.get("cloud_api_url") or "").lower()
    model = (config.get("cloud_model") or "").lower()
    if "nvidia" in url or "nvidia" in model or "nemotron" in model:
        return "nvidia-nim"
    return "cloud"


def _cloud_status(config: dict[str, str]) -> str:
    if config.get("provider") != "cloud":
        return "local"
    if not (
        config.get("cloud_api_url")
        and config.get("cloud_key_configured")
        and config.get("cloud_model")
    ):
        return "incomplete"
    if config.get("remote_content_consent") != "true":
        return "disabled"
    if config.get("last_test_status") == "connected":
        return "connected"
    if config.get("last_test_status") == "failed":
        return "failed"
    return "configured"


def _worker_status(worker: WorkerStatus | None, now: datetime) -> str:
    if worker is None:
        return "offline"
    last = _as_aware(worker.last_heartbeat)
    if last and now - last > timedelta(minutes=2):
        return "offline"
    return worker.status


def _progress_state(
    worker: WorkerStatus | None,
    running_jobs: list[JobRecord],
    pending_jobs: list[JobRecord],
    failed_jobs: list[JobRecord],
) -> str:
    if _worker_status(worker, utc_now()) == "offline" and (
        running_jobs or pending_jobs
    ):
        return "offline"
    if running_jobs:
        return "running"
    if pending_jobs:
        return "queued"
    if failed_jobs:
        return "completed"
    return "completed"


def _current_step(running_jobs: list[JobRecord], pending_jobs: list[JobRecord]) -> str:
    job = (
        sorted(running_jobs, key=lambda item: item.started_at or item.created_at)[0]
        if running_jobs
        else None
    )
    if job is None and pending_jobs:
        job = sorted(pending_jobs, key=lambda item: item.created_at)[0]
    if job is None:
        return "All set"
    return JOB_LABELS.get(job.type, job.type.replace("_", " ").title())


def _serialize_note(note: NoteRecord) -> dict[str, Any]:
    return {
        "id": note.id,
        "title": note.title,
        "path": note.path,
        "folder": note.path.split("/")[0] if "/" in note.path else "inbox",
        "status": note.status,
        "updatedAt": serialize_datetime(note.updated_at),
    }


def _serialize_active_job(
    job: JobRecord,
    note_by_path: dict[str, NoteRecord],
    ai_config: dict[str, str],
) -> dict[str, Any]:
    payload = parse_json(job.payload)
    note_path = payload.get("note_path", "")
    note = note_by_path.get(note_path)
    started = _as_aware(job.started_at)
    elapsed = int((utc_now() - started).total_seconds()) if started else 0
    return {
        "id": job.id,
        "type": job.type,
        "label": JOB_LABELS.get(job.type, job.type.replace("_", " ").title()),
        "notePath": note_path,
        "noteTitle": note.title if note else "",
        "provider": _cloud_provider(ai_config),
        "model": ai_config.get("cloud_model") or "",
        "startedAt": serialize_datetime(job.started_at),
        "elapsedSeconds": elapsed,
        "progress": None,
    }


def _serialize_completion(
    job: JobRecord, note_by_path: dict[str, NoteRecord]
) -> dict[str, Any]:
    payload = parse_json(job.payload)
    note_path = payload.get("note_path", "")
    note = note_by_path.get(note_path)
    return {
        "id": job.id,
        "type": job.type,
        "label": _completion_label(job.type, note.title if note else note_path),
        "notePath": note_path,
        "noteTitle": note.title if note else "",
        "completedAt": serialize_datetime(job.completed_at),
    }


def _completion_label(job_type: str, note_title: str) -> str:
    subject = f' for "{note_title}"' if note_title else ""
    if job_type == "FIND_CONNECTIONS":
        return f"Connections analyzed{subject}"
    if job_type == "EXPAND_KNOWLEDGE_GRAPH":
        return f"Graph expanded{subject}"
    if job_type == "GENERATE_EMBEDDING":
        return f"Embedding created{subject}"
    if job_type == "GENERATE_INSIGHTS":
        return "Insights generated"
    if job_type == "GENERATE_NOTE_TITLE":
        return f"Automatic title applied{subject}"
    return f"{JOB_LABELS.get(job_type, job_type)} completed{subject}"


def _recent_logs(session: Session, limit: int) -> list[AutomationLogRecord]:
    return list(
        session.execute(
            select(AutomationLogRecord)
            .order_by(AutomationLogRecord.created_at.desc())
            .limit(limit)
        ).scalars()
    )


def _serialize_activity(log: AutomationLogRecord) -> dict[str, Any]:
    description = log.description
    for job_type, label in ACTIVITY_LABELS.items():
        if job_type in description:
            description = label
            break
    return {
        "id": log.id,
        "action": log.action_type,
        "targetType": log.target_type,
        "targetId": log.target_id,
        "description": description,
        "technicalDescription": log.description,
        "when": serialize_datetime(log.created_at),
    }


def _serialize_insight(insight: InsightRecord) -> dict[str, Any]:
    related = parse_json(insight.related_notes)
    return {
        "id": insight.id,
        "type": insight.type,
        "title": insight.title,
        "description": insight.description,
        "relatedNotes": related if isinstance(related, list) else [],
        "priority": insight.priority,
        "whyItMatters": getattr(insight, "why_it_matters", ""),
        "evidence": _safe_json_list(getattr(insight, "evidence", "[]")),
        "suggestedAction": getattr(insight, "suggested_action", ""),
        "graphImpact": getattr(insight, "graph_impact", ""),
        "confidence": getattr(insight, "confidence", 0.5),
        "status": getattr(insight, "status", "suggested"),
        "provider": getattr(insight, "provider", ""),
        "model": getattr(insight, "model", ""),
        "promptVersion": getattr(insight, "prompt_version", "v1"),
        "reasoning": getattr(insight, "reasoning", ""),
        "sourceContext": getattr(insight, "source_context", ""),
        "appliedAt": serialize_datetime(insight.applied_at)
        if insight.applied_at
        else None,
        "ignoredAt": serialize_datetime(insight.ignored_at)
        if insight.ignored_at
        else None,
        "createdAt": serialize_datetime(insight.created_at),
        "updatedAt": serialize_datetime(insight.updated_at)
        if insight.updated_at
        else None,
        "dismissedAt": serialize_datetime(insight.dismissed_at)
        if insight.dismissed_at
        else None,
    }


def _suggested_action(insight_type: str) -> str:
    return {
        "knowledge_gap": "Create permanent note",
        "weak_note": "Strengthen note",
        "isolated_concept": "Connect concept",
        "duplicate_content": "Review duplicate",
        "study_path": "Open suggested path",
        "review_opportunity": "Review now",
    }.get(insight_type, "Open insight")


def _detected_concepts(
    concepts: list[ConceptRecord],
    session: Session,
    limit: int = 8,
) -> list[dict[str, Any]]:
    frequency = _concept_frequency(session)
    ordered = sorted(
        concepts,
        key=lambda item: (frequency.get(item.normalized_name, 1), item.created_at),
        reverse=True,
    )
    return [
        {
            "id": concept.id,
            "name": concept.name,
            "normalizedName": concept.normalized_name,
            "description": concept.description,
            "frequency": concept.frequency or frequency.get(concept.normalized_name, 1),
            "relatedNotesCount": concept.frequency
            or frequency.get(concept.normalized_name, 0),
            "trend": "novo"
            if _same_day(concept.created_at, utc_now().date())
            else "recorrente",
            "hasPermanentNote": False,
            "extractedBy": getattr(concept, "extracted_by", "ai"),
            "confidence": getattr(concept, "confidence", None),
            "status": getattr(concept, "status", "suggested"),
            "provider": getattr(concept, "provider", ""),
            "model": getattr(concept, "model", ""),
        }
        for concept in ordered[:limit]
    ]


def _concept_frequency(session: Session) -> dict[str, int]:
    counts: Counter[str] = Counter()
    rows = session.execute(
        select(GeneratedMetadataRecord).where(
            GeneratedMetadataRecord.generation_type == "concepts"
        )
    ).scalars()
    for row in rows:
        data = parse_json(row.content)
        concepts = data.get("concepts", []) if isinstance(data, dict) else []
        for item in concepts:
            name = item.get("name") if isinstance(item, dict) else str(item)
            if name:
                counts[_normalize_name(name)] += 1
    return dict(counts)


def _serialize_connection(
    connection: ConnectionRecord,
    note_by_id: dict[int, NoteRecord],
) -> dict[str, Any]:
    source = note_by_id.get(connection.source_note_id)
    target = note_by_id.get(connection.target_note_id)
    return {
        "id": connection.id,
        "source": _serialize_connection_note(source),
        "target": _serialize_connection_note(target),
        "type": connection.connection_type,
        "confidence": connection.confidence / 100
        if connection.confidence > 1
        else connection.confidence,
        "confidencePercent": connection.confidence,
        "reason": connection.reason,
        "evidence": _safe_json_list(getattr(connection, "evidence", "[]")),
        "createdBy": connection.created_by,
        "status": getattr(
            connection,
            "status",
            "suggested" if connection.created_by == "ai" else "confirmed",
        ),
        "provider": getattr(connection, "provider", ""),
        "model": getattr(connection, "model", ""),
        "createdAt": serialize_datetime(connection.created_at),
    }


def _serialize_connection_note(note: NoteRecord | None) -> dict[str, Any] | None:
    if note is None:
        return None
    return {"id": note.id, "title": note.title, "path": note.path}


def _safe_json_list(value: str) -> list[Any]:
    try:
        parsed = json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return []
    return parsed if isinstance(parsed, list) else []


def _safe_json_dict(value: str) -> dict[str, Any]:
    try:
        parsed = json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _graph_summary(
    session: Session, notes: list[NoteRecord], connections: list[ConnectionRecord]
) -> dict[str, Any]:
    graph_nodes = list(session.execute(select(GraphNodeRecord)).scalars())
    graph_edges = list(session.execute(select(GraphEdgeRecord)).scalars())
    if graph_nodes:
        active_edges = [
            edge for edge in graph_edges if getattr(edge, "status", "") != "ignored"
        ]
        degrees: Counter[int] = Counter()
        for edge in active_edges:
            degrees[edge.source_node_id] += 1
            degrees[edge.target_node_id] += 1
        central = sorted(degrees.items(), key=lambda item: item[1], reverse=True)[:5]
        node_by_id = {node.id: node for node in graph_nodes}
        return {
            "nodes": len(graph_nodes),
            "edges": len(active_edges),
            "orphans": sum(1 for node in graph_nodes if degrees.get(node.id, 0) == 0),
            "clusters": max(1, len({node.type for node in graph_nodes})),
            "centralNotes": [
                {
                    "id": node_id,
                    "title": node_by_id[node_id].label,
                    "path": _safe_json_dict(node_by_id[node_id].graph_metadata).get(
                        "path", ""
                    ),
                    "degree": degree,
                }
                for node_id, degree in central
                if node_id in node_by_id and degree > 0
            ],
            "updatedAt": serialize_datetime(_latest_note_update(notes)),
        }

    degrees: Counter[int] = Counter()
    for connection in connections:
        degrees[connection.source_note_id] += 1
        degrees[connection.target_note_id] += 1
    central = sorted(degrees.items(), key=lambda item: item[1], reverse=True)[:5]
    note_by_id = {note.id: note for note in notes}
    return {
        "nodes": len(notes),
        "edges": len(connections),
        "orphans": sum(1 for note in notes if degrees.get(note.id, 0) == 0),
        "clusters": _estimate_clusters(notes, connections),
        "centralNotes": [
            {
                "id": note_id,
                "title": note_by_id[note_id].title,
                "path": note_by_id[note_id].path,
                "degree": degree,
            }
            for note_id, degree in central
            if note_id in note_by_id and degree > 0
        ],
        "updatedAt": serialize_datetime(_latest_note_update(notes)),
    }


def _estimate_clusters(
    notes: list[NoteRecord], connections: list[ConnectionRecord]
) -> int:
    if not notes:
        return 0
    parent = {note.id: note.id for note in notes}

    def find(value: int) -> int:
        while parent[value] != value:
            parent[value] = parent[parent[value]]
            value = parent[value]
        return value

    def union(left: int, right: int) -> None:
        if left in parent and right in parent:
            parent[find(left)] = find(right)

    for connection in connections:
        union(connection.source_note_id, connection.target_note_id)
    return len({find(note.id) for note in notes})


def _needs_attention(
    worker: WorkerStatus | None,
    failed_jobs: list[JobRecord],
    unassimilated: list[NoteRecord],
    insights: list[InsightRecord],
    ai_config: dict[str, str],
    now: datetime,
) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    if _worker_status(worker, now) == "offline":
        items.append(
            {
                "kind": "worker_offline",
                "title": "Worker offline",
                "description": "Jobs are paused until the Worker comes back.",
                "action": "Open monitor",
            }
        )
    if failed_jobs:
        items.append(
            {
                "kind": "failed_jobs",
                "title": f"{len(failed_jobs)} jobs failed",
                "description": "Review recent errors in Monitor.",
                "action": "View errors",
            }
        )
    return items[:5]


def _last_processing_at(
    jobs: list[JobRecord], notes: list[NoteRecord]
) -> datetime | None:
    values = [job.completed_at for job in jobs if job.completed_at]
    values.extend(note.last_processed_at for note in notes if note.last_processed_at)
    return max(values) if values else None


def _last_result(
    recently_completed: list[dict[str, Any]],
    recent_connections: list[dict[str, Any]],
    insights: list[InsightRecord],
) -> str:
    if recently_completed:
        return recently_completed[0]["label"]
    if recent_connections:
        return f"{len(recent_connections)} connections found"
    if insights:
        return f"{len(insights)} insights available"
    return "No recent results"


def _average_confidence(connections: list[ConnectionRecord]) -> float:
    if not connections:
        return 0
    return round(
        sum(connection.confidence for connection in connections)
        / len(connections)
        / 100,
        2,
    )


def _concepts_without_notes(
    concepts: list[ConceptRecord], notes: list[NoteRecord]
) -> int:
    note_titles = {_normalize_name(note.title) for note in notes}
    return sum(1 for concept in concepts if concept.normalized_name not in note_titles)


def _latest_note_update(notes: list[NoteRecord]) -> datetime | None:
    return max((note.updated_at for note in notes), default=None)


def _normalize_name(value: str) -> str:
    return " ".join(value.strip().lower().split())


def _same_day(value: datetime | None, day: object) -> bool:
    if value is None:
        return False
    return value.date() == day


def _as_aware(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value
