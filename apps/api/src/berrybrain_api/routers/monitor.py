import json
from datetime import UTC, datetime

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import select

from berrybrain_api.database import SessionLocal
from berrybrain_api.jobs import list_jobs, parse_json
from berrybrain_api.models import (
    ConnectionRecord,
    EmbeddingRecord,
    GeneratedMetadataRecord,
    InsightRecord,
    NoteRecord,
    WorkerStatus,
)
from berrybrain_api.services import find_similar_notes, store_embedding

router = APIRouter(prefix="/api/v1", tags=["monitor"])


class HeartbeatRequest(BaseModel):
    jobs_processed: int = 0
    errors: int = 0
    ollama_healthy: bool = False


@router.get("/monitor/stats")
def monitor_stats() -> dict:
    with SessionLocal() as session:
        jobs = list_jobs(session, limit=200)
        completed = [j for j in jobs if j.status == "completed"]
        failed = [j for j in jobs if j.status == "failed"]
        pending = [j for j in jobs if j.status == "pending"]
        types = {}
        for j in completed:
            types[j.type] = types.get(j.type, 0) + 1
        running = [j for j in jobs if j.status == "running"]
        return {
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
        ws.ollama_healthy = payload.ollama_healthy
        session.commit()
        session.refresh(ws)
        return {
            "worker": {
                "status": ws.status,
                "last_heartbeat": ws.last_heartbeat.isoformat(),
                "jobs_processed": ws.jobs_processed,
                "errors": ws.errors,
                "ollama_healthy": ws.ollama_healthy,
            }
        }


@router.get("/worker/status")
def worker_status() -> dict:
    with SessionLocal() as session:
        ws = session.execute(
            select(WorkerStatus).order_by(WorkerStatus.id.desc()).limit(1)
        ).scalar_one_or_none()
        if ws is None:
            return {"worker": None}
        return {
            "worker": {
                "status": ws.status,
                "last_heartbeat": ws.last_heartbeat.isoformat(),
                "jobs_processed": ws.jobs_processed,
                "errors": ws.errors,
                "ollama_healthy": ws.ollama_healthy,
            }
        }


class EmbeddingRequest(BaseModel):
    note_id: int
    content_hash: str = ""
    vector: list[float]
    model: str = "bge-m3"


@router.post("/embeddings")
def create_embedding(payload: EmbeddingRequest) -> dict:
    with SessionLocal() as session:
        emb = store_embedding(
            session,
            payload.note_id,
            payload.content_hash,
            payload.vector,
            payload.model,
        )
        return {
            "embedding": {
                "id": emb.id,
                "note_id": emb.note_id,
                "created_at": emb.created_at.isoformat(),
            }
        }


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
        vector = json.loads(emb.vector) if isinstance(emb.vector, str) else emb.vector
        results = find_similar_notes(
            session, vector, exclude_note_id=note_id, limit=limit
        )
        return {"similar": results}
