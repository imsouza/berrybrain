from __future__ import annotations

import re
import threading
from collections import defaultdict, deque
from contextvars import ContextVar
from time import time
from typing import Any
from uuid import uuid4

MAX_SAMPLES_PER_ROUTE = 2_048
SAFE_CORRELATION = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")
correlation_id_context: ContextVar[str] = ContextVar("correlation_id", default="")

_lock = threading.Lock()
_samples: dict[tuple[str, str], deque[tuple[float, int, float]]] = defaultdict(
    lambda: deque(maxlen=MAX_SAMPLES_PER_ROUTE)
)


def _percentile(values: list[float], quantile: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * quantile
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def begin_request(headers: dict[str, str]) -> str:
    supplied = headers.get("x-correlation-id", "")
    if supplied and SAFE_CORRELATION.fullmatch(supplied):
        correlation_id = supplied
    else:
        traceparent = headers.get("traceparent", "")
        parts = traceparent.split("-")
        trace_id = parts[1] if len(parts) == 4 and len(parts[1]) == 32 else ""
        correlation_id = trace_id if trace_id.isalnum() else uuid4().hex
    correlation_id_context.set(correlation_id)
    return correlation_id


def record_request(
    method: str,
    route: str,
    status_code: int,
    duration_ms: float,
    *,
    enabled: bool = True,
) -> None:
    if not enabled:
        return
    key = (method.upper()[:8], route[:200] if route.startswith("/") else "unmatched")
    with _lock:
        _samples[key].append((duration_ms, status_code, time()))


def performance_snapshot() -> dict[str, Any]:
    with _lock:
        snapshot = {key: list(values) for key, values in _samples.items()}
    routes = []
    for (method, route), samples in sorted(snapshot.items()):
        durations = [item[0] for item in samples]
        errors = sum(item[1] >= 500 for item in samples)
        routes.append(
            {
                "method": method,
                "route": route,
                "samples": len(samples),
                "errors": errors,
                "errorRate": errors / len(samples),
                "latencyP50Ms": _percentile(durations, 0.50),
                "latencyP95Ms": _percentile(durations, 0.95),
                "latencyP99Ms": _percentile(durations, 0.99),
                "lastMeasuredAtUnix": max(item[2] for item in samples),
            }
        )
    return {
        "schemaVersion": "berrybrain-api-performance.v1",
        "retention": f"last {MAX_SAMPLES_PER_ROUTE} samples per method and route",
        "routes": routes,
    }


def reset_performance_metrics() -> None:
    with _lock:
        _samples.clear()
