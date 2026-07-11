from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import delete, func, select, text

from berrybrain_api.config import get_settings as get_app_settings
from berrybrain_api.database import SessionLocal
from berrybrain_api.security import get_session_user, normalize_email, require_admin
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
    NoteAttachmentRecord,
    NotificationRecord,
    SettingRecord,
    TagRecord,
    WorkerStatus,
)
from berrybrain_api.settings_store import (
    get_setting,
    list_settings,
    set_setting,
    serialize_setting,
)
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/settings", tags=["settings"])

SECRET_KEYS = {"ai_api_key", "graph_ai_api_key"}


def _caller_state(request: Request) -> str:
    app_settings = get_app_settings()
    with SessionLocal() as session:
        result = get_session_user(session, app_settings, request)
        if result is None:
            return "anon"
        user, _ = result
        if normalize_email(user.email) == normalize_email(app_settings.admin_email):
            return "admin"
        return "user"


class UpdateSettingRequest(BaseModel):
    value: str


class WipeDataRequest(BaseModel):
    reset_settings: bool = False


WIPE_MODELS = [
    GraphEdgeRecord,
    GraphNodeRecord,
    EmbeddingRecord,
    GeneratedMetadataRecord,
    ConnectionRecord,
    ConceptRecord,
    InsightRecord,
    NotificationRecord,
    AutomationLogRecord,
    JobRecord,
    WorkerStatus,
    TagRecord,
    NoteAttachmentRecord,
    NoteRecord,
]


@router.get("")
def get_settings_list(request: Request) -> dict:
    hide_secrets = _caller_state(request) == "user"
    with SessionLocal() as session:
        settings = list_settings(session)
        items = []
        for s in settings:
            data = serialize_setting(s)
            if hide_secrets and data.get("key") in SECRET_KEYS:
                data["value"] = ""
            items.append(data)
        return {"settings": items}


@router.get("/ai/config")
def get_ai_config(request: Request) -> dict:
    hide_secrets = _caller_state(request) == "user"
    with SessionLocal() as session:

        def _get(key: str) -> str:
            row = session.execute(
                select(SettingRecord).where(SettingRecord.key == key.replace("__", "/"))
            ).scalar_one_or_none()
            return row.value if row else ""

        api_url = _get("ai_api_url") or _get("ai_custom_url")
        return {
            "provider": _get("ai_provider") or "local",
            "cloud_api_url": api_url,
            "cloud_api_key": "" if hide_secrets else _get("ai_api_key"),
            "cloud_model": _get("ai_model"),
            "embedding_model": _get("kb_embedding_model") or _get("embedding_model"),
            "cloud_embedding_model": _get("kb_embedding_model")
            or _get("cloud_embedding_model")
            or _get("embedding_model"),
            "kb_vector_store": _get("kb_vector_store") or "sqlite",
            "kb_embedding_provider": _get("kb_embedding_provider")
            or _get("ai_provider")
            or "local",
        }


@router.get("/graph/config")
def get_graph_config(request: Request) -> dict:
    hide_secrets = _caller_state(request) == "user"
    with SessionLocal() as session:

        def _get(key: str) -> str:
            row = session.execute(
                select(SettingRecord).where(SettingRecord.key == key)
            ).scalar_one_or_none()
            return row.value if row else ""

        return {
            "provider": _get("graph_ai_provider") or _get("ai_provider") or "local",
            "cloud_api_url": _get("graph_ai_api_url")
            or _get("ai_api_url")
            or _get("ai_custom_url"),
            "cloud_api_key": ""
            if hide_secrets
            else (_get("graph_ai_api_key") or _get("ai_api_key")),
            "cloud_model": _get("graph_ai_model") or _get("ai_model"),
            "ollama_model": _get("graph_ollama_model") or _get("ollama_model"),
            "auto_confirm_confidence": _get("graph_auto_confirm_confidence") or "0.9",
            "default_layout": _get("graph_default_layout") or "brain",
        }


@router.get("/ai/models")
def get_ai_models(url: str = "", key: str = "") -> dict:
    import urllib.request, json as _json

    with SessionLocal() as session:

        def _get(k: str) -> str:
            row = session.execute(
                select(SettingRecord).where(SettingRecord.key == k)
            ).scalar_one_or_none()
            return row.value if row else ""

        api_url = url or _get("ai_api_url") or _get("ai_custom_url")
        api_key = key or _get("ai_api_key")
        if not api_url or not api_key:
            return {"models": [], "error": "URL ou API Key nao configurada"}

        base = api_url.rstrip("/")
        try:
            req = urllib.request.Request(f"{base}/models")
            req.add_header("Authorization", f"Bearer {api_key}")
            r = urllib.request.urlopen(req, timeout=10)
            d = _json.loads(r.read())
            models = [
                {"id": m["id"]}
                for m in (d.get("data", []) or [])
                if m.get("id") and len(m.get("id", "")) < 80
            ]
            return {"models": models}
        except Exception as e:
            return {"models": [], "error": str(e)}


@router.get("/{key:path}")
def get_setting_endpoint(key: str, request: Request) -> dict:
    with SessionLocal() as session:
        setting = get_setting(session, key)
        data = serialize_setting(setting)
        if key in SECRET_KEYS and _caller_state(request) == "user":
            data["value"] = ""
        return {"setting": data}


@router.put("/{key:path}")
def update_setting_endpoint(
    key: str, payload: UpdateSettingRequest, request: Request
) -> dict:
    if _caller_state(request) == "user":
        raise HTTPException(
            status_code=403, detail="Only the admin can change workspace settings"
        )
    with SessionLocal() as session:
        setting = set_setting(session, key, payload.value)
        return {"setting": serialize_setting(setting)}


@router.post("/danger/wipe", dependencies=[Depends(require_admin)])
def wipe_all_data(payload: WipeDataRequest) -> dict:
    cfg = get_app_settings()
    vault_path = cfg.vault_path.resolve()
    if not vault_path.exists() or not vault_path.is_dir():
        raise HTTPException(status_code=400, detail="Vault path is not available")
    if str(vault_path) in {"/", "/app", "/app/data"}:
        raise HTTPException(status_code=400, detail="Unsafe vault path")

    deleted_rows: dict[str, int] = {}
    with SessionLocal() as session:
        for model in WIPE_MODELS:
            table = model.__tablename__
            count = (
                session.execute(select(func.count()).select_from(model)).scalar() or 0
            )
            session.execute(delete(model))
            deleted_rows[table] = int(count)
        try:
            session.execute(text("DELETE FROM notes_fts"))
        except Exception:
            pass
        if payload.reset_settings:
            count = (
                session.execute(
                    select(func.count()).select_from(SettingRecord)
                ).scalar()
                or 0
            )
            session.execute(delete(SettingRecord))
            deleted_rows["settings"] = int(count)
        session.commit()

    deleted_files = _wipe_vault_files(vault_path)
    return {
        "status": "wiped",
        "settingsPreserved": not payload.reset_settings,
        "deletedRows": deleted_rows,
        "deletedFiles": deleted_files,
    }


def _wipe_vault_files(vault_path: Path) -> int:
    deleted = 0
    for item in sorted(vault_path.rglob("*"), key=lambda p: len(p.parts), reverse=True):
        if item.is_file():
            item.unlink()
            deleted += 1
        elif item.is_dir():
            try:
                item.rmdir()
            except OSError:
                pass
    vault_path.mkdir(parents=True, exist_ok=True)
    return deleted
