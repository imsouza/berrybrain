from __future__ import annotations

import json
import hashlib
import re
from uuid import uuid4
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from berrybrain_api.ai_gateway import (
    GraphAIUnavailable,
    generate_graph_answer,
    get_ai_config,
)
from berrybrain_api.models import (
    ConceptRecord,
    ConnectionRecord,
    ChunkRecord,
    GeneratedMetadataRecord,
    GraphEdgeRecord,
    GraphNodeRecord,
    InsightRecord,
    NoteRecord,
)

PROMPT_VERSION = "graph-expand.deterministic.v1"
STOPWORDS = {
    "a",
    "as",
    "de",
    "do",
    "da",
    "das",
    "dos",
    "e",
    "em",
    "o",
    "os",
    "para",
    "por",
    "que",
    "um",
    "uma",
    "com",
    "sobre",
    "qual",
    "quais",
    "relacao",
    "relação",
    "tem",
    "ver",
}


def _merge_duplicate_nodes(session: Session) -> int:
    from berrybrain_api.graph_write_service import GraphWriteService

    return GraphWriteService(session, autocommit=False).deduplicate_nodes()


def _delete_duplicate_edges(session: Session) -> int:
    from berrybrain_api.graph_write_service import GraphWriteService

    return GraphWriteService(session, autocommit=False).deduplicate_edges()


def expand_knowledge_graph(session: Session) -> dict[str, int]:
    _merge_duplicate_nodes(session)

    notes = list(session.execute(select(NoteRecord)).scalars())
    metadata = list(session.execute(select(GeneratedMetadataRecord)).scalars())
    metadata_by_note: dict[int, list[GeneratedMetadataRecord]] = defaultdict(list)
    for record in metadata:
        metadata_by_note[record.note_id].append(record)

    note_nodes = {_node_key("note", n.id): _upsert_note_node(session, n) for n in notes}
    _prune_generated_typed_nodes(session)
    _prune_generated_graph_insights(session)
    _prune_orphan_insight_nodes(session)
    _prune_title_duplicate_typed_nodes(session, notes)
    concept_to_note_ids: dict[str, set[int]] = defaultdict(set)
    concept_sources: dict[str, list[str]] = defaultdict(list)
    concept_models: dict[str, str] = {}

    for note in notes:
        for concept_name, evidence, model in _extract_note_concepts(
            note, metadata_by_note.get(note.id, [])
        ):
            normalized = normalize_concept_name(concept_name)
            if not normalized:
                continue
            concept_to_note_ids[normalized].add(note.id)
            if evidence and evidence not in concept_sources[normalized]:
                concept_sources[normalized].append(evidence)
            if model:
                concept_models[normalized] = model

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
    for normalized, concept_node in concept_nodes.items():
        for note_id in concept_to_note_ids[normalized]:
            note_node = note_nodes.get(_node_key("note", note_id))
            if note_node is None:
                continue
            edge = _upsert_graph_edge(
                session,
                note_node.id,
                concept_node.id,
                edge_type="shared_concept",
                label="shared concept",
                reason=f'The note mentions the concept "{concept_node.label}".',
                evidence=[concept_node.label],
                source_note_ids=[note_id],
                created_by="system",
                status="confirmed",
            )
            if edge:
                edges_count += 1

        note_ids = sorted(concept_to_note_ids[normalized])
        if len(note_ids) > 1:
            for index, source_id in enumerate(note_ids):
                for target_id in note_ids[index + 1 :]:
                    source_note = next(
                        (note for note in notes if note.id == source_id), None
                    )
                    target_note = next(
                        (note for note in notes if note.id == target_id), None
                    )
                    if source_note is None or target_note is None:
                        continue
                    reason = (
                        f'The notes "{source_note.title}" and "{target_note.title}" '
                        f'share the concept "{concept_node.label}".'
                    )
                    conn = _upsert_note_connection(
                        session,
                        source_id,
                        target_id,
                        connection_type="shared_concept",
                        confidence=78,
                        reason=reason,
                        evidence=[
                            concept_node.label,
                            source_note.title,
                            target_note.title,
                        ],
                        created_by="system",
                        status="suggested",
                    )
                    if conn:
                        connections_count += 1
                    source_node = note_nodes.get(_node_key("note", source_id))
                    target_node = note_nodes.get(_node_key("note", target_id))
                    if source_node and target_node:
                        edge = _upsert_graph_edge(
                            session,
                            source_node.id,
                            target_node.id,
                            edge_type="shared_concept",
                            label="shared concept",
                            reason=reason,
                            evidence=_parse_json_list(conn.evidence),
                            source_note_ids=[source_id, target_id],
                            created_by="system",
                            status="suggested",
                        )
                        if edge:
                            edges_count += 1

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
                    edge_type="shared_context",
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
                confidence=100,
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

    topics_count = _extract_topics_from_metadata(session, metadata_by_note)
    entities_count = _extract_entities_from_metadata(session, metadata_by_note)
    context_count = _extract_context_from_metadata(session, metadata_by_note)
    gaps_count = _extract_gaps_from_metadata(session, metadata_by_note)
    sources_count = _extract_sources_from_notes(session, notes)
    _generate_deterministic_insights(session)
    insights_count = _generate_graph_insights(session)

    typed_nodes = (
        session.execute(
            select(GraphNodeRecord).where(
                GraphNodeRecord.type.in_(
                    ("topico", "entidade", "contexto", "lacuna", "fonte", "insight")
                )
            )
        )
        .scalars()
        .all()
    )
    for typed_node in typed_nodes:
        source_ids = _parse_json_list(typed_node.source_note_ids)
        for note_id in source_ids:
            note_node = note_nodes.get(_node_key("note", note_id))
            if not note_node:
                continue
            existing = session.execute(
                select(GraphEdgeRecord).where(
                    GraphEdgeRecord.source_node_id.in_((typed_node.id, note_node.id)),
                    GraphEdgeRecord.target_node_id.in_((typed_node.id, note_node.id)),
                )
            ).first()
            if existing:
                continue
            edge = _upsert_graph_edge(
                session,
                typed_node.id,
                note_node.id,
                edge_type="related",
                label=f"{typed_node.type}↔note",
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
    visible_nodes = [
        node
        for node in session.execute(select(GraphNodeRecord)).scalars()
        if node.status != "ignored"
    ]
    visible_edges = [
        edge
        for edge in session.execute(select(GraphEdgeRecord)).scalars()
        if edge.status != "ignored"
    ]

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

    if node_type in {"concept", "conceito"}:
        summary = (
            node.summary or f'"{label}" is a recurring concept grounded in {note_text}.'
        )
        context = (
            f"This concept helps connect notes that discuss the same idea. It should be "
            f"reviewed as a possible permanent note when it appears across multiple sources. "
            f"Evidence: {evidence_text}."
        )
        return summary, context, "concept"

    if node_type in {"topico", "topic"}:
        summary = node.summary or f'"{label}" is a topic detected from {note_text}.'
        context = (
            f"This topic groups nearby ideas from the source material. It is useful when "
            f"it explains what area of study the related notes belong to. Evidence: {evidence_text}."
        )
        return summary, context, "topic"

    if node_type in {"entidade", "entity"}:
        summary = node.summary or f'"{label}" is an entity mentioned in {note_text}.'
        context = (
            f"This entity can anchor references to people, tools, systems, projects, or named "
            f"objects across the graph. Evidence: {evidence_text}."
        )
        return summary, context, "entity"

    if node_type in {"contexto", "context"}:
        summary = node.summary or f'"{label}" is a context inferred from {note_text}.'
        context = (
            f"This context explains the situation or domain where related concepts are being "
            f"used. It helps BerryBrain answer why notes belong together. Evidence: {evidence_text}."
        )
        return summary, context, "context"

    if node_type in {"lacuna", "gap"}:
        summary = (
            node.summary or f'"{label}" is a knowledge gap detected in {note_text}.'
        )
        context = (
            f"This gap marks a missing explanation, bridge, or source that would improve the "
            f"knowledge graph. Treat it as a candidate for a new note or study path. Evidence: {evidence_text}."
        )
        return summary, context, "gap"

    if node_type in {"fonte", "source"}:
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
                evidence=evidence[:12],
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
        writer.upsert_edge(
            source_node_id=edge.source_node_id,
            target_node_id=edge.target_node_id,
            edge_type=edge.type,
            label=edge.label,
            reason=edge.reason
            or "Legacy AI relation recovered from current note chunks.",
            evidence=[evidence],
            source_note_ids=selected_ids,
            confidence=edge.confidence or 0.5,
            status=edge.status or "suggested",
            created_by="ai",
            provider=edge.provider or "legacy-ai",
            model=edge.model or edge.created_by_model or "legacy-ai",
            prompt_version=edge.prompt_version or "graph-evidence-migration.v1",
            pipeline_run_id=f"graph-evidence-migration:{uuid4()}",
        )
        recovered += 1
    return {"recovered": recovered, "stale": stale}


def _human_join(items: list[str]) -> str:
    clean = [str(item).strip() for item in items if str(item).strip()]
    if not clean:
        return ""
    if len(clean) == 1:
        return clean[0]
    if len(clean) == 2:
        return f"{clean[0]} and {clean[1]}"
    return f"{', '.join(clean[:-1])}, and {clean[-1]}"


async def generate_inferred_graph_connections(
    session: Session, max_pairs: int = 20
) -> dict[str, int]:
    """Use AI to find non-obvious connections between existing graph nodes.

    Only one AI provider is used (cloud NVIDIA NIM or local Ollama), never both.
    Respects auto_confirm_confidence for edge status.
    """
    config = get_ai_config(session)
    nodes = list(session.execute(select(GraphNodeRecord)).scalars())
    candidate_types = {"concept", "topico", "entidade", "contexto", "note"}
    candidates = [n for n in nodes if n.type in candidate_types and n.label]
    if len(candidates) < 2:
        return {"connections": 0, "reason": "not_enough_nodes"}

    label_to_node = {n.label: n for n in candidates}

    def node_chunk(node: GraphNodeRecord) -> tuple[ChunkRecord, NoteRecord] | None:
        note_ids = [
            int(value)
            for value in _parse_json_list(node.source_note_ids)
            if str(value).isdigit()
        ]
        if node.type == "note" and node.source_id:
            note_ids.insert(0, node.source_id)
        if not note_ids:
            return None
        return session.execute(
            select(ChunkRecord, NoteRecord)
            .join(NoteRecord, NoteRecord.id == ChunkRecord.note_id)
            .where(
                ChunkRecord.note_id.in_(note_ids),
                ChunkRecord.content_hash == NoteRecord.content_hash,
            )
            .order_by(ChunkRecord.chunk_index.asc())
            .limit(1)
        ).first()

    chunk_by_node_id = {node.id: node_chunk(node) for node in candidates[:60]}
    evidenced_candidates = [
        node for node in candidates[:60] if chunk_by_node_id.get(node.id) is not None
    ]
    if len(evidenced_candidates) < 2:
        return {"connections": 0, "reason": "insufficient_chunk_evidence"}
    context = "\n".join(
        f"- [{node.type}] {node.label}: {chunk_by_node_id[node.id][0].text[:280]}"
        for node in evidenced_candidates
    )
    prompt = (
        "Below are nodes from a knowledge graph. Identify non-obvious, "
        "semantically meaningful connections between DIFFERENT nodes.\n\n"
        f"{context}\n\n"
        'Return JSON: {"connections": [{"source": "<exact label>", '
        '"target": "<exact label>", "type": "<semantic_relation|prerequisite|example_of|contrasts_with|duplicates|applies_to|supports|contradicts>", '
        '"reason": "<why they connect using the supplied excerpts>", '
        '"confidence": 0.0}]}. Maximum 20 connections. Confidence between 0 and 1.'
    )
    system = (
        "You are a knowledge graph reasoning engine. Find meaningful, "
        "non-obvious connections between concepts. Respond only with JSON."
    )

    try:
        result = await generate_graph_answer(config, prompt, system)
    except GraphAIUnavailable:
        return {"connections": 0, "reason": "ai_unavailable"}
    except (json.JSONDecodeError, ValueError) as exc:
        return {
            "connections": 0,
            "reason": "invalid_ai_response",
            "error": str(exc)[:240],
        }
    except Exception as exc:
        return {
            "connections": 0,
            "reason": "ai_request_failed",
            "error": str(exc)[:240],
        }

    connections = result.get("connections", []) if isinstance(result, dict) else []
    auto_confirm = float(config.get("auto_confirm_confidence") or "0.9")
    model = config.get("cloud_model") or config.get("ollama_model", "")
    provider = config.get("provider", "local")
    created = 0
    rejected = 0
    pipeline_run_id = f"graph-infer:{uuid4()}"
    from berrybrain_api.graph_write_service import GraphWriteService

    writer = GraphWriteService(session)
    for c in connections[:max_pairs]:
        src_label = str(c.get("source", "")).strip()
        tgt_label = str(c.get("target", "")).strip()
        source_node = label_to_node.get(src_label)
        target_node = label_to_node.get(tgt_label)
        if (
            source_node is None
            or target_node is None
            or source_node.id == target_node.id
        ):
            rejected += 1
            continue
        source_pair = chunk_by_node_id.get(source_node.id)
        target_pair = chunk_by_node_id.get(target_node.id)
        if source_pair is None or target_pair is None:
            rejected += 1
            continue
        source_chunk, source_note = source_pair
        target_chunk, target_note = target_pair
        try:
            conf = float(c.get("confidence", 0.5))
        except (TypeError, ValueError):
            conf = 0.5
        reason = (
            str(c.get("reason", "")).strip()
            or f"Relationship between {src_label} and {tgt_label}."
        )
        excerpt = (
            f"{source_note.title}: {source_chunk.text[:180]} | "
            f"{target_note.title}: {target_chunk.text[:180]}"
        )
        evidence = {
            "sourceNoteId": source_note.id,
            "targetNoteId": target_note.id,
            "sourceChunkId": source_chunk.id,
            "targetChunkId": target_chunk.id,
            "startLine": source_chunk.start_line,
            "endLine": source_chunk.end_line,
            "targetStartLine": target_chunk.start_line,
            "targetEndLine": target_chunk.end_line,
            "excerpt": excerpt,
            "hash": hashlib.sha256(excerpt.encode()).hexdigest(),
            "sourceContentHash": source_chunk.content_hash,
            "targetContentHash": target_chunk.content_hash,
        }
        try:
            edge = writer.upsert_edge(
                source_node_id=source_node.id,
                target_node_id=target_node.id,
                edge_type=str(c.get("type") or "semantic_relation"),
                label=reason[:255],
                reason=reason,
                evidence=[evidence],
                source_note_ids=[source_note.id, target_note.id],
                created_by="ai",
                status="confirmed" if conf >= auto_confirm else "suggested",
                provider=provider,
                model=model,
                prompt_version="graph-infer.v1",
                pipeline_run_id=pipeline_run_id,
                confidence=conf,
            )
        except HTTPException:
            rejected += 1
            continue
        if edge:
            created += 1
    return {"connections": created, "rejected": rejected}


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


def delete_graph_node(session: Session, node_id: int) -> bool:
    node = session.get(GraphNodeRecord, node_id)
    if node is None:
        return False
    _delete_graph_node_with_edges(session, node)
    return True


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


def _prune_generated_typed_nodes(session: Session) -> int:
    nodes = list(
        session.execute(
            select(GraphNodeRecord).where(
                GraphNodeRecord.type.in_(
                    ("topico", "entidade", "contexto", "lacuna", "fonte")
                ),
                GraphNodeRecord.status == "suggested",
            )
        ).scalars()
    )
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
                InsightRecord.type == "recurring_concept",
                InsightRecord.status == "suggested",
            )
        ).scalars()
    )
    for insight in insights:
        concept_name = insight.title.removeprefix("Conceito recorrente: ").strip()
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
            .where(GraphEdgeRecord.status != "ignored")
            .order_by(GraphEdgeRecord.confidence.desc())
        ).scalars()
    )
    graph_nodes = list(session.execute(select(GraphNodeRecord)).scalars())
    node_by_id = {node.id: node for node in graph_nodes}
    edge_matches: list[
        tuple[int, GraphEdgeRecord, GraphNodeRecord, GraphNodeRecord]
    ] = []
    for edge in edges:
        source = node_by_id.get(edge.source_node_id)
        target = node_by_id.get(edge.target_node_id)
        if source is None or target is None:
            continue
        haystack = " ".join(
            [
                source.label,
                target.label,
                edge.type,
                edge.reason or "",
                edge.evidence or "",
            ]
        )
        score = len(tokens & _tokenize(haystack))
        if score >= 2:
            edge_matches.append((score, edge, source, target))

    if not matches and not edge_matches:
        return _insufficient(question)

    best_conn_score = max((m[0] for m in matches), default=0)
    best_edge_score = max((m[0] for m in edge_matches), default=0)

    if best_edge_score >= best_conn_score and edge_matches:
        edge_matches.sort(
            key=lambda item: (item[0], item[1].confidence or 0), reverse=True
        )
        _, edge, source, target = edge_matches[0]
        evidence = _parse_json_list(edge.evidence) or [source.label, target.label]
        return {
            "status": "answered",
            "question": question,
            "answer": edge.reason or f"{source.label} is connected to {target.label}.",
            "confidence": round((edge.confidence or 0) / 100, 2),
            "relatedNodes": [source.label, target.label],
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
        "confidence": round((conn.confidence or 0) / 100, 2),
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
            confidence=min(0.95, 0.72 + (len(note_ids) * 0.05)),
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
            confidence=0.68,
            priority=5,
        )
        if insight:
            created_or_updated += 1

    return created_or_updated


def _generate_graph_insights(session: Session) -> int:
    insights = list(session.execute(select(InsightRecord)).scalars())
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
            confidence=insight.confidence or 0.7,
            status=insight.status or "suggested",
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
    confidence: float,
    priority: int,
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
    insight.confidence = confidence
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
    if (insight.status or "") in {"ignored", "archived"}:
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
    if (insight.title or "").strip() == (insight.description or "").strip():
        return False
    return True


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
            confidence=insight.confidence or 0.7,
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
        r"\b(?:note|concept|topico|topic|contexto|context|entidade|entity|gap|lacuna|source)_(\d+)\b",
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
                ):
                    targets[node.id] = node

    normalized_evidence = normalize_concept_name(evidence_text)
    if normalized_evidence:
        nodes = list(
            session.execute(
                select(GraphNodeRecord).where(GraphNodeRecord.status != "ignored")
            ).scalars()
        )
        for node in nodes:
            if node.id == insight_node_id:
                continue
            label = normalize_concept_name(node.label)
            title = normalize_concept_name(node.title or "")
            if label and label in normalized_evidence:
                targets[node.id] = node
            elif title and title in normalized_evidence:
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
    nodes = list(session.execute(select(GraphNodeRecord)).scalars())
    edges = list(
        session.execute(
            select(GraphEdgeRecord).where(GraphEdgeRecord.status != "ignored")
        ).scalars()
    )
    if not nodes:
        notes = list(session.execute(select(NoteRecord)).scalars())
        if not notes:
            return _insufficient(question)
        return {
            "status": "context_ready",
            "question": question,
            "answer": "",
            "confidence": 0.4,
            "relatedNodes": [note.title for note in notes[:12]],
            "connections": [],
            "evidence": [f"Note: {note.title} ({note.path})" for note in notes[:12]],
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

    return {
        "status": "context_ready",
        "question": question,
        "answer": "",
        "confidence": 0.5,
        "relatedNodes": [node["label"] for node in context_nodes],
        "connections": context_edges,
        "evidence": evidence[:12],
        "graphContext": {"nodes": context_nodes, "edges": context_edges},
        "actions": ["Highlight in graph", "Create insight", "Create permanent note"],
    }


def summarize_graph(session: Session) -> dict[str, Any]:
    nodes = list(session.execute(select(GraphNodeRecord)).scalars())
    edges = list(session.execute(select(GraphEdgeRecord)).scalars())
    degrees: dict[int, int] = defaultdict(int)
    for edge in edges:
        if edge.status == "ignored":
            continue
        degrees[edge.source_node_id] += 1
        degrees[edge.target_node_id] += 1
    active_edges = [edge for edge in edges if edge.status != "ignored"]
    return {
        "nodes": len(nodes),
        "edges": len(active_edges),
        "orphans": sum(1 for node in nodes if degrees.get(node.id, 0) == 0),
        "clusters": _estimate_clusters(nodes, active_edges),
        "centralNotes": [
            {"id": node_id, "degree": degree}
            for node_id, degree in sorted(
                degrees.items(), key=lambda item: item[1], reverse=True
            )[:5]
        ],
    }


def get_node_summary(session: Session, node_id: int) -> dict[str, Any]:
    node = session.get(GraphNodeRecord, node_id)
    if node is None:
        raise HTTPException(status_code=404, detail="Graph node not found")
    note_ids = _parse_json_list(node.source_note_ids)
    notes = [
        session.get(NoteRecord, note_id)
        for note_id in note_ids
        if isinstance(note_id, int)
    ]
    notes = [note for note in notes if note is not None]
    edges = list(
        session.execute(
            select(GraphEdgeRecord).where(
                (GraphEdgeRecord.source_node_id == node.id)
                | (GraphEdgeRecord.target_node_id == node.id),
                GraphEdgeRecord.status != "ignored",
            )
        ).scalars()
    )
    edge_types = {}
    for edge in edges:
        edge_types[edge.type] = edge_types.get(edge.type, 0) + 1
    synthetic_summary = node.summary or _build_node_summary(
        node, notes, edges, edge_types
    )

    return {
        "id": node.id,
        "type": node.type,
        "label": node.label,
        "title": node.title or node.label,
        "summary": synthetic_summary,
        "source": node.source,
        "sourceNoteIds": note_ids,
        "confidence": node.confidence,
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
        "generatedAt": node.generated_at.isoformat()
        if getattr(node, "generated_at", None)
        else None,
        "metadata": _parse_json_object(node.graph_metadata),
        "notes": [
            {"id": note.id, "title": note.title, "path": note.path} for note in notes
        ],
        "connections": [_serialize_edge(edge) for edge in edges],
        "whyThisExists": _why_node_exists(node, notes),
    }


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


def normalize_concept_name(value: str) -> str:
    cleaned = re.sub(r"[-_]+", " ", value.strip().lower())
    cleaned = re.sub(r"\s+", " ", cleaned)
    cleaned = re.sub(r"^[#/\\-]+|[#/\\-]+$", "", cleaned)
    if len(cleaned) < 3 or cleaned in STOPWORDS:
        return ""
    return cleaned[:120]


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
        confidence=1.0,
        created_by="system",
        status="confirmed",
        source_quality="vault_note",
        learning_value="source",
        graph_metadata=metadata,
    )


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
    concept.extracted_by = "system"
    concept.confidence = 0.7 if len(note_ids) == 1 else 0.85
    concept.status = "suggested"
    concept.provider = "deterministic"
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


def _upsert_note_connection(
    session: Session,
    source_note_id: int,
    target_note_id: int,
    connection_type: str,
    confidence: int,
    reason: str,
    evidence: list[str],
    created_by: str,
    status: str,
) -> ConnectionRecord:
    conn = session.execute(
        select(ConnectionRecord).where(
            ConnectionRecord.source_note_id == source_note_id,
            ConnectionRecord.target_note_id == target_note_id,
            ConnectionRecord.connection_type == connection_type,
        )
    ).scalar_one_or_none()
    if conn is None:
        conn = ConnectionRecord(
            source_note_id=source_note_id,
            target_note_id=target_note_id,
            connection_type=connection_type,
        )
        session.add(conn)
        session.flush()
    conn.confidence = confidence
    conn.reason = reason
    conn.evidence = _dump_json(evidence)
    conn.ai_notes = (
        f"Subagent connection-reasoner: {connection_type} connection created with "
        f"{confidence}% confidence using registered evidence."
    )
    conn.created_by = created_by
    conn.provider = "deterministic"
    conn.model = "backlink-parser"
    conn.prompt_version = PROMPT_VERSION
    conn.status = status
    conn.updated_at = datetime.now(UTC)
    return conn


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
            evidence=evidence,
            source_note_ids=source_note_ids,
            confidence=(
                confidence
                if confidence is not None
                else (1.0 if status == "confirmed" else 0.7)
            ),
            created_by=created_by,
            provider=provider,
            model=model,
            prompt_version=prompt_version,
            status=status,
        )
    except HTTPException:
        return None


def _extract_note_concepts(
    note: NoteRecord, metadata: list[GeneratedMetadataRecord]
) -> list[tuple[str, str, str]]:
    concepts: list[tuple[str, str, str]] = []
    seen: set[str] = set()
    note_title_key = normalize_concept_name(note.title)
    for record in metadata:
        content = _parse_json_object(record.content)
        values: list[Any] = []
        if record.generation_type == "concepts":
            values = _extract_values(content, ["concepts", "items", "keywords"])
        elif record.generation_type == "summary":
            values = _extract_values(content, ["concepts", "keywords"])
        elif record.generation_type == "classification":
            values = _extract_values(content, ["concepts"])
        if not values and record.generation_type in {"concepts", "summary"}:
            values = _extract_terms_from_metadata_text(content)
        for value in values:
            if isinstance(value, dict):
                name = str(
                    value.get("name")
                    or value.get("title")
                    or value.get("label")
                    or value.get("text")
                    or ""
                )
            else:
                name = str(value)
            normalized = normalize_concept_name(name)
            if not normalized or normalized == note_title_key or normalized in seen:
                continue
            if _is_valid_concept_name(name):
                seen.add(normalized)
                concepts.append(
                    (name, f"{note.title}: {name}", record.model_used or "")
                )
    for name in _extract_content_concepts(note):
        normalized = normalize_concept_name(name)
        if not normalized or normalized == note_title_key or normalized in seen:
            continue
        if _is_valid_concept_name(name):
            seen.add(normalized)
            concepts.append((name, f"{note.title}: {name}", "content-analysis"))
    return concepts


def _is_valid_concept_name(name: str) -> bool:
    clean = " ".join(str(name or "").strip().split())
    if len(clean) < 2 or len(clean) > 80:
        return False
    if len(clean.split()) > 8:
        return False
    lowered = clean.lower()
    if normalize_concept_name(clean) in {
        "assim",
        "apesar",
        "baixe",
        "contatos",
        "durante",
        "foto",
        "home",
        "study",
        "studies",
        "note",
        "notes",
        "draft",
        "rascunho",
        "inbox",
        "janeiro",
        "meus",
        "processo",
        "projetos",
        "resumo",
        "rio",
        "servicos",
        "serviços",
        "tanto",
    }:
        return False
    if "/" in lowered or "\\" in lowered:
        return False
    if lowered.endswith(".md"):
        return False
    blocked_prefixes = (
        "falta ",
        "faltam ",
        "nao ha ",
        "não há ",
        "sem ",
        "lacuna",
        "missing ",
        "no ",
    )
    return not lowered.startswith(blocked_prefixes)


def _is_valid_topic_name(name: str, note_title_key: str = "") -> bool:
    if not _is_valid_concept_name(name):
        return False
    normalized = normalize_concept_name(name)
    if normalized == note_title_key:
        return False
    if normalized.replace(" ", "-") == note_title_key.replace(" ", "-"):
        return False
    generic = {
        "study",
        "studies",
        "note",
        "notes",
        "permanent",
        "permanente",
        "permanentes",
        "inbox",
        "draft",
        "rascunho",
    }
    if normalized in generic:
        return False
    if "/" in str(name) or "\\" in str(name):
        return False
    return True


def _concepts_from_title(title: str) -> list[tuple[str, str, str]]:
    parts = [p for p in re.split(r"[:|/\\-]", title) if p.strip()]
    concepts = [(title, f"Note title: {title}", "")]
    concepts.extend((part, f"Note title: {title}", "") for part in parts)
    return concepts


CONTENT_CONCEPT_PATTERNS = {
    "frontend": "Frontend development",
    "backend": "Backend development",
    "full stack": "Full Stack development",
    "ux/ui": "UX/UI design",
    "ux ui": "UX/UI design",
    "desenvolvimento web": "Web development",
    "design de interfaces": "Interface design",
    "design gráfico": "Graphic design",
    "ciência da computação": "Computer Science",
    "html": "HTML",
    "css": "CSS",
    "javascript": "JavaScript",
    "typescript": "TypeScript",
    "react": "React",
    "next.js": "Next.js",
    "node.js": "Node.js",
    "tailwind": "Tailwind CSS",
    "docker": "Docker",
    "postgresql": "PostgreSQL",
    "hulk": "Hulk",
    "bruce banner": "Bruce Banner",
    "radiação": "Radiation",
    "raiva": "Emotional control",
    "emoções": "Emotional control",
    "equilíbrio": "Balance",
    "conflitos internos": "Internal conflict",
    "força": "Strength",
    "superação": "Overcoming adversity",
    "rio de janeiro": "Rio de Janeiro",
    "desafios sociais": "Social challenges",
    "desafios urbanos": "Urban challenges",
    "desenvolvimento": "Development",
    "transformação": "Transformation",
}


def _extract_content_concepts(note: NoteRecord) -> list[str]:
    text = _clean_note_text_for_concepts(note.content or "")
    if not text.strip():
        return []
    lowered = text.lower()
    candidates: list[str] = []
    for needle, concept in CONTENT_CONCEPT_PATTERNS.items():
        if needle in lowered:
            candidates.append(concept)

    # Capture explicit proper names that often act as entities/concepts.
    for match in re.finditer(
        r"\b([A-ZÀ-Ý][\wÀ-ÿ]+(?:\s+[A-ZÀ-Ý][\wÀ-ÿ]+){0,3})\b", text
    ):
        name = " ".join(match.group(1).split())
        normalized = normalize_concept_name(name)
        if _is_valid_concept_name(name) and normalized not in {"home", "resumo"}:
            candidates.append(name)

    return _unique_concept_names(candidates)[:18]


def _extract_terms_from_metadata_text(content: Any) -> list[str]:
    text = _flatten_metadata_text(content)
    if not text:
        return []
    candidates: list[str] = []
    for line in re.split(r"[\n;]+", text):
        clean = re.sub(r"^[*\-\d.\s]+", "", line).strip()
        if _is_valid_concept_name(clean):
            candidates.append(clean)
    for phrase in re.findall(r'"([^"]{3,80})"', text):
        if _is_valid_concept_name(phrase):
            candidates.append(phrase)
    return _unique_concept_names(candidates)[:12]


def _flatten_metadata_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "\n".join(_flatten_metadata_text(item) for item in value)
    if isinstance(value, dict):
        return "\n".join(_flatten_metadata_text(item) for item in value.values())
    return ""


def _unique_concept_names(values: list[str]) -> list[str]:
    seen: set[str] = set()
    preliminary: list[str] = []
    for value in values:
        clean = " ".join(str(value or "").strip().split())
        normalized = normalize_concept_name(clean)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        preliminary.append(clean)
    normalized_all = {normalize_concept_name(value): value for value in preliminary}
    result: list[str] = []
    for value in preliminary:
        normalized = normalize_concept_name(value)
        is_partial = (
            len(normalized.split()) == 1
            and not value.isupper()
            and any(
                normalized != other and normalized in other.split()
                for other in normalized_all
            )
        )
        if not is_partial:
            result.append(value)
    return result


def _clean_note_text_for_concepts(text: str) -> str:
    cleaned = re.sub(r"!\[[^\]]*\]\([^)]+\)", " ", text)
    cleaned = re.sub(r"\[[^\]]+\]\([^)]+\)", " ", cleaned)
    cleaned = re.sub(r"`[^`]*`", " ", cleaned)
    cleaned = re.sub(r"https?://\S+", " ", cleaned)
    return cleaned


def _extract_values(content: Any, keys: list[str]) -> list[Any]:
    if isinstance(content, list):
        return content
    if not isinstance(content, dict):
        return []
    values: list[Any] = []
    for key in keys:
        item = content.get(key)
        if isinstance(item, list):
            values.extend(item)
        elif item:
            values.append(item)
    return values


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
        "confidence": edge.confidence,
        "status": edge.status,
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
    if node.type in {"topic", "topico"} and node.label:
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
    if node.type in {"topic", "topico"}:
        titles = ", ".join(note.title for note in notes[:3])
        return (
            f"Topic extracted from: {titles}."
            if titles
            else "Topic detected from note headings."
        )
    if node.type in {"entity", "entidade"}:
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


def _display_concept_name(normalized: str) -> str:
    return normalized


def _node_key(node_type: str, source_id: int) -> str:
    return f"{node_type}:{source_id}"


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
    confidence: float = 0.7,
    status: str = "suggested",
    model: str = "",
) -> GraphNodeRecord | None:
    normalized_label = normalize_concept_name(label)
    if not normalized_label:
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
        confidence=confidence,
        created_by=created_by,
        model=model or "deterministic",
        status=status,
        source_quality="extracted",
        learning_value=node_type[:20],
        graph_metadata={"evidence": merged_evidence},
    )
    return None if existing is not None else node


def _extract_topics_from_metadata(
    session: Session, metadata_by_note: dict[int, list[GeneratedMetadataRecord]]
) -> int:
    count = 0
    seen: set[tuple[int, str]] = set()
    note_titles = {
        note.id: normalize_concept_name(note.title)
        for note in session.execute(select(NoteRecord)).scalars()
    }
    for note_id, records in metadata_by_note.items():
        for record in records:
            content = _parse_json_object(record.content)
            if not isinstance(content, dict):
                continue
            for key in ("topics", "tags", "categories", "note_type"):
                values = content.get(key)
                if not values:
                    continue
                if isinstance(values, str):
                    values = [v.strip() for v in values.split(",") if v.strip()]
                if not isinstance(values, list):
                    continue
                for topic_name in values:
                    name = (
                        str(topic_name.get("name", topic_name))
                        if isinstance(topic_name, dict)
                        else str(topic_name)
                    )
                    normalized_name = normalize_concept_name(name)
                    if not _is_valid_topic_name(name, note_titles.get(note_id, "")):
                        continue
                    seen_key = (note_id, normalized_name)
                    if not name or seen_key in seen:
                        continue
                    seen.add(seen_key)
                    node = _upsert_typed_node(
                        session,
                        "topico",
                        name,
                        name,
                        f"Topic detected in note metadata: {name}",
                        "metadata",
                        record.id,
                        [note_id],
                        [name],
                        "system",
                        confidence=0.6,
                        status="suggested",
                        model=record.model_used or "",
                    )
                    if node:
                        count += 1
            headings = content.get("headings")
            if isinstance(headings, list):
                for h in headings:
                    if not isinstance(h, dict):
                        continue
                    name = str(h.get("text", "")).strip()
                    normalized_name = normalize_concept_name(name)
                    if not _is_valid_topic_name(name, note_titles.get(note_id, "")):
                        continue
                    seen_key = (note_id, normalized_name)
                    if not name or seen_key in seen or len(name) < 3:
                        continue
                    seen.add(seen_key)
                    node = _upsert_typed_node(
                        session,
                        "topico",
                        name,
                        name,
                        "Topic extracted from note headings",
                        "metadata",
                        record.id,
                        [note_id],
                        [name],
                        "system",
                        confidence=0.5,
                        status="suggested",
                        model="content-based",
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
    for note_id, records in metadata_by_note.items():
        for record in records:
            content = _parse_json_object(record.content)
            if not isinstance(content, dict):
                continue
            for key in ("technical_terms", "entities", "tools", "technologies"):
                values = content.get(key)
                if not values:
                    continue
                if isinstance(values, str):
                    values = [v.strip() for v in values.split(",") if v.strip()]
                if not isinstance(values, list):
                    continue
                for ent in values:
                    name = (
                        str(ent.get("name", ent)) if isinstance(ent, dict) else str(ent)
                    )
                    normalized_name = normalize_concept_name(name)
                    if normalized_name == note_titles.get(note_id):
                        continue
                    seen_key = (note_id, normalized_name)
                    if not name or seen_key in seen:
                        continue
                    seen.add(seen_key)
                    node = _upsert_typed_node(
                        session,
                        "entidade",
                        name,
                        name,
                        f"Entity detected in metadata: {name}",
                        "metadata",
                        record.id,
                        [note_id],
                        [name],
                        "system",
                        confidence=0.6,
                        status="suggested",
                        model=record.model_used or "",
                    )
                    if node:
                        count += 1
            headings = content.get("headings")
            if isinstance(headings, list):
                for h in headings:
                    if not isinstance(h, dict):
                        continue
                    name = str(h.get("text", "")).strip()
                    normalized_name = normalize_concept_name(name)
                    if normalized_name == note_titles.get(note_id):
                        continue
                    seen_key = (note_id, normalized_name)
                    if not name or seen_key in seen or len(name) < 4:
                        continue
                    seen.add(seen_key)
                    node = _upsert_typed_node(
                        session,
                        "entidade",
                        name,
                        name,
                        "Entity extracted from note headings",
                        "metadata",
                        record.id,
                        [note_id],
                        [name],
                        "system",
                        confidence=0.45,
                        status="suggested",
                        model="content-based",
                    )
                    if node:
                        count += 1
    return count


def _extract_context_from_metadata(
    session: Session, metadata_by_note: dict[int, list[GeneratedMetadataRecord]]
) -> int:
    count = 0
    seen: set[tuple[int, str]] = set()
    for note_id, records in metadata_by_note.items():
        for record in records:
            content = _parse_json_object(record.content)
            if not isinstance(content, dict):
                continue
            for key in ("context", "domain", "language", "scope"):
                val = content.get(key)
                if not val:
                    continue
                if isinstance(val, dict):
                    domain = val.get("domain", "")
                    if domain:
                        val = domain
                ctx_name = str(val).strip()
                seen_key = (note_id, normalize_concept_name(ctx_name))
                if not _is_valid_context_name(ctx_name) or seen_key in seen:
                    continue
                seen.add(seen_key)
                node = _upsert_typed_node(
                    session,
                    "contexto",
                    ctx_name,
                    ctx_name,
                    f"Detected context: {ctx_name}",
                    "metadata",
                    record.id,
                    [note_id],
                    [ctx_name],
                    "system",
                    confidence=0.5,
                    status="suggested",
                    model=record.model_used or "",
                )
                if node:
                    count += 1
            note_type = content.get("note_type")
            if isinstance(note_type, str) and note_type.strip():
                nt = note_type.strip()
                seen_key = (note_id, normalize_concept_name(nt))
                if seen_key not in seen and _is_valid_context_name(nt):
                    seen.add(seen_key)
                    node = _upsert_typed_node(
                        session,
                        "contexto",
                        nt,
                        nt,
                        f"Note type: {nt}",
                        "metadata",
                        record.id,
                        [note_id],
                        [nt],
                        "system",
                        confidence=0.5,
                        status="suggested",
                        model="deterministic",
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
        "pt br",
        "pt-br",
        "unknown",
        "general",
        "outro",
        "nao especificado no prompt",
        "não especificado no prompt",
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
                        "lacuna",
                        name,
                        name,
                        desc or f"Lacuna detectada: {name}",
                        "metadata",
                        record.id,
                        [note_id],
                        [name],
                        "system",
                        confidence=0.5,
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
        for key in ("source", "fonte", "source_url", "references", "origin"):
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
                        "fonte",
                        name,
                        name,
                        f"Fonte mencionada no frontmatter: {name}",
                        "frontmatter",
                        note.id,
                        [note.id],
                        [name],
                        "system",
                        confidence=0.7,
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
                    "fonte",
                    val.strip(),
                    val.strip(),
                    f"Fonte mencionada no frontmatter: {val.strip()}",
                    "frontmatter",
                    note.id,
                    [note.id],
                    [val.strip()],
                    "system",
                    confidence=0.7,
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
