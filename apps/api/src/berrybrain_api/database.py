from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from berrybrain_api.config import get_settings


class Base(DeclarativeBase):
    pass


settings = get_settings()
engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_database() -> None:
    from berrybrain_api import models  # noqa: F401
    from berrybrain_api.schema_migrations import (
        apply_schema_migrations,
        assert_schema_compatible,
    )
    from berrybrain_api.search import init_fts

    assert_schema_compatible(engine)
    Base.metadata.create_all(bind=engine)
    ensure_sqlite_columns()
    apply_schema_migrations(engine)
    ensure_default_profile()

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
            "max_attempts": "INTEGER NOT NULL DEFAULT 3",
            "note_id": "INTEGER NOT NULL DEFAULT 0",
            "note_path": "TEXT NOT NULL DEFAULT ''",
            "content_hash": "TEXT NOT NULL DEFAULT ''",
            "pipeline_run_id": "TEXT NOT NULL DEFAULT ''",
            "idempotency_key": "TEXT NOT NULL DEFAULT ''",
            "claimed_by": "TEXT NOT NULL DEFAULT ''",
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

    sqlite_columns = {
        "concepts": {
            "frequency": "INTEGER NOT NULL DEFAULT 0",
            "related_note_ids": "TEXT NOT NULL DEFAULT '[]'",
            "extracted_by": "VARCHAR(80) NOT NULL DEFAULT 'system'",
            "confidence": "FLOAT NOT NULL DEFAULT 0.5",
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
        },
        "insights": {
            "why_it_matters": "TEXT NOT NULL DEFAULT ''",
            "evidence": "TEXT NOT NULL DEFAULT '[]'",
            "suggested_action": "TEXT NOT NULL DEFAULT ''",
            "graph_impact": "TEXT NOT NULL DEFAULT ''",
            "confidence": "FLOAT NOT NULL DEFAULT 0.5",
            "status": "VARCHAR(50) NOT NULL DEFAULT 'suggested'",
            "provider": "VARCHAR(80) NOT NULL DEFAULT ''",
            "model": "VARCHAR(160) NOT NULL DEFAULT ''",
            "fingerprint": "VARCHAR(128) NOT NULL DEFAULT ''",
            "quality_score": "FLOAT NOT NULL DEFAULT 0.0",
            "feedback_score": "INTEGER NOT NULL DEFAULT 0",
            "expires_at": "DATETIME",
            "last_recalculated_at": "DATETIME",
            "updated_at": "DATETIME",
        },
        "graph_nodes": {
            "title": "VARCHAR(255) NOT NULL DEFAULT ''",
            "summary": "TEXT NOT NULL DEFAULT ''",
            "ai_notes": "TEXT NOT NULL DEFAULT ''",
            "user_notes": "TEXT NOT NULL DEFAULT ''",
            "source": "VARCHAR(80) NOT NULL DEFAULT 'system'",
            "source_note_ids": "TEXT NOT NULL DEFAULT '[]'",
            "source_attachment_ids": "TEXT NOT NULL DEFAULT '[]'",
            "confidence": "FLOAT NOT NULL DEFAULT 0.5",
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
