import json as _json
import secrets
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import delete, func, select, text

from berrybrain_api.config import get_settings as get_app_settings
from berrybrain_api.database import SessionLocal
from berrybrain_api.security import (
    assert_csrf,
    get_session_user,
    normalize_email,
    require_session_user,
    verify_service_token,
)
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


def _safe_int(value: str | None) -> int | None:
    try:
        return int(value) if value not in {None, ""} else None
    except (TypeError, ValueError):
        return None


def _provider_name(api_url: str) -> str:
    host = (urllib.parse.urlparse(api_url).hostname or "").lower()
    if "nvidia" in host:
        return "nvidia-nim"
    if "openai" in host:
        return "openai"
    if "deepseek" in host:
        return "deepseek"
    if "groq" in host:
        return "groq"
    if "openrouter" in host:
        return "openrouter"
    return host or "cloud"


def _provider_error(error: Exception) -> str:
    if isinstance(error, urllib.error.HTTPError):
        messages = {
            400: "The provider rejected the request. Check the base URL and API key.",
            401: "The provider rejected the API key.",
            403: "The API key does not have permission to access this provider.",
            404: "The provider models endpoint was not found. Check the base URL.",
            408: "The provider timed out while testing the connection.",
            429: "The provider rate limit was reached. Try again shortly.",
        }
        return messages.get(
            error.code,
            f"The provider returned HTTP {error.code} while testing the connection.",
        )
    if isinstance(error, (TimeoutError, urllib.error.URLError)):
        reason = getattr(error, "reason", None)
        if isinstance(reason, TimeoutError) or "timed out" in str(reason).lower():
            return "The provider did not respond within 15 seconds."
        return (
            "The provider could not be reached. Check the URL and network connection."
        )
    if isinstance(error, (_json.JSONDecodeError, KeyError, TypeError, ValueError)):
        return "The provider returned an invalid response."
    return "The provider connection test failed."


def _set_values(session, values: dict[str, str]) -> None:
    existing = {
        row.key: row
        for row in session.execute(
            select(SettingRecord).where(SettingRecord.key.in_(values))
        ).scalars()
    }
    for key, value in values.items():
        setting = existing.get(key)
        if setting is None:
            session.add(SettingRecord(key=key, value=value))
        else:
            setting.value = value


def _record_ai_test(
    session,
    status: str,
    error: str = "",
    latency_ms: int | None = None,
    api_url: str = "",
    method: str = "",
) -> str:
    tested_at = datetime.now(UTC).isoformat()
    _set_values(
        session,
        {
            "ai_last_test_status": status,
            "ai_last_test_at": tested_at,
            "ai_last_test_latency_ms": "" if latency_ms is None else str(latency_ms),
            "ai_last_test_error": error,
            "ai_last_test_url": api_url.rstrip("/"),
            "ai_last_test_key_revision": _current_ai_key_revision(session),
            "ai_last_test_method": method,
        },
    )
    session.commit()
    return tested_at


def _new_key_revision() -> str:
    return secrets.token_urlsafe(18)


def _current_ai_key_revision(session) -> str:
    setting = session.execute(
        select(SettingRecord).where(SettingRecord.key == "ai_key_revision")
    ).scalar_one_or_none()
    if setting is not None and setting.value:
        return setting.value
    revision = _new_key_revision()
    _set_values(session, {"ai_key_revision": revision})
    return revision


def _caller_state(request: Request) -> str:
    app_settings = get_app_settings()
    with SessionLocal() as session:
        authorization = request.headers.get("authorization", "")
        if authorization.lower().startswith("bearer ") and verify_service_token(
            session, app_settings, authorization[7:].strip()
        ):
            return "service"
        result = get_session_user(session, app_settings, request)
        if result is None:
            return "anon"
        user, _ = result
        if normalize_email(user.email) == normalize_email(app_settings.admin_email):
            return "admin"
        return "user"


def _require_settings_reader(request: Request) -> None:
    state = _caller_state(request)
    if state == "anon":
        raise HTTPException(status_code=401, detail="Unauthorized")
    if state == "user":
        raise HTTPException(status_code=403, detail="Owner access required")


def _require_admin_csrf(request: Request) -> None:
    app_settings = get_app_settings()
    with SessionLocal() as session:
        user, session_record = require_session_user(session, app_settings, request)
        if normalize_email(user.email) != normalize_email(app_settings.admin_email):
            raise HTTPException(status_code=403, detail="Owner access required")
        assert_csrf(app_settings, request, session_record)


class UpdateSettingRequest(BaseModel):
    value: str


class AiModelsRequest(BaseModel):
    url: str = ""
    key: str = ""
    model: str = ""


class BatchUpdateSettingsRequest(BaseModel):
    values: dict[str, str]


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


@router.get("", dependencies=[Depends(_require_settings_reader)])
def get_settings_list(request: Request) -> dict:
    with SessionLocal() as session:
        settings = list_settings(session)
        items = []
        for s in settings:
            data = serialize_setting(s)
            if data.get("key") in SECRET_KEYS:
                data["configured"] = bool(data.get("value"))
                data["value"] = ""
            items.append(data)
        return {"settings": items}


@router.get("/ai/config", dependencies=[Depends(_require_settings_reader)])
def get_ai_config(request: Request) -> dict:
    hide_secrets = _caller_state(request) != "service"
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
            "ollama_base_url": _get("ollama_base_url"),
            "ollama_model": _get("ollama_model") or _get("graph_ollama_model"),
            "embedding_model": _get("kb_embedding_model") or _get("embedding_model"),
            "cloud_embedding_model": _get("kb_embedding_model")
            or _get("cloud_embedding_model")
            or _get("embedding_model"),
            "kb_vector_store": _get("kb_vector_store") or "sqlite",
            "kb_embedding_provider": _get("kb_embedding_provider")
            or _get("ai_provider")
            or "local",
            "remote_content_consent": _get("remote_content_consent") or "false",
        }


@router.get("/graph/config", dependencies=[Depends(_require_settings_reader)])
def get_graph_config(request: Request) -> dict:
    hide_secrets = _caller_state(request) != "service"
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
            "remote_content_consent": _get("remote_content_consent") or "false",
        }


@router.post("/ai/models", dependencies=[Depends(_require_admin_csrf)])
def get_ai_models(payload: AiModelsRequest) -> dict:
    with SessionLocal() as session:

        def _get(k: str) -> str:
            row = session.execute(
                select(SettingRecord).where(SettingRecord.key == k)
            ).scalar_one_or_none()
            return row.value if row else ""

        api_url = payload.url or _get("ai_api_url") or _get("ai_custom_url")
        api_key = payload.key or _get("ai_api_key")
        if not api_url or not api_key:
            _record_ai_test(
                session,
                "incomplete",
                "Provider URL and API key are required.",
                api_url=api_url,
            )
            return {
                "connected": False,
                "models": [],
                "error": "Provider URL and API key are required.",
            }

        base = api_url.rstrip("/")
        parsed = urllib.parse.urlparse(base)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            _record_ai_test(
                session,
                "failed",
                "Invalid provider URL.",
                api_url=base,
            )
            return {
                "connected": False,
                "models": [],
                "error": "Enter a valid HTTP or HTTPS provider URL.",
            }
        started = time.perf_counter()
        models: list[dict[str, str]] = []
        try:
            req = urllib.request.Request(f"{base}/models")
            req.add_header("Authorization", f"Bearer {api_key}")
            req.add_header("Accept", "application/json")
            with urllib.request.urlopen(req, timeout=15) as response:
                d = _json.loads(response.read())
            models = [
                {"id": m["id"]}
                for m in (d.get("data", []) or [])
                if m.get("id") and len(m.get("id", "")) < 80
            ]
            model = payload.model.strip()
            if not model:
                tested_at = _record_ai_test(
                    session,
                    "untested",
                    "Select a model to verify generation access.",
                    api_url=base,
                )
                return {
                    "connected": False,
                    "requiresModel": True,
                    "provider": _provider_name(base),
                    "models": models,
                    "error": "Models loaded. Select a model to verify generation access.",
                    "testedAt": tested_at,
                }
            if models and not any(item["id"] == model for item in models):
                raise ValueError("Selected model is not available from this provider")

            generation_request = urllib.request.Request(
                f"{base}/chat/completions",
                data=_json.dumps(
                    {
                        "model": model,
                        "messages": [{"role": "user", "content": "Reply with OK."}],
                        "max_tokens": 1,
                        "temperature": 0,
                        "stream": False,
                    }
                ).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                method="POST",
            )
            with urllib.request.urlopen(generation_request, timeout=30) as response:
                generation_payload = _json.loads(response.read())
            if not generation_payload.get("choices"):
                raise ValueError("Provider generation response has no choices")

            latency_ms = max(1, round((time.perf_counter() - started) * 1000))
            tested_at = _record_ai_test(
                session,
                "connected",
                "",
                latency_ms,
                api_url=base,
                method="chat_completions",
            )
            return {
                "connected": True,
                "provider": _provider_name(base),
                "models": models,
                "latencyMs": latency_ms,
                "testedAt": tested_at,
            }
        except Exception as error:
            message = _provider_error(error)
            latency_ms = max(1, round((time.perf_counter() - started) * 1000))
            tested_at = _record_ai_test(
                session,
                "failed",
                message,
                latency_ms,
                api_url=base,
                method="chat_completions" if payload.model.strip() else "models",
            )
            return {
                "connected": False,
                "models": models,
                "error": message,
                "latencyMs": latency_ms,
                "testedAt": tested_at,
            }


@router.get("/ai/status", dependencies=[Depends(_require_settings_reader)])
def get_ai_status(request: Request) -> dict:
    with SessionLocal() as session:
        values = {
            row.key: row.value
            for row in session.execute(select(SettingRecord)).scalars()
        }
    provider = values.get("ai_provider") or "local"
    api_url = values.get("ai_api_url") or values.get("ai_custom_url") or ""
    key_configured = bool(values.get("ai_api_key"))
    model_configured = bool(values.get("ai_model"))
    graph_provider = values.get("graph_ai_provider") or provider
    graph_key_configured = bool(
        values.get("graph_ai_api_key") or values.get("ai_api_key")
    )
    graph_model_configured = bool(
        values.get("graph_ai_model") or values.get("ai_model")
    )
    consent = values.get("remote_content_consent", "false").lower() == "true"
    last_test = values.get("ai_last_test_status") or "untested"
    tested_configuration_matches = (
        values.get("ai_last_test_url", "").rstrip("/") == api_url.rstrip("/")
        and values.get("ai_last_test_key_revision", "")
        == values.get("ai_key_revision", "")
        and values.get("ai_last_test_method") == "chat_completions"
    )
    if not tested_configuration_matches:
        last_test = "untested"
    if provider != "cloud":
        state = "local"
    elif not api_url or not key_configured or not model_configured:
        state = "incomplete"
    elif not consent:
        state = "disabled"
    elif last_test == "connected":
        state = "connected"
    elif last_test == "failed":
        state = "failed"
    else:
        state = "configured"
    return {
        "state": state,
        "provider": _provider_name(api_url) if provider == "cloud" else "local",
        "providerMode": provider,
        "keyConfigured": key_configured,
        "modelConfigured": model_configured,
        "model": values.get("ai_model") or "",
        "graphProviderMode": graph_provider,
        "graphKeyConfigured": graph_key_configured,
        "graphModelConfigured": graph_model_configured,
        "graphModel": values.get("graph_ai_model") or values.get("ai_model") or "",
        "remoteContentConsent": consent,
        "lastTestStatus": last_test,
        "lastTestAt": values.get("ai_last_test_at") or None,
        "lastTestLatencyMs": _safe_int(values.get("ai_last_test_latency_ms")),
        "lastError": values.get("ai_last_test_error") or "",
    }


@router.put("/batch", dependencies=[Depends(_require_admin_csrf)])
def update_settings_batch(payload: BatchUpdateSettingsRequest) -> dict:
    if not payload.values or len(payload.values) > 100:
        raise HTTPException(status_code=400, detail="Invalid settings batch")
    if any(not key or len(key) > 128 or "\x00" in key for key in payload.values):
        raise HTTPException(status_code=400, detail="Invalid setting key")

    with SessionLocal() as session:
        values = {
            key: value
            for key, value in payload.values.items()
            if key not in SECRET_KEYS or bool(value.strip())
        }
        if "ai_api_key" in values:
            values["ai_key_revision"] = _new_key_revision()
        _set_values(session, values)
        session.commit()
        return {"status": "saved", "count": len(values)}


@router.delete("/ai/key", dependencies=[Depends(_require_admin_csrf)])
def clear_ai_key() -> dict:
    with SessionLocal() as session:
        _set_values(
            session,
            {
                "ai_api_key": "",
                "graph_ai_api_key": "",
                "ai_last_test_status": "untested",
                "ai_last_test_at": "",
                "ai_last_test_latency_ms": "",
                "ai_last_test_error": "",
                "ai_last_test_url": "",
                "ai_last_test_key_fingerprint": "",
                "ai_last_test_key_revision": "",
                "ai_last_test_method": "",
                "ai_key_revision": "",
            },
        )
        session.commit()
    return {"status": "cleared"}


@router.get("/{key:path}", dependencies=[Depends(_require_settings_reader)])
def get_setting_endpoint(key: str, request: Request) -> dict:
    with SessionLocal() as session:
        setting = get_setting(session, key)
        data = serialize_setting(setting)
        if key in SECRET_KEYS:
            data["configured"] = bool(data.get("value"))
            data["value"] = ""
        return {"setting": data}


@router.put("/{key:path}", dependencies=[Depends(_require_admin_csrf)])
def update_setting_endpoint(
    key: str, payload: UpdateSettingRequest, request: Request
) -> dict:
    with SessionLocal() as session:
        setting = set_setting(session, key, payload.value)
        if key == "ai_api_key" and payload.value.strip():
            _set_values(session, {"ai_key_revision": _new_key_revision()})
            session.commit()
        data = serialize_setting(setting)
        if key in SECRET_KEYS:
            data["configured"] = bool(data.get("value"))
            data["value"] = ""
        return {"setting": data}


@router.post("/danger/wipe", dependencies=[Depends(_require_admin_csrf)])
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
