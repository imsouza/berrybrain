from fastapi import APIRouter
from sqlalchemy import select

from berrybrain_api.database import SessionLocal
from berrybrain_api.models import SettingRecord
from berrybrain_api.settings_store import (
    get_setting,
    list_settings,
    set_setting,
    serialize_setting,
)
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/settings", tags=["settings"])


class UpdateSettingRequest(BaseModel):
    value: str


@router.get("")
def get_settings_list() -> dict:
    with SessionLocal() as session:
        settings = list_settings(session)
        return {"settings": [serialize_setting(s) for s in settings]}


@router.get("/ai/config")
def get_ai_config() -> dict:
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
            "cloud_api_key": _get("ai_api_key"),
            "cloud_model": _get("ai_model"),
        }


@router.get("/graph/config")
def get_graph_config() -> dict:
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
            "cloud_api_key": _get("graph_ai_api_key") or _get("ai_api_key"),
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
def get_setting_endpoint(key: str) -> dict:
    with SessionLocal() as session:
        setting = get_setting(session, key)
        return {"setting": serialize_setting(setting)}


@router.put("/{key:path}")
def update_setting_endpoint(key: str, payload: UpdateSettingRequest) -> dict:
    with SessionLocal() as session:
        setting = set_setting(session, key, payload.value)
        return {"setting": serialize_setting(setting)}
