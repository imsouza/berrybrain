from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
import time
from dataclasses import asdict, dataclass
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session, sessionmaker

import berrybrain_api.models  # noqa: F401
from berrybrain_api.database import Base
from berrybrain_api.models import ChunkRecord, ConnectionRecord, NoteRecord
from berrybrain_api.search import hybrid_search, init_fts
from berrybrain_api.services import find_similar_chunk_notes, store_embedding


@dataclass(frozen=True)
class TopicFixture:
    key: str
    title: str
    terms: str
    semantic_queries: tuple[str, str]


@dataclass(frozen=True)
class BenchmarkQuery:
    text: str
    topic: str | None
    expected_paths: tuple[str, ...]


@dataclass
class BenchmarkMetrics:
    note_count: int
    query_count: int
    positive_query_count: int
    negative_query_count: int
    recall_at_5: float
    recall_at_10: float
    mean_reciprocal_rank: float
    ndcg_at_10: float
    zero_result_rate: float
    unexpected_zero_result_rate: float
    negative_rejection_rate: float
    latency_p50_ms: float
    latency_p95_ms: float
    indexing_coverage: float
    relationship_recall_at_10: float
    stale_evidence_count: int
    meets_initial_targets: bool


TOPICS = (
    TopicFixture(
        "observability",
        "Distributed Observability",
        "logs metrics traces telemetry latency failures services monitoring",
        (
            "how to understand failures across many independent services",
            "following one request through a decentralized application",
        ),
    ),
    TopicFixture(
        "semantic-retrieval",
        "Semantic Retrieval",
        "embeddings vectors retrieval rag similarity chunks meaning index",
        (
            "representing meaning as coordinates for finding related knowledge",
            "locating passages that use different words for the same idea",
        ),
    ),
    TopicFixture(
        "containers",
        "Containerized Applications",
        "docker containers images compose runtime isolation reproducible deployment",
        (
            "packaging an application with its runtime for repeatable execution",
            "isolating software dependencies without a full virtual machine",
        ),
    ),
    TopicFixture(
        "shell-automation",
        "Shell Automation",
        "linux shell bash scripts pipes commands automation terminal processes",
        (
            "joining small command line tools into a repeatable workflow",
            "automating operating system tasks with executable text files",
        ),
    ),
    TopicFixture(
        "async-python",
        "Asynchronous Python",
        "python async await event loop coroutines concurrency io tasks",
        (
            "handling many waiting operations without one thread per request",
            "cooperative scheduling for network bound programs",
        ),
    ),
    TopicFixture(
        "statistics",
        "Statistical Inference",
        "probability distributions hypothesis confidence sampling variance bayesian data",
        (
            "reasoning from a sample about an unknown population",
            "quantifying uncertainty before accepting an experimental claim",
        ),
    ),
    TopicFixture(
        "edge-computing",
        "Edge Computing",
        "edge devices latency local processing sensors distributed bandwidth cloud",
        (
            "processing information near where physical signals are produced",
            "reducing response delay by moving computation away from a central region",
        ),
    ),
    TopicFixture(
        "knowledge-graphs",
        "Knowledge Graphs",
        "knowledge graph nodes edges entities concepts relations evidence ontology",
        (
            "representing facts as explainable relationships between things",
            "navigating ideas through typed links and supporting evidence",
        ),
    ),
    TopicFixture(
        "application-security",
        "Application Security",
        "security authentication authorization threats encryption sessions attacks audit",
        (
            "limiting damage when an identity credential is stolen",
            "verifying who may perform a sensitive operation",
        ),
    ),
    TopicFixture(
        "databases",
        "Database Reliability",
        "database transactions indexes consistency replication recovery queries storage",
        (
            "keeping committed information correct after a machine failure",
            "making durable state available across multiple copies",
        ),
    ),
)

NEGATIVE_QUERIES = (
    "coral spawning cycles in tropical reefs",
    "renaissance oil pigment restoration",
    "volcanic minerals in lunar samples",
    "baroque counterpoint for string quartets",
    "fermentation temperatures for sourdough starters",
)


def _topic_vector(topic_index: int) -> list[float]:
    vector = [0.0] * 16
    vector[topic_index] = 1.0
    return vector


def build_fixture_database(
    notes_per_topic: int = 10,
) -> tuple[Session, list[BenchmarkQuery], dict[str, int], list[tuple[int, str]]]:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = session_factory()
    init_fts(session)

    paths_by_topic: dict[str, list[str]] = {}
    note_ids_by_topic: dict[str, list[int]] = {}
    topic_index_by_path: dict[str, int] = {}
    for topic_index, topic in enumerate(TOPICS):
        for note_index in range(notes_per_topic):
            path = f"benchmark/{topic.key}-{note_index + 1:03d}.md"
            content = (
                f"# {topic.title}: Study {note_index + 1}\n\n"
                f"This note examines {topic.terms}. "
                f"It records evidence, assumptions, and an applied example {note_index + 1}."
            )
            content_hash = hashlib.sha256(content.encode()).hexdigest()
            note = NoteRecord(
                title=f"{topic.title} Study {note_index + 1}",
                slug=f"{topic.key}-{note_index + 1}",
                path=path,
                content=content,
                content_hash=content_hash,
                status="assimilated",
                language="en",
            )
            session.add(note)
            session.flush()
            paths_by_topic.setdefault(topic.key, []).append(path)
            note_ids_by_topic.setdefault(topic.key, []).append(note.id)
            topic_index_by_path[path] = topic_index
        session.commit()

    for topic in TOPICS:
        topic_index = TOPICS.index(topic)
        for note_id, path in zip(
            note_ids_by_topic[topic.key], paths_by_topic[topic.key]
        ):
            note = session.get(NoteRecord, note_id)
            assert note is not None
            store_embedding(
                session,
                note_id=note.id,
                content_hash=note.content_hash,
                vector=_topic_vector(topic_index),
                model="benchmark-semantic-v1",
                provider="deterministic-fixture",
                chunk_index=0,
                chunk_text=note.content,
                heading_path=note.title,
                start_line=1,
                end_line=3,
                token_count=len(note.content.split()),
            )

        ids = note_ids_by_topic[topic.key]
        session.add(
            ConnectionRecord(
                source_note_id=ids[0],
                target_note_id=ids[1],
                connection_type="semantic_similarity",
                confidence=95,
                reason=f"Both notes provide evidence about {topic.title}.",
                evidence=json.dumps([paths_by_topic[topic.key][0], paths_by_topic[topic.key][1]]),
                created_by="benchmark",
                provider="deterministic-fixture",
                model="benchmark-semantic-v1",
                status="confirmed",
            )
        )
    session.commit()

    queries: list[BenchmarkQuery] = []
    for topic in TOPICS:
        expected = tuple(paths_by_topic[topic.key][:10])
        queries.extend(
            (
                BenchmarkQuery(topic.title, topic.key, expected),
                BenchmarkQuery(topic.terms.split()[0] + " " + topic.terms.split()[1], topic.key, expected),
                BenchmarkQuery(topic.semantic_queries[0], topic.key, expected),
                BenchmarkQuery(topic.semantic_queries[1], topic.key, expected),
            )
        )
    queries.extend(BenchmarkQuery(text, None, ()) for text in NEGATIVE_QUERIES)

    relation_expectations = [
        (note_ids_by_topic[topic.key][0], paths_by_topic[topic.key][1])
        for topic in TOPICS
    ]
    return session, queries, topic_index_by_path, relation_expectations


def _recall(results: list[str], expected: set[str], k: int) -> float:
    if not expected:
        return 0.0
    return len(set(results[:k]) & expected) / len(expected)


def _reciprocal_rank(results: list[str], expected: set[str]) -> float:
    for rank, path in enumerate(results, start=1):
        if path in expected:
            return 1.0 / rank
    return 0.0


def _ndcg(results: list[str], expected: set[str], k: int) -> float:
    dcg = sum(
        1.0 / math.log2(rank + 1)
        for rank, path in enumerate(results[:k], start=1)
        if path in expected
    )
    ideal = sum(
        1.0 / math.log2(rank + 1)
        for rank in range(1, min(k, len(expected)) + 1)
    )
    return dcg / ideal if ideal else 0.0


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = max(0, math.ceil(percentile * len(ordered)) - 1)
    return ordered[index]


def run_benchmark(notes_per_topic: int = 10) -> BenchmarkMetrics:
    session, queries, _topic_indexes, relation_expectations = build_fixture_database(
        notes_per_topic
    )
    recalls_5: list[float] = []
    recalls_10: list[float] = []
    reciprocal_ranks: list[float] = []
    ndcgs: list[float] = []
    latencies: list[float] = []
    zero_results = 0
    unexpected_zero_results = 0
    rejected_negatives = 0
    stale_evidence_count = 0

    try:
        for query in queries:
            query_vector = None
            if query.topic is not None:
                topic_index = next(
                    index for index, topic in enumerate(TOPICS) if topic.key == query.topic
                )
                query_vector = _topic_vector(topic_index)
            started = time.perf_counter()
            results = hybrid_search(
                session,
                query.text,
                limit=10,
                query_vector=query_vector,
            )
            latencies.append((time.perf_counter() - started) * 1000)
            paths = [str(item["path"]) for item in results]
            if not results:
                zero_results += 1
                if query.topic is not None:
                    unexpected_zero_results += 1
            if query.topic is None:
                rejected_negatives += int(not results)
                continue

            expected = set(query.expected_paths)
            recalls_5.append(_recall(paths, expected, 5))
            recalls_10.append(_recall(paths, expected, 10))
            reciprocal_ranks.append(_reciprocal_rank(paths, expected))
            ndcgs.append(_ndcg(paths, expected, 10))
            for item in results:
                note = session.execute(
                    select(NoteRecord).where(NoteRecord.path == item["path"])
                ).scalar_one()
                for evidence in item.get("evidence", []):
                    evidence_hash = evidence.get("contentHash")
                    if evidence_hash and evidence_hash != note.content_hash:
                        stale_evidence_count += 1

        relation_hits = 0
        for source_note_id, expected_path in relation_expectations:
            candidates = find_similar_chunk_notes(
                session, source_note_id=source_note_id, limit=10
            )
            relation_hits += int(
                expected_path in {str(item["path"]) for item in candidates}
            )

        note_count = session.scalar(select(func.count()).select_from(NoteRecord)) or 0
        current_chunk_count = (
            session.scalar(
                select(func.count())
                .select_from(ChunkRecord)
                .join(NoteRecord, NoteRecord.id == ChunkRecord.note_id)
                .where(ChunkRecord.content_hash == NoteRecord.content_hash)
            )
            or 0
        )
        coverage = current_chunk_count / note_count if note_count else 0.0
        positive_count = len(recalls_10)
        negative_count = len(queries) - positive_count
        metrics = BenchmarkMetrics(
            note_count=note_count,
            query_count=len(queries),
            positive_query_count=positive_count,
            negative_query_count=negative_count,
            recall_at_5=statistics.fmean(recalls_5),
            recall_at_10=statistics.fmean(recalls_10),
            mean_reciprocal_rank=statistics.fmean(reciprocal_ranks),
            ndcg_at_10=statistics.fmean(ndcgs),
            zero_result_rate=zero_results / len(queries),
            unexpected_zero_result_rate=(
                unexpected_zero_results / positive_count if positive_count else 0.0
            ),
            negative_rejection_rate=(
                rejected_negatives / negative_count if negative_count else 0.0
            ),
            latency_p50_ms=statistics.median(latencies),
            latency_p95_ms=_percentile(latencies, 0.95),
            indexing_coverage=coverage,
            relationship_recall_at_10=relation_hits / len(relation_expectations),
            stale_evidence_count=stale_evidence_count,
            meets_initial_targets=False,
        )
        metrics.meets_initial_targets = (
            metrics.recall_at_10 >= 0.85
            and metrics.mean_reciprocal_rank >= 0.70
            and metrics.latency_p95_ms <= 500
            and metrics.indexing_coverage >= 0.995
            and metrics.stale_evidence_count == 0
        )
        return metrics
    finally:
        session.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="BerryBrain semantic retrieval benchmark")
    parser.add_argument(
        "--notes-per-topic",
        type=int,
        default=10,
        help="10 creates the canonical 100-note dataset; 100 creates the 1,000-note latency run.",
    )
    args = parser.parse_args()
    metrics = run_benchmark(notes_per_topic=max(10, args.notes_per_topic))
    print(json.dumps(asdict(metrics), indent=2, sort_keys=True))
    return 0 if metrics.meets_initial_targets else 1


if __name__ == "__main__":
    raise SystemExit(main())
