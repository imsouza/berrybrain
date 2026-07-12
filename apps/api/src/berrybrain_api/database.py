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
    from berrybrain_api.search import init_fts

    Base.metadata.create_all(bind=engine)
    ensure_sqlite_columns()
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


def ensure_sqlite_columns() -> None:
    inspector = inspect(engine)
    if "notes" not in inspector.get_table_names():
        return

    existing = {column["name"] for column in inspector.get_columns("notes")}
    required_columns = {
        "frontmatter": "TEXT NOT NULL DEFAULT '{}'",
        "links": "TEXT NOT NULL DEFAULT '[]'",
    }
    with engine.begin() as connection:
        for name, definition in required_columns.items():
            if name not in existing:
                connection.execute(
                    text(f"ALTER TABLE notes ADD COLUMN {name} {definition}")
                )

    if "jobs" in inspector.get_table_names():
        existing_jobs = {column["name"] for column in inspector.get_columns("jobs")}
        if "max_attempts" not in existing_jobs:
            with engine.begin() as connection:
                connection.execute(
                    text(
                        "ALTER TABLE jobs ADD COLUMN max_attempts INTEGER NOT NULL DEFAULT 3"
                    )
                )

    if "worker_status" in inspector.get_table_names():
        existing_ws = {
            column["name"] for column in inspector.get_columns("worker_status")
        }
        if "ollama_healthy" not in existing_ws:
            with engine.begin() as connection:
                connection.execute(
                    text(
                        "ALTER TABLE worker_status ADD COLUMN ollama_healthy BOOLEAN NOT NULL DEFAULT 0"
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
    }

    table_names = set(inspector.get_table_names())
    with engine.begin() as connection:
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
