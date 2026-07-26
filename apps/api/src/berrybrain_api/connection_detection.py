from __future__ import annotations

import hashlib
import json
import sys
from datetime import UTC, datetime
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
from berrybrain_api.models import (
    ChunkRecord,
    ConnectionRecord,
    GraphNodeRecord,
    NoteRecord,
)

# Constants from second_brain
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


def _parse_json_list(value: str | None) -> list[Any]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return []
    return parsed if isinstance(parsed, list) else []


def _dump_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


async def generate_inferred_graph_connections(
    session: Session, max_pairs: int = 20
) -> dict[str, int]:
    """Use AI to find non-obvious connections between existing graph nodes.

    Only one AI provider is used (cloud NVIDIA NIM or local Ollama), never both.
    Respects auto_confirm_confidence for edge status.
    """
    facade = sys.modules.get("berrybrain_api.second_brain")
    config_fn = getattr(facade, "get_ai_config", get_ai_config)
    generate_fn = getattr(facade, "generate_graph_answer", generate_graph_answer)
    config = config_fn(session)
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
        result = await generate_fn(config, prompt, system)
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
    if not (
        conn.status in {"confirmed", "accepted", "applied", "reviewed"}
        and status == "suggested"
    ):
        conn.status = status
    conn.updated_at = datetime.now(UTC)
    return conn
