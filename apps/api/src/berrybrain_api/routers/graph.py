import hashlib
import json
import logging
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from berrybrain_api.ai_gateway import (
    GraphAIUnavailable,
    generate_graph_answer,
    get_ai_config,
)
from berrybrain_api.artifact_state import (
    accepted_edge_clause,
    accepted_node_clause,
    processable_edge_clause,
    processable_node_clause,
)
from berrybrain_api.automation_logs import create_automation_log
from berrybrain_api.cognitive_layer import answer_cognitive_query
from berrybrain_api.confidence import serialize_confidence
from berrybrain_api.config import get_settings
from berrybrain_api.database import SessionLocal, get_session
from berrybrain_api.graph_inference_service import (
    persist_graph_inference,
    serialize_graph_inference,
)
from berrybrain_api.graph_semantic_service import (
    audit_graph_semantics,
    list_semantic_candidates,
    resolve_semantic_candidate,
)
from berrybrain_api.graph_write_service import GraphWriteService
from berrybrain_api.job_contracts import judge_artifact_payload
from berrybrain_api.jobs import (
    ENRICH_GRAPH_NODE,
    EXPAND_KNOWLEDGE_GRAPH,
    GENERATE_GRAPH_INSIGHTS,
    PENDING,
    RUNNING,
    SYNC_HIPPORAG_GRAPH,
    UPDATE_GRAPH_CLUSTERS,
    UPDATE_GRAPH_STATS,
    create_job,
    enqueue_job,
)
from berrybrain_api.learning import build_learning_guidance, record_learning_event
from berrybrain_api.models import (
    GraphEdgeRecord,
    GraphInferenceRecord,
    GraphNodeRecord,
    GraphResearchResultRecord,
    GraphResearchRunRecord,
    InsightRecord,
    JobRecord,
    NoteRecord,
    SettingRecord,
)
from berrybrain_api.ontology_service import (
    ontology_metadata,
    serialize_knowledge_graph,
    validate_knowledge_graph,
)
from berrybrain_api.second_brain import (
    expand_knowledge_graph,
    generate_inferred_graph_connections,
    get_node_summary,
    summarize_graph,
)
from berrybrain_api.services import (
    build_graph,
    create_insight,
    graph_quality_report,
    serialize_insight,
    sync_knowledge_graph,
    validate_node_with_web,
)

router = APIRouter(prefix="/api/v1/graph", tags=["graph"])
logger = logging.getLogger(__name__)


class GraphInferRequest(BaseModel):
    question: str


class InferenceFeedbackRequest(BaseModel):
    action: str = Field(pattern="^(upvoted|downvoted|corrected)$")
    correction: str = Field(default="", max_length=8000)


class ManualNotesRequest(BaseModel):
    notes: str = ""


class UpdateGraphNodeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: str | None = Field(default=None, max_length=80)
    label: str | None = Field(default=None, max_length=255)
    title: str | None = Field(default=None, max_length=255)
    summary: str | None = None
    source: str | None = Field(default=None, max_length=255)
    status: str | None = None


class EdgeTypeRequest(BaseModel):
    type: str


class ConfidenceRecalculationRequest(BaseModel):
    node_ids: list[int] = Field(default_factory=list, alias="nodeIds")


class ManualEvidenceRequest(BaseModel):
    excerpt: str
    source_note_id: int | None = None


class EnrichNodeRequest(BaseModel):
    ai_summary: str = ""
    ai_context: str = ""
    source_evidence: str = ""
    learning_value: str = ""
    source_quality: str = ""
    provider: str = ""
    model: str = ""
    reasoning: str = ""
    analysis: dict[str, Any] = Field(default_factory=dict)


class ReclusterRequest(BaseModel):
    preview: bool = True
    preview_token: str = ""
    scope_node_ids: list[int] | None = None


class OntologyAuditRequest(BaseModel):
    apply: bool = False


class ResolveSemanticCandidateRequest(BaseModel):
    action: str


def _parse_json_list(raw: str | None) -> list[Any]:
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return []
    return parsed if isinstance(parsed, list) else []


def _current_graph_model(config: dict[str, str]) -> str:
    return config.get("cloud_model") or config.get("ollama_model") or ""


def _setting_value(session, key: str, default: str = "") -> str:
    row = session.execute(
        select(SettingRecord).where(SettingRecord.key == key)
    ).scalar_one_or_none()
    return row.value if row and row.value != "" else default


def _graph_version(session: Session) -> int:
    node_updated = session.scalar(select(func.max(GraphNodeRecord.updated_at)))
    edge_updated = session.scalar(select(func.max(GraphEdgeRecord.updated_at)))
    latest = (
        max(value for value in (node_updated, edge_updated) if value is not None)
        if node_updated or edge_updated
        else None
    )
    return int(latest.timestamp() * 1_000_000) if latest else 0


def _serialize_paged_node(node: GraphNodeRecord) -> dict[str, Any]:
    metadata = _json_object(node.graph_metadata)
    return {
        "id": f"{node.type}_{node.id}",
        "recordId": node.id,
        "stableId": node.stable_id,
        "iri": node.iri,
        "artifactVersion": node.artifact_version,
        "type": node.type,
        "label": node.label,
        "title": node.title or node.label,
        "summary": node.summary,
        "path": metadata.get("path", ""),
        "folder": metadata.get("folder", ""),
        "sourceId": node.source_id,
        "status": node.status,
        "confidence": node.confidence if node.confidence_sample_size else None,
        "confidenceInterval": serialize_confidence(node),
        "createdBy": node.created_by,
        "createdByModel": node.created_by_model,
        "semanticState": node.semantic_state,
        "semanticProfileVersion": node.semantic_profile_version,
        "clusterId": node.cluster_id,
        "vaultId": node.vault_id,
        "colorId": node.color_id,
        "colorConfidence": node.color_confidence,
        "colorReason": node.color_reason,
        "semanticStatus": node.semantic_status,
        "ontology": {
            "class": node.ontology_class,
            "canonicalLabel": node.canonical_label,
        },
    }


def _json_object(raw: str | None) -> dict[str, Any]:
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


@router.get("")
def get_graph(
    max_depth: int = 2,
    view: str = "",
    include_provisional: bool = Query(False, alias="includeProvisional"),
) -> dict:
    """GET /graph supports view filtering: enriched, raw, validated, needs_review, hidden."""
    with SessionLocal() as session:
        return build_graph(
            session,
            max_depth=max_depth,
            view=view,
            include_provisional=include_provisional,
        )


@router.get("/ontology")
def get_graph_ontology() -> dict[str, Any]:
    return ontology_metadata()


@router.get("/learning-policy")
def get_graph_learning_policy(
    note_id: list[int] | None = Query(None, alias="noteId"),
    note_path: str = Query("", alias="notePath"),
    target_type: str = Query("", alias="targetType"),
) -> dict[str, Any]:
    with SessionLocal() as session:
        source_note_ids = [value for value in (note_id or []) if value > 0]
        if note_path:
            matching_id = session.scalar(
                select(NoteRecord.id).where(NoteRecord.path == note_path)
            )
            if matching_id:
                source_note_ids.append(int(matching_id))
        return build_learning_guidance(
            session,
            source_note_ids=source_note_ids,
            target_type=target_type or None,
        )


@router.get("/ontology/export")
def export_graph_ontology(
    output_format: str = Query("json-ld", alias="format", pattern="^(json-ld|turtle)$"),
    include_provisional: bool = Query(False, alias="includeProvisional"),
) -> Response:
    with SessionLocal() as session:
        payload = serialize_knowledge_graph(
            session,
            output_format=output_format,
            include_provisional=include_provisional,
        )
    media_type = "application/ld+json" if output_format == "json-ld" else "text/turtle"
    return Response(content=payload, media_type=media_type)


@router.get("/ontology/validate")
def validate_graph_ontology(
    include_provisional: bool = Query(False, alias="includeProvisional"),
) -> dict[str, Any]:
    with SessionLocal() as session:
        return validate_knowledge_graph(
            session, include_provisional=include_provisional
        )


@router.get("/summary")
def get_graph_summary(
    include_provisional: bool = Query(False, alias="includeProvisional"),
) -> dict:
    with SessionLocal() as session:
        return {
            **summarize_graph(session, include_provisional=include_provisional),
            "graphVersion": _graph_version(session),
        }


@router.get("/nodes")
def get_graph_nodes_page(
    cursor: int = Query(default=0, ge=0),
    limit: int = Query(default=250, ge=1, le=2000),
    types: str = "",
    include_provisional: bool = Query(False, alias="includeProvisional"),
) -> dict:
    with SessionLocal() as session:
        query = (
            select(GraphNodeRecord)
            .where(
                GraphNodeRecord.id > cursor,
                accepted_node_clause(include_provisional=include_provisional),
            )
            .order_by(GraphNodeRecord.id)
            .limit(limit + 1)
        )
        requested_types = [item.strip() for item in types.split(",") if item.strip()]
        if requested_types:
            query = query.where(GraphNodeRecord.type.in_(requested_types))
        records = list(session.execute(query).scalars())
        has_more = len(records) > limit
        page = records[:limit]
        return {
            "nodes": [_serialize_paged_node(node) for node in page],
            "nextCursor": page[-1].id if has_more and page else None,
            "graphVersion": _graph_version(session),
        }


@router.get("/edges")
def get_graph_edges_page(
    cursor: int = Query(default=0, ge=0),
    limit: int = Query(default=500, ge=1, le=5000),
    node_ids: str = "",
    include_provisional: bool = Query(False, alias="includeProvisional"),
) -> dict:
    with SessionLocal() as session:
        query = (
            select(GraphEdgeRecord)
            .where(
                GraphEdgeRecord.id > cursor,
                accepted_edge_clause(include_provisional=include_provisional),
            )
            .order_by(GraphEdgeRecord.id)
            .limit(limit + 1)
        )
        requested_ids = {
            int(item.rsplit("_", 1)[-1])
            for item in node_ids.split(",")
            if item.rsplit("_", 1)[-1].isdigit()
        }
        if requested_ids:
            query = query.where(
                or_(
                    GraphEdgeRecord.source_node_id.in_(requested_ids),
                    GraphEdgeRecord.target_node_id.in_(requested_ids),
                )
            )
        records = list(session.execute(query).scalars())
        has_more = len(records) > limit
        page = records[:limit]
        endpoint_ids = {
            node_id
            for edge in page
            for node_id in (edge.source_node_id, edge.target_node_id)
        }
        node_types = dict(
            session.execute(
                select(GraphNodeRecord.id, GraphNodeRecord.type).where(
                    GraphNodeRecord.id.in_(endpoint_ids)
                )
            ).all()
        )
        edges = [
            {
                "id": edge.id,
                "stableId": edge.stable_id,
                "iri": edge.iri,
                "artifactVersion": edge.artifact_version,
                "source": f"{node_types.get(edge.source_node_id, 'node')}_{edge.source_node_id}",
                "target": f"{node_types.get(edge.target_node_id, 'node')}_{edge.target_node_id}",
                "type": edge.type,
                "label": edge.label,
                "confidence": edge.confidence if edge.confidence_sample_size else None,
                "confidenceInterval": serialize_confidence(edge),
                "reason": edge.reason,
                "evidence": _parse_json_list(edge.evidence),
                "status": edge.status,
                "provider": edge.provider,
                "model": edge.model,
                "semanticStatus": edge.semantic_status,
                "ontology": {"property": edge.ontology_property},
            }
            for edge in page
            if edge.source_node_id in node_types and edge.target_node_id in node_types
        ]
        return {
            "edges": edges,
            "nextCursor": page[-1].id if has_more and page else None,
            "graphVersion": _graph_version(session),
        }


@router.get("/delta")
def get_graph_delta(
    since_version: int = Query(default=0, ge=0),
    include_provisional: bool = Query(False, alias="includeProvisional"),
) -> dict:
    since = datetime.fromtimestamp(since_version / 1_000_000, UTC).replace(tzinfo=None)
    with SessionLocal() as session:
        nodes = list(
            session.execute(
                select(GraphNodeRecord)
                .where(
                    GraphNodeRecord.updated_at > since,
                    accepted_node_clause(include_provisional=include_provisional),
                )
                .order_by(GraphNodeRecord.id)
                .limit(1001)
            ).scalars()
        )
        edges = list(
            session.execute(
                select(GraphEdgeRecord.id)
                .where(
                    GraphEdgeRecord.updated_at > since,
                    accepted_edge_clause(include_provisional=include_provisional),
                )
                .order_by(GraphEdgeRecord.id)
                .limit(2001)
            ).scalars()
        )
        truncated = len(nodes) > 1000 or len(edges) > 2000
        return {
            "graphVersion": _graph_version(session),
            "nodes": [_serialize_paged_node(node) for node in nodes[:1000]],
            "edgeIds": edges[:2000],
            "requiresEdgeRefresh": bool(edges),
            "requiresFullRefresh": truncated,
            "nodeCount": session.scalar(
                select(func.count(GraphNodeRecord.id)).where(
                    accepted_node_clause(include_provisional=include_provisional)
                )
            )
            or 0,
            "edgeCount": session.scalar(
                select(func.count(GraphEdgeRecord.id)).where(
                    accepted_edge_clause(include_provisional=include_provisional)
                )
            )
            or 0,
        }


@router.get("/clusters")
def get_graph_clusters() -> dict:
    from berrybrain_api.semantic_clustering import serialize_clusters

    with SessionLocal() as session:
        return {
            "clusters": serialize_clusters(session),
            "graphVersion": _graph_version(session),
        }


@router.get("/palette")
def get_graph_palette() -> dict:
    from berrybrain_api.semantic_clustering import serialize_palette

    with SessionLocal() as session:
        return serialize_palette(session)


@router.post("/recluster")
def recluster_graph(payload: ReclusterRequest) -> dict:
    from berrybrain_api.semantic_clustering import (
        apply_cluster_preview,
        build_cluster_preview,
    )

    with SessionLocal() as session:
        scope_node_ids = (
            {int(node_id) for node_id in payload.scope_node_ids if int(node_id) > 0}
            if payload.scope_node_ids is not None
            else None
        )
        preview = build_cluster_preview(
            session,
            node_ids=scope_node_ids,
        )
        preview_token = hashlib.sha256(
            json.dumps(preview, sort_keys=True).encode("utf-8")
        ).hexdigest()
        if payload.preview:
            return {**preview, "applied": False, "previewToken": preview_token}
        if not payload.preview_token or payload.preview_token != preview_token:
            raise HTTPException(
                status_code=409,
                detail="Graph changed after preview. Generate a new recluster preview.",
            )
        return {
            **apply_cluster_preview(session, preview),
            "previewToken": preview_token,
            "graphVersion": _graph_version(session),
        }


@router.post("/ontology/audit")
def audit_graph_ontology(payload: OntologyAuditRequest) -> dict:
    with SessionLocal() as session:
        return audit_graph_semantics(session, apply=payload.apply)


@router.get("/semantic-candidates")
def get_semantic_candidates(status: str = "pending") -> dict:
    with SessionLocal() as session:
        return {"items": list_semantic_candidates(session, status=status)}


@router.post("/semantic-candidates/{candidate_id}/resolve")
def resolve_graph_semantic_candidate(
    candidate_id: int, payload: ResolveSemanticCandidateRequest
) -> dict:
    with SessionLocal() as session:
        return resolve_semantic_candidate(session, candidate_id, payload.action)


@router.post("/expand")
def expand_graph() -> dict:
    with SessionLocal() as session:
        return expand_knowledge_graph(session)


@router.post("/infer-connections")
async def infer_graph_connections() -> dict:
    with SessionLocal() as session:
        return await generate_inferred_graph_connections(session)


@router.post("/rebuild")
def rebuild_graph(dry_run: bool = True) -> dict:
    with SessionLocal() as session:
        if dry_run:
            return {"dryRun": True, "summary": summarize_graph(session)}
        result = expand_knowledge_graph(session)
        return {"dryRun": False, **result}


@router.post("/infer")
async def infer_graph(
    payload: GraphInferRequest,
    session: Session = Depends(get_session),
) -> dict:
    question = payload.question.strip()
    if not question:
        raise HTTPException(status_code=422, detail="Question is required")
    graph_question = (
        "Use BerryBrain's knowledge graph as queryable data. If the user asks "
        "which nodes, node types, connections, graph areas, or clusters mention "
        "a subject, inspect graph nodes and edges and answer with matching "
        "labels, types, and evidence instead of doing only note text search.\n\n"
        f"Question: {question}"
    )
    try:
        result = await answer_cognitive_query(session, graph_question)
    except GraphAIUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Graph Ask failed")
        raise HTTPException(
            status_code=502,
            detail="Ask could not complete with the configured AI provider.",
        ) from exc
    if result.get("status") == "waiting_provider":
        raise HTTPException(
            status_code=503,
            detail={
                "code": "provider_unavailable",
                "message": "The configured AI provider did not return an answer.",
            },
        )
    inference = persist_graph_inference(session, question, result)
    return serialize_graph_inference(inference)


@router.post("/inferences/{inference_id}/feedback")
def record_inference_feedback(
    inference_id: int,
    payload: InferenceFeedbackRequest,
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    inference = session.get(GraphInferenceRecord, inference_id)
    if inference is None:
        raise HTTPException(status_code=404, detail="Graph inference not found")
    if payload.action == "corrected" and not payload.correction.strip():
        raise HTTPException(
            status_code=422,
            detail="A corrected answer is required for correction feedback",
        )
    source_note_ids = _inference_source_note_ids(session, inference)
    event = record_learning_event(
        session,
        event_type=f"ask.answer.{payload.action}",
        target_type="ask_answer",
        target_key=f"graph-inference:{inference.id}",
        action=payload.action,
        source_note_ids=source_note_ids,
        before_state={"answer": inference.answer, "question": inference.question},
        after_state={"correction": payload.correction.strip()},
        actor_type="user",
        origin="graph_ask_api",
    )
    session.commit()
    return {"status": "recorded", "eventId": event.event_id, "action": event.action}


def _inference_source_note_ids(
    session: Session, inference: GraphInferenceRecord
) -> list[int]:
    note_ids: set[int] = set()

    def collect(value: Any) -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                if key in {"noteId", "sourceNoteId"} and str(item).isdigit():
                    note_ids.add(int(item))
                elif key == "sourceNoteIds" and isinstance(item, list):
                    note_ids.update(
                        int(value) for value in item if str(value).isdigit()
                    )
                else:
                    collect(item)
        elif isinstance(value, list):
            for item in value:
                collect(item)

    collect(_parse_json_list(inference.evidence))
    related_node_ids = {
        int(value.rsplit("_", 1)[-1])
        for value in _parse_json_list(inference.related_nodes)
        if isinstance(value, str) and value.rsplit("_", 1)[-1].isdigit()
    }
    if related_node_ids:
        for raw in session.scalars(
            select(GraphNodeRecord.source_note_ids).where(
                GraphNodeRecord.id.in_(related_node_ids)
            )
        ):
            collect({"sourceNoteIds": _parse_json_list(raw)})
    return sorted(value for value in note_ids if value > 0)


@router.post("/sync")
def sync_graph() -> dict:
    with SessionLocal() as session:
        result = sync_knowledge_graph(session)
        return {"status": "synced", **result}


@router.post("/enrich-missing")
def enrich_missing_graph_nodes(limit: int = 20) -> dict:
    from berrybrain_api.semantic_enrichment import queue_node_enrichment

    with SessionLocal() as session:
        candidates = list(
            session.execute(
                select(GraphNodeRecord)
                .where(accepted_node_clause(include_provisional=True))
                .where(
                    GraphNodeRecord.semantic_state.in_(["pending", "stale", "failed"])
                )
                .order_by(GraphNodeRecord.type == "note", GraphNodeRecord.id.asc())
                .limit(max(1, min(limit, 50)))
            ).scalars()
        )
        created = 0
        skipped = 0
        for node in candidates:
            marker = f'"node_id":{node.id}'
            existing = (
                session.execute(
                    select(JobRecord).where(
                        JobRecord.type == ENRICH_GRAPH_NODE,
                        JobRecord.status.in_([PENDING, RUNNING]),
                        JobRecord.payload.like(f"%{marker}%"),
                    )
                )
                .scalars()
                .first()
            )
            if existing is not None:
                skipped += 1
                continue
            try:
                _, was_created = queue_node_enrichment(session, node)
            except HTTPException as exc:
                if exc.status_code != 409:
                    raise
                skipped += 1
                continue
            created += int(was_created)
            skipped += int(not was_created)
        return {"queued": created, "skipped": skipped, "candidates": len(candidates)}


@router.get("/nodes/{node_id}/summary")
def graph_node_summary(node_id: int) -> dict:
    with SessionLocal() as session:
        return get_node_summary(session, node_id)


@router.post("/nodes/{node_id}/confirm")
def confirm_graph_node(node_id: int) -> dict:
    with SessionLocal() as session:
        node = GraphWriteService(session).set_node_status(
            node_id, "confirmed", user_decision=True
        )
        return {
            "id": node.id,
            "status": node.status,
            "mutationLogId": getattr(node, "mutation_log_id", None),
        }


@router.post("/nodes/{node_id}/ignore")
def ignore_graph_node(node_id: int) -> dict:
    with SessionLocal() as session:
        node = GraphWriteService(session).set_node_status(
            node_id, "ignored", user_decision=True
        )
        return {
            "id": node.id,
            "status": node.status,
            "mutationLogId": getattr(node, "mutation_log_id", None),
        }


@router.delete("/nodes/{node_id}")
def delete_graph_node_endpoint(node_id: int) -> dict:
    with SessionLocal() as session:
        node = session.get(GraphNodeRecord, node_id)
        if node is None:
            raise HTTPException(status_code=404, detail="Graph node not found")
        from berrybrain_api.graph_invalidation import (
            collect_node_deletion_impact,
            invalidate_dependent_insights,
            invalidate_dependent_relationships,
        )

        impact = collect_node_deletion_impact(session, node)
        invalidated_insights = invalidate_dependent_insights(
            session,
            impact,
            primary_node_id=node_id,
        )
        invalidated_relationships = invalidate_dependent_relationships(session, impact)
        GraphWriteService(session, autocommit=False).delete_node(
            node_id, user_decision=True
        )
        session.commit()
        from berrybrain_api.jobs import supersede_missing_graph_artifact_jobs

        supersede_missing_graph_artifact_jobs(session)
        version = _graph_version(session)
        stats_job = create_job(
            session,
            UPDATE_GRAPH_STATS,
            {
                "trigger": "node_deleted",
                "idempotency_key": f"delete-node-stats:{node_id}:{version}",
            },
            max_attempts=2,
        )
        cluster_job = create_job(
            session,
            UPDATE_GRAPH_CLUSTERS,
            {
                "trigger": "node_deleted",
                "scope_node_ids": list(impact.cluster_scope_node_ids),
                "idempotency_key": f"delete-node-clusters:{node_id}:{version}",
            },
            max_attempts=2,
        )
        insight_job = create_job(
            session,
            GENERATE_GRAPH_INSIGHTS,
            {
                "trigger": "node_deleted",
                "source_note_ids": list(impact.source_note_ids),
                "affected_node_ids": list(impact.cluster_scope_node_ids),
                "idempotency_key": f"delete-node-insights:{node_id}:{version}",
            },
            max_attempts=2,
        )
        retrieval_job = create_job(
            session,
            SYNC_HIPPORAG_GRAPH,
            {
                "trigger": "node_deleted",
                "idempotency_key": f"delete-node-retrieval:{node_id}:{version}",
            },
            max_attempts=2,
        )
        return {
            "id": node_id,
            "status": "deleted",
            "jobs": {
                "stats": stats_job.id,
                "clusters": cluster_job.id,
                "insights": insight_job.id,
                "retrieval": retrieval_job.id,
            },
            "impact": {
                **impact.to_dict(),
                "invalidatedInsights": invalidated_insights,
                "invalidatedRelationships": invalidated_relationships,
                "scope": "incident_subgraph",
            },
            "message": (
                "Node deleted. Dependent insights were invalidated and the affected "
                "subgraph is being recalculated."
            ),
        }


@router.post("/nodes/{node_id}/reprocess")
def reprocess_graph_node(node_id: int) -> dict:
    from berrybrain_api.semantic_enrichment import (
        SEMANTIC_PROMPT_VERSION,
        source_fingerprint,
    )

    with SessionLocal() as session:
        node = session.get(GraphNodeRecord, node_id)
        if node is None:
            raise HTTPException(status_code=404, detail="Node not found")
        job = create_job(
            session,
            ENRICH_GRAPH_NODE,
            {
                "node_id": node.id,
                "source_fingerprint": source_fingerprint(session, node),
                "prompt_version": SEMANTIC_PROMPT_VERSION,
            },
            max_attempts=2,
        )
        create_automation_log(
            session,
            "GRAPH_NODE_REPROCESS_QUEUED",
            "graph_node",
            str(node.id),
            f'Node reprocess queued: "{node.label}"',
            {"status": node.status},
            {"job_id": job.id},
            False,
        )
        return {"status": "queued", "job_id": job.id}


@router.put("/nodes/{node_id}", status_code=202)
def update_graph_node(node_id: int, payload: UpdateGraphNodeRequest) -> dict:
    from berrybrain_api.semantic_enrichment import (
        SEMANTIC_PROMPT_VERSION,
        source_fingerprint,
    )

    with SessionLocal() as session:
        node = GraphWriteService(session).update_node_fields(
            node_id,
            node_type=payload.type,
            label=payload.label,
            title=payload.title,
            summary=payload.summary,
            source=payload.source,
            status=payload.status,
            user_decision=True,
        )
        version = _graph_version(session)
        reprocess_job = create_job(
            session,
            ENRICH_GRAPH_NODE,
            {
                "node_id": node.id,
                "source_fingerprint": source_fingerprint(session, node),
                "prompt_version": SEMANTIC_PROMPT_VERSION,
                "trigger": "manual_node_edit",
                "idempotency_key": f"edit-node-enrich:{node.id}:{version}",
            },
            max_attempts=2,
        )
        expand_job = create_job(
            session,
            EXPAND_KNOWLEDGE_GRAPH,
            {
                "node_id": node.id,
                "trigger": "manual_node_edit",
                "idempotency_key": f"edit-node-expand:{node.id}:{version}",
            },
            max_attempts=2,
        )
        stats_job = create_job(
            session,
            UPDATE_GRAPH_STATS,
            {
                "trigger": "manual_node_edit",
                "idempotency_key": f"edit-node-stats:{node.id}:{version}",
            },
            max_attempts=2,
        )
        cluster_job = create_job(
            session,
            UPDATE_GRAPH_CLUSTERS,
            {
                "trigger": "manual_node_edit",
                "idempotency_key": f"edit-node-clusters:{node.id}:{version}",
            },
            max_attempts=2,
        )
        judge_job = enqueue_job(
            session,
            "JUDGE_ARTIFACT",
            judge_artifact_payload(
                session,
                "node",
                node.id,
                str(node.updated_at.timestamp()) if node.updated_at else str(version),
            ),
            priority=20,
            max_attempts=2,
        )
        return {
            "id": node.id,
            "type": node.type,
            "label": node.label,
            "title": node.title or node.label,
            "summary": node.summary,
            "source": node.source,
            "status": node.status,
            "confidence": node.confidence if node.confidence_sample_size else None,
            "confidenceInterval": serialize_confidence(node),
            "semanticStatus": node.semantic_status,
            "ontology": {
                "class": node.ontology_class,
                "canonicalLabel": node.canonical_label,
            },
            "validation": {
                "status": "accepted_for_recalculation",
                "message": "Name, type, and current evidence are context-compatible.",
            },
            "mutationLogId": getattr(node, "mutation_log_id", None),
            "jobs": {
                "enrich": reprocess_job.id,
                "expand": expand_job.id,
                "stats": stats_job.id,
                "clusters": cluster_job.id,
                "judge": judge_job.id,
            },
        }


@router.put("/nodes/{node_id}/notes")
def update_graph_node_notes(node_id: int, payload: ManualNotesRequest) -> dict:
    with SessionLocal() as session:
        node = GraphWriteService(session).set_node_user_notes(node_id, payload.notes)
        return {"id": node.id, "userNotes": node.user_notes}


@router.post("/connections/{edge_id}/confirm")
def confirm_graph_edge(edge_id: int) -> dict:
    with SessionLocal() as session:
        edge = GraphWriteService(session).set_edge_status(
            edge_id, "confirmed", user_decision=True
        )
        return {
            "id": edge.id,
            "status": edge.status,
            "mutationLogId": getattr(edge, "mutation_log_id", None),
        }


@router.put("/connections/{edge_id}/notes")
def update_graph_edge_notes(edge_id: int, payload: ManualNotesRequest) -> dict:
    with SessionLocal() as session:
        edge = GraphWriteService(session).set_edge_user_notes(edge_id, payload.notes)
        return {"id": edge.id, "userNotes": edge.user_notes}


@router.post("/connections/{edge_id}/ignore")
def ignore_graph_edge(edge_id: int) -> dict:
    with SessionLocal() as session:
        edge = GraphWriteService(session).set_edge_status(
            edge_id, "ignored", user_decision=True
        )
        return {
            "id": edge.id,
            "status": edge.status,
            "mutationLogId": getattr(edge, "mutation_log_id", None),
        }


@router.post("/connections/{edge_id}/restore")
def restore_graph_edge(edge_id: int) -> dict:
    with SessionLocal() as session:
        edge = GraphWriteService(session).set_edge_status(
            edge_id, "suggested", user_decision=True
        )
        return {
            "id": edge.id,
            "status": edge.status,
            "mutationLogId": getattr(edge, "mutation_log_id", None),
        }


@router.patch("/connections/{edge_id}/type", status_code=202)
def update_graph_edge_type(edge_id: int, payload: EdgeTypeRequest) -> dict:
    with SessionLocal() as session:
        edge = GraphWriteService(session).update_edge_type(edge_id, payload.type)
        version = _graph_version(session)
        endpoint_ids = [edge.source_node_id, edge.target_node_id]
        judge_job = enqueue_job(
            session,
            "JUDGE_ARTIFACT",
            judge_artifact_payload(
                session,
                "edge",
                edge.id,
                str(edge.updated_at.timestamp()) if edge.updated_at else str(version),
            ),
            priority=20,
            max_attempts=2,
        )
        stats_job = create_job(
            session,
            UPDATE_GRAPH_STATS,
            {
                "trigger": "edge_type_corrected",
                "affected_node_ids": endpoint_ids,
                "idempotency_key": f"edge-type-stats:{edge.id}:{version}",
            },
            max_attempts=2,
        )
        cluster_job = create_job(
            session,
            UPDATE_GRAPH_CLUSTERS,
            {
                "trigger": "edge_type_corrected",
                "scope_node_ids": endpoint_ids,
                "idempotency_key": f"edge-type-clusters:{edge.id}:{version}",
            },
            max_attempts=2,
        )
        insight_job = create_job(
            session,
            GENERATE_GRAPH_INSIGHTS,
            {
                "trigger": "edge_type_corrected",
                "affected_node_ids": endpoint_ids,
                "idempotency_key": f"edge-type-insights:{edge.id}:{version}",
            },
            max_attempts=2,
        )
        return {
            "id": edge.id,
            "type": edge.type,
            "status": "accepted_for_recalculation",
            "jobs": {
                "judge": judge_job.id,
                "stats": stats_job.id,
                "clusters": cluster_job.id,
                "insights": insight_job.id,
            },
        }


@router.post("/connections/{edge_id}/evidence")
def add_graph_edge_evidence(edge_id: int, payload: ManualEvidenceRequest) -> dict:
    with SessionLocal() as session:
        edge = GraphWriteService(session).add_manual_evidence(
            edge_id, payload.excerpt, payload.source_note_id
        )
        return {"id": edge.id, "evidence": _parse_json_list(edge.evidence)}


@router.get("/connections/{edge_id}/explanation")
def explain_graph_edge(edge_id: int) -> dict:
    with SessionLocal() as session:
        edge = session.get(GraphEdgeRecord, edge_id)
        if edge is None:
            raise HTTPException(status_code=404, detail="Graph edge not found")
        source = session.get(GraphNodeRecord, edge.source_node_id)
        target = session.get(GraphNodeRecord, edge.target_node_id)
        return {
            "id": edge.id,
            "type": edge.type,
            "reason": edge.reason,
            "confidence": edge.confidence,
            "evidence": _parse_json_list(edge.evidence),
            "source": {"id": source.id, "label": source.label} if source else None,
            "target": {"id": target.id, "label": target.label} if target else None,
            "provider": edge.provider,
            "model": edge.model,
            "promptVersion": edge.prompt_version,
        }


@router.post("/mutations/{mutation_log_id}/undo")
def undo_graph_mutation(mutation_log_id: int) -> dict:
    with SessionLocal() as session:
        mutation = GraphWriteService(session).undo(mutation_log_id)
        return {
            "id": mutation.id,
            "status": "undone",
            "revertedAt": mutation.reverted_at.isoformat()
            if mutation.reverted_at
            else None,
            "revertedByLogId": mutation.reverted_by_log_id,
        }


@router.post("/nodes/{survivor_id}/merge/{merged_node_id}")
def merge_graph_nodes(survivor_id: int, merged_node_id: int) -> dict:
    with SessionLocal() as session:
        node, mutation = GraphWriteService(session).merge_nodes(
            survivor_id, merged_node_id
        )
        return {
            "id": node.id,
            "status": node.status,
            "mutationLogId": mutation.id,
            "mergedNodeId": merged_node_id,
        }


@router.post("/merges/{mutation_log_id}/split")
def split_merged_graph_nodes(mutation_log_id: int) -> dict:
    with SessionLocal() as session:
        mutation = GraphWriteService(session).undo(mutation_log_id)
        return {
            "id": mutation.id,
            "status": "split",
            "revertedAt": mutation.reverted_at.isoformat()
            if mutation.reverted_at
            else None,
        }


# --- Enrichment & Validation endpoints ---


@router.post("/nodes/{node_id}/enrich")
def enrich_graph_node(node_id: int, payload: EnrichNodeRequest) -> dict:
    with SessionLocal() as session:
        if payload.analysis:
            from berrybrain_api.semantic_enrichment import (
                SemanticAnalysis,
                persist_semantic_analysis,
            )

            node = session.get(GraphNodeRecord, node_id)
            if node is None:
                raise HTTPException(status_code=404, detail="Node not found")
            try:
                analysis = SemanticAnalysis.model_validate(payload.analysis)
            except ValidationError as exc:
                raise HTTPException(
                    status_code=422,
                    detail="Semantic analysis payload is invalid.",
                ) from exc
            profile = persist_semantic_analysis(session, node, analysis)
            create_job(
                session,
                UPDATE_GRAPH_CLUSTERS,
                {
                    "graph_version": _graph_version(session),
                    "idempotency_key": "update-semantic-clusters",
                },
            )
            return {
                "id": node.id,
                "enriched": True,
                "semanticState": node.semantic_state,
                "profileId": profile.id,
            }
        has_content = any(
            [
                payload.ai_summary.strip(),
                payload.ai_context.strip(),
                payload.source_evidence.strip(),
                payload.learning_value.strip(),
                payload.source_quality.strip(),
            ]
        )
        if not has_content:
            raise HTTPException(
                status_code=422,
                detail="Enrichment payload has no semantic content.",
            )
        node = GraphWriteService(session).update_node_enrichment(
            node_id,
            {
                "ai_summary": payload.ai_summary,
                "ai_context": payload.ai_context,
                "source_evidence": payload.source_evidence,
                "learning_value": payload.learning_value,
                "source_quality": payload.source_quality,
                "provider": payload.provider,
                "model": payload.model,
                "prompt_version": "enrich-node.v1"
                if payload.provider or payload.model
                else "",
            },
        )
        return {"id": node.id, "enriched": True}


@router.get("/nodes/{node_id}/semantic-analysis")
def get_node_semantic_analysis(node_id: int) -> dict:
    from berrybrain_api.semantic_enrichment import semantic_analysis_payload

    with SessionLocal() as session:
        return semantic_analysis_payload(session, node_id)


@router.post("/nodes/{node_id}/semantic-analysis/retry")
def retry_node_semantic_analysis(node_id: int) -> dict:
    from berrybrain_api.semantic_enrichment import queue_node_enrichment

    with SessionLocal() as session:
        node = session.get(GraphNodeRecord, node_id)
        if node is None:
            raise HTTPException(status_code=404, detail="Node not found")
        if node.semantic_state not in {
            "failed",
            "stale",
            "not_configured",
            "needs_review",
        }:
            raise HTTPException(
                status_code=409, detail="Node semantic analysis is not retryable"
            )
        job, created = queue_node_enrichment(session, node)
        return {"queued": created, "jobId": getattr(job, "id", None)}


@router.post("/nodes/{node_id}/semantic-analysis/regenerate")
def regenerate_node_semantic_analysis(node_id: int) -> dict:
    from berrybrain_api.semantic_enrichment import queue_node_enrichment

    with SessionLocal() as session:
        node = session.get(GraphNodeRecord, node_id)
        if node is None:
            raise HTTPException(status_code=404, detail="Node not found")
        job, created = queue_node_enrichment(session, node, force=True)
        return {"queued": created, "jobId": getattr(job, "id", None)}


@router.post("/nodes/{node_id}/enrich-ai")
async def enrich_graph_node_with_ai(node_id: int, response: Response) -> dict:
    response.headers["Deprecation"] = "true"
    response.headers["Sunset"] = "Wed, 30 Sep 2026 23:59:59 GMT"
    response.headers["Link"] = (
        f"</api/v1/graph/nodes/{node_id}/semantic-analysis/regenerate>; "
        'rel="successor-version"'
    )
    with SessionLocal() as session:
        node = session.get(GraphNodeRecord, node_id)
        if not node:
            raise HTTPException(status_code=404, detail="Node not found")

        note_ids = [
            int(value)
            for value in _parse_json_list(node.source_note_ids)
            if isinstance(value, int | str) and str(value).isdigit()
        ]
        notes = []
        if note_ids:
            notes = list(
                session.execute(
                    select(NoteRecord).where(NoteRecord.id.in_(note_ids[:12]))
                ).scalars()
            )
        edges = list(
            session.execute(
                select(GraphEdgeRecord)
                .where(
                    (GraphEdgeRecord.source_node_id == node.id)
                    | (GraphEdgeRecord.target_node_id == node.id)
                )
                .where(accepted_edge_clause())
                .limit(12)
            ).scalars()
        )
        connected_ids = {
            edge.target_node_id
            if edge.source_node_id == node.id
            else edge.source_node_id
            for edge in edges
        }
        connected_nodes = (
            list(
                session.execute(
                    select(GraphNodeRecord).where(GraphNodeRecord.id.in_(connected_ids))
                ).scalars()
            )
            if connected_ids
            else []
        )

        config = get_ai_config(session)
        model = _current_graph_model(config)
        system = (
            "You enrich a personal knowledge graph node. Use only the provided "
            "notes, node fields, and graph connections. Return JSON with: "
            "ai_summary, ai_context, learning_value, source_quality, "
            "source_evidence. source_evidence must be a list of concrete note "
            "titles, snippets, or connection reasons. Do not invent facts."
        )
        prompt = json.dumps(
            {
                "node": {
                    "type": node.type,
                    "label": node.label,
                    "title": node.title,
                    "summary": node.summary,
                    "existingAiNotes": node.ai_notes,
                    "manualNotes": node.user_notes,
                    "source": node.source,
                },
                "notes": [
                    {
                        "id": note.id,
                        "title": note.title,
                        "path": note.path,
                        "snippet": note.content[:1200],
                    }
                    for note in notes
                ],
                "connections": [
                    {
                        "type": edge.type,
                        "label": edge.label,
                        "reason": edge.reason,
                        "confidence": edge.confidence,
                        "evidence": _parse_json_list(edge.evidence),
                    }
                    for edge in edges
                ],
                "connectedNodes": [
                    {
                        "type": connected.type,
                        "label": connected.label,
                        "summary": connected.summary,
                    }
                    for connected in connected_nodes
                ],
                "rules": [
                    "Explain why this node matters for learning.",
                    "Describe context, not generic metadata.",
                    "If evidence is insufficient, return source_quality as insufficient_evidence.",
                ],
            },
            ensure_ascii=False,
        )

        try:
            result = await generate_graph_answer(config, prompt, system)
        except GraphAIUnavailable as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(
                status_code=502, detail=f"AI enrichment failed: {exc}"
            ) from exc

        evidence = result.get("source_evidence")
        if isinstance(evidence, str):
            evidence = [evidence]
        if not isinstance(evidence, list) or not evidence:
            raise HTTPException(
                status_code=502,
                detail="AI did not return source evidence for this node.",
            )

        node = GraphWriteService(session).update_node_enrichment(
            node.id,
            {
                "ai_summary": str(result.get("ai_summary") or "").strip(),
                "ai_context": str(result.get("ai_context") or "").strip(),
                "learning_value": str(result.get("learning_value") or "").strip()[:20],
                "source_quality": str(result.get("source_quality") or "ai_enriched")[
                    :20
                ],
                "source_evidence": json.dumps(evidence[:8], ensure_ascii=False),
                "provider": config.get("provider", ""),
                "model": model,
                "prompt_version": "node-enrich.v2",
            },
        )
        return get_node_summary(session, node.id)


@router.post("/nodes/{node_id}/validate-web")
def validate_node_web(node_id: int, response: Response) -> dict:
    response.headers["Deprecation"] = "true"
    response.headers["Sunset"] = "Wed, 30 Sep 2026 23:59:59 GMT"
    response.headers["Link"] = '</api/v1/graph/research-runs>; rel="successor-version"'
    settings = get_settings()
    with SessionLocal() as session:
        if _setting_value(session, "research_mode_enabled", "false") != "true":
            raise HTTPException(
                status_code=403, detail="Research Mode is disabled in Settings."
            )
        result = validate_node_with_web(session, node_id, settings.searxng_url)
        create_automation_log(
            session,
            "GRAPH_NODE_WEB_VALIDATED",
            "graph_node",
            str(node_id),
            "Node validated with web sources.",
            {"researchMode": True},
            result,
            False,
        )
        return result


@router.post("/connections/{edge_id}/generate-insight")
async def generate_connection_insight(edge_id: int) -> dict:
    with SessionLocal() as session:
        edge = session.get(GraphEdgeRecord, edge_id)
        if not edge:
            raise HTTPException(status_code=404, detail="Connection not found")
        source = session.get(GraphNodeRecord, edge.source_node_id)
        target = session.get(GraphNodeRecord, edge.target_node_id)
        if not source or not target:
            raise HTTPException(status_code=404, detail="Connection endpoints missing")

        note_ids = [
            int(value)
            for value in _parse_json_list(edge.source_note_ids)
            if isinstance(value, int | str) and str(value).isdigit()
        ]
        note_ids.extend(
            int(value)
            for node in (source, target)
            for value in _parse_json_list(node.source_note_ids)
            if isinstance(value, int | str) and str(value).isdigit()
        )
        note_ids = list(dict.fromkeys(note_ids))[:12]
        notes = (
            list(
                session.execute(
                    select(NoteRecord).where(NoteRecord.id.in_(note_ids))
                ).scalars()
            )
            if note_ids
            else []
        )

        config = get_ai_config(session)
        model = _current_graph_model(config)
        system = (
            "You generate real second-brain insights from one graph connection. "
            "Use only the provided nodes, connection, notes, and evidence. "
            "Return JSON with: title, description, why_it_matters, evidence, "
            "suggested_action, graph_impact, confidence, reasoning. "
            "Do not produce generic graph metrics or unsupported claims."
        )
        prompt = json.dumps(
            {
                "sourceNode": {
                    "type": source.type,
                    "label": source.label,
                    "summary": source.ai_summary or source.summary,
                    "context": source.ai_context,
                    "manualNotes": source.user_notes,
                },
                "targetNode": {
                    "type": target.type,
                    "label": target.label,
                    "summary": target.ai_summary or target.summary,
                    "context": target.ai_context,
                    "manualNotes": target.user_notes,
                },
                "connection": {
                    "type": edge.type,
                    "label": edge.label,
                    "reason": edge.reason,
                    "confidence": edge.confidence,
                    "evidence": _parse_json_list(edge.evidence),
                    "aiNotes": edge.ai_notes,
                    "manualNotes": edge.user_notes,
                },
                "notes": [
                    {
                        "id": note.id,
                        "title": note.title,
                        "path": note.path,
                        "snippet": note.content[:1200],
                    }
                    for note in notes
                ],
                "rules": [
                    "The insight must be a conclusion, hypothesis, premise, gap, or learning implication.",
                    "Every claim must be traceable to notes or connection evidence.",
                    "If evidence is insufficient, return confidence below 0.45 and explain what is missing.",
                ],
            },
            ensure_ascii=False,
        )

        try:
            result = await generate_graph_answer(config, prompt, system)
        except GraphAIUnavailable as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(
                status_code=502, detail=f"Connection insight failed: {exc}"
            ) from exc

        evidence = result.get("evidence")
        if isinstance(evidence, str):
            evidence = [evidence]
        if not isinstance(evidence, list) or not evidence:
            raise HTTPException(
                status_code=502,
                detail="AI did not return evidence for this connection insight.",
            )

        title = str(result.get("title") or "").strip()
        description = str(result.get("description") or "").strip()
        if not title or not description:
            raise HTTPException(
                status_code=502,
                detail="AI did not return a useful connection insight.",
            )

        existing = session.execute(
            select(InsightRecord).where(
                InsightRecord.title == title,
                InsightRecord.dismissed_at.is_(None),
            )
        ).scalar_one_or_none()
        if existing:
            return {"status": "exists", "insight": serialize_insight(existing)}

        raw_confidence = result.get("confidence")
        try:
            confidence = float(raw_confidence) if raw_confidence is not None else None
        except (TypeError, ValueError):
            confidence = None
        if confidence is None and edge.confidence_sample_size:
            confidence = edge.confidence
        insight = create_insight(
            session,
            "connection_insight",
            title,
            description,
            related_notes=note_ids,
            priority=2 if confidence is not None and confidence >= 0.7 else 1,
            why_it_matters=str(result.get("why_it_matters") or ""),
            evidence=[str(item) for item in evidence[:8]],
            suggested_action=str(result.get("suggested_action") or ""),
            graph_impact=str(result.get("graph_impact") or ""),
            confidence=(
                max(0.0, min(1.0, confidence)) if confidence is not None else None
            ),
            status="suggested",
            provider=config.get("provider", ""),
            model=model,
        )
        insight.prompt_version = "connection-insight.v2"
        insight.reasoning = str(result.get("reasoning") or "")
        insight.source_context = json.dumps(
            {
                "edgeId": edge.id,
                "sourceNodeId": source.id,
                "targetNodeId": target.id,
                "sourceLabel": source.label,
                "targetLabel": target.label,
            },
            ensure_ascii=False,
        )
        session.commit()
        session.refresh(insight)
        create_automation_log(
            session,
            "GRAPH_CONNECTION_INSIGHT_CREATED",
            "graph_edge",
            str(edge.id),
            f'Connection insight created: "{insight.title}"',
            {"edgeId": edge.id},
            {
                "insightId": insight.id,
                "provider": insight.provider,
                "model": insight.model,
            },
            False,
        )
        return {"status": "created", "insight": serialize_insight(insight)}


@router.post("/research-runs", status_code=202)
def start_graph_research_run() -> dict:
    from berrybrain_api.graph_research import (
        create_research_run,
        serialize_research_run,
    )

    with SessionLocal() as session:
        if _setting_value(session, "research_mode_enabled", "false") != "true":
            raise HTTPException(
                status_code=403,
                detail="Research Mode is disabled in Settings.",
            )
        run = create_research_run(session)
        return {"run": serialize_research_run(run)}


@router.get("/research-runs/{run_id}")
def get_graph_research_run(run_id: int) -> dict:
    from berrybrain_api.graph_research import serialize_research_run

    with SessionLocal() as session:
        run = session.get(GraphResearchRunRecord, run_id)
        if run is None:
            raise HTTPException(status_code=404, detail="Research run not found")
        return {"run": serialize_research_run(run)}


@router.post("/research-runs/{run_id}/cancel")
def cancel_graph_research_run(run_id: int) -> dict:
    from berrybrain_api.graph_research import (
        cancel_research_run,
        serialize_research_run,
    )

    with SessionLocal() as session:
        run = cancel_research_run(session, run_id)
        return {"run": serialize_research_run(run)}


@router.get("/research-runs/{run_id}/results")
def graph_research_run_results(run_id: int) -> dict:
    from berrybrain_api.graph_research import serialize_research_result

    with SessionLocal() as session:
        run = session.get(GraphResearchRunRecord, run_id)
        if run is None:
            raise HTTPException(status_code=404, detail="Research run not found")
        results = list(
            session.execute(
                select(GraphResearchResultRecord)
                .where(GraphResearchResultRecord.run_id == run_id)
                .order_by(GraphResearchResultRecord.id.asc())
            ).scalars()
        )
        return {"results": [serialize_research_result(item) for item in results]}


@router.post("/research-runs/{run_id}/execute-internal")
def execute_graph_research_run(run_id: int) -> dict:
    from berrybrain_api.graph_research import (
        execute_research_run,
        serialize_research_run,
    )

    with SessionLocal() as session:
        run = execute_research_run(session, run_id, get_settings().searxng_url)
        return {"run": serialize_research_run(run)}


@router.get("/quality-report")
def quality_report() -> dict:
    with SessionLocal() as session:
        return graph_quality_report(session)


@router.post("/quality-report/recalculate")
def recalculate_quality_report() -> dict:
    with SessionLocal() as session:
        job = create_job(
            session,
            UPDATE_GRAPH_STATS,
            {"scope": "graph_quality"},
            max_attempts=2,
        )
        return {"status": "queued", "jobId": job.id}


@router.post("/confidence/recalculate")
def recalculate_graph_confidence(
    payload: ConfidenceRecalculationRequest,
) -> dict[str, int | str]:
    from berrybrain_api.graph_write_service import (
        recalculate_edge_confidence,
        recalculate_node_confidence,
    )

    with SessionLocal() as session:
        node_query = select(GraphNodeRecord).where(processable_node_clause())
        if payload.node_ids:
            node_query = node_query.where(GraphNodeRecord.id.in_(payload.node_ids))
        nodes = list(session.execute(node_query).scalars())
        node_ids = {node.id for node in nodes}
        edge_query = select(GraphEdgeRecord).where(processable_edge_clause())
        if node_ids:
            edge_query = edge_query.where(
                (GraphEdgeRecord.source_node_id.in_(node_ids))
                | (GraphEdgeRecord.target_node_id.in_(node_ids))
            )
        elif payload.node_ids:
            return {"status": "completed", "nodes": 0, "edges": 0}
        edges = list(session.execute(edge_query).scalars())
        for node in nodes:
            recalculate_node_confidence(node, session)
        for edge in edges:
            recalculate_edge_confidence(edge, session)
        session.commit()
        return {"status": "completed", "nodes": len(nodes), "edges": len(edges)}
