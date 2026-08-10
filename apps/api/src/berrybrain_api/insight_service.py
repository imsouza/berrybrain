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
    InsightRecord,
)

VALID_CONNECTION_TYPES = {
    "backlink",
    "semantic_similarity",
    "shared_concept",
    "semantic",
    "prerequisite",
    "related",
    "duplicate",
    "contrast",
    "example",
    "application",
}

VALID_INSIGHT_TYPES = {
    "knowledge_gap",
    "weak_note",
    "isolated_concept",
    "duplicate_content",
    "study_path",
    "review_opportunity",
}

VALID_REVIEW_RESULTS = {"correct", "wrong", "hard"}


def _parse_json_list(value: str) -> list[Any]:
    try:
        parsed = json.loads(value)
        return parsed if isinstance(parsed, list) else []
    except Exception:
        return []


def _invalidate_cache(session: Session, key: str) -> None:
    """Compatibility hook for services that can add cache invalidation later."""
    _ = (session, key)


def create_insight(
    session: Session,
    insight_type: str,
    title: str,
    description: str = "",
    related_notes: list[int] | None = None,
    priority: int = 0,
    why_it_matters: str = "",
    evidence: list[str] | None = None,
    suggested_action: str = "",
    graph_impact: str = "",
    confidence: float = 0.5,
    status: str = "suggested",
    provider: str = "",
    model: str = "",
    prompt_version: str = "v1",
    reasoning: str = "",
    source_context: str = "",
    autocommit: bool = True,
) -> InsightRecord:
    related = related_notes or []
    source_evidence = evidence or []
    diagnostic_types = {
        "system_diagnostic",
        "pipeline_bottleneck",
        "provider_issue",
        "job_backlog",
        "worker_status",
    }
    if insight_type not in diagnostic_types:
        missing = []
        if not source_evidence:
            missing.append("evidence")
        if not why_it_matters.strip():
            missing.append("why_it_matters")
        if not suggested_action.strip():
            missing.append("suggested_action")
        if not graph_impact.strip():
            missing.append("graph_impact")
        if missing:
            raise HTTPException(
                status_code=422,
                detail="Knowledge insight is incomplete: " + ", ".join(missing),
            )
    fingerprint = insight_fingerprint(
        insight_type,
        title,
        related,
        source_evidence,
    )
    existing = session.execute(
        select(InsightRecord).where(
            InsightRecord.fingerprint == fingerprint,
            InsightRecord.status.not_in(("dismissed", "expired")),
        )
    ).scalar_one_or_none()
    quality_score = score_insight_quality(
        title=title,
        description=description,
        why_it_matters=why_it_matters,
        evidence=source_evidence,
        suggested_action=suggested_action,
        graph_impact=graph_impact,
        confidence=confidence,
    )
    adjusted_priority = max(0, priority - (2 if quality_score < 0.5 else 0))
    adjusted_confidence = min(confidence, max(0.2, quality_score + 0.15))
    now = datetime.now(UTC)
    if existing is not None:
        existing.title = title
        existing.description = description
        existing.related_notes = json.dumps(related, ensure_ascii=False)
        existing.priority = max(existing.priority, adjusted_priority)
        existing.why_it_matters = why_it_matters
        existing.evidence = json.dumps(source_evidence, ensure_ascii=False)
        existing.suggested_action = suggested_action
        existing.graph_impact = graph_impact
        existing.confidence = max(existing.confidence, adjusted_confidence)
        existing.provider = provider or existing.provider
        existing.model = model or existing.model
        existing.prompt_version = prompt_version or existing.prompt_version
        existing.reasoning = reasoning or existing.reasoning
        existing.source_context = source_context or existing.source_context
        existing.quality_score = max(existing.quality_score, quality_score)
        existing.last_recalculated_at = now
        existing.expires_at = now + timedelta(days=30)
        existing.updated_at = now
        if autocommit:
            session.commit()
            session.refresh(existing)
        else:
            session.flush()
        return existing

    insight = InsightRecord(
        type=insight_type,
        title=title,
        description=description,
        related_notes=json.dumps(related, ensure_ascii=False),
        priority=adjusted_priority,
        why_it_matters=why_it_matters,
        evidence=json.dumps(source_evidence, ensure_ascii=False),
        suggested_action=suggested_action,
        graph_impact=graph_impact,
        confidence=adjusted_confidence,
        status=status,
        provider=provider,
        model=model,
        prompt_version=prompt_version,
        reasoning=reasoning,
        source_context=source_context,
        fingerprint=fingerprint,
        quality_score=quality_score,
        expires_at=now + timedelta(days=30),
        last_recalculated_at=now,
    )
    session.add(insight)
    session.flush()

    from berrybrain_api.job_contracts import judge_artifact_payload
    from berrybrain_api.jobs import enqueue_job

    if autocommit:
        enqueue_job(
            session,
            "JUDGE_ARTIFACT",
            judge_artifact_payload(
                session,
                "insight",
                insight.id,
                str(insight.updated_at.timestamp()),
            ),
            priority=20,
        )

    if autocommit:
        session.commit()
        session.refresh(insight)
    else:
        session.flush()

    _invalidate_cache(session, "insight_metrics")
    return insight


def insight_fingerprint(
    insight_type: str,
    title: str,
    related_notes: list[int],
    evidence: list[Any],
) -> str:
    normalized_evidence = sorted(
        {
            json.dumps(item, ensure_ascii=False, sort_keys=True).strip().lower()
            for item in evidence
            if str(item).strip()
        }
    )
    title_tokens = sorted(
        {
            token
            for token in re.findall(r"[\w-]+", title.lower(), flags=re.UNICODE)
            if len(token) > 2
        }
    )
    payload = {
        "type": insight_type.strip().lower(),
        "notes": sorted(set(related_notes)),
        "evidence": normalized_evidence,
        "title": [] if normalized_evidence else title_tokens,
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()


def score_insight_quality(
    *,
    title: str,
    description: str,
    why_it_matters: str,
    evidence: list[Any],
    suggested_action: str,
    graph_impact: str,
    confidence: float,
) -> float:
    score = 0.0
    score += 0.15 if len(title.strip()) >= 12 else 0.03
    score += 0.15 if len(description.strip()) >= 50 else 0.04
    score += 0.15 if len(why_it_matters.strip()) >= 30 else 0.0
    score += 0.20 if len(evidence) >= 2 else (0.10 if evidence else 0.0)
    score += 0.10 if len(suggested_action.strip()) >= 15 else 0.0
    score += 0.10 if len(graph_impact.strip()) >= 15 else 0.0
    score += 0.15 * max(0.0, min(1.0, confidence))
    generic = {
        "connection found",
        "new insight",
        "interesting concept",
        "knowledge gap",
        "related notes",
    }
    if title.strip().lower() in generic:
        score -= 0.40
    return round(max(0.0, min(1.0, score)), 4)


def migrate_legacy_insights(session: Session) -> dict[str, int]:
    """Archive unsupported legacy insights and backfill metadata on grounded ones."""
    now = datetime.now(UTC)
    archived = 0
    upgraded = 0
    for insight in session.execute(select(InsightRecord)).scalars():
        if insight.status in {"archived", "dismissed", "expired"}:
            continue
        evidence = _parse_json_list(insight.evidence)
        related_notes = [
            int(value)
            for value in _parse_json_list(insight.related_notes)
            if str(value).isdigit()
        ]
        has_cognitive_fields = all(
            str(value or "").strip()
            for value in (
                insight.description,
                insight.why_it_matters,
                insight.suggested_action,
                insight.graph_impact,
            )
        )
        if (
            not evidence
            or not related_notes
            or not has_cognitive_fields
            or not _is_visible_insight(insight)
        ):
            insight.status = "archived"
            insight.dismissed_at = insight.dismissed_at or now
            insight.updated_at = now
            archived += 1
            continue
        fingerprint = insight_fingerprint(
            insight.type,
            insight.title,
            related_notes,
            evidence,
        )
        quality = score_insight_quality(
            title=insight.title,
            description=insight.description,
            why_it_matters=insight.why_it_matters,
            evidence=evidence,
            suggested_action=insight.suggested_action,
            graph_impact=insight.graph_impact,
            confidence=insight.confidence,
        )
        changed = False
        if not insight.fingerprint:
            insight.fingerprint = fingerprint
            changed = True
        if not insight.quality_score:
            insight.quality_score = quality
            changed = True
        if insight.expires_at is None and insight.status in {"suggested", "reviewed"}:
            insight.expires_at = now + timedelta(days=30)
            changed = True
        if changed:
            insight.last_recalculated_at = now
            insight.updated_at = now
            upgraded += 1
    if archived or upgraded:
        session.commit()
    return {"archived": archived, "upgraded": upgraded}


def get_active_insights(
    session: Session,
    limit: int = 20,
) -> list[InsightRecord]:
    migrate_legacy_insights(session)
    now = datetime.now(UTC)
    expired = list(
        session.execute(
            select(InsightRecord).where(
                InsightRecord.expires_at.is_not(None),
                InsightRecord.expires_at <= now,
                InsightRecord.status.in_(("suggested", "reviewed")),
            )
        ).scalars()
    )
    for insight in expired:
        insight.status = "expired"
        insight.updated_at = now
    if expired:
        session.commit()
    insights = list(
        session.execute(
            select(InsightRecord)
            .where(InsightRecord.dismissed_at.is_(None))
            .where(
                InsightRecord.status.not_in(
                    ("expired", "archived", "dismissed", "ignored")
                )
            )
            .order_by(
                InsightRecord.feedback_score.desc(),
                InsightRecord.quality_score.desc(),
                InsightRecord.priority.desc(),
                InsightRecord.created_at.desc(),
            )
            .limit(limit * 3)
        ).scalars()
    )
    return [insight for insight in insights if _is_visible_insight(insight)][:limit]


def _is_visible_insight(insight: InsightRecord) -> bool:
    title = insight.title or ""
    description = getattr(insight, "description", "") or ""
    provider = (getattr(insight, "provider", "") or "").lower()
    model = (getattr(insight, "model", "") or "").lower()
    insight_type = (getattr(insight, "type", "") or "").lower()
    if insight_type in {
        "system_diagnostic",
        "pipeline_bottleneck",
        "provider_issue",
        "job_backlog",
        "worker_status",
    }:
        return False
    evidence = _parse_json_list(getattr(insight, "evidence", "[]"))
    combined = " ".join(
        [
            title,
            description,
            getattr(insight, "why_it_matters", "") or "",
            getattr(insight, "suggested_action", "") or "",
            getattr(insight, "graph_impact", "") or "",
            " ".join(str(item) for item in evidence),
        ]
    ).lower()
    if any(
        term in combined
        for term in (
            "explainedconnections",
            "graphnotes",
            "jobsbytype",
            "generate_note_title",
            "enrich_graph_node",
            "semanticstate",
            "raw json",
            "pipeline bottleneck",
            "jobrecord",
            "pendingjobs",
            "activejobs",
            "failedjobs",
        )
    ):
        return False
    legacy_prefixes = (
        "Nó central no grafo:",
        "No central no grafo:",
        "Conceito recorrente:",
        "Lacuna detectada:",
    )
    if title.startswith(legacy_prefixes) and provider in {
        "",
        "system",
        "deterministic",
    }:
        return False
    if model == "graph-insight.v1" and provider in {"", "system", "deterministic"}:
        return False
    has_cognitive_fields = all(
        [
            (getattr(insight, "why_it_matters", "") or "").strip(),
            (getattr(insight, "suggested_action", "") or "").strip(),
            (getattr(insight, "graph_impact", "") or "").strip(),
        ]
    )
    if provider in {"nvidia-nim", "cloud", "ai"}:
        if len(evidence) < 2 or not has_cognitive_fields:
            return False
        if title.strip() == description.strip():
            return False
    return True


def dismiss_insight(session: Session, insight_id: int) -> InsightRecord:
    insight = session.get(InsightRecord, insight_id)
    if insight is None:
        raise HTTPException(status_code=404, detail="Insight not found")
    insight.dismissed_at = datetime.now(UTC)
    insight.ignored_at = datetime.now(UTC)
    insight.status = "dismissed"
    insight.feedback_score -= 1
    insight.updated_at = datetime.now(UTC)
    session.commit()
    session.refresh(insight)
    return insight


def serialize_insight(insight: InsightRecord) -> dict[str, Any]:
    try:
        related = json.loads(insight.related_notes)
    except json.JSONDecodeError:
        related = []
    return {
        "id": insight.id,
        "type": insight.type,
        "title": insight.title,
        "description": insight.description,
        "relatedNotes": related,
        "priority": insight.priority,
        "whyItMatters": getattr(insight, "why_it_matters", ""),
        "evidence": _parse_json_list(getattr(insight, "evidence", "[]")),
        "suggestedAction": getattr(insight, "suggested_action", ""),
        "graphImpact": getattr(insight, "graph_impact", ""),
        "confidence": getattr(insight, "confidence", 0.5),
        "status": getattr(insight, "status", "suggested"),
        "provider": getattr(insight, "provider", ""),
        "model": getattr(insight, "model", ""),
        "promptVersion": getattr(insight, "prompt_version", "v1"),
        "reasoning": getattr(insight, "reasoning", ""),
        "sourceContext": getattr(insight, "source_context", ""),
        "fingerprint": getattr(insight, "fingerprint", ""),
        "qualityScore": getattr(insight, "quality_score", 0.0),
        "feedbackScore": getattr(insight, "feedback_score", 0),
        "expiresAt": insight.expires_at.isoformat()
        if getattr(insight, "expires_at", None)
        else None,
        "lastRecalculatedAt": insight.last_recalculated_at.isoformat()
        if getattr(insight, "last_recalculated_at", None)
        else None,
        "appliedAt": insight.applied_at.isoformat() if insight.applied_at else None,
        "ignoredAt": insight.ignored_at.isoformat() if insight.ignored_at else None,
        "createdAt": insight.created_at.isoformat() if insight.created_at else None,
        "updatedAt": insight.updated_at.isoformat()
        if getattr(insight, "updated_at", None)
        else None,
        "dismissedAt": insight.dismissed_at.isoformat()
        if insight.dismissed_at
        else None,
    }
