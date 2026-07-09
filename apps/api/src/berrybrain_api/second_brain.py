from __future__ import annotations

import json
import re
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import HTTPException
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from berrybrain_api.ai_gateway import (
    GraphAIUnavailable,
    generate_graph_answer,
    get_ai_config,
)
from berrybrain_api.models import (
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
    nodes = list(session.execute(select(GraphNodeRecord)).scalars())
    by_key: dict[tuple[str, str], list[GraphNodeRecord]] = defaultdict(list)
    for n in nodes:
        if n.type == "insight":
            continue
        if n.type == "note" and n.source_id:
            by_key[(n.type, f"source:{n.source_id}")].append(n)
            continue
        key = normalize_concept_name(n.label or "")
        if key:
            by_key[(n.type, key)].append(n)
    merged = 0
    for key, group in by_key.items():
        if len(group) < 2:
            continue
        group.sort(key=lambda n: n.confidence or 0, reverse=True)
        survivor = group[0]
        for victim in group[1:]:
            for edge in session.execute(
                select(GraphEdgeRecord).where(
                    GraphEdgeRecord.source_node_id == victim.id
                )
            ).scalars():
                edge.source_node_id = survivor.id
            for edge in session.execute(
                select(GraphEdgeRecord).where(
                    GraphEdgeRecord.target_node_id == victim.id
                )
            ).scalars():
                edge.target_node_id = survivor.id
            sur_ids = set(_parse_json_list(survivor.source_note_ids))
            vic_ids = set(_parse_json_list(victim.source_note_ids))
            survivor.source_note_ids = _dump_json(sorted(sur_ids | vic_ids))
            survivor.confidence = max(survivor.confidence, victim.confidence or 0)
            session.delete(victim)
            merged += 1
    if merged:
        session.flush()
        _delete_duplicate_edges(session)
    return merged


def _delete_duplicate_edges(session: Session) -> int:
    edges = list(session.execute(select(GraphEdgeRecord)).scalars())
    seen: dict[tuple[int, int, str], GraphEdgeRecord] = {}
    deleted = 0
    for edge in edges:
        key = (edge.source_node_id, edge.target_node_id, edge.type)
        existing = seen.get(key)
        if existing is None:
            seen[key] = edge
            continue
        existing.confidence = max(existing.confidence or 0, edge.confidence or 0)
        evidence = set(_parse_json_list(existing.evidence)) | set(
            _parse_json_list(edge.evidence)
        )
        source_note_ids = set(_parse_json_list(existing.source_note_ids)) | set(
            _parse_json_list(edge.source_note_ids)
        )
        existing.evidence = _dump_json(sorted(evidence))
        existing.source_note_ids = _dump_json(sorted(source_note_ids))
        if not existing.reason and edge.reason:
            existing.reason = edge.reason
        session.delete(edge)
        deleted += 1
    if deleted:
        session.flush()
    return deleted


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
                label="conceito compartilhado",
                reason=f'A nota menciona o conceito "{concept_node.label}".',
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
                        f'As notas "{source_note.title}" e "{target_note.title}" '
                        f'compartilham o conceito "{concept_node.label}".'
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
                            label="conceito compartilhado",
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
                    label="contexto compartilhado",
                    reason=(
                        f'Os conceitos "{left.label}" e "{right.label}" aparecem '
                        f'juntos na nota "{note.title}".'
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
                reason=f'A nota "{source.title}" referencia "{target.title}" por backlink.',
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
                label=f"{typed_node.type}↔nota",
                reason=f'"{typed_node.label}" extraído da nota "{note_node.label}"',
                evidence=[typed_node.label, note_node.label],
                source_note_ids=[note_id],
                created_by="system",
                status="suggested",
            )
            if edge:
                edges_count += 1

    session.commit()
    total_nodes = (
        len(note_nodes)
        + len(concept_nodes)
        + topics_count
        + entities_count
        + context_count
        + gaps_count
        + sources_count
    )
    return {
        "notes": len(notes),
        "concepts": concepts_count,
        "topics": topics_count,
        "entities": entities_count,
        "contexts": context_count,
        "gaps": gaps_count,
        "sources": sources_count,
        "nodes": total_nodes,
        "edges": edges_count,
        "connections": connections_count,
        "insights": insights_count,
    }


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
            session.execute(
                delete(GraphEdgeRecord).where(
                    (GraphEdgeRecord.source_node_id == node.id)
                    | (GraphEdgeRecord.target_node_id == node.id)
                )
            )
            session.delete(node)
        session.delete(concept)
        removed += 1
    if removed:
        session.flush()
    return removed


def _delete_graph_node_with_edges(session: Session, node: GraphNodeRecord) -> None:
    session.execute(
        delete(GraphEdgeRecord).where(
            (GraphEdgeRecord.source_node_id == node.id)
            | (GraphEdgeRecord.target_node_id == node.id)
        )
    )
    session.delete(node)


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

    if not matches:
        return _insufficient(question)

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
            "Destacar no grafo",
            "Criar insight",
            "Criar nota permanente",
            "Gerar revisão",
        ],
    }


def _generate_graph_insights(session: Session) -> int:
    insights = list(session.execute(select(InsightRecord)).scalars())
    for insight in insights:
        existing = session.execute(
            select(GraphNodeRecord).where(
                GraphNodeRecord.type == "insight",
                GraphNodeRecord.source == "insight",
                GraphNodeRecord.source_id == insight.id,
            )
        ).scalar_one_or_none()
        if existing:
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

    return 0


async def infer_from_graph_with_ai(session: Session, question: str) -> dict[str, Any]:
    evidence_base = infer_from_graph(session, question)
    if evidence_base["status"] != "answered":
        evidence_base = _build_graph_context_for_ai(session, question)
    if evidence_base["status"] == "insufficient_evidence":
        return evidence_base

    config = get_ai_config(session)
    system = (
        "Voce e o modulo de inferencia do grafo do BerryBrain. "
        "Responda em pt-BR somente com base nas evidencias fornecidas. "
        "Se a evidencia nao sustentar a resposta, retorne status insufficient_evidence. "
        "Responda JSON com: status, answer, evidence, relatedNodes, suggestions."
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
                "Nao invente conexoes sem evidencia.",
                "Cite as evidencias usadas.",
                "Mantenha a resposta curta e acionavel.",
                "Se a pergunta pedir busca/listagem, use os nos e arestas enviados.",
            ],
        }
    )
    try:
        ai_result = await generate_graph_answer(config, prompt, system)
    except (GraphAIUnavailable, Exception) as exc:
        return {
            **evidence_base,
            "status": "waiting_provider",
            "answer": f"IA configurada indisponivel para inferir no grafo: {exc}",
            "provider": config.get("provider", ""),
            "model": config.get("cloud_model") or config.get("ollama_model") or "",
        }

    status = str(ai_result.get("status") or "answered")
    evidence = ai_result.get("evidence")
    if not isinstance(evidence, list) or not evidence:
        return {
            **evidence_base,
            "status": "insufficient_evidence",
            "answer": "A IA nao retornou evidencias suficientes para sustentar essa inferencia.",
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
            "evidence": [f"Nota: {note.title} ({note.path})" for note in notes[:12]],
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
            "actions": ["Destacar no grafo", "Criar insight", "Criar nota permanente"],
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
        "actions": ["Destacar no grafo", "Criar insight", "Criar nota permanente"],
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
        "metadata": _parse_json_object(node.graph_metadata),
        "notes": [
            {"id": note.id, "title": note.title, "path": note.path} for note in notes
        ],
        "connections": [_serialize_edge(edge) for edge in edges],
        "whyThisExists": _why_node_exists(node, notes),
    }


def set_node_status(session: Session, node_id: int, status: str) -> GraphNodeRecord:
    node = session.get(GraphNodeRecord, node_id)
    if node is None:
        raise HTTPException(status_code=404, detail="Graph node not found")
    node.status = status
    node.updated_at = datetime.now(UTC)
    session.commit()
    session.refresh(node)
    return node


def set_node_user_notes(session: Session, node_id: int, notes: str) -> GraphNodeRecord:
    node = session.get(GraphNodeRecord, node_id)
    if node is None:
        raise HTTPException(status_code=404, detail="Graph node not found")
    node.user_notes = notes
    node.updated_at = datetime.now(UTC)
    session.commit()
    session.refresh(node)
    return node


def set_edge_status(session: Session, edge_id: int, status: str) -> GraphEdgeRecord:
    edge = session.get(GraphEdgeRecord, edge_id)
    if edge is None:
        raise HTTPException(status_code=404, detail="Graph edge not found")
    edge.status = status
    edge.updated_at = datetime.now(UTC)
    session.commit()
    session.refresh(edge)
    return edge


def set_edge_user_notes(session: Session, edge_id: int, notes: str) -> GraphEdgeRecord:
    edge = session.get(GraphEdgeRecord, edge_id)
    if edge is None:
        raise HTTPException(status_code=404, detail="Graph edge not found")
    edge.user_notes = notes
    edge.updated_at = datetime.now(UTC)
    session.commit()
    session.refresh(edge)
    return edge


def normalize_concept_name(value: str) -> str:
    cleaned = re.sub(r"[-_]+", " ", value.strip().lower())
    cleaned = re.sub(r"\s+", " ", cleaned)
    cleaned = re.sub(r"^[#/\\-]+|[#/\\-]+$", "", cleaned)
    if len(cleaned) < 3 or cleaned in STOPWORDS:
        return ""
    return cleaned[:120]


def _upsert_note_node(session: Session, note: NoteRecord) -> GraphNodeRecord:
    node = session.execute(
        select(GraphNodeRecord).where(
            GraphNodeRecord.type == "note",
            GraphNodeRecord.source_id == note.id,
        )
    ).scalar_one_or_none()
    metadata = {
        "path": note.path,
        "folder": note.path.split("/")[0] if "/" in note.path else "inbox",
        "status": note.status,
    }
    if node is None:
        node = GraphNodeRecord(type="note", label=note.title, source_id=note.id)
        session.add(node)
        session.flush()
    node.label = note.title
    node.title = note.title
    node.summary = f"Nota do vault: {note.path}"
    node.ai_notes = (
        "Subagent graph-expander: vertice criado a partir de nota real do vault; "
        "use o caminho da nota como origem auditavel."
    )
    node.source = "note"
    node.source_note_ids = _dump_json([note.id])
    node.confidence = 1.0
    node.created_by = "system"
    node.status = "confirmed"
    node.graph_metadata = _dump_json(metadata)
    node.updated_at = datetime.now(UTC)
    return node


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
    concept.description = concept.description or f'Conceito detectado: "{name}".'
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
    node = session.execute(
        select(GraphNodeRecord).where(
            GraphNodeRecord.type == "concept",
            GraphNodeRecord.source_id == concept.id,
        )
    ).scalar_one_or_none()
    if node is None:
        normalized = concept.normalized_name or normalize_concept_name(concept.name)
        existing = session.execute(
            select(GraphNodeRecord).where(
                GraphNodeRecord.type != "note",
                GraphNodeRecord.type != "insight",
                GraphNodeRecord.label == concept.name,
            )
        ).scalar_one_or_none()
        if existing is None and normalized:
            candidates = session.execute(
                select(GraphNodeRecord).where(
                    GraphNodeRecord.type != "note",
                    GraphNodeRecord.type != "insight",
                )
            ).scalars()
            existing = next(
                (
                    n
                    for n in candidates
                    if normalize_concept_name(n.label) == normalized
                ),
                None,
            )
        if existing is not None:
            node = existing
            node.source = node.source or "concept_extraction"
        else:
            node = GraphNodeRecord(
                type="concept", label=concept.name, source_id=concept.id
            )
            session.add(node)
            session.flush()
    node.label = concept.name
    node.title = concept.name
    node.summary = concept.description
    node.ai_notes = (
        "Subagent concept-extractor: vertice conceitual criado a partir de "
        "metadados/conceitos extraidos das notas relacionadas."
    )
    node.source = "concept_extraction"
    node.source_note_ids = concept.related_note_ids
    node.confidence = concept.confidence
    node.created_by = concept.extracted_by
    node.created_by_model = concept.model
    node.status = concept.status
    node.graph_metadata = _dump_json(
        {
            "normalizedName": concept.normalized_name,
            "frequency": concept.frequency,
            "sourceEvidence": _parse_json_list(concept.source_evidence),
            "relatedNoteCount": len(note_ids),
        }
    )
    node.updated_at = datetime.now(UTC)
    return node


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
        f"Subagent connection-reasoner: conexao {connection_type} criada com "
        f"confianca {confidence}% usando evidencia registrada."
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
) -> GraphEdgeRecord | None:
    if not reason or not evidence:
        return None
    edge = session.execute(
        select(GraphEdgeRecord).where(
            GraphEdgeRecord.source_node_id == source_node_id,
            GraphEdgeRecord.target_node_id == target_node_id,
            GraphEdgeRecord.type == edge_type,
        )
    ).scalar_one_or_none()
    if edge is None:
        edge = GraphEdgeRecord(
            source_node_id=source_node_id,
            target_node_id=target_node_id,
            type=edge_type,
        )
        session.add(edge)
        session.flush()
    edge.label = label
    edge.reason = reason
    edge.evidence = _dump_json(evidence)
    edge.ai_notes = (
        f"Subagent graph-expander: aresta {edge_type} criada porque ha evidencia "
        "persistida conectando estes vertices."
    )
    edge.source_note_ids = _dump_json(source_note_ids)
    edge.confidence = 1.0 if status == "confirmed" else 0.7
    edge.created_by = created_by
    edge.created_by_model = "metadata-parser"
    edge.provider = "deterministic"
    edge.model = "metadata-parser"
    edge.prompt_version = PROMPT_VERSION
    edge.status = status
    edge.updated_at = datetime.now(UTC)
    return edge


def _extract_note_concepts(
    note: NoteRecord, metadata: list[GeneratedMetadataRecord]
) -> list[tuple[str, str, str]]:
    concepts: list[tuple[str, str, str]] = []
    note_title_key = normalize_concept_name(note.title)
    for record in metadata:
        content = _parse_json_object(record.content)
        values: list[Any] = []
        if record.generation_type == "concepts":
            values = _extract_values(content, ["concepts", "items", "keywords"])
        elif record.generation_type == "summary":
            values = _extract_values(content, ["concepts", "keywords"])
        for value in values:
            if isinstance(value, dict):
                name = str(value.get("name") or value.get("title") or "")
            else:
                name = str(value)
            normalized = normalize_concept_name(name)
            if normalized == note_title_key:
                continue
            if _is_valid_concept_name(name):
                concepts.append(
                    (name, f"{note.title}: {name}", record.model_used or "")
                )
    return concepts


def _is_valid_concept_name(name: str) -> bool:
    clean = " ".join(str(name or "").strip().split())
    if len(clean) < 2 or len(clean) > 80:
        return False
    if len(clean.split()) > 8:
        return False
    lowered = clean.lower()
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
    concepts = [(title, f"Título da nota: {title}", "")]
    concepts.extend((part, f"Título da nota: {title}", "") for part in parts)
    return concepts


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
        parts.append(f"Vem destas notas: {', '.join(note_titles)}.")
    if edge_types:
        type_names = {
            "backlink": "backlinks",
            "semantic": "semânticas",
            "shared_concept": "conceitos compartilhados",
            "related": "relações",
        }
        conn_list = [
            f"{edge_types[t]} {type_names.get(t, t)}"
            for t in sorted(edge_types.keys())[:4]
        ]
        parts.append(f"Conecta-se por: {', '.join(conn_list)}.")
    if node.type == "note" and len(notes) == 1:
        snippet = (getattr(notes[0], "content", "") or "")[:150].strip()
        if snippet:
            parts.append(f'Conteúdo: "{snippet}..."')
    if node.type == "topico" and node.label:
        parts.append(
            f"É um tópico extraído das notas. Expanda-o como nota permanente ou conecte-o a outros conceitos."
        )
    if node.type == "concept" and node.label:
        parts.append(
            f"Conceito recorrente. Relacione-o com notas para fortalecer o grafo."
        )
    return (
        " ".join(parts)
        if parts
        else "Nó do grafo de conhecimento. Clique para ver conexões e notas de origem."
    )


def _why_node_exists(node: GraphNodeRecord, notes: list[NoteRecord]) -> str:
    if node.type == "note":
        path = notes[0].path if notes else ""
        folder = path.split("/")[0] if "/" in path else ""
        return f"Esta nota está no vault{f' em {folder}' if folder else ''}."
    if node.type == "concept":
        titles = ", ".join(note.title for note in notes[:3])
        return (
            f"Extraído de: {titles}." if titles else "Extraído de metadados do sistema."
        )
    if node.type == "topico":
        titles = ", ".join(note.title for note in notes[:3])
        return (
            f"Tópico extraído de: {titles}."
            if titles
            else "Tópico detectado nos headings das notas."
        )
    if node.type == "entidade":
        return "Entidade técnica detectada nos metadados."
    return f"Este nó ({node.type}) foi criado pelo pipeline de conhecimento."


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
        "answer": "Ainda não há evidência suficiente no seu grafo para afirmar essa relação.",
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
    candidates = session.execute(
        select(GraphNodeRecord).where(
            GraphNodeRecord.type == node_type,
            GraphNodeRecord.source == source,
        )
    ).scalars()
    existing = next(
        (
            node
            for node in candidates
            if normalize_concept_name(node.label) == normalized_label
        ),
        None,
    )
    if existing is None:
        all_candidates = session.execute(
            select(GraphNodeRecord).where(
                GraphNodeRecord.type != "note",
                GraphNodeRecord.type != "insight",
            )
        ).scalars()
        existing = next(
            (
                node
                for node in all_candidates
                if normalize_concept_name(node.label) == normalized_label
            ),
            None,
        )
    if existing is not None:
        existing.label = label or existing.label
        existing.title = title or existing.title
        existing.summary = summary or existing.summary
        existing.source_note_ids = _dump_json(
            sorted(
                {
                    int(item)
                    for item in _parse_json_list(existing.source_note_ids)
                    + source_note_ids
                    if str(item).isdigit()
                }
            )
        )
        metadata = _parse_json_object(existing.graph_metadata)
        previous_evidence = metadata.get("evidence")
        if not isinstance(previous_evidence, list):
            previous_evidence = []
        metadata["evidence"] = sorted(
            {str(item) for item in previous_evidence + evidence if str(item)}
        )
        existing.graph_metadata = _dump_json(metadata)
        existing.confidence = max(existing.confidence, confidence)
        existing.updated_at = datetime.now(UTC)
        return None
    node = GraphNodeRecord(
        type=node_type,
        label=label,
        title=title,
        summary=summary,
        source=source,
        source_id=source_id,
        source_note_ids=_dump_json(source_note_ids),
        confidence=confidence,
        created_by=created_by,
        created_by_model=model or "deterministic",
        status=status,
        graph_metadata=_dump_json({"evidence": evidence}),
    )
    session.add(node)
    session.flush()
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
                        f"Tópico detectado nos metadados da nota: {name}",
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
                        f"Tópico extraído dos headings da nota",
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
                        f"Entidade detectada nos metadados: {name}",
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
                        f"Entidade extraída dos headings da nota",
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
                if not ctx_name or len(ctx_name) < 3 or seen_key in seen:
                    continue
                seen.add(seen_key)
                node = _upsert_typed_node(
                    session,
                    "contexto",
                    ctx_name,
                    ctx_name,
                    f"Contexto detectado: {ctx_name}",
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
                if seen_key not in seen and nt not in ("unknown", "general", "outro"):
                    seen.add(seen_key)
                    node = _upsert_typed_node(
                        session,
                        "contexto",
                        nt,
                        nt,
                        f"Tipo de nota: {nt}",
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
