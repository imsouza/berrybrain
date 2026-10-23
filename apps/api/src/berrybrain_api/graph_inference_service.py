from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException, Request
from sqlalchemy.orm import Session

from berrybrain_api.automation_logs import create_automation_log
from berrybrain_api.confidence import (
    estimate_connection_confidence,
    persist_confidence,
    serialize_confidence,
)
from berrybrain_api.config import Settings, get_settings
from berrybrain_api.jobs import EXPAND_KNOWLEDGE_GRAPH, create_job
from berrybrain_api.models import GraphInferenceRecord, InsightRecord
from berrybrain_api.modules.graph_inference.domain import (
    InferenceNotSavableError,
    InferenceSnapshot,
    MissingGroundedEvidenceError,
    build_insight_draft,
)
from berrybrain_api.security import get_session_user
from berrybrain_api.services import create_insight, serialize_insight

PROMPT_VERSION = "graph-inference.v2"


def persist_graph_inference(
    session: Session,
    question: str,
    result: dict[str, Any],
    *,
    owner_user_id: int | None = None,
) -> GraphInferenceRecord:
    raw_evidence = result.get("evidence")
    evidence: list[Any] = list(raw_evidence) if isinstance(raw_evidence, list) else []
    provider = str(result.get("provider") or "")
    model = str(result.get("model") or "")
    record = GraphInferenceRecord(
        owner_user_id=owner_user_id,
        access_scope="browser" if owner_user_id is not None else "service",
        question=question.strip(),
        answer=str(result.get("answer") or "").strip(),
        status=str(result.get("status") or "insufficient_evidence"),
        confidence=0.0,
        routes=_json(result.get("routes")),
        evidence=_json(evidence),
        related_nodes=_json(result.get("relatedNodes")),
        suggestions=_json(result.get("suggestions")),
        provider=provider,
        model=model,
        fallback_used=bool(result.get("fallbackUsed")),
        fallback_reason=str(result.get("fallbackReason") or "")[:40],
        prompt_version=PROMPT_VERSION,
    )
    estimate = estimate_connection_confidence(
        reason=record.answer,
        evidence=evidence,
        model_score=result.get("confidence"),
        model_source=":".join(part for part in (provider, model) if part)
        or "graph-inference",
    )
    persist_confidence(record, estimate)
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


def request_inference_owner_id(
    session: Session, request: Request, settings: Settings | None = None
) -> int | None:
    """Browser answers stay private; service-token answers have no user owner."""
    identity = get_session_user(session, settings or get_settings(), request)
    return identity[0].id if identity is not None else None


def get_owned_inference(
    session: Session, inference_id: int, owner_user_id: int | None
) -> GraphInferenceRecord:
    inference = session.get(GraphInferenceRecord, inference_id)
    expected_scope = "browser" if owner_user_id is not None else "service"
    if (
        inference is None
        or inference.owner_user_id != owner_user_id
        or inference.access_scope != expected_scope
    ):
        raise HTTPException(status_code=404, detail="Graph inference not found")
    return inference


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
        "confidence": (record.confidence if record.confidence_sample_size else None),
        "confidenceInterval": serialize_confidence(record),
        "provider": record.provider,
        "model": record.model,
        "fallbackUsed": record.fallback_used,
        "fallbackReason": record.fallback_reason,
        "promptVersion": record.prompt_version,
        "insightId": record.insight_id,
        "createdAt": record.created_at.isoformat() if record.created_at else None,
    }


def create_insight_from_persisted_inference(
    session: Session,
    inference_id: int,
    *,
    owner_user_id: int | None = None,
) -> dict[str, Any]:
    inference = get_owned_inference(session, inference_id, owner_user_id)
    if inference.confidence_updated_at is None:
        persist_confidence(
            inference,
            estimate_connection_confidence(
                reason=inference.answer,
                evidence=_list(inference.evidence),
            ),
        )
        session.flush()
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
        autocommit=False,
    )
    inference.insight_id = insight.id
    inference.updated_at = datetime.now(UTC)
    create_automation_log(
        session,
        "INSIGHT_CREATED_FROM_INFERENCE",
        "insight",
        str(insight.id),
        f'Insight created from graph question: "{inference.question}"',
        {"inferenceId": inference.id, "status": inference.status},
        {"insightId": insight.id, "type": insight.type},
        False,
        autocommit=False,
    )
    create_job(
        session,
        EXPAND_KNOWLEDGE_GRAPH,
        {
            "insight_id": insight.id,
            "idempotency_key": f"insight-graph:{insight.id}",
            "trigger": "graph_inference",
        },
        max_attempts=2,
        autocommit=False,
    )
    session.commit()
    session.refresh(insight)
    return {
        "status": "created",
        "graphUpdate": "queued",
        "insight": serialize_insight(insight),
    }


def _json(value: Any) -> str:
    return json.dumps(value if isinstance(value, list) else [], ensure_ascii=False)


def _list(value: str) -> list[Any]:
    try:
        parsed = json.loads(value or "[]")
    except (TypeError, json.JSONDecodeError):
        return []
    return parsed if isinstance(parsed, list) else []
