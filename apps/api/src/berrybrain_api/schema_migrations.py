from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import Engine, inspect, text
from sqlalchemy.engine import Connection

CURRENT_SCHEMA_VERSION = 8
MIN_SUPPORTED_SCHEMA_VERSION = 0


class IncompatibleSchemaError(RuntimeError):
    pass


@dataclass(frozen=True)
class SchemaMigration:
    version: int
    name: str
    description: str


MIGRATIONS = (
    SchemaMigration(
        version=1,
        name="structured-jobs-and-embeddings",
        description="Adds structured job identity, leases, chunks, and embedding provenance.",
    ),
    SchemaMigration(
        version=2,
        name="cognitive-attachments-and-graph-provenance",
        description="Adds attachment extraction locations and graph/insight traceability.",
    ),
    SchemaMigration(
        version=3,
        name="managed-service-token-rotation",
        description="Adds hashed rotating service tokens for API and Worker authentication.",
    ),
    SchemaMigration(
        version=4,
        name="persisted-graph-inferences",
        description="Adds auditable graph inference records linked to saved insights.",
    ),
    SchemaMigration(
        version=5,
        name="model-invocation-ledger",
        description="Adds privacy-preserving model invocation provenance and diagnostics.",
    ),
    SchemaMigration(
        version=6,
        name="worker-inbox-and-claim-tokens",
        description="Adds exactly-once worker terminal-message consumption per claim.",
    ),
    SchemaMigration(
        version=7,
        name="semantic-graph-runtime",
        description=(
            "Adds versioned job payloads, semantic graph fields, research runs, "
            "persistent Flow sessions, and supporting indexes."
        ),
    ),
    SchemaMigration(
        version=8,
        name="graph-pagination-and-vault-namespace",
        description=(
            "Adds explicit vault identity and indexes used by graph pagination "
            "and versioned delta reads."
        ),
    ),
)


def assert_schema_compatible(bind: Engine) -> int:
    version = get_schema_version(bind)
    if version > CURRENT_SCHEMA_VERSION:
        raise IncompatibleSchemaError(
            "Database schema is newer than this BerryBrain build "
            f"({version} > {CURRENT_SCHEMA_VERSION}). Upgrade BerryBrain before starting."
        )
    if version < MIN_SUPPORTED_SCHEMA_VERSION:
        raise IncompatibleSchemaError(
            f"Database schema {version} is no longer supported."
        )
    return version


def get_schema_version(bind: Engine) -> int:
    if "schema_migrations" not in inspect(bind).get_table_names():
        return 0
    with bind.connect() as connection:
        value = connection.execute(
            text("SELECT COALESCE(MAX(version), 0) FROM schema_migrations")
        ).scalar_one()
    return int(value or 0)


def apply_schema_migrations(bind: Engine) -> dict[str, object]:
    previous = assert_schema_compatible(bind)
    _ensure_migration_table(bind)
    applied: list[dict[str, object]] = []
    with bind.begin() as connection:
        for migration in MIGRATIONS:
            if migration.version <= previous:
                continue
            _apply_migration_ddl(connection, migration.version)
            connection.execute(
                text(
                    "INSERT INTO schema_migrations "
                    "(version, name, description, applied_at) "
                    "VALUES (:version, :name, :description, :applied_at)"
                ),
                {
                    "version": migration.version,
                    "name": migration.name,
                    "description": migration.description,
                    "applied_at": datetime.now(UTC).isoformat(),
                },
            )
            applied.append({"version": migration.version, "name": migration.name})
    return {
        "fromVersion": previous,
        "toVersion": get_schema_version(bind),
        "applied": applied,
    }


def _apply_migration_ddl(connection: Connection, version: int) -> None:
    if version == 8:
        _add_columns(
            connection,
            "graph_nodes",
            {"vault_id": "VARCHAR(160) NOT NULL DEFAULT 'default'"},
        )
        existing_tables = set(inspect(connection).get_table_names())
        for table, column in (
            ("graph_nodes", "vault_id"),
            ("graph_nodes", "updated_at"),
            ("graph_edges", "updated_at"),
        ):
            if table not in existing_tables:
                continue
            connection.execute(
                text(
                    f"CREATE INDEX IF NOT EXISTS ix_{table}_{column} "
                    f"ON {table} ({column})"
                )
            )
        return
    if version == 7:
        from berrybrain_api.models import (
            AskSessionRecord,
            AskTurnRecord,
            GraphPaletteRecord,
            GraphResearchResultRecord,
            GraphResearchRunRecord,
            JobAttemptRecord,
            NodeEnrichmentVersionRecord,
            SemanticClusterAssignmentRecord,
            SemanticClusterRecord,
            SemanticProfileRecord,
            VaultVisualIdentityRecord,
        )

        for model in (
            JobAttemptRecord,
            SemanticProfileRecord,
            SemanticClusterRecord,
            SemanticClusterAssignmentRecord,
            GraphPaletteRecord,
            VaultVisualIdentityRecord,
            NodeEnrichmentVersionRecord,
            GraphResearchRunRecord,
            GraphResearchResultRecord,
            AskSessionRecord,
            AskTurnRecord,
        ):
            model.__table__.create(bind=connection, checkfirst=True)
        _add_columns(
            connection,
            "jobs",
            {
                "payload_schema_version": "INTEGER NOT NULL DEFAULT 1",
            },
        )
        _add_columns(
            connection,
            "graph_nodes",
            {
                "semantic_state": "VARCHAR(30) NOT NULL DEFAULT 'pending'",
                "semantic_profile_version": "INTEGER NOT NULL DEFAULT 0",
                "cluster_id": "INTEGER",
                "color_id": "VARCHAR(80) NOT NULL DEFAULT 'pending'",
                "color_confidence": "FLOAT NOT NULL DEFAULT 0",
                "color_reason": "TEXT NOT NULL DEFAULT ''",
                "color_updated_at": "DATETIME",
            },
        )
        for table, column in (
            ("job_attempts", "job_id"),
            ("job_attempts", "stage"),
            ("semantic_profiles", "node_id"),
            ("semantic_profiles", "source_fingerprint"),
            ("semantic_clusters", "stable_key"),
            ("semantic_cluster_assignments", "node_id"),
            ("semantic_cluster_assignments", "cluster_id"),
            ("graph_research_runs", "status"),
            ("graph_research_results", "run_id"),
            ("ask_turns", "session_id"),
        ):
            connection.execute(
                text(
                    f"CREATE INDEX IF NOT EXISTS ix_{table}_{column} "
                    f"ON {table} ({column})"
                )
            )
        return
    if version == 6:
        job_columns = {
            str(row[1])
            for row in connection.execute(text("PRAGMA table_info(jobs)")).all()
        }
        if job_columns and "claim_token" not in job_columns:
            connection.execute(
                text(
                    "ALTER TABLE jobs ADD COLUMN claim_token "
                    "VARCHAR(64) NOT NULL DEFAULT ''"
                )
            )
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS worker_inbox (
                    id INTEGER PRIMARY KEY,
                    message_id VARCHAR(220) NOT NULL UNIQUE,
                    job_id INTEGER NOT NULL,
                    message_type VARCHAR(40) NOT NULL,
                    claim_token VARCHAR(64) NOT NULL DEFAULT '',
                    status VARCHAR(30) NOT NULL DEFAULT 'processed',
                    received_at DATETIME NOT NULL
                )
                """
            )
        )
        for column in ("message_id", "job_id", "message_type"):
            connection.execute(
                text(
                    f"CREATE INDEX IF NOT EXISTS ix_worker_inbox_{column} "
                    f"ON worker_inbox ({column})"
                )
            )
        return
    if version != 5:
        return
    connection.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS model_invocations (
                id INTEGER PRIMARY KEY,
                capability VARCHAR(80) NOT NULL,
                provider VARCHAR(80) NOT NULL,
                model VARCHAR(160) NOT NULL DEFAULT '',
                prompt_version VARCHAR(80) NOT NULL DEFAULT '',
                status VARCHAR(30) NOT NULL,
                remote BOOLEAN NOT NULL DEFAULT 0,
                latency_ms INTEGER NOT NULL DEFAULT 0,
                attempt_count INTEGER NOT NULL DEFAULT 1,
                input_units INTEGER NOT NULL DEFAULT 0,
                output_units INTEGER NOT NULL DEFAULT 0,
                estimated_cost_usd FLOAT NOT NULL DEFAULT 0,
                error_class VARCHAR(120) NOT NULL DEFAULT '',
                error_message TEXT NOT NULL DEFAULT '',
                correlation_id VARCHAR(128) NOT NULL DEFAULT '',
                started_at DATETIME NOT NULL,
                completed_at DATETIME
            )
            """
        )
    )
    for column in ("capability", "provider", "status", "correlation_id"):
        connection.execute(
            text(
                f"CREATE INDEX IF NOT EXISTS ix_model_invocations_{column} "
                f"ON model_invocations ({column})"
            )
        )


def _add_columns(connection: Connection, table: str, columns: dict[str, str]) -> None:
    existing = {
        str(row[1])
        for row in connection.execute(text(f"PRAGMA table_info({table})")).all()
    }
    if not existing:
        return
    for name, definition in columns.items():
        if name not in existing:
            connection.execute(
                text(f"ALTER TABLE {table} ADD COLUMN {name} {definition}")
            )


def downgrade_schema(bind: Engine, target_version: int) -> dict[str, int]:
    if target_version < MIN_SUPPORTED_SCHEMA_VERSION:
        raise ValueError("Target schema version is not supported")
    if target_version > CURRENT_SCHEMA_VERSION:
        raise ValueError("Target schema version is newer than this build")
    previous = assert_schema_compatible(bind)
    _ensure_migration_table(bind)
    with bind.begin() as connection:
        connection.execute(
            text("DELETE FROM schema_migrations WHERE version > :target"),
            {"target": target_version},
        )
    return {"fromVersion": previous, "toVersion": get_schema_version(bind)}


def schema_diagnostic(bind: Engine) -> dict[str, object]:
    current = get_schema_version(bind)
    return {
        "currentVersion": current,
        "targetVersion": CURRENT_SCHEMA_VERSION,
        "minimumSupportedVersion": MIN_SUPPORTED_SCHEMA_VERSION,
        "compatible": MIN_SUPPORTED_SCHEMA_VERSION <= current <= CURRENT_SCHEMA_VERSION,
    }


def _ensure_migration_table(bind: Engine) -> None:
    with bind.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL DEFAULT '',
                    applied_at TEXT NOT NULL
                )
                """
            )
        )
