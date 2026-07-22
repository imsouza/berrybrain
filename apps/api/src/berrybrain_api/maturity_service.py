from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from berrybrain_api.models import (
    GraphEdgeRecord,
    GraphInferenceRecord,
    GraphNodeRecord,
    InsightRecord,
)

DIAGNOSTIC_TYPES = {
    "system_diagnostic",
    "pipeline_bottleneck",
    "provider_issue",
    "job_backlog",
    "worker_status",
}
TECHNICAL_MARKERS = (
    "jobsbytype",
    "generate_note_title",
    "graphnotes",
    "explainedconnections",
    "pipeline bottleneck",
    "raw json",
)
ACTIVE_STATUSES = {"suggested", "confirmed", "accepted", "applied", "reviewed"}


def cognitive_maturity_report(
    session: Session,
    *,
    now: datetime | None = None,
    minimum_reviewed_insights: int = 20,
) -> dict[str, Any]:
    reference = now or datetime.now(UTC)
    nodes = list(
        session.execute(
            select(GraphNodeRecord).where(GraphNodeRecord.status.in_(ACTIVE_STATUSES))
        ).scalars()
    )
    edges = list(
        session.execute(
            select(GraphEdgeRecord).where(GraphEdgeRecord.status.in_(ACTIVE_STATUSES))
        ).scalars()
    )
    insights = list(
        session.execute(
            select(InsightRecord).where(InsightRecord.status.in_(ACTIVE_STATUSES))
        ).scalars()
    )
    inferences = list(session.execute(select(GraphInferenceRecord)).scalars())

    generated_nodes = [node for node in nodes if node.type != "note"]
    knowledge_insights = [
        insight for insight in insights if insight.type not in DIAGNOSTIC_TYPES
    ]
    diagnostics = [insight for insight in insights if _is_diagnostic(insight)]
    grounded_inferences = [
        inference
        for inference in inferences
        if inference.status in {"answered", "success", "sufficient_evidence"}
    ]

    node_provenance = _coverage(generated_nodes, _node_has_provenance)
    edge_provenance = _coverage(edges, _edge_has_provenance)
    insight_grounding = _coverage(knowledge_insights, _insight_is_grounded)
    inference_grounding = _coverage(grounded_inferences, _inference_is_grounded)
    unresolved_count = _unresolved_artifact_count(session)
    archived_stale_count = _archived_stale_artifact_count(session)
    outcomes = insight_outcome_metrics(
        session,
        now=reference,
        minimum_reviewed=minimum_reviewed_insights,
    )

    structural_ready = (
        node_provenance == 1.0
        and edge_provenance == 1.0
        and insight_grounding == 1.0
        and inference_grounding == 1.0
        and not diagnostics
        and unresolved_count == 0
    )
    blockers: list[str] = []
    if node_provenance < 1.0:
        blockers.append("Generated graph nodes are missing complete provenance.")
    if edge_provenance < 1.0:
        blockers.append(
            "Active graph edges are missing reason, evidence, or provenance."
        )
    if insight_grounding < 1.0:
        blockers.append("Knowledge Insights are missing evidence or a learning action.")
    if inference_grounding < 1.0:
        blockers.append(
            "Grounded graph inferences are missing model or evidence provenance."
        )
    if diagnostics:
        blockers.append("System diagnostics are still present in Knowledge Insights.")
    if unresolved_count:
        blockers.append(f"{unresolved_count} errored knowledge artifacts remain.")
    if not outcomes["meetsTarget"]:
        blockers.extend(outcomes["blockers"])

    return {
        "status": "mature"
        if structural_ready and outcomes["meetsTarget"]
        else "measuring",
        "eligibleFor100Percent": structural_ready and outcomes["meetsTarget"],
        "structuralReady": structural_ready,
        "metrics": {
            "nodeProvenanceCoverage": node_provenance,
            "edgeProvenanceCoverage": edge_provenance,
            "insightGroundingCoverage": insight_grounding,
            "inferenceGroundingCoverage": inference_grounding,
            "diagnosticLeakageRate": _ratio(len(diagnostics), len(insights)),
            "unresolvedArtifactCount": unresolved_count,
            "archivedStaleArtifactCount": archived_stale_count,
        },
        "insightOutcomes": outcomes,
        "sample": {
            "activeNodes": len(nodes),
            "activeEdges": len(edges),
            "activeKnowledgeInsights": len(knowledge_insights),
            "persistedInferences": len(inferences),
        },
        "blockers": list(dict.fromkeys(blockers)),
        "measuredAt": reference.isoformat(),
    }


def insight_outcome_metrics(
    session: Session,
    *,
    now: datetime | None = None,
    window_days: int = 30,
    minimum_reviewed: int = 20,
) -> dict[str, Any]:
    reference = now or datetime.now(UTC)
    start = reference - timedelta(days=window_days)
    candidates = list(
        session.execute(
            select(InsightRecord).where(InsightRecord.created_at >= start)
        ).scalars()
    )
    reviewed = [insight for insight in candidates if _has_outcome(insight)]
    useful = [insight for insight in reviewed if _is_useful_outcome(insight)]
    usefulness_rate = _ratio(len(useful), len(reviewed)) if reviewed else 0.0
    observation_days = 0
    if candidates:
        earliest = min(_as_utc(insight.created_at) for insight in candidates)
        observation_days = min(window_days, max(0, (reference - earliest).days))

    blockers: list[str] = []
    if len(reviewed) < minimum_reviewed:
        blockers.append(
            f"Review at least {minimum_reviewed} insights; {len(reviewed)} have outcomes."
        )
    if observation_days < window_days:
        blockers.append(
            f"Collect {window_days} days of insight outcomes; {observation_days} days observed."
        )
    if reviewed and usefulness_rate < 0.70:
        blockers.append(
            f"Insight usefulness is {usefulness_rate:.0%}; the maturity gate is 70%."
        )

    meets_target = (
        len(reviewed) >= minimum_reviewed
        and observation_days >= window_days
        and usefulness_rate >= 0.70
    )
    return {
        "windowDays": window_days,
        "observationDays": observation_days,
        "minimumReviewed": minimum_reviewed,
        "reviewed": len(reviewed),
        "usefulOrApplied": len(useful),
        "usefulnessRate": round(usefulness_rate, 4),
        "meetsTarget": meets_target,
        "blockers": blockers,
    }


def _node_has_provenance(node: GraphNodeRecord) -> bool:
    return bool(
        node.source
        and _json_list(node.source_note_ids)
        and _json_list(node.source_evidence)
        and node.provider
        and node.model
        and node.prompt_version
    )


def _edge_has_provenance(edge: GraphEdgeRecord) -> bool:
    return bool(
        edge.reason.strip()
        and _json_list(edge.evidence)
        and edge.created_by
        and edge.provider
        and edge.model
        and edge.prompt_version
        and 0.0 <= edge.confidence <= 1.0
    )


def _insight_is_grounded(insight: InsightRecord) -> bool:
    return bool(
        len(_json_list(insight.evidence)) >= 2
        and insight.why_it_matters.strip()
        and insight.suggested_action.strip()
        and insight.graph_impact.strip()
        and insight.provider
        and insight.model
        and insight.prompt_version
    )


def _inference_is_grounded(inference: GraphInferenceRecord) -> bool:
    return bool(
        _json_list(inference.evidence)
        and inference.provider
        and inference.model
        and inference.prompt_version
    )


def _is_diagnostic(insight: InsightRecord) -> bool:
    text = " ".join(
        (insight.type, insight.title, insight.description, insight.reasoning)
    ).lower()
    return insight.type in DIAGNOSTIC_TYPES or any(
        marker in text for marker in TECHNICAL_MARKERS
    )


def _has_outcome(insight: InsightRecord) -> bool:
    return bool(
        insight.applied_at
        or insight.ignored_at
        or insight.dismissed_at
        or insight.status in {"accepted", "applied", "ignored", "dismissed"}
        or insight.feedback_score != 0
    )


def _is_useful_outcome(insight: InsightRecord) -> bool:
    return bool(
        insight.applied_at
        or insight.status in {"accepted", "applied"}
        or insight.feedback_score > 0
    )


def _unresolved_artifact_count(session: Session) -> int:
    return sum(
        len(
            list(
                session.execute(select(model).where(model.status == "error")).scalars()
            )
        )
        for model in (GraphNodeRecord, GraphEdgeRecord)
    )


def _archived_stale_artifact_count(session: Session) -> int:
    return sum(
        len(
            list(
                session.execute(select(model).where(model.status == "stale")).scalars()
            )
        )
        for model in (GraphNodeRecord, GraphEdgeRecord)
    )


def _coverage(items: list[Any], predicate) -> float:
    return round(_ratio(sum(1 for item in items if predicate(item)), len(items)), 4)


def _ratio(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 0.0


def _json_list(raw: str) -> list[Any]:
    try:
        value = json.loads(raw or "[]")
    except (TypeError, json.JSONDecodeError):
        return []
    return value if isinstance(value, list) else []


def _as_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)
