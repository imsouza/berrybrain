import json
import re

import httpx


class CloudError(Exception):
    pass


async def cloud_generate(
    api_url: str,
    api_key: str,
    model: str,
    prompt: str,
    system: str | None = None,
    timeout: int = 120,
    json_mode: bool = False,
) -> str:
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    body: dict = {
        "model": model,
        "messages": messages,
        "max_tokens": 8192,
        "temperature": 0.1,
    }
    if json_mode:
        body["response_format"] = {"type": "json_object"}

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                f"{api_url}/chat/completions",
                json=body,
                headers={"Authorization": f"Bearer {api_key}"},
            )
            response.raise_for_status()
            data = response.json()
            msg = data["choices"][0]["message"]
            content = msg.get("content") or ""
            reasoning = msg.get("reasoning_content") or ""
            if not content and reasoning:
                content = reasoning
            return content
    except httpx.TimeoutException:
        raise CloudError(f"Cloud timeout after {timeout}s")
    except httpx.HTTPError as e:
        raise CloudError(f"Cloud HTTP error: {e}")
    except Exception as e:
        raise CloudError(f"Cloud error: {e}")


async def cloud_generate_json(
    api_url: str,
    api_key: str,
    model: str,
    prompt: str,
    system: str | None = None,
    timeout: int = 120,
) -> dict:
    raw = await cloud_generate(
        api_url, api_key, model, prompt, system, timeout, json_mode=True
    )
    if not raw or not raw.strip():
        raise CloudError("Cloud returned empty response")
    try:
        return json.loads(_clean_json_text(raw))
    except json.JSONDecodeError:
        candidate = _extract_balanced_json_object(raw)
        if not candidate:
            raise CloudError(
                f"Cloud returned invalid JSON (len={len(raw)}): {raw[:200]}"
            )
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            raise CloudError(
                f"Cloud returned invalid JSON (len={len(raw)}): {raw[:200]}"
            )
        if not isinstance(parsed, dict):
            raise CloudError("Cloud JSON response is not an object")
        return parsed


def _clean_json_text(raw: str) -> str:
    text = str(raw or "").strip()
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)
    text = "".join(ch for ch in text if ch >= " " or ch in "\n\r\t")
    return re.sub(r",(\s*[}\]])", r"\1", text).strip()


def _extract_balanced_json_object(raw: str) -> str:
    text = _clean_json_text(raw)
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
                return re.sub(r",(\s*[}\]])", r"\1", text[start : index + 1])
    return ""


async def cloud_generate_embedding(
    api_url: str,
    api_key: str,
    model: str,
    text: str,
    timeout: int = 120,
) -> list[float]:
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                f"{api_url}/embeddings",
                json={"model": model, "input": text},
                headers={"Authorization": f"Bearer {api_key}"},
            )
            response.raise_for_status()
            return response.json()["data"][0]["embedding"]
    except httpx.TimeoutException:
        raise CloudError(f"Cloud embedding timeout after {timeout}s")
    except httpx.HTTPError as e:
        raise CloudError(f"Cloud embedding HTTP error: {e}")
    except Exception as e:
        raise CloudError(f"Cloud embedding error: {e}")
