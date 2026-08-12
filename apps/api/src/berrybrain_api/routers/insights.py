import json
import re
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from berrybrain_api.automation_logs import create_automation_log
from berrybrain_api.cognitive_layer import answer_cognitive_query
from berrybrain_api.database import SessionLocal, get_session
from berrybrain_api.graph_inference_service import (
    create_insight_from_persisted_inference,
    persist_graph_inference,
)
from berrybrain_api.jobs import GENERATE_GRAPH_INSIGHTS, create_job
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
    inferenceId: int | None = None
    question: str = ""
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
            keys = {str(key).lower() for key in item}
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
                "concept",
                "connection",
                "vertex",
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
    confidence: float | None,
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
    if (
        not why_it_matters.strip()
        or not suggested_action.strip()
        or not graph_impact.strip()
    ):
        return False, "missing_cognitive_fields"
    if len(evidence) < 2:
        return False, "not_enough_evidence"
    useful_evidence = [item for item in evidence if len(str(item).strip()) >= 8]
    if len(useful_evidence) < 2:
        return False, "weak_evidence"
    if not _has_knowledge_evidence(evidence):
        return False, "missing_knowledge_evidence"
    if confidence is not None and confidence < 0.3:
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
            confidence_raw = item.get("confidence")
            try:
                confidence = (
                    max(0.0, min(1.0, float(confidence_raw)))
                    if confidence_raw is not None
                    else None
                )
            except (TypeError, ValueError):
                confidence = None
            if priority == 0 or priority == 5:
                priority = min(9, 3 + evidence_count)
            # Diversify types if model only generates knowledge_gap
            title_lower = title.lower()
            if itype == "knowledge_gap":
                if any(
                    w in title_lower
                    for w in ["conclusion", "confirmed", "interdepend", "ecosystem"]
                ):
                    itype = "conclusion"
                elif any(
                    w in title_lower
                    for w in [
                        "path",
                        "sequence",
                        "next steps",
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
                    item.get("sourceContext") or item.get("source_context") or {},
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
        auto_job = _ensure_auto_graph_insights(session)
        insights = get_active_insights(session, limit=min(limit, 50))
        return {
            "insights": [serialize_insight(i) for i in insights],
            "autoGeneration": auto_job,
        }


@router.post("/from-inference")
async def create_insight_from_inference(
    payload: InferenceInsightRequest,
    session: Session = Depends(get_session),
) -> dict:
    if payload.inferenceId is not None:
        return create_insight_from_persisted_inference(session, payload.inferenceId)

    # Compatibility path for older clients. The server deliberately ignores the
    # supplied inference JSON and regenerates a canonical, persisted result.
    question = payload.question.strip()
    if not question:
        raise HTTPException(status_code=422, detail="Question is required")
    result = await answer_cognitive_query(session, question)
    inference = persist_graph_inference(session, question, result)
    return create_insight_from_persisted_inference(session, inference.id)


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
        insight.status = "accepted"
        insight.applied_at = utc_now()
        insight.feedback_score += 1
        insight.expires_at = None
        insight.updated_at = utc_now()
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
        return {"status": "accepted", "insight": serialize_insight(insight)}


@router.post("/{insight_id}/converted-to-note")
def converted_to_note_endpoint(insight_id: int) -> dict:
    with SessionLocal() as session:
        insight = session.get(InsightRecord, insight_id)
        if insight is None:
            return {"status": "insight_not_found"}
        insight.status = "converted_to_note"
        insight.feedback_score += 1
        insight.expires_at = None
        insight.updated_at = datetime.now(UTC)
        session.commit()
        session.refresh(insight)
        return {"status": insight.status, "insight": serialize_insight(insight)}


@router.post("/{insight_id}/create-note")
def create_note_from_insight(insight_id: int) -> dict:
    with SessionLocal() as session:
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


@router.post("/generate")
def generate_insights() -> dict:
    with SessionLocal() as session:
        job = create_job(
            session,
            GENERATE_GRAPH_INSIGHTS,
            {"trigger": "manual", "idempotency_key": "manual-graph-insights"},
            max_attempts=2,
        )
        return {"status": "job_created", "job_id": job.id}


def _ensure_auto_graph_insights(session: Session) -> dict:
    from berrybrain_api.agent_monitor import ensure_agent_monitoring

    result = ensure_agent_monitoring(session)
    insight_job = next(
        (
            item
            for item in result.get("jobs", [])
            if item.get("type") == GENERATE_GRAPH_INSIGHTS
        ),
        None,
    )
    return {
        "status": "queued" if insight_job else result.get("status", "monitoring"),
        "jobId": insight_job.get("id") if insight_job else None,
    }
