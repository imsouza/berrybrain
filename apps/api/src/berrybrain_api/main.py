from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import select
from starlette.middleware.base import BaseHTTPMiddleware

from berrybrain_api.config import get_settings
from berrybrain_api.database import SessionLocal, init_database
from berrybrain_api.automation_logs import create_automation_log
from berrybrain_api.home_summary import build_home_summary
from berrybrain_api.jobs import utc_now
from berrybrain_api.models import GeneratedMetadataRecord, JobRecord, NoteRecord
from berrybrain_api.search import text_search
from berrybrain_api.vault_watcher import VaultWatcher

from berrybrain_api.routers import (
    automation,
    backup,
    connections,
    concepts,
    graph,
    insights,
    jobs,
    monitor,
    notes,
    notifications,
    settings as settings_router,
    vault,
)

# --- Lifespan ---


@asynccontextmanager
async def lifespan(app: FastAPI):
    cfg = get_settings()
    init_database()
    watcher: VaultWatcher | None = None
    if cfg.vault_watcher_enabled:
        watcher = VaultWatcher(
            vault_path=cfg.vault_path,
            session_factory=SessionLocal,
            interval_seconds=cfg.vault_watcher_interval_seconds,
        )
        watcher.start()
        app.state.vault_watcher = watcher
    try:
        yield
    finally:
        if watcher:
            watcher.stop()


# --- App ---

app = FastAPI(title="BerryBrain API", version="0.1.0", lifespan=lifespan)
settings = get_settings()

origins = settings.cors_origins.replace(" ", "").split(",")
app.add_middleware(
    CORSMiddleware, allow_origins=origins, allow_methods=["*"], allow_headers=["*"]
)

TOKEN_EXEMPT = {
    "/health",
    "/api/v1/jobs/claim",
    "/api/v1/jobs/",
    "/api/v1/worker/heartbeat",
}


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        token = settings.api_token
        if token and request.method != "OPTIONS":
            # ponytail: /health and worker mutation endpoints stay open; everything else—including all GETs—needs the token.
            is_exempt = any(request.url.path.startswith(p) for p in TOKEN_EXEMPT)
            if not is_exempt:
                auth = request.headers.get("Authorization", "")
                if auth != f"Bearer {token}":
                    return JSONResponse(
                        status_code=401, content={"detail": "Unauthorized"}
                    )
        return await call_next(request)


app.add_middleware(AuthMiddleware)

# --- Routers ---

app.include_router(notes.router)
app.include_router(jobs.router)
app.include_router(insights.router)
app.include_router(connections.router)
app.include_router(concepts.router)
app.include_router(graph.router)
app.include_router(monitor.router)
app.include_router(notifications.router)
app.include_router(vault.router)
app.include_router(settings_router.router)
app.include_router(backup.router)
app.include_router(automation.router)

# --- Core endpoints ---


class ResetRequest(BaseModel):
    confirm: str = ""


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/v1/status")
def status():
    cfg = get_settings()
    with SessionLocal() as session:
        count = session.query(NoteRecord).count()
        return {
            "app": "berrybrain",
            "environment": cfg.environment,
            "vault_path": str(cfg.vault_path),
            "notes": count,
        }


@app.get("/api/v1/search")
def search(q: str, limit: int = 10):
    with SessionLocal() as session:
        results = text_search(session, q, limit=max(limit, 50))
        note_ids = [r["id"] for r in results]
        backlinks: dict[int, list[dict]] = {}
        if note_ids:
            from berrybrain_api.models import ConnectionRecord, NoteRecord

            rows = (
                session.query(
                    ConnectionRecord.source_note_id,
                    ConnectionRecord.target_note_id,
                    ConnectionRecord.connection_type,
                    ConnectionRecord.reason,
                    NoteRecord.path.label("source_path"),
                    NoteRecord.title.label("source_title"),
                )
                .join(NoteRecord, ConnectionRecord.source_note_id == NoteRecord.id)
                .filter(ConnectionRecord.target_note_id.in_(note_ids))
                .all()
            )
            for row in rows:
                backlinks.setdefault(row.target_note_id, []).append(
                    {
                        "note_path": row.source_path,
                        "note_title": row.source_title,
                        "connection_type": row.connection_type,
                        "reason": row.reason,
                    }
                )
        enriched = [
            {
                "title": r["title"],
                "path": r["path"],
                "score": r["score"],
                "snippet": r.get("snippet", ""),
                "backlinks": backlinks.get(r["id"], []),
            }
            for r in results
        ]
        return {"results": enriched}


@app.get("/api/v1/home/summary")
def home_summary():
    with SessionLocal() as session:
        return build_home_summary(session)


@app.get("/api/v1/metadata/{generation_type}")
def get_metadata(generation_type: str, note_path: str | None = None, limit: int = 10):
    from berrybrain_api.generated_metadata import (
        get_generated_metadata,
        resolve_note_id,
        serialize_generated_metadata,
    )

    with SessionLocal() as session:
        note_id = resolve_note_id(session, note_path) if note_path else None
        metadata = get_generated_metadata(
            session, note_id=note_id, generation_type=generation_type
        )
        return {"metadata": [serialize_generated_metadata(m) for m in metadata]}


@app.put("/api/v1/metadata/{generation_type}")
def upsert_metadata(generation_type: str, note_path: str, payload: dict):
    from berrybrain_api.generated_metadata import (
        resolve_note_id,
        serialize_generated_metadata,
        upsert_generated_metadata,
    )

    with SessionLocal() as session:
        note_id = resolve_note_id(session, note_path)
        metadata = upsert_generated_metadata(
            session,
            note_id=note_id,
            generation_type=generation_type,
            content=payload.get("content", {}),
            content_hash=payload.get("content_hash", ""),
            model_used=payload.get("model_used"),
        )
        return {"metadata": serialize_generated_metadata(metadata)}


@app.delete("/api/v1/metadata/{generation_type}")
def delete_metadata(generation_type: str, note_path: str):
    from berrybrain_api.generated_metadata import (
        delete_generated_metadata,
        resolve_note_id,
    )

    with SessionLocal() as session:
        note_id = resolve_note_id(session, note_path)
        delete_generated_metadata(
            session, note_id=note_id, generation_type=generation_type
        )
        return {"status": "deleted"}


@app.get("/api/v1/metadata")
def list_metadata_endpoint(note_path: str | None = None, limit: int = 20):
    from berrybrain_api.generated_metadata import (
        get_generated_metadata,
        resolve_note_id,
        serialize_generated_metadata,
    )

    with SessionLocal() as session:
        note_id = resolve_note_id(session, note_path) if note_path else None
        if note_id:
            metadata = get_generated_metadata(session, note_id=note_id)
        else:
            from berrybrain_api.models import GeneratedMetadataRecord

            metadata = list(
                session.execute(select(GeneratedMetadataRecord).limit(limit)).scalars()
            )
        return {"metadata": [serialize_generated_metadata(m) for m in metadata]}


@app.post("/api/v1/system/reset")
def reset_system(payload: ResetRequest):
    import shutil
    from pathlib import Path

    from berrybrain_api.database import engine
    from berrybrain_api.models import Base

    cfg = get_settings()
    if payload.confirm != "berrybrain-reset-all":
        raise HTTPException(status_code=400, detail="Invalid reset confirmation")

    md = Path("/app/data")
    vault = cfg.vault_path

    with SessionLocal() as s:
        s.close()

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    if vault.exists():
        shutil.rmtree(vault, ignore_errors=True)
        vault.mkdir(parents=True, exist_ok=True)
        for d in ["inbox", "estudos", "permanentes", "revisao", "anexos", "templates"]:
            (vault / d).mkdir(parents=True, exist_ok=True)

    if md.exists():
        shutil.rmtree(md, ignore_errors=True)
        md.mkdir(parents=True, exist_ok=True)
        for d in ["backups", "generated", "jobs", "logs", "sqlite", "vector"]:
            (md / d).mkdir(parents=True, exist_ok=True)

    from berrybrain_api.database import init_database

    init_database()

    return {"status": "reset", "message": "Todos os dados foram apagados."}


@app.get("/api/v1/system/audit")
def audit_system():
    from collections import Counter

    from sqlalchemy import func

    with SessionLocal() as session:
        total = session.query(func.count(JobRecord.id)).scalar() or 0
        completed = (
            session.query(func.count(JobRecord.id))
            .where(JobRecord.status == "completed")
            .scalar()
            or 0
        )
        failed = (
            session.query(func.count(JobRecord.id))
            .where(JobRecord.status == "failed")
            .scalar()
            or 0
        )
        running = (
            session.query(func.count(JobRecord.id))
            .where(JobRecord.status == "running")
            .scalar()
            or 0
        )
        pending = (
            session.query(func.count(JobRecord.id))
            .where(JobRecord.status == "pending")
            .scalar()
            or 0
        )

        failed_rows = (
            session.execute(select(JobRecord).where(JobRecord.status == "failed"))
            .scalars()
            .all()
        )

        by_type = Counter()
        by_reason = Counter()
        for job in failed_rows:
            by_type[job.job_type] += 1
            error = job.error_message or "unknown"
            tag = error.split(":")[0].split("\n")[0][:80]
            by_reason[tag] += 1

        completion_rate = round((completed / total * 100), 1) if total else 0

        return {
            "total_jobs": total,
            "completed": completed,
            "failed": failed,
            "running": running,
            "pending": pending,
            "completion_rate_pct": completion_rate,
            "failed_by_type": dict(by_type.most_common(20)),
            "failed_reasons": dict(by_reason.most_common(20)),
        }


@app.get("/api/v1/activity")
def list_activity(limit: int = 50) -> dict:
    from berrybrain_api.automation_logs import (
        list_automation_logs,
        serialize_automation_log,
    )
    from berrybrain_api.jobs import PENDING, COMPLETED, FAILED

    with SessionLocal() as session:
        logs = list_automation_logs(session, limit=limit)
        jobs = list(
            session.execute(
                select(JobRecord)
                .where(JobRecord.status.in_([PENDING, COMPLETED, FAILED]))
                .order_by(JobRecord.created_at.desc())
                .limit(limit)
            ).scalars()
        )

        activity = []
        for log in logs:
            activity.append(
                {
                    "id": log.id,
                    "action": log.action_type,
                    "description": log.description,
                    "technicalDescription": log.description,
                    "when": serialize_datetime(log.created_at),
                    "type": "log",
                }
            )

        for job in jobs:
            if job.status == COMPLETED:
                activity.append(
                    {
                        "id": job.id,
                        "action": job.type,
                        "description": f"{job.type} concluído",
                        "technicalDescription": job.type,
                        "when": serialize_datetime(job.completed_at or job.created_at),
                        "type": "completed",
                    }
                )
            elif job.status == FAILED:
                activity.append(
                    {
                        "id": job.id,
                        "action": job.type,
                        "description": f"{job.type} falhou",
                        "technicalDescription": job.type,
                        "when": serialize_datetime(job.created_at),
                        "type": "failed",
                        "error": job.error_message,
                    }
                )

        activity.sort(key=lambda x: x["when"] or "", reverse=True)
        return {"activity": activity[:limit]}
