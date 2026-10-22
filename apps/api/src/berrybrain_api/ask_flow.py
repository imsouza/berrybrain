from __future__ import annotations

import json
import re
import unicodedata
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from berrybrain_api.ai_configuration import load_configuration
from berrybrain_api.ask_references import (
    append_verified_reference_links,
    capture_ask_references,
    resolve_ask_references,
)
from berrybrain_api.cognitive_layer import answer_cognitive_query
from berrybrain_api.config import get_settings
from berrybrain_api.graph_inference_service import (
    create_insight_from_persisted_inference,
    get_owned_inference,
    persist_graph_inference,
)
from berrybrain_api.models import AskSessionRecord, AskTurnRecord


def create_ask_session(
    session: Session,
    *,
    mode: str = "flow",
    title: str = "",
    inference_id: int | None = None,
    owner_user_id: int | None = None,
) -> AskSessionRecord:
    configuration = load_configuration(session)
    if configuration is None or not configuration.validated_at:
        raise HTTPException(status_code=409, detail="AI configuration is not valid")
    item = AskSessionRecord(
        id=uuid4().hex,
        owner_user_id=owner_user_id,
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
    processing_turn = session.execute(
        select(AskTurnRecord.id)
        .where(
            AskTurnRecord.session_id == session_id,
            AskTurnRecord.role == "user",
            AskTurnRecord.status == "processing",
        )
        .limit(1)
    ).scalar_one_or_none()
    if processing_turn is not None:
        raise HTTPException(status_code=409, detail="A Flow turn is already processing")
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
    try:
        session.commit()
    except IntegrityError as error:
        session.rollback()
        if "ask_turns.session_id" in str(error.orig):
            raise HTTPException(
                status_code=409, detail="A Flow turn is already processing"
            ) from error
        raise
    context = _build_context(session, ask_session)
    started = datetime.now(UTC)
    reused_references: list[dict[str, Any]] = []
    try:
        if _asks_for_previous_links(question):
            reused_references = _previous_reference_specs(
                session, session_id, next_sequence
            )
        if reused_references:
            live_references = resolve_ask_references(session, reused_references)
            linked_sources = []
            for index, reference in enumerate(live_references, start=1):
                marker = f"resolved:{reference['kind']}:{reference['id']}"
                label = re.sub(
                    r"([\\\[\]])",
                    r"\\\1",
                    " ".join(str(reference["title"]).split()),
                )
                linked_sources.append(f"{index}. [{label}](bbref:{marker})")
            result = {
                "status": "answered",
                "answer": "Referências verificadas da conversa:\n\n"
                + "\n".join(linked_sources),
                "evidence": [],
                "provider": "berrybrain",
                "model": "reference-resolver",
            }
        else:
            result = await answer_cognitive_query(
                session,
                question,
                conversation_context=context,
            )
    except Exception:
        if _finish_processing_turn(session, user_turn.id, "failed"):
            session.commit()
        else:
            session.rollback()
        raise
    if result.get("status") == "waiting_provider":
        if not _finish_processing_turn(session, user_turn.id, "failed"):
            session.rollback()
            _raise_interrupted_turn(session, user_turn)
        session.commit()
        raise HTTPException(
            status_code=503,
            detail={
                "code": "provider_unavailable",
                "message": "The configured AI provider did not return an answer.",
            },
        )
    if not _finish_processing_turn(session, user_turn.id, "completed"):
        session.rollback()
        _raise_interrupted_turn(session, user_turn)
    answer = str(result.get("answer") or "").strip()
    if not answer:
        answer = "There is not enough evidence in BerryBrain to answer this turn."
    evidence_ids = _evidence_ids(result.get("evidence"))
    references = reused_references or capture_ask_references(
        session, result.get("evidence")
    )
    answer = append_verified_reference_links(
        answer, resolve_ask_references(session, references)
    )
    assistant_turn = AskTurnRecord(
        session_id=session_id,
        sequence=next_sequence + 1,
        role="assistant",
        content=answer,
        context_summary=ask_session.context_summary,
        evidence_ids=json.dumps(evidence_ids, separators=(",", ":")),
        references_json=json.dumps(references, separators=(",", ":")),
        provider=str(result.get("provider") or ""),
        model=str(result.get("model") or ""),
        fallback_used=bool(result.get("fallbackUsed")),
        fallback_reason=str(result.get("fallbackReason") or "")[:40],
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


def _finish_processing_turn(session: Session, turn_id: int, status: str) -> bool:
    """Claim a turn's final state atomically against cancellation or failure."""
    result = session.execute(
        update(AskTurnRecord)
        .where(AskTurnRecord.id == turn_id, AskTurnRecord.status == "processing")
        .values(status=status)
        .execution_options(synchronize_session=False)
    )
    return result.rowcount == 1


def _raise_interrupted_turn(session: Session, turn: AskTurnRecord) -> None:
    session.refresh(turn)
    if turn.status == "cancelled":
        raise HTTPException(status_code=409, detail="Flow turn was cancelled")
    raise HTTPException(status_code=409, detail="Flow turn is no longer processing")


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
        "turns": [serialize_ask_turn(turn, session=session) for turn in turns],
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
        owner_user_id=item.owner_user_id,
    )
    return create_insight_from_persisted_inference(
        session, inference.id, owner_user_id=item.owner_user_id
    )


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
    for turn in session.execute(
        select(AskTurnRecord).where(
            AskTurnRecord.session_id == session_id,
            AskTurnRecord.status == "processing",
        )
    ).scalars():
        turn.status = "cancelled"
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


def serialize_ask_turn(
    item: AskTurnRecord, *, session: Session | None = None
) -> dict[str, Any]:
    try:
        evidence_ids = json.loads(item.evidence_ids)
    except json.JSONDecodeError:
        evidence_ids = []
    try:
        stored_references = json.loads(item.references_json or "[]")
    except (TypeError, json.JSONDecodeError):
        stored_references = []
    return {
        "id": item.id,
        "sessionId": item.session_id,
        "sequence": item.sequence,
        "role": item.role,
        "content": item.content,
        "contextSummary": item.context_summary,
        "evidenceIds": evidence_ids,
        "references": resolve_ask_references(session, stored_references)
        if session
        else [],
        "provider": item.provider,
        "model": item.model,
        "fallbackUsed": item.fallback_used,
        "fallbackReason": item.fallback_reason,
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


def _asks_for_previous_links(question: str) -> bool:
    plain = "".join(
        char
        for char in unicodedata.normalize("NFKD", question.casefold())
        if not unicodedata.combining(char)
    )
    return len(plain) <= 220 and bool(
        re.search(
            r"\b(linkar|links? das? notas?|links? (?:to|for) (?:the )?notes?|"
            r"abrir (?:as )?notas mencionadas|link (?:the )?sources?)\b",
            plain,
        )
    )


def _previous_reference_specs(
    session: Session, session_id: str, before_sequence: int
) -> list[dict[str, Any]]:
    turns = session.scalars(
        select(AskTurnRecord)
        .where(
            AskTurnRecord.session_id == session_id,
            AskTurnRecord.role == "assistant",
            AskTurnRecord.status == "completed",
            AskTurnRecord.sequence < before_sequence,
            AskTurnRecord.references_json != "[]",
        )
        .order_by(AskTurnRecord.sequence.desc())
        .limit(100)
    )
    for turn in turns:
        try:
            stored = json.loads(turn.references_json or "[]")
        except (TypeError, json.JSONDecodeError):
            continue
        if not isinstance(stored, list):
            continue
        # Keep only live references; deleted or recycled IDs cannot be revived.
        live = {
            (ref["kind"], ref["id"]) for ref in resolve_ask_references(session, stored)
        }
        selected = []
        for ref in stored:
            if (
                not isinstance(ref, dict)
                or (ref.get("kind"), ref.get("id")) not in live
            ):
                continue
            marker = f"resolved:{ref['kind']}:{ref['id']}"
            raw_ids = ref.get("evidenceIds")
            previous_ids = (
                [value for value in raw_ids if isinstance(value, str)]
                if isinstance(raw_ids, list)
                else []
            )
            selected.append(
                {
                    **ref,
                    "evidenceIds": list(dict.fromkeys([*previous_ids, marker])),
                }
            )
        if selected:
            return selected
    return []


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
                item.get("noteId")
                or item.get("nodeId")
                or item.get("path")
                or item.get("id")
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
    inference = get_owned_inference(session, inference_id, ask_session.owner_user_id)
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
                references_json=json.dumps(
                    capture_ask_references(session, evidence), separators=(",", ":")
                ),
                provider=inference.provider,
                model=inference.model,
                fallback_used=inference.fallback_used,
                fallback_reason=inference.fallback_reason,
                status="completed",
            ),
        ]
    )
