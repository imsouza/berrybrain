from __future__ import annotations

import json
import re
from collections import defaultdict
from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from berrybrain_api.artifact_state import accepted_edge_clause, accepted_node_clause
from berrybrain_api.concept_extraction import (
    _extract_note_concepts,
    normalize_concept_name,
)
from berrybrain_api.confidence import (
    ConfidenceSignal,
    estimate_confidence,
    persist_confidence,
)
from berrybrain_api.connection_detection import _upsert_note_connection
from berrybrain_api.deduplication import (
    _delete_graph_node_with_edges,
    _merge_duplicate_nodes,
    _prune_generated_graph_insights,
    _prune_generated_typed_nodes,
    _prune_orphan_insight_nodes,
    _prune_stale_concepts,
    _prune_stale_graph_insights,
    _prune_title_duplicate_typed_nodes,
)
from berrybrain_api.graph_feedback import node_artifact_key, resolve_feedback
from berrybrain_api.graph_ontology import validate_node_name
from berrybrain_api.graph_semantic_service import quarantine_generated_candidate
from berrybrain_api.models import (
    ConceptRecord,
    ConnectionRecord,
    GeneratedMetadataRecord,
    GraphEdgeRecord,
    GraphNodeRecord,
    NoteRecord,
    SettingRecord,
)
from berrybrain_api.settings_store import decode_setting_value

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


def _parse_json_list(value: str | None) -> list[Any]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return []
    return parsed if isinstance(parsed, list) else []


def _second_brain_helper(name: str) -> Any:
    from berrybrain_api import second_brain

    return getattr(second_brain, name)


def _dump_json(value: Any) -> str:
    return _second_brain_helper("_dump_json")(value)


def _note_lookup_key(value: str) -> str:
    return _second_brain_helper("_note_lookup_key")(value)


def _extract_topics_from_metadata(session: Session, metadata_by_note: dict) -> int:
    return _second_brain_helper("_extract_topics_from_metadata")(
        session, metadata_by_note
    )


def _extract_entities_from_metadata(session: Session, metadata_by_note: dict) -> int:
    return _second_brain_helper("_extract_entities_from_metadata")(
        session, metadata_by_note
    )


def _extract_context_from_metadata(session: Session, metadata_by_note: dict) -> int:
    return _second_brain_helper("_extract_context_from_metadata")(
        session, metadata_by_note
    )


def _extract_gaps_from_metadata(session: Session, metadata_by_note: dict) -> int:
    return _second_brain_helper("_extract_gaps_from_metadata")(
        session, metadata_by_note
    )


def _extract_sources_from_notes(session: Session, notes: list[NoteRecord]) -> int:
    return _second_brain_helper("_extract_sources_from_notes")(session, notes)


def _generate_deterministic_insights(session: Session) -> None:
    _second_brain_helper("_generate_deterministic_insights")(session)


def _generate_graph_insights(session: Session) -> int:
    return _second_brain_helper("_generate_graph_insights")(session)


def _ensure_graph_node_context(session: Session) -> int:
    return _second_brain_helper("_ensure_graph_node_context")(session)


def _ensure_graph_edge_traceability(session: Session) -> int:
    return _second_brain_helper("_ensure_graph_edge_traceability")(session)


def _migrate_active_ai_edge_evidence(session: Session) -> dict[str, int]:
    return _second_brain_helper("_migrate_active_ai_edge_evidence")(session)


def expand_knowledge_graph(session: Session) -> dict[str, int]:
    _merge_duplicate_nodes(session)

    notes = list(session.execute(select(NoteRecord)).scalars())
    metadata = list(session.execute(select(GeneratedMetadataRecord)).scalars())
    metadata_by_note: dict[int, list[GeneratedMetadataRecord]] = defaultdict(list)
    for record in metadata:
        metadata_by_note[record.note_id].append(record)

    note_nodes = {_node_key("note", n.id): _upsert_note_node(session, n) for n in notes}
    _prune_generated_graph_insights(session)
    _prune_orphan_insight_nodes(session)
    _prune_title_duplicate_typed_nodes(session, notes)
    concept_to_note_ids: dict[str, set[int]] = defaultdict(set)
    concept_sources: dict[str, list[str]] = defaultdict(list)
    concept_models: dict[str, str] = {}
    rejected_candidates = 0

    for note in notes:
        for concept_name, evidence, model in _extract_note_concepts(
            note, metadata_by_note.get(note.id, [])
        ):
            issues = validate_node_name("concept", concept_name)
            if issues:
                quarantine_generated_candidate(
                    session,
                    kind="node",
                    proposed_type="concept",
                    proposed_label=concept_name,
                    issues=issues,
                    payload={
                        "noteId": note.id,
                        "evidence": [evidence] if evidence else [],
                    },
                )
                rejected_candidates += 1
                continue
            normalized = normalize_concept_name(concept_name)
            if not normalized:
                continue
            concept_to_note_ids[normalized].add(note.id)
            if evidence and evidence not in concept_sources[normalized]:
                concept_sources[normalized].append(evidence)
            if model and (
                normalized not in concept_models
                or concept_models[normalized] == "content-analysis"
            ):
                concept_models[normalized] = model

    # Deterministic text candidates need independent corpus corroboration. AI
    # concepts instead carry model evidence and are evaluated by the Judge.
    for normalized in list(concept_to_note_ids):
        if (
            concept_models.get(normalized) == "content-analysis"
            and len(concept_to_note_ids[normalized]) < 2
        ):
            del concept_to_note_ids[normalized]
            concept_sources.pop(normalized, None)
            concept_models.pop(normalized, None)

    for normalized in list(concept_to_note_ids):
        source_note_ids = sorted(concept_to_note_ids[normalized])
        decision = resolve_feedback(
            session,
            artifact_kind="node",
            artifact_key=node_artifact_key(
                "concept", _display_concept_name(normalized)
            ),
            source_note_ids=source_note_ids,
        )
        if decision is None or not decision.suppresses:
            continue
        del concept_to_note_ids[normalized]
        concept_sources.pop(normalized, None)
        concept_models.pop(normalized, None)

    _prune_stale_concepts(session, set(concept_to_note_ids))
    _prune_stale_graph_insights(session, set(concept_to_note_ids))

    concept_nodes: dict[str, GraphNodeRecord] = {}
    concepts_count = 0
    for normalized, note_ids in concept_to_note_ids.items():
        concept = _upsert_concept(
            session,
            name=_display_concept_name(normalized),
            normalized_name=normalized,
            note_ids=sorted(note_ids),
            evidence=concept_sources[normalized],
            model=concept_models.get(normalized, ""),
        )
        concepts_count += 1
        concept_nodes[normalized] = _upsert_concept_node(session, concept)

    edges_count = 0
    connections_count = 0
    valid_shared_pairs: set[tuple[int, int]] = set()
    minimum_shared_concepts = _minimum_shared_concepts(session)
    shared_concepts_by_pair: dict[tuple[int, int], list[str]] = defaultdict(list)
    for normalized, concept_node in concept_nodes.items():
        for note_id in concept_to_note_ids[normalized]:
            note_node = note_nodes.get(_node_key("note", note_id))
            if note_node is None:
                continue
            edge = _upsert_graph_edge(
                session,
                note_node.id,
                concept_node.id,
                edge_type="mentions",
                label="shared concept",
                reason=f'The note mentions the concept "{concept_node.label}".',
                evidence=[concept_node.label],
                source_note_ids=[note_id],
                created_by="system",
                status="suggested",
            )
            if edge:
                edges_count += 1

        shared_note_ids = sorted(concept_to_note_ids[normalized])
        if len(shared_note_ids) > 1:
            for index, source_id in enumerate(shared_note_ids):
                for target_id in shared_note_ids[index + 1 :]:
                    pair = (source_id, target_id)
                    shared_concepts_by_pair[pair].append(concept_node.label)

    note_by_id = {note.id: note for note in notes}
    for (source_id, target_id), concept_labels in shared_concepts_by_pair.items():
        source_note = note_by_id.get(source_id)
        target_note = note_by_id.get(target_id)
        if source_note is None or target_note is None:
            continue
        unique_labels = sorted(set(concept_labels), key=str.casefold)
        has_enough_independent_evidence = len(unique_labels) >= minimum_shared_concepts
        has_specific_single_evidence = len(
            unique_labels
        ) == 1 and _is_specific_concept_label(unique_labels[0])
        if not (has_enough_independent_evidence or has_specific_single_evidence):
            continue
        valid_shared_pairs.add((source_id, target_id))
        concept_text = ", ".join(f'"{label}"' for label in unique_labels)
        reason = (
            f'The notes "{source_note.title}" and "{target_note.title}" share '
            f"the supported {'concept' if len(unique_labels) == 1 else 'concepts'} "
            f"{concept_text}."
        )
        evidence = [*unique_labels, source_note.title, target_note.title]
        conn = _upsert_note_connection(
            session,
            source_id,
            target_id,
            connection_type="shared_concept",
            reason=reason,
            evidence=evidence,
            created_by="system",
            status="suggested",
        )
        connections_count += int(conn is not None)
        source_node = note_nodes.get(_node_key("note", source_id))
        target_node = note_nodes.get(_node_key("note", target_id))
        if source_node is None or target_node is None:
            continue
        edge = _upsert_graph_edge(
            session,
            source_node.id,
            target_node.id,
            edge_type="related",
            label="shared concept",
            reason=reason,
            evidence=evidence,
            source_note_ids=[source_id, target_id],
            created_by="system",
            status="suggested",
            replace_evidence=True,
        )
        edges_count += int(edge is not None)

    _mark_stale_shared_concept_connections(session, valid_shared_pairs)

    note_to_concepts: dict[int, list[str]] = defaultdict(list)
    for normalized, note_ids in concept_to_note_ids.items():
        for note_id in note_ids:
            note_to_concepts[note_id].append(normalized)
    note_by_id = {note.id: note for note in notes}
    for note_id, normalized_names in note_to_concepts.items():
        note = note_by_id.get(note_id)
        if note is None:
            continue
        limited = sorted(set(normalized_names))[:8]
        for index, left_name in enumerate(limited):
            for right_name in limited[index + 1 :]:
                left = concept_nodes.get(left_name)
                right = concept_nodes.get(right_name)
                if left is None or right is None:
                    continue
                edge = _upsert_graph_edge(
                    session,
                    left.id,
                    right.id,
                    edge_type="related",
                    label="shared context",
                    reason=(
                        f'The concepts "{left.label}" and "{right.label}" appear '
                        f'together in the note "{note.title}".'
                    ),
                    evidence=[note.title, left.label, right.label],
                    source_note_ids=[note_id],
                    created_by="subagent:concept-linker",
                    status="suggested",
                )
                if edge:
                    edges_count += 1

    note_by_title = {_note_lookup_key(note.title): note for note in notes}
    note_by_slug = {_note_lookup_key(note.slug): note for note in notes}
    for source in notes:
        for link in _parse_json_list(source.links):
            target = note_by_title.get(_note_lookup_key(str(link))) or note_by_slug.get(
                _note_lookup_key(str(link))
            )
            if target is None or target.id == source.id:
                continue
            conn = _upsert_note_connection(
                session,
                source.id,
                target.id,
                connection_type="backlink",
                reason=f'The note "{source.title}" references "{target.title}" through a backlink.',
                evidence=[str(link), source.path, target.path],
                created_by="backlink",
                status="confirmed",
            )
            if conn:
                connections_count += 1
            source_node = note_nodes.get(_node_key("note", source.id))
            target_node = note_nodes.get(_node_key("note", target.id))
            if source_node and target_node:
                edge = _upsert_graph_edge(
                    session,
                    source_node.id,
                    target_node.id,
                    edge_type="backlink",
                    label="backlink",
                    reason=conn.reason,
                    evidence=_parse_json_list(conn.evidence),
                    source_note_ids=[source.id, target.id],
                    created_by="backlink",
                    status="confirmed",
                )
                if edge:
                    edges_count += 1

    session.info["graph_expansion_typed_node_ids"] = set()
    topics_count = _extract_topics_from_metadata(session, metadata_by_note)
    entities_count = _extract_entities_from_metadata(session, metadata_by_note)
    context_count = _extract_context_from_metadata(session, metadata_by_note)
    gaps_count = _extract_gaps_from_metadata(session, metadata_by_note)
    sources_count = _extract_sources_from_notes(session, notes)
    retained_typed_node_ids = set(
        session.info.pop("graph_expansion_typed_node_ids", set())
    )
    _prune_generated_typed_nodes(session, retained_typed_node_ids)
    retained_type_counts: dict[str, int] = defaultdict(int)
    if retained_typed_node_ids:
        for node_type in session.execute(
            select(GraphNodeRecord.type).where(
                GraphNodeRecord.id.in_(retained_typed_node_ids)
            )
        ).scalars():
            retained_type_counts[node_type] += 1
    topics_count = retained_type_counts["topic"]
    entities_count = retained_type_counts["entity"]
    context_count = retained_type_counts["context"]
    gaps_count = retained_type_counts["gap"]
    sources_count = retained_type_counts["source"]
    _generate_deterministic_insights(session)
    insights_count = _generate_graph_insights(session)

    typed_nodes = (
        session.execute(
            select(GraphNodeRecord).where(
                GraphNodeRecord.type.in_(
                    (
                        "concept",
                        "topic",
                        "entity",
                        "context",
                        "gap",
                        "source",
                        "insight",
                    )
                )
            )
        )
        .scalars()
        .all()
    )
    note_id_by_graph_node_id: dict[int, int] = {}
    for note_node in note_nodes.values():
        if note_node.source_id is not None:
            note_id_by_graph_node_id[note_node.id] = int(note_node.source_id)
    legacy_edges_by_node: dict[int, list[GraphEdgeRecord]] = defaultdict(list)
    for legacy_edge in session.execute(select(GraphEdgeRecord)).scalars():
        legacy_edges_by_node[legacy_edge.source_node_id].append(legacy_edge)
        legacy_edges_by_node[legacy_edge.target_node_id].append(legacy_edge)
    for typed_node in typed_nodes:
        source_ids = {
            int(value)
            for value in _parse_json_list(typed_node.source_note_ids)
            if str(value).isdigit()
        }
        for legacy_edge in legacy_edges_by_node.get(typed_node.id, []):
            other_id = (
                legacy_edge.target_node_id
                if legacy_edge.source_node_id == typed_node.id
                else legacy_edge.source_node_id
            )
            related_note_id = note_id_by_graph_node_id.get(other_id)
            if related_note_id:
                source_ids.add(related_note_id)
        typed_node.source_note_ids = _dump_json(sorted(source_ids))
        for note_id in sorted(source_ids):
            note_node = note_nodes.get(_node_key("note", note_id))
            if not note_node:
                continue
            existing = session.execute(
                select(GraphEdgeRecord).where(
                    GraphEdgeRecord.source_node_id == note_node.id,
                    GraphEdgeRecord.target_node_id == typed_node.id,
                    GraphEdgeRecord.type == "mentions",
                )
            ).first()
            if existing:
                continue
            edge = _upsert_graph_edge(
                session,
                note_node.id,
                typed_node.id,
                edge_type="mentions",
                label=f"mentions {typed_node.type}",
                reason=f'"{typed_node.label}" was extracted from the note "{note_node.label}".',
                evidence=[typed_node.label, note_node.label],
                source_note_ids=[note_id],
                created_by="system",
                status="suggested",
            )
            if edge:
                edges_count += 1

    contextualized_nodes = _ensure_graph_node_context(session)
    qualified_edges = _ensure_graph_edge_traceability(session)
    ai_evidence_migration = _migrate_active_ai_edge_evidence(session)
    from berrybrain_api.jobs import supersede_missing_graph_artifact_jobs

    stale_jobs_superseded = supersede_missing_graph_artifact_jobs(session)
    visible_nodes = list(
        session.execute(select(GraphNodeRecord).where(accepted_node_clause())).scalars()
    )
    visible_edges = list(
        session.execute(select(GraphEdgeRecord).where(accepted_edge_clause())).scalars()
    )

    session.commit()
    return {
        "notes": len(notes),
        "concepts": concepts_count,
        "topics": topics_count,
        "entities": entities_count,
        "contexts": context_count,
        "gaps": gaps_count,
        "sources": sources_count,
        "nodes": len(visible_nodes),
        "edges": len(visible_edges),
        "connections": connections_count,
        "insights": insights_count,
        "createdEdges": edges_count,
        "contextualizedNodes": contextualized_nodes,
        "qualifiedEdges": qualified_edges,
        "aiEdgesEvidenceRecovered": ai_evidence_migration["recovered"],
        "aiEdgesMarkedStale": ai_evidence_migration["stale"],
        "rejectedCandidates": rejected_candidates,
        "staleJobsSuperseded": stale_jobs_superseded,
    }


def delete_graph_node(session: Session, node_id: int) -> bool:
    node = session.get(GraphNodeRecord, node_id)
    if node is None:
        return False
    _delete_graph_node_with_edges(session, node)
    return True


def set_node_status(session: Session, node_id: int, status: str) -> GraphNodeRecord:
    from berrybrain_api.graph_write_service import GraphWriteService

    return GraphWriteService(session).set_node_status(node_id, status)


def set_node_user_notes(session: Session, node_id: int, notes: str) -> GraphNodeRecord:
    from berrybrain_api.graph_write_service import GraphWriteService

    return GraphWriteService(session).set_node_user_notes(node_id, notes)


def set_edge_status(session: Session, edge_id: int, status: str) -> GraphEdgeRecord:
    from berrybrain_api.graph_write_service import GraphWriteService

    return GraphWriteService(session).set_edge_status(edge_id, status)


def set_edge_user_notes(session: Session, edge_id: int, notes: str) -> GraphEdgeRecord:
    from berrybrain_api.graph_write_service import GraphWriteService

    return GraphWriteService(session).set_edge_user_notes(edge_id, notes)


def _upsert_note_node(session: Session, note: NoteRecord) -> GraphNodeRecord:
    metadata = {
        "path": note.path,
        "folder": note.path.split("/")[0] if "/" in note.path else "inbox",
        "status": note.status,
    }
    from berrybrain_api.graph_write_service import GraphWriteService

    return GraphWriteService(session, autocommit=False).upsert_node(
        node_type="note",
        label=note.title,
        title=note.title,
        summary=f"Vault note: {note.path}",
        ai_notes=(
            "Subagent graph-expander: vertex created from a real vault note; "
            "the note path is the auditable source."
        ),
        source="note",
        source_id=note.id,
        source_note_ids=[note.id],
        source_evidence=[note.path, note.title],
        created_by="system",
        status="confirmed",
        source_quality="vault_note",
        learning_value="source",
        graph_metadata=metadata,
    )


def sync_note_graph_node(session: Session, note: NoteRecord) -> GraphNodeRecord:
    """Materialize the source note before derived graph processing starts."""
    return _upsert_note_node(session, note)


def _upsert_concept(
    session: Session,
    name: str,
    normalized_name: str,
    note_ids: list[int],
    evidence: list[str],
    model: str = "",
) -> ConceptRecord:
    concept = session.execute(
        select(ConceptRecord).where(ConceptRecord.normalized_name == normalized_name)
    ).scalar_one_or_none()
    if concept is None:
        concept = ConceptRecord(name=name, normalized_name=normalized_name)
        session.add(concept)
        session.flush()
    concept.name = name
    concept.description = concept.description or f'Detected concept: "{name}".'
    concept.frequency = len(note_ids)
    concept.related_note_ids = _dump_json(note_ids)
    generated_by_ai = bool(
        model and model not in {"content-analysis", "metadata-parser"}
    )
    concept.extracted_by = "ai" if generated_by_ai else "system"
    estimate = estimate_confidence(
        ConfidenceSignal(1.0, f"source-note:{note_id}") for note_id in note_ids
    )
    persist_confidence(concept, estimate)
    concept.status = "suggested"
    concept.provider = "configured-ai" if generated_by_ai else "deterministic"
    concept.model = model or "metadata-parser"
    concept.source_evidence = _dump_json(evidence[:8])
    concept.updated_at = datetime.now(UTC)
    return concept


def _upsert_concept_node(session: Session, concept: ConceptRecord) -> GraphNodeRecord:
    note_ids = _parse_json_list(concept.related_note_ids)
    from berrybrain_api.graph_write_service import GraphWriteService

    return GraphWriteService(session, autocommit=False).upsert_node(
        node_type="concept",
        label=concept.name,
        title=concept.name,
        summary=concept.description,
        ai_notes=(
            "Subagent concept-extractor: conceptual vertex created from metadata "
            "and concepts extracted from related notes."
        ),
        source="concept_extraction",
        source_id=concept.id,
        source_note_ids=[int(value) for value in note_ids if str(value).isdigit()],
        source_evidence=concept.source_evidence,
        source_quality="extracted",
        learning_value="concept",
        confidence=concept.confidence,
        created_by=concept.extracted_by,
        model=concept.model,
        provider=concept.provider,
        status=concept.status,
        graph_metadata={
            "normalizedName": concept.normalized_name,
            "frequency": concept.frequency,
            "sourceEvidence": _parse_json_list(concept.source_evidence),
            "relatedNoteCount": len(note_ids),
        },
    )


def _upsert_graph_edge(
    session: Session,
    source_node_id: int,
    target_node_id: int,
    edge_type: str,
    label: str,
    reason: str,
    evidence: list[str],
    source_note_ids: list[int],
    created_by: str,
    status: str,
    provider: str = "deterministic",
    model: str = "metadata-parser",
    prompt_version: str = PROMPT_VERSION,
    confidence: float | None = None,
    replace_evidence: bool = False,
) -> GraphEdgeRecord | None:
    if not reason or not evidence:
        return None
    from berrybrain_api.graph_write_service import GraphWriteService

    try:
        return GraphWriteService(session, autocommit=False).upsert_edge(
            source_node_id=source_node_id,
            target_node_id=target_node_id,
            edge_type=edge_type,
            label=label,
            reason=reason,
            evidence=list(evidence),
            source_note_ids=source_note_ids,
            confidence=confidence,
            created_by=created_by,
            provider=provider,
            model=model,
            prompt_version=prompt_version,
            status=status,
            replace_evidence=replace_evidence,
        )
    except HTTPException:
        return None


def _mark_stale_shared_concept_connections(
    session: Session, valid_pairs: set[tuple[int, int]]
) -> int:
    stale_count = 0
    connections = list(
        session.execute(
            select(ConnectionRecord).where(
                ConnectionRecord.connection_type == "shared_concept",
                ConnectionRecord.status.not_in(("ignored", "archived", "stale")),
            )
        ).scalars()
    )
    for connection in connections:
        pair = tuple(sorted((connection.source_note_id, connection.target_note_id)))
        if pair in valid_pairs:
            continue
        connection.status = "stale"
        connection.updated_at = datetime.now(UTC)
        stale_count += 1

    note_nodes = {
        node.id: int(node.source_id or 0)
        for node in session.execute(
            select(GraphNodeRecord).where(GraphNodeRecord.type == "note")
        ).scalars()
    }
    edges = list(
        session.execute(
            select(GraphEdgeRecord).where(
                GraphEdgeRecord.type == "related",
                GraphEdgeRecord.label == "shared concept",
                GraphEdgeRecord.created_by == "system",
                GraphEdgeRecord.status.not_in(("ignored", "archived", "stale")),
            )
        ).scalars()
    )
    for edge in edges:
        source_note_id = note_nodes.get(edge.source_node_id, 0)
        target_note_id = note_nodes.get(edge.target_node_id, 0)
        if not source_note_id or not target_note_id:
            continue
        pair = tuple(sorted((source_note_id, target_note_id)))
        if pair in valid_pairs:
            continue
        edge.status = "stale"
        edge.semantic_status = "quarantined"
        edge.updated_at = datetime.now(UTC)
        stale_count += 1
    if stale_count:
        session.flush()
    return stale_count


def _node_key(node_type: str, source_id: int) -> str:
    return f"{node_type}:{source_id}"


def _display_concept_name(normalized: str) -> str:
    return normalized


def _human_join(items: list[str]) -> str:
    clean = [str(item).strip() for item in items if str(item).strip()]
    if not clean:
        return ""
    if len(clean) == 1:
        return clean[0]
    if len(clean) == 2:
        return f"{clean[0]} and {clean[1]}"
    return f"{', '.join(clean[:-1])}, and {clean[-1]}"


def _minimum_shared_concepts(session: Session) -> int:
    row = session.scalar(
        select(SettingRecord).where(SettingRecord.key == "graph_min_shared_concepts")
    )
    if row is None:
        return 2
    try:
        value = int(decode_setting_value(row.key, row.value))
    except (TypeError, ValueError):
        return 2
    return max(2, min(value, 10))


def _is_specific_concept_label(label: str) -> bool:
    tokens = re.findall(r"[^\W_]+", str(label).casefold(), flags=re.UNICODE)
    return len(tokens) >= 2
