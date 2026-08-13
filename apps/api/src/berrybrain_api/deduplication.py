from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from berrybrain_api.concept_extraction import normalize_concept_name
from berrybrain_api.models import (
    ConceptRecord,
    GraphNodeRecord,
    InsightRecord,
    NoteRecord,
)

# Constants from second_brain
PROMPT_VERSION = "graph-expand.deterministic.v1"
STOPWORDS = {
    "a",
    "about",
    "an",
    "and",
    "for",
    "from",
    "has",
    "have",
    "in",
    "is",
    "of",
    "on",
    "relationship",
    "relationships",
    "see",
    "the",
    "to",
    "what",
    "which",
    "with",
}


def _merge_duplicate_nodes(session: Session) -> int:
    from berrybrain_api.graph_write_service import GraphWriteService

    return GraphWriteService(session, autocommit=False).deduplicate_nodes()


def _delete_duplicate_edges(session: Session) -> int:
    from berrybrain_api.graph_write_service import GraphWriteService

    return GraphWriteService(session, autocommit=False).deduplicate_edges()


def _prune_stale_concepts(session: Session, valid_normalized: set[str]) -> int:
    stale_concepts = list(
        session.execute(
            select(ConceptRecord).where(ConceptRecord.status == "suggested")
        ).scalars()
    )
    removed = 0
    for concept in stale_concepts:
        normalized = normalize_concept_name(concept.normalized_name or concept.name)
        if normalized in valid_normalized:
            continue
        nodes = list(
            session.execute(
                select(GraphNodeRecord).where(
                    GraphNodeRecord.type == "concept",
                    GraphNodeRecord.source_id == concept.id,
                )
            ).scalars()
        )
        for node in nodes:
            _delete_graph_node_with_edges(session, node)
        session.delete(concept)
        removed += 1
    if removed:
        session.flush()
    return removed


def _delete_graph_node_with_edges(session: Session, node: GraphNodeRecord) -> None:
    from berrybrain_api.graph_write_service import GraphWriteService

    GraphWriteService(session, autocommit=False).delete_node(node.id)


def _prune_title_duplicate_typed_nodes(
    session: Session, notes: list[NoteRecord]
) -> int:
    note_titles = {normalize_concept_name(note.title) for note in notes}
    note_titles.discard("")
    if not note_titles:
        return 0
    removed = 0
    nodes = list(
        session.execute(
            select(GraphNodeRecord).where(
                GraphNodeRecord.type.not_in(("note", "insight"))
            )
        ).scalars()
    )
    for node in nodes:
        if normalize_concept_name(node.label) not in note_titles:
            continue
        _delete_graph_node_with_edges(session, node)
        removed += 1
    if removed:
        session.flush()
    return removed


def _prune_generated_typed_nodes(
    session: Session, keep_node_ids: set[int] | None = None
) -> int:
    nodes = list(
        session.execute(
            select(GraphNodeRecord).where(
                GraphNodeRecord.type.in_(
                    ("topic", "entity", "context", "gap", "source")
                ),
                GraphNodeRecord.status == "suggested",
                GraphNodeRecord.source.in_(("metadata", "frontmatter")),
            )
        ).scalars()
    )
    if keep_node_ids is not None:
        nodes = [node for node in nodes if node.id not in keep_node_ids]
    for node in nodes:
        _delete_graph_node_with_edges(session, node)
    if nodes:
        session.flush()
    return len(nodes)


def _prune_generated_graph_insights(session: Session) -> int:
    generated_types = {
        "recurring_concept",
        "central_concept",
        "new_connection",
        "knowledge_gap",
    }
    insights = list(
        session.execute(
            select(InsightRecord).where(
                InsightRecord.type.in_(generated_types),
                InsightRecord.status == "suggested",
                InsightRecord.provider.in_(("deterministic", "system", "")),
            )
        ).scalars()
    )
    removed = 0
    for insight in insights:
        nodes = list(
            session.execute(
                select(GraphNodeRecord).where(
                    GraphNodeRecord.type == "insight",
                    GraphNodeRecord.source_id == insight.id,
                )
            ).scalars()
        )
        for node in nodes:
            _delete_graph_node_with_edges(session, node)
        session.delete(insight)
        removed += 1
    if removed:
        session.flush()
    return removed


def _prune_orphan_insight_nodes(session: Session) -> int:
    valid_ids = set(session.execute(select(InsightRecord.id)).scalars())
    nodes = list(
        session.execute(
            select(GraphNodeRecord).where(GraphNodeRecord.type == "insight")
        ).scalars()
    )
    removed = 0
    for node in nodes:
        if node.source_id not in valid_ids:
            _delete_graph_node_with_edges(session, node)
            removed += 1
    if removed:
        session.flush()
    return removed


def _prune_stale_graph_insights(session: Session, valid_normalized: set[str]) -> int:
    removed = 0
    insights = list(
        session.execute(
            select(InsightRecord).where(
                InsightRecord.type.in_(("recurring_concept", "new_connection")),
                InsightRecord.status == "suggested",
            )
        ).scalars()
    )
    for insight in insights:
        concept_name = _insight_concept_name(insight.title)
        if normalize_concept_name(concept_name) in valid_normalized:
            continue
        nodes = list(
            session.execute(
                select(GraphNodeRecord).where(
                    GraphNodeRecord.type == "insight",
                    GraphNodeRecord.source_id == insight.id,
                )
            ).scalars()
        )
        for node in nodes:
            _delete_graph_node_with_edges(session, node)
        session.delete(insight)
        removed += 1
    if removed:
        session.flush()
    return removed


def _insight_concept_name(title: str) -> str:
    clean = str(title or "").strip()
    if clean.startswith("Recurring concept: "):
        return clean.removeprefix("Recurring concept: ").strip()
    if clean.startswith("Connection pattern: "):
        parts = clean.split('"')
        if len(parts) >= 3:
            return parts[1].strip()
    return clean
