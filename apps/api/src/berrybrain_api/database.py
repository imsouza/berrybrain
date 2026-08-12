from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from berrybrain_api.config import get_settings


class Base(DeclarativeBase):
    pass


settings = get_settings()


def _ensure_sqlite_parent(database_url: str) -> None:
    url = make_url(database_url)
    if url.drivername != "sqlite":
        return
    database = url.database or ""
    if not database or database == ":memory:":
        return
    try:
        Path(database).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)
    except OSError:
        # Some tests replace the engine after import while local .env may point to
        # container-only paths such as /app/data. Let the actual DB connection
        # surface a clear error if that path is used for real.
        return


_ensure_sqlite_parent(settings.database_url)
_engine_url = make_url(settings.database_url)
_connect_args = (
    {"check_same_thread": False, "timeout": 30}
    if _engine_url.drivername == "sqlite"
    else {}
)
engine = create_engine(settings.database_url, connect_args=_connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def _configure_sqlite_connection(dbapi_connection, _connection_record=None) -> None:
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("PRAGMA busy_timeout = 30000")
        cursor.execute("PRAGMA foreign_keys = ON")
    finally:
        cursor.close()


if _engine_url.drivername == "sqlite":
    event.listen(engine, "connect", _configure_sqlite_connection)


def _configure_sqlite_journal(database_engine=None) -> None:
    target_engine = database_engine or engine
    if target_engine.dialect.name != "sqlite":
        return
    with target_engine.connect() as connection:
        connection.exec_driver_sql("PRAGMA journal_mode = WAL")
        connection.exec_driver_sql("PRAGMA synchronous = NORMAL")


def get_session() -> Generator[Session, None, None]:
    with SessionLocal() as session:
        yield session


def init_database() -> None:
    from berrybrain_api import models  # noqa: F401
    from berrybrain_api.schema_migrations import (
        apply_schema_migrations,
        assert_schema_compatible,
    )
    from berrybrain_api.search import init_fts

    _configure_sqlite_journal()
    assert_schema_compatible(engine)
    Base.metadata.create_all(bind=engine)
    ensure_sqlite_columns()
    apply_schema_migrations(engine)
    ensure_default_profile()
    ensure_default_owner()

    with SessionLocal() as session:
        init_fts(session)


def ensure_default_profile() -> None:
    from sqlalchemy import select

    from berrybrain_api.models import ProfileRecord

    with SessionLocal() as session:
        existing = session.execute(
            select(ProfileRecord).where(ProfileRecord.slug == "default")
        ).scalar_one_or_none()
        if existing is None:
            session.add(
                ProfileRecord(
                    name="Default",
                    slug="default",
                    vault_subpath="",
                    source="system",
                    status="active",
                )
            )
            session.commit()


def ensure_default_owner() -> None:
    settings = get_settings()
    if not settings.enable_default_owner:
        return
    if settings.environment.lower() in {"prod", "production"}:
        raise RuntimeError("BERRYBRAIN_ENABLE_DEFAULT_OWNER is forbidden in production")
    if not settings.default_owner_password:
        raise RuntimeError(
            "BERRYBRAIN_DEFAULT_OWNER_PASSWORD must be set when default owner is enabled"
        )

    from sqlalchemy import select

    from berrybrain_api.models import UserRecord
    from berrybrain_api.security import (
        hash_password,
        normalize_email,
        validate_email,
        validate_password,
    )

    admin_email = validate_email(settings.admin_email)
    validate_password(settings.default_owner_password)
    with SessionLocal() as session:
        existing = session.execute(
            select(UserRecord).where(UserRecord.email == normalize_email(admin_email))
        ).scalar_one_or_none()
        if existing is not None:
            return
        session.add(
            UserRecord(
                email=normalize_email(admin_email),
                display_name="Local Administrator",
                password_hash=hash_password(
                    settings.default_owner_password, settings.session_secret
                ),
                email_verified=True,
                two_factor_enabled=False,
                force_password_reset=settings.default_owner_force_password_reset,
            )
        )
        session.commit()


def ensure_sqlite_columns(bind=None) -> None:
    database_engine = bind or engine
    inspector = inspect(database_engine)
    if "notes" not in inspector.get_table_names():
        return

    existing = {column["name"] for column in inspector.get_columns("notes")}
    required_columns = {
        "frontmatter": "TEXT NOT NULL DEFAULT '{}'",
        "links": "TEXT NOT NULL DEFAULT '[]'",
    }
    with database_engine.begin() as connection:
        for name, definition in required_columns.items():
            if name not in existing:
                connection.execute(
                    text(f"ALTER TABLE notes ADD COLUMN {name} {definition}")
                )

    if "jobs" in inspector.get_table_names():
        existing_jobs = {column["name"] for column in inspector.get_columns("jobs")}
        required_job_columns = {
            "payload_schema_version": "INTEGER NOT NULL DEFAULT 1",
            "max_attempts": "INTEGER NOT NULL DEFAULT 3",
            "note_id": "INTEGER NOT NULL DEFAULT 0",
            "note_path": "TEXT NOT NULL DEFAULT ''",
            "content_hash": "TEXT NOT NULL DEFAULT ''",
            "pipeline_run_id": "TEXT NOT NULL DEFAULT ''",
            "idempotency_key": "TEXT NOT NULL DEFAULT ''",
            "claimed_by": "TEXT NOT NULL DEFAULT ''",
            "claim_token": "TEXT NOT NULL DEFAULT ''",
            "lease_expires_at": "DATETIME",
        }
        with database_engine.begin() as connection:
            for name, definition in required_job_columns.items():
                if name not in existing_jobs:
                    connection.execute(
                        text(f"ALTER TABLE jobs ADD COLUMN {name} {definition}")
                    )
            if "note_path" not in existing_jobs or "content_hash" not in existing_jobs:
                connection.execute(
                    text(
                        """
                        UPDATE jobs
                        SET
                          note_id = COALESCE((SELECT id FROM notes WHERE notes.path = json_extract(jobs.payload, '$.note_path')), 0),
                          note_path = COALESCE(json_extract(payload, '$.note_path'), ''),
                          content_hash = COALESCE(json_extract(payload, '$.content_hash'), ''),
                          pipeline_run_id = COALESCE(json_extract(payload, '$.pipeline_run_id'), ''),
                          idempotency_key = CASE
                            WHEN COALESCE(json_extract(payload, '$.note_path'), '') != ''
                            THEN type || ':' || COALESCE(json_extract(payload, '$.note_path'), '') || ':' || COALESCE(json_extract(payload, '$.content_hash'), '')
                            ELSE ''
                          END
                        WHERE note_path = '' AND content_hash = '' AND idempotency_key = ''
                        """
                    )
                )
            connection.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS idx_jobs_note_pipeline "
                    "ON jobs(note_id, note_path, content_hash, type, status)"
                )
            )
            connection.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS idx_jobs_idempotency_key "
                    "ON jobs(idempotency_key)"
                )
            )
            connection.execute(
                text(
                    """
                    UPDATE jobs
                    SET status = 'superseded',
                        error_message = 'Duplicate active job superseded during migration'
                    WHERE id IN (
                      SELECT id FROM (
                        SELECT id,
                               ROW_NUMBER() OVER (
                                 PARTITION BY idempotency_key
                                 ORDER BY created_at DESC, id DESC
                               ) AS rn
                        FROM jobs
                        WHERE idempotency_key != ''
                          AND status IN ('pending', 'running')
                      )
                      WHERE rn > 1
                    )
                    """
                )
            )
            connection.execute(
                text(
                    "CREATE UNIQUE INDEX IF NOT EXISTS idx_jobs_active_idempotency_key "
                    "ON jobs(idempotency_key) "
                    "WHERE idempotency_key != '' AND status IN ('pending', 'running')"
                )
            )

    if "users" in inspector.get_table_names():
        existing_users = {column["name"] for column in inspector.get_columns("users")}
        if "role" not in existing_users:
            with database_engine.begin() as connection:
                connection.execute(
                    text(
                        "ALTER TABLE users ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'viewer'"
                    )
                )

    quality_columns = {
        "quality_gate_status": "VARCHAR(50) NOT NULL DEFAULT 'pending'",
        "quality_score": "FLOAT NOT NULL DEFAULT 0.0",
        "latest_evaluation_id": "INTEGER",
    }

    for table_name in ["graph_nodes", "graph_edges", "connections", "insights"]:
        if table_name in inspector.get_table_names():
            existing_cols = {
                column["name"] for column in inspector.get_columns(table_name)
            }
            with database_engine.begin() as connection:
                for name, definition in quality_columns.items():
                    if name not in existing_cols:
                        connection.execute(
                            text(
                                f"ALTER TABLE {table_name} ADD COLUMN {name} {definition}"
                            )
                        )

    if "worker_status" in inspector.get_table_names():
        existing_ws = {
            column["name"] for column in inspector.get_columns("worker_status")
        }
        if "ollama_healthy" not in existing_ws:
            with database_engine.begin() as connection:
                connection.execute(
                    text(
                        "ALTER TABLE worker_status ADD COLUMN ollama_healthy BOOLEAN NOT NULL DEFAULT 0"
                    )
                )

    if "embeddings" in inspector.get_table_names():
        existing_embeddings = {
            column["name"] for column in inspector.get_columns("embeddings")
        }
        required_embedding_columns = {
            "chunk_index": "INTEGER NOT NULL DEFAULT -1",
            "provider": "TEXT NOT NULL DEFAULT ''",
            "vector_dimensions": "INTEGER NOT NULL DEFAULT 0",
            "vector_blob": "BLOB",
        }
        with database_engine.begin() as connection:
            for name, definition in required_embedding_columns.items():
                if name not in existing_embeddings:
                    connection.execute(
                        text(f"ALTER TABLE embeddings ADD COLUMN {name} {definition}")
                    )
            connection.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS idx_embeddings_note_chunk "
                    "ON embeddings(note_id, content_hash, chunk_index)"
                )
            )

    if "chunks" in inspector.get_table_names():
        with database_engine.begin() as connection:
            connection.execute(
                text(
                    "CREATE UNIQUE INDEX IF NOT EXISTS idx_chunks_note_hash_index "
                    "ON chunks(note_id, content_hash, chunk_index)"
                )
            )

    if "automation_logs" in inspector.get_table_names():
        existing_logs = {
            column["name"] for column in inspector.get_columns("automation_logs")
        }
        required_log_columns = {
            "reverted_at": "DATETIME",
            "reverted_by_log_id": "INTEGER",
        }
        with database_engine.begin() as connection:
            for name, definition in required_log_columns.items():
                if name not in existing_logs:
                    connection.execute(
                        text(
                            f"ALTER TABLE automation_logs ADD COLUMN {name} {definition}"
                        )
                    )

    if "graph_nodes" in inspector.get_table_names():
        existing_nodes = {
            column["name"] for column in inspector.get_columns("graph_nodes")
        }
        required_node_columns = {
            "semantic_state": "TEXT NOT NULL DEFAULT 'pending'",
            "semantic_profile_version": "INTEGER NOT NULL DEFAULT 0",
            "cluster_id": "INTEGER",
            "vault_id": "VARCHAR(160) NOT NULL DEFAULT 'default'",
            "color_id": "TEXT NOT NULL DEFAULT 'pending'",
            "color_confidence": "FLOAT NOT NULL DEFAULT 0",
            "color_reason": "TEXT NOT NULL DEFAULT ''",
            "color_updated_at": "DATETIME",
            "semantic_status": "TEXT NOT NULL DEFAULT 'active'",
            "ontology_class": "TEXT NOT NULL DEFAULT ''",
            "canonical_label": "TEXT NOT NULL DEFAULT ''",
            "aliases_json": "TEXT NOT NULL DEFAULT '[]'",
            "confidence_lower": "FLOAT",
            "confidence_upper": "FLOAT",
            "confidence_sample_size": "INTEGER NOT NULL DEFAULT 0",
            "confidence_method": "TEXT NOT NULL DEFAULT 'unavailable'",
            "confidence_factors": "TEXT NOT NULL DEFAULT '[]'",
            "confidence_updated_at": "DATETIME",
        }
        with database_engine.begin() as connection:
            for name, definition in required_node_columns.items():
                if name not in existing_nodes:
                    connection.execute(
                        text(f"ALTER TABLE graph_nodes ADD COLUMN {name} {definition}")
                    )

    sqlite_columns = {
        "concepts": {
            "frequency": "INTEGER NOT NULL DEFAULT 0",
            "related_note_ids": "TEXT NOT NULL DEFAULT '[]'",
            "extracted_by": "VARCHAR(80) NOT NULL DEFAULT 'system'",
            "confidence": "FLOAT NOT NULL DEFAULT 0",
            "confidence_lower": "FLOAT",
            "confidence_upper": "FLOAT",
            "confidence_sample_size": "INTEGER NOT NULL DEFAULT 0",
            "confidence_method": "TEXT NOT NULL DEFAULT 'unavailable'",
            "confidence_factors": "TEXT NOT NULL DEFAULT '[]'",
            "confidence_updated_at": "DATETIME",
            "status": "VARCHAR(50) NOT NULL DEFAULT 'suggested'",
            "provider": "VARCHAR(80) NOT NULL DEFAULT ''",
            "model": "VARCHAR(160) NOT NULL DEFAULT ''",
            "source_evidence": "TEXT NOT NULL DEFAULT '[]'",
            "updated_at": "DATETIME",
        },
        "connections": {
            "evidence": "TEXT NOT NULL DEFAULT '[]'",
            "ai_notes": "TEXT NOT NULL DEFAULT ''",
            "user_notes": "TEXT NOT NULL DEFAULT ''",
            "provider": "VARCHAR(80) NOT NULL DEFAULT ''",
            "model": "VARCHAR(160) NOT NULL DEFAULT ''",
            "prompt_version": "VARCHAR(80) NOT NULL DEFAULT ''",
            "status": "VARCHAR(50) NOT NULL DEFAULT 'suggested'",
            "updated_at": "DATETIME",
            "confidence_lower": "FLOAT",
            "confidence_upper": "FLOAT",
            "confidence_sample_size": "INTEGER NOT NULL DEFAULT 0",
            "confidence_method": "TEXT NOT NULL DEFAULT 'unavailable'",
            "confidence_factors": "TEXT NOT NULL DEFAULT '[]'",
            "confidence_updated_at": "DATETIME",
        },
        "graph_inferences": {
            "confidence_lower": "FLOAT",
            "confidence_upper": "FLOAT",
            "confidence_sample_size": "INTEGER NOT NULL DEFAULT 0",
            "confidence_method": "TEXT NOT NULL DEFAULT 'unavailable'",
            "confidence_factors": "TEXT NOT NULL DEFAULT '[]'",
            "confidence_updated_at": "DATETIME",
        },
        "insights": {
            "why_it_matters": "TEXT NOT NULL DEFAULT ''",
            "evidence": "TEXT NOT NULL DEFAULT '[]'",
            "suggested_action": "TEXT NOT NULL DEFAULT ''",
            "graph_impact": "TEXT NOT NULL DEFAULT ''",
            "confidence": "FLOAT NOT NULL DEFAULT 0",
            "status": "VARCHAR(50) NOT NULL DEFAULT 'suggested'",
            "provider": "VARCHAR(80) NOT NULL DEFAULT ''",
            "model": "VARCHAR(160) NOT NULL DEFAULT ''",
            "fingerprint": "VARCHAR(128) NOT NULL DEFAULT ''",
            "quality_score": "FLOAT NOT NULL DEFAULT 0.0",
            "feedback_score": "INTEGER NOT NULL DEFAULT 0",
            "expires_at": "DATETIME",
            "last_recalculated_at": "DATETIME",
            "updated_at": "DATETIME",
            "confidence_lower": "FLOAT",
            "confidence_upper": "FLOAT",
            "confidence_sample_size": "INTEGER NOT NULL DEFAULT 0",
            "confidence_method": "TEXT NOT NULL DEFAULT 'unavailable'",
            "confidence_factors": "TEXT NOT NULL DEFAULT '[]'",
            "confidence_updated_at": "DATETIME",
        },
        "graph_nodes": {
            "title": "VARCHAR(255) NOT NULL DEFAULT ''",
            "summary": "TEXT NOT NULL DEFAULT ''",
            "ai_notes": "TEXT NOT NULL DEFAULT ''",
            "user_notes": "TEXT NOT NULL DEFAULT ''",
            "source": "VARCHAR(80) NOT NULL DEFAULT 'system'",
            "source_note_ids": "TEXT NOT NULL DEFAULT '[]'",
            "source_attachment_ids": "TEXT NOT NULL DEFAULT '[]'",
            "confidence": "FLOAT NOT NULL DEFAULT 0",
            "created_by": "VARCHAR(80) NOT NULL DEFAULT 'system'",
            "created_by_model": "VARCHAR(160) NOT NULL DEFAULT ''",
            "status": "VARCHAR(50) NOT NULL DEFAULT 'suggested'",
            "source_evidence": "TEXT NOT NULL DEFAULT ''",
            "ai_context": "TEXT NOT NULL DEFAULT ''",
            "ai_summary": "TEXT NOT NULL DEFAULT ''",
            "learning_value": "VARCHAR(20) NOT NULL DEFAULT ''",
            "source_quality": "VARCHAR(20) NOT NULL DEFAULT ''",
            "validation_status": "VARCHAR(20) NOT NULL DEFAULT 'unvalidated'",
            "provider": "VARCHAR(80) NOT NULL DEFAULT ''",
            "model": "VARCHAR(160) NOT NULL DEFAULT ''",
            "prompt_version": "VARCHAR(80) NOT NULL DEFAULT ''",
            "generated_at": "DATETIME",
            "updated_at": "DATETIME",
        },
        "graph_edges": {
            "label": "VARCHAR(255) NOT NULL DEFAULT ''",
            "evidence": "TEXT NOT NULL DEFAULT '[]'",
            "ai_notes": "TEXT NOT NULL DEFAULT ''",
            "user_notes": "TEXT NOT NULL DEFAULT ''",
            "source_note_ids": "TEXT NOT NULL DEFAULT '[]'",
            "created_by_model": "VARCHAR(160) NOT NULL DEFAULT ''",
            "provider": "VARCHAR(80) NOT NULL DEFAULT ''",
            "model": "VARCHAR(160) NOT NULL DEFAULT ''",
            "prompt_version": "VARCHAR(80) NOT NULL DEFAULT ''",
            "status": "VARCHAR(50) NOT NULL DEFAULT 'suggested'",
            "created_at": "DATETIME",
            "updated_at": "DATETIME",
            "semantic_status": "TEXT NOT NULL DEFAULT 'active'",
            "ontology_property": "TEXT NOT NULL DEFAULT ''",
            "confidence_lower": "FLOAT",
            "confidence_upper": "FLOAT",
            "confidence_sample_size": "INTEGER NOT NULL DEFAULT 0",
            "confidence_method": "TEXT NOT NULL DEFAULT 'unavailable'",
            "confidence_factors": "TEXT NOT NULL DEFAULT '[]'",
            "confidence_updated_at": "DATETIME",
        },
        "note_attachments": {
            "declared_mime_type": "VARCHAR(160) NOT NULL DEFAULT ''",
            "checksum": "VARCHAR(64) NOT NULL DEFAULT ''",
            "validation_status": "VARCHAR(40) NOT NULL DEFAULT 'validated'",
        },
        "attachment_extractions": {
            "stage": "VARCHAR(50) NOT NULL DEFAULT 'pending'",
            "progress": "INTEGER NOT NULL DEFAULT 0",
            "extractor": "VARCHAR(80) NOT NULL DEFAULT 'attachment-text.v1'",
            "location_metadata": "TEXT NOT NULL DEFAULT '{}'",
        },
    }

    table_names = set(inspector.get_table_names())
    with database_engine.begin() as connection:
        for table_name, columns in sqlite_columns.items():
            if table_name not in table_names:
                continue
            existing_columns = {
                column["name"] for column in inspector.get_columns(table_name)
            }
            for name, definition in columns.items():
                if name not in existing_columns:
                    connection.execute(
                        text(f"ALTER TABLE {table_name} ADD COLUMN {name} {definition}")
                    )
