from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from berrybrain_api.models import (
    ChunkRecord,
    InsightRecord,
    NoteRecord,
    ReviewItemRecord,
)


SCHEDULER_VERSION = "sm2.berrybrain.v1"
REVIEW_TYPES = {
    "explain",
    "compare",
    "apply",
    "predict",
    "identify_gap",
    "retrieval_question",
    "cloze",
    "connection_review",
    "insight_review",
}
REVIEW_RATINGS = {"forgot", "hard", "good", "easy"}
LOW_RETENTION_INSIGHT_TYPES = {
    "system_diagnostic",
    "pipeline_bottleneck",
    "provider_issue",
    "job_backlog",
    "worker_status",
}
GROUNDING_STOPWORDS = {
    "a",
    "an",
    "and",
    "as",
    "at",
    "by",
    "de",
    "do",
    "da",
    "e",
    "em",
    "for",
    "from",
    "in",
    "is",
    "of",
    "on",
    "or",
    "para",
    "the",
    "to",
    "um",
    "uma",
    "with",
}


def _load_json(raw: str, fallback: Any) -> Any:
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return fallback


def _normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def _meaningful_tokens(value: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[\wÀ-ÿ-]+", _normalize(value))
        if len(token) >= 3 and token not in GROUNDING_STOPWORDS
    }


def _expected_point_is_supported(point: str, source_text: str) -> bool:
    normalized_point = _normalize(point)
    normalized_source = _normalize(source_text)
    if normalized_point and normalized_point in normalized_source:
        return True
    tokens = _meaningful_tokens(point)
    if not tokens:
        return False
    overlap = tokens & _meaningful_tokens(source_text)
    required = 1 if len(tokens) == 1 else max(2, round(len(tokens) * 0.6))
    return len(overlap) >= required


def review_fingerprint(
    source_insight_id: int, review_type: str, prompt: str, source_note_ids: list[int]
) -> str:
    canonical = json.dumps(
        {
            "insight": source_insight_id,
            "type": review_type,
            "prompt": _normalize(prompt),
            "notes": sorted(set(source_note_ids)),
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode()).hexdigest()


def create_review_item(
    session: Session,
    *,
    source_insight_id: int,
    review_type: str,
    prompt: str,
    expected_points: list[str],
    evidence: list[Any],
) -> ReviewItemRecord:
    insight = session.get(InsightRecord, source_insight_id)
    if insight is None:
        raise HTTPException(status_code=404, detail="Insight not found")
    if insight.type in LOW_RETENTION_INSIGHT_TYPES:
        raise HTTPException(
            status_code=422, detail="System diagnostics cannot become reviews"
        )
    if insight.confidence < 0.55 or not insight.why_it_matters.strip():
        raise HTTPException(
            status_code=422, detail="Insight has insufficient retention value"
        )
    if review_type not in REVIEW_TYPES:
        raise HTTPException(status_code=422, detail="Unsupported review type")
    if not prompt.strip() or not expected_points:
        raise HTTPException(
            status_code=422, detail="Review prompt and expected points are required"
        )

    insight_evidence = _load_json(insight.evidence, [])
    if not isinstance(insight_evidence, list) or not insight_evidence:
        raise HTTPException(status_code=422, detail="Insight has no source evidence")
    evidence_keys = {
        json.dumps(item, sort_keys=True, ensure_ascii=False)
        for item in insight_evidence
    }
    selected_evidence = evidence or insight_evidence
    if any(
        json.dumps(item, sort_keys=True, ensure_ascii=False) not in evidence_keys
        for item in selected_evidence
    ):
        raise HTTPException(
            status_code=422,
            detail="Review evidence must come from the source insight",
        )

    source_note_ids = [
        int(value)
        for value in _load_json(insight.related_notes, [])
        if str(value).isdigit()
    ]
    source_chunk_ids = sorted(
        {
            int(value)
            for item in selected_evidence
            if isinstance(item, dict)
            for value in (item.get("sourceChunkId"), item.get("targetChunkId"))
            if value is not None and str(value).isdigit()
        }
    )
    notes = list(
        session.execute(
            select(NoteRecord).where(NoteRecord.id.in_(source_note_ids))
        ).scalars()
    )
    content_hashes = {str(note.id): note.content_hash for note in notes}
    chunks = (
        list(
            session.execute(
                select(ChunkRecord).where(ChunkRecord.id.in_(source_chunk_ids))
            ).scalars()
        )
        if source_chunk_ids
        else []
    )
    current_chunks = [
        chunk
        for chunk in chunks
        if chunk.note_id in source_note_ids
        and content_hashes.get(str(chunk.note_id)) == chunk.content_hash
    ]
    if source_chunk_ids and len(current_chunks) != len(source_chunk_ids):
        raise HTTPException(
            status_code=422,
            detail="Review evidence references missing or stale source chunks",
        )
    evidence_text = " ".join(
        json.dumps(item, ensure_ascii=False, sort_keys=True)
        for item in selected_evidence
    )
    source_text = " ".join(
        [evidence_text]
        + [chunk.text for chunk in current_chunks]
        + [note.content for note in notes]
    )
    unsupported_points = [
        point
        for point in expected_points
        if not _expected_point_is_supported(point, source_text)
    ]
    if unsupported_points:
        raise HTTPException(
            status_code=422,
            detail="Review expected points are not supported by source evidence",
        )
    fingerprint = review_fingerprint(insight.id, review_type, prompt, source_note_ids)
    existing = session.execute(
        select(ReviewItemRecord).where(ReviewItemRecord.fingerprint == fingerprint)
    ).scalar_one_or_none()
    if existing is None:
        existing = ReviewItemRecord(
            source_insight_id=insight.id,
            fingerprint=fingerprint,
            review_type=review_type,
            prompt=prompt.strip(),
        )
        session.add(existing)
    existing.source_note_ids = json.dumps(source_note_ids)
    existing.source_chunk_ids = json.dumps(source_chunk_ids)
    existing.source_content_hashes = json.dumps(content_hashes, sort_keys=True)
    existing.expected_points = json.dumps(expected_points, ensure_ascii=False)
    existing.evidence = json.dumps(selected_evidence, ensure_ascii=False)
    existing.status = "active"
    existing.due_at = datetime.now(UTC)
    existing.updated_at = datetime.now(UTC)
    insight.status = "converted_to_review"
    insight.updated_at = datetime.now(UTC)
    session.commit()
    session.refresh(existing)
    return existing


def grade_review_item(
    session: Session,
    review_id: int,
    rating: str,
    perceived_difficulty: int | None = None,
) -> ReviewItemRecord:
    item = session.get(ReviewItemRecord, review_id)
    if item is None or item.status == "deleted":
        raise HTTPException(status_code=404, detail="Review item not found")
    if item.status == "paused":
        raise HTTPException(
            status_code=409, detail="Paused review items cannot be graded"
        )
    if rating not in REVIEW_RATINGS:
        raise HTTPException(status_code=422, detail="Unsupported review rating")
    if perceived_difficulty is not None and not 1 <= perceived_difficulty <= 5:
        raise HTTPException(
            status_code=422, detail="Perceived difficulty must be 1 to 5"
        )

    quality = {"forgot": 1, "hard": 3, "good": 4, "easy": 5}[rating]
    ease = max(
        1.3,
        item.ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)),
    )
    if rating == "forgot":
        repetitions = 0
        interval = 1
    elif rating == "hard":
        repetitions = item.repetitions + 1
        interval = max(1, round(item.interval_days * 1.2))
    elif item.repetitions == 0:
        repetitions = 1
        interval = 4 if rating == "easy" else 1
    elif item.repetitions == 1:
        repetitions = 2
        interval = 7 if rating == "easy" else 6
    else:
        repetitions = item.repetitions + 1
        multiplier = ease * (1.3 if rating == "easy" else 1.0)
        interval = max(item.interval_days + 1, round(item.interval_days * multiplier))

    item.ease_factor = round(ease, 4)
    item.repetitions = repetitions
    item.interval_days = interval
    item.stability = round(max(1.0, interval * item.ease_factor), 3)
    item.last_performance = rating
    if perceived_difficulty is not None:
        item.perceived_difficulty = perceived_difficulty
    item.due_at = datetime.now(UTC) + timedelta(days=interval)
    item.status = "active"
    item.scheduler_version = SCHEDULER_VERSION
    item.updated_at = datetime.now(UTC)
    session.commit()
    session.refresh(item)
    return item


def set_review_status(
    session: Session, review_id: int, status: str
) -> ReviewItemRecord:
    if status not in {"active", "paused", "deleted"}:
        raise HTTPException(status_code=422, detail="Unsupported review status")
    item = session.get(ReviewItemRecord, review_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Review item not found")
    item.status = status
    due_at = item.due_at
    if due_at and due_at.tzinfo is None:
        due_at = due_at.replace(tzinfo=UTC)
    if status == "active" and due_at and due_at < datetime.now(UTC):
        item.due_at = datetime.now(UTC)
    item.updated_at = datetime.now(UTC)
    session.commit()
    session.refresh(item)
    return item


def mark_reviews_stale_for_note(
    session: Session, note_id: int, current_content_hash: str
) -> int:
    items = list(
        session.execute(
            select(ReviewItemRecord).where(
                ReviewItemRecord.status.not_in(("deleted", "stale"))
            )
        ).scalars()
    )
    stale = 0
    for item in items:
        hashes = _load_json(item.source_content_hashes, {})
        if str(note_id) not in hashes or hashes[str(note_id)] == current_content_hash:
            continue
        item.status = "stale"
        item.updated_at = datetime.now(UTC)
        stale += 1
    return stale


def serialize_review(item: ReviewItemRecord) -> dict[str, Any]:
    return {
        "id": item.id,
        "sourceInsightId": item.source_insight_id,
        "sourceNoteIds": _load_json(item.source_note_ids, []),
        "sourceChunkIds": _load_json(item.source_chunk_ids, []),
        "reviewType": item.review_type,
        "prompt": item.prompt,
        "expectedPoints": _load_json(item.expected_points, []),
        "evidence": _load_json(item.evidence, []),
        "perceivedDifficulty": item.perceived_difficulty,
        "lastPerformance": item.last_performance,
        "status": item.status,
        "dueAt": item.due_at.isoformat() if item.due_at else None,
        "intervalDays": item.interval_days,
        "stability": item.stability,
        "schedulerVersion": item.scheduler_version,
        "createdAt": item.created_at.isoformat() if item.created_at else None,
        "updatedAt": item.updated_at.isoformat() if item.updated_at else None,
    }
