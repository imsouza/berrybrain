from __future__ import annotations

import argparse
import gc
import json
import statistics
import tempfile
import time
import tracemalloc
from dataclasses import asdict, dataclass
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

import berrybrain_api.models  # noqa: F401
from benchmarks.evidence import create_manifest, write_evidence_bundle
from berrybrain_api.database import Base
from berrybrain_api.models import GraphEdgeRecord, GraphNodeRecord
from berrybrain_api.services import build_graph


@dataclass(frozen=True)
class GraphPerformanceMetrics:
    node_count: int
    edge_count: int
    sample_count: int
    latency_p50_ms: float
    latency_p95_ms: float
    payload_bytes: int
    peak_memory_bytes: int
    p95_budget_ms: float
    payload_budget_bytes: int
    memory_budget_bytes: int
    latency_samples_ms: tuple[float, ...]
    meets_targets: bool


def run_benchmark(
    *,
    node_count: int = 5_000,
    edge_count: int = 20_000,
    sample_count: int = 7,
    p95_budget_ms: float = 5_000,
    payload_budget_bytes: int = 16 * 1024 * 1024,
    memory_budget_bytes: int = 512 * 1024 * 1024,
    database_url: str = "sqlite:///:memory:",
) -> GraphPerformanceMetrics:
    if node_count < 2 or edge_count < 1 or sample_count < 2:
        raise ValueError("Graph benchmark requires nodes, edges, and multiple samples")

    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False)
    try:
        with session_factory() as session:
            session.bulk_save_objects(
                [
                    GraphNodeRecord(
                        type="note" if index % 4 == 0 else "concept",
                        label=f"Benchmark node {index}",
                        title=f"Benchmark node {index}",
                        summary=f"Grounded benchmark summary {index}",
                        source="benchmark",
                        source_id=index + 1,
                        source_note_ids=json.dumps([index // 4 + 1]),
                        source_evidence=f"benchmark-evidence:{index}",
                        confidence=0.9,
                        created_by="system",
                        status="confirmed",
                    )
                    for index in range(node_count)
                ]
            )
            session.commit()
            node_ids = list(
                session.execute(
                    select(GraphNodeRecord.id).order_by(GraphNodeRecord.id)
                ).scalars()
            )
            edges = []
            for index in range(edge_count):
                source_index = index % node_count
                offset = 1 + ((index * 17) % (node_count - 1))
                target_index = (source_index + offset) % node_count
                edges.append(
                    GraphEdgeRecord(
                        source_node_id=node_ids[source_index],
                        target_node_id=node_ids[target_index],
                        type="semantic_similarity",
                        label="benchmark relation",
                        confidence=0.85,
                        reason="Deterministic evidence-backed benchmark relation.",
                        evidence=json.dumps([f"benchmark-edge:{index}"]),
                        source_note_ids=json.dumps(
                            [source_index // 4 + 1, target_index // 4 + 1]
                        ),
                        created_by="system",
                        provider="benchmark",
                        model="deterministic.v1",
                        prompt_version="graph-performance.v1",
                        status="confirmed",
                    )
                )
            session.bulk_save_objects(edges)
            session.commit()

            build_graph(session)
            gc.collect()
            tracemalloc.start()
            memory_payload = build_graph(session)
            json.dumps(
                memory_payload, ensure_ascii=False, separators=(",", ":")
            ).encode("utf-8")
            _, peak_memory_bytes = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            del memory_payload
            gc.collect()
            latencies = []
            payload_bytes = 0
            gc_was_enabled = gc.isenabled()
            gc.disable()
            try:
                for _ in range(sample_count):
                    started = time.perf_counter()
                    payload = build_graph(session)
                    encoded = json.dumps(
                        payload, ensure_ascii=False, separators=(",", ":")
                    ).encode("utf-8")
                    latencies.append((time.perf_counter() - started) * 1000)
                    payload_bytes = max(payload_bytes, len(encoded))
            finally:
                if gc_was_enabled:
                    gc.enable()

            measured_nodes = int(payload["stats"]["node_count"])
            measured_edges = int(payload["stats"]["edge_count"])
    finally:
        engine.dispose()

    latency_p95 = _percentile(latencies, 0.95)
    return GraphPerformanceMetrics(
        node_count=measured_nodes,
        edge_count=measured_edges,
        sample_count=sample_count,
        latency_p50_ms=statistics.median(latencies),
        latency_p95_ms=latency_p95,
        payload_bytes=payload_bytes,
        peak_memory_bytes=peak_memory_bytes,
        p95_budget_ms=p95_budget_ms,
        payload_budget_bytes=payload_budget_bytes,
        memory_budget_bytes=memory_budget_bytes,
        latency_samples_ms=tuple(latencies),
        meets_targets=(
            measured_nodes == node_count
            and measured_edges == edge_count
            and payload_bytes <= payload_budget_bytes
            and peak_memory_bytes <= memory_budget_bytes
        ),
    )


def _percentile(values: list[float], percentile: float) -> float:
    ordered = sorted(values)
    rank = max(0, min(len(ordered) - 1, round((len(ordered) - 1) * percentile)))
    return ordered[rank]


def write_report(
    output: Path,
    *,
    node_count: int,
    edge_count: int,
    sample_count: int,
    on_disk: bool,
    evidence_root: Path | None = None,
) -> GraphPerformanceMetrics:
    temporary_directory: tempfile.TemporaryDirectory[str] | None = None
    database_url = "sqlite:///:memory:"
    if on_disk:
        temporary_directory = tempfile.TemporaryDirectory(
            prefix="berrybrain-graph-benchmark-"
        )
        database_url = f"sqlite:///{Path(temporary_directory.name) / 'graph.db'}"
    try:
        result = run_benchmark(
            node_count=node_count,
            edge_count=edge_count,
            sample_count=sample_count,
            database_url=database_url,
        )
        summary = asdict(result)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
        if evidence_root is not None:
            manifest = create_manifest(
                "graph-performance",
                dataset={"nodes": node_count, "edges": edge_count},
                configuration={
                    "sampleCount": sample_count,
                    "storage": "on-disk SQLite" if on_disk else "in-memory SQLite",
                },
                classification="exploratory" if on_disk else "ci-regression",
            )
            observations = [
                {"sample": index, "latencyMs": latency}
                for index, latency in enumerate(result.latency_samples_ms, 1)
            ]
            write_evidence_bundle(
                evidence_root, manifest, summary=summary, observations=observations
            )
        return result
    finally:
        if temporary_directory is not None:
            temporary_directory.cleanup()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Measure graph projection performance."
    )
    parser.add_argument("--nodes", type=int, default=5_000)
    parser.add_argument("--edges", type=int, default=20_000)
    parser.add_argument("--samples", type=int, default=7)
    parser.add_argument("--on-disk", action="store_true")
    parser.add_argument("--output", default="reports/graph-performance.json")
    parser.add_argument("--evidence-root", default="")
    args = parser.parse_args()
    result = write_report(
        Path(args.output),
        node_count=args.nodes,
        edge_count=args.edges,
        sample_count=args.samples,
        on_disk=args.on_disk,
        evidence_root=Path(args.evidence_root) if args.evidence_root else None,
    )
    print(json.dumps(asdict(result), indent=2, sort_keys=True))
    return 0 if result.meets_targets else 1


if __name__ == "__main__":
    raise SystemExit(main())
