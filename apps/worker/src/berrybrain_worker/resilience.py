from __future__ import annotations

import asyncio
import json
import random
import re
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


def retry_delay_for_error(retry: int, exc: Exception) -> float:
    delay = retry_delay_seconds(retry)
    if not isinstance(exc, httpx.HTTPStatusError):
        return delay
    raw_retry_after = exc.response.headers.get("Retry-After", "")
    try:
        retry_after = float(raw_retry_after)
    except (TypeError, ValueError):
        return delay
    return max(delay, min(300.0, max(0.0, retry_after)))


def concurrent_job_limit(settings: WorkerSettings, provider: str) -> int:
    configured = (
        settings.cloud_max_concurrent_jobs
        if provider == "cloud"
        else settings.max_concurrent_jobs
    )
    return max(1, min(16, configured))


def is_permanent_job_error(exc: Exception) -> bool:
    if isinstance(
        exc, asyncio.TimeoutError | httpx.TimeoutException | httpx.ConnectError
    ):
        return False
    if isinstance(exc, httpx.HTTPStatusError):
        status = exc.response.status_code
        return status < 500 and status not in {408, 409, 425, 429}
    if isinstance(exc, CloudError | OllamaError):
        if any(
            marker in str(exc).lower()
            for marker in (
                "insufficient quota",
                "insufficient_quota",
                "quota exhausted",
            )
        ):
            return True
        cause = exc.__cause__ or exc.__context__
        if isinstance(cause, httpx.HTTPStatusError):
            return is_permanent_job_error(cause)
        detail = str(exc).lower()
        status = re.search(r"\bhttp(?: error)?[ :]+(\d{3})\b", detail)
        if status:
            code = int(status.group(1))
            return 400 <= code < 500 and code not in {408, 409, 425, 429}
        return any(
            marker in detail
            for marker in (
                "http 400",
                "http 401",
                "http 403",
                "http 404",
                "http 422",
                "invalid api key",
                "unauthorized",
                "does not provide",
                "model not found",
                "model is not available",
                "insufficient quota",
            )
        )
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
        "JUDGE_ARTIFACT": "artifact quality evaluation",
    }
    return labels.get(job_type, job_type.replace("_", " ").lower())


def format_job_failure(job_type: str, exc: Exception, permanent: bool = False) -> str:
    step = humanize_job_type(job_type)
    detail = str(exc).strip()
    lowered = detail.lower()

    if isinstance(exc, asyncio.TimeoutError | httpx.TimeoutException):
        if job_type == "UPDATE_GRAPH_STATS":
            return (
                "Graph statistics update timed out while computing local graph data. "
                "Check API/database load. Eligible jobs can retry through bounded "
                "automatic recovery; review details in Monitor."
            )
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
    if isinstance(exc, CloudError | OllamaError):
        if permanent:
            return (
                f"{step.capitalize()} cannot use the configured AI provider/model. "
                "Check credentials, model availability and quota in Settings. "
                "Automatic retry is disabled for this permanent error."
            )
        cause = exc.__cause__ or exc.__context__
        if isinstance(cause, httpx.HTTPStatusError):
            return format_job_failure(job_type, cause, permanent=permanent)
        status = re.search(r"\bhttp(?: error)?[ :]+(\d{3})\b", lowered)
        if status:
            return (
                f"{step.capitalize()} failed because the AI provider returned HTTP {status.group(1)}. "
                "Review provider availability in Settings; eligible transient failures can retry automatically."
            )
        if "provider circuit open" in lowered:
            return (
                f"{step.capitalize()} is paused by the provider circuit breaker after repeated failures. "
                "Wait for bounded recovery or review the provider in Settings."
            )
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
    if job_type == "EXPAND_KNOWLEDGE_GRAPH":
        # Expand (120s), enrichment admission (60s), HippoRAG sync (120s),
        # plus context and completion. Never inherit the client's 10s default.
        return max(ai_job_timeout, 330)
    if job_type == "GENERATE_NODE_SUMMARY":
        return max(ai_job_timeout, 150)
    long_running = {
        "ASSIMILATE_NOTE",
        "GENERATE_GRAPH_INSIGHTS",
        "GENERATE_INFERRED_CONNECTIONS",
        "EXPAND_KNOWLEDGE_GRAPH",
        "PROCESS_ATTACHMENT",
    }
    if job_type in long_running:
        return max(ai_job_timeout, 300)
    if job_type == "UPDATE_GRAPH_CLUSTERS":
        # Reclustering performs a preview and a guarded apply. Both are CPU-bound
        # and can exceed a minute on the low-cost hardware BerryBrain supports.
        return 660
    if job_type == "UPDATE_GRAPH_STATS":
        return 120
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
