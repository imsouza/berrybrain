import json
import re

from pydantic import BaseModel

from fastapi import APIRouter

from berrybrain_api.automation_logs import create_automation_log
from berrybrain_api.cognitive_layer import answer_cognitive_query
from berrybrain_api.database import SessionLocal
from berrybrain_api.models import InsightRecord, JobRecord
from berrybrain_api.second_brain import expand_knowledge_graph
from berrybrain_api.services import (
    create_insight,
    dismiss_insight,
    get_active_insights,
    serialize_insight,
)

router = APIRouter(prefix="/api/v1/insights", tags=["insights"])


class SyncInsightsRequest(BaseModel):
    payload: dict


class InferenceInsightRequest(BaseModel):
    question: str
    inference: dict | None = None


VALID_INSIGHT_TYPES = {
    "knowledge_gap",
    "new_connection",
    "recurring_concept",
    "weak_concept",
    "central_concept",
    "isolated_note",
    "duplicate_content",
    "permanent_note_candidate",
    "study_path",
    "review_opportunity",
    "possible_contradiction",
    "emerging_context",
    "growing_cluster",
    "neglected_subject",
    "deepening_opportunity",
    "weak_note",
    "isolated_concept",
    "context",
    "conclusion",
    "hypothesis",
    "premise",
    "assertion",
}

SYSTEM_DIAGNOSTIC_TYPES = {
    "system_diagnostic",
    "pipeline_bottleneck",
    "provider_issue",
    "job_backlog",
    "worker_status",
}

INTERNAL_TECHNICAL_TERMS = (
    "explainedconnections",
    "graphnotes",
    "jobsbytype",
    "generate_note_title",
    "enrich_graph_node",
    "generate_graph_insights",
    "semanticstate",
    "raw json",
    "pipeline bottleneck",
    "jobrecord",
    "pendingjobs",
    "activejobs",
    "failedjobs",
    "provider status",
    "worker status",
    "backlog",
    "queue",
)

INSIGHT_TYPE_DISPLAY = {
    "context": "Central theme",
    "conclusion": "Confirmed relationship",
    "hypothesis": "Possible connection",
    "premise": "Recurring pattern",
    "assertion": "Strong evidence",
    "knowledge_gap": "Gap to explore",
    "new_connection": "New connection",
    "study_path": "Study path",
    "possible_contradiction": "Possible conflict",
    "deepening_opportunity": "Deepening opportunity",
    "recurring_concept": "Recurring concept",
    "review_opportunity": "Suggested review",
    "permanent_note_candidate": "Suggested note",
    "emerging_context": "Emerging context",
}

GENERIC_INSIGHT_TITLES = {
    "insight",
    "new insight",
    "knowledge gap",
    "gap to explore",
    "new connection",
    "central theme",
    "suggested review",
}

GENERIC_PHRASES = (
    "node central in the graph",
    "nó central no grafo",
    "central node in the graph",
    "continue writing",
    "keep writing",
    "not enough information",
)


def _as_list(value: object) -> list:
    return value if isinstance(value, list) else []


def _as_float(value: object, default: float = 0.7) -> float:
    try:
        parsed = float(value or default)
    except (TypeError, ValueError):
        parsed = default
    return max(0.0, min(0.95, parsed))


def _as_int(value: object, default: int = 5) -> int:
    try:
        return int(value or default)
    except (TypeError, ValueError):
        return default


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def _evidence_text(item: object) -> str:
    if isinstance(item, dict):
        visible = [
            item.get("source"),
            item.get("title"),
            item.get("text"),
            item.get("reference"),
            item.get("quoteOrSummary"),
            item.get("whyRelevant"),
            item.get("path"),
            item.get("type"),
        ]
        return _normalize_text(" ".join(str(v) for v in visible if v))
    return _normalize_text(str(item))


def _has_internal_technical_terms(*values: object) -> bool:
    combined = _normalize_text(" ".join(str(value or "") for value in values))
    return any(term in combined for term in INTERNAL_TECHNICAL_TERMS)


def _has_knowledge_evidence(evidence: list) -> bool:
    for item in evidence:
        if isinstance(item, dict):
            source = _normalize_text(str(item.get("source", "")))
            keys = {str(key).lower() for key in item.keys()}
            if source in {"knowledge_base", "knowledge_graph"}:
                return True
            if keys & {
                "note_id",
                "noteid",
                "source_note_id",
                "sourcenoteid",
                "source_note_ids",
                "sourcenoteids",
                "node_id",
                "nodeid",
                "edge_id",
                "edgeid",
                "concept",
                "path",
                "reference",
            }:
                return True
        text = _evidence_text(item)
        if any(
            marker in text
            for marker in (
                ".md",
                "note:",
                "nota:",
                "concept",
                "conceito",
                "connection",
                "conexao",
                "conexão",
                "vertex",
                "vertice",
                "vértice",
                "node:",
                "edge:",
                "↔",
            )
        ):
            return True
        if "/" in text and not _has_internal_technical_terms(text):
            return True
    return False


def _is_system_diagnostic_item(
    itype: str,
    title: str,
    description: str,
    why_it_matters: str,
    suggested_action: str,
    graph_impact: str,
    evidence: list,
) -> bool:
    if itype in SYSTEM_DIAGNOSTIC_TYPES:
        return True
    if not _has_internal_technical_terms(
        title, description, why_it_matters, suggested_action, graph_impact, evidence
    ):
        return False
    return not _has_knowledge_evidence(evidence)


def _is_valid_generated_insight(
    title: str,
    description: str,
    why_it_matters: str,
    suggested_action: str,
    graph_impact: str,
    evidence: list,
    confidence: float,
) -> tuple[bool, str]:
    normalized_title = _normalize_text(title)
    combined = _normalize_text(
        " ".join([title, description, why_it_matters, suggested_action, graph_impact])
    )
    if normalized_title in GENERIC_INSIGHT_TITLES:
        return False, "generic_title"
    if _has_internal_technical_terms(
        title, description, why_it_matters, suggested_action, graph_impact, evidence
    ):
        return False, "technical_or_system_diagnostic"
    if any(phrase in combined for phrase in GENERIC_PHRASES):
        return False, "generic_phrase"
    if len(title.strip()) < 12 or len(description.strip()) < 50:
        return False, "too_short"
    if not why_it_matters.strip() or not suggested_action.strip() or not graph_impact.strip():
        return False, "missing_cognitive_fields"
    if len(evidence) < 2:
        return False, "not_enough_evidence"
    useful_evidence = [item for item in evidence if len(str(item).strip()) >= 8]
    if len(useful_evidence) < 2:
        return False, "weak_evidence"
    if not _has_knowledge_evidence(evidence):
        return False, "missing_knowledge_evidence"
    if confidence < 0.3:
        return False, "low_confidence"
    return True, ""


@router.post("/sync")
def sync_insights_from_ai(payload: SyncInsightsRequest) -> dict:
    data = payload.payload
    insights = data.get("insights", [])
    if not insights and isinstance(data, dict):
        items = [data] if data else []
    else:
        items = insights if isinstance(insights, list) else []

    created = 0
    skipped: list[dict] = []
    with SessionLocal() as session:
        for item in items:
            if not isinstance(item, dict):
                continue
            itype = item.get("type", "knowledge_gap")
            title = str(
                item.get("title", "") or item.get("description", "") or "Insight"
            )
            desc = str(item.get("description", "") or item.get("title", "") or "")
            why_it_matters = str(item.get("why_it_matters", "") or "")
            suggested_action = str(item.get("suggested_action", "") or "")
            graph_impact = str(item.get("graph_impact", "") or "")
            evidence = _as_list(item.get("evidence", []))
            if _is_system_diagnostic_item(
                str(itype),
                title,
                desc,
                why_it_matters,
                suggested_action,
                graph_impact,
                evidence,
            ):
                skipped.append({"title": title[:120], "reason": "system_diagnostic"})
                continue
            if itype not in VALID_INSIGHT_TYPES:
                itype = "knowledge_gap"
            priority = _as_int(item.get("priority", 5), 5)
            related = item.get("related_notes", []) or []
            evidence_count = len(evidence)
            confidence = _as_float(item.get("confidence", 0.7), 0.7)
            # Confidence = estimated probability the insight is valid, in [0,1].
            # When the model is silent or uncertain, derive deterministically from
            # evidence volume so the same insight yields a stable, reproducible %.
            if confidence < 0.3 or confidence == 0.5:
                base = 0.45 + (evidence_count * 0.08)
                confidence = min(0.95, max(0.35, base))
            if priority == 0 or priority == 5:
                priority = min(9, 3 + evidence_count)
            # Diversify types if model only generates knowledge_gap
            title_lower = title.lower()
            if itype == "knowledge_gap":
                if any(
                    w in title_lower
                    for w in ["conclus", "confirmado", "interdep", "ecossistema"]
                ):
                    itype = "conclusion"
                elif any(
                    w in title_lower
                    for w in [
                        "path",
                        "sequence",
                        "next steps",
                        "trilha",
                        "sequência",
                        "caminho",
                        "próximos passos",
                    ]
                ):
                    itype = "study_path"
                elif any(
                    w in title_lower
                    for w in [
                        "hypothesis",
                        "possible",
                        "maybe",
                        "speculat",
                        "hipótese",
                        "possivel",
                        "talvez",
                    ]
                ):
                    itype = "hypothesis"
                elif any(
                    w in title_lower
                    for w in [
                        "connect",
                        "relation",
                        "bridge",
                        "conex",
                        "liga",
                        "relacion",
                        "ponte",
                    ]
                ):
                    itype = "new_connection"
                elif any(
                    w in title_lower
                    for w in ["foundation", "base", "premise", "fundamento", "premissa"]
                ):
                    itype = "premise"
                elif any(
                    w in title_lower
                    for w in [
                        "context",
                        "ecossistema",
                        "ecosystem",
                        "cluster",
                        "core",
                        "panorama",
                    ]
                ):
                    itype = "context"
            is_valid, reason = _is_valid_generated_insight(
                title,
                desc,
                why_it_matters,
                suggested_action,
                graph_impact,
                evidence,
                confidence,
            )
            if not is_valid:
                skipped.append({"title": title[:120], "reason": reason})
                continue

            create_insight(
                session,
                itype,
                title,
                desc,
                related if isinstance(related, list) else [],
                priority,
                why_it_matters=why_it_matters,
                evidence=evidence,
                suggested_action=suggested_action,
                graph_impact=graph_impact,
                confidence=confidence,
                status=item.get("status", "suggested"),
                provider=item.get("provider", ""),
                model=item.get("model", ""),
                prompt_version=item.get("promptVersion")
                or item.get("prompt_version")
                or "insight-generate.v2",
                reasoning=str(item.get("reasoning", "") or ""),
                source_context=json.dumps(
                    item.get("sourceContext")
                    or item.get("source_context")
                    or {},
                    ensure_ascii=False,
                ),
            )
            created += 1
        if created:
            expand_knowledge_graph(session)
    return {"status": "synced", "insights_created": created, "skipped": skipped[:20]}


@router.get("")
def list_insights(limit: int = 10) -> dict:
    with SessionLocal() as session:
        insights = get_active_insights(session, limit=min(limit, 50))
        return {"insights": [serialize_insight(i) for i in insights]}


@router.post("/from-inference")
async def create_insight_from_inference(payload: InferenceInsightRequest) -> dict:
    with SessionLocal() as session:
        result = payload.inference or await answer_cognitive_query(session, payload.question)
        if result["status"] not in {"answered", "success", "sufficient_evidence"}:
            return {"status": "insufficient_evidence", "inference": result}
        insight = create_insight(
            session,
            "new_connection",
            f"Inference: {payload.question}"[:255],
            result["answer"],
            [],
            6,
            why_it_matters="This inference is grounded in the Knowledge Base, Knowledge Graph, and Semantic Data evidence returned by the configured model.",
            evidence=result.get("evidence", []),
            suggested_action="Review the cited nodes and decide whether this should become a permanent note or confirmed graph connection.",
            graph_impact="Creates an insight node linked to the evidence that supported the graph inference.",
            confidence=float(result.get("confidence", 0.5) or 0.5),
            status="suggested",
            provider=result.get("provider", ""),
            model=result.get("model", ""),
            prompt_version="graph-inference.v2",
            reasoning=f"Saved from graph inference question: {payload.question}",
            source_context=json.dumps(
                {
                    "question": payload.question,
                    "routes": result.get("routes", []),
                    "relatedNodes": result.get("relatedNodes", []),
                },
                ensure_ascii=False,
            ),
        )
        expand_knowledge_graph(session)
        return {"status": "created", "insight": serialize_insight(insight)}


@router.post("/{insight_id}/dismiss")
def dismiss_insight_endpoint(insight_id: int) -> dict:
    with SessionLocal() as session:
        insight = dismiss_insight(session, insight_id)
        return {"insight": serialize_insight(insight)}


@router.post("/{insight_id}/ignore")
def ignore_insight_endpoint(insight_id: int) -> dict:
    with SessionLocal() as session:
        insight = dismiss_insight(session, insight_id)
        create_automation_log(
            session,
            "INSIGHT_IGNORED",
            "insight",
            str(insight.id),
            f'Insight ignored: "{insight.title}"',
            {"status": insight.status},
            {"dismissed": True},
            False,
        )
        return {"insight": serialize_insight(insight)}


@router.post("/{insight_id}/apply")
def apply_insight_endpoint(insight_id: int) -> dict:
    with SessionLocal() as session:
        from berrybrain_api.jobs import utc_now

        insight = session.get(InsightRecord, insight_id)
        if insight is None:
            return {"status": "insight_not_found"}
        insight.status = "applied"
        insight.applied_at = utc_now()
        session.commit()
        session.refresh(insight)
        create_automation_log(
            session,
            "INSIGHT_APPLIED",
            "insight",
            str(insight.id),
            f'Insight applied: "{insight.title}"',
            {"status": "suggested"},
            {"status": insight.status},
            False,
        )
        return {"status": "applied", "insight": serialize_insight(insight)}


@router.post("/{insight_id}/create-note")
def create_note_from_insight(insight_id: int) -> dict:
    with SessionLocal() as session:
        from berrybrain_api.jobs import utc_now

        insight = session.get(InsightRecord, insight_id)
        if insight is None:
            return {"status": "insight_not_found"}

        job = JobRecord(
            type="CREATE_NOTE_FROM_INSIGHT",
            status="pending",
            payload=f'{{"insight_id": {insight_id}}}',
        )
        session.add(job)
        session.commit()
        session.refresh(job)
        return {"status": "job_created", "job_id": job.id}


@router.post("/{insight_id}/create-review")
def create_review_from_insight(insight_id: int) -> dict:
    with SessionLocal() as session:
        insight = session.get(InsightRecord, insight_id)
        if insight is None:
            return {"status": "insight_not_found"}

        job = JobRecord(
            type="CREATE_REVIEW_FROM_INSIGHT",
            status="pending",
            payload=f'{{"insight_id": {insight_id}}}',
        )
        session.add(job)
        session.commit()
        session.refresh(job)
        return {"status": "job_created", "job_id": job.id}


@router.post("/generate")
def generate_insights() -> dict:
    with SessionLocal() as session:
        job = JobRecord(
            type="GENERATE_GRAPH_INSIGHTS",
            status="pending",
            payload="{}",
        )
        session.add(job)
        session.commit()
        session.refresh(job)
        return {"status": "job_created", "job_id": job.id}
