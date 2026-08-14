from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
    Text,
    event,
    inspect,
)
from sqlalchemy.orm import Mapped, mapped_column

from berrybrain_api.database import Base


def utc_now() -> datetime:
    return datetime.now(UTC)


def new_stable_id() -> str:
    return str(uuid4())


def new_graph_node_iri() -> str:
    return f"urn:berrybrain:graph-node:{new_stable_id()}"


def new_graph_edge_iri() -> str:
    return f"urn:berrybrain:graph-edge:{new_stable_id()}"


class NoteRecord(Base):
    __tablename__ = "notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    stable_id: Mapped[str] = mapped_column(
        String(36), unique=True, nullable=False, default=new_stable_id, index=True
    )
    source_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False)
    path: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    content_hash: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    frontmatter: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    links: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="new")
    language: Mapped[str] = mapped_column(String(20), nullable=False, default="und")
    note_type: Mapped[str] = mapped_column(String(50), nullable=False, default="note")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    last_processed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class NoteAttachmentRecord(Base):
    __tablename__ = "note_attachments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    note_id: Mapped[int] = mapped_column(
        ForeignKey("notes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    note_path: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_path: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(160), nullable=False, default="")
    declared_mime_type: Mapped[str] = mapped_column(
        String(160), nullable=False, default=""
    )
    checksum: Mapped[str] = mapped_column(
        String(64), nullable=False, default="", index=True
    )
    validation_status: Mapped[str] = mapped_column(
        String(40), nullable=False, default="validated"
    )
    category: Mapped[str] = mapped_column(String(40), nullable=False, default="other")
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class AttachmentExtractionRecord(Base):
    __tablename__ = "attachment_extractions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    attachment_id: Mapped[int] = mapped_column(
        ForeignKey("note_attachments.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    extracted_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    language: Mapped[str] = mapped_column(String(20), nullable=False, default="")
    provider: Mapped[str] = mapped_column(
        String(80), nullable=False, default="deterministic"
    )
    model: Mapped[str] = mapped_column(
        String(160), nullable=False, default="attachment-text.v1"
    )
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    error: Mapped[str] = mapped_column(Text, nullable=False, default="")
    stage: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    progress: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    extractor: Mapped[str] = mapped_column(
        String(80), nullable=False, default="attachment-text.v1"
    )
    location_metadata: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class JobRecord(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    type: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    payload: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    payload_schema_version: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1
    )
    note_id: Mapped[int] = mapped_column(Integer, nullable=False, default=0, index=True)
    note_path: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    content_hash: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    pipeline_run_id: Mapped[str] = mapped_column(
        String(128), nullable=False, default=""
    )
    idempotency_key: Mapped[str] = mapped_column(
        String(700), nullable=False, default=""
    )
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    claimed_by: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    claim_token: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    lease_expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class JobAttemptRecord(Base):
    __tablename__ = "job_attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    job_id: Mapped[int] = mapped_column(
        ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    job_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    payload_schema_version: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1
    )
    run_id: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    dependency_ids: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    note_id: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    note_version: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    content_hash: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    artifact_id: Mapped[str] = mapped_column(String(160), nullable=False, default="")
    artifact_version: Mapped[str] = mapped_column(
        String(128), nullable=False, default=""
    )
    active_ai_mode: Mapped[str] = mapped_column(String(20), nullable=False, default="")
    resolved_provider: Mapped[str] = mapped_column(
        String(80), nullable=False, default=""
    )
    resolved_model: Mapped[str] = mapped_column(String(160), nullable=False, default="")
    stage: Mapped[str] = mapped_column(
        String(50), nullable=False, default="claimed", index=True
    )
    attempt: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    model_call_started: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    model_call_id: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    error_class: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    error_code: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    retryability: Mapped[str] = mapped_column(
        String(30), nullable=False, default="unknown"
    )
    dead_letter_reason: Mapped[str] = mapped_column(Text, nullable=False, default="")
    started_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class WorkerInboxRecord(Base):
    __tablename__ = "worker_inbox"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    message_id: Mapped[str] = mapped_column(
        String(220), unique=True, nullable=False, index=True
    )
    job_id: Mapped[int] = mapped_column(
        ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    message_type: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    claim_token: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="processed")
    received_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class WorkerStatus(Base):
    __tablename__ = "worker_status"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="running")
    last_heartbeat: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    jobs_processed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    errors: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ollama_healthy: Mapped[bool] = mapped_column(default=False)


class UserRecord(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    display_name: Mapped[str] = mapped_column(String(160), nullable=False, default="")
    password_hash: Mapped[str] = mapped_column(Text, nullable=False, default="")
    email_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    two_factor_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    locked_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    force_password_reset: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    failed_login_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class ProfileRecord(Base):
    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    slug: Mapped[str] = mapped_column(
        String(120), unique=True, nullable=False, index=True
    )
    vault_subpath: Mapped[str] = mapped_column(Text, nullable=False, default="")
    source: Mapped[str] = mapped_column(String(40), nullable=False, default="manual")
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class UserSessionRecord(Base):
    __tablename__ = "user_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    session_hash: Mapped[str] = mapped_column(
        String(128), unique=True, nullable=False, index=True
    )
    csrf_token_hash: Mapped[str] = mapped_column(
        String(128), nullable=False, default=""
    )
    ip_address: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    user_agent: Mapped[str] = mapped_column(Text, nullable=False, default="")
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class ServiceTokenRecord(Base):
    __tablename__ = "service_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False, default="worker")
    token_hash: Mapped[str] = mapped_column(
        String(128), unique=True, nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        String(40), nullable=False, default="active", index=True
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class AuthOtpRecord(Base):
    __tablename__ = "auth_otps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    purpose: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    code_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    challenge_token_hash: Mapped[str] = mapped_column(
        String(128), nullable=False, default=""
    )
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    sent_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class LoginAttemptRecord(Base):
    __tablename__ = "login_attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(
        String(255), nullable=False, default="", index=True
    )
    ip_address: Mapped[str] = mapped_column(
        String(80), nullable=False, default="", index=True
    )
    action: Mapped[str] = mapped_column(String(50), nullable=False, default="login")
    success: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    reason: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class SecurityAuditRecord(Base):
    __tablename__ = "security_audit_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    actor_user_id: Mapped[int | None] = mapped_column(
        Integer, nullable=True, index=True
    )
    actor_email: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    action: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    target_type: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    target_id: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    ip_address: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    user_agent: Mapped[str] = mapped_column(Text, nullable=False, default="")
    audit_metadata: Mapped[str] = mapped_column(
        "metadata", Text, nullable=False, default="{}"
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class TagRecord(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    color: Mapped[str] = mapped_column(String(40), nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class ConceptRecord(Base):
    __tablename__ = "concepts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_name: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False
    )
    language: Mapped[str] = mapped_column(String(20), nullable=False, default="und")
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    frequency: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    related_note_ids: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    extracted_by: Mapped[str] = mapped_column(
        String(80), nullable=False, default="system"
    )
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    confidence_lower: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence_upper: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence_sample_size: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    confidence_method: Mapped[str] = mapped_column(
        String(80), nullable=False, default="unavailable"
    )
    confidence_factors: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    confidence_updated_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="suggested")
    provider: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    model: Mapped[str] = mapped_column(String(160), nullable=False, default="")
    source_evidence: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    quality_gate_status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="pending"
    )
    quality_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    latest_evaluation_id: Mapped[int] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class AIGatewayInvocationRecord(Base):
    __tablename__ = "ai_gateway_invocations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    capability: Mapped[str] = mapped_column(String(50), nullable=False)
    provider: Mapped[str] = mapped_column(String(80), nullable=False)
    model: Mapped[str] = mapped_column(String(160), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    outcome: Mapped[str] = mapped_column(String(50), nullable=False, default="success")
    prompt_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class ArtifactEvaluationRecord(Base):
    __tablename__ = "artifact_evaluations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    artifact_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # node, edge, connection, insight
    artifact_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    verdict: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # passed, review, rejected, insufficient_evidence, error
    score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    rubric: Mapped[str] = mapped_column(
        Text, nullable=False, default="{}"
    )  # JSON containing scores per criteria
    reasoning: Mapped[str] = mapped_column(Text, nullable=False, default="")
    evidence_used: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    provider: Mapped[str] = mapped_column(String(80), nullable=False)
    model: Mapped[str] = mapped_column(String(160), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class ConnectionRecord(Base):
    __tablename__ = "connections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    source_note_id: Mapped[int] = mapped_column(
        ForeignKey("notes.id", ondelete="CASCADE"), nullable=False
    )
    target_note_id: Mapped[int] = mapped_column(
        ForeignKey("notes.id", ondelete="CASCADE"), nullable=False
    )
    connection_type: Mapped[str] = mapped_column(String(80), nullable=False)
    confidence: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    confidence_lower: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence_upper: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence_sample_size: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    confidence_method: Mapped[str] = mapped_column(
        String(80), nullable=False, default="unavailable"
    )
    confidence_factors: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    confidence_updated_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False, default="")
    evidence: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    ai_notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    user_notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_by: Mapped[str] = mapped_column(
        String(80), nullable=False, default="system"
    )
    provider: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    model: Mapped[str] = mapped_column(String(160), nullable=False, default="")
    prompt_version: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="suggested")
    quality_gate_status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="pending"
    )
    quality_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    latest_evaluation_id: Mapped[int] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class InsightRecord(Base):
    __tablename__ = "insights"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    type: Mapped[str] = mapped_column(String(80), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    related_notes: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    why_it_matters: Mapped[str] = mapped_column(Text, nullable=False, default="")
    evidence: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    suggested_action: Mapped[str] = mapped_column(Text, nullable=False, default="")
    graph_impact: Mapped[str] = mapped_column(Text, nullable=False, default="")
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    confidence_lower: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence_upper: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence_sample_size: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    confidence_method: Mapped[str] = mapped_column(
        String(80), nullable=False, default="unavailable"
    )
    confidence_factors: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    confidence_updated_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="suggested")
    provider: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    model: Mapped[str] = mapped_column(String(160), nullable=False, default="")
    prompt_version: Mapped[str] = mapped_column(
        String(80), nullable=False, default="v1"
    )
    reasoning: Mapped[str] = mapped_column(Text, nullable=False, default="")
    source_context: Mapped[str] = mapped_column(Text, nullable=False, default="")
    fingerprint: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    quality_gate_status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="pending"
    )
    quality_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    latest_evaluation_id: Mapped[int] = mapped_column(Integer, nullable=True)
    feedback_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_recalculated_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
    applied_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    ignored_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    dismissed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class GraphInferenceRecord(Base):
    __tablename__ = "graph_inferences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="insufficient_evidence", index=True
    )
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    confidence_lower: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence_upper: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence_sample_size: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    confidence_method: Mapped[str] = mapped_column(
        String(80), nullable=False, default="unavailable"
    )
    confidence_factors: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    confidence_updated_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
    routes: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    evidence: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    related_nodes: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    suggestions: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    provider: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    model: Mapped[str] = mapped_column(String(160), nullable=False, default="")
    prompt_version: Mapped[str] = mapped_column(
        String(80), nullable=False, default="graph-inference.v2"
    )
    insight_id: Mapped[int | None] = mapped_column(
        ForeignKey("insights.id", ondelete="SET NULL"), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class LegacyRecallItemRecord(Base):
    __tablename__ = "review_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    source_insight_id: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    source_note_ids: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    source_chunk_ids: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    source_content_hashes: Mapped[str] = mapped_column(
        Text, nullable=False, default="{}"
    )
    item_type: Mapped[str] = mapped_column("review_type", String(50), nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    expected_points: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    evidence: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    perceived_difficulty: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    last_performance: Mapped[str] = mapped_column(
        String(20), nullable=False, default=""
    )
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="active")
    due_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    interval_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ease_factor: Mapped[float] = mapped_column(Float, nullable=False, default=2.5)
    repetitions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    stability: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    scheduler_version: Mapped[str] = mapped_column(
        String(50), nullable=False, default="sm2.berrybrain.v1"
    )
    fingerprint: Mapped[str] = mapped_column(
        String(128), unique=True, nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class AutomationLogRecord(Base):
    __tablename__ = "automation_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    action_type: Mapped[str] = mapped_column(String(80), nullable=False)
    target_type: Mapped[str] = mapped_column(String(80), nullable=False)
    target_id: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    before_state: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    after_state: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    reversible: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reverted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    reverted_by_log_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class SettingRecord(Base):
    __tablename__ = "settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    key: Mapped[str] = mapped_column(String(160), unique=True, nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False, default="")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class GeneratedMetadataRecord(Base):
    __tablename__ = "generated_metadata"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    note_id: Mapped[int] = mapped_column(
        ForeignKey("notes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    generation_type: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    content_hash: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    model_used: Mapped[str | None] = mapped_column(String(80), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class EmbeddingRecord(Base):
    __tablename__ = "embeddings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    note_id: Mapped[int] = mapped_column(
        ForeignKey("notes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    content_hash: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False, default=-1)
    vector: Mapped[str] = mapped_column(Text, nullable=False)
    vector_blob: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    model: Mapped[str] = mapped_column(String(80), nullable=False)
    provider: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    vector_dimensions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class ModelInvocationRecord(Base):
    __tablename__ = "model_invocations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    capability: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    model: Mapped[str] = mapped_column(String(160), nullable=False, default="")
    prompt_version: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    status: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    remote: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    input_units: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    output_units: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    estimated_cost_usd: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0
    )
    error_class: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    error_message: Mapped[str] = mapped_column(Text, nullable=False, default="")
    correlation_id: Mapped[str] = mapped_column(
        String(128), nullable=False, default="", index=True
    )
    started_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class ChunkRecord(Base):
    __tablename__ = "chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    note_id: Mapped[int] = mapped_column(
        ForeignKey("notes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    note_version: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    content_hash: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    heading_path: Mapped[str] = mapped_column(Text, nullable=False, default="")
    text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    token_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    start_line: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    end_line: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    embedding_id: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class GraphNodeRecord(Base):
    __tablename__ = "graph_nodes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    stable_id: Mapped[str] = mapped_column(
        String(36), unique=True, nullable=False, default=new_stable_id, index=True
    )
    iri: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, default=new_graph_node_iri
    )
    artifact_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    ai_notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    user_notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    source: Mapped[str] = mapped_column(String(80), nullable=False, default="system")
    source_id: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    source_note_ids: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    source_attachment_ids: Mapped[str] = mapped_column(
        Text, nullable=False, default="[]"
    )
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    confidence_lower: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence_upper: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence_sample_size: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    confidence_method: Mapped[str] = mapped_column(
        String(80), nullable=False, default="unavailable"
    )
    confidence_factors: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    confidence_updated_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
    created_by: Mapped[str] = mapped_column(
        String(80), nullable=False, default="system"
    )
    created_by_model: Mapped[str] = mapped_column(
        String(160), nullable=False, default=""
    )
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="suggested")
    source_evidence: Mapped[str] = mapped_column(Text, nullable=False, default="")
    ai_context: Mapped[str] = mapped_column(Text, nullable=False, default="")
    ai_summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    learning_value: Mapped[str] = mapped_column(String(20), nullable=False, default="")
    source_quality: Mapped[str] = mapped_column(String(20), nullable=False, default="")
    validation_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="unvalidated"
    )
    quality_gate_status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="pending"
    )
    quality_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    latest_evaluation_id: Mapped[int] = mapped_column(Integer, nullable=True)
    provider: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    model: Mapped[str] = mapped_column(String(160), nullable=False, default="")
    prompt_version: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    semantic_state: Mapped[str] = mapped_column(
        String(30), nullable=False, default="pending", index=True
    )
    semantic_profile_version: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    cluster_id: Mapped[int | None] = mapped_column(
        ForeignKey("semantic_clusters.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    vault_id: Mapped[str] = mapped_column(
        String(160), nullable=False, default="default", index=True
    )
    color_id: Mapped[str] = mapped_column(String(80), nullable=False, default="pending")
    color_confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    color_reason: Mapped[str] = mapped_column(Text, nullable=False, default="")
    color_updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    semantic_status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="active", index=True
    )
    ontology_class: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    canonical_label: Mapped[str] = mapped_column(
        String(255), nullable=False, default=""
    )
    aliases_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    generated_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    graph_metadata: Mapped[str] = mapped_column(
        "metadata", Text, nullable=False, default="{}"
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class GraphEdgeRecord(Base):
    __tablename__ = "graph_edges"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    stable_id: Mapped[str] = mapped_column(
        String(36), unique=True, nullable=False, default=new_stable_id, index=True
    )
    iri: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, default=new_graph_edge_iri
    )
    artifact_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    source_node_id: Mapped[int] = mapped_column(
        ForeignKey("graph_nodes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    target_node_id: Mapped[int] = mapped_column(
        ForeignKey("graph_nodes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    confidence_lower: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence_upper: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence_sample_size: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    confidence_method: Mapped[str] = mapped_column(
        String(80), nullable=False, default="unavailable"
    )
    confidence_factors: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    confidence_updated_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False, default="")
    evidence: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    ai_notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    user_notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    source_note_ids: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    created_by: Mapped[str] = mapped_column(String(80), nullable=False, default="ai")
    created_by_model: Mapped[str] = mapped_column(
        String(160), nullable=False, default=""
    )
    provider: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    model: Mapped[str] = mapped_column(String(160), nullable=False, default="")
    prompt_version: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="suggested")
    quality_gate_status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="pending"
    )
    quality_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    latest_evaluation_id: Mapped[int] = mapped_column(Integer, nullable=True)
    semantic_status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="active", index=True
    )
    ontology_property: Mapped[str] = mapped_column(
        String(120), nullable=False, default=""
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class GraphFeedbackRecord(Base):
    __tablename__ = "graph_feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    artifact_kind: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    artifact_key: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    context_key: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    source_note_ids: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    original_payload: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    replacement_payload: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class LearningEventRecord(Base):
    __tablename__ = "learning_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    event_id: Mapped[str] = mapped_column(
        String(36), unique=True, nullable=False, default=new_stable_id, index=True
    )
    event_type: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    target_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    target_key: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    signal: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    context_key: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    source_note_ids: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    before_state: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    after_state: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    actor_type: Mapped[str] = mapped_column(
        String(40), nullable=False, default="user", index=True
    )
    origin: Mapped[str] = mapped_column(String(80), nullable=False, default="api")
    consumed_by: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, index=True)


@event.listens_for(NoteRecord, "before_insert")
def _initialize_note_identity(_mapper, _connection, note: NoteRecord) -> None:
    note.stable_id = note.stable_id or new_stable_id()
    note.source_version = max(1, int(note.source_version or 1))


@event.listens_for(NoteRecord, "before_update")
def _advance_note_source_version(_mapper, _connection, note: NoteRecord) -> None:
    if inspect(note).attrs.content_hash.history.has_changes():
        note.source_version = max(1, int(note.source_version or 1)) + 1


def _initialize_graph_identity(artifact, kind: str) -> None:
    artifact.stable_id = artifact.stable_id or new_stable_id()
    artifact.iri = artifact.iri or f"urn:berrybrain:{kind}:{artifact.stable_id}"
    artifact.artifact_version = max(1, int(artifact.artifact_version or 1))


@event.listens_for(GraphNodeRecord, "before_insert")
def _initialize_graph_node_identity(
    _mapper, _connection, node: GraphNodeRecord
) -> None:
    _initialize_graph_identity(node, "graph-node")


@event.listens_for(GraphEdgeRecord, "before_insert")
def _initialize_graph_edge_identity(
    _mapper, _connection, edge: GraphEdgeRecord
) -> None:
    _initialize_graph_identity(edge, "graph-edge")


@event.listens_for(GraphNodeRecord, "before_update")
@event.listens_for(GraphEdgeRecord, "before_update")
def _advance_graph_artifact_version(_mapper, _connection, artifact) -> None:
    artifact.artifact_version = max(1, int(artifact.artifact_version or 1)) + 1


class SemanticProfileRecord(Base):
    __tablename__ = "semantic_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    node_id: Mapped[int] = mapped_column(
        ForeignKey("graph_nodes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_fingerprint: Mapped[str] = mapped_column(
        String(128), nullable=False, index=True
    )
    profile_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    embedding_ref: Mapped[str] = mapped_column(String(160), nullable=False, default="")
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="pending", index=True
    )
    provider: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    model: Mapped[str] = mapped_column(String(160), nullable=False, default="")
    prompt_version: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class SemanticClusterRecord(Base):
    __tablename__ = "semantic_clusters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    stable_key: Mapped[str] = mapped_column(
        String(160), unique=True, nullable=False, index=True
    )
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    centroid_ref: Mapped[str] = mapped_column(String(160), nullable=False, default="")
    parent_cluster_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    color_id: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="active", index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class SemanticClusterAssignmentRecord(Base):
    __tablename__ = "semantic_cluster_assignments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    node_id: Mapped[int] = mapped_column(
        ForeignKey("graph_nodes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    cluster_id: Mapped[int] = mapped_column(
        ForeignKey("semantic_clusters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    confidence_lower: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence_upper: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence_sample_size: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    confidence_method: Mapped[str] = mapped_column(
        String(80), nullable=False, default="unavailable"
    )
    alternative_cluster_id: Mapped[int | None] = mapped_column(
        ForeignKey("semantic_clusters.id", ondelete="SET NULL"), nullable=True
    )
    margin: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    reason: Mapped[str] = mapped_column(Text, nullable=False, default="")
    evidence_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    validated_by: Mapped[str] = mapped_column(
        String(80), nullable=False, default="algorithm"
    )
    pinned_by_user: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class GraphSemanticCandidateRecord(Base):
    __tablename__ = "graph_semantic_candidates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    candidate_kind: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    source_record_id: Mapped[int | None] = mapped_column(
        Integer, nullable=True, index=True
    )
    proposed_type: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    proposed_label: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="pending", index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class GraphPaletteRecord(Base):
    __tablename__ = "graph_palettes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    color_id: Mapped[str] = mapped_column(
        String(80), unique=True, nullable=False, index=True
    )
    oklch: Mapped[str] = mapped_column(String(80), nullable=False)
    light_hex: Mapped[str] = mapped_column(String(12), nullable=False)
    dark_hex: Mapped[str] = mapped_column(String(12), nullable=False)
    border: Mapped[str] = mapped_column(String(12), nullable=False)
    text: Mapped[str] = mapped_column(String(12), nullable=False)
    namespace: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    accessibility_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")


class VaultVisualIdentityRecord(Base):
    __tablename__ = "vault_visual_identities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    vault_id: Mapped[str] = mapped_column(
        String(160), unique=True, nullable=False, index=True
    )
    color_id: Mapped[str] = mapped_column(String(80), nullable=False)
    icon: Mapped[str] = mapped_column(String(80), nullable=False, default="vault")
    assigned_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class NodeEnrichmentVersionRecord(Base):
    __tablename__ = "node_enrichment_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    node_id: Mapped[int] = mapped_column(
        ForeignKey("graph_nodes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    source_fingerprint: Mapped[str] = mapped_column(
        String(128), nullable=False, index=True
    )
    analysis_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    evidence_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    provider: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    model: Mapped[str] = mapped_column(String(160), nullable=False, default="")
    prompt_version: Mapped[str] = mapped_column(String(80), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class GraphResearchRunRecord(Base):
    __tablename__ = "graph_research_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="pending", index=True
    )
    graph_version: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    progress: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    planned_queries: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completed_queries: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class GraphResearchResultRecord(Base):
    __tablename__ = "graph_research_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    run_id: Mapped[int] = mapped_column(
        ForeignKey("graph_research_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    node_id: Mapped[int | None] = mapped_column(
        ForeignKey("graph_nodes.id", ondelete="SET NULL"), nullable=True, index=True
    )
    query: Mapped[str] = mapped_column(Text, nullable=False)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    source_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    evidence: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="suggested", index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class AskSessionRecord(Base):
    __tablename__ = "ask_sessions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    mode: Mapped[str] = mapped_column(String(20), nullable=False, default="flow")
    title: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    configuration_fingerprint: Mapped[str] = mapped_column(
        String(128), nullable=False, default=""
    )
    context_summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class AskTurnRecord(Base):
    __tablename__ = "ask_turns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_id: Mapped[str] = mapped_column(
        ForeignKey("ask_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    context_summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    evidence_ids: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    provider: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    model: Mapped[str] = mapped_column(String(160), nullable=False, default="")
    token_usage: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="completed", index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class NotificationRecord(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    type: Mapped[str] = mapped_column(String(80), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    action: Mapped[str] = mapped_column(String(80), nullable=False)
    action_url: Mapped[str] = mapped_column(String(255), nullable=True)
    related_insight_id: Mapped[int] = mapped_column(Integer, nullable=True)
    related_job_id: Mapped[int] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    read_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class MetricRecord(Base):
    __tablename__ = "metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    unit: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    formula: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    version: Mapped[str] = mapped_column(String(50), nullable=False, default="1.0")
    window: Mapped[str] = mapped_column(String(50), nullable=False, default="all_time")
    sample_size: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sources: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    measured_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class JudgeVerdictRecord(Base):
    """Individual verdict emitted by a single judge in a (possibly multi-judge) evaluation.

    A committee run (`ArtifactEvaluationRecord`) groups N verdicts via `committee_id`.
    The summary verdict on the parent ArtifactEvaluationRecord is derived from these rows.
    """

    __tablename__ = "judge_verdicts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    committee_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    artifact_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    artifact_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    judge_slot: Mapped[str] = mapped_column(String(80), nullable=False)
    provider: Mapped[str] = mapped_column(String(80), nullable=False)
    model: Mapped[str] = mapped_column(String(160), nullable=False)
    verdict: Mapped[str] = mapped_column(String(50), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    rubric: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    reasoning: Mapped[str] = mapped_column(Text, nullable=False, default="")
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_summary: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class HumanReviewRecord(Base):
    """Human reviewer verdict against a committee run, importable from the
    `judge_human_review.jsonl` format. Powers the §9 scorecard calibration gates.
    """

    __tablename__ = "judge_human_reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    committee_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    artifact_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    artifact_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    reviewer: Mapped[str] = mapped_column(String(120), nullable=False)
    verdict: Mapped[str] = mapped_column(String(50), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
