from __future__ import annotations

import ipaddress
import json
import re
import socket
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Literal
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import delete, func, select

from berrybrain_api.ai_configuration import (
    PROVIDERS,
    AIConfiguration,
    configuration_gate,
    load_configuration,
    load_provider_credentials,
    provider_api_key,
    provider_catalog,
    provider_endpoint,
    save_configuration,
    save_provider_credentials,
)
from berrybrain_api.cloud_compat import cloud_chat_options
from berrybrain_api.config import get_settings as get_app_settings
from berrybrain_api.database import SessionLocal
from berrybrain_api.models import EmbeddingRecord, NoteRecord, SettingRecord
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
    api_keys: dict[str, str] = Field(default_factory=dict)


class ProviderModelsPayload(BaseModel):
    endpoint_url: str = ""
    api_key: str = ""
    capability: Literal["chat", "embeddings"] | None = None


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
        api_key = provider_api_key(session, provider_id)
    try:
        models = _fetch_models(provider_id, endpoint, api_key)
    except (OSError, ValueError, urllib.error.URLError) as exc:
        raise HTTPException(status_code=502, detail=_model_catalog_error(exc)) from exc
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
    with SessionLocal() as session:
        api_key = payload.api_key.strip() or provider_api_key(session, provider_id)
    try:
        models = _fetch_models(provider_id, endpoint, api_key)
        model_results = _filter_models_by_capability(
            provider_id,
            endpoint,
            api_key,
            models,
            payload.capability,
        )
    except (OSError, ValueError, urllib.error.URLError) as exc:
        raise HTTPException(status_code=422, detail=_model_catalog_error(exc)) from exc
    return {
        "providerId": provider_id,
        "capability": payload.capability,
        "models": model_results,
    }


@router.get("/configuration")
def get_configuration() -> dict[str, object]:
    with SessionLocal() as session:
        configuration = load_configuration(session)
        gate = configuration_gate(session)
        configured_providers = sorted(load_provider_credentials(session))
        if (
            configuration
            and _setting(session, "ai_api_key")
            and configuration.main.provider_id not in configured_providers
        ):
            configured_providers.append(configuration.main.provider_id)
    return {
        "configuration": (
            configuration.model_dump(mode="json") if configuration else None
        ),
        "configurationGate": gate,
        "credentialProviders": sorted(configured_providers),
    }


@router.post("/configuration/validate", dependencies=[Depends(_require_admin_csrf)])
def validate_configuration(payload: ConfigurationPayload) -> dict[str, object]:
    configuration = payload.configuration
    with SessionLocal() as session:
        contexts = _provider_contexts(session, configuration, payload)
    requested = _validate_requested_models(configuration, contexts)
    slot_capabilities = _probe_requested_capabilities(configuration, contexts)
    capabilities = {
        "chat": True,
        "embeddings": True,
        "structuredOutput": True,
        "health": True,
        "models": sorted(requested),
        "slots": slot_capabilities,
    }
    from berrybrain_api.judge_committee import (
        DEFAULT_COMMITTEE_SIZE,
        MIN_COMMITTEE_SIZE,
        recommend_committee,
    )

    committee = recommend_committee(
        provider=configuration.judge.provider_id,
        available_models=contexts[configuration.judge.provider_id]["models"],
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
    with SessionLocal() as session:
        previous_configuration = load_configuration(session)
        contexts = _provider_contexts(session, configuration, payload)
        _validate_requested_models(configuration, contexts)
        slot_capabilities = _probe_requested_capabilities(configuration, contexts)
        configuration = configuration.model_copy(
            update={
                "capability_snapshot": {
                    **configuration.capability_snapshot,
                    "validated": True,
                    "slots": slot_capabilities,
                }
            }
        )
        from berrybrain_api.settings_store import set_setting

        supplied_keys = _supplied_api_keys(payload, configuration)
        if configuration.mode == "cloud":
            saved_keys = save_provider_credentials(session, supplied_keys)
            main_key = (
                saved_keys.get(configuration.main.provider_id)
                or contexts[configuration.main.provider_id]["api_key"]
            )
            if main_key:
                set_setting(session, "ai_api_key", str(main_key))
        set_setting(session, "onboarding_completed", "true")
        from berrybrain_api.judge_committee import (
            DEFAULT_COMMITTEE_SIZE,
            configure_provider_committee,
            judge_model_candidates,
            load_judge_config,
        )

        current_judge = load_judge_config(session)
        candidates = judge_model_candidates(
            available_models=contexts[configuration.judge.provider_id]["models"],
            generator_model=configuration.main.model_id,
            primary_judge_model=configuration.judge.model_id,
            preferred_models=[
                str(item.get("model") or "") for item in current_judge.committee
            ],
        )
        validated_judge_models = _probe_judge_models(
            configuration.judge.provider_id,
            str(contexts[configuration.judge.provider_id]["endpoint"]),
            str(contexts[configuration.judge.provider_id]["api_key"]),
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
        embedding_reindex = _queue_embedding_reindex(
            session, previous_configuration, saved
        )
        session.commit()
        gate = configuration_gate(session)
    return {
        "configuration": saved.model_dump(mode="json"),
        "configurationGate": gate,
        "embeddingReindex": embedding_reindex,
    }


def _queue_embedding_reindex(
    session,
    previous: AIConfiguration | None,
    current: AIConfiguration,
) -> dict[str, object]:
    previous_identity = (
        (previous.embedding.provider_id, previous.embedding.model_id)
        if previous is not None
        else None
    )
    current_identity = (
        current.embedding.provider_id,
        current.embedding.model_id,
    )
    if previous_identity is None or previous_identity == current_identity:
        return {"required": False, "jobsQueued": 0, "vectorsInvalidated": 0}

    from berrybrain_api.jobs import GENERATE_EMBEDDING, create_job

    vectors_invalidated = int(
        session.scalar(select(func.count(EmbeddingRecord.id))) or 0
    )
    session.execute(delete(EmbeddingRecord))
    jobs_queued = 0
    for note in session.execute(select(NoteRecord)).scalars():
        if not (note.content or "").strip():
            continue
        create_job(
            session,
            GENERATE_EMBEDDING,
            {
                "note_id": note.id,
                "note_path": note.path,
                "content_hash": note.content_hash,
                "event_type": "EMBEDDING_CONFIGURATION_CHANGED",
                "idempotency_key": (
                    f"embedding-config:{current.embedding.provider_id}:"
                    f"{current.embedding.model_id}:{note.id}:{note.content_hash}"
                ),
            },
            max_attempts=3,
            autocommit=False,
        )
        jobs_queued += 1
    return {
        "required": True,
        "jobsQueued": jobs_queued,
        "vectorsInvalidated": vectors_invalidated,
        "provider": current.embedding.provider_id,
        "model": current.embedding.model_id,
    }


def _validate_requested_models(
    configuration: AIConfiguration,
    contexts: dict[str, dict[str, Any]],
) -> set[str]:
    requested_slots = _slot_specs(configuration)
    requested = {model for _, _, model, _ in requested_slots}
    missing = [
        {"slot": slot, "provider": provider_id, "model": model}
        for slot, provider_id, model, _ in requested_slots
        if contexts[provider_id]["models"]
        and model not in contexts[provider_id]["models"]
    ]
    if missing:
        raise HTTPException(
            status_code=422,
            detail={"code": "models_unavailable", "models": missing},
        )
    return requested


def _probe_requested_capabilities(
    configuration: AIConfiguration,
    contexts: dict[str, dict[str, Any]],
) -> dict[str, dict[str, object]]:
    slots = _slot_specs(configuration)

    def probe(item: tuple[str, str, str, str]) -> tuple[str, dict[str, object]]:
        slot, provider_id, model, capability = item
        context = contexts[provider_id]
        return slot, _probe_model_capability(
            provider_id=provider_id,
            endpoint=str(context["endpoint"]),
            api_key=str(context["api_key"]),
            model=model,
            capability=capability,
        )

    with ThreadPoolExecutor(max_workers=len(slots)) as executor:
        results = list(executor.map(probe, slots))
    failures = [
        {"slot": slot, **result}
        for slot, result in results
        if not result.get("available")
    ]
    if failures:
        raise HTTPException(
            status_code=422,
            detail={"code": "model_capability_mismatch", "failures": failures},
        )
    return {slot: result for slot, result in results}


def _slot_specs(
    configuration: AIConfiguration,
) -> tuple[tuple[str, str, str, str], ...]:
    return (
        (
            "main",
            configuration.main.provider_id,
            configuration.main.model_id,
            "chat",
        ),
        (
            "embedding",
            configuration.embedding.provider_id,
            configuration.embedding.model_id,
            "embeddings",
        ),
        (
            "judge",
            configuration.judge.provider_id,
            configuration.judge.model_id,
            "chat",
        ),
        (
            "hipporag",
            configuration.hipporag.provider_id,
            configuration.hipporag.model_id,
            "chat",
        ),
    )


def _supplied_api_keys(
    payload: ConfigurationPayload, configuration: AIConfiguration
) -> dict[str, str]:
    supplied = {
        provider_id: value.strip()
        for provider_id, value in payload.api_keys.items()
        if provider_id in PROVIDERS and value.strip()
    }
    if payload.api_key.strip():
        supplied[configuration.main.provider_id] = payload.api_key.strip()
    return supplied


def _provider_contexts(
    session,
    configuration: AIConfiguration,
    payload: ConfigurationPayload,
) -> dict[str, dict[str, Any]]:
    supplied = _supplied_api_keys(payload, configuration)
    contexts: dict[str, dict[str, Any]] = {}
    provider_ids = {provider_id for _, provider_id, _, _ in _slot_specs(configuration)}
    for provider_id in sorted(provider_ids):
        endpoint = provider_endpoint(configuration, provider_id)
        _validate_provider_endpoint(provider_id, endpoint)
        api_key = supplied.get(provider_id) or provider_api_key(session, provider_id)
        if configuration.mode == "cloud" and not api_key:
            raise HTTPException(
                status_code=422,
                detail={"code": "provider_key_required", "provider": provider_id},
            )
        try:
            models = _fetch_models(provider_id, endpoint, api_key)
        except (OSError, ValueError, urllib.error.URLError) as exc:
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "provider_compatibility_failed",
                    "provider": provider_id,
                },
            ) from exc
        contexts[provider_id] = {
            "endpoint": endpoint,
            "api_key": api_key,
            "models": models,
        }
    return contexts


def _capability_http_error(exc: urllib.error.HTTPError, api_key: str) -> str:
    """Return bounded provider diagnostics without credentials or raw HTML."""
    fallback = f"Provider rejected the validation request (HTTP {exc.code})."
    try:
        payload = json.loads(exc.read(8192))
        error = payload.get("error", payload) if isinstance(payload, dict) else {}
        message = (
            error.get("message", error.get("detail", ""))
            if isinstance(error, dict)
            else error
        )
        if not isinstance(message, str) or not message.strip():
            return fallback
        if api_key:
            message = message.replace(api_key, "[REDACTED]")
        message = re.sub(r"(?i)bearer\s+\S+", "Bearer [REDACTED]", message)
        message = re.sub(
            r"\b(?:sk|sk-or|sk-opencode)-[A-Za-z0-9_-]+", "[REDACTED]", message
        )
        message = re.sub(r"[\w.+-]+@[\w.-]+", "[EMAIL]", message)
        return f"{fallback} {' '.join(message.split())[:400]}"
    except (OSError, ValueError, TypeError):
        return fallback


def _probe_model_capability(
    *,
    provider_id: str,
    endpoint: str,
    api_key: str,
    model: str,
    capability: str,
) -> dict[str, object]:
    if provider_id == "opencode-zen" and (
        capability == "embeddings" or not _zen_chat_model(model)
    ):
        return {
            "available": False,
            "model": model,
            "capability": capability,
            "status": None,
            "reason": "Zen supports documented Chat Completions models here. Select another cloud provider for embeddings.",
        }
    base = endpoint.rstrip("/")
    if capability == "embeddings":
        path = "/api/embed" if provider_id == "ollama" else "/embeddings"
        body: dict[str, object] = {"model": model, "input": "capability probe"}
        if provider_id == "nvidia-nim":
            body.update(
                {
                    "input_type": "query",
                    "encoding_format": "float",
                    "truncate": "END",
                }
            )
        timeout = 45
    else:
        path = "/api/chat" if provider_id == "ollama" else "/chat/completions"
        body = {
            "model": model,
            "messages": [{"role": "user", "content": "Reply with OK."}],
            "stream": False,
        }
        if provider_id == "ollama":
            body["stream"] = False
        else:
            body.update({"temperature": 0, "max_tokens": 1})
            body.update(cloud_chat_options(endpoint, model))
        timeout = 90
    request = urllib.request.Request(
        f"{base}{path}",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "User-Agent": "BerryBrain/1.4.8",
            **({"Authorization": f"Bearer {api_key}"} if api_key else {}),
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read())
        dimensions = None
        if capability == "embeddings":
            if provider_id == "ollama":
                vectors = payload.get("embeddings", [])
                vector = vectors[0] if vectors else []
            else:
                rows = payload.get("data", [])
                vector = rows[0].get("embedding", []) if rows else []
            if not isinstance(vector, list) or not vector:
                raise ValueError("The provider returned no embedding vector")
            dimensions = len(vector)
        return {
            "available": True,
            "model": model,
            "capability": capability,
            "status": int(getattr(response, "status", 200)),
            **({"dimensions": dimensions} if dimensions is not None else {}),
        }
    except urllib.error.HTTPError as exc:
        return {
            "available": False,
            "model": model,
            "capability": capability,
            "status": exc.code,
            "reason": _capability_http_error(exc, api_key),
        }
    except (OSError, TimeoutError, ValueError, json.JSONDecodeError):
        return {
            "available": False,
            "model": model,
            "capability": capability,
            "status": None,
            "reason": "The provider capability probe did not complete successfully.",
        }


def _filter_models_by_capability(
    provider_id: str,
    endpoint: str,
    api_key: str,
    models: list[str],
    capability: Literal["chat", "embeddings"] | None,
) -> list[dict[str, object]]:
    if capability is None:
        return [{"id": model} for model in models]

    def probe(model: str) -> dict[str, object]:
        return _probe_model_capability(
            provider_id=provider_id,
            endpoint=endpoint,
            api_key=api_key,
            model=model,
            capability=capability,
        )

    with ThreadPoolExecutor(max_workers=min(8, len(models) or 1)) as executor:
        results = list(executor.map(probe, models))
    return [
        {
            "id": str(result["model"]),
            "capability": capability,
            **(
                {"dimensions": int(result["dimensions"])}
                if result.get("dimensions") is not None
                else {}
            ),
        }
        for result in results
        if result.get("available")
    ]


def _provider_endpoint(session, provider_id: str) -> str:
    configuration = load_configuration(session)
    if configuration:
        return provider_endpoint(configuration, provider_id)
    if provider_id == "ollama":
        return _setting(session, "ollama_base_url") or str(PROVIDERS["ollama"]["url"])
    return str(PROVIDERS[provider_id]["url"])


def _zen_chat_model(model: str) -> bool:
    # Zen mixes Responses, Messages, Gemini and Chat Completions in /models.
    # Only these documented families use the adapter implemented by BerryBrain.
    # Reference: https://opencode.ai/docs/zen/#endpoints (2026-09-09).
    return model.lower().startswith(
        (
            "deepseek-",
            "minimax-",
            "glm-",
            "kimi-",
            "big-pickle",
            "nemotron-",
            "ling-",
            "mimo-",
        )
    )


def _model_catalog_error(exc: Exception) -> str:
    if isinstance(exc, urllib.error.HTTPError):
        reason = {
            401: "authentication required or invalid API key",
            403: "access denied by the provider",
            429: "provider rate limit reached; retry later",
        }.get(exc.code, "provider request failed")
        return f"Provider model catalog returned HTTP {exc.code}: {reason}."
    if isinstance(exc, TimeoutError):
        return "Provider model catalog request timed out. Please retry."
    return "Provider models could not be loaded. Check connectivity and retry."


def _fetch_models(provider_id: str, endpoint: str, api_key: str) -> list[str]:
    base = endpoint.rstrip("/")
    path = "/api/tags" if provider_id == "ollama" else "/models"
    request = urllib.request.Request(f"{base}{path}")
    if api_key:
        request.add_header("Authorization", f"Bearer {api_key}")
    request.add_header("Accept", "application/json")
    # Identify this API client explicitly; Zen rejects urllib's default agent.
    request.add_header("User-Agent", "BerryBrain/1.4.8")
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
        if model_id and (
            provider_id != "opencode-zen" or _zen_chat_model(str(model_id))
        ):
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
