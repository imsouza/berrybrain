import logging
import time
from contextlib import asynccontextmanager, suppress

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import select
from starlette.concurrency import run_in_threadpool
from starlette.middleware.trustedhost import TrustedHostMiddleware

from berrybrain_api import __version__
from berrybrain_api.ai_gateway import generate_query_embedding, get_ai_config
from berrybrain_api.api_contract import (
    PUBLIC_OPERATIONS,
    PageLimit,
    SearchLimit,
    SearchResponse,
    install_openapi_contract,
)
from berrybrain_api.config import get_settings
from berrybrain_api.database import SessionLocal, init_database
from berrybrain_api.home_summary import build_home_summary
from berrybrain_api.jobs import serialize_datetime
from berrybrain_api.models import JobRecord, NoteRecord
from berrybrain_api.performance_metrics import begin_request, record_request
from berrybrain_api.request_limits import RequestSizeLimitMiddleware
from berrybrain_api.routers import (
    ai_configuration,
    ask,
    auth,
    automation,
    backup,
    bootstrap,
    cognitive,
    concepts,
    connections,
    folders,
    graph,
    hipporag,
    insights,
    jobs,
    judge,
    maintenance,
    metrics,
    monitor,
    notes,
    notifications,
    observability,
    security_tokens,
    vault,
)
from berrybrain_api.routers import (
    settings as settings_router,
)
from berrybrain_api.search import hybrid_search
from berrybrain_api.security import (
    assert_csrf,
    get_session_user,
    require_admin,
    verify_service_token,
)
from berrybrain_api.vault_watcher import VaultWatcher

# --- Lifespan ---


@asynccontextmanager
async def lifespan(app: FastAPI):
    cfg = get_settings()
    if not cfg.session_secret:
        raise RuntimeError("BERRYBRAIN_SESSION_SECRET must be set")
    if len(cfg.session_secret) < 32:
        logging.getLogger("berrybrain").warning(
            "INSECURE: BERRYBRAIN_SESSION_SECRET is shorter than 32 characters. "
            "Set a strong random secret before exposing this service."
        )
    if cfg.environment.lower() in {"prod", "production"}:
        problems = []
        if len(cfg.session_secret) < 32:
            problems.append("BERRYBRAIN_SESSION_SECRET must be at least 32 characters")
        if not cfg.session_secure_cookie:
            problems.append("BERRYBRAIN_SESSION_SECURE_COOKIE must be true")
        if "*" in cfg.cors_origins:
            problems.append("BERRYBRAIN_CORS_ORIGINS must not contain *")
        if problems:
            raise RuntimeError("Unsafe production auth config: " + "; ".join(problems))
    init_database()
    from berrybrain_api.attachment_cleanup import drain_attachment_cleanup

    with SessionLocal() as cleanup_session:
        drain_attachment_cleanup(cleanup_session, cfg.vault_path)
    from berrybrain_api.cleanup_worker import CleanupWorker

    cleanup_worker = CleanupWorker(SessionLocal, cfg.vault_path)
    cleanup_worker.start()
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
        cleanup_worker.stop()
        if watcher:
            watcher.stop()


# --- App ---

app = FastAPI(title="BerryBrain API", version=__version__, lifespan=lifespan)
settings = get_settings()

origins = settings.cors_origins.replace(" ", "").split(",")
allowed_hosts = [
    host.strip() for host in settings.allowed_hosts.split(",") if host.strip()
]
app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Correlation-ID", "Server-Timing", "Retry-After", "Location"],
)
app.add_middleware(
    RequestSizeLimitMiddleware, maximum=lambda: settings.max_request_body_bytes
)
install_openapi_contract(app, settings)

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    "Content-Security-Policy": "default-src 'self'; frame-ancestors 'none'; base-uri 'self'",
}


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    # Fail closed: every non-exempt route requires a valid shared token
    # or a valid browser session. An empty api_token no longer disables auth.
    if request.method == "OPTIONS":
        return await call_next(request)
    is_exempt = (request.method, request.url.path) in PUBLIC_OPERATIONS
    if is_exempt:
        return await call_next(request)
    authorization = request.headers.get("Authorization", "")
    bearer = (
        authorization.removeprefix("Bearer ")
        if authorization.startswith("Bearer ")
        else ""
    )

    def authorize() -> bool:
        if bearer:
            with SessionLocal() as session:
                if verify_service_token(session, settings, bearer):
                    return True
        if request.cookies.get(settings.session_cookie_name):
            with SessionLocal() as session:
                identity = get_session_user(session, settings, request)
                if identity is not None:
                    assert_csrf(settings, request, identity[1])
                    return True
        return False

    try:
        authorized = await run_in_threadpool(authorize)
    except HTTPException as exc:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
            headers=exc.headers,
        )
    if not authorized:
        return JSONResponse(
            status_code=401,
            content={"detail": "Unauthorized"},
            headers={"WWW-Authenticate": "Bearer"},
        )
    return await call_next(request)


@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    # RequestSizeLimitMiddleware validates declared and streamed byte lengths,
    # including malformed/overlong integer headers, before the route executes.
    if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
        origin = request.headers.get("origin")
        if origin and "*" not in origins and origin not in origins:
            return JSONResponse(
                status_code=403, content={"detail": "Origin not allowed"}
            )
    response = await call_next(request)
    for name, value in SECURITY_HEADERS.items():
        response.headers.setdefault(name, value)
    if request.url.path.startswith("/api/"):
        response.headers.setdefault("Cache-Control", "no-store")
    if request.url.path in {"/docs", "/redoc", "/docs/oauth2-redirect", "/api/v1/docs"}:
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; frame-ancestors 'none'; base-uri 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; img-src 'self' data: https://fastapi.tiangolo.com"
        )
    if request.url.scheme == "https":
        response.headers.setdefault(
            "Strict-Transport-Security", "max-age=31536000; includeSubDomains"
        )
    return response


@app.middleware("http")
async def performance_metrics_middleware(request: Request, call_next):
    correlation_id = begin_request(dict(request.headers))
    started = time.perf_counter()
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
    finally:
        duration_ms = (time.perf_counter() - started) * 1000
        route_object = request.scope.get("route")
        route = str(getattr(route_object, "path", "unmatched"))
        record_request(request.method, route, status_code, duration_ms)
    response.headers["X-Correlation-ID"] = correlation_id
    response.headers["Server-Timing"] = f"app;dur={duration_ms:.3f}"
    return response


# --- Routers ---


@app.middleware("http")
async def database_maintenance_middleware(request: Request, call_next):
    from berrybrain_api.runtime_guard import MaintenanceUnavailable

    try:
        return await call_next(request)
    except MaintenanceUnavailable as exc:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
            headers=exc.headers,
        )


app.include_router(notes.router)
app.include_router(auth.router)
app.include_router(ai_configuration.router)
app.include_router(ask.router)
app.include_router(bootstrap.router)
app.include_router(jobs.router)
app.include_router(maintenance.router)
app.include_router(insights.router)
app.include_router(connections.router)
app.include_router(concepts.router)
app.include_router(cognitive.router)
app.include_router(folders.router)
app.include_router(graph.router)
app.include_router(monitor.router)
app.include_router(notifications.router)
app.include_router(security_tokens.router)
app.include_router(vault.router)
app.include_router(settings_router.router)
app.include_router(backup.router)
app.include_router(automation.router)
app.include_router(judge.router)
app.include_router(hipporag.router)
app.include_router(metrics.router)
app.include_router(observability.router)

# --- Core endpoints ---


class ResetRequest(BaseModel):
    confirm: str = ""


@app.exception_handler(RequestValidationError)
async def request_validation_error(request: Request, exc: RequestValidationError):
    # Validation diagnostics must not echo submitted passwords, keys or note bodies.
    return JSONResponse(
        status_code=422,
        content={
            "detail": [
                {"type": error["type"], "loc": list(error["loc"]), "msg": error["msg"]}
                for error in exc.errors()
            ],
        },
    )


@app.get("/api/v1", tags=["integration"])
def api_discovery() -> dict:
    return {
        "name": "BerryBrain",
        "version": __version__,
        "apiVersion": "v1",
        "workspaceModel": "single-owner-shared-workspace",
        "authentication": ["service-bearer", "browser-session-csrf"],
        "openapi": "/api/v1/openapi.json",
        "docs": "/api/v1/docs",
    }


@app.get("/api/v1/openapi.json", include_in_schema=False)
def integration_schema():
    # Relative to this document, ../.. preserves a proxy mount such as /berrybrain.
    return {**app.openapi(), "servers": [{"url": "../.."}]}


@app.get("/api/v1/docs", include_in_schema=False)
def integration_docs():
    return get_swagger_ui_html(openapi_url="./openapi.json", title="BerryBrain API v1")


@app.get("/health")
def health():
    from berrybrain_api.database import engine
    from berrybrain_api.schema_migrations import schema_diagnostic

    return {"status": "ok", "schema": schema_diagnostic(engine)}


@app.get("/api/v1/status")
def status():
    cfg = get_settings()
    with SessionLocal() as session:
        count = session.query(NoteRecord).count()
        return {
            "app": "berrybrain",
            "environment": cfg.environment,
            "public_app_url": cfg.public_app_url,
            "vault_path": str(cfg.vault_path),
            "notes": count,
        }


@app.get("/api/v1/model-router/status")
def model_router_status():
    from berrybrain_api.ai_gateway import check_router_status, get_ai_config

    with SessionLocal() as session:
        config = get_ai_config(session)
        status = check_router_status(config)
        return {"capabilities": status}


@app.get("/api/v1/model-router/capabilities")
def model_router_capabilities():
    from berrybrain_api.ai_gateway import check_router_status, get_ai_config

    with SessionLocal() as session:
        config = get_ai_config(session)
        status = check_router_status(config)
        return {"capabilities": list(status.keys())}


@app.get("/api/v1/search", response_model=SearchResponse, tags=["search"])
def search(q: str = Query(min_length=1, max_length=4000), limit: SearchLimit = 10):
    with SessionLocal() as session:
        query_vector = None
        with suppress(Exception):
            query_vector = generate_query_embedding(get_ai_config(session), q)
        return {"results": hybrid_search(session, q, limit, query_vector)}


@app.get("/api/v1/home/summary")
def home_summary():
    with SessionLocal() as session:
        return build_home_summary(session)


@app.get("/api/v1/metadata/{generation_type:path}")
def get_metadata(
    generation_type: str, note_path: str | None = None, limit: PageLimit = 10
):
    from berrybrain_api.generated_metadata import (
        get_generated_metadata,
        resolve_note_id,
        serialize_generated_metadata,
    )

    with SessionLocal() as session:
        note_id = resolve_note_id(session, note_path) if note_path else None
        metadata = get_generated_metadata(
            session, note_id=note_id, generation_type=generation_type, limit=limit
        )
        return {"metadata": [serialize_generated_metadata(m) for m in metadata]}


@app.put("/api/v1/metadata/{generation_type:path}")
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


@app.delete("/api/v1/metadata/{generation_type:path}")
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
def list_metadata_endpoint(note_path: str | None = None, limit: PageLimit = 20):
    from berrybrain_api.generated_metadata import (
        get_generated_metadata,
        resolve_note_id,
        serialize_generated_metadata,
    )

    with SessionLocal() as session:
        note_id = resolve_note_id(session, note_path) if note_path else None
        if note_id:
            metadata = get_generated_metadata(session, note_id=note_id, limit=limit)
        else:
            from berrybrain_api.models import GeneratedMetadataRecord

            metadata = list(
                session.execute(
                    select(GeneratedMetadataRecord)
                    .order_by(GeneratedMetadataRecord.id.desc())
                    .limit(limit)
                ).scalars()
            )
        return {"metadata": [serialize_generated_metadata(m) for m in metadata]}


@app.post("/api/v1/system/reset", dependencies=[Depends(require_admin)])
def reset_system(payload: ResetRequest):
    _ = payload
    raise HTTPException(
        status_code=410,
        detail=(
            "Danger zone reset moved to Settings. Use /api/v1/settings/danger/wipe."
        ),
    )


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
            by_type[job.type] += 1
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
def list_activity(limit: PageLimit = 50) -> dict:
    from berrybrain_api.automation_logs import (
        list_automation_logs,
    )
    from berrybrain_api.jobs import COMPLETED, FAILED, PENDING

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
                        "description": f"{job.type} completed",
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
                        "description": f"{job.type} failed",
                        "technicalDescription": job.type,
                        "when": serialize_datetime(job.created_at),
                        "type": "failed",
                        "error": job.error_message,
                    }
                )

        activity.sort(key=lambda x: x["when"] or "", reverse=True)
        return {"activity": activity[:limit]}
