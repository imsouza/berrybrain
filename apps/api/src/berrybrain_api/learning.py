from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from berrybrain_api.models import GraphFeedbackRecord, LearningEventRecord

NEGATIVE_ACTIONS = frozenset(
    {"deleted", "ignored", "rejected", "dismissed", "downvoted"}
)
POSITIVE_ACTIONS = frozenset(
    {"accepted", "confirmed", "corrected", "restored", "upvoted"}
)
ANNOTATION_ACTIONS = frozenset({"annotated", "evidence_added"})


def learning_context_key(source_note_ids: list[int]) -> str:
    normalized = sorted({int(value) for value in source_note_ids if int(value) > 0})
    payload = json.dumps(normalized, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def record_learning_event(
    session: Session,
    *,
    event_type: str,
    target_type: str,
    target_key: str,
    action: str,
    source_note_ids: list[int] | None = None,
    before_state: dict[str, Any] | None = None,
    after_state: dict[str, Any] | None = None,
    actor_type: str = "user",
    origin: str = "api",
    signal: float | None = None,
) -> LearningEventRecord:
    normalized_ids = sorted(
        {int(value) for value in (source_note_ids or []) if int(value) > 0}
    )
    resolved_signal = _action_signal(action) if signal is None else float(signal)
    if not -1.0 <= resolved_signal <= 1.0:
        raise ValueError("Learning signal must be between -1 and 1")
    event = LearningEventRecord(
        event_type=str(event_type).strip()[:120],
        target_type=str(target_type).strip()[:80],
        target_key=str(target_key).strip()[:512],
        action=str(action).strip()[:80],
        signal=resolved_signal,
        context_key=learning_context_key(normalized_ids),
        source_note_ids=_json_dump(normalized_ids),
        before_state=_json_dump(before_state or {}),
        after_state=_json_dump(after_state or {}),
        actor_type=str(actor_type).strip()[:40] or "user",
        origin=str(origin).strip()[:80] or "api",
        created_at=datetime.now(UTC),
    )
    session.add(event)
    session.flush()
    return event


def build_learning_guidance(
    session: Session,
    *,
    source_note_ids: list[int] | None = None,
    target_type: str | None = None,
    limit: int = 24,
) -> dict[str, Any]:
    normalized_ids = sorted(
        {int(value) for value in (source_note_ids or []) if int(value) > 0}
    )
    context_keys = {
        learning_context_key([]),
        learning_context_key(normalized_ids),
    }
    if not callable(getattr(session, "execute", None)):
        return _guidance_response(normalized_ids)
    candidate_limit = max(100, min(limit * 20, 1000))
    feedback_candidates = list(
        session.execute(
            select(GraphFeedbackRecord)
            .where(
                GraphFeedbackRecord.active.is_(True),
            )
            .order_by(
                GraphFeedbackRecord.updated_at.desc(), GraphFeedbackRecord.id.desc()
            )
            .limit(candidate_limit)
        ).scalars()
    )
    feedback = [
        item
        for item in feedback_candidates
        if _matches_context(
            item.context_key,
            item.source_note_ids,
            normalized_ids,
            context_keys,
        )
    ][: max(1, min(limit, 100))]
    event_query = select(LearningEventRecord)
    if target_type:
        event_query = event_query.where(
            or_(
                LearningEventRecord.target_type == target_type,
                LearningEventRecord.target_type == "system",
            )
        )
    event_candidates = list(
        session.execute(
            event_query.order_by(
                LearningEventRecord.created_at.desc(), LearningEventRecord.id.desc()
            ).limit(candidate_limit)
        ).scalars()
    )
    events: list[LearningEventRecord] = []
    seen_targets: set[tuple[str, str, str]] = set()
    for event in event_candidates:
        if not _matches_context(
            event.context_key,
            event.source_note_ids,
            normalized_ids,
            context_keys,
        ):
            continue
        latest_key = (event.actor_type, event.target_type, event.target_key)
        if latest_key in seen_targets:
            continue
        seen_targets.add(latest_key)
        events.append(event)
        if len(events) >= max(1, min(limit, 100)):
            break
    negative_patterns: list[dict[str, Any]] = []
    positive_patterns: list[dict[str, Any]] = []
    corrections: list[dict[str, Any]] = []
    annotations: list[dict[str, Any]] = []
    represented_feedback = {(item.artifact_key, item.action) for item in feedback}
    for item in feedback:
        payload = {
            "artifactKind": item.artifact_kind,
            "artifactKey": item.artifact_key,
            "action": item.action,
            "sourceNoteIds": _json_list(item.source_note_ids),
        }
        replacement = _json_object(item.replacement_payload)
        if replacement:
            payload["replacement"] = replacement
            corrections.append(payload)
        elif item.action in NEGATIVE_ACTIONS:
            negative_patterns.append(payload)
        else:
            positive_patterns.append(payload)
    for event in events:
        if (event.target_key, event.action) in represented_feedback:
            continue
        event_payload = {
            "targetType": event.target_type,
            "targetKey": event.target_key,
            "action": event.action,
            "sourceNoteIds": _json_list(event.source_note_ids),
            "before": _bounded_state(_json_object(event.before_state)),
            "after": _bounded_state(_json_object(event.after_state)),
        }
        if event.action in ANNOTATION_ACTIONS:
            annotations.append(event_payload)
        elif event.action == "corrected" and event_payload["after"]:
            event_payload["replacement"] = event_payload["after"]
            corrections.append(event_payload)
        elif event.action in NEGATIVE_ACTIONS:
            negative_patterns.append(event_payload)
        elif event.action in POSITIVE_ACTIONS:
            positive_patterns.append(event_payload)
    return _guidance_response(
        normalized_ids,
        negative_patterns=negative_patterns,
        positive_patterns=positive_patterns,
        corrections=corrections,
        annotations=annotations,
        events=events,
    )


def _guidance_response(
    source_note_ids: list[int],
    *,
    negative_patterns: list[dict[str, Any]] | None = None,
    positive_patterns: list[dict[str, Any]] | None = None,
    corrections: list[dict[str, Any]] | None = None,
    annotations: list[dict[str, Any]] | None = None,
    events: list[LearningEventRecord] | None = None,
) -> dict[str, Any]:
    return {
        "policyVersion": "feedback-policy.v1",
        "scope": "source-context" if source_note_ids else "global",
        "sourceNoteIds": source_note_ids,
        "negativePatterns": negative_patterns or [],
        "positivePatterns": positive_patterns or [],
        "corrections": corrections or [],
        "annotations": annotations or [],
        "recentSignals": [
            {
                "eventId": event.event_id,
                "eventType": event.event_type,
                "targetType": event.target_type,
                "targetKey": event.target_key,
                "action": event.action,
                "signal": event.signal,
                "before": _bounded_state(_json_object(event.before_state)),
                "after": _bounded_state(_json_object(event.after_state)),
            }
            for event in (events or [])
        ],
        "instructions": [
            "Do not recreate a negative pattern without new, explicit evidence.",
            "Prefer a recorded correction when the same source context recurs.",
            "Treat positive signals as evidence, not as permission to bypass validation.",
            "Use annotations as user-authored context, not as automatically verified facts.",
            "When signals conflict, follow the newest scoped signal shown in this policy.",
            "Judge every generated artifact against source evidence and ontology constraints.",
        ],
    }


def _action_signal(action: str) -> float:
    normalized = str(action).strip().casefold()
    if normalized in NEGATIVE_ACTIONS:
        return -1.0
    if normalized in POSITIVE_ACTIONS:
        return 1.0
    return 0.0


def _json_dump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _json_object(value: str) -> dict[str, Any]:
    try:
        parsed = json.loads(value or "{}")
    except (TypeError, json.JSONDecodeError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _json_list(value: str) -> list[Any]:
    try:
        parsed = json.loads(value or "[]")
    except (TypeError, json.JSONDecodeError):
        return []
    return parsed if isinstance(parsed, list) else []


def _matches_context(
    stored_key: str,
    raw_source_note_ids: str,
    requested_note_ids: list[int],
    exact_keys: set[str],
) -> bool:
    if stored_key == learning_context_key([]):
        return True
    if stored_key in exact_keys:
        return True
    if not requested_note_ids:
        return False
    stored_ids = {
        int(value)
        for value in _json_list(raw_source_note_ids)
        if str(value).isdigit() and int(value) > 0
    }
    return bool(stored_ids.intersection(requested_note_ids))


def _bounded_state(value: Any, *, depth: int = 0) -> Any:
    if depth >= 3:
        return "[truncated]"
    if isinstance(value, str):
        return value[:1200]
    if isinstance(value, dict):
        return {
            str(key)[:120]: _bounded_state(item, depth=depth + 1)
            for key, item in list(value.items())[:20]
        }
    if isinstance(value, list):
        return [_bounded_state(item, depth=depth + 1) for item in value[:20]]
    return value
