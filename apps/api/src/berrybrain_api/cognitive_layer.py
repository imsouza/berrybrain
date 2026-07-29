from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from berrybrain_api.ai_gateway import (
    generate_graph_answer,
    get_ai_config,
)
from berrybrain_api.assimilation import note_assimilation_map
from berrybrain_api.models import (
    EmbeddingRecord,
    GraphEdgeRecord,
    GraphNodeRecord,
    InsightRecord,
    JobRecord,
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
        "use_real_embeddings": get("use_real_embeddings", "false"),
        "hipporag_enabled": get("hipporag_enabled", "false"),
    }


# Facade imports for extracted modules
from berrybrain_api.cognitive_query import (  # noqa: E402,F401
    _bounded_query_evidence,
    _evidence_dict,
    _fallback_answer,
    _json_list,
    _safe_confidence,
    _token_score,
    orchestrate_retrieval,
    retrieve_external_kb,
    retrieve_graph,
    retrieve_kb,
)
from berrybrain_api.cognitive_query import (  # noqa: E402
    answer_cognitive_query as _answer_cognitive_query,
)
from berrybrain_api.vector_store import (  # noqa: E402,F401
    _attachment_chunks,
    _batches,
    _extracted_attachments,
    _first_nested_list,
    _float_value,
    _hash_embedding,
    _http_json,
    _int_setting,
    _knowledge_chunks,
    _retrieve_chroma,
    _retrieve_qdrant,
    _stable_attachment_chunk_id,
    _stable_chunk_id,
    _sync_chroma,
    _sync_qdrant,
    _tokens,
    chunk_markdown,
    index_knowledge_base,
    sync_external_vector_store,
)


async def answer_cognitive_query(session: Session, question: str) -> dict[str, Any]:
    """Compatibility facade for callers that patch cognitive_layer globals."""
    import berrybrain_api.cognitive_query as cognitive_query

    cognitive_query.generate_graph_answer = generate_graph_answer
    cognitive_query.get_ai_config = get_ai_config
    cognitive_query.orchestrate_retrieval = orchestrate_retrieval
    return await _answer_cognitive_query(session, question)
