from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import Engine, inspect, text

CURRENT_SCHEMA_VERSION = 4
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
