from __future__ import annotations

import asyncio
import json
import random
import time

import httpx

from berrybrain_worker.cloud_gateway import CloudError
from berrybrain_worker.config import WorkerSettings
from berrybrain_worker.ollama_gateway import OllamaError

CIRCUIT_FAILURE_THRESHOLD = 3
CIRCUIT_OPEN_SECONDS = 300
_provider_circuit: dict[str, dict[str, float]] = {}


def retry_delay_seconds(retry: int) -> float:
    base = min(30.0, 2.0**retry)
    return base + random.uniform(0.1, 1.0)


def is_permanent_job_error(exc: Exception) -> bool:
    if isinstance(
        exc, (asyncio.TimeoutError, httpx.TimeoutException, httpx.ConnectError)
    ):
        return False
    if isinstance(exc, httpx.HTTPStatusError):
        status = exc.response.status_code
        return status < 500 and status not in {408, 409, 425, 429}
    if isinstance(exc, (CloudError, OllamaError)):
        return False
    return isinstance(exc, ValueError)


def humanize_job_type(job_type: str) -> str:
    labels = {
        "PARSE_NOTE": "note analysis",
        "CLASSIFY_NOTE": "note classification",
        "ASSIMILATE_NOTE": "note assimilation",
        "EXTRACT_CONCEPTS": "concept extraction",
        "EXTRACT_ENTITIES": "entity extraction",
        "DETECT_TOPICS": "topic detection",
        "EXTRACT_CONTEXT": "context extraction",
        "GENERATE_EMBEDDING": "embedding generation",
        "FIND_CONNECTIONS": "connection search",
        "GENERATE_INSIGHTS": "insight generation",
        "GENERATE_GRAPH_INSIGHTS": "graph insight generation",
        "GENERATE_NOTE_TITLE": "automatic title generation",
        "EXPAND_KNOWLEDGE_GRAPH": "knowledge graph expansion",
        "PROCESS_ATTACHMENT": "attachment processing",
        "GENERATE_INFERRED_CONNECTIONS": "inferred connection generation",
        "GENERATE_NODE_SUMMARY": "node summary generation",
        "UPDATE_GRAPH_STATS": "graph statistics update",
        "EXPAND_CONCEPT_TO_NOTE": "permanent note creation",
        "ENRICH_GRAPH_NODE": "AI node enrichment",
        "VALIDATE_GRAPH_NODE_WITH_WEB": "web validation",
        "REASON_GRAPH_CONNECTION": "connection reasoning",
    }
    return labels.get(job_type, job_type.replace("_", " ").lower())


def format_job_failure(job_type: str, exc: Exception, permanent: bool = False) -> str:
    step = humanize_job_type(job_type)
    detail = str(exc).strip()
    lowered = detail.lower()

    if isinstance(exc, (asyncio.TimeoutError, httpx.TimeoutException)):
        return (
            f"{step.capitalize()} timed out. Check the selected AI provider, then retry "
            "the job from Monitor."
        )
    if isinstance(exc, httpx.ConnectError):
        return (
            f"{step.capitalize()} could not reach a required service. Check API/provider "
            "connectivity, then retry from Monitor."
        )
    if isinstance(exc, httpx.HTTPStatusError):
        status = exc.response.status_code
        return (
            f"{step.capitalize()} failed because a service returned HTTP {status}. "
            "Check provider or API availability, then retry from Monitor."
        )
    if isinstance(exc, (CloudError, OllamaError)):
        if "invalid json" in lowered or "json response is not an object" in lowered:
            return (
                f"{step.capitalize()} received an invalid AI response. Retry with the "
                "same model or choose another provider/model in Settings."
            )
        if "empty response" in lowered:
            return (
                f"{step.capitalize()} received an empty AI response. Retry after checking "
                "the configured model/provider."
            )
        if "timeout" in lowered:
            return (
                f"{step.capitalize()} timed out while waiting for the AI provider. "
                "Retry after checking provider health."
            )
        if "http error" in lowered:
            return (
                f"{step.capitalize()} failed at the AI provider. Check the provider "
                "configuration and retry from Monitor."
            )
        return (
            f"{step.capitalize()} could not complete with the configured AI provider. "
            "Check Settings and retry from Monitor."
        )
    if "provider circuit open" in lowered:
        return (
            f"{step.capitalize()} is paused because the provider failed repeatedly. "
            "Wait for the circuit breaker to recover or switch provider in Settings."
        )
    if isinstance(exc, json.JSONDecodeError) or "invalid json" in lowered:
        return (
            f"{step.capitalize()} received malformed JSON. Retry with the same model or "
            "choose another provider/model in Settings."
        )
    if permanent:
        return (
            f"{step.capitalize()} cannot continue because the job data is invalid or no "
            "longer supported. Reprocess the source note if the data changed."
        )
    return f"{step.capitalize()} failed. Review the provider status and retry from Monitor."


def timeout_for_job(settings: WorkerSettings, job_type: str) -> int:
    ai_job_timeout = max(30, settings.ollama_timeout + 30)
    long_running = {
        "ASSIMILATE_NOTE",
        "GENERATE_GRAPH_INSIGHTS",
        "GENERATE_INFERRED_CONNECTIONS",
        "EXPAND_KNOWLEDGE_GRAPH",
        "PROCESS_ATTACHMENT",
    }
    quick = {"UPDATE_GRAPH_STATS", "UPDATE_GRAPH_CLUSTERS"}
    if job_type in long_running:
        return max(ai_job_timeout, 300)
    if job_type in quick:
        return 60
    return ai_job_timeout


def circuit_state(provider: str) -> dict[str, float]:
    return _provider_circuit.setdefault(
        provider, {"failures": 0.0, "opened_until": 0.0}
    )


def assert_provider_available(provider: str) -> None:
    state = circuit_state(provider)
    opened_until = state.get("opened_until", 0.0)
    if opened_until and opened_until > time.time():
        remaining = int(opened_until - time.time())
        message = f"Provider circuit open for {provider}; retry in {remaining}s"
        if provider.startswith("cloud:"):
            raise CloudError(message)
        raise OllamaError(message)


def record_provider_success(provider: str) -> None:
    _provider_circuit[provider] = {"failures": 0.0, "opened_until": 0.0}


def record_provider_failure(provider: str) -> None:
    state = circuit_state(provider)
    failures = state.get("failures", 0.0) + 1
    opened_until = 0.0
    if failures >= CIRCUIT_FAILURE_THRESHOLD:
        opened_until = time.time() + CIRCUIT_OPEN_SECONDS
    _provider_circuit[provider] = {"failures": failures, "opened_until": opened_until}
