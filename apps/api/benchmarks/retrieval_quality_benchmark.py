from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

import berrybrain_api.models  # noqa: F401
from benchmarks.evidence import (
    create_manifest,
    paired_bootstrap_difference,
    percentile,
    write_evidence_bundle,
)
from berrybrain_api.database import Base
from berrybrain_api.models import ConnectionRecord, NoteRecord
from berrybrain_api.search import chunk_search, hybrid_search, init_fts, text_search
from berrybrain_api.services import find_similar_chunks_by_vector, store_embedding


@dataclass(frozen=True)
class RetrievalCase:
    case_id: str
    kind: str
    query: str
    expected_paths: tuple[str, ...]
    query_vector: tuple[float, ...] | None


@dataclass(frozen=True)
class AblationMetrics:
    configuration: str
    query_count: int
    recall_at_10: float
    mean_reciprocal_rank: float
    ndcg_at_10: float
    negative_rejection_rate: float
    latency_p50_ms: float
    latency_p95_ms: float
    latency_p99_ms: float
    failures: int


@dataclass(frozen=True)
class RetrievalBenchmarkMetrics:
    dataset_version: str
    query_count: int
    multi_hop_query_count: int
    factual_query_count: int
    negative_query_count: int
    standard_multi_hop_recall: float
    graph_multi_hop_recall: float
    multi_hop_recall_gain: float
    multi_hop_gain_ci95: dict[str, Any]
    standard_factual_recall: float
    graph_factual_recall: float
    factual_recall_regression: float
    citation_precision: float
    evidence_faithfulness: float
    negative_rejection_rate: float
    ignored_edge_rejected: bool
    stale_deleted_rejected: bool
    ablations: tuple[AblationMetrics, ...]
    observations: tuple[dict[str, Any], ...]
    gates_passed: bool


DATASET_VERSION = "retrieval-ablation.v1"
CHAIN_COUNT = 20
NEGATIVE_QUERIES = (
    "coral spawning thermocline",
    "renaissance pigment varnish",
    "lunar volcanic mineralogy",
    "baroque counterpoint quartet",
)


def _vector(index: int, dimensions: int = 64) -> tuple[float, ...]:
    vector = [0.0] * dimensions
    vector[index % dimensions] = 1.0
    return tuple(vector)


def _content_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _add_note(session: Session, *, path: str, title: str, content: str) -> NoteRecord:
    note = NoteRecord(
        path=path,
        slug=path.removesuffix(".md").replace("/", "-"),
        title=title,
        content=content,
        content_hash=_content_hash(content),
        status="assimilated",
        language="en",
    )
    session.add(note)
    session.flush()
    return note


def build_retrieval_fixture() -> tuple[Session, list[RetrievalCase], dict[str, Any]]:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False)()
    init_fts(session)
    cases: list[RetrievalCase] = []
    paths: list[str] = []

    for index in range(CHAIN_COUNT):
        number = index + 1
        marker = f"gatewaytoken{number:02d}"
        answer = f"resolutiontoken{number:02d}"
        source_path = f"benchmark/source-{number:02d}.md"
        target_path = f"benchmark/target-{number:02d}.md"
        source = _add_note(
            session,
            path=source_path,
            title=f"Gateway Evidence {number:02d}",
            content=(
                f"# Gateway Evidence {number:02d}\n\n"
                f"The diagnostic entry point is {marker}. Follow its confirmed dependency "
                "to locate the independent resolution evidence."
            ),
        )
        target = _add_note(
            session,
            path=target_path,
            title=f"Independent Resolution {number:02d}",
            content=(
                f"# Independent Resolution {number:02d}\n\n"
                f"The verified outcome is {answer}. This note deliberately omits the gateway "
                "query vocabulary and is reachable through the recorded relationship."
            ),
        )
        source_vector = _vector(index)
        target_vector = _vector(CHAIN_COUNT + index)
        for note, vector in ((source, source_vector), (target, target_vector)):
            store_embedding(
                session,
                note_id=note.id,
                content_hash=note.content_hash,
                vector=list(vector),
                model="benchmark-vector-v1",
                provider="deterministic-fixture",
                chunk_index=0,
                chunk_text=note.content,
                heading_path=note.title,
                start_line=1,
                end_line=3,
                token_count=len(note.content.split()),
            )
        session.add(
            ConnectionRecord(
                source_note_id=source.id,
                target_note_id=target.id,
                connection_type="prerequisite_for",
                confidence=95,
                reason=f"{source.title} is the documented entry point for {target.title}.",
                evidence=json.dumps([source_path, target_path]),
                created_by="benchmark",
                provider="deterministic-fixture",
                model="benchmark-graph-v1",
                status="confirmed",
            )
        )
        cases.extend(
            [
                RetrievalCase(
                    f"multi-hop-{number:02d}",
                    "multi_hop",
                    marker,
                    (target_path,),
                    source_vector,
                ),
                RetrievalCase(
                    f"factual-{number:02d}",
                    "factual",
                    f"What evidence contains {answer}?",
                    (target_path,),
                    target_vector,
                ),
            ]
        )
        paths.extend([source_path, target_path])

    ignored_target = _add_note(
        session,
        path="benchmark/ignored-target.md",
        title="Ignored Contradictory Target",
        content="This isolated note contains ignoredcontradictiontoken only.",
    )
    first_source = (
        session.query(NoteRecord).filter_by(path="benchmark/source-01.md").one()
    )
    session.add(
        ConnectionRecord(
            source_note_id=first_source.id,
            target_note_id=ignored_target.id,
            connection_type="contradicts",
            confidence=90,
            reason="This benchmark edge is intentionally ignored.",
            evidence=json.dumps([first_source.path, ignored_target.path]),
            created_by="benchmark",
            provider="deterministic-fixture",
            model="benchmark-graph-v1",
            status="ignored",
        )
    )
    for index, query in enumerate(NEGATIVE_QUERIES, start=1):
        cases.append(
            RetrievalCase(f"negative-{index:02d}", "negative", query, (), None)
        )
    session.commit()
    dataset = {
        "version": DATASET_VERSION,
        "chainCount": CHAIN_COUNT,
        "paths": paths,
        "cases": [
            {
                "id": case.case_id,
                "kind": case.kind,
                "query": case.query,
                "expected": list(case.expected_paths),
            }
            for case in cases
        ],
    }
    return session, cases, dataset


def _rank_fusion(candidates: list[list[dict]], limit: int = 10) -> list[dict]:
    scores: dict[int, float] = {}
    records: dict[int, dict] = {}
    for rows in candidates:
        for rank, item in enumerate(rows, start=1):
            note_id = int(item["id"])
            scores[note_id] = scores.get(note_id, 0.0) + 1.0 / (60 + rank)
            records.setdefault(note_id, item)
    ranked = sorted(scores, key=scores.get, reverse=True)[:limit]
    return [{**records[note_id], "evidence": []} for note_id in ranked]


def _lexical_retrieve(
    session: Session, case: RetrievalCase, limit: int = 10
) -> list[dict]:
    return _rank_fusion(
        [
            text_search(session, case.query, limit=50),
            chunk_search(session, case.query, limit=50),
        ],
        limit,
    )


def _dense_retrieve(
    session: Session, case: RetrievalCase, limit: int = 10
) -> list[dict]:
    if case.query_vector is None:
        return []
    return _rank_fusion(
        [find_similar_chunks_by_vector(session, list(case.query_vector), limit=50)],
        limit,
    )


def _standard_retrieve(
    session: Session, case: RetrievalCase, limit: int = 10
) -> list[dict]:
    candidates = [
        text_search(session, case.query, limit=50),
        chunk_search(session, case.query, limit=50),
    ]
    if case.query_vector is not None:
        candidates.append(
            find_similar_chunks_by_vector(session, list(case.query_vector), limit=50)
        )
    return _rank_fusion(candidates, limit)


def _recall(paths: list[str], expected: tuple[str, ...], limit: int = 10) -> float:
    if not expected:
        return float(not paths)
    return len(set(paths[:limit]) & set(expected)) / len(expected)


def _reciprocal_rank(paths: list[str], expected: tuple[str, ...]) -> float:
    for rank, path in enumerate(paths, start=1):
        if path in expected:
            return 1.0 / rank
    return 0.0


def _ndcg(paths: list[str], expected: tuple[str, ...], limit: int = 10) -> float:
    expected_set = set(expected)
    dcg = sum(
        1 / math.log2(rank + 1)
        for rank, path in enumerate(paths[:limit], start=1)
        if path in expected_set
    )
    ideal = sum(
        1 / math.log2(rank + 1) for rank in range(1, min(limit, len(expected_set)) + 1)
    )
    return dcg / ideal if ideal else float(not paths)


def _evaluate_configuration(
    session: Session,
    cases: list[RetrievalCase],
    configuration: str,
) -> tuple[AblationMetrics, list[dict[str, Any]]]:
    observations: list[dict[str, Any]] = []
    for case in cases:
        started = time.perf_counter()
        error: str | None = None
        try:
            if configuration == "lexical_only":
                results = _lexical_retrieve(session, case)
            elif configuration == "dense_only":
                results = _dense_retrieve(session, case)
            elif configuration == "standard_hybrid":
                results = _standard_retrieve(session, case)
            elif configuration == "graph_lexical":
                results = hybrid_search(session, case.query, limit=10)
            elif configuration == "graph_hybrid":
                results = hybrid_search(
                    session,
                    case.query,
                    limit=10,
                    query_vector=list(case.query_vector) if case.query_vector else None,
                )
            else:
                raise ValueError(
                    f"unsupported retrieval configuration: {configuration}"
                )
        except Exception as exc:  # pragma: no cover - retained as benchmark observation
            results = []
            error = type(exc).__name__
        latency = (time.perf_counter() - started) * 1000
        paths = [str(item["path"]) for item in results]
        observations.append(
            {
                "benchmark": "retrieval-quality",
                "caseId": case.case_id,
                "kind": case.kind,
                "configuration": configuration,
                "success": error is None,
                "latencyMs": round(latency, 6),
                "paths": paths,
                "expectedPaths": list(case.expected_paths),
                "recallAt10": _recall(paths, case.expected_paths),
                "reciprocalRank": _reciprocal_rank(paths, case.expected_paths),
                "ndcgAt10": _ndcg(paths, case.expected_paths),
                "supportedExpected": sum(
                    1
                    for item in results
                    if item["path"] in case.expected_paths and item.get("evidence")
                ),
                "errorClass": error,
            }
        )
    positive = [row for row in observations if row["kind"] != "negative"]
    negatives = [row for row in observations if row["kind"] == "negative"]
    latencies = [float(row["latencyMs"]) for row in observations]
    return (
        AblationMetrics(
            configuration=configuration,
            query_count=len(observations),
            recall_at_10=round(
                statistics.fmean(row["recallAt10"] for row in positive), 6
            ),
            mean_reciprocal_rank=round(
                statistics.fmean(row["reciprocalRank"] for row in positive), 6
            ),
            ndcg_at_10=round(statistics.fmean(row["ndcgAt10"] for row in positive), 6),
            negative_rejection_rate=round(
                statistics.fmean(row["recallAt10"] for row in negatives), 6
            ),
            latency_p50_ms=round(percentile(latencies, 0.50), 6),
            latency_p95_ms=round(percentile(latencies, 0.95), 6),
            latency_p99_ms=round(percentile(latencies, 0.99), 6),
            failures=sum(not row["success"] for row in observations),
        ),
        observations,
    )


def run_benchmark() -> RetrievalBenchmarkMetrics:
    session, cases, _dataset = build_retrieval_fixture()
    try:
        evaluated = {
            configuration: _evaluate_configuration(session, cases, configuration)
            for configuration in (
                "lexical_only",
                "dense_only",
                "standard_hybrid",
                "graph_lexical",
                "graph_hybrid",
            )
        }
        standard, standard_rows = evaluated["standard_hybrid"]
        graph, graph_rows = evaluated["graph_hybrid"]
        standard_by_id = {row["caseId"]: row for row in standard_rows}
        graph_by_id = {row["caseId"]: row for row in graph_rows}
        multi_hop = [case for case in cases if case.kind == "multi_hop"]
        factual = [case for case in cases if case.kind == "factual"]
        negatives = [case for case in cases if case.kind == "negative"]
        standard_multi = [
            standard_by_id[case.case_id]["recallAt10"] for case in multi_hop
        ]
        graph_multi = [graph_by_id[case.case_id]["recallAt10"] for case in multi_hop]
        standard_factual = [
            standard_by_id[case.case_id]["recallAt10"] for case in factual
        ]
        graph_factual = [graph_by_id[case.case_id]["recallAt10"] for case in factual]
        gain_ci = paired_bootstrap_difference(graph_multi, standard_multi)
        cited_expected = sum(
            int(graph_by_id[case.case_id]["recallAt10"] > 0) for case in multi_hop
        )
        supported_expected = sum(
            int(graph_by_id[case.case_id]["supportedExpected"] > 0)
            for case in multi_hop
        )

        ignored_probe = RetrievalCase(
            "ignored-edge-probe",
            "negative",
            "gatewaytoken01",
            (),
            _vector(0),
        )
        ignored_paths = {
            item["path"]
            for item in hybrid_search(
                session,
                ignored_probe.query,
                limit=10,
                query_vector=list(ignored_probe.query_vector or ()),
            )
        }
        stale = _add_note(
            session,
            path="benchmark/stale-deleted.md",
            title="Stale Deleted Evidence",
            content="The unique stale deletion probe is staledeletiontoken.",
        )
        session.commit()
        stale_id = stale.id
        session.delete(stale)
        session.commit()
        stale_paths = {
            item["path"]
            for item in hybrid_search(session, "staledeletiontoken", limit=10)
        }
        stale_deleted = (
            session.get(NoteRecord, stale_id) is None
            and "benchmark/stale-deleted.md" not in stale_paths
        )

        standard_multi_recall = statistics.fmean(standard_multi)
        graph_multi_recall = statistics.fmean(graph_multi)
        standard_factual_recall = statistics.fmean(standard_factual)
        graph_factual_recall = statistics.fmean(graph_factual)
        negative_rejection = statistics.fmean(
            graph_by_id[case.case_id]["recallAt10"] for case in negatives
        )
        citation_precision = supported_expected / max(1, cited_expected)
        factual_regression = max(0.0, standard_factual_recall - graph_factual_recall)
        ignored_rejected = "benchmark/ignored-target.md" not in ignored_paths
        gates_passed = (
            graph_multi_recall - standard_multi_recall >= 0.10
            and gain_ci.lower > 0
            and factual_regression <= 0.02
            and citation_precision >= 0.95
            and negative_rejection == 1.0
            and ignored_rejected
            and stale_deleted
            and standard.failures == 0
            and graph.failures == 0
        )
        return RetrievalBenchmarkMetrics(
            dataset_version=DATASET_VERSION,
            query_count=len(cases),
            multi_hop_query_count=len(multi_hop),
            factual_query_count=len(factual),
            negative_query_count=len(negatives),
            standard_multi_hop_recall=round(standard_multi_recall, 6),
            graph_multi_hop_recall=round(graph_multi_recall, 6),
            multi_hop_recall_gain=round(graph_multi_recall - standard_multi_recall, 6),
            multi_hop_gain_ci95=asdict(gain_ci),
            standard_factual_recall=round(standard_factual_recall, 6),
            graph_factual_recall=round(graph_factual_recall, 6),
            factual_recall_regression=round(factual_regression, 6),
            citation_precision=round(citation_precision, 6),
            evidence_faithfulness=round(citation_precision, 6),
            negative_rejection_rate=round(negative_rejection, 6),
            ignored_edge_rejected=ignored_rejected,
            stale_deleted_rejected=stale_deleted,
            ablations=tuple(metrics for metrics, _rows in evaluated.values()),
            observations=tuple(
                row for _metrics, rows in evaluated.values() for row in rows
            ),
            gates_passed=gates_passed,
        )
    finally:
        bind = session.get_bind()
        session.close()
        bind.dispose()


def write_report(
    output: Path, evidence_root: Path | None = None
) -> RetrievalBenchmarkMetrics:
    metrics = run_benchmark()
    summary = asdict(metrics)
    observations = summary.pop("observations")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    if evidence_root is not None:
        manifest = create_manifest(
            "retrieval-quality",
            dataset={
                "version": metrics.dataset_version,
                "queryCount": metrics.query_count,
                "caseIds": [
                    row["caseId"] for row in observations[: metrics.query_count]
                ],
            },
            configuration={
                "ablations": [item.configuration for item in metrics.ablations],
                "topK": 10,
                "bootstrapResamples": 2_000,
            },
            classification="ci-regression",
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
        description="BerryBrain executed retrieval ablation benchmark"
    )
    parser.add_argument("--output", default="reports/retrieval-benchmark.json")
    parser.add_argument("--evidence-root", default="")
    args = parser.parse_args()
    metrics = write_report(
        Path(args.output),
        Path(args.evidence_root) if args.evidence_root else None,
    )
    report = asdict(metrics)
    report.pop("observations", None)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if metrics.gates_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
