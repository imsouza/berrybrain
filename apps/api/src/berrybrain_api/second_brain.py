from __future__ import annotations

import json
import re
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from berrybrain_api.ai_gateway import (
    GraphAIUnavailable,
    generate_graph_answer,
    get_ai_config,
)
from berrybrain_api.concept_extraction import (  # noqa: F401
    _clean_note_text_for_concepts,
    _concepts_from_title,
    _extract_content_concepts,
    _extract_note_concepts,
    _extract_terms_from_metadata_text,
    _extract_values,
    _flatten_metadata_text,
    _is_valid_concept_name,
    _is_valid_topic_name,
    _traceable_content_evidence,
    _unique_concept_names,
    normalize_concept_name,
)
from berrybrain_api.confidence import (
    ConfidenceSignal,
    estimate_confidence,
    evidence_coverage_signal,
    persist_confidence,
    serialize_confidence,
    serialize_estimate,
    serialize_percentage_confidence,
)

# Facade imports for extracted modules
from berrybrain_api.connection_detection import (  # noqa: F401
    _upsert_note_connection,
    generate_inferred_graph_connections,
)
from berrybrain_api.deduplication import (  # noqa: F401
    _delete_duplicate_edges,
    _delete_graph_node_with_edges,
    _merge_duplicate_nodes,
    _prune_generated_graph_insights,
    _prune_generated_typed_nodes,
    _prune_orphan_insight_nodes,
    _prune_stale_concepts,
    _prune_stale_graph_insights,
    _prune_title_duplicate_typed_nodes,
)
from berrybrain_api.graph_contracts import canonical_edge_type, canonical_node_type
from berrybrain_api.graph_expansion import (  # noqa: F401
    _display_concept_name,
    _human_join,
    _node_key,
    _upsert_concept,
    _upsert_concept_node,
    _upsert_graph_edge,
    _upsert_note_node,
    delete_graph_node,
    expand_knowledge_graph,
    set_edge_status,
    set_edge_user_notes,
    set_node_status,
    set_node_user_notes,
)
from berrybrain_api.graph_ontology import validate_node_name
from berrybrain_api.graph_semantic_service import quarantine_generated_candidate
from berrybrain_api.models import (
    ChunkRecord,
    ConceptRecord,
    ConnectionRecord,
    GeneratedMetadataRecord,
    GraphEdgeRecord,
    GraphNodeRecord,
    InsightRecord,
    NoteRecord,
)

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


def _ensure_graph_node_context(session: Session) -> int:
    notes_by_id = {
        note.id: note for note in session.execute(select(NoteRecord)).scalars()
    }
    changed = 0
    from berrybrain_api.graph_write_service import GraphWriteService

    writer = GraphWriteService(session, autocommit=False)
    for node in session.execute(select(GraphNodeRecord)).scalars():
        if node.status == "ignored":
            continue
        source_note_ids = [
            int(item)
            for item in _parse_json_list(node.source_note_ids)
            if str(item).isdigit()
        ]
        related_notes = [
            notes_by_id[note_id].title
            for note_id in source_note_ids
            if note_id in notes_by_id
        ]
        evidence = [
            str(item)
            for item in _parse_json_list(node.source_evidence)
            if str(item).strip()
        ]
        if not evidence:
            evidence = related_notes or ([node.label] if node.label else [])

        ai_summary, ai_context, learning_value = _build_node_context(
            node, related_notes, evidence
        )
        values = {
            "ai_summary": node.ai_summary or ai_summary,
            "ai_context": node.ai_context or ai_context,
            "source_evidence": node.source_evidence or _dump_json(evidence[:12]),
            "learning_value": node.learning_value or learning_value[:20],
            "source_quality": node.source_quality or "contextualized",
            "provider": node.provider or node.created_by or "deterministic",
            "model": node.model or node.created_by_model or PROMPT_VERSION,
            "prompt_version": node.prompt_version or PROMPT_VERSION,
        }
        if any(
            not current
            for current in (
                node.ai_summary,
                node.ai_context,
                node.source_evidence,
                node.learning_value,
                node.source_quality,
                node.provider,
                node.model,
                node.prompt_version,
                node.generated_at,
            )
        ):
            writer.update_node_enrichment(node.id, values)
            changed += 1
    return changed


def _build_node_context(
    node: GraphNodeRecord, related_notes: list[str], evidence: list[str]
) -> tuple[str, str, str]:
    label = node.label or node.title or "Untitled node"
    note_text = _human_join(related_notes[:4]) if related_notes else "the current vault"
    evidence_text = _human_join(evidence[:4]) if evidence else label
    node_type = (node.type or "node").lower()

    if node_type == "note":
        summary = node.summary or f'"{label}" is a source note from the vault.'
        context = (
            f"This note is a primary knowledge source. BerryBrain uses it to extract "
            f"concepts, backlinks, evidence, and graph connections. Evidence: {evidence_text}."
        )
        return summary, context, "source"

    if node_type == "concept":
        summary = (
            node.summary or f'"{label}" is a recurring concept grounded in {note_text}.'
        )
        context = (
            f"This concept helps connect notes that discuss the same idea. It should be "
            f"reviewed as a possible permanent note when it appears across multiple sources. "
            f"Evidence: {evidence_text}."
        )
        return summary, context, "concept"

    if node_type == "topic":
        summary = node.summary or f'"{label}" is a topic detected from {note_text}.'
        context = (
            f"This topic groups nearby ideas from the source material. It is useful when "
            f"it explains what area of study the related notes belong to. Evidence: {evidence_text}."
        )
        return summary, context, "topic"

    if node_type == "entity":
        summary = node.summary or f'"{label}" is an entity mentioned in {note_text}.'
        context = (
            f"This entity can anchor references to people, tools, systems, projects, or named "
            f"objects across the graph. Evidence: {evidence_text}."
        )
        return summary, context, "entity"

    if node_type == "context":
        summary = node.summary or f'"{label}" is a context inferred from {note_text}.'
        context = (
            f"This context explains the situation or domain where related concepts are being "
            f"used. It helps BerryBrain answer why notes belong together. Evidence: {evidence_text}."
        )
        return summary, context, "context"

    if node_type == "gap":
        summary = (
            node.summary or f'"{label}" is a knowledge gap detected in {note_text}.'
        )
        context = (
            f"This gap marks a missing explanation, bridge, or source that would improve the "
            f"knowledge graph. Treat it as a candidate for a new note or study path. Evidence: {evidence_text}."
        )
        return summary, context, "gap"

    if node_type == "source":
        summary = node.summary or f'"{label}" is a referenced source from {note_text}.'
        context = (
            f"This source node preserves where knowledge came from and can be validated or "
            f"revisited later. Evidence: {evidence_text}."
        )
        return summary, context, "source"

    if node_type == "attachment":
        summary = node.summary or f'"{label}" is an attachment linked to {note_text}.'
        context = (
            f"This attachment is treated as supporting material for the related note. Extracted "
            f"text or future OCR/transcription can feed the Knowledge Base and graph. Evidence: {evidence_text}."
        )
        return summary, context, "attachment"

    if node_type == "insight":
        summary = (
            node.summary or f'"{label}" is an insight generated from vault evidence.'
        )
        context = (
            f"This insight exists to explain a pattern, gap, hypothesis, or action derived "
            f"from notes and graph evidence. Evidence: {evidence_text}."
        )
        return summary, context, "insight"

    summary = node.summary or f'"{label}" is a graph node grounded in {note_text}.'
    context = (
        f"This node exists because BerryBrain found evidence in the knowledge base or graph. "
        f"Evidence: {evidence_text}."
    )
    return summary, context, "knowledge"


def _ensure_graph_edge_traceability(session: Session) -> int:
    nodes_by_id = {
        node.id: node for node in session.execute(select(GraphNodeRecord)).scalars()
    }
    notes_by_id = {
        note.id: note for note in session.execute(select(NoteRecord)).scalars()
    }
    changed = 0
    from berrybrain_api.graph_write_service import GraphWriteService

    writer = GraphWriteService(session, autocommit=False)
    for edge in session.execute(select(GraphEdgeRecord)).scalars():
        if edge.status == "ignored":
            continue
        # AI edges are validated or quarantined by the chunk-evidence migration below.
        if edge.created_by == "ai":
            continue
        source = nodes_by_id.get(edge.source_node_id)
        target = nodes_by_id.get(edge.target_node_id)
        if source is None or target is None:
            continue
        source_note_ids = [
            int(item)
            for item in _parse_json_list(edge.source_note_ids)
            if str(item).isdigit()
        ]
        note_titles = [
            notes_by_id[note_id].title
            for note_id in source_note_ids
            if note_id in notes_by_id
        ]
        evidence = [
            str(item) for item in _parse_json_list(edge.evidence) if str(item).strip()
        ]
        if not evidence:
            evidence = note_titles or [source.label, target.label]

        if any(
            value in (None, "", "[]")
            for value in (
                edge.label,
                edge.reason,
                edge.evidence,
                edge.status,
                edge.created_by,
                edge.provider,
                edge.model,
                edge.prompt_version,
            )
        ):
            edge_evidence: list[dict[str, Any] | str] = list(evidence[:12])
            writer.upsert_edge(
                source_node_id=edge.source_node_id,
                target_node_id=edge.target_node_id,
                edge_type=edge.type,
                label=edge.label or edge.type.replace("_", " "),
                reason=edge.reason
                or (
                    f'"{source.label}" connects to "{target.label}" through '
                    f"{edge.type.replace('_', ' ')} evidence."
                ),
                evidence=edge_evidence,
                source_note_ids=source_note_ids,
                confidence=edge.confidence
                if edge.confidence is not None
                else (1.0 if edge.status == "confirmed" else 0.7),
                status=edge.status or "suggested",
                created_by="legacy_ai"
                if edge.created_by == "ai"
                else (edge.created_by or "system"),
                provider=edge.provider or "deterministic",
                model=edge.model or edge.created_by_model or PROMPT_VERSION,
                prompt_version=edge.prompt_version or PROMPT_VERSION,
            )
            changed += 1
    if changed:
        writer.deduplicate_edges()
    return changed


def _migrate_active_ai_edge_evidence(session: Session) -> dict[str, int]:
    from berrybrain_api.graph_write_service import (
        GraphWriteService,
        has_traceable_ai_evidence,
    )

    writer = GraphWriteService(session, autocommit=False)
    nodes = {
        node.id: node for node in session.execute(select(GraphNodeRecord)).scalars()
    }
    notes = {note.id: note for note in session.execute(select(NoteRecord)).scalars()}
    recovered = 0
    stale = 0
    for edge in session.execute(
        select(GraphEdgeRecord).where(
            GraphEdgeRecord.created_by == "ai",
            GraphEdgeRecord.status.not_in(("ignored", "archived", "stale")),
            GraphEdgeRecord.semantic_status == "active",
        )
    ).scalars():
        if has_traceable_ai_evidence(edge):
            continue
        note_ids = {
            int(value)
            for value in _parse_json_list(edge.source_note_ids)
            if str(value).isdigit()
        }
        for node_id in (edge.source_node_id, edge.target_node_id):
            node = nodes.get(node_id)
            if node is None:
                continue
            note_ids.update(
                int(value)
                for value in _parse_json_list(node.source_note_ids)
                if str(value).isdigit()
            )
        selected_ids = [note_id for note_id in sorted(note_ids) if note_id in notes][:2]
        chunks: list[ChunkRecord] = []
        for note_id in selected_ids:
            note = notes[note_id]
            chunk = (
                session.execute(
                    select(ChunkRecord)
                    .where(
                        ChunkRecord.note_id == note_id,
                        ChunkRecord.content_hash == note.content_hash,
                    )
                    .order_by(ChunkRecord.chunk_index)
                )
                .scalars()
                .first()
            )
            if chunk is not None:
                chunks.append(chunk)
        if len(chunks) != 2:
            writer.set_edge_status(edge.id, "stale")
            stale += 1
            continue
        source_chunk, target_chunk = chunks
        evidence = {
            "sourceNoteId": source_chunk.note_id,
            "targetNoteId": target_chunk.note_id,
            "sourceChunkId": source_chunk.id,
            "targetChunkId": target_chunk.id,
            "startLine": source_chunk.start_line,
            "endLine": source_chunk.end_line,
            "excerpt": f"{source_chunk.text[:240]} | {target_chunk.text[:240]}",
            "hash": f"{source_chunk.content_hash}:{target_chunk.content_hash}",
        }
        edge.type = canonical_edge_type(edge.type)
        writer.upsert_edge(
            source_node_id=edge.source_node_id,
            target_node_id=edge.target_node_id,
            edge_type=edge.type,
            label=edge.label,
            reason=edge.reason
            or "Legacy AI relation recovered from current note chunks.",
            evidence=[evidence],
            source_note_ids=selected_ids,
            confidence=(
                edge.confidence if getattr(edge, "confidence_sample_size", 0) else None
            ),
            status=edge.status or "suggested",
            created_by="ai",
            provider=edge.provider or "legacy-ai",
            model=edge.model or edge.created_by_model or "legacy-ai",
            prompt_version=edge.prompt_version or "graph-evidence-migration.v1",
            pipeline_run_id=f"graph-evidence-migration:{uuid4()}",
        )
        recovered += 1
    return {"recovered": recovered, "stale": stale}


def infer_from_graph(session: Session, question: str) -> dict[str, Any]:
    tokens = _tokenize(question)
    if not tokens:
        return _insufficient(question)

    notes = list(session.execute(select(NoteRecord)).scalars())
    note_by_id = {note.id: note for note in notes}
    connections = list(
        session.execute(
            select(ConnectionRecord)
            .where(ConnectionRecord.status != "ignored")
            .order_by(ConnectionRecord.confidence.desc())
        ).scalars()
    )

    matches: list[tuple[int, ConnectionRecord, NoteRecord, NoteRecord]] = []
    for conn in connections:
        source = note_by_id.get(conn.source_note_id)
        target = note_by_id.get(conn.target_note_id)
        if source is None or target is None:
            continue
        haystack = " ".join([source.title, target.title, conn.reason, conn.evidence])
        score = len(tokens & _tokenize(haystack))
        if score >= 2:
            matches.append((score, conn, source, target))

    edges = list(
        session.execute(
            select(GraphEdgeRecord)
            .where(
                GraphEdgeRecord.status != "ignored",
                GraphEdgeRecord.semantic_status == "active",
            )
            .order_by(GraphEdgeRecord.confidence.desc())
        ).scalars()
    )
    graph_nodes = list(
        session.execute(
            select(GraphNodeRecord).where(GraphNodeRecord.semantic_status == "active")
        ).scalars()
    )
    node_by_id = {node.id: node for node in graph_nodes}
    edge_matches: list[
        tuple[int, GraphEdgeRecord, GraphNodeRecord, GraphNodeRecord]
    ] = []
    for edge in edges:
        graph_source = node_by_id.get(edge.source_node_id)
        graph_target = node_by_id.get(edge.target_node_id)
        if graph_source is None or graph_target is None:
            continue
        haystack = " ".join(
            [
                graph_source.label,
                graph_target.label,
                edge.type,
                edge.reason or "",
                edge.evidence or "",
            ]
        )
        score = len(tokens & _tokenize(haystack))
        if score >= 2:
            edge_matches.append((score, edge, graph_source, graph_target))

    if not matches and not edge_matches:
        return _insufficient(question)

    best_conn_score = max((m[0] for m in matches), default=0)
    best_edge_score = max((m[0] for m in edge_matches), default=0)

    if best_edge_score >= best_conn_score and edge_matches:
        edge_matches.sort(
            key=lambda item: (item[0], item[1].confidence or 0), reverse=True
        )
        _, edge, graph_source, graph_target = edge_matches[0]
        evidence = _parse_json_list(edge.evidence) or [
            graph_source.label,
            graph_target.label,
        ]
        return {
            "status": "answered",
            "question": question,
            "answer": edge.reason
            or f"{graph_source.label} is connected to {graph_target.label}.",
            "confidence": edge.confidence if edge.confidence_sample_size else None,
            "confidenceInterval": serialize_confidence(edge),
            "relatedNodes": [graph_source.label, graph_target.label],
            "connections": [
                {
                    "id": edge.id,
                    "type": edge.type,
                    "reason": edge.reason,
                    "confidence": edge.confidence,
                }
            ],
            "evidence": evidence,
            "actions": [
                "Highlight in graph",
                "Create insight",
                "Create permanent note",
                "Generate review",
            ],
        }

    matches.sort(key=lambda item: (item[0], item[1].confidence), reverse=True)
    _, conn, source, target = matches[0]
    evidence = _parse_json_list(conn.evidence) or [source.title, target.title]
    return {
        "status": "answered",
        "question": question,
        "answer": conn.reason,
        "confidence": (conn.confidence or 0) / 100
        if conn.confidence_sample_size
        else None,
        "confidenceInterval": serialize_percentage_confidence(conn),
        "relatedNodes": [source.title, target.title],
        "connections": [
            {
                "id": conn.id,
                "type": conn.connection_type,
                "reason": conn.reason,
                "confidence": conn.confidence,
            }
        ],
        "evidence": evidence,
        "actions": [
            "Highlight in graph",
            "Create insight",
            "Create permanent note",
            "Generate review",
        ],
    }


def _generate_deterministic_insights(session: Session) -> int:
    """Create learner-facing insights only when note evidence is concrete."""
    notes = list(session.execute(select(NoteRecord)).scalars())
    note_by_id = {note.id: note for note in notes}
    concepts = list(session.execute(select(ConceptRecord)).scalars())
    created_or_updated = 0

    for concept in concepts:
        visible_concept_node = session.execute(
            select(GraphNodeRecord).where(
                GraphNodeRecord.type == "concept",
                GraphNodeRecord.source_id == concept.id,
                GraphNodeRecord.status != "ignored",
                GraphNodeRecord.semantic_status == "active",
            )
        ).scalar_one_or_none()
        if visible_concept_node is None:
            continue
        note_ids = [
            note_id
            for note_id in _parse_json_list(concept.related_note_ids)
            if isinstance(note_id, int) and note_id in note_by_id
        ]
        if len(note_ids) < 2:
            continue
        related = [note_by_id[note_id] for note_id in note_ids[:4]]
        title = f'Connection pattern: "{concept.name}" links {len(note_ids)} notes'
        description = (
            f'The concept "{concept.name}" appears across '
            + ", ".join(note.title for note in related)
            + ". This is a real overlap in the current vault, not a system diagnostic."
        )
        insight = _upsert_content_insight(
            session,
            insight_type="new_connection",
            title=title,
            description=description,
            related_note_ids=note_ids,
            evidence=[f"{note.title}: {concept.name}" for note in related],
            why_it_matters=(
                "Repeated concepts indicate material that can be connected into a "
                "study path or permanent note."
            ),
            suggested_action=(
                f'Open the related notes and create a bridge note around "{concept.name}".'
            ),
            graph_impact=(
                f'Keeps "{concept.name}" as a concept node and connects it to the '
                "source notes that support it."
            ),
            priority=7,
        )
        if insight:
            created_or_updated += 1

    graph_nodes = list(
        session.execute(
            select(GraphNodeRecord).where(
                GraphNodeRecord.type == "note",
                GraphNodeRecord.status != "ignored",
            )
        ).scalars()
    )
    graph_edges = list(
        session.execute(
            select(GraphEdgeRecord).where(GraphEdgeRecord.status != "ignored")
        ).scalars()
    )
    connected_ids = {edge.source_node_id for edge in graph_edges} | {
        edge.target_node_id for edge in graph_edges
    }
    isolated = [node for node in graph_nodes if node.id not in connected_ids]
    for node in isolated[:3]:
        title = f'Knowledge gap: "{node.label}" is still isolated'
        note_ids = [
            note_id
            for note_id in _parse_json_list(node.source_note_ids)
            if isinstance(note_id, int)
        ]
        insight = _upsert_content_insight(
            session,
            insight_type="knowledge_gap",
            title=title,
            description=(
                f'The note "{node.label}" exists in the vault but has no visible '
                "knowledge connection yet."
            ),
            related_note_ids=note_ids,
            evidence=[node.label, node.source_evidence or node.summary],
            why_it_matters=(
                "Isolated notes are harder to reuse because they do not yet explain "
                "how they relate to the rest of the vault."
            ),
            suggested_action=(
                "Add links, tags, or a short context paragraph so BerryBrain can "
                "connect this note to nearby ideas."
            ),
            graph_impact="Marks an orphan note that needs more context or connections.",
            priority=5,
        )
        if insight:
            created_or_updated += 1

    return created_or_updated


def _generate_graph_insights(
    session: Session, insight_ids: set[int] | None = None
) -> int:
    query = select(InsightRecord)
    if insight_ids is not None:
        query = query.where(InsightRecord.id.in_(insight_ids))
    insights = list(session.execute(query).scalars())
    for insight in insights:
        if not _is_graph_worthy_insight(insight):
            stale = session.execute(
                select(GraphNodeRecord).where(
                    GraphNodeRecord.type == "insight",
                    GraphNodeRecord.source == "insight",
                    GraphNodeRecord.source_id == insight.id,
                )
            ).scalar_one_or_none()
            if stale:
                _delete_graph_node_with_edges(session, stale)
            continue
        existing = session.execute(
            select(GraphNodeRecord).where(
                GraphNodeRecord.type == "insight",
                GraphNodeRecord.source == "insight",
                GraphNodeRecord.source_id == insight.id,
            )
        ).scalar_one_or_none()
        if existing:
            _connect_insight_to_sources(session, insight, existing)
            continue
        related_ids = _parse_json_list(insight.related_notes)
        graph_status = (
            "confirmed"
            if (insight.status or "") in {"accepted", "applied", "reviewed"}
            else (insight.status or "suggested")
        )
        node = _upsert_typed_node(
            session,
            "insight",
            insight.title[:120],
            insight.title,
            insight.description or "",
            "insight",
            insight.id,
            related_ids,
            _parse_json_list(insight.evidence),
            "ai"
            if insight.provider and insight.provider != "deterministic"
            else "system",
            confidence=(insight.confidence if insight.confidence_sample_size else None),
            status=graph_status,
            model=insight.model or "graph-insight.v1",
        )
        if node is None:
            continue
        _connect_insight_to_sources(session, insight, node)

    return 0


def _upsert_content_insight(
    session: Session,
    insight_type: str,
    title: str,
    description: str,
    related_note_ids: list[int],
    evidence: list[str],
    why_it_matters: str,
    suggested_action: str,
    graph_impact: str,
    priority: int = 0,
) -> InsightRecord | None:
    if len([item for item in evidence if str(item or "").strip()]) < 2:
        return None
    existing = session.execute(
        select(InsightRecord).where(
            InsightRecord.title == title,
            InsightRecord.type == insight_type,
        )
    ).scalar_one_or_none()
    insight = existing or InsightRecord(type=insight_type, title=title)
    if existing is None:
        session.add(insight)
        session.flush()
    insight.description = description
    insight.related_notes = _dump_json(sorted(set(related_note_ids)))
    insight.priority = priority
    insight.why_it_matters = why_it_matters
    insight.evidence = _dump_json(evidence[:8])
    insight.suggested_action = suggested_action
    insight.graph_impact = graph_impact
    signals = [
        ConfidenceSignal(1.0, f"insight-evidence:{index}:{item}")
        for index, item in enumerate(evidence[:8])
    ]
    signals.extend(
        ConfidenceSignal(1.0, f"related-note:{note_id}")
        for note_id in sorted(set(related_note_ids))
    )
    coverage_signal = evidence_coverage_signal(
        [title, description, why_it_matters, suggested_action, graph_impact],
        evidence,
    )
    if coverage_signal is not None:
        signals.append(coverage_signal)
    persist_confidence(insight, estimate_confidence(signals))
    insight.status = (
        insight.status if insight.status in {"applied", "ignored"} else "suggested"
    )
    insight.provider = "content-analysis"
    insight.model = "deterministic-knowledge-insights.v1"
    insight.prompt_version = "content-insight.v1"
    insight.reasoning = "Generated from shared concepts and graph structure using vault notes as evidence."
    insight.source_context = _dump_json({"source": "knowledge_graph"})
    insight.updated_at = datetime.now(UTC)
    return insight


def _is_graph_worthy_insight(insight: InsightRecord) -> bool:
    if getattr(insight, "dismissed_at", None) is not None:
        return False
    if (insight.status or "") in {
        "ignored",
        "archived",
        "expired",
        "dismissed",
    }:
        return False
    if (getattr(insight, "type", "") or "").lower() in {
        "system_diagnostic",
        "pipeline_bottleneck",
        "provider_issue",
        "job_backlog",
        "worker_status",
    }:
        return False
    evidence = _parse_json_list(insight.evidence)
    combined = " ".join(
        [
            insight.title or "",
            insight.description or "",
            getattr(insight, "why_it_matters", "") or "",
            getattr(insight, "suggested_action", "") or "",
            getattr(insight, "graph_impact", "") or "",
            " ".join(str(item) for item in evidence),
        ]
    ).lower()
    if any(
        term in combined
        for term in (
            "explainedconnections",
            "graphnotes",
            "jobsbytype",
            "generate_note_title",
            "enrich_graph_node",
            "semanticstate",
            "raw json",
            "pipeline bottleneck",
            "jobrecord",
        )
    ):
        return False
    if len(evidence) < 2:
        return False
    required_text = [
        insight.title,
        insight.description,
        getattr(insight, "why_it_matters", ""),
        getattr(insight, "suggested_action", ""),
        getattr(insight, "graph_impact", ""),
    ]
    if any(not (value or "").strip() for value in required_text):
        return False
    return (insight.title or "").strip() != (insight.description or "").strip()


def _connect_insight_to_sources(
    session: Session, insight: InsightRecord, insight_node: GraphNodeRecord
) -> int:
    targets = _resolve_insight_source_nodes(session, insight, insight_node.id)
    evidence = _insight_evidence_strings(insight)[:8]
    created = 0
    for target in targets[:8]:
        source_note_ids = sorted(
            {
                int(item)
                for item in _parse_json_list(target.source_note_ids)
                if str(item).isdigit()
            }
        )
        edge = _upsert_graph_edge(
            session,
            insight_node.id,
            target.id,
            "insight_suggested",
            "insight citation",
            (
                f'The insight "{insight.title}" cites "{target.label}" as part '
                "of its supporting evidence."
            ),
            evidence or [insight.title, target.label],
            source_note_ids,
            "system",
            "confirmed"
            if (
                insight_node.status == "confirmed"
                or insight.status in {"confirmed", "applied"}
            )
            else "suggested",
            provider=insight.provider or "unknown",
            model=insight.model or "insight-generate.v2",
            prompt_version=insight.prompt_version or "insight-generate.v2",
            confidence=(insight.confidence if insight.confidence_sample_size else None),
        )
        if edge is not None:
            created += 1
    return created


def _resolve_insight_source_nodes(
    session: Session, insight: InsightRecord, insight_node_id: int
) -> list[GraphNodeRecord]:
    evidence_text = "\n".join(_insight_evidence_strings(insight))
    targets: dict[int, GraphNodeRecord] = {}

    for match in re.finditer(
        r"\b(?:note|concept|topic|context|entity|gap|source)_(\d+)\b",
        evidence_text,
        re.IGNORECASE,
    ):
        node = session.get(GraphNodeRecord, int(match.group(1)))
        if node is not None and node.id != insight_node_id and node.status != "ignored":
            targets[node.id] = node

    edge_ids = {
        int(match.group(1))
        for match in re.finditer(
            r"\b(?:edge\s+id|connection\s+id|edge|connection)\s*[_#:]?\s*(\d+)\b",
            evidence_text,
            re.IGNORECASE,
        )
    }
    if edge_ids:
        edges = list(
            session.execute(
                select(GraphEdgeRecord).where(GraphEdgeRecord.id.in_(edge_ids))
            ).scalars()
        )
        for edge in edges:
            for node_id in (edge.source_node_id, edge.target_node_id):
                node = session.get(GraphNodeRecord, node_id)
                if (
                    node is not None
                    and node.id != insight_node_id
                    and node.status != "ignored"
                    and node.semantic_status == "active"
                ):
                    targets[node.id] = node

    normalized_evidence = normalize_concept_name(evidence_text)
    if normalized_evidence:
        nodes = list(
            session.execute(
                select(GraphNodeRecord).where(
                    GraphNodeRecord.status != "ignored",
                    GraphNodeRecord.semantic_status == "active",
                )
            ).scalars()
        )
        for node in nodes:
            if node.id == insight_node_id:
                continue
            label = normalize_concept_name(node.label)
            title = normalize_concept_name(node.title or "")
            if (label and label in normalized_evidence) or (
                title and title in normalized_evidence
            ):
                targets[node.id] = node
            if len(targets) >= 8:
                break

    return list(targets.values())


def _insight_evidence_strings(insight: InsightRecord) -> list[str]:
    values = []
    for item in _parse_json_list(insight.evidence):
        if isinstance(item, dict):
            values.append(_dump_json(item))
        elif item:
            values.append(str(item))
    return values


async def infer_from_graph_with_ai(session: Session, question: str) -> dict[str, Any]:
    evidence_base = infer_from_graph(session, question)
    if evidence_base["status"] != "answered":
        evidence_base = _build_graph_context_for_ai(session, question)
    if evidence_base["status"] == "insufficient_evidence":
        return evidence_base

    config = get_ai_config(session)
    system = (
        "You are BerryBrain's graph inference module. "
        "Answer in English using only the provided evidence. "
        "If the evidence does not support the answer, return status insufficient_evidence. "
        "Return JSON with: status, answer, evidence, relatedNodes, suggestions."
    )
    prompt = _dump_json(
        {
            "question": question,
            "graphEvidence": evidence_base,
            "configuredProvider": config.get("provider", ""),
            "configuredModel": config.get("cloud_model")
            or config.get("ollama_model")
            or "",
            "rules": [
                "Do not invent connections without evidence.",
                "Cite the evidence used.",
                "Keep the answer short and actionable.",
                "If the question asks for search/listing, use the provided nodes and edges.",
            ],
        }
    )
    try:
        ai_result = await generate_graph_answer(config, prompt, system)
    except (GraphAIUnavailable, Exception) as exc:
        return {
            **evidence_base,
            "status": "waiting_provider",
            "answer": f"Configured AI is unavailable for graph inference: {exc}",
            "provider": config.get("provider", ""),
            "model": config.get("cloud_model") or config.get("ollama_model") or "",
        }

    status = str(ai_result.get("status") or "answered")
    evidence = ai_result.get("evidence")
    if not isinstance(evidence, list) or not evidence:
        return {
            **evidence_base,
            "status": "insufficient_evidence",
            "answer": "The AI did not return enough evidence to support this inference.",
            "provider": config.get("provider", ""),
            "model": config.get("cloud_model") or config.get("ollama_model") or "",
        }
    return {
        **evidence_base,
        "status": status,
        "answer": str(ai_result.get("answer") or evidence_base["answer"]),
        "evidence": evidence,
        "relatedNodes": ai_result.get("relatedNodes")
        if isinstance(ai_result.get("relatedNodes"), list)
        else evidence_base.get("relatedNodes", []),
        "suggestions": ai_result.get("suggestions", []),
        "provider": config.get("provider", ""),
        "model": config.get("cloud_model") or config.get("ollama_model") or "",
    }


def _build_graph_context_for_ai(session: Session, question: str) -> dict[str, Any]:
    tokens = _tokenize(question)
    nodes = list(
        session.execute(
            select(GraphNodeRecord).where(
                GraphNodeRecord.status != "ignored",
                GraphNodeRecord.semantic_status == "active",
            )
        ).scalars()
    )
    edges = list(
        session.execute(
            select(GraphEdgeRecord).where(
                GraphEdgeRecord.status != "ignored",
                GraphEdgeRecord.semantic_status == "active",
            )
        ).scalars()
    )
    if not nodes:
        notes = list(session.execute(select(NoteRecord)).scalars())
        if not notes:
            return _insufficient(question)
        note_evidence = [f"Note: {note.title} ({note.path})" for note in notes[:12]]
        estimate = estimate_confidence(
            ConfidenceSignal(1.0, f"source-note:{note.id}") for note in notes[:12]
        )
        return {
            "status": "context_ready",
            "question": question,
            "answer": "",
            "confidence": estimate.score,
            "confidenceInterval": serialize_estimate(estimate),
            "relatedNodes": [note.title for note in notes[:12]],
            "connections": [],
            "evidence": note_evidence,
            "graphContext": {
                "nodes": [
                    {
                        "id": f"note_{note.id}",
                        "type": "note",
                        "label": note.title,
                        "path": note.path,
                    }
                    for note in notes[:12]
                ],
                "edges": [],
            },
            "actions": [
                "Highlight in graph",
                "Create insight",
                "Create permanent note",
            ],
        }

    node_by_id = {node.id: node for node in nodes}
    scored_nodes: list[tuple[int, GraphNodeRecord]] = []
    for node in nodes:
        haystack = " ".join(
            [
                node.label,
                getattr(node, "title", ""),
                getattr(node, "summary", ""),
                getattr(node, "ai_notes", ""),
                getattr(node, "graph_metadata", ""),
            ]
        )
        score = len(tokens & _tokenize(haystack)) if tokens else 0
        scored_nodes.append((score, node))
    scored_nodes.sort(key=lambda item: (item[0], item[1].confidence), reverse=True)

    scored_edges: list[tuple[int, GraphEdgeRecord]] = []
    for edge in edges:
        source = node_by_id.get(edge.source_node_id)
        target = node_by_id.get(edge.target_node_id)
        haystack = " ".join(
            [
                source.label if source else "",
                target.label if target else "",
                edge.type,
                edge.reason,
                edge.evidence,
                getattr(edge, "ai_notes", ""),
            ]
        )
        score = len(tokens & _tokenize(haystack)) if tokens else 0
        scored_edges.append((score, edge))
    scored_edges.sort(key=lambda item: (item[0], item[1].confidence), reverse=True)

    matched_nodes = [node for score, node in scored_nodes if score > 0][:12]
    matched_edges = [edge for score, edge in scored_edges if score > 0][:12]
    if not matched_nodes:
        matched_nodes = [node for _, node in scored_nodes[:12]]
    if not matched_edges:
        matched_edges = [edge for _, edge in scored_edges[:12]]
    if not matched_nodes and not matched_edges:
        return _insufficient(question)

    context_nodes = [
        {
            "id": node.id,
            "type": node.type,
            "label": node.label,
            "summary": node.summary,
            "status": node.status,
            "confidence": node.confidence,
            "sourceNoteIds": _parse_json_list(node.source_note_ids),
            "aiNotes": getattr(node, "ai_notes", ""),
        }
        for node in matched_nodes
    ]
    context_edges = []
    evidence: list[str] = []
    for edge in matched_edges:
        source = node_by_id.get(edge.source_node_id)
        target = node_by_id.get(edge.target_node_id)
        item = {
            "id": edge.id,
            "type": edge.type,
            "source": source.label if source else str(edge.source_node_id),
            "target": target.label if target else str(edge.target_node_id),
            "reason": edge.reason,
            "evidence": _parse_json_list(edge.evidence),
            "confidence": edge.confidence,
            "status": edge.status,
            "aiNotes": getattr(edge, "ai_notes", ""),
        }
        context_edges.append(item)
        evidence.append(f"{item['source']} -> {item['target']}: {edge.reason}")

    if not evidence:
        evidence = [f"{node.type}: {node.label}" for node in matched_nodes[:8]]

    confidence_signals = [
        ConfidenceSignal(node.confidence, f"graph-node:{node.id}")
        for node in matched_nodes
        if node.confidence_sample_size
    ]
    confidence_signals.extend(
        ConfidenceSignal(edge.confidence, f"graph-edge:{edge.id}")
        for edge in matched_edges
        if edge.confidence_sample_size
    )
    estimate = estimate_confidence(confidence_signals)
    return {
        "status": "context_ready",
        "question": question,
        "answer": "",
        "confidence": estimate.score,
        "confidenceInterval": serialize_estimate(estimate),
        "relatedNodes": [node["label"] for node in context_nodes],
        "connections": context_edges,
        "evidence": evidence[:12],
        "graphContext": {"nodes": context_nodes, "edges": context_edges},
        "actions": ["Highlight in graph", "Create insight", "Create permanent note"],
    }


def summarize_graph(session: Session) -> dict[str, Any]:
    nodes = list(
        session.execute(
            select(GraphNodeRecord).where(
                GraphNodeRecord.status != "ignored",
                GraphNodeRecord.semantic_status == "active",
            )
        ).scalars()
    )
    node_ids = {node.id for node in nodes}
    edges = list(
        session.execute(
            select(GraphEdgeRecord).where(
                GraphEdgeRecord.status != "ignored",
                GraphEdgeRecord.semantic_status == "active",
            )
        ).scalars()
    )
    edges = [
        edge
        for edge in edges
        if edge.source_node_id in node_ids and edge.target_node_id in node_ids
    ]
    degrees: dict[int, int] = defaultdict(int)
    for edge in edges:
        degrees[edge.source_node_id] += 1
        degrees[edge.target_node_id] += 1
    return {
        "nodes": len(nodes),
        "edges": len(edges),
        "orphans": sum(1 for node in nodes if degrees.get(node.id, 0) == 0),
        "clusters": _estimate_clusters(nodes, edges),
        "centralNotes": [
            {"id": node_id, "degree": degree}
            for node_id, degree in sorted(
                degrees.items(), key=lambda item: item[1], reverse=True
            )[:5]
        ],
    }


def get_node_summary(session: Session, node_id: int) -> dict[str, Any]:
    from berrybrain_api.graph_feedback import (
        node_artifact_key,
        node_source_note_ids,
        resolve_feedback,
    )
    from berrybrain_api.semantic_enrichment import source_fingerprint

    node = session.get(GraphNodeRecord, node_id)
    if node is None:
        raise HTTPException(status_code=404, detail="Graph node not found")
    note_ids = _parse_json_list(node.source_note_ids)
    notes = [
        session.get(NoteRecord, note_id)
        for note_id in note_ids
        if isinstance(note_id, int)
    ]
    note_records: list[NoteRecord] = [note for note in notes if note is not None]
    edges = list(
        session.execute(
            select(GraphEdgeRecord).where(
                (GraphEdgeRecord.source_node_id == node.id)
                | (GraphEdgeRecord.target_node_id == node.id),
                GraphEdgeRecord.status != "ignored",
                GraphEdgeRecord.semantic_status == "active",
            )
        ).scalars()
    )
    edge_types: dict[str, int] = {}
    for edge in edges:
        edge_types[edge.type] = edge_types.get(edge.type, 0) + 1
    synthetic_summary = node.summary or _build_node_summary(
        node, note_records, edges, edge_types
    )
    feedback = resolve_feedback(
        session,
        artifact_kind="node",
        artifact_key=node_artifact_key(node.type, node.label),
        source_note_ids=node_source_note_ids(node),
    )

    return {
        "id": node.id,
        "type": node.type,
        "label": node.label,
        "title": node.title or node.label,
        "summary": synthetic_summary,
        "source": node.source,
        "sourceNoteIds": note_ids,
        "sourceFingerprint": source_fingerprint(session, node),
        "confidence": node.confidence if node.confidence_sample_size else None,
        "confidenceInterval": serialize_confidence(node),
        "createdBy": node.created_by,
        "createdByModel": node.created_by_model,
        "status": node.status,
        "aiNotes": getattr(node, "ai_notes", ""),
        "userNotes": getattr(node, "user_notes", ""),
        "aiContext": getattr(node, "ai_context", ""),
        "aiSummary": getattr(node, "ai_summary", ""),
        "sourceEvidence": getattr(node, "source_evidence", ""),
        "learningValue": getattr(node, "learning_value", ""),
        "sourceQuality": getattr(node, "source_quality", ""),
        "validationStatus": getattr(node, "validation_status", "unvalidated"),
        "provider": getattr(node, "provider", ""),
        "model": getattr(node, "model", ""),
        "promptVersion": getattr(node, "prompt_version", ""),
        "semanticState": getattr(node, "semantic_state", "pending"),
        "semanticProfileVersion": getattr(node, "semantic_profile_version", 0),
        "clusterId": getattr(node, "cluster_id", None),
        "colorId": getattr(node, "color_id", "pending"),
        "colorConfidence": getattr(node, "color_confidence", 0.0),
        "colorReason": getattr(node, "color_reason", ""),
        "semanticStatus": getattr(node, "semantic_status", "active"),
        "ontology": {
            "class": getattr(node, "ontology_class", ""),
            "canonicalLabel": getattr(node, "canonical_label", ""),
        },
        "generatedAt": node.generated_at.isoformat()
        if getattr(node, "generated_at", None)
        else None,
        "metadata": _parse_json_object(node.graph_metadata),
        "notes": [
            {"id": note.id, "title": note.title, "path": note.path}
            for note in note_records
        ],
        "connections": [_serialize_edge(edge) for edge in edges],
        "whyThisExists": _why_node_exists(node, note_records),
        "feedback": (
            {
                "action": feedback.action,
                "recordId": feedback.record_id,
                "suppresses": feedback.suppresses,
                "scope": "source_context",
            }
            if feedback
            else None
        ),
    }


def _serialize_edge(edge: GraphEdgeRecord) -> dict[str, Any]:
    return {
        "id": edge.id,
        "sourceNodeId": edge.source_node_id,
        "targetNodeId": edge.target_node_id,
        "type": edge.type,
        "label": edge.label,
        "reason": edge.reason,
        "evidence": _parse_json_list(edge.evidence),
        "aiNotes": edge.ai_notes,
        "userNotes": getattr(edge, "user_notes", ""),
        "confidence": edge.confidence if edge.confidence_sample_size else None,
        "confidenceInterval": serialize_confidence(edge),
        "status": edge.status,
        "semanticStatus": getattr(edge, "semantic_status", "active"),
        "ontology": {"property": getattr(edge, "ontology_property", "")},
        "createdBy": edge.created_by,
        "provider": edge.provider,
        "model": edge.model,
    }


def _build_node_summary(
    node: GraphNodeRecord,
    notes: list[NoteRecord],
    edges: list[GraphEdgeRecord],
    edge_types: dict,
) -> str:
    parts = []
    note_titles = [n.title for n in notes[:3] if n.title]
    if note_titles:
        parts.append(f"Source notes: {', '.join(note_titles)}.")
    if edge_types:
        type_names = {
            "backlink": "backlinks",
            "explicit_link": "explicit links",
            "semantic": "semantic links",
            "semantic_relation": "semantic relations",
            "shared_concept": "shared concepts",
            "related": "relations",
            "derived_from": "derived evidence",
        }
        conn_list = [
            f"{edge_types[t]} {type_names.get(t, t)}"
            for t in sorted(edge_types.keys())[:4]
        ]
        parts.append(f"Connected through: {', '.join(conn_list)}.")
    if node.type == "note" and len(notes) == 1:
        snippet = (getattr(notes[0], "content", "") or "")[:150].strip()
        if snippet:
            parts.append(f'Content: "{snippet}..."')
    if node.type == "topic" and node.label:
        parts.append(
            "This topic was extracted from notes. Enrich it with AI, turn it into a permanent note, or connect it to other concepts."
        )
    if node.type == "concept" and node.label:
        parts.append(
            "Recurring concept. Connect it with notes to strengthen the graph."
        )
    return (
        " ".join(parts)
        if parts
        else "Knowledge graph node. Open it to inspect connections and source notes."
    )


def _why_node_exists(node: GraphNodeRecord, notes: list[NoteRecord]) -> str:
    if node.type == "note":
        path = notes[0].path if notes else ""
        folder = path.split("/")[0] if "/" in path else ""
        return f"This note exists in the vault{f' under {folder}' if folder else ''}."
    if node.type == "concept":
        titles = ", ".join(note.title for note in notes[:3])
        return (
            f"Extracted from: {titles}."
            if titles
            else "Extracted from system metadata."
        )
    if node.type == "topic":
        titles = ", ".join(note.title for note in notes[:3])
        return (
            f"Topic extracted from: {titles}."
            if titles
            else "Topic detected from note headings."
        )
    if node.type == "entity":
        return "Technical entity detected from metadata."
    return f"This node ({node.type}) was created by the knowledge pipeline."


def _estimate_clusters(
    nodes: list[GraphNodeRecord], edges: list[GraphEdgeRecord]
) -> int:
    if not nodes:
        return 0
    adjacency: dict[int, set[int]] = defaultdict(set)
    for edge in edges:
        adjacency[edge.source_node_id].add(edge.target_node_id)
        adjacency[edge.target_node_id].add(edge.source_node_id)
    visited: set[int] = set()
    clusters = 0
    for node in nodes:
        if node.id in visited:
            continue
        clusters += 1
        stack = [node.id]
        while stack:
            current = stack.pop()
            if current in visited:
                continue
            visited.add(current)
            stack.extend(adjacency[current] - visited)
    return clusters


def _insufficient(question: str) -> dict[str, Any]:
    return {
        "status": "insufficient_evidence",
        "question": question,
        "answer": "There is not enough evidence in your graph to support that relationship yet.",
        "relatedNodes": [],
        "connections": [],
        "evidence": [],
        "actions": [],
    }


def _tokenize(text: str) -> set[str]:
    words = re.findall(r"[\wÀ-ÿ]{3,}", text.lower())
    return {word for word in words if word not in STOPWORDS}


def _note_lookup_key(value: str) -> str:
    return normalize_concept_name(Path(value).stem.replace("-", " "))


def _upsert_typed_node(
    session: Session,
    node_type: str,
    label: str,
    title: str,
    summary: str,
    source: str,
    source_id: int,
    source_note_ids: list[int],
    evidence: list[str],
    created_by: str,
    confidence: float | None = None,
    status: str = "suggested",
    model: str = "",
) -> GraphNodeRecord | None:
    normalized_label = normalize_concept_name(label)
    if not normalized_label:
        return None
    canonical_type = canonical_node_type(node_type)
    issues = validate_node_name(canonical_type, label)
    if issues:
        quarantine_generated_candidate(
            session,
            kind="node",
            proposed_type=canonical_type,
            proposed_label=label,
            issues=issues,
            payload={"source": source, "sourceId": source_id, "evidence": evidence},
        )
        return None
    candidates = list(
        session.execute(
            select(GraphNodeRecord).where(
                GraphNodeRecord.type != "note",
                GraphNodeRecord.type != "insight",
            )
        ).scalars()
    )
    existing = next(
        (
            node
            for node in candidates
            if normalize_concept_name(node.label) == normalized_label
        ),
        None,
    )
    previous_evidence = (
        _parse_json_list(existing.source_evidence) if existing is not None else []
    )
    merged_evidence = sorted(
        {str(item) for item in previous_evidence + evidence if str(item)}
    )[:12]
    from berrybrain_api.graph_write_service import GraphWriteService

    node = GraphWriteService(session, autocommit=False).upsert_node(
        node_type=node_type,
        label=label,
        title=title,
        summary=summary,
        source=source,
        source_id=source_id,
        source_note_ids=source_note_ids,
        source_evidence=merged_evidence,
        confidence=None,
        created_by=created_by,
        model=model or "deterministic",
        status=status,
        source_quality="extracted",
        learning_value=node_type[:20],
        graph_metadata={"evidence": merged_evidence},
    )
    session.info.setdefault("graph_expansion_typed_node_ids", set()).add(node.id)
    return node


def _extract_topics_from_metadata(
    session: Session, metadata_by_note: dict[int, list[GeneratedMetadataRecord]]
) -> int:
    count = 0
    seen: set[tuple[int, str]] = set()
    note_titles = {
        note.id: normalize_concept_name(note.title)
        for note in session.execute(select(NoteRecord)).scalars()
    }
    notes = {note.id: note for note in session.execute(select(NoteRecord)).scalars()}
    for note_id, records in metadata_by_note.items():
        for record in records:
            if record.generation_type != "topics":
                continue
            content = _parse_json_object(record.content)
            if not isinstance(content, dict):
                continue
            for key in ("topics",):
                values = content.get(key)
                if not values:
                    continue
                if isinstance(values, str):
                    values = [v.strip() for v in values.split(",") if v.strip()]
                if not isinstance(values, list):
                    continue
                for topic_name in values:
                    if not isinstance(topic_name, dict):
                        continue
                    name = str(topic_name.get("name") or "")
                    evidence = str(
                        topic_name.get("evidence")
                        or topic_name.get("scope")
                        or topic_name.get("description")
                        or ""
                    ).strip()
                    note = notes.get(note_id)
                    evidence = (
                        _traceable_content_evidence(note.content, name, evidence)
                        if note is not None
                        else ""
                    )
                    normalized_name = normalize_concept_name(name)
                    if not _is_valid_topic_name(name, note_titles.get(note_id, "")):
                        continue
                    seen_key = (note_id, normalized_name)
                    if not name or not evidence or seen_key in seen:
                        continue
                    seen.add(seen_key)
                    node = _upsert_typed_node(
                        session,
                        "topic",
                        name,
                        name,
                        f"Topic detected in note metadata: {name}",
                        "metadata",
                        record.id,
                        [note_id],
                        [evidence],
                        "ai",
                        status="suggested",
                        model=record.model_used or "",
                    )
                    if node:
                        count += 1
    return count


def _extract_entities_from_metadata(
    session: Session, metadata_by_note: dict[int, list[GeneratedMetadataRecord]]
) -> int:
    count = 0
    seen: set[tuple[int, str]] = set()
    note_titles = {
        note.id: normalize_concept_name(note.title)
        for note in session.execute(select(NoteRecord)).scalars()
    }
    notes = {note.id: note for note in session.execute(select(NoteRecord)).scalars()}
    for note_id, records in metadata_by_note.items():
        for record in records:
            if record.generation_type != "entities":
                continue
            content = _parse_json_object(record.content)
            if not isinstance(content, dict):
                continue
            for key in ("entities",):
                values = content.get(key)
                if not values:
                    continue
                if isinstance(values, str):
                    values = [v.strip() for v in values.split(",") if v.strip()]
                if not isinstance(values, list):
                    continue
                for ent in values:
                    if not isinstance(ent, dict):
                        continue
                    name = str(ent.get("name") or "")
                    evidence = str(
                        ent.get("evidence") or ent.get("description") or ""
                    ).strip()
                    note = notes.get(note_id)
                    evidence = (
                        _traceable_content_evidence(note.content, name, evidence)
                        if note is not None
                        else ""
                    )
                    normalized_name = normalize_concept_name(name)
                    if normalized_name == note_titles.get(note_id):
                        continue
                    seen_key = (note_id, normalized_name)
                    if not name or not evidence or seen_key in seen:
                        continue
                    seen.add(seen_key)
                    node = _upsert_typed_node(
                        session,
                        "entity",
                        name,
                        name,
                        f"Entity detected in metadata: {name}",
                        "metadata",
                        record.id,
                        [note_id],
                        [evidence],
                        "ai",
                        status="suggested",
                        model=record.model_used or "",
                    )
                    if node:
                        count += 1
    return count


def _extract_context_from_metadata(
    session: Session, metadata_by_note: dict[int, list[GeneratedMetadataRecord]]
) -> int:
    count = 0
    seen: set[tuple[int, str]] = set()
    notes = {note.id: note for note in session.execute(select(NoteRecord)).scalars()}
    for note_id, records in metadata_by_note.items():
        for record in records:
            if record.generation_type != "context":
                continue
            content = _parse_json_object(record.content)
            if not isinstance(content, dict):
                continue
            for key in ("context",):
                val = content.get(key)
                if not val:
                    continue
                if isinstance(val, dict):
                    domain = val.get("domain", "")
                    evidence = str(val.get("evidence") or domain or "")
                    if domain:
                        val = domain
                else:
                    evidence = str(val)
                ctx_name = str(val).strip()
                note = notes.get(note_id)
                evidence = (
                    _traceable_content_evidence(note.content, ctx_name, evidence)
                    if note is not None
                    else ""
                )
                seen_key = (note_id, normalize_concept_name(ctx_name))
                if (
                    not _is_valid_context_name(ctx_name)
                    or not evidence
                    or seen_key in seen
                ):
                    continue
                seen.add(seen_key)
                node = _upsert_typed_node(
                    session,
                    "context",
                    ctx_name,
                    ctx_name,
                    f"Detected context: {ctx_name}",
                    "metadata",
                    record.id,
                    [note_id],
                    [evidence],
                    "ai",
                    status="suggested",
                    model=record.model_used or "",
                )
                if node:
                    count += 1
    return count


def _is_valid_context_name(name: str) -> bool:
    normalized = normalize_concept_name(name)
    if not normalized:
        return False
    generic = {
        "study",
        "studies",
        "unknown",
        "general",
        "not specified",
        "unspecified",
    }
    return normalized not in generic


def _extract_gaps_from_metadata(
    session: Session, metadata_by_note: dict[int, list[GeneratedMetadataRecord]]
) -> int:
    count = 0
    seen = set()
    for note_id, records in metadata_by_note.items():
        for record in records:
            content = _parse_json_object(record.content)
            if not isinstance(content, dict):
                continue
            for key in ("gaps", "missing", "questions", "unanswered"):
                values = content.get(key)
                if not values:
                    continue
                if isinstance(values, str):
                    values = [
                        {"name": v.strip()} for v in values.split("\n") if v.strip()
                    ]
                if not isinstance(values, list):
                    continue
                for gap in values:
                    name = (
                        str(gap.get("name", gap.get("question", gap)))
                        if isinstance(gap, dict)
                        else str(gap)
                    )
                    if not name or name in seen:
                        continue
                    seen.add(name)
                    desc = (
                        str(gap.get("description", gap.get("what_is_missing", "")))
                        if isinstance(gap, dict)
                        else name
                    )
                    node = _upsert_typed_node(
                        session,
                        "gap",
                        name,
                        name,
                        desc or f"Knowledge gap detected: {name}",
                        "metadata",
                        record.id,
                        [note_id],
                        [name],
                        "system",
                        status="suggested",
                        model=record.model_used or "",
                    )
                    if node:
                        count += 1
    return count


def _extract_sources_from_notes(session: Session, notes: list[NoteRecord]) -> int:
    count = 0
    seen = set()
    for note in notes:
        fm = _parse_json_object(note.frontmatter)
        if not isinstance(fm, dict):
            continue
        for key in ("source", "source_url", "references", "origin"):
            val = fm.get(key)
            if not val:
                continue
            if isinstance(val, list):
                for item in val:
                    name = (
                        str(item.get("name", item.get("title", item)))
                        if isinstance(item, dict)
                        else str(item)
                    )
                    if not name or name in seen:
                        continue
                    seen.add(name)
                    node = _upsert_typed_node(
                        session,
                        "source",
                        name,
                        name,
                        f"Source mentioned in frontmatter: {name}",
                        "frontmatter",
                        note.id,
                        [note.id],
                        [name],
                        "system",
                        status="suggested",
                    )
                    if node:
                        count += 1
            elif isinstance(val, str) and val.strip():
                if val.strip() in seen:
                    continue
                seen.add(val.strip())
                node = _upsert_typed_node(
                    session,
                    "source",
                    val.strip(),
                    val.strip(),
                    f"Source mentioned in frontmatter: {val.strip()}",
                    "frontmatter",
                    note.id,
                    [note.id],
                    [val.strip()],
                    "system",
                    status="suggested",
                )
                if node:
                    count += 1
    return count


def _extract_graph_node_type(node_type: str) -> str:
    mapping = {
        "PARSE_NOTE": "parse",
        "CLASSIFY_NOTE": "classify",
        "ASSIMILATE_NOTE": "assimilate",
        "EXTRACT_CONCEPTS": "concepts",
        "EXTRACT_CONTEXT": "context",
        "EXTRACT_ENTITIES": "entities",
        "DETECT_TOPICS": "topics",
        "GENERATE_NODE_SUMMARY": "summary",
        "GENERATE_INFERRED_CONNECTIONS": "connections",
        "GENERATE_GRAPH_INSIGHTS": "insights",
        "UPDATE_GRAPH_CLUSTERS": "clusters",
        "UPDATE_GRAPH_STATS": "stats",
        "EXPAND_KNOWLEDGE_GRAPH": "graph",
    }
    return mapping.get(node_type, node_type)


def _dump_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _parse_json_list(value: str) -> list[Any]:
    try:
        parsed = json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return []
    return parsed if isinstance(parsed, list) else []


def _parse_json_object(value: str) -> dict[str, Any]:
    try:
        parsed = json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return {}
    return parsed if isinstance(parsed, dict) else {}
