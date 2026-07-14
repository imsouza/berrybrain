from __future__ import annotations

import json
import hashlib
import math
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from berrybrain_api.assimilation import note_assimilation_map
from berrybrain_api.ai_gateway import (
    GraphAIUnavailable,
    generate_graph_answer,
    get_ai_config,
)
from berrybrain_api.models import (
    AttachmentExtractionRecord,
    EmbeddingRecord,
    GraphEdgeRecord,
    GraphNodeRecord,
    InsightRecord,
    JobRecord,
    NoteAttachmentRecord,
    NoteRecord,
    SettingRecord,
)


TOKEN_RE = re.compile(r"[a-zA-ZÀ-ÿ0-9][a-zA-ZÀ-ÿ0-9_-]{2,}")
VECTOR_DIMENSIONS = 64


@dataclass
class RetrievalEvidence:
    source: str
    title: str
    text: str
    score: float
    metadata: dict[str, Any]


def cognitive_status(session: Session) -> dict[str, Any]:
    note_rows = list(session.execute(select(NoteRecord)).scalars())
    notes = len(note_rows)
    processable_notes = [note for note in note_rows if (note.content or "").strip()]
    embeddings = session.query(func.count(EmbeddingRecord.id)).scalar() or 0
    nodes = session.query(func.count(GraphNodeRecord.id)).scalar() or 0
    edges = session.query(func.count(GraphEdgeRecord.id)).scalar() or 0
    insights = session.query(func.count(InsightRecord.id)).scalar() or 0
    jobs = dict(
        session.execute(
            select(JobRecord.status, func.count()).group_by(JobRecord.status)
        ).all()
    )
    config = get_ai_config(session)
    cognitive = cognitive_config(session)
    return {
        "name": "BerryBrain Knowledge System",
        "localFirst": True,
        "knowledgeBase": {
            "store": cognitive["kb_vector_store"],
            "qdrant": "configured" if cognitive["qdrant_url"] else "optional",
            "chroma": "configured" if cognitive["chroma_url"] else "optional",
            "chunkSize": cognitive["kb_chunk_size"],
            "chunkOverlap": cognitive["kb_chunk_overlap"],
            "embeddingProvider": cognitive["kb_embedding_provider"],
            "embeddingModel": cognitive["kb_embedding_model"],
            "notesIndexed": notes,
            "processableNotes": len(processable_notes),
            "embeddings": embeddings,
            "status": "ready" if processable_notes else "empty",
        },
        "knowledgeGraph": {
            "store": "sqlite",
            "neo4j": "optional_future",
            "nodes": nodes,
            "edges": edges,
            "insights": insights,
        },
        "semanticDataLayer": {
            "jobs": jobs,
            "status": "ready",
        },
        "modelRouter": {
            "provider": config.get("provider", "local"),
            "model": config.get("cloud_model") or config.get("ollama_model") or "",
        },
        "retrievalOrchestrator": {
            "mode": cognitive["cognitive_retrieval_mode"],
            "routes": ["knowledge_base", "knowledge_graph", "semantic_data"],
        },
        "settings": cognitive,
    }


def index_knowledge_base(session: Session) -> dict[str, Any]:
    cognitive = cognitive_config(session)
    chunk_size = _int_setting(cognitive["kb_chunk_size"], 900, 300, 4000)
    notes = list(session.execute(select(NoteRecord)).scalars())
    processable_notes = [note for note in notes if (note.content or "").strip()]
    attachment_chunks = _attachment_chunks(session, chunk_size)
    embeddings = {
        emb.note_id: emb for emb in session.execute(select(EmbeddingRecord)).scalars()
    }
    chunk_records = _knowledge_chunks(processable_notes, chunk_size) + attachment_chunks
    chunk_count = len(chunk_records)
    external_sync = sync_external_vector_store(cognitive, chunk_records)
    missing_embeddings = [
        note.path for note in processable_notes if note.id not in embeddings
    ]
    skipped_empty = [note.path for note in notes if not (note.content or "").strip()]
    return {
        "status": "indexed",
        "store": cognitive["kb_vector_store"],
        "qdrant": "configured" if cognitive["qdrant_url"] else "not_configured",
        "chroma": "configured" if cognitive["chroma_url"] else "not_configured",
        "chunkSize": chunk_size,
        "chunkOverlap": _int_setting(cognitive["kb_chunk_overlap"], 120, 0, 1000),
        "embeddingProvider": cognitive["kb_embedding_provider"],
        "embeddingModel": cognitive["kb_embedding_model"],
        "notes": len(notes),
        "processableNotes": len(processable_notes),
        "skippedEmptyNotes": skipped_empty[:20],
        "chunks": chunk_count,
        "attachmentChunks": len(attachment_chunks),
        "embeddings": len(embeddings),
        "externalVectorStore": external_sync,
        "missingEmbeddings": missing_embeddings[:20],
        "updatedAt": datetime.now(UTC).isoformat(),
    }


def sync_external_vector_store(
    cognitive: dict[str, str],
    chunk_records: list[dict[str, Any]],
) -> dict[str, Any]:
    store = cognitive["kb_vector_store"]
    if store == "qdrant":
        if not cognitive["qdrant_url"]:
            return {"status": "skipped", "store": "qdrant", "reason": "missing_url"}
        try:
            return _sync_qdrant(cognitive, chunk_records)
        except Exception as exc:
            return {"status": "failed", "store": "qdrant", "error": str(exc)[:240]}
    if store == "chroma":
        if not cognitive["chroma_url"]:
            return {"status": "skipped", "store": "chroma", "reason": "missing_url"}
        try:
            return _sync_chroma(cognitive, chunk_records)
        except Exception as exc:
            return {"status": "failed", "store": "chroma", "error": str(exc)[:240]}
    return {"status": "skipped", "store": "sqlite", "reason": "local_fallback"}


async def answer_cognitive_query(session: Session, question: str) -> dict[str, Any]:
    orchestrated = orchestrate_retrieval(session, question)
    evidence = orchestrated["evidence"]
    if not evidence:
        return {
            "status": "insufficient_evidence",
            "question": question,
            "answer": "There is not enough evidence in your BerryBrain data to answer this.",
            "routes": orchestrated["routes"],
            "evidence": [],
            "relatedNodes": [],
            "suggestions": ["Add or process more notes before asking again."],
        }

    config = get_ai_config(session)
    system = (
        "You are BerryBrain Cognitive Layer. Answer only from provided evidence. "
        "Return JSON with status, answer, evidence, relatedNodes, suggestions, "
        "confidence. If evidence is weak, status must be insufficient_evidence."
    )
    prompt = json.dumps(
        {
            "question": question,
            "routes": orchestrated["routes"],
            "semanticState": orchestrated["semanticState"],
            "evidence": evidence[:16],
            "rules": [
                "Do not invent facts.",
                "Cite concrete note/node/edge/job evidence.",
                "Keep the answer useful for learning and graph navigation.",
            ],
        },
        ensure_ascii=False,
    )
    try:
        result = await generate_graph_answer(config, prompt, system, timeout=120)
    except GraphAIUnavailable as exc:
        return _fallback_answer(question, orchestrated, f"AI unavailable: {exc}")
    except urllib.error.HTTPError as exc:
        if exc.code in {401, 403}:
            reason = (
                "NVIDIA NIM authentication failed. Replace the API key in Settings "
                "and save again."
            )
        elif exc.code == 429:
            reason = "The AI provider rate limit was reached. Try again shortly."
        else:
            reason = f"The AI provider returned HTTP {exc.code}. Check Settings."
        return _fallback_answer(question, orchestrated, reason)
    except Exception:
        return _fallback_answer(
            question,
            orchestrated,
            "The AI provider request failed. Check the provider configuration in Settings.",
        )

    answer_text = str(result.get("answer") or "").strip()
    returned_evidence = result.get("evidence")
    if not isinstance(returned_evidence, list) or not returned_evidence:
        # ponytail: model answered but skipped the strict evidence list -> use retrieved evidence
        if not answer_text:
            return _fallback_answer(question, orchestrated, "AI returned no answer.")
        returned_evidence = orchestrated["evidence"][:8]
    if not answer_text:
        return _fallback_answer(question, orchestrated, "AI returned no answer.")
    return {
        "status": str(result.get("status") or "answered"),
        "question": question,
        "answer": answer_text,
        "routes": orchestrated["routes"],
        "evidence": returned_evidence,
        "relatedNodes": result.get("relatedNodes")
        if isinstance(result.get("relatedNodes"), list)
        else orchestrated["relatedNodes"],
        "suggestions": result.get("suggestions")
        if isinstance(result.get("suggestions"), list)
        else [],
        "confidence": float(result.get("confidence") or 0.5),
        "provider": config.get("provider", ""),
        "model": config.get("cloud_model") or config.get("ollama_model") or "",
    }


def orchestrate_retrieval(session: Session, question: str) -> dict[str, Any]:
    cognitive = cognitive_config(session)
    tokens = _tokens(question)
    semantic_needed = bool(
        tokens & {"job", "jobs", "erro", "erros", "fila", "worker", "stats", "status"}
    )
    mode = cognitive["cognitive_retrieval_mode"]
    graph_needed = mode in {"hybrid", "graph_first"}
    kb_needed = mode in {"hybrid", "kb_first"}
    routes = []
    evidence: list[dict[str, Any]] = []
    if kb_needed:
        routes.append("knowledge_base")
        evidence.extend(
            [_evidence_dict(item) for item in retrieve_kb(session, question)]
        )
    if graph_needed or len(evidence) < 4:
        routes.append("knowledge_graph")
        graph_items, related_nodes = retrieve_graph(session, question)
        evidence.extend([_evidence_dict(item) for item in graph_items])
    else:
        related_nodes = []
    semantic_state = {}
    if semantic_needed or cognitive["semantic_data_enabled"] == "true":
        routes.append("semantic_data")
        semantic_state = semantic_data_state(session)
        evidence.append(
            {
                "source": "semantic_data",
                "title": "BerryBrain system state",
                "text": json.dumps(semantic_state, ensure_ascii=False),
                "score": 1.0,
                "metadata": {"type": "system_state"},
            }
        )
    return {
        "routes": list(dict.fromkeys(routes)),
        "evidence": evidence[:20],
        "relatedNodes": related_nodes[:12],
        "semanticState": semantic_state,
    }


def retrieve_kb(
    session: Session, query: str, limit: int = 8
) -> list[RetrievalEvidence]:
    external_results = retrieve_external_kb(session, query, limit=limit)
    if external_results:
        return external_results

    query_tokens = _tokens(query)
    notes = list(session.execute(select(NoteRecord)).scalars())
    results: list[RetrievalEvidence] = []
    for note in notes:
        chunks = chunk_markdown(note.content)
        for index, chunk in enumerate(chunks):
            score = _token_score(query_tokens, _tokens(chunk + " " + note.title))
            if score <= 0:
                continue
            results.append(
                RetrievalEvidence(
                    source="knowledge_base",
                    title=note.title,
                    text=chunk[:900],
                    score=score,
                    metadata={
                        "noteId": note.id,
                        "path": note.path,
                        "chunk": index,
                        "retrieval": "lexical_plus_metadata",
                    },
                )
            )
    attachments = _extracted_attachments(session)
    for attachment, extraction, note in attachments:
        chunks = chunk_markdown(extraction.extracted_text)
        for index, chunk in enumerate(chunks):
            score = _token_score(
                query_tokens,
                _tokens(chunk + " " + attachment.filename + " " + note.title),
            )
            if score <= 0:
                continue
            results.append(
                RetrievalEvidence(
                    source="knowledge_base",
                    title=f"{attachment.filename} ({note.title})",
                    text=chunk[:900],
                    score=score,
                    metadata={
                        "attachmentId": attachment.id,
                        "noteId": note.id,
                        "path": attachment.stored_path,
                        "notePath": note.path,
                        "chunk": index,
                        "kind": "attachment_text",
                        "retrieval": "lexical_plus_metadata",
                    },
                )
            )
    results.sort(key=lambda item: item.score, reverse=True)
    return results[:limit]


def retrieve_external_kb(
    session: Session, query: str, limit: int = 8
) -> list[RetrievalEvidence]:
    cognitive = cognitive_config(session)
    store = cognitive["kb_vector_store"]
    if store == "qdrant" and cognitive["qdrant_url"]:
        try:
            return _retrieve_qdrant(cognitive, query, limit)
        except Exception:
            return []
    if store == "chroma" and cognitive["chroma_url"]:
        try:
            return _retrieve_chroma(cognitive, query, limit)
        except Exception:
            return []
    return []


def retrieve_graph(
    session: Session, query: str, limit: int = 10
) -> tuple[list[RetrievalEvidence], list[str]]:
    query_tokens = _tokens(query)
    nodes = list(
        session.execute(
            select(GraphNodeRecord).where(GraphNodeRecord.status != "ignored")
        ).scalars()
    )
    edges = list(
        session.execute(
            select(GraphEdgeRecord).where(GraphEdgeRecord.status != "ignored")
        ).scalars()
    )
    node_by_id = {node.id: node for node in nodes}
    results: list[RetrievalEvidence] = []
    related_nodes: list[str] = []
    for node in nodes:
        body = " ".join(
            [
                node.label or "",
                node.summary or "",
                node.ai_summary or "",
                node.ai_context or "",
                node.source_evidence or "",
            ]
        )
        score = _token_score(query_tokens, _tokens(body))
        if score <= 0:
            continue
        related_nodes.append(f"{node.type}_{node.id}")
        results.append(
            RetrievalEvidence(
                source="knowledge_graph",
                title=node.label,
                text=(node.ai_context or node.ai_summary or node.summary or node.label)[
                    :900
                ],
                score=score,
                metadata={
                    "nodeId": node.id,
                    "type": node.type,
                    "confidence": node.confidence,
                    "status": node.status,
                    "evidence": _json_list(node.source_evidence),
                    "provider": node.provider,
                    "model": node.model,
                },
            )
        )
    for edge in edges:
        source = node_by_id.get(edge.source_node_id)
        target = node_by_id.get(edge.target_node_id)
        body = " ".join(
            [
                edge.label or "",
                edge.reason or "",
                edge.evidence or "",
                source.label if source else "",
                target.label if target else "",
            ]
        )
        score = _token_score(query_tokens, _tokens(body))
        if score <= 0:
            continue
        if source:
            related_nodes.append(f"{source.type}_{source.id}")
        if target:
            related_nodes.append(f"{target.type}_{target.id}")
        results.append(
            RetrievalEvidence(
                source="knowledge_graph",
                title=edge.label or edge.type,
                text=edge.reason[:900],
                score=score,
                metadata={
                    "edgeId": edge.id,
                    "type": edge.type,
                    "confidence": edge.confidence,
                    "status": edge.status,
                    "evidence": _json_list(edge.evidence),
                    "provider": edge.provider,
                    "model": edge.model,
                },
            )
        )
    results.sort(key=lambda item: item.score, reverse=True)
    return results[:limit], list(dict.fromkeys(related_nodes))


def semantic_data_state(session: Session) -> dict[str, Any]:
    job_counts = dict(
        session.execute(
            select(JobRecord.status, func.count()).group_by(JobRecord.status)
        ).all()
    )
    jobs_by_type = {
        row[0]: {
            "total": row[1],
            "pending": row[2],
            "running": row[3],
            "failed": row[4],
            "completed": row[5],
        }
        for row in session.execute(
            select(
                JobRecord.type,
                func.count(),
                func.sum(case((JobRecord.status == "pending", 1), else_=0)),
                func.sum(case((JobRecord.status == "running", 1), else_=0)),
                func.sum(case((JobRecord.status == "failed", 1), else_=0)),
                func.sum(case((JobRecord.status == "completed", 1), else_=0)),
            ).group_by(JobRecord.type)
        ).all()
    }
    failed_by_type = dict(
        session.execute(
            select(JobRecord.type, func.count())
            .where(JobRecord.status == "failed")
            .group_by(JobRecord.type)
        ).all()
    )
    notes = list(session.execute(select(NoteRecord)).scalars())
    processable_notes = [note for note in notes if (note.content or "").strip()]
    embedding_note_ids = set(session.execute(select(EmbeddingRecord.note_id)).scalars())
    assimilation = note_assimilation_map(session, notes)
    unassimilated = [
        note for note in notes if not assimilation.get(note.id, {}).get("assimilated")
    ]
    graph_nodes = list(session.execute(select(GraphNodeRecord)).scalars())
    visible_nodes = [node for node in graph_nodes if node.status != "ignored"]
    graph_edges = list(session.execute(select(GraphEdgeRecord)).scalars())
    visible_edges = [edge for edge in graph_edges if edge.status != "ignored"]
    visible_nodes_with_ai_context = [
        node for node in visible_nodes if (node.ai_context or "").strip()
    ]
    visible_edges_with_reason = [
        edge for edge in visible_edges if (edge.reason or "").strip()
    ]
    recent_failed = list(
        session.execute(
            select(JobRecord)
            .where(JobRecord.status == "failed")
            .order_by(JobRecord.created_at.desc())
            .limit(8)
        ).scalars()
    )
    active_jobs = list(
        session.execute(
            select(JobRecord)
            .where(JobRecord.status.in_(("pending", "running")))
            .order_by(JobRecord.created_at.asc())
            .limit(12)
        ).scalars()
    )
    config = get_ai_config(session)
    cognitive = cognitive_config(session)
    processable_count = len(processable_notes)
    embeddings_count = len(embedding_note_ids)
    kb_coverage = (
        round(embeddings_count / processable_count, 4) if processable_count else 1.0
    )
    graph_context_coverage = (
        round(len(visible_nodes_with_ai_context) / len(visible_nodes), 4)
        if visible_nodes
        else 1.0
    )
    edge_reason_coverage = (
        round(len(visible_edges_with_reason) / len(visible_edges), 4)
        if visible_edges
        else 1.0
    )
    active_work = (job_counts.get("pending", 0) or 0) + (
        job_counts.get("running", 0) or 0
    )
    return {
        "jobs": job_counts,
        "jobsByType": jobs_by_type,
        "failedByType": failed_by_type,
        "activeJobs": [
            {
                "id": job.id,
                "type": job.type,
                "status": job.status,
                "attempts": job.attempts,
                "createdAt": job.created_at.isoformat() if job.created_at else None,
                "startedAt": job.started_at.isoformat() if job.started_at else None,
            }
            for job in active_jobs
        ],
        "recentFailures": [
            {
                "id": job.id,
                "type": job.type,
                "error": (job.error_message or "")[:240],
                "attempts": job.attempts,
                "createdAt": job.created_at.isoformat() if job.created_at else None,
            }
            for job in recent_failed
        ],
        "notes": len(notes),
        "processableNotes": processable_count,
        "emptyNotes": len(notes) - processable_count,
        "unassimilatedNotes": [
            {
                "id": note.id,
                "title": note.title,
                "path": note.path,
                "status": note.status,
            }
            for note in unassimilated[:20]
        ],
        "knowledgeBase": {
            "store": cognitive["kb_vector_store"],
            "embeddingProvider": cognitive["kb_embedding_provider"],
            "embeddingModel": cognitive["kb_embedding_model"],
            "embeddings": embeddings_count,
            "processableNotes": processable_count,
            "coverage": kb_coverage,
            "missingEmbeddings": [
                {"id": note.id, "title": note.title, "path": note.path}
                for note in processable_notes
                if note.id not in embedding_note_ids
            ][:20],
        },
        "knowledgeGraph": {
            "nodes": len(graph_nodes),
            "visibleNodes": len(visible_nodes),
            "edges": len(graph_edges),
            "visibleEdges": len(visible_edges),
            "visibleNodesWithAiContext": len(visible_nodes_with_ai_context),
            "visibleAiContextCoverage": graph_context_coverage,
            "visibleEdgesWithReason": len(visible_edges_with_reason),
            "edgeReasonCoverage": edge_reason_coverage,
        },
        "insights": session.query(func.count(InsightRecord.id)).scalar() or 0,
        "provider": {
            "mode": config.get("provider", ""),
            "model": config.get("cloud_model") or config.get("ollama_model") or "",
            "embeddingModel": cognitive["kb_embedding_model"],
        },
        "processing": {
            "status": "processing" if active_work else "idle",
            "activeWork": active_work,
            "failedHistory": job_counts.get("failed", 0) or 0,
        },
    }


def chunk_markdown(content: str, max_chars: int = 900) -> list[str]:
    parts = re.split(r"\n(?=#{1,6}\s)", content or "")
    chunks: list[str] = []
    for part in parts:
        text = part.strip()
        if not text:
            continue
        while len(text) > max_chars:
            cut = text.rfind("\n", 0, max_chars)
            if cut < max_chars // 2:
                cut = max_chars
            chunks.append(text[:cut].strip())
            text = text[cut:].strip()
        if text:
            chunks.append(text)
    return chunks or ([content.strip()] if content and content.strip() else [])


def _knowledge_chunks(notes: list[NoteRecord], chunk_size: int) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for note in notes:
        for index, chunk in enumerate(chunk_markdown(note.content, chunk_size)):
            records.append(
                {
                    "id": _stable_chunk_id(note.id, index),
                    "documentId": f"note:{note.id}:chunk:{index}",
                    "noteId": note.id,
                    "title": note.title,
                    "path": note.path,
                    "chunkIndex": index,
                    "text": chunk,
                    "vector": _hash_embedding(" ".join([note.title or "", chunk])),
                    "metadata": {
                        "source": "berrybrain",
                        "kind": "note_chunk",
                        "note_id": note.id,
                        "path": note.path,
                        "title": note.title,
                        "chunk": index,
                    },
                }
            )
    return records


def _attachment_chunks(session: Session, chunk_size: int) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for attachment, extraction, note in _extracted_attachments(session):
        for index, chunk in enumerate(
            chunk_markdown(extraction.extracted_text, chunk_size)
        ):
            records.append(
                {
                    "id": _stable_attachment_chunk_id(attachment.id, index),
                    "documentId": f"attachment:{attachment.id}:chunk:{index}",
                    "noteId": note.id,
                    "attachmentId": attachment.id,
                    "title": attachment.filename,
                    "path": attachment.stored_path,
                    "chunkIndex": index,
                    "text": chunk,
                    "vector": _hash_embedding(
                        " ".join([attachment.filename or "", note.title or "", chunk])
                    ),
                    "metadata": {
                        "source": "berrybrain",
                        "kind": "attachment_text",
                        "note_id": note.id,
                        "attachment_id": attachment.id,
                        "path": attachment.stored_path,
                        "note_path": note.path,
                        "title": attachment.filename,
                        "chunk": index,
                    },
                }
            )
    return records


def _extracted_attachments(
    session: Session,
) -> list[tuple[NoteAttachmentRecord, AttachmentExtractionRecord, NoteRecord]]:
    return list(
        session.execute(
            select(NoteAttachmentRecord, AttachmentExtractionRecord, NoteRecord)
            .join(
                AttachmentExtractionRecord,
                AttachmentExtractionRecord.attachment_id == NoteAttachmentRecord.id,
            )
            .join(NoteRecord, NoteRecord.id == NoteAttachmentRecord.note_id)
            .where(
                AttachmentExtractionRecord.status == "completed",
                AttachmentExtractionRecord.extracted_text != "",
            )
        ).all()
    )


def _stable_attachment_chunk_id(attachment_id: int, index: int) -> str:
    return hashlib.sha1(f"attachment:{attachment_id}:{index}".encode()).hexdigest()


def _stable_chunk_id(note_id: int, chunk_index: int) -> int:
    raw = f"note:{note_id}:chunk:{chunk_index}".encode("utf-8")
    return int(hashlib.sha1(raw).hexdigest()[:15], 16)


def _hash_embedding(text: str, dimensions: int = VECTOR_DIMENSIONS) -> list[float]:
    vector = [0.0] * dimensions
    for token in _tokens(text):
        digest = hashlib.sha1(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:2], "big") % dimensions
        sign = 1.0 if digest[2] % 2 == 0 else -1.0
        vector[index] += sign
    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    return [round(value / norm, 6) for value in vector]


def _sync_qdrant(
    cognitive: dict[str, str], records: list[dict[str, Any]]
) -> dict[str, Any]:
    base_url = cognitive["qdrant_url"].rstrip("/")
    collection = cognitive["qdrant_collection"] or "berrybrain"
    collection_url = f"{base_url}/collections/{collection}"
    _http_json(
        "PUT",
        collection_url,
        {
            "vectors": {
                "size": VECTOR_DIMENSIONS,
                "distance": "Cosine",
            }
        },
        ok_statuses={200, 201, 409},
    )
    points = [
        {
            "id": item["id"],
            "vector": item["vector"],
            "payload": {
                **item["metadata"],
                "document_id": item["documentId"],
                "text": item["text"],
            },
        }
        for item in records
    ]
    upserted = 0
    for batch in _batches(points, 64):
        _http_json(
            "PUT",
            f"{collection_url}/points",
            {"points": batch},
            ok_statuses={200, 201},
        )
        upserted += len(batch)
    return {
        "status": "synced",
        "store": "qdrant",
        "collection": collection,
        "chunks": upserted,
        "vectorSize": VECTOR_DIMENSIONS,
    }


def _sync_chroma(
    cognitive: dict[str, str], records: list[dict[str, Any]]
) -> dict[str, Any]:
    base_url = cognitive["chroma_url"].rstrip("/")
    collection = cognitive["chroma_collection"] or "berrybrain"
    created = _http_json(
        "POST",
        f"{base_url}/api/v1/collections",
        {
            "name": collection,
            "metadata": {"source": "berrybrain"},
            "get_or_create": True,
        },
        ok_statuses={200, 201, 409},
    )
    collection_id = created.get("id") or created.get("name") or collection
    upserted = 0
    for batch in _batches(records, 64):
        _http_json(
            "POST",
            f"{base_url}/api/v1/collections/{collection_id}/upsert",
            {
                "ids": [item["documentId"] for item in batch],
                "embeddings": [item["vector"] for item in batch],
                "metadatas": [item["metadata"] for item in batch],
                "documents": [item["text"] for item in batch],
            },
            ok_statuses={200, 201},
        )
        upserted += len(batch)
    return {
        "status": "synced",
        "store": "chroma",
        "collection": collection,
        "chunks": upserted,
        "vectorSize": VECTOR_DIMENSIONS,
    }


def _retrieve_qdrant(
    cognitive: dict[str, str], query: str, limit: int
) -> list[RetrievalEvidence]:
    base_url = cognitive["qdrant_url"].rstrip("/")
    collection = cognitive["qdrant_collection"] or "berrybrain"
    result = _http_json(
        "POST",
        f"{base_url}/collections/{collection}/points/search",
        {
            "vector": _hash_embedding(query),
            "limit": limit,
            "with_payload": True,
        },
        ok_statuses={200},
    )
    points = result.get("result", [])
    if not isinstance(points, list):
        return []
    evidence: list[RetrievalEvidence] = []
    for point in points:
        if not isinstance(point, dict):
            continue
        payload = point.get("payload") if isinstance(point.get("payload"), dict) else {}
        title = str(payload.get("title") or payload.get("path") or "Knowledge chunk")
        text = str(payload.get("text") or "")
        if not text.strip():
            continue
        score = _float_value(point.get("score"), 0.0)
        evidence.append(
            RetrievalEvidence(
                source="knowledge_base",
                title=title,
                text=text[:900],
                score=score,
                metadata={
                    "retrieval": "qdrant_vector",
                    "store": "qdrant",
                    "collection": collection,
                    "noteId": payload.get("note_id"),
                    "path": payload.get("path"),
                    "chunk": payload.get("chunk"),
                    "documentId": payload.get("document_id"),
                },
            )
        )
    return evidence


def _retrieve_chroma(
    cognitive: dict[str, str], query: str, limit: int
) -> list[RetrievalEvidence]:
    base_url = cognitive["chroma_url"].rstrip("/")
    collection = cognitive["chroma_collection"] or "berrybrain"
    created = _http_json(
        "POST",
        f"{base_url}/api/v1/collections",
        {
            "name": collection,
            "metadata": {"source": "berrybrain"},
            "get_or_create": True,
        },
        ok_statuses={200, 201, 409},
    )
    collection_id = created.get("id") or created.get("name") or collection
    result = _http_json(
        "POST",
        f"{base_url}/api/v1/collections/{collection_id}/query",
        {
            "query_embeddings": [_hash_embedding(query)],
            "n_results": limit,
            "include": ["documents", "metadatas", "distances"],
        },
        ok_statuses={200},
    )
    documents = _first_nested_list(result.get("documents"))
    metadatas = _first_nested_list(result.get("metadatas"))
    distances = _first_nested_list(result.get("distances"))
    evidence: list[RetrievalEvidence] = []
    for index, document in enumerate(documents):
        text = str(document or "")
        if not text.strip():
            continue
        metadata = (
            metadatas[index]
            if index < len(metadatas) and isinstance(metadatas[index], dict)
            else {}
        )
        distance = _float_value(
            distances[index] if index < len(distances) else None, 1.0
        )
        evidence.append(
            RetrievalEvidence(
                source="knowledge_base",
                title=str(
                    metadata.get("title") or metadata.get("path") or "Knowledge chunk"
                ),
                text=text[:900],
                score=round(1 / (1 + max(distance, 0.0)), 6),
                metadata={
                    "retrieval": "chroma_vector",
                    "store": "chroma",
                    "collection": collection,
                    "noteId": metadata.get("note_id"),
                    "path": metadata.get("path"),
                    "chunk": metadata.get("chunk"),
                },
            )
        )
    return evidence


def _http_json(
    method: str,
    url: str,
    payload: dict[str, Any],
    ok_statuses: set[int],
) -> dict[str, Any]:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            body = response.read().decode("utf-8")
            if response.status not in ok_statuses:
                raise RuntimeError(f"HTTP {response.status}: {body[:240]}")
            return json.loads(body) if body.strip() else {}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        if exc.code in ok_statuses:
            return json.loads(body) if body.strip() else {}
        raise RuntimeError(f"HTTP {exc.code}: {body[:240]}") from exc


def _batches(items: list[Any], size: int) -> list[list[Any]]:
    return [items[index : index + size] for index in range(0, len(items), size)]


def _first_nested_list(value: Any) -> list[Any]:
    if isinstance(value, list) and value and isinstance(value[0], list):
        return value[0]
    return value if isinstance(value, list) else []


def _float_value(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def cognitive_config(session: Session) -> dict[str, str]:
    def get(key: str, default: str = "") -> str:
        row = session.execute(
            select(SettingRecord).where(SettingRecord.key == key)
        ).scalar_one_or_none()
        return row.value if row and row.value != "" else default

    return {
        "kb_vector_store": get("kb_vector_store", "sqlite"),
        "kb_embedding_provider": get("kb_embedding_provider", "cloud"),
        "kb_embedding_model": get("kb_embedding_model", ""),
        "kb_chunk_size": get("kb_chunk_size", "900"),
        "kb_chunk_overlap": get("kb_chunk_overlap", "120"),
        "qdrant_url": get("qdrant_url", ""),
        "qdrant_collection": get("qdrant_collection", "berrybrain"),
        "chroma_url": get("chroma_url", ""),
        "chroma_collection": get("chroma_collection", "berrybrain"),
        "cognitive_retrieval_mode": get("cognitive_retrieval_mode", "hybrid"),
        "semantic_data_enabled": get("semantic_data_enabled", "true"),
        "cognitive_enrich_on_save": get("cognitive_enrich_on_save", "true"),
        "cognitive_insights_on_save": get("cognitive_insights_on_save", "true"),
    }


def _fallback_answer(
    question: str, orchestrated: dict[str, Any], reason: str
) -> dict[str, Any]:
    evidence = orchestrated["evidence"]
    if "authentication failed" in reason.lower():
        answer = "Evidence was found, but NVIDIA NIM rejected the configured API key."
        suggestions = [
            "Replace the NVIDIA NIM API key in Settings and click Save.",
            "Retry the question after Settings shows Connected.",
        ]
    else:
        answer = (
            "Evidence found, but the configured model did not return a grounded answer."
        )
        suggestions = [
            "Retry after the provider recovers.",
            "Create an insight manually from the evidence.",
        ]
    if evidence:
        answer = f"{answer} Strongest evidence: {evidence[0]['title']}."
    if reason:
        answer = f"{answer} ({reason})"
    return {
        "status": "waiting_provider",
        "question": question,
        "answer": answer,
        "routes": orchestrated["routes"],
        "evidence": evidence[:8],
        "relatedNodes": orchestrated["relatedNodes"],
        "suggestions": suggestions,
        "reason": reason,
    }


def _tokens(text: str) -> set[str]:
    return {m.group(0).lower() for m in TOKEN_RE.finditer(text or "")}


def _token_score(query_tokens: set[str], body_tokens: set[str]) -> float:
    if not query_tokens or not body_tokens:
        return 0.0
    overlap = len(query_tokens & body_tokens)
    if overlap == 0:
        return 0.0
    return overlap / math.sqrt(len(query_tokens) * len(body_tokens))


def _evidence_dict(item: RetrievalEvidence) -> dict[str, Any]:
    return {
        "source": item.source,
        "title": item.title,
        "text": item.text,
        "score": round(item.score, 4),
        "metadata": item.metadata,
    }


def _json_list(raw: str) -> list[Any]:
    try:
        parsed = json.loads(raw or "[]")
    except json.JSONDecodeError:
        return [raw] if raw else []
    return parsed if isinstance(parsed, list) else [parsed]


def _int_setting(value: str, default: int, minimum: int, maximum: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = default
    return max(minimum, min(maximum, parsed))
