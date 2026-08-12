from __future__ import annotations

import argparse
import json
import tempfile
import time
from dataclasses import asdict, dataclass
from pathlib import Path

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker

import berrybrain_api.models  # noqa: F401
from benchmarks.evidence import create_manifest, percentile, write_evidence_bundle
from berrybrain_api.database import Base
from berrybrain_api.jobs import (
    GENERATE_INSIGHTS,
    claim_next_job,
    complete_job,
    create_job,
)
from berrybrain_api.models import JobRecord


@dataclass(frozen=True)
class WorkerQueueMetrics:
    jobs: int
    enqueue_rate_jobs_per_second: float
    drain_rate_jobs_per_second: float
    end_to_end_p50_ms: float
    end_to_end_p95_ms: float
    end_to_end_p99_ms: float
    claim_p95_ms: float
    duplicate_claims: int
    completed_jobs: int
    remaining_jobs: int


def run_worker_queue_benchmark(
    *,
    jobs: int = 100,
    database_path: Path | None = None,
) -> tuple[WorkerQueueMetrics, list[dict[str, object]]]:
    if jobs < 1:
        raise ValueError("jobs must be at least 1")

    temporary_directory: tempfile.TemporaryDirectory[str] | None = None
    if database_path is None:
        temporary_directory = tempfile.TemporaryDirectory(
            prefix="berrybrain-worker-benchmark-"
        )
        database_path = Path(temporary_directory.name) / "queue.db"
    engine = create_engine(f"sqlite:///{database_path}")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    enqueued_at: dict[int, float] = {}
    observations: list[dict[str, object]] = []

    enqueue_started = time.perf_counter()
    with session_factory() as session:
        for index in range(jobs):
            job = create_job(
                session,
                GENERATE_INSIGHTS,
                {"idempotency_key": f"worker-benchmark:{index}"},
            )
            enqueued_at[job.id] = time.perf_counter()
    enqueue_duration = max(time.perf_counter() - enqueue_started, 1e-9)

    claimed_ids: set[int] = set()
    duplicate_claims = 0
    drain_started = time.perf_counter()
    with session_factory() as session:
        while len(claimed_ids) < jobs:
            claim_started = time.perf_counter()
            job = claim_next_job(session, claimed_by="benchmark-worker")
            claim_latency_ms = (time.perf_counter() - claim_started) * 1000
            if job is None:
                break
            if job.id in claimed_ids:
                duplicate_claims += 1
            claimed_ids.add(job.id)
            claim_token = job.claim_token
            complete_job(session, job.id, claim_token)
            observations.append(
                {
                    "jobId": job.id,
                    "claimLatencyMs": round(claim_latency_ms, 6),
                    "endToEndLatencyMs": round(
                        (time.perf_counter() - enqueued_at[job.id]) * 1000, 6
                    ),
                    "status": "completed",
                }
            )
        completed = int(
            session.scalar(
                select(func.count(JobRecord.id)).where(JobRecord.status == "completed")
            )
            or 0
        )
        remaining = int(
            session.scalar(
                select(func.count(JobRecord.id)).where(JobRecord.status != "completed")
            )
            or 0
        )
    drain_duration = max(time.perf_counter() - drain_started, 1e-9)
    engine.dispose()
    if temporary_directory is not None:
        temporary_directory.cleanup()

    end_to_end = [float(item["endToEndLatencyMs"]) for item in observations]
    claim_latencies = [float(item["claimLatencyMs"]) for item in observations]
    metrics = WorkerQueueMetrics(
        jobs=jobs,
        enqueue_rate_jobs_per_second=jobs / enqueue_duration,
        drain_rate_jobs_per_second=completed / drain_duration,
        end_to_end_p50_ms=percentile(end_to_end, 0.50),
        end_to_end_p95_ms=percentile(end_to_end, 0.95),
        end_to_end_p99_ms=percentile(end_to_end, 0.99),
        claim_p95_ms=percentile(claim_latencies, 0.95),
        duplicate_claims=duplicate_claims,
        completed_jobs=completed,
        remaining_jobs=remaining,
    )
    return metrics, observations


def write_report(
    output: Path,
    *,
    jobs: int,
    database_path: Path | None = None,
    evidence_root: Path | None = None,
) -> WorkerQueueMetrics:
    metrics, observations = run_worker_queue_benchmark(
        jobs=jobs, database_path=database_path
    )
    summary = asdict(metrics)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    if evidence_root is not None:
        manifest = create_manifest(
            "worker-queue",
            dataset={"syntheticJobCount": jobs, "containsUserContent": False},
            configuration={"jobs": jobs, "database": "isolated SQLite"},
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
        description="Measure the production job queue path."
    )
    parser.add_argument("--jobs", type=int, default=100)
    parser.add_argument("--database-path", default="")
    parser.add_argument("--output", default="reports/worker-queue-benchmark.json")
    parser.add_argument("--evidence-root", default="")
    args = parser.parse_args()
    metrics = write_report(
        Path(args.output),
        jobs=args.jobs,
        database_path=Path(args.database_path) if args.database_path else None,
        evidence_root=Path(args.evidence_root) if args.evidence_root else None,
    )
    print(json.dumps(asdict(metrics), indent=2, sort_keys=True))
    return 0 if metrics.remaining_jobs == 0 and metrics.duplicate_claims == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
