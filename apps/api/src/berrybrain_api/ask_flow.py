from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from berrybrain_api.ai_configuration import load_configuration
from berrybrain_api.cognitive_layer import answer_cognitive_query
from berrybrain_api.config import get_settings
from berrybrain_api.graph_inference_service import (
    create_insight_from_persisted_inference,
    persist_graph_inference,
)
from berrybrain_api.models import AskSessionRecord, AskTurnRecord, GraphInferenceRecord


def create_ask_session(
    session: Session,
    *,
    mode: str = "flow",
    title: str = "",
    inference_id: int | None = None,
) -> AskSessionRecord:
    configuration = load_configuration(session)
    if configuration is None or not configuration.validated_at:
        raise HTTPException(status_code=409, detail="AI configuration is not valid")
    item = AskSessionRecord(
        id=uuid4().hex,
        mode=mode,
        title=title.strip()[:255],
        active=True,
        configuration_fingerprint=configuration.configuration_fingerprint,
    )
    session.add(item)
    session.flush()
    if inference_id is not None:
        _seed_from_inference(session, item, inference_id)
    session.commit()
    session.refresh(item)
    return item


async def append_ask_turn(
    session: Session,
    session_id: str,
    content: str,
) -> tuple[AskTurnRecord, AskTurnRecord]:
    ask_session = _get_active_session(session, session_id)
    question = content.strip()
    if not question:
        raise HTTPException(status_code=422, detail="Question is required")
    configuration = load_configuration(session)
    if (
        configuration is None
        or configuration.configuration_fingerprint
        != ask_session.configuration_fingerprint
    ):
        raise HTTPException(
            status_code=409,
            detail="AI configuration changed; start a new Flow session",
        )
    processing_duplicate = session.execute(
        select(AskTurnRecord).where(
            AskTurnRecord.session_id == session_id,
            AskTurnRecord.role == "user",
            AskTurnRecord.content == question,
            AskTurnRecord.status == "processing",
        )
    ).scalar_one_or_none()
    if processing_duplicate is not None:
        raise HTTPException(status_code=409, detail="Duplicate turn is processing")
    next_sequence = (
        int(
            session.scalar(
                select(func.max(AskTurnRecord.sequence)).where(
                    AskTurnRecord.session_id == session_id
                )
            )
            or 0
        )
        + 1
    )
    user_turn = AskTurnRecord(
        session_id=session_id,
        sequence=next_sequence,
        role="user",
        content=question,
        status="processing",
    )
    session.add(user_turn)
    if not ask_session.title:
        ask_session.title = question[:120]
    ask_session.updated_at = datetime.now(UTC)
    session.commit()
    context = _build_context(session, ask_session)
    started = datetime.now(UTC)
    try:
        result = await answer_cognitive_query(
            session,
            (
                "Use BerryBrain's knowledge graph as queryable data when the "
                "turn asks about nodes, node types, connections, graph areas, "
                "or clusters. Inspect graph entities and relationships before "
                "falling back to note text search.\n\n"
                f"Flow conversation context:\n{context}\n\nCurrent question:\n{question}"
            ),
        )
    except Exception:
        user_turn.status = "failed"
        session.commit()
        raise
    session.refresh(user_turn)
    if user_turn.status == "cancelled":
        raise HTTPException(status_code=409, detail="Flow turn was cancelled")
    user_turn.status = "completed"
    answer = str(result.get("answer") or "").strip()
    if not answer:
        answer = "There is not enough evidence in BerryBrain to answer this turn."
    evidence_ids = _evidence_ids(result.get("evidence"))
    assistant_turn = AskTurnRecord(
        session_id=session_id,
        sequence=next_sequence + 1,
        role="assistant",
        content=answer,
        context_summary=ask_session.context_summary,
        evidence_ids=json.dumps(evidence_ids, separators=(",", ":")),
        provider=str(result.get("provider") or ""),
        model=str(result.get("model") or ""),
        token_usage=max(1, (len(question) + len(answer)) // 4),
        latency_ms=max(0, int((datetime.now(UTC) - started).total_seconds() * 1000)),
        status="completed",
    )
    session.add(assistant_turn)
    _refresh_summary(session, ask_session)
    ask_session.updated_at = datetime.now(UTC)
    session.commit()
    session.refresh(user_turn)
    session.refresh(assistant_turn)
    return user_turn, assistant_turn


def get_ask_session_payload(session: Session, session_id: str) -> dict[str, Any]:
    item = session.get(AskSessionRecord, session_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Flow session not found")
    turns = list(
        session.execute(
            select(AskTurnRecord)
            .where(AskTurnRecord.session_id == session_id)
            .order_by(AskTurnRecord.sequence.asc())
        ).scalars()
    )
    return {
        "session": serialize_ask_session(item),
        "turns": [serialize_ask_turn(turn) for turn in turns],
    }


def create_insight_from_flow_session(
    session: Session, session_id: str
) -> dict[str, Any]:
    item = session.get(AskSessionRecord, session_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Flow session not found")
    assistant_turn = session.execute(
        select(AskTurnRecord)
        .where(
            AskTurnRecord.session_id == session_id,
            AskTurnRecord.role == "assistant",
            AskTurnRecord.status == "completed",
        )
        .order_by(AskTurnRecord.sequence.desc())
        .limit(1)
    ).scalar_one_or_none()
    if assistant_turn is None:
        raise HTTPException(status_code=409, detail="Flow has no completed answer")
    user_turn = session.execute(
        select(AskTurnRecord)
        .where(
            AskTurnRecord.session_id == session_id,
            AskTurnRecord.role == "user",
            AskTurnRecord.sequence < assistant_turn.sequence,
        )
        .order_by(AskTurnRecord.sequence.desc())
        .limit(1)
    ).scalar_one_or_none()
    evidence = [
        {
            "nodeId": value,
            "source": "flow",
            "reference": f"ask_turn:{assistant_turn.id}",
        }
        for value in _evidence_ids_from_json(assistant_turn.evidence_ids)
    ]
    inference = persist_graph_inference(
        session,
        user_turn.content if user_turn is not None else item.title or "Flow insight",
        {
            "answer": assistant_turn.content,
            "status": "answered" if evidence else "insufficient_evidence",
            "routes": ["flow", "knowledge_graph"],
            "evidence": evidence,
            "relatedNodes": evidence,
            "provider": assistant_turn.provider,
            "model": assistant_turn.model,
        },
    )
    return create_insight_from_persisted_inference(session, inference.id)


def cancel_ask_session(session: Session, session_id: str) -> AskSessionRecord:
    item = _get_active_session(session, session_id)
    for turn in session.execute(
        select(AskTurnRecord).where(
            AskTurnRecord.session_id == session_id,
            AskTurnRecord.status == "processing",
        )
    ).scalars():
        turn.status = "cancelled"
    item.updated_at = datetime.now(UTC)
    session.commit()
    session.refresh(item)
    return item


def close_ask_session(session: Session, session_id: str) -> AskSessionRecord:
    item = session.get(AskSessionRecord, session_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Flow session not found")
    item.active = False
    item.updated_at = datetime.now(UTC)
    session.commit()
    session.refresh(item)
    return item


def serialize_ask_session(item: AskSessionRecord) -> dict[str, Any]:
    return {
        "id": item.id,
        "mode": item.mode,
        "title": item.title,
        "active": item.active,
        "configurationFingerprint": item.configuration_fingerprint,
        "contextSummary": item.context_summary,
        "createdAt": item.created_at.isoformat(),
        "updatedAt": item.updated_at.isoformat(),
    }


def serialize_ask_turn(item: AskTurnRecord) -> dict[str, Any]:
    try:
        evidence_ids = json.loads(item.evidence_ids)
    except json.JSONDecodeError:
        evidence_ids = []
    return {
        "id": item.id,
        "sessionId": item.session_id,
        "sequence": item.sequence,
        "role": item.role,
        "content": item.content,
        "contextSummary": item.context_summary,
        "evidenceIds": evidence_ids,
        "provider": item.provider,
        "model": item.model,
        "tokenUsage": item.token_usage,
        "latencyMs": item.latency_ms,
        "status": item.status,
        "createdAt": item.created_at.isoformat(),
    }


def _get_active_session(session: Session, session_id: str) -> AskSessionRecord:
    item = session.get(AskSessionRecord, session_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Flow session not found")
    if not item.active:
        raise HTTPException(status_code=409, detail="Flow session is closed")
    return item


def _build_context(session: Session, item: AskSessionRecord) -> str:
    settings = get_settings()
    turns = list(
        session.execute(
            select(AskTurnRecord)
            .where(
                AskTurnRecord.session_id == item.id,
                AskTurnRecord.status.in_(["completed", "processing"]),
            )
            .order_by(AskTurnRecord.sequence.desc())
            .limit(max(2, settings.flow_recent_turns))
        ).scalars()
    )
    turns.reverse()
    lines = []
    if item.context_summary:
        lines.append(f"Earlier summary: {item.context_summary}")
    lines.extend(f"{turn.role}: {turn.content}" for turn in turns)
    context = "\n".join(lines)
    max_chars = max(1024, settings.flow_context_token_budget * 4)
    return context[-max_chars:]


def _refresh_summary(session: Session, item: AskSessionRecord) -> None:
    settings = get_settings()
    old_turns = list(
        session.execute(
            select(AskTurnRecord)
            .where(
                AskTurnRecord.session_id == item.id,
                AskTurnRecord.status == "completed",
            )
            .order_by(AskTurnRecord.sequence.asc())
        ).scalars()
    )
    if len(old_turns) <= settings.flow_recent_turns:
        return
    summarized = old_turns[: -settings.flow_recent_turns]
    fragments = [
        f"{turn.role}: {' '.join(turn.content.split())[:280]}" for turn in summarized
    ]
    item.context_summary = "\n".join(fragments)[-4000:]


def _evidence_ids(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    result: list[str] = []
    for item in value:
        if isinstance(item, dict):
            identity = (
                item.get("id")
                or item.get("noteId")
                or item.get("nodeId")
                or item.get("path")
            )
            if identity is not None:
                result.append(str(identity))
    return list(dict.fromkeys(result))


def _evidence_ids_from_json(raw: str) -> list[str]:
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        parsed = []
    return [str(item) for item in parsed if str(item).strip()]


def _seed_from_inference(
    session: Session,
    ask_session: AskSessionRecord,
    inference_id: int,
) -> None:
    inference = session.get(GraphInferenceRecord, inference_id)
    if inference is None:
        raise HTTPException(status_code=404, detail="Graph inference not found")
    try:
        evidence = json.loads(inference.evidence or "[]")
    except (TypeError, ValueError):
        evidence = []
    ask_session.title = ask_session.title or inference.question[:120]
    session.add_all(
        [
            AskTurnRecord(
                session_id=ask_session.id,
                sequence=1,
                role="user",
                content=inference.question,
                status="completed",
            ),
            AskTurnRecord(
                session_id=ask_session.id,
                sequence=2,
                role="assistant",
                content=inference.answer,
                evidence_ids=json.dumps(_evidence_ids(evidence), separators=(",", ":")),
                provider=inference.provider,
                model=inference.model,
                status="completed",
            ),
        ]
    )
