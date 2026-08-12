from __future__ import annotations

import argparse
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from benchmarks.evidence import create_manifest, percentile, write_evidence_bundle


@dataclass(frozen=True)
class HttpLoadMetrics:
    requests: int
    concurrency: int
    successes: int
    failures: int
    error_rate: float
    throughput_rps: float
    latency_p50_ms: float
    latency_p95_ms: float
    latency_p99_ms: float
    duration_seconds: float
    status_codes: dict[str, int]


def _request_once(
    request_id: int,
    url: str,
    *,
    timeout_seconds: float,
    headers: dict[str, str],
) -> dict[str, object]:
    started = time.perf_counter()
    status_code = 0
    error = ""
    try:
        request = Request(url, headers=headers, method="GET")
        with urlopen(request, timeout=timeout_seconds) as response:
            status_code = response.status
            response.read()
    except HTTPError as exc:
        status_code = exc.code
        error = f"HTTP {exc.code}"
    except (TimeoutError, URLError, OSError) as exc:
        error = type(exc).__name__
    latency_ms = (time.perf_counter() - started) * 1000
    return {
        "requestId": request_id,
        "statusCode": status_code,
        "success": 200 <= status_code < 400,
        "latencyMs": round(latency_ms, 6),
        "error": error,
    }


def run_http_load(
    base_url: str,
    *,
    path: str = "/status",
    requests: int = 100,
    concurrency: int = 10,
    timeout_seconds: float = 10.0,
    headers: dict[str, str] | None = None,
) -> tuple[HttpLoadMetrics, list[dict[str, object]]]:
    if requests < 1:
        raise ValueError("requests must be at least 1")
    if concurrency < 1:
        raise ValueError("concurrency must be at least 1")
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")

    url = f"{base_url.rstrip('/')}/{path.lstrip('/')}"
    started = time.perf_counter()
    observations: list[dict[str, object]] = []
    with ThreadPoolExecutor(max_workers=min(concurrency, requests)) as pool:
        futures = [
            pool.submit(
                _request_once,
                request_id,
                url,
                timeout_seconds=timeout_seconds,
                headers=headers or {},
            )
            for request_id in range(requests)
        ]
        for future in as_completed(futures):
            observations.append(future.result())
    duration = max(time.perf_counter() - started, 1e-9)
    observations.sort(key=lambda item: int(item["requestId"]))

    latencies = [float(item["latencyMs"]) for item in observations]
    successes = sum(bool(item["success"]) for item in observations)
    status_codes: dict[str, int] = {}
    for item in observations:
        key = str(item["statusCode"])
        status_codes[key] = status_codes.get(key, 0) + 1
    metrics = HttpLoadMetrics(
        requests=requests,
        concurrency=concurrency,
        successes=successes,
        failures=requests - successes,
        error_rate=(requests - successes) / requests,
        throughput_rps=requests / duration,
        latency_p50_ms=percentile(latencies, 0.50),
        latency_p95_ms=percentile(latencies, 0.95),
        latency_p99_ms=percentile(latencies, 0.99),
        duration_seconds=duration,
        status_codes=status_codes,
    )
    return metrics, observations


def write_report(
    output: Path,
    *,
    base_url: str,
    path: str,
    requests: int,
    concurrency: int,
    timeout_seconds: float,
    headers: dict[str, str] | None = None,
    evidence_root: Path | None = None,
) -> HttpLoadMetrics:
    metrics, observations = run_http_load(
        base_url,
        path=path,
        requests=requests,
        concurrency=concurrency,
        timeout_seconds=timeout_seconds,
        headers=headers,
    )
    summary = asdict(metrics)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    if evidence_root is not None:
        configuration = {
            "baseUrl": base_url,
            "path": path,
            "requests": requests,
            "concurrency": concurrency,
            "timeoutSeconds": timeout_seconds,
        }
        manifest = create_manifest(
            "http-load",
            dataset={"method": "GET", "path": path},
            configuration=configuration,
            classification="exploratory",
        )
        write_evidence_bundle(
            evidence_root,
            manifest,
            summary=summary,
            observations=observations,
        )
    return metrics


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Measure concurrent HTTP service load."
    )
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--path", default="/status")
    parser.add_argument("--requests", type=int, default=100)
    parser.add_argument("--concurrency", type=int, default=10)
    parser.add_argument("--timeout-seconds", type=float, default=10.0)
    parser.add_argument("--bearer-token", default="")
    parser.add_argument("--output", default="reports/http-load-benchmark.json")
    parser.add_argument("--evidence-root", default="")
    args = parser.parse_args()
    headers = (
        {"Authorization": f"Bearer {args.bearer_token}"} if args.bearer_token else None
    )
    metrics = write_report(
        Path(args.output),
        base_url=args.base_url,
        path=args.path,
        requests=args.requests,
        concurrency=args.concurrency,
        timeout_seconds=args.timeout_seconds,
        headers=headers,
        evidence_root=Path(args.evidence_root) if args.evidence_root else None,
    )
    print(json.dumps(asdict(metrics), indent=2, sort_keys=True))
    return 0 if metrics.failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
