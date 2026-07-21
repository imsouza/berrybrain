from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from berrybrain_api.automation_logs import create_automation_log
from berrybrain_api.models import GraphInferenceRecord, InsightRecord
from berrybrain_api.modules.graph_inference.domain import (
    InferenceNotSavableError,
    InferenceSnapshot,
    MissingGroundedEvidenceError,
    build_insight_draft,
)
from berrybrain_api.second_brain import expand_knowledge_graph
from berrybrain_api.services import create_insight, serialize_insight

PROMPT_VERSION = "graph-inference.v2"


def persist_graph_inference(
    session: Session,
    question: str,
    result: dict[str, Any],
) -> GraphInferenceRecord:
    record = GraphInferenceRecord(
        question=question.strip(),
        answer=str(result.get("answer") or "").strip(),
        status=str(result.get("status") or "insufficient_evidence"),
        confidence=_confidence(result.get("confidence")),
        routes=_json(result.get("routes")),
        evidence=_json(result.get("evidence")),
        related_nodes=_json(result.get("relatedNodes")),
        suggestions=_json(result.get("suggestions")),
        provider=str(result.get("provider") or ""),
        model=str(result.get("model") or ""),
        prompt_version=PROMPT_VERSION,
    )
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


def serialize_graph_inference(record: GraphInferenceRecord) -> dict[str, Any]:
    return {
        "inferenceId": record.id,
        "status": record.status,
        "question": record.question,
        "answer": record.answer,
        "routes": _list(record.routes),
        "evidence": _list(record.evidence),
        "relatedNodes": _list(record.related_nodes),
        "suggestions": _list(record.suggestions),
        "confidence": record.confidence,
        "provider": record.provider,
        "model": record.model,
        "promptVersion": record.prompt_version,
        "insightId": record.insight_id,
        "createdAt": record.created_at.isoformat() if record.created_at else None,
    }


def create_insight_from_persisted_inference(
    session: Session,
    inference_id: int,
) -> dict[str, Any]:
    inference = session.get(GraphInferenceRecord, inference_id)
    if inference is None:
        raise HTTPException(status_code=404, detail="Graph inference not found")
    routes = tuple(str(item) for item in _list(inference.routes) if str(item).strip())
    snapshot = InferenceSnapshot(
        id=inference.id,
        question=inference.question,
        answer=inference.answer,
        status=inference.status,
        confidence=inference.confidence,
        routes=routes,
        evidence=tuple(_list(inference.evidence)),
        related_nodes=tuple(_list(inference.related_nodes)),
        provider=inference.provider,
        model=inference.model,
        prompt_version=inference.prompt_version,
    )
    try:
        draft = build_insight_draft(snapshot)
    except InferenceNotSavableError as exc:
        raise HTTPException(
            status_code=409,
            detail="This inference cannot become an insight until processing completes.",
        ) from exc
    except MissingGroundedEvidenceError as exc:
        raise HTTPException(
            status_code=422,
            detail="A grounded knowledge insight requires persisted evidence.",
        ) from exc
    if inference.insight_id:
        existing = session.get(InsightRecord, inference.insight_id)
        if existing is not None:
            return {"status": "existing", "insight": serialize_insight(existing)}

    insight = create_insight(
        session,
        draft.type,
        draft.title,
        draft.description,
        [],
        draft.priority,
        why_it_matters=draft.why_it_matters,
        evidence=list(draft.evidence),
        suggested_action=draft.suggested_action,
        graph_impact=draft.graph_impact,
        confidence=draft.confidence,
        status="suggested",
        provider=inference.provider,
        model=inference.model,
        prompt_version=inference.prompt_version,
        reasoning=f"Created from persisted graph inference {inference.id}.",
        source_context=json.dumps(
            {
                "inferenceId": inference.id,
                "question": inference.question,
                "routes": list(snapshot.routes),
                "relatedNodes": list(snapshot.related_nodes),
                "grounded": draft.grounded,
            },
            ensure_ascii=False,
        ),
    )
    inference.insight_id = insight.id
    inference.updated_at = datetime.now(UTC)
    session.commit()
    expand_knowledge_graph(session)
    create_automation_log(
        session,
        "INSIGHT_CREATED_FROM_INFERENCE",
        "insight",
        str(insight.id),
        f'Insight created from graph question: "{inference.question}"',
        {"inferenceId": inference.id, "status": inference.status},
        {"insightId": insight.id, "type": insight.type},
        False,
    )
    return {"status": "created", "insight": serialize_insight(insight)}


def _json(value: Any) -> str:
    return json.dumps(value if isinstance(value, list) else [], ensure_ascii=False)


def _list(value: str) -> list[Any]:
    try:
        parsed = json.loads(value or "[]")
    except (TypeError, json.JSONDecodeError):
        return []
    return parsed if isinstance(parsed, list) else []


def _confidence(value: Any) -> float:
    try:
        return max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return 0.0
