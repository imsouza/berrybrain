from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from berrybrain_api.models import SettingRecord
from berrybrain_api.settings_store import decode_setting_value, set_setting

AI_CONFIGURATION_KEY = "ai_configuration_v2"
AI_CONFIGURATION_SCHEMA_VERSION: Literal[2] = 2

PROVIDERS = {
    "nvidia-nim": {
        "label": "NVIDIA NIM",
        "mode": "cloud",
        "url": "https://integrate.api.nvidia.com/v1",
    },
    "openai": {
        "label": "OpenAI",
        "mode": "cloud",
        "url": "https://api.openai.com/v1",
    },
    "openrouter": {
        "label": "OpenRouter",
        "mode": "cloud",
        "url": "https://openrouter.ai/api/v1",
    },
    "groq": {
        "label": "Groq",
        "mode": "cloud",
        "url": "https://api.groq.com/openai/v1",
    },
    "deepseek": {
        "label": "DeepSeek",
        "mode": "cloud",
        "url": "https://api.deepseek.com",
    },
    "custom-cloud": {
        "label": "Custom OpenAI-compatible",
        "mode": "cloud",
        "url": "",
    },
    "ollama": {
        "label": "Ollama",
        "mode": "local",
        "url": "http://localhost:11434",
    },
}


class ModelSlot(BaseModel):
    provider_id: str = ""
    model_id: str = ""


class JudgeSlot(ModelSlot):
    enabled: bool = True
    mode: Literal["single_model", "committee"] = "single_model"


class HippoRagSlot(ModelSlot):
    enabled: bool = True


class AIConfiguration(BaseModel):
    schema_version: Literal[2] = AI_CONFIGURATION_SCHEMA_VERSION
    mode: Literal["cloud", "local"]
    main: ModelSlot
    embedding: ModelSlot
    judge: JudgeSlot
    hipporag: HippoRagSlot
    endpoint_url: str = ""
    validated_at: datetime | None = None
    capability_snapshot: dict[str, object] = Field(default_factory=dict)
    configuration_fingerprint: str = ""

    @model_validator(mode="after")
    def validate_mode_and_slots(self) -> AIConfiguration:
        slots = {
            "main": self.main,
            "embedding": self.embedding,
            "judge": self.judge,
            "hipporag": self.hipporag,
        }
        for name, slot in slots.items():
            if name == "judge" and not self.judge.enabled:
                raise ValueError("Judge must be enabled")
            if name == "hipporag" and not self.hipporag.enabled:
                raise ValueError("HippoRAG must be enabled")
            provider = PROVIDERS.get(slot.provider_id)
            if provider is None:
                raise ValueError(f"Unknown provider for {name}")
            if provider["mode"] != self.mode:
                raise ValueError(
                    f"{name} provider belongs to {provider['mode']}, not {self.mode}"
                )
            if not slot.model_id.strip():
                raise ValueError(f"A model is required for {name}")
        if self.mode == "cloud" and not self.endpoint_url.strip():
            provider = PROVIDERS[self.main.provider_id]
            if not provider["url"]:
                raise ValueError("A provider endpoint URL is required")
        return self


def configuration_fingerprint(
    configuration: AIConfiguration, key_revision: str = ""
) -> str:
    payload = configuration.model_dump(mode="json")
    payload["validated_at"] = None
    payload["configuration_fingerprint"] = ""
    payload["key_revision"] = key_revision
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def provider_catalog() -> list[dict[str, object]]:
    from berrybrain_api.judge_committee import (
        DEFAULT_COMMITTEE_SIZE,
        DEFAULT_JUDGE_ROLES,
    )

    return [
        {
            "id": provider_id,
            "label": data["label"],
            "mode": data["mode"],
            "url": data["url"],
            "capabilities": [
                "chat",
                "embeddings",
                "structured_output",
                "health",
            ],
            "judgeDefaults": {
                "committeeSize": DEFAULT_COMMITTEE_SIZE,
                "roles": [dict(role) for role in DEFAULT_JUDGE_ROLES[:3]],
                "assignment": "distinct_available_non_generator_models",
            },
        }
        for provider_id, data in PROVIDERS.items()
    ]


def load_configuration(session: Session) -> AIConfiguration | None:
    row = session.execute(
        select(SettingRecord).where(SettingRecord.key == AI_CONFIGURATION_KEY)
    ).scalar_one_or_none()
    if row is None:
        return migrate_legacy_configuration(session)
    try:
        raw = decode_setting_value(AI_CONFIGURATION_KEY, row.value)
        return AIConfiguration.model_validate_json(raw)
    except (ValueError, json.JSONDecodeError):
        return None


def save_configuration(
    session: Session,
    configuration: AIConfiguration,
    *,
    validated: bool,
) -> AIConfiguration:
    key_revision = _setting(session, "ai_key_revision")
    updated = configuration.model_copy(
        update={
            "validated_at": datetime.now(UTC) if validated else None,
            "configuration_fingerprint": configuration_fingerprint(
                configuration, key_revision
            ),
        }
    )
    set_setting(
        session,
        AI_CONFIGURATION_KEY,
        updated.model_dump_json(),
    )
    provider = PROVIDERS[updated.main.provider_id]
    endpoint = updated.endpoint_url or str(provider["url"])
    legacy = {
        "ai_provider": updated.mode,
        "graph_ai_provider": updated.mode,
        "kb_embedding_provider": updated.mode,
        "judge_provider": updated.judge.provider_id,
        "hipporag_provider": updated.hipporag.provider_id,
        "ai_api_url": endpoint if updated.mode == "cloud" else "",
        "ai_custom_url": endpoint if updated.mode == "cloud" else "",
        "ollama_base_url": endpoint if updated.mode == "local" else "",
        "ai_model": updated.main.model_id if updated.mode == "cloud" else "",
        "graph_ai_model": updated.main.model_id if updated.mode == "cloud" else "",
        "ollama_model": updated.main.model_id if updated.mode == "local" else "",
        "graph_ollama_model": (
            updated.main.model_id if updated.mode == "local" else ""
        ),
        "kb_embedding_model": updated.embedding.model_id,
        "judge_model": updated.judge.model_id,
        "hipporag_model": updated.hipporag.model_id,
        "judge_enabled": "true",
        "hipporag_enabled": "true",
        "automatic_vault_organization": "true",
        "cognitive_enrich_on_save": "true",
        "remote_content_consent": "true" if updated.mode == "cloud" else "false",
    }
    for key, value in legacy.items():
        set_setting(session, key, value)
    return updated


def configuration_gate(session: Session) -> dict[str, object]:
    configuration = load_configuration(session)
    if configuration is None:
        return {
            "required": True,
            "valid": False,
            "reason": "missing_or_conflicting_configuration",
            "schemaVersion": AI_CONFIGURATION_SCHEMA_VERSION,
        }
    fingerprint = configuration_fingerprint(
        configuration, _setting(session, "ai_key_revision")
    )
    valid = bool(
        configuration.validated_at
        and configuration.configuration_fingerprint == fingerprint
    )
    return {
        "required": not valid,
        "valid": valid,
        "reason": "" if valid else "configuration_requires_validation",
        "schemaVersion": AI_CONFIGURATION_SCHEMA_VERSION,
        "mode": configuration.mode,
        "fingerprint": configuration.configuration_fingerprint,
        "validatedAt": (
            configuration.validated_at.isoformat()
            if configuration.validated_at
            else None
        ),
    }


def embedding_execution_configuration(session: Session) -> dict[str, str]:
    configuration = load_configuration(session)
    gate = configuration_gate(session)
    if configuration is None or not gate["valid"]:
        return {}
    provider = PROVIDERS[configuration.embedding.provider_id]
    endpoint = configuration.endpoint_url or str(provider["url"])
    result = {
        "provider": configuration.mode,
        "embedding_provider": configuration.mode,
        "embedding_model": configuration.embedding.model_id,
        "remote_content_consent": (
            "true" if configuration.mode == "cloud" else "false"
        ),
    }
    if configuration.mode == "cloud":
        result.update(
            {
                "cloud_api_url": endpoint,
                "cloud_api_key": _setting(session, "ai_api_key"),
                "cloud_embedding_model": configuration.embedding.model_id,
            }
        )
    else:
        result.update(
            {
                "ollama_base_url": endpoint,
                "ollama_model": configuration.embedding.model_id,
            }
        )
    return result


def migrate_legacy_configuration(session: Session) -> AIConfiguration | None:
    provider = _setting(session, "ai_provider") or "local"
    graph_provider = _setting(session, "graph_ai_provider") or provider
    embedding_provider = _setting(session, "kb_embedding_provider") or provider
    if len({provider, graph_provider, embedding_provider}) != 1:
        return None
    mode = "cloud" if provider == "cloud" else "local"
    provider_id = (
        _provider_id_for_url(
            _setting(session, "ai_api_url") or _setting(session, "ai_custom_url")
        )
        if mode == "cloud"
        else "ollama"
    )
    main_model = (
        _setting(session, "ai_model")
        if mode == "cloud"
        else _setting(session, "ollama_model")
    )
    embedding_model = _setting(session, "kb_embedding_model")
    judge_model = _setting(session, "judge_model") or main_model
    hipporag_model = _setting(session, "hipporag_model") or embedding_model
    if not all((main_model, embedding_model, judge_model, hipporag_model)):
        return None
    endpoint = (
        _setting(session, "ai_api_url") or _setting(session, "ai_custom_url")
        if mode == "cloud"
        else _setting(session, "ollama_base_url") or str(PROVIDERS["ollama"]["url"])
    )
    try:
        configuration = AIConfiguration(
            mode=mode,
            main=ModelSlot(provider_id=provider_id, model_id=main_model),
            embedding=ModelSlot(provider_id=provider_id, model_id=embedding_model),
            judge=JudgeSlot(provider_id=provider_id, model_id=judge_model),
            hipporag=HippoRagSlot(provider_id=provider_id, model_id=hipporag_model),
            endpoint_url=endpoint,
        )
    except ValueError:
        return None
    return configuration


def _setting(session: Session, key: str) -> str:
    row = session.execute(
        select(SettingRecord).where(SettingRecord.key == key)
    ).scalar_one_or_none()
    return decode_setting_value(key, row.value) if row is not None else ""


def _provider_id_for_url(url: str) -> str:
    normalized = url.rstrip("/")
    for provider_id, data in PROVIDERS.items():
        if data["mode"] == "cloud" and str(data["url"]).rstrip("/") == normalized:
            return provider_id
    return "custom-cloud"
