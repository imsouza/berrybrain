from __future__ import annotations

import json
import os
import re
import urllib.request
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from berrybrain_api.models import SettingRecord


class GraphAIUnavailable(Exception):
    pass


def get_ai_config(session: Session) -> dict[str, str]:
    rows = session.execute(select(SettingRecord)).scalars()
    values = {row.key: row.value for row in rows}
    return {
        "provider": values.get("graph_ai_provider")
        or values.get("ai_provider", "local"),
        "cloud_api_url": values.get("graph_ai_api_url")
        or values.get("ai_api_url")
        or values.get("ai_custom_url")
        or "",
        "cloud_api_key": values.get("graph_ai_api_key") or values.get("ai_api_key", ""),
        "cloud_model": values.get("graph_ai_model") or values.get("ai_model", ""),
        "ollama_base_url": values.get("ollama_base_url")
        or os.getenv("BERRYBRAIN_OLLAMA_BASE_URL", "http://localhost:11434"),
        "ollama_model": values.get("graph_ollama_model")
        or values.get("ollama_model")
        or values.get("ai_model")
        or os.getenv("BERRYBRAIN_OLLAMA_MODEL", "qwen3:8b"),
        "auto_confirm_confidence": values.get("graph_auto_confirm_confidence", "0.9"),
        "default_layout": values.get("graph_default_layout", "brain"),
    }


async def generate_graph_answer(
    config: dict[str, str],
    prompt: str,
    system: str,
    timeout: int = 90,
) -> dict[str, Any]:
    provider = config.get("provider") or "local"
    if provider == "cloud":
        return await _to_thread(_cloud_json, config, prompt, system, timeout)
    return await _to_thread(_ollama_json, config, prompt, system, timeout)


def _cloud_json(
    config: dict[str, str], prompt: str, system: str, timeout: int
) -> dict[str, Any]:
    api_url = config.get("cloud_api_url", "").rstrip("/")
    api_key = config.get("cloud_api_key", "")
    model = config.get("cloud_model", "")
    if not api_url or not api_key or not model:
        raise GraphAIUnavailable("Cloud provider is not configured")
    request = urllib.request.Request(
        f"{api_url}/chat/completions",
        data=json.dumps(
            {
                "model": model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0,
                "max_tokens": 4096,
            }
        ).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))
    raw = payload["choices"][0]["message"]["content"]
    return _loads_json_object(raw)


def _ollama_json(
    config: dict[str, str], prompt: str, system: str, timeout: int
) -> dict[str, Any]:
    base_url = config.get("ollama_base_url", "").rstrip("/")
    model = config.get("ollama_model", "")
    if not base_url or not model:
        raise GraphAIUnavailable("Ollama provider is not configured")
    request = urllib.request.Request(
        f"{base_url}/api/generate",
        data=json.dumps(
            {
                "model": model,
                "prompt": prompt,
                "system": system,
                "stream": False,
                "format": "json",
            }
        ).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))
    raw = payload.get("response", "{}")
    return _loads_json_object(raw)


async def _to_thread(func, *args):
    import asyncio

    return await asyncio.to_thread(func, *args)


def _loads_json_object(raw: str) -> dict[str, Any]:
    raw = _clean_json_text(raw)
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        candidate = _extract_balanced_json_object(raw)
        if not candidate:
            raise
        parsed = json.loads(candidate)
    if not isinstance(parsed, dict):
        raise ValueError("AI response is not a JSON object")
    return parsed


def _clean_json_text(raw: str) -> str:
    text = str(raw or "").strip()
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)
    text = "".join(ch for ch in text if ch >= " " or ch in "\n\r\t")
    text = re.sub(r",(\s*[}\]])", r"\1", text)
    return text.strip()


def _extract_balanced_json_object(text: str) -> str:
    start = text.find("{")
    if start < 0:
        return ""
    depth = 0
    in_string = False
    escape = False
    for index in range(start, len(text)):
        char = text[index]
        if escape:
            escape = False
            continue
        if char == "\\" and in_string:
            escape = True
            continue
        if char == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                candidate = text[start : index + 1]
                return re.sub(r",(\s*[}\]])", r"\1", candidate)
    return ""
