from __future__ import annotations

import ipaddress
import json
import socket
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from typing import Any
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select

from berrybrain_api.ai_configuration import (
    PROVIDERS,
    AIConfiguration,
    configuration_gate,
    load_configuration,
    provider_catalog,
    save_configuration,
)
from berrybrain_api.config import get_settings as get_app_settings
from berrybrain_api.database import SessionLocal
from berrybrain_api.models import SettingRecord
from berrybrain_api.security import (
    assert_csrf,
    normalize_email,
    require_session_user,
)
from berrybrain_api.settings_store import decode_setting_value

router = APIRouter(prefix="/api/v1/ai", tags=["ai-configuration"])


class ConfigurationPayload(BaseModel):
    configuration: AIConfiguration
    api_key: str = ""


class ProviderModelsPayload(BaseModel):
    endpoint_url: str = ""
    api_key: str = ""


def _require_admin_csrf(request: Request) -> None:
    app_settings = get_app_settings()
    with SessionLocal() as session:
        user, session_record = require_session_user(session, app_settings, request)
        if normalize_email(user.email) != normalize_email(app_settings.admin_email):
            raise HTTPException(status_code=403, detail="Owner access required")
        assert_csrf(app_settings, request, session_record)


@router.get("/providers")
def list_providers() -> dict[str, object]:
    return {"providers": provider_catalog()}


@router.get("/providers/{provider_id}/models")
def list_provider_models(provider_id: str) -> dict[str, object]:
    provider = PROVIDERS.get(provider_id)
    if provider is None:
        raise HTTPException(status_code=404, detail="Provider not found")
    with SessionLocal() as session:
        endpoint = _provider_endpoint(session, provider_id)
        api_key = _setting(session, "ai_api_key")
    try:
        models = _fetch_models(provider_id, endpoint, api_key)
    except (OSError, ValueError, urllib.error.URLError) as exc:
        raise HTTPException(
            status_code=502, detail="Provider models could not be loaded"
        ) from exc
    return {"providerId": provider_id, "models": [{"id": item} for item in models]}


@router.post(
    "/providers/{provider_id}/models",
    dependencies=[Depends(_require_admin_csrf)],
)
def discover_provider_models(
    provider_id: str, payload: ProviderModelsPayload
) -> dict[str, object]:
    provider = PROVIDERS.get(provider_id)
    if provider is None:
        raise HTTPException(status_code=404, detail="Provider not found")
    endpoint = payload.endpoint_url.strip() or str(provider["url"])
    _validate_provider_endpoint(provider_id, endpoint)
    try:
        models = _fetch_models(provider_id, endpoint, payload.api_key.strip())
    except (OSError, ValueError, urllib.error.URLError) as exc:
        raise HTTPException(
            status_code=422, detail="Provider models could not be loaded"
        ) from exc
    return {"providerId": provider_id, "models": [{"id": item} for item in models]}


@router.get("/configuration")
def get_configuration() -> dict[str, object]:
    with SessionLocal() as session:
        configuration = load_configuration(session)
        gate = configuration_gate(session)
    return {
        "configuration": (
            configuration.model_dump(mode="json") if configuration else None
        ),
        "configurationGate": gate,
    }


@router.post("/configuration/validate", dependencies=[Depends(_require_admin_csrf)])
def validate_configuration(payload: ConfigurationPayload) -> dict[str, object]:
    configuration = payload.configuration
    provider = PROVIDERS[configuration.main.provider_id]
    endpoint = configuration.endpoint_url or str(provider["url"])
    _validate_provider_endpoint(configuration.main.provider_id, endpoint)
    with SessionLocal() as session:
        api_key = payload.api_key.strip() or _setting(session, "ai_api_key")
    if configuration.mode == "cloud" and not api_key:
        raise HTTPException(status_code=422, detail="Cloud API key is required")
    try:
        models = _fetch_models(
            configuration.main.provider_id,
            endpoint,
            api_key,
        )
    except (OSError, ValueError, urllib.error.URLError) as exc:
        raise HTTPException(
            status_code=422, detail="Provider compatibility test failed"
        ) from exc
    requested = _validate_requested_models(configuration, models)
    capabilities = {
        "chat": True,
        "embeddings": True,
        "structuredOutput": True,
        "health": True,
        "models": sorted(requested),
    }
    from berrybrain_api.judge_committee import (
        DEFAULT_COMMITTEE_SIZE,
        MIN_COMMITTEE_SIZE,
        recommend_committee,
    )

    committee = recommend_committee(
        provider=configuration.judge.provider_id,
        available_models=models,
        generator_model=configuration.main.model_id,
        primary_judge_model=configuration.judge.model_id,
        committee_size=DEFAULT_COMMITTEE_SIZE,
    )
    return {
        "valid": True,
        "capabilitySnapshot": capabilities,
        "judgeDefaults": {
            "mode": (
                "committee" if len(committee) >= MIN_COMMITTEE_SIZE else "single_model"
            ),
            "committeeSize": DEFAULT_COMMITTEE_SIZE,
            "committee": committee,
        },
    }


@router.put("/configuration", dependencies=[Depends(_require_admin_csrf)])
def put_configuration(payload: ConfigurationPayload) -> dict[str, object]:
    configuration = payload.configuration.model_copy(
        update={
            "capability_snapshot": payload.configuration.capability_snapshot
            or {"validated": True}
        }
    )
    provider = PROVIDERS[configuration.main.provider_id]
    endpoint = configuration.endpoint_url or str(provider["url"])
    _validate_provider_endpoint(configuration.main.provider_id, endpoint)
    with SessionLocal() as session:
        api_key = payload.api_key.strip() or _setting(session, "ai_api_key")
        if configuration.mode == "cloud" and not api_key:
            raise HTTPException(status_code=422, detail="Cloud API key is required")
        try:
            models = _fetch_models(
                configuration.main.provider_id,
                endpoint,
                api_key,
            )
        except (OSError, ValueError, urllib.error.URLError) as exc:
            raise HTTPException(
                status_code=422, detail="Provider compatibility test failed"
            ) from exc
        _validate_requested_models(configuration, models)
        from berrybrain_api.settings_store import set_setting

        if configuration.mode == "cloud" and payload.api_key.strip():
            set_setting(session, "ai_api_key", payload.api_key.strip())
        set_setting(session, "onboarding_completed", "true")
        from berrybrain_api.judge_committee import (
            DEFAULT_COMMITTEE_SIZE,
            configure_provider_committee,
            judge_model_candidates,
            load_judge_config,
        )

        current_judge = load_judge_config(session)
        candidates = judge_model_candidates(
            available_models=models,
            generator_model=configuration.main.model_id,
            primary_judge_model=configuration.judge.model_id,
            preferred_models=[
                str(item.get("model") or "") for item in current_judge.committee
            ],
        )
        validated_judge_models = _probe_judge_models(
            configuration.judge.provider_id,
            endpoint,
            api_key,
            candidates,
            required=max(
                DEFAULT_COMMITTEE_SIZE,
                current_judge.committee_size,
            ),
        )

        judge_config = configure_provider_committee(
            session,
            provider=configuration.judge.provider_id,
            available_models=validated_judge_models,
            generator_model=configuration.main.model_id,
            primary_judge_model=configuration.judge.model_id,
        )
        configuration = configuration.model_copy(
            update={
                "judge": configuration.judge.model_copy(
                    update={"mode": judge_config.mode.value}
                )
            }
        )
        saved = save_configuration(session, configuration, validated=True)
        session.commit()
        gate = configuration_gate(session)
    return {
        "configuration": saved.model_dump(mode="json"),
        "configurationGate": gate,
    }


def _validate_requested_models(
    configuration: AIConfiguration, models: list[str]
) -> set[str]:
    requested = {
        configuration.main.model_id,
        configuration.embedding.model_id,
        configuration.judge.model_id,
        configuration.hipporag.model_id,
    }
    missing = sorted(model for model in requested if model not in models)
    if models and missing:
        raise HTTPException(
            status_code=422,
            detail={"code": "models_unavailable", "models": missing},
        )
    return requested


def _provider_endpoint(session, provider_id: str) -> str:
    configuration = load_configuration(session)
    if configuration and configuration.main.provider_id == provider_id:
        return configuration.endpoint_url or str(PROVIDERS[provider_id]["url"])
    if provider_id == "ollama":
        return _setting(session, "ollama_base_url") or str(PROVIDERS["ollama"]["url"])
    return str(PROVIDERS[provider_id]["url"])


def _fetch_models(provider_id: str, endpoint: str, api_key: str) -> list[str]:
    base = endpoint.rstrip("/")
    path = "/api/tags" if provider_id == "ollama" else "/models"
    request = urllib.request.Request(f"{base}{path}")
    if api_key:
        request.add_header("Authorization", f"Bearer {api_key}")
    request.add_header("Accept", "application/json")
    with urllib.request.urlopen(request, timeout=15) as response:
        if int(response.status) >= 400:
            raise ValueError("Provider returned an error")
        payload: Any = json.loads(response.read())
    if isinstance(payload, list):
        raw = payload
    elif provider_id == "ollama":
        raw = payload.get("models", [])
    else:
        raw = payload.get("data", payload.get("models", []))
    models = []
    for item in raw:
        model_id = (
            item
            if isinstance(item, str)
            else item.get("id") or item.get("name") or item.get("model")
        )
        if model_id:
            models.append(str(model_id).strip())
    return sorted(set(models))


def _probe_judge_models(
    provider_id: str,
    endpoint: str,
    api_key: str,
    candidates: list[str],
    *,
    required: int,
) -> list[str]:
    from berrybrain_api.ai_gateway import _cloud_json, _ollama_json

    def probe(model: str) -> bool:
        try:
            if provider_id == "ollama":
                result = _ollama_json(
                    {"ollama_base_url": endpoint, "ollama_model": model},
                    "Return an object with probe set to true.",
                    "Return one JSON object and no prose.",
                    8,
                    32,
                )
            else:
                result = _cloud_json(
                    {
                        "cloud_api_url": endpoint,
                        "cloud_api_key": api_key,
                        "cloud_model": model,
                    },
                    "Return an object with probe set to true.",
                    "Return one JSON object and no prose.",
                    12,
                    32,
                )
            return isinstance(result, dict) and result.get("probe") is True
        except Exception:
            return False

    max_probes = min(len(candidates), 8 if provider_id == "ollama" else 12)
    selected = candidates[:max_probes]
    if provider_id == "ollama":
        checks = [probe(model) for model in selected]
    else:
        with ThreadPoolExecutor(max_workers=min(3, len(selected) or 1)) as executor:
            checks = list(executor.map(probe, selected))
    return [model for model, valid in zip(selected, checks, strict=True) if valid][
        :required
    ]


def _validate_provider_endpoint(provider_id: str, endpoint: str) -> None:
    parsed = urlparse(endpoint)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise HTTPException(status_code=422, detail="Provider endpoint URL is invalid")
    provider = PROVIDERS[provider_id]
    official_url = str(provider["url"]).rstrip("/")
    if provider_id not in {"custom-cloud", "ollama"}:
        if endpoint.rstrip("/") != official_url:
            raise HTTPException(
                status_code=422,
                detail="Known providers must use their registered endpoint URL",
            )
        return
    if provider_id == "ollama":
        return
    if parsed.scheme != "https":
        raise HTTPException(
            status_code=422,
            detail="Custom cloud providers must use HTTPS",
        )
    try:
        addresses = {
            item[4][0]
            for item in socket.getaddrinfo(
                parsed.hostname,
                parsed.port or 443,
                type=socket.SOCK_STREAM,
            )
        }
    except socket.gaierror as exc:
        raise HTTPException(
            status_code=422,
            detail="Custom provider hostname could not be resolved",
        ) from exc
    for address in addresses:
        ip = ipaddress.ip_address(address)
        if not ip.is_global:
            raise HTTPException(
                status_code=422,
                detail="Custom cloud providers must resolve to public addresses",
            )


def _setting(session, key: str) -> str:
    row = session.scalar(select(SettingRecord).where(SettingRecord.key == key))
    return decode_setting_value(key, row.value) if row else ""
