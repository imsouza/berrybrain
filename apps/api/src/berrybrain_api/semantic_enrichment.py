from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from berrybrain_api.ai_configuration import AIConfiguration, load_configuration
from berrybrain_api.confidence import (
    ConfidenceSignal,
    estimate_confidence,
    persist_confidence,
)
from berrybrain_api.jobs import ENRICH_GRAPH_NODE, create_job
from berrybrain_api.models import (
    GraphNodeRecord,
    GraphResearchResultRecord,
    JobRecord,
    NodeEnrichmentVersionRecord,
    SemanticProfileRecord,
)

SEMANTIC_PROMPT_VERSION = "enrich-node.v3"
ENRICHMENT_RETRY_COOLDOWN = timedelta(minutes=15)
SEMANTIC_STATES = {
    "pending",
    "processing",
    "completed",
    "failed",
    "stale",
    "needs_review",
    "not_configured",
}


class SemanticConfidence(BaseModel):
    concept_detection: float = 0.0
    semantic_interpretation: float = 0.0
    evidence_coverage: float = 0.0

    @field_validator("*")
    @classmethod
    def clamp_score(cls, value: float) -> float:
        return max(0.0, min(1.0, value))


class SemanticAnalysis(BaseModel):
    meaning_in_context: str
    use_in_notes: str
    why_it_matters_here: str
    supported_findings: list[str] = Field(default_factory=list)
    inferences: list[str] = Field(default_factory=list)
    uncertainties: list[str] = Field(default_factory=list)
    evidence: list[dict[str, Any] | str] = Field(default_factory=list)
    connection_assessments: list[dict[str, Any]] = Field(default_factory=list)
    confidence: SemanticConfidence
    provider: str
    model: str
    prompt_version: str = SEMANTIC_PROMPT_VERSION
    source_fingerprint: str

    @field_validator(
        "meaning_in_context",
        "use_in_notes",
        "why_it_matters_here",
        "provider",
        "model",
        "source_fingerprint",
    )
    @classmethod
    def require_content(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Semantic analysis contains an empty required field")
        return value.strip()

    @field_validator("evidence")
    @classmethod
    def require_evidence(
        cls, value: list[dict[str, Any] | str]
    ) -> list[dict[str, Any] | str]:
        if not value:
            raise ValueError("Semantic analysis requires evidence")
        return value


def source_fingerprint(session: Session, node: GraphNodeRecord) -> str:
    configuration = load_configuration(session)
    external_evidence_hashes = list(
        session.scalars(
            select(GraphResearchResultRecord.source_hash)
            .where(
                GraphResearchResultRecord.node_id == node.id,
                GraphResearchResultRecord.status == "suggested",
            )
            .order_by(GraphResearchResultRecord.source_hash.asc())
        )
    )
    payload = {
        "nodeId": node.id,
        "label": node.label,
        "type": node.type,
        "summary": node.summary,
        "sourceNoteIds": node.source_note_ids,
        "sourceAttachmentIds": node.source_attachment_ids,
        "sourceEvidence": node.source_evidence,
        "metadata": node.graph_metadata,
        "externalEvidenceHashes": external_evidence_hashes,
        "promptVersion": SEMANTIC_PROMPT_VERSION,
        "configurationFingerprint": (
            configuration.configuration_fingerprint if configuration else ""
        ),
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def queue_node_enrichment(
    session: Session,
    node: GraphNodeRecord,
    *,
    force: bool = False,
    configuration: AIConfiguration | None = None,
) -> tuple[object, bool]:
    configuration = configuration or load_configuration(session)
    if configuration is None or not configuration.validated_at:
        node.semantic_state = "not_configured"
        session.commit()
        raise HTTPException(status_code=409, detail="AI configuration is not valid")
    fingerprint = source_fingerprint(session, node)
    existing = session.execute(
        select(SemanticProfileRecord)
        .where(
            SemanticProfileRecord.node_id == node.id,
            SemanticProfileRecord.source_fingerprint == fingerprint,
            SemanticProfileRecord.status == "completed",
        )
        .order_by(SemanticProfileRecord.id.desc())
    ).scalar_one_or_none()
    if existing is not None and not force:
        return existing, False
    node.semantic_state = "pending"
    idempotency_key = (
        f"node-enrichment:{node.id}:{fingerprint}:{SEMANTIC_PROMPT_VERSION}:"
        f"{configuration.configuration_fingerprint}"
    )
    latest_job = (
        session.execute(
            select(JobRecord)
            .where(
                JobRecord.idempotency_key == idempotency_key,
            )
            .order_by(JobRecord.id.desc())
        )
        .scalars()
        .first()
    )
    if latest_job is not None:
        if latest_job.status in {"pending", "running"}:
            return latest_job, False
        finished_at = (
            latest_job.completed_at or latest_job.started_at or latest_job.created_at
        )
        if finished_at.tzinfo is None:
            finished_at = finished_at.replace(tzinfo=UTC)
        if (
            not force
            and latest_job.status == "dead_letter"
            and datetime.now(UTC) - finished_at < ENRICHMENT_RETRY_COOLDOWN
        ):
            return latest_job, False
    job = create_job(
        session,
        ENRICH_GRAPH_NODE,
        {
            "node_id": node.id,
            "source_fingerprint": fingerprint,
            "prompt_version": SEMANTIC_PROMPT_VERSION,
            "configuration_fingerprint": configuration.configuration_fingerprint,
            "force": force,
            "idempotency_key": idempotency_key,
        },
        max_attempts=2,
    )
    return job, True


def persist_semantic_analysis(
    session: Session,
    node: GraphNodeRecord,
    analysis: SemanticAnalysis,
) -> SemanticProfileRecord:
    expected = source_fingerprint(session, node)
    if analysis.source_fingerprint != expected:
        raise HTTPException(
            status_code=409,
            detail="Node evidence changed while semantic analysis was running",
        )
    latest_version = session.scalar(
        select(func.max(NodeEnrichmentVersionRecord.version)).where(
            NodeEnrichmentVersionRecord.node_id == node.id
        )
    )
    version = int(latest_version or 0) + 1
    analysis_json = analysis.model_dump_json()
    confidence = (
        analysis.confidence.concept_detection
        + analysis.confidence.semantic_interpretation
        + analysis.confidence.evidence_coverage
    ) / 3
    confidence_estimate = estimate_confidence(
        [
            ConfidenceSignal(
                analysis.confidence.concept_detection, "semantic:concept-detection"
            ),
            ConfidenceSignal(
                analysis.confidence.semantic_interpretation, "semantic:interpretation"
            ),
            ConfidenceSignal(
                analysis.confidence.evidence_coverage, "semantic:evidence-coverage"
            ),
        ]
    )
    history = NodeEnrichmentVersionRecord(
        node_id=node.id,
        version=version,
        source_fingerprint=analysis.source_fingerprint,
        analysis_json=analysis_json,
        evidence_json=json.dumps(analysis.evidence, ensure_ascii=False),
        confidence=confidence,
        provider=analysis.provider,
        model=analysis.model,
        prompt_version=analysis.prompt_version,
    )
    profile = SemanticProfileRecord(
        node_id=node.id,
        source_fingerprint=analysis.source_fingerprint,
        profile_json=analysis_json,
        status="completed",
        provider=analysis.provider,
        model=analysis.model,
        prompt_version=analysis.prompt_version,
    )
    session.add_all([history, profile])
    node.ai_summary = analysis.meaning_in_context
    persist_confidence(node, confidence_estimate)
    node.ai_context = analysis.why_it_matters_here
    node.source_evidence = json.dumps(analysis.evidence, ensure_ascii=False)
    node.semantic_state = "completed"
    node.semantic_profile_version = version
    node.provider = analysis.provider
    node.model = analysis.model
    node.prompt_version = analysis.prompt_version
    node.generated_at = datetime.now(UTC)
    node.updated_at = datetime.now(UTC)
    session.commit()
    session.refresh(profile)
    return profile


def semantic_analysis_payload(session: Session, node_id: int) -> dict[str, Any]:
    node = session.get(GraphNodeRecord, node_id)
    if node is None:
        raise HTTPException(status_code=404, detail="Node not found")
    profile = (
        session.execute(
            select(SemanticProfileRecord)
            .where(SemanticProfileRecord.node_id == node_id)
            .order_by(SemanticProfileRecord.id.desc())
        )
        .scalars()
        .first()
    )
    history_count = session.scalar(
        select(func.count(NodeEnrichmentVersionRecord.id)).where(
            NodeEnrichmentVersionRecord.node_id == node_id
        )
    )
    analysis: dict[str, Any] | None = None
    if profile is not None:
        try:
            parsed = json.loads(profile.profile_json)
            analysis = parsed if isinstance(parsed, dict) else None
        except json.JSONDecodeError:
            analysis = None
    return {
        "nodeId": node.id,
        "state": node.semantic_state,
        "analysis": analysis,
        "historyCount": int(history_count or 0),
        "profileVersion": node.semantic_profile_version,
        "sourceFingerprint": profile.source_fingerprint if profile else "",
    }


def mark_stale_legacy_profiles(session: Session, limit: int = 100) -> int:
    nodes = list(
        session.execute(
            select(GraphNodeRecord)
            .where(GraphNodeRecord.semantic_state == "completed")
            .order_by(GraphNodeRecord.id.asc())
            .limit(max(1, min(limit, 1000)))
        ).scalars()
    )
    changed = 0
    for node in nodes:
        profile = (
            session.execute(
                select(SemanticProfileRecord)
                .where(SemanticProfileRecord.node_id == node.id)
                .order_by(SemanticProfileRecord.id.desc())
            )
            .scalars()
            .first()
        )
        if profile is None or profile.prompt_version != SEMANTIC_PROMPT_VERSION:
            node.semantic_state = "stale"
            changed += 1
    session.commit()
    return changed
