from pydantic import BaseModel

from fastapi import APIRouter

from berrybrain_api.database import SessionLocal
from berrybrain_api.second_brain import infer_from_graph
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

INSIGHT_TYPE_DISPLAY = {
    "context": "Tema central",
    "conclusion": "Relação confirmada",
    "hypothesis": "Possível conexão",
    "premise": "Padrão recorrente",
    "assertion": "Evidência forte",
    "knowledge_gap": "Falta explorar",
    "new_connection": "Nova conexão",
    "study_path": "Trilha de estudo",
    "possible_contradiction": "Possível conflito",
    "deepening_opportunity": "Aprofundamento",
    "recurring_concept": "Conceito recorrente",
    "review_opportunity": "Revisão sugerida",
    "permanent_note_candidate": "Nota sugerida",
    "emerging_context": "Contexto emergente",
}


@router.post("/sync")
def sync_insights_from_ai(payload: SyncInsightsRequest) -> dict:
    data = payload.payload
    insights = data.get("insights", [])
    if not insights and isinstance(data, dict):
        items = [data] if data else []
    else:
        items = insights if isinstance(insights, list) else []

    created = 0
    with SessionLocal() as session:
        gap_count = 0
        for item in items:
            if not isinstance(item, dict):
                continue
            itype = item.get("type", "knowledge_gap")
            if itype not in VALID_INSIGHT_TYPES:
                itype = "knowledge_gap"
            if itype == "knowledge_gap":
                gap_count += 1
            title = str(
                item.get("title", "") or item.get("description", "") or "Insight"
            )
            desc = str(item.get("description", "") or item.get("title", "") or "")
            priority = item.get("priority", 5) or 5
            try:
                priority = int(priority)
            except:
                priority = 5
            related = item.get("related_notes", []) or []
            evidence = (
                item.get("evidence", [])
                if isinstance(item.get("evidence", []), list)
                else []
            )
            evidence_count = len(evidence)
            confidence = float(item.get("confidence", 0.7) or 0.7)
            # Base confidence on evidence count + model value
            import random

            if confidence < 0.3 or confidence == 0.5:
                base = 0.45 + (evidence_count * 0.08)
                jitter = random.uniform(-0.05, 0.05)
                confidence = min(0.95, max(0.35, base + jitter))
            if confidence > 0.95:
                confidence = 0.95
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
                    for w in ["trilha", "sequência", "caminho", "próximos passos"]
                ):
                    itype = "study_path"
                elif any(
                    w in title_lower
                    for w in ["hipótese", "possivel", "talvez", "especul", "pode ser"]
                ):
                    itype = "hypothesis"
                elif any(
                    w in title_lower for w in ["conex", "liga", "relacion", "ponte"]
                ):
                    itype = "new_connection"
                elif any(w in title_lower for w in ["fundamento", "base", "premissa"]):
                    itype = "premise"
                elif any(
                    w in title_lower
                    for w in [
                        "contexto",
                        "ecossistema",
                        "cluster",
                        "núcleo",
                        "panorama",
                    ]
                ):
                    itype = "context"
            evidence = (
                item.get("evidence", [])
                if isinstance(item.get("evidence", []), list)
                else []
            )
            evidence_count = len(evidence)

            create_insight(
                session,
                itype,
                title,
                desc,
                related if isinstance(related, list) else [],
                priority,
                why_it_matters=item.get("why_it_matters", ""),
                evidence=evidence,
                suggested_action=item.get("suggested_action", ""),
                graph_impact=item.get("graph_impact", ""),
                confidence=confidence,
                status=item.get("status", "suggested"),
                provider=item.get("provider", ""),
                model=item.get("model", ""),
            )
            created += 1
    return {"status": "synced", "insights_created": created}


@router.get("")
def list_insights(limit: int = 10) -> dict:
    with SessionLocal() as session:
        insights = get_active_insights(session, limit=min(limit, 50))
        return {"insights": [serialize_insight(i) for i in insights]}


@router.post("/from-inference")
def create_insight_from_inference(payload: InferenceInsightRequest) -> dict:
    with SessionLocal() as session:
        result = infer_from_graph(session, payload.question)
        if result["status"] != "answered":
            return {"status": "insufficient_evidence", "inference": result}
        insight = create_insight(
            session,
            "new_connection",
            payload.question,
            result["answer"],
            [],
            3,
            why_it_matters="Esta relação foi sustentada por conexões reais do grafo.",
            evidence=result.get("evidence", []),
            suggested_action="Revisar nós relacionados e decidir se a conexão deve virar nota permanente.",
            graph_impact="Pode consolidar uma conexão explicável no grafo.",
            confidence=float(result.get("confidence", 0.5) or 0.5),
            status="suggested",
            provider="deterministic",
            model="graph-inference.v1",
        )
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
        return {"status": "applied", "insight": serialize_insight(insight)}


@router.post("/{insight_id}/create-note")
def create_note_from_insight(insight_id: int) -> dict:
    with SessionLocal() as session:
        from berrybrain_api.jobs import utc_now

        insight = session.get(InsightRecord, insight_id)
        if insight is None:
            return {"status": "insight_not_found"}

        from berrybrain_api.models import JobRecord

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
        from berrybrain_api.models import JobRecord

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
        from berrybrain_api.models import JobRecord

        job = JobRecord(
            type="GENERATE_GRAPH_INSIGHTS",
            status="pending",
            payload="{}",
        )
        session.add(job)
        session.commit()
        session.refresh(job)
        return {"status": "job_created", "job_id": job.id}
