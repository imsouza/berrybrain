from __future__ import annotations

import re
from typing import Any

SENSITIVE_KEY_MARKERS = (
    "api_key",
    "apikey",
    "password",
    "secret",
    "token",
    "authorization",
    "credential",
)

SECRET_PATTERNS = (
    re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/-]{12,}=?=?"),
    re.compile(r"\b(?:ghp_|github_pat_)[A-Za-z0-9_]{16,}\b"),
    re.compile(r"\b(?:sk-|nvapi-)[A-Za-z0-9_-]{12,}\b"),
    re.compile(r"(?i)\b(api[_-]?key|password|secret|token)\b\s*[:=]\s*[^\s,;]+"),
)


def redact_text(value: str) -> str:
    redacted = str(value or "")
    for pattern in SECRET_PATTERNS:
        redacted = pattern.sub(_replacement, redacted)
    return redacted


def redact_value(value: Any, key: str = "") -> Any:
    if _is_sensitive_key(key):
        return "[REDACTED]"
    if isinstance(value, dict):
        return {
            str(item_key): redact_value(item_value, str(item_key))
            for item_key, item_value in value.items()
        }
    if isinstance(value, list):
        return [redact_value(item) for item in value]
    if isinstance(value, tuple):
        return [redact_value(item) for item in value]
    if isinstance(value, str):
        return redact_text(value)
    return value


def _is_sensitive_key(key: str) -> bool:
    normalized = key.lower().replace("-", "_")
    return any(marker in normalized for marker in SENSITIVE_KEY_MARKERS)


def _replacement(match: re.Match[str]) -> str:
    text = match.group(0)
    if ":" in text:
        return f"{text.split(':', 1)[0]}: [REDACTED]"
    if "=" in text:
        return f"{text.split('=', 1)[0]}=[REDACTED]"
    if text.lower().startswith("bearer "):
        return "Bearer [REDACTED]"
    return "[REDACTED]"
