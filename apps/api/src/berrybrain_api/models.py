from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from berrybrain_api.database import Base


def utc_now() -> datetime:
    return datetime.now(UTC)


class NoteRecord(Base):
    __tablename__ = "notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False)
    path: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    content_hash: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    frontmatter: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    links: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="new")
    language: Mapped[str] = mapped_column(String(20), nullable=False, default="pt-BR")
    note_type: Mapped[str] = mapped_column(String(50), nullable=False, default="note")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    last_processed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class NoteAttachmentRecord(Base):
    __tablename__ = "note_attachments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    note_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    note_path: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_path: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(160), nullable=False, default="")
    category: Mapped[str] = mapped_column(String(40), nullable=False, default="other")
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class AttachmentExtractionRecord(Base):
    __tablename__ = "attachment_extractions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    attachment_id: Mapped[int] = mapped_column(
        Integer, nullable=False, unique=True, index=True
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
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class JobRecord(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    type: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    payload: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


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
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
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


class AuthOtpRecord(Base):
    __tablename__ = "auth_otps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
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
    language: Mapped[str] = mapped_column(String(20), nullable=False, default="pt-BR")
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    frequency: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    related_note_ids: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    extracted_by: Mapped[str] = mapped_column(
        String(80), nullable=False, default="system"
    )
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="suggested")
    provider: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    model: Mapped[str] = mapped_column(String(160), nullable=False, default="")
    source_evidence: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class ConnectionRecord(Base):
    __tablename__ = "connections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    source_note_id: Mapped[int] = mapped_column(Integer, nullable=False)
    target_note_id: Mapped[int] = mapped_column(Integer, nullable=False)
    connection_type: Mapped[str] = mapped_column(String(80), nullable=False)
    confidence: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
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
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="suggested")
    provider: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    model: Mapped[str] = mapped_column(String(160), nullable=False, default="")
    prompt_version: Mapped[str] = mapped_column(
        String(80), nullable=False, default="v1"
    )
    reasoning: Mapped[str] = mapped_column(Text, nullable=False, default="")
    source_context: Mapped[str] = mapped_column(Text, nullable=False, default="")
    applied_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    ignored_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    dismissed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


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
    note_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    generation_type: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    content_hash: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    model_used: Mapped[str | None] = mapped_column(String(80), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class EmbeddingRecord(Base):
    __tablename__ = "embeddings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    note_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    content_hash: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    vector: Mapped[str] = mapped_column(Text, nullable=False)
    model: Mapped[str] = mapped_column(String(80), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class GraphNodeRecord(Base):
    __tablename__ = "graph_nodes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
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
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
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
    provider: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    model: Mapped[str] = mapped_column(String(160), nullable=False, default="")
    prompt_version: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    generated_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    graph_metadata: Mapped[str] = mapped_column(
        "metadata", Text, nullable=False, default="{}"
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class GraphEdgeRecord(Base):
    __tablename__ = "graph_edges"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    source_node_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    target_node_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
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
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


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
