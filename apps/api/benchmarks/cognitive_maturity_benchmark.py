from __future__ import annotations

import json
from dataclasses import asdict, dataclass

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

import berrybrain_api.models  # noqa: F401
from berrybrain_api.database import Base
from berrybrain_api.generated_metadata import upsert_generated_metadata
from berrybrain_api.models import (
    ConceptRecord,
    ConnectionRecord,
    GraphEdgeRecord,
    GraphNodeRecord,
    InsightRecord,
    NoteRecord,
)
from berrybrain_api.second_brain import expand_knowledge_graph


@dataclass(frozen=True)
class KnowledgeFixture:
    key: str
    title: str
    concepts: tuple[str, ...]


@dataclass(frozen=True)
class CognitiveMaturityMetrics:
    note_count: int
    concept_recall: float
    concept_precision: float
    connection_recall: float
    connection_precision: float
    insight_grounded_rate: float
    provenance_coverage: float
    unsupported_claim_rate: float
    diagnostic_leakage_rate: float
    idempotent_rebuild: bool
    stale_knowledge_removed: bool
    review_status_preserved: bool
    meets_targets: bool


FIXTURES = (
    KnowledgeFixture(
        "observability",
        "Distributed Observability",
        ("distributed tracing", "latency", "telemetry sampling"),
    ),
    KnowledgeFixture(
        "edge-monitoring",
        "Edge Monitoring",
        ("distributed tracing", "latency", "edge devices"),
    ),
    KnowledgeFixture(
        "statistical-sampling",
        "Statistical Sampling",
        ("telemetry sampling", "sampling bias", "confidence intervals"),
    ),
    KnowledgeFixture(
        "docker-operations",
        "Docker Operations",
        ("container lifecycle", "shell automation", "namespaces"),
    ),
    KnowledgeFixture(
        "shell-runbooks",
        "Shell Runbooks",
        ("shell automation", "container lifecycle", "incident recovery"),
    ),
    KnowledgeFixture(
        "database-recovery",
        "Database Recovery",
        ("incident recovery", "backup restoration", "replication"),
    ),
)

EXPECTED_CONCEPTS = frozenset(
    concept for fixture in FIXTURES for concept in fixture.concepts
)
EXPECTED_CONNECTIONS = frozenset(
    {
        frozenset(("observability", "edge-monitoring")),
        frozenset(("observability", "statistical-sampling")),
        frozenset(("docker-operations", "shell-runbooks")),
        frozenset(("shell-runbooks", "database-recovery")),
    }
)
TECHNICAL_MARKERS = (
    "jobsbytype",
    "generate_note_title",
    "graphnotes",
    "explainedconnections",
    "pipeline bottleneck",
    "raw json",
)


def build_fixture_database() -> tuple[Session, dict[int, str]]:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False, autocommit=False)()
    key_by_note_id: dict[int, str] = {}

    for index, fixture in enumerate(FIXTURES):
        content_hash = f"fixture-{index}-v1"
        note = NoteRecord(
            title=fixture.title,
            slug=fixture.key,
            path=f"knowledge/{fixture.key}.md",
            content="curated maturity benchmark source material.",
            content_hash=content_hash,
            status="processed",
            language="en",
        )
        session.add(note)
        session.flush()
        key_by_note_id[note.id] = fixture.key
        upsert_generated_metadata(
            session,
            note.id,
            "concepts",
            {"concepts": list(fixture.concepts)},
            content_hash,
            model_used="expert-labeled-fixture.v1",
        )

    expand_knowledge_graph(session)
    return session, key_by_note_id


def run_benchmark() -> CognitiveMaturityMetrics:
    session, key_by_note_id = build_fixture_database()
    try:
        concepts = {
            record.normalized_name
            for record in session.query(ConceptRecord).all()
            if record.status != "ignored"
        }
        concept_recall = _ratio(
            len(concepts & EXPECTED_CONCEPTS), len(EXPECTED_CONCEPTS)
        )
        concept_precision = _ratio(len(concepts & EXPECTED_CONCEPTS), len(concepts))

        connections = [
            record
            for record in session.query(ConnectionRecord).all()
            if record.connection_type == "shared_concept"
            and record.status not in {"ignored", "archived", "stale"}
        ]
        found_connections = {
            frozenset(
                (
                    key_by_note_id[record.source_note_id],
                    key_by_note_id[record.target_note_id],
                )
            )
            for record in connections
        }
        connection_recall = _ratio(
            len(found_connections & EXPECTED_CONNECTIONS), len(EXPECTED_CONNECTIONS)
        )
        connection_precision = _ratio(
            len(found_connections & EXPECTED_CONNECTIONS), len(found_connections)
        )

        insights = [
            record
            for record in session.query(InsightRecord).all()
            if record.status not in {"ignored", "archived", "dismissed"}
        ]
        grounded = [record for record in insights if _is_grounded_insight(record)]
        diagnostics = [record for record in insights if _is_diagnostic(record)]
        unsupported = [record for record in insights if not _is_supported(record)]

        provenance_items = _provenance_items(session)
        provenance_coverage = _ratio(
            sum(1 for complete in provenance_items if complete), len(provenance_items)
        )
        counts_before = _artifact_counts(session)
        expand_knowledge_graph(session)
        counts_after = _artifact_counts(session)
        idempotent_rebuild = counts_before == counts_after

        reviewed_connection = connections[0]
        reviewed_connection.status = "confirmed"
        session.commit()
        expand_knowledge_graph(session)
        session.refresh(reviewed_connection)
        review_status_preserved = reviewed_connection.status == "confirmed"

        stale_knowledge_removed = _remove_shared_evidence_and_rebuild(
            session, key_by_note_id
        )

        metrics = CognitiveMaturityMetrics(
            note_count=len(FIXTURES),
            concept_recall=round(concept_recall, 4),
            concept_precision=round(concept_precision, 4),
            connection_recall=round(connection_recall, 4),
            connection_precision=round(connection_precision, 4),
            insight_grounded_rate=round(_ratio(len(grounded), len(insights)), 4),
            provenance_coverage=round(provenance_coverage, 4),
            unsupported_claim_rate=round(_ratio(len(unsupported), len(insights)), 4),
            diagnostic_leakage_rate=round(_ratio(len(diagnostics), len(insights)), 4),
            idempotent_rebuild=idempotent_rebuild,
            stale_knowledge_removed=stale_knowledge_removed,
            review_status_preserved=review_status_preserved,
            meets_targets=False,
        )
        object.__setattr__(
            metrics,
            "meets_targets",
            metrics.concept_recall >= 0.95
            and metrics.concept_precision >= 0.95
            and metrics.connection_recall >= 0.90
            and metrics.connection_precision >= 0.85
            and metrics.insight_grounded_rate == 1.0
            and metrics.provenance_coverage == 1.0
            and metrics.unsupported_claim_rate <= 0.02
            and metrics.diagnostic_leakage_rate == 0.0
            and metrics.idempotent_rebuild
            and metrics.stale_knowledge_removed
            and metrics.review_status_preserved,
        )
        return metrics
    finally:
        engine = session.get_bind()
        session.close()
        engine.dispose()


def _is_grounded_insight(insight: InsightRecord) -> bool:
    return bool(
        _json_list(insight.evidence)
        and insight.why_it_matters.strip()
        and insight.suggested_action.strip()
        and insight.graph_impact.strip()
        and insight.provider.strip()
        and insight.model.strip()
        and insight.prompt_version.strip()
    )


def _is_diagnostic(insight: InsightRecord) -> bool:
    text = " ".join(
        (insight.type, insight.title, insight.description, insight.reasoning)
    ).lower()
    return insight.type == "system_diagnostic" or any(
        marker in text for marker in TECHNICAL_MARKERS
    )


def _is_supported(insight: InsightRecord) -> bool:
    evidence = _json_list(insight.evidence)
    related_notes = _json_list(insight.related_notes)
    return len(evidence) >= 2 and bool(related_notes)


def _provenance_items(session: Session) -> list[bool]:
    items: list[bool] = []
    for node in session.query(GraphNodeRecord).filter(GraphNodeRecord.type != "note"):
        items.append(
            bool(
                node.source
                and _json_list(node.source_note_ids)
                and _json_list(node.source_evidence)
                and node.provider
                and node.model
                and node.prompt_version
            )
        )
    for edge in session.query(GraphEdgeRecord).filter(
        GraphEdgeRecord.status.not_in(("ignored", "archived", "stale"))
    ):
        items.append(
            bool(
                edge.reason
                and _json_list(edge.evidence)
                and edge.created_by
                and edge.provider
                and edge.model
                and edge.prompt_version
            )
        )
    for insight in session.query(InsightRecord).filter(
        InsightRecord.status.not_in(("ignored", "archived", "dismissed"))
    ):
        items.append(_is_grounded_insight(insight))
    return items


def _remove_shared_evidence_and_rebuild(
    session: Session, key_by_note_id: dict[int, str]
) -> bool:
    target_id = next(
        note_id for note_id, key in key_by_note_id.items() if key == "edge-monitoring"
    )
    target = session.get(NoteRecord, target_id)
    if target is None:
        return False
    target.content_hash = "edge-monitoring-v2"
    session.commit()
    upsert_generated_metadata(
        session,
        target.id,
        "concepts",
        {"concepts": ["edge devices"]},
        target.content_hash,
        model_used="expert-labeled-fixture.v1",
    )
    expand_knowledge_graph(session)
    observability_id = next(
        note_id for note_id, key in key_by_note_id.items() if key == "observability"
    )
    stale_pair = (
        session.query(ConnectionRecord)
        .filter(
            ConnectionRecord.connection_type == "shared_concept",
            ConnectionRecord.source_note_id.in_((observability_id, target.id)),
            ConnectionRecord.target_note_id.in_((observability_id, target.id)),
        )
        .all()
    )
    return all(
        record.status in {"stale", "ignored", "archived"} for record in stale_pair
    )


def _artifact_counts(session: Session) -> tuple[int, int, int, int]:
    return (
        session.query(ConceptRecord).count(),
        session.query(ConnectionRecord).count(),
        session.query(GraphEdgeRecord).count(),
        session.query(InsightRecord).count(),
    )


def _json_list(raw: str) -> list[object]:
    try:
        value = json.loads(raw or "[]")
    except (json.JSONDecodeError, TypeError):
        return []
    return value if isinstance(value, list) else []


def _ratio(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 1.0


if __name__ == "__main__":
    metrics = run_benchmark()
    print(json.dumps(asdict(metrics), indent=2, sort_keys=True))
    raise SystemExit(0 if metrics.meets_targets else 1)
