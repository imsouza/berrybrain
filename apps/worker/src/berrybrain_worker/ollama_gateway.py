import time

import httpx


class OllamaError(Exception):
    pass


async def check_health(ollama_base_url: str, timeout: float = 10) -> bool:
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(f"{ollama_base_url}/api/tags")
            return response.status_code == 200
    except Exception:
        return False


async def generate(
    ollama_base_url: str,
    model: str,
    prompt: str,
    system: str | None = None,
    ollama_timeout: int = 120,
) -> str:
    payload: dict = {"model": model, "prompt": prompt, "stream": False}
    if system:
        payload["system"] = system

    try:
        async with httpx.AsyncClient(timeout=ollama_timeout) as client:
            response = await client.post(
                f"{ollama_base_url}/api/generate",
                json=payload,
            )
            response.raise_for_status()
            return response.json()["response"]
    except httpx.TimeoutException:
        raise OllamaError(f"Ollama timeout after {ollama_timeout}s")
    except httpx.HTTPError as e:
        raise OllamaError(f"Ollama HTTP error: {e}")
    except Exception as e:
        raise OllamaError(f"Ollama error: {e}")


async def generate_json(
    ollama_base_url: str,
    model: str,
    prompt: str,
    system: str | None = None,
    ollama_timeout: int = 120,
) -> dict:
    payload: dict = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "format": "json",
    }
    if system:
        payload["system"] = system

    try:
        async with httpx.AsyncClient(timeout=ollama_timeout) as client:
            response = await client.post(
                f"{ollama_base_url}/api/generate",
                json=payload,
            )
            response.raise_for_status()
            return response.json()["response"]
    except httpx.TimeoutException:
        raise OllamaError(f"Ollama timeout after {ollama_timeout}s")
    except httpx.HTTPError as e:
        raise OllamaError(f"Ollama HTTP error: {e}")
    except Exception as e:
        raise OllamaError(f"Ollama error: {e}")


async def generate_embedding(
    ollama_base_url: str,
    model: str,
    text: str,
    ollama_timeout: int = 120,
) -> list[float]:
    payload = {"model": model, "input": text}
    try:
        async with httpx.AsyncClient(timeout=ollama_timeout) as client:
            response = await client.post(
                f"{ollama_base_url}/api/embed",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            if "embeddings" in data and len(data["embeddings"]) > 0:
                return data["embeddings"][0]
            return data.get("embedding", [])
    except httpx.TimeoutException:
        raise OllamaError(f"Ollama embedding timeout after {ollama_timeout}s")
    except httpx.HTTPError as e:
        raise OllamaError(f"Ollama embedding HTTP error: {e}")
    except Exception as e:
        raise OllamaError(f"Ollama embedding error: {e}")


async def log_ai_call(
    api_client: httpx.AsyncClient,
    api_url: str,
    model: str,
    prompt: str,
    response_text: str,
    duration_ms: float,
    target_type: str = "system",
    target_id: str = "worker",
) -> None:
    try:
        await api_client.post(
            f"{api_url}/api/v1/automation-logs",
            json={
                "action_type": "OLLAMA_GENERATE",
                "target_type": target_type,
                "target_id": target_id,
                "description": f"Ollama call: {model}",
                "before_state": {
                    "model": model,
                    "prompt_length": len(prompt),
                },
                "after_state": {
                    "response_length": len(response_text),
                    "duration_ms": duration_ms,
                },
                "reversible": False,
            },
        )
    except Exception:
        pass
