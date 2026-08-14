from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass(frozen=True)
class SettingSpec:
    kind: str = "text"
    choices: frozenset[str] = frozenset()
    minimum: float | None = None
    maximum: float | None = None
    max_length: int = 512
    allow_empty: bool = True


def _choice(*values: str) -> SettingSpec:
    return SettingSpec(kind="choice", choices=frozenset(values), allow_empty=False)


def _integer(minimum: int, maximum: int) -> SettingSpec:
    return SettingSpec(kind="integer", minimum=minimum, maximum=maximum)


def _number(minimum: float, maximum: float) -> SettingSpec:
    return SettingSpec(kind="number", minimum=minimum, maximum=maximum)


PUBLIC_SETTING_SPECS: dict[str, SettingSpec] = {
    "onboarding_completed": _choice("true", "false"),
    "theme": _choice("light", "dark"),
    "lang": _choice("en"),
    "font_size": _integer(12, 24),
    "editor_font_size": _integer(12, 32),
    "ui_font": _choice("inter", "system"),
    "editor_font": _choice("mono", "sans"),
    "display_name": SettingSpec(max_length=120),
    "graph_auto_confirm_confidence": _number(0.0, 1.0),
    "graph_default_layout": _choice("brain", "radial", "type", "connections"),
    "graph_min_shared_concepts": _integer(2, 10),
    "kb_vector_store": _choice("sqlite", "qdrant", "chroma"),
    "kb_embedding_provider": _choice("local", "cloud"),
    "kb_embedding_model": SettingSpec(max_length=200),
    "kb_chunk_size": _integer(128, 8192),
    "kb_chunk_overlap": _integer(0, 4096),
    "qdrant_url": SettingSpec(kind="url"),
    "qdrant_collection": SettingSpec(max_length=120),
    "chroma_url": SettingSpec(kind="url"),
    "chroma_collection": SettingSpec(max_length=120),
    "cognitive_retrieval_mode": _choice("hybrid", "kb_first", "graph_first"),
    "semantic_data_enabled": _choice("true", "false"),
    "insights_auto_interval_hours": _integer(1, 720),
    "research_mode_enabled": _choice("true", "false"),
    "judge_enabled": _choice("true", "false"),
    "hipporag_enabled": _choice("true", "false"),
    "automatic_vault_organization": _choice("true", "false"),
    "attachment_image_limit_mb": _integer(1, 1024),
    "attachment_video_limit_mb": _integer(1, 8192),
    "attachment_audio_limit_mb": _integer(1, 4096),
    "attachment_other_limit_mb": _integer(1, 4096),
    "attachment_ocr_language": SettingSpec(max_length=32, allow_empty=False),
    "attachment_transcription_executable": _choice("faster-whisper", "whisper"),
    "attachment_transcription_model": SettingSpec(max_length=120, allow_empty=False),
    "ai_provider": _choice("local", "cloud"),
    "ai_api_url": SettingSpec(kind="url"),
    "ai_custom_url": SettingSpec(kind="url"),
    "ai_api_key": SettingSpec(max_length=4096),
    "ai_model": SettingSpec(max_length=200),
    "graph_ai_provider": _choice("local", "cloud"),
    "graph_ai_api_url": SettingSpec(kind="url"),
    "graph_ai_api_key": SettingSpec(max_length=4096),
    "graph_ai_model": SettingSpec(max_length=200),
    "ollama_base_url": SettingSpec(kind="url"),
    "ollama_model": SettingSpec(max_length=200),
    "graph_ollama_model": SettingSpec(max_length=200),
    "judge_provider": SettingSpec(max_length=80),
    "judge_model": SettingSpec(max_length=200),
    "hipporag_provider": SettingSpec(max_length=80),
    "hipporag_model": SettingSpec(max_length=200),
    "remote_content_consent": _choice("true", "false"),
}


def validate_public_setting(key: str, value: str) -> str:
    spec = PUBLIC_SETTING_SPECS.get(key)
    if spec is None:
        raise ValueError("Unknown setting key")
    normalized = str(value).strip()
    if not normalized and not spec.allow_empty:
        raise ValueError("Setting value is required")
    if len(normalized) > spec.max_length:
        raise ValueError(f"Setting value exceeds {spec.max_length} characters")
    if spec.kind == "choice" and normalized not in spec.choices:
        raise ValueError("Unsupported setting value")
    if spec.kind in {"integer", "number"}:
        try:
            parsed = int(normalized) if spec.kind == "integer" else float(normalized)
        except ValueError as exc:
            raise ValueError("Setting value must be numeric") from exc
        if spec.minimum is not None and parsed < spec.minimum:
            raise ValueError(f"Setting value must be at least {spec.minimum:g}")
        if spec.maximum is not None and parsed > spec.maximum:
            raise ValueError(f"Setting value must be at most {spec.maximum:g}")
        normalized = str(parsed)
    if spec.kind == "url" and normalized:
        parsed_url = urlparse(normalized)
        if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
            raise ValueError("Setting value must be an HTTP or HTTPS URL")
    return normalized
