from datetime import UTC, datetime, timedelta

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import func, select

from berrybrain_api.ai_configuration import load_configuration
from berrybrain_api.ai_gateway import provider_resilience_snapshot
from berrybrain_api.database import SessionLocal, engine
from berrybrain_api.jobs import list_jobs, parse_json, serialize_datetime
from berrybrain_api.models import (
    ConnectionRecord,
    EmbeddingRecord,
    GeneratedMetadataRecord,
    GraphFeedbackRecord,
    InsightRecord,
    LearningEventRecord,
    ModelInvocationRecord,
    NoteRecord,
    WorkerStatus,
)
from berrybrain_api.schema_migrations import schema_diagnostic
from berrybrain_api.services import (
    decode_embedding_vector,
    find_similar_chunk_notes,
    find_similar_notes,
    store_embedding,
)

router = APIRouter(prefix="/api/v1", tags=["monitor"])


class HeartbeatRequest(BaseModel):
    jobs_processed: int = 0
    errors: int = 0
    active_provider_healthy: bool | None = None
    ollama_healthy: bool | None = None


def _worker_status_payload(session, worker: WorkerStatus) -> dict:
    configuration = load_configuration(session)
    mode = configuration.mode if configuration is not None else "unconfigured"
    provider_id = (
        configuration.main.provider_id if configuration is not None else "unconfigured"
    )
    active_healthy = bool(worker.ollama_healthy)
    return {
        "status": worker.status,
        "last_heartbeat_at": serialize_datetime(worker.last_heartbeat),
        "jobs_processed": worker.jobs_processed,
        "errors": worker.errors,
        "active_provider_mode": mode,
        "active_provider_id": provider_id,
        "active_provider_healthy": active_healthy,
        "capability_health": {
            "generation": "healthy" if active_healthy else "unavailable",
            "worker": "healthy" if worker.status == "running" else worker.status,
        },
    }


@router.get("/monitor/stats")
def monitor_stats() -> dict:
    with SessionLocal() as session:
        jobs = list_jobs(session, limit=200)
        worker = session.execute(
            select(WorkerStatus).order_by(WorkerStatus.id.desc()).limit(1)
        ).scalar_one_or_none()
        completed = [j for j in jobs if j.status == "completed"]
        failed = [j for j in jobs if j.status == "failed"]
        pending = [j for j in jobs if j.status == "pending"]
        types: dict[str, int] = {}
        for j in completed:
            types[j.type] = types.get(j.type, 0) + 1
        running = [j for j in jobs if j.status == "running"]
        invocations = list(
            session.execute(
                select(ModelInvocationRecord)
                .order_by(ModelInvocationRecord.started_at.desc())
                .limit(200)
            ).scalars()
        )
        finished_invocations = [
            item for item in invocations if item.status in {"completed", "failed"}
        ]
        successful_invocations = [
            item for item in finished_invocations if item.status == "completed"
        ]
        provider_totals: dict[str, dict[str, int]] = {}
        for item in invocations:
            provider = item.provider or "unknown"
            bucket = provider_totals.setdefault(
                provider, {"total": 0, "completed": 0, "failed": 0}
            )
            bucket["total"] += 1
            if item.status in {"completed", "failed"}:
                bucket[item.status] += 1
        learning_total = session.scalar(select(func.count(LearningEventRecord.id))) or 0
        learning_recent = (
            session.scalar(
                select(func.count(LearningEventRecord.id)).where(
                    LearningEventRecord.created_at
                    >= datetime.now(UTC) - timedelta(hours=24)
                )
            )
            or 0
        )
        learning_by_target = {
            target: int(count)
            for target, count in session.execute(
                select(
                    LearningEventRecord.target_type,
                    func.count(LearningEventRecord.id),
                ).group_by(LearningEventRecord.target_type)
            )
        }
        latest_learning_event = session.scalar(
            select(LearningEventRecord)
            .order_by(
                LearningEventRecord.created_at.desc(), LearningEventRecord.id.desc()
            )
            .limit(1)
        )
        return {
            "schema": schema_diagnostic(engine),
            "worker": _worker_status_payload(session, worker) if worker else None,
            "notes": session.query(NoteRecord).count(),
            "connections": session.query(ConnectionRecord).count(),
            "insights": session.query(InsightRecord).count(),
            "metadata": session.query(GeneratedMetadataRecord).count(),
            "embeddings": session.query(EmbeddingRecord).count(),
            "jobs": {
                "total": len(jobs),
                "completed": len(completed),
                "failed": len(failed),
                "pending": len(pending),
                "running": len(running),
                "per_hour": len(
                    [
                        j
                        for j in completed
                        if j.completed_at
                        and (datetime.now() - j.completed_at).total_seconds() < 3600
                    ]
                ),
            },
            "model_invocations": {
                "total": len(invocations),
                "completed": len(successful_invocations),
                "failed": len(
                    [item for item in invocations if item.status == "failed"]
                ),
                "cancelled": len(
                    [item for item in invocations if item.status == "cancelled"]
                ),
                "success_rate": round(
                    len(successful_invocations) / len(finished_invocations), 4
                )
                if finished_invocations
                else None,
                "average_latency_ms": round(
                    sum(item.latency_ms for item in successful_invocations)
                    / len(successful_invocations)
                )
                if successful_invocations
                else None,
                "by_provider": provider_totals,
                "recent_failures": [
                    {
                        "capability": item.capability,
                        "provider": item.provider,
                        "model": item.model,
                        "error_class": item.error_class,
                        "error_message": item.error_message,
                        "when": item.completed_at.isoformat()
                        if item.completed_at
                        else item.started_at.isoformat(),
                    }
                    for item in invocations
                    if item.status == "failed"
                ][:5],
                "circuits": provider_resilience_snapshot(),
            },
            "learning": {
                "mode": "feedback-guided-adaptation",
                "policy_version": "feedback-policy.v1",
                "model_weights_updated": False,
                "total_events": int(learning_total),
                "events_last_24h": int(learning_recent),
                "positive_events": session.scalar(
                    select(func.count(LearningEventRecord.id)).where(
                        LearningEventRecord.signal > 0
                    )
                )
                or 0,
                "negative_events": session.scalar(
                    select(func.count(LearningEventRecord.id)).where(
                        LearningEventRecord.signal < 0
                    )
                )
                or 0,
                "neutral_events": session.scalar(
                    select(func.count(LearningEventRecord.id)).where(
                        LearningEventRecord.signal == 0
                    )
                )
                or 0,
                "active_graph_feedback": session.scalar(
                    select(func.count(GraphFeedbackRecord.id)).where(
                        GraphFeedbackRecord.active.is_(True)
                    )
                )
                or 0,
                "by_target": learning_by_target,
                "latest_event_at": serialize_datetime(
                    latest_learning_event.created_at
                    if latest_learning_event is not None
                    else None
                ),
            },
            "running_jobs": [
                {
                    "id": j.id,
                    "type": j.type,
                    "note_path": parse_json(j.payload).get("note_path", "?"),
                    "started_at": j.started_at.isoformat() if j.started_at else "?",
                    "elapsed_s": (datetime.now() - j.started_at).total_seconds()
                    if j.started_at
                    else 0,
                }
                for j in running
            ],
            "job_types": types,
            "recent_completions": [
                {
                    "type": j.type,
                    "when": j.completed_at.isoformat() if j.completed_at else "?",
                }
                for j in sorted(
                    completed,
                    key=lambda x: x.completed_at or x.created_at,
                    reverse=True,
                )[:10]
            ],
        }


@router.post("/worker/heartbeat")
def worker_heartbeat(payload: HeartbeatRequest) -> dict:
    with SessionLocal() as session:
        ws = session.execute(
            select(WorkerStatus).order_by(WorkerStatus.id.desc()).limit(1)
        ).scalar_one_or_none()
        if ws is None:
            ws = WorkerStatus()
            session.add(ws)
        ws.status = "running"
        ws.last_heartbeat = datetime.now(UTC)
        ws.jobs_processed = payload.jobs_processed
        ws.errors = payload.errors
        ws.ollama_healthy = (
            payload.active_provider_healthy
            if payload.active_provider_healthy is not None
            else bool(payload.ollama_healthy)
        )
        session.commit()
        session.refresh(ws)
        from berrybrain_api.agent_monitor import ensure_agent_monitoring

        agent_monitor = ensure_agent_monitoring(session)
        return {
            "worker": _worker_status_payload(session, ws),
            "agentMonitor": agent_monitor,
        }


@router.get("/worker/status")
def worker_status() -> dict:
    with SessionLocal() as session:
        ws = session.execute(
            select(WorkerStatus).order_by(WorkerStatus.id.desc()).limit(1)
        ).scalar_one_or_none()
        if ws is None:
            return {"worker": None}
        return {"worker": _worker_status_payload(session, ws)}


class EmbeddingRequest(BaseModel):
    note_id: int
    content_hash: str = ""
    vector: list[float]
    model: str = "bge-m3"
    provider: str = ""
    chunk_index: int = -1
    chunk_text: str = ""
    heading_path: str = ""
    start_line: int = 0
    end_line: int = 0
    token_count: int = 0


class EmbeddingBatchRequest(BaseModel):
    embeddings: list[EmbeddingRequest]


@router.post("/embeddings")
def create_embedding(payload: EmbeddingRequest) -> dict:
    with SessionLocal() as session:
        emb = store_embedding(
            session,
            payload.note_id,
            payload.content_hash,
            payload.vector,
            payload.model,
            chunk_index=payload.chunk_index,
            chunk_text=payload.chunk_text,
            heading_path=payload.heading_path,
            start_line=payload.start_line,
            end_line=payload.end_line,
            token_count=payload.token_count,
            provider=payload.provider,
        )
        return {
            "embedding": {
                "id": emb.id,
                "note_id": emb.note_id,
                "chunk_index": emb.chunk_index,
                "created_at": emb.created_at.isoformat(),
            }
        }


@router.post("/embeddings/batch")
def create_embeddings_batch(payload: EmbeddingBatchRequest) -> dict:
    with SessionLocal() as session:
        created = []
        for item in payload.embeddings[:128]:
            emb = store_embedding(
                session,
                item.note_id,
                item.content_hash,
                item.vector,
                item.model,
                chunk_index=item.chunk_index,
                chunk_text=item.chunk_text,
                heading_path=item.heading_path,
                start_line=item.start_line,
                end_line=item.end_line,
                token_count=item.token_count,
                provider=item.provider,
            )
            created.append(
                {
                    "id": emb.id,
                    "note_id": emb.note_id,
                    "chunk_index": emb.chunk_index,
                }
            )
        return {"embeddings": created, "count": len(created)}


@router.get("/embeddings/similar/{note_id}")
def similar_notes(note_id: int, limit: int = 10) -> dict:
    with SessionLocal() as session:
        emb = session.execute(
            select(EmbeddingRecord)
            .where(EmbeddingRecord.note_id == note_id)
            .order_by(EmbeddingRecord.created_at.desc())
        ).scalar_one_or_none()
        if not emb:
            return {"similar": []}
        vector = decode_embedding_vector(emb)
        results = find_similar_notes(
            session, vector, exclude_note_id=note_id, limit=limit
        )
        return {"similar": results}


@router.get("/embeddings/similar-chunks/{note_id}")
def similar_chunk_notes(note_id: int, limit: int = 10) -> dict:
    with SessionLocal() as session:
        return {
            "similar": find_similar_chunk_notes(
                session, source_note_id=note_id, limit=limit
            )
        }
