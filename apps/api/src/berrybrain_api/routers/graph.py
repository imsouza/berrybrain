import json
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from berrybrain_api.ai_gateway import (
    GraphAIUnavailable,
    generate_graph_answer,
    get_ai_config,
)
from berrybrain_api.automation_logs import create_automation_log
from berrybrain_api.cognitive_layer import answer_cognitive_query
from berrybrain_api.config import get_settings
from berrybrain_api.database import SessionLocal
from berrybrain_api.jobs import ENRICH_GRAPH_NODE, PENDING, RUNNING, create_job
from berrybrain_api.models import (
    GraphEdgeRecord,
    GraphNodeRecord,
    InsightRecord,
    JobRecord,
    NoteRecord,
    SettingRecord,
)
from berrybrain_api.second_brain import (
    expand_knowledge_graph,
    generate_inferred_graph_connections,
    get_node_summary,
    set_edge_status,
    set_edge_user_notes,
    set_node_status,
    set_node_user_notes,
    summarize_graph,
    delete_graph_node,
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


class GraphInferRequest(BaseModel):
    question: str


class ManualNotesRequest(BaseModel):
    notes: str = ""


class EnrichNodeRequest(BaseModel):
    ai_summary: str = ""
    ai_context: str = ""
    source_evidence: str = ""
    learning_value: str = ""
    source_quality: str = ""
    provider: str = ""
    model: str = ""
    reasoning: str = ""


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


@router.get("")
def get_graph(
    max_depth: int = 2,
    view: str = "",
) -> dict:
    """GET /graph supports view filtering: enriched, raw, validated, needs_review, hidden."""
    with SessionLocal() as session:
        return build_graph(session, max_depth=max_depth, view=view)


@router.get("/summary")
def get_graph_summary() -> dict:
    with SessionLocal() as session:
        return summarize_graph(session)


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
async def infer_graph(payload: GraphInferRequest) -> dict:
    with SessionLocal() as session:
        return await answer_cognitive_query(session, payload.question)


@router.post("/sync")
def sync_graph() -> dict:
    with SessionLocal() as session:
        result = sync_knowledge_graph(session)
        return {"status": "synced", **result}


@router.post("/enrich-missing")
def enrich_missing_graph_nodes(limit: int = 20) -> dict:
    with SessionLocal() as session:
        candidates = list(
            session.execute(
                select(GraphNodeRecord)
                .where(GraphNodeRecord.status != "ignored")
                .where(
                    (GraphNodeRecord.ai_context == "")
                    | (GraphNodeRecord.ai_context.is_(None))
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
            create_job(session, ENRICH_GRAPH_NODE, {"node_id": node.id}, max_attempts=2)
            created += 1
        return {"queued": created, "skipped": skipped, "candidates": len(candidates)}


@router.get("/nodes/{node_id}/summary")
def graph_node_summary(node_id: int) -> dict:
    with SessionLocal() as session:
        return get_node_summary(session, node_id)


@router.post("/nodes/{node_id}/confirm")
def confirm_graph_node(node_id: int) -> dict:
    with SessionLocal() as session:
        node = set_node_status(session, node_id, "confirmed")
        create_automation_log(
            session,
            "GRAPH_NODE_CONFIRMED",
            "graph_node",
            str(node.id),
            f'Node confirmed: "{node.label}"',
            {"status": "suggested"},
            {"status": node.status},
            False,
        )
        return {"id": node.id, "status": node.status}


@router.post("/nodes/{node_id}/ignore")
def ignore_graph_node(node_id: int) -> dict:
    with SessionLocal() as session:
        node = set_node_status(session, node_id, "ignored")
        create_automation_log(
            session,
            "GRAPH_NODE_IGNORED",
            "graph_node",
            str(node.id),
            f'Node ignored: "{node.label}"',
            {"status": "suggested"},
            {"status": node.status},
            False,
        )
        return {"id": node.id, "status": node.status}


@router.delete("/nodes/{node_id}")
def delete_graph_node_endpoint(node_id: int) -> dict:
    with SessionLocal() as session:
        node = session.get(GraphNodeRecord, node_id)
        removed = delete_graph_node(session, node_id)
        if not removed:
            raise HTTPException(status_code=404, detail="node not found")
        create_automation_log(
            session,
            "GRAPH_NODE_DELETED",
            "graph_node",
            str(node_id),
            f'Node deleted from graph: "{node.label if node else node_id}"',
            {"id": node_id, "label": node.label if node else ""},
            {"deleted": True},
            False,
        )
        return {"id": node_id, "status": "deleted"}


@router.post("/nodes/{node_id}/reprocess")
def reprocess_graph_node(node_id: int) -> dict:
    with SessionLocal() as session:
        node = session.get(GraphNodeRecord, node_id)
        if node is None:
            raise HTTPException(status_code=404, detail="Node not found")
        job = create_job(
            session, ENRICH_GRAPH_NODE, {"node_id": node.id}, max_attempts=2
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


@router.put("/nodes/{node_id}/notes")
def update_graph_node_notes(node_id: int, payload: ManualNotesRequest) -> dict:
    with SessionLocal() as session:
        node = set_node_user_notes(session, node_id, payload.notes)
        return {"id": node.id, "userNotes": node.user_notes}


@router.post("/connections/{edge_id}/confirm")
def confirm_graph_edge(edge_id: int) -> dict:
    with SessionLocal() as session:
        edge = set_edge_status(session, edge_id, "confirmed")
        create_automation_log(
            session,
            "GRAPH_CONNECTION_CONFIRMED",
            "graph_edge",
            str(edge.id),
            f"Connection confirmed: {edge.label or edge.type}",
            {"status": "suggested"},
            {"status": edge.status},
            False,
        )
        return {"id": edge.id, "status": edge.status}


@router.put("/connections/{edge_id}/notes")
def update_graph_edge_notes(edge_id: int, payload: ManualNotesRequest) -> dict:
    with SessionLocal() as session:
        edge = set_edge_user_notes(session, edge_id, payload.notes)
        return {"id": edge.id, "userNotes": edge.user_notes}


@router.post("/connections/{edge_id}/ignore")
def ignore_graph_edge(edge_id: int) -> dict:
    with SessionLocal() as session:
        edge = set_edge_status(session, edge_id, "ignored")
        create_automation_log(
            session,
            "GRAPH_CONNECTION_IGNORED",
            "graph_edge",
            str(edge.id),
            f"Connection ignored: {edge.label or edge.type}",
            {"status": "suggested"},
            {"status": edge.status},
            False,
        )
        return {"id": edge.id, "status": edge.status}


# --- Enrichment & Validation endpoints ---


@router.post("/nodes/{node_id}/enrich")
def enrich_graph_node(node_id: int, payload: EnrichNodeRequest) -> dict:
    with SessionLocal() as session:
        node = session.get(GraphNodeRecord, node_id)
        if not node:
            return {"error": "Node not found"}
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
        if payload.ai_summary:
            node.ai_summary = payload.ai_summary
        if payload.ai_context:
            node.ai_context = payload.ai_context
        if payload.source_evidence:
            node.source_evidence = payload.source_evidence
        if payload.learning_value:
            node.learning_value = payload.learning_value
        if payload.source_quality:
            node.source_quality = payload.source_quality
        if payload.provider:
            node.provider = payload.provider
        if payload.model:
            node.model = payload.model
        if payload.provider or payload.model:
            node.prompt_version = "enrich-node.v1"
            from datetime import UTC, datetime

            node.generated_at = datetime.now(UTC)
        from datetime import UTC, datetime

        node.updated_at = datetime.now(UTC)
        session.commit()
        return {"id": node.id, "enriched": True}


@router.post("/nodes/{node_id}/enrich-ai")
async def enrich_graph_node_with_ai(node_id: int) -> dict:
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
                .where(GraphEdgeRecord.status != "ignored")
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

        node.ai_summary = str(result.get("ai_summary") or "").strip()
        node.ai_context = str(result.get("ai_context") or "").strip()
        node.learning_value = str(result.get("learning_value") or "").strip()[:20]
        node.source_quality = str(result.get("source_quality") or "ai_enriched")[:20]
        node.source_evidence = json.dumps(evidence[:8], ensure_ascii=False)
        node.provider = config.get("provider", "")
        node.model = model
        node.prompt_version = "node-enrich.v2"
        node.generated_at = datetime.now(UTC)
        node.updated_at = datetime.now(UTC)
        session.commit()
        session.refresh(node)
        create_automation_log(
            session,
            "GRAPH_NODE_ENRICHED",
            "graph_node",
            str(node.id),
            f'Node enriched with AI: "{node.label}"',
            {"provider": node.provider, "model": node.model},
            {
                "promptVersion": node.prompt_version,
                "sourceQuality": node.source_quality,
            },
            False,
        )
        return get_node_summary(session, node.id)


@router.post("/nodes/{node_id}/validate-web")
def validate_node_web(node_id: int) -> dict:
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

        confidence = float(result.get("confidence") or edge.confidence or 0.5)
        insight = create_insight(
            session,
            "connection_insight",
            title,
            description,
            related_notes=note_ids,
            priority=2 if confidence >= 0.7 else 1,
            why_it_matters=str(result.get("why_it_matters") or ""),
            evidence=[str(item) for item in evidence[:8]],
            suggested_action=str(result.get("suggested_action") or ""),
            graph_impact=str(result.get("graph_impact") or ""),
            confidence=max(0.0, min(1.0, confidence)),
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


@router.get("/quality-report")
def quality_report() -> dict:
    with SessionLocal() as session:
        return graph_quality_report(session)
