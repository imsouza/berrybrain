from __future__ import annotations

from typing import Any

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from berrybrain_api.ai_gateway import get_ai_config
from berrybrain_api.artifact_state import accepted_edge_clause, accepted_node_clause
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
        "hipporag_enabled": get("hipporag_enabled", "true"),
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
    graph_node_count = session.scalar(select(func.count(GraphNodeRecord.id))) or 0
    graph_edge_count = session.scalar(select(func.count(GraphEdgeRecord.id))) or 0
    assimilation = note_assimilation_map(session, notes)
    unassimilated = [
        note for note in notes if not assimilation.get(note.id, {}).get("assimilated")
    ]
    visible_nodes = list(
        session.execute(select(GraphNodeRecord).where(accepted_node_clause())).scalars()
    )
    visible_edges = list(
        session.execute(select(GraphEdgeRecord).where(accepted_edge_clause())).scalars()
    )
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
            "nodes": graph_node_count,
            "visibleNodes": len(visible_nodes),
            "edges": graph_edge_count,
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
