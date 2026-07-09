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
    import json

    if not raw or not raw.strip():
        raise CloudError("Cloud returned empty response")
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        trimmed = raw.strip()
        # Fix truncated arrays
        open_braces = trimmed.count("{") - trimmed.count("}")
        open_brackets = trimmed.count("[") - trimmed.count("]")
        if open_brackets > 0:
            trimmed += "]" * open_brackets
        if open_braces > 0:
            trimmed += "}" * open_braces
        # Fix truncated strings
        in_string = False
        for i, c in enumerate(trimmed):
            if c == '"' and (i == 0 or trimmed[i - 1] != "\\"):
                in_string = not in_string
        if in_string:
            trimmed += '"'
        try:
            return json.loads(trimmed)
        except json.JSONDecodeError:
            raise CloudError(
                f"Cloud returned invalid JSON (len={len(raw)}): {raw[:200]}"
            )


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
