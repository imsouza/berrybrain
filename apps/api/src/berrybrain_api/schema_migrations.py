from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid5

from sqlalchemy import Engine, inspect, text
from sqlalchemy.engine import Connection

CURRENT_SCHEMA_VERSION = 12
MIN_SUPPORTED_SCHEMA_VERSION = 0
IDENTITY_NAMESPACE = UUID("a5f2308d-83a5-4cba-a14a-12942a074af7")


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
    SchemaMigration(
        version=9,
        name="graph-ontology-and-confidence-intervals",
        description=(
            "Adds semantic quarantine, ontology identifiers, and auditable "
            "95 percent confidence intervals for graph artifacts."
        ),
    ),
    SchemaMigration(
        version=10,
        name="remaining-knowledge-confidence-intervals",
        description=(
            "Adds auditable 95 percent confidence intervals to note connections, "
            "concepts, and persisted graph inferences."
        ),
    ),
    SchemaMigration(
        version=11,
        name="contextual-graph-feedback",
        description=(
            "Adds durable contextual user decisions used to suppress rejected graph "
            "artifacts and retain corrections across graph rebuilds."
        ),
    ),
    SchemaMigration(
        version=12,
        name="stable-artifact-identity-and-integrity",
        description=(
            "Adds stable note and graph identities, graph artifact versions, "
            "semantic child cleanup, endpoint guards, and scoped delete cascades."
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
    if version == 12:
        from berrybrain_api.models import LearningEventRecord

        LearningEventRecord.__table__.create(bind=connection, checkfirst=True)
        _apply_integrity_migration(connection)
        return
    if version == 9:
        from berrybrain_api.models import GraphSemanticCandidateRecord

        GraphSemanticCandidateRecord.__table__.create(bind=connection, checkfirst=True)
        confidence_columns = {
            "confidence_lower": "FLOAT",
            "confidence_upper": "FLOAT",
            "confidence_sample_size": "INTEGER NOT NULL DEFAULT 0",
            "confidence_method": "VARCHAR(80) NOT NULL DEFAULT 'unavailable'",
            "confidence_factors": "TEXT NOT NULL DEFAULT '[]'",
            "confidence_updated_at": "DATETIME",
        }
        for table in ("graph_nodes", "graph_edges", "insights"):
            _add_columns(connection, table, confidence_columns)
        _add_columns(
            connection,
            "semantic_cluster_assignments",
            {
                key: value
                for key, value in confidence_columns.items()
                if key not in {"confidence_factors", "confidence_updated_at"}
            },
        )
        _add_columns(
            connection,
            "graph_nodes",
            {
                "semantic_status": "VARCHAR(30) NOT NULL DEFAULT 'active'",
                "ontology_class": "VARCHAR(120) NOT NULL DEFAULT ''",
                "canonical_label": "VARCHAR(255) NOT NULL DEFAULT ''",
                "aliases_json": "TEXT NOT NULL DEFAULT '[]'",
            },
        )
        _add_columns(
            connection,
            "graph_edges",
            {
                "semantic_status": "VARCHAR(30) NOT NULL DEFAULT 'active'",
                "ontology_property": "VARCHAR(120) NOT NULL DEFAULT ''",
            },
        )
        existing_tables = set(inspect(connection).get_table_names())
        for table, column in (
            ("graph_nodes", "semantic_status"),
            ("graph_edges", "semantic_status"),
            ("graph_semantic_candidates", "candidate_kind"),
            ("graph_semantic_candidates", "status"),
        ):
            if table not in existing_tables:
                continue
            connection.execute(
                text(
                    f"CREATE INDEX IF NOT EXISTS ix_{table}_{column} ON {table} ({column})"
                )
            )
        return
    if version == 10:
        confidence_columns = {
            "confidence_lower": "FLOAT",
            "confidence_upper": "FLOAT",
            "confidence_sample_size": "INTEGER NOT NULL DEFAULT 0",
            "confidence_method": "VARCHAR(80) NOT NULL DEFAULT 'unavailable'",
            "confidence_factors": "TEXT NOT NULL DEFAULT '[]'",
            "confidence_updated_at": "DATETIME",
        }
        for table in ("connections", "concepts", "graph_inferences"):
            _add_columns(connection, table, confidence_columns)
        return
    if version == 11:
        from berrybrain_api.models import GraphFeedbackRecord

        GraphFeedbackRecord.__table__.create(bind=connection, checkfirst=True)
        return
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
    if version <= 7:
        _apply_legacy_migration_ddl(connection, version)
        return


def _apply_integrity_migration(connection: Connection) -> None:
    _add_columns(
        connection,
        "notes",
        {
            "stable_id": "VARCHAR(36) NOT NULL DEFAULT ''",
            "source_version": "INTEGER NOT NULL DEFAULT 1",
        },
    )
    for table in ("graph_nodes", "graph_edges"):
        _add_columns(
            connection,
            table,
            {
                "stable_id": "VARCHAR(36) NOT NULL DEFAULT ''",
                "iri": "VARCHAR(255) NOT NULL DEFAULT ''",
                "artifact_version": "INTEGER NOT NULL DEFAULT 1",
            },
        )

    existing_tables = set(inspect(connection).get_table_names())
    for table, iri_kind in (
        ("notes", None),
        ("graph_nodes", "graph-node"),
        ("graph_edges", "graph-edge"),
    ):
        if table not in existing_tables:
            continue
        rows = connection.execute(
            text(f"SELECT id, stable_id FROM {table} ORDER BY id")
        ).mappings()
        for row in rows:
            stable_id = str(row["stable_id"] or "").strip() or str(
                uuid5(IDENTITY_NAMESPACE, f"{table}:{row['id']}")
            )
            values: dict[str, object] = {"id": row["id"], "stable_id": stable_id}
            assignments = "stable_id = :stable_id"
            if iri_kind:
                values["iri"] = f"urn:berrybrain:{iri_kind}:{stable_id}"
                assignments += ", iri = :iri"
            connection.execute(
                text(f"UPDATE {table} SET {assignments} WHERE id = :id"), values
            )
        connection.execute(
            text(
                f"CREATE UNIQUE INDEX IF NOT EXISTS ux_{table}_stable_id ON {table} (stable_id)"
            )
        )
        if iri_kind:
            connection.execute(
                text(
                    f"CREATE UNIQUE INDEX IF NOT EXISTS ux_{table}_iri ON {table} (iri)"
                )
            )

    connection.execute(
        text(
            "CREATE TABLE IF NOT EXISTS schema_migration_archive ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, migration_version INTEGER NOT NULL, "
            "table_name VARCHAR(120) NOT NULL, row_id INTEGER NOT NULL, "
            "payload TEXT NOT NULL, archived_at DATETIME NOT NULL)"
        )
    )
    orphan_queries = {
        "note_attachments": (
            "SELECT child.* FROM note_attachments child LEFT JOIN notes parent "
            "ON parent.id = child.note_id WHERE parent.id IS NULL"
        ),
        "attachment_extractions": (
            "SELECT child.* FROM attachment_extractions child "
            "LEFT JOIN note_attachments parent ON parent.id = child.attachment_id "
            "WHERE parent.id IS NULL"
        ),
        "job_attempts": (
            "SELECT child.* FROM job_attempts child LEFT JOIN jobs parent "
            "ON parent.id = child.job_id WHERE parent.id IS NULL"
        ),
        "worker_inbox": (
            "SELECT child.* FROM worker_inbox child LEFT JOIN jobs parent "
            "ON parent.id = child.job_id WHERE parent.id IS NULL"
        ),
        "user_sessions": (
            "SELECT child.* FROM user_sessions child LEFT JOIN users parent "
            "ON parent.id = child.user_id WHERE parent.id IS NULL"
        ),
        "generated_metadata": (
            "SELECT child.* FROM generated_metadata child LEFT JOIN notes parent "
            "ON parent.id = child.note_id WHERE parent.id IS NULL"
        ),
        "embeddings": (
            "SELECT child.* FROM embeddings child LEFT JOIN notes parent "
            "ON parent.id = child.note_id WHERE parent.id IS NULL"
        ),
        "chunks": (
            "SELECT child.* FROM chunks child LEFT JOIN notes parent "
            "ON parent.id = child.note_id WHERE parent.id IS NULL"
        ),
        "connections": (
            "SELECT child.* FROM connections child "
            "LEFT JOIN notes source ON source.id = child.source_note_id "
            "LEFT JOIN notes target ON target.id = child.target_note_id "
            "WHERE source.id IS NULL OR target.id IS NULL"
        ),
        "graph_research_results": (
            "SELECT child.* FROM graph_research_results child "
            "LEFT JOIN graph_research_runs parent ON parent.id = child.run_id "
            "WHERE parent.id IS NULL"
        ),
        "ask_turns": (
            "SELECT child.* FROM ask_turns child LEFT JOIN ask_sessions parent "
            "ON parent.id = child.session_id WHERE parent.id IS NULL"
        ),
        "semantic_profiles": (
            "SELECT child.* FROM semantic_profiles child LEFT JOIN graph_nodes parent "
            "ON parent.id = child.node_id WHERE parent.id IS NULL"
        ),
        "semantic_cluster_assignments": (
            "SELECT child.* FROM semantic_cluster_assignments child "
            "LEFT JOIN graph_nodes node ON node.id = child.node_id "
            "LEFT JOIN semantic_clusters cluster ON cluster.id = child.cluster_id "
            "WHERE node.id IS NULL OR cluster.id IS NULL"
        ),
        "node_enrichment_versions": (
            "SELECT child.* FROM node_enrichment_versions child "
            "LEFT JOIN graph_nodes parent ON parent.id = child.node_id "
            "WHERE parent.id IS NULL"
        ),
    }
    orphan_dependencies = {
        "note_attachments": {"note_attachments", "notes"},
        "attachment_extractions": {"attachment_extractions", "note_attachments"},
        "job_attempts": {"job_attempts", "jobs"},
        "worker_inbox": {"worker_inbox", "jobs"},
        "user_sessions": {"user_sessions", "users"},
        "generated_metadata": {"generated_metadata", "notes"},
        "embeddings": {"embeddings", "notes"},
        "chunks": {"chunks", "notes"},
        "connections": {"connections", "notes"},
        "graph_research_results": {
            "graph_research_results",
            "graph_research_runs",
        },
        "ask_turns": {"ask_turns", "ask_sessions"},
        "semantic_profiles": {"semantic_profiles", "graph_nodes"},
        "semantic_cluster_assignments": {
            "semantic_cluster_assignments",
            "graph_nodes",
            "semantic_clusters",
        },
        "node_enrichment_versions": {"node_enrichment_versions", "graph_nodes"},
    }
    archived_at = datetime.now(UTC).isoformat()
    for table, query in orphan_queries.items():
        if not orphan_dependencies[table].issubset(existing_tables):
            continue
        rows = list(connection.execute(text(query)).mappings())
        for row in rows:
            connection.execute(
                text(
                    "INSERT INTO schema_migration_archive "
                    "(migration_version, table_name, row_id, payload, archived_at) "
                    "VALUES (12, :table_name, :row_id, :payload, :archived_at)"
                ),
                {
                    "table_name": table,
                    "row_id": row["id"],
                    "payload": json.dumps(dict(row), default=str, sort_keys=True),
                    "archived_at": archived_at,
                },
            )
            connection.execute(
                text(f"DELETE FROM {table} WHERE id = :id"), {"id": row["id"]}
            )

    if {"auth_otps", "users"}.issubset(existing_tables):
        connection.execute(
            text(
                "UPDATE auth_otps SET user_id = NULL WHERE user_id IS NOT NULL "
                "AND NOT EXISTS (SELECT 1 FROM users WHERE users.id = auth_otps.user_id)"
            )
        )
    if {"graph_research_results", "graph_nodes"}.issubset(existing_tables):
        connection.execute(
            text(
                "UPDATE graph_research_results SET node_id = NULL "
                "WHERE node_id IS NOT NULL AND NOT EXISTS "
                "(SELECT 1 FROM graph_nodes WHERE graph_nodes.id = graph_research_results.node_id)"
            )
        )
    if {"graph_inferences", "insights"}.issubset(existing_tables):
        connection.execute(
            text(
                "UPDATE graph_inferences SET insight_id = NULL "
                "WHERE insight_id IS NOT NULL AND NOT EXISTS "
                "(SELECT 1 FROM insights WHERE insights.id = graph_inferences.insight_id)"
            )
        )

    for table in (
        "graph_nodes",
        "graph_edges",
        "insights",
        "connections",
        "concepts",
        "graph_inferences",
    ):
        if table not in existing_tables:
            continue
        columns = {
            str(column[1])
            for column in connection.execute(text(f"PRAGMA table_info({table})"))
        }
        required = {
            "confidence",
            "confidence_lower",
            "confidence_upper",
            "confidence_sample_size",
            "confidence_method",
        }
        if not required.issubset(columns):
            continue
        connection.execute(
            text(
                f"UPDATE {table} SET confidence = 0, confidence_lower = NULL, "
                "confidence_upper = NULL, confidence_sample_size = 0, "
                "confidence_method = 'unavailable' "
                "WHERE confidence_method = 'jeffreys-wilson-evidence-v2'"
            )
        )

    from berrybrain_api.graph_ontology import EDGE_RULES, NODE_RULES

    if "graph_nodes" in existing_tables:
        connection.execute(
            text(
                "UPDATE graph_nodes SET semantic_status = 'quarantined' "
                "WHERE quality_gate_status IN ('rejected', 'insufficient_evidence')"
            )
        )
        for node_type, rule in NODE_RULES.items():
            connection.execute(
                text(
                    "UPDATE graph_nodes SET ontology_class = :ontology_class "
                    "WHERE type = :node_type"
                ),
                {
                    "ontology_class": rule.ontology_class,
                    "node_type": node_type,
                },
            )
    if "graph_edges" in existing_tables:
        connection.execute(
            text(
                "UPDATE graph_edges SET semantic_status = 'quarantined' "
                "WHERE quality_gate_status IN ('rejected', 'insufficient_evidence')"
            )
        )
        for edge_type, rule in EDGE_RULES.items():
            connection.execute(
                text(
                    "UPDATE graph_edges SET ontology_property = :ontology_property "
                    "WHERE type = :edge_type"
                ),
                {
                    "ontology_property": rule.ontology_property,
                    "edge_type": edge_type,
                },
            )
        invalid_edges = list(
            connection.execute(
                text(
                    "SELECT edge.* FROM graph_edges edge "
                    "LEFT JOIN graph_nodes source ON source.id = edge.source_node_id "
                    "LEFT JOIN graph_nodes target ON target.id = edge.target_node_id "
                    "WHERE source.id IS NULL OR target.id IS NULL"
                )
            ).mappings()
        )
        for row in invalid_edges:
            connection.execute(
                text(
                    "INSERT INTO schema_migration_archive "
                    "(migration_version, table_name, row_id, payload, archived_at) "
                    "VALUES (12, 'graph_edges', :row_id, :payload, :archived_at)"
                ),
                {
                    "row_id": row["id"],
                    "payload": json.dumps(dict(row), default=str, sort_keys=True),
                    "archived_at": archived_at,
                },
            )
            connection.execute(
                text("DELETE FROM graph_edges WHERE id = :id"), {"id": row["id"]}
            )

    _create_graph_integrity_triggers(connection, existing_tables)
    _create_relational_integrity_triggers(connection, existing_tables)


def _create_graph_integrity_triggers(
    connection: Connection, existing_tables: set[str]
) -> None:
    if not {"graph_nodes", "graph_edges"}.issubset(existing_tables):
        return
    statements = [
        "CREATE TRIGGER IF NOT EXISTS graph_edges_parent_guard_insert BEFORE INSERT ON graph_edges BEGIN "
        "SELECT RAISE(ABORT, 'Graph edge source node does not exist') WHERE NOT EXISTS "
        "(SELECT 1 FROM graph_nodes WHERE id = NEW.source_node_id); "
        "SELECT RAISE(ABORT, 'Graph edge target node does not exist') WHERE NOT EXISTS "
        "(SELECT 1 FROM graph_nodes WHERE id = NEW.target_node_id); END",
        "CREATE TRIGGER IF NOT EXISTS graph_edges_parent_guard_update BEFORE UPDATE OF source_node_id, target_node_id ON graph_edges BEGIN "
        "SELECT RAISE(ABORT, 'Graph edge source node does not exist') WHERE NOT EXISTS "
        "(SELECT 1 FROM graph_nodes WHERE id = NEW.source_node_id); "
        "SELECT RAISE(ABORT, 'Graph edge target node does not exist') WHERE NOT EXISTS "
        "(SELECT 1 FROM graph_nodes WHERE id = NEW.target_node_id); END",
    ]
    cascade_statements = [
        "DELETE FROM graph_edges WHERE source_node_id = OLD.id OR target_node_id = OLD.id"
    ]
    for table in (
        "semantic_profiles",
        "semantic_cluster_assignments",
        "node_enrichment_versions",
    ):
        if table in existing_tables:
            cascade_statements.append(f"DELETE FROM {table} WHERE node_id = OLD.id")
    statements.append(
        "CREATE TRIGGER IF NOT EXISTS graph_nodes_scoped_delete AFTER DELETE ON graph_nodes BEGIN "
        + "; ".join(cascade_statements)
        + "; END"
    )
    for statement in statements:
        connection.execute(text(statement))


def _create_relational_integrity_triggers(
    connection: Connection, existing_tables: set[str]
) -> None:
    relationships = (
        ("note_attachments", "note_id", "notes", "CASCADE"),
        ("attachment_extractions", "attachment_id", "note_attachments", "CASCADE"),
        ("job_attempts", "job_id", "jobs", "CASCADE"),
        ("worker_inbox", "job_id", "jobs", "CASCADE"),
        ("user_sessions", "user_id", "users", "CASCADE"),
        ("auth_otps", "user_id", "users", "CASCADE"),
        ("generated_metadata", "note_id", "notes", "CASCADE"),
        ("embeddings", "note_id", "notes", "CASCADE"),
        ("chunks", "note_id", "notes", "CASCADE"),
        ("connections", "source_note_id", "notes", "CASCADE"),
        ("connections", "target_note_id", "notes", "CASCADE"),
        ("graph_inferences", "insight_id", "insights", "SET NULL"),
        ("semantic_profiles", "node_id", "graph_nodes", "CASCADE"),
        (
            "semantic_cluster_assignments",
            "node_id",
            "graph_nodes",
            "CASCADE",
        ),
        (
            "semantic_cluster_assignments",
            "cluster_id",
            "semantic_clusters",
            "CASCADE",
        ),
        (
            "semantic_cluster_assignments",
            "alternative_cluster_id",
            "semantic_clusters",
            "SET NULL",
        ),
        ("node_enrichment_versions", "node_id", "graph_nodes", "CASCADE"),
        (
            "graph_research_results",
            "run_id",
            "graph_research_runs",
            "CASCADE",
        ),
        ("graph_research_results", "node_id", "graph_nodes", "SET NULL"),
        ("ask_turns", "session_id", "ask_sessions", "CASCADE"),
    )
    for child, column, parent, on_delete in relationships:
        if not {child, parent}.issubset(existing_tables):
            continue
        prefix = f"ri_{child}_{column}"
        error = f"{child}.{column} parent does not exist"
        condition = (
            f"NEW.{column} IS NOT NULL AND NOT EXISTS "
            f"(SELECT 1 FROM {parent} WHERE id = NEW.{column})"
        )
        connection.execute(
            text(
                f"CREATE TRIGGER IF NOT EXISTS {prefix}_insert BEFORE INSERT ON {child} "
                f"BEGIN SELECT RAISE(ABORT, '{error}') WHERE {condition}; END"
            )
        )
        connection.execute(
            text(
                f"CREATE TRIGGER IF NOT EXISTS {prefix}_update BEFORE UPDATE OF {column} ON {child} "
                f"BEGIN SELECT RAISE(ABORT, '{error}') WHERE {condition}; END"
            )
        )
        if on_delete == "CASCADE":
            action = f"DELETE FROM {child} WHERE {column} = OLD.id"
        else:
            action = f"UPDATE {child} SET {column} = NULL WHERE {column} = OLD.id"
        connection.execute(
            text(
                f"CREATE TRIGGER IF NOT EXISTS {prefix}_delete AFTER DELETE ON {parent} "
                f"BEGIN {action}; END"
            )
        )


def _apply_legacy_migration_ddl(connection: Connection, version: int) -> None:
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
        if target_version < 12:
            trigger_names = connection.execute(
                text(
                    "SELECT name FROM sqlite_master WHERE type = 'trigger' "
                    "AND (name LIKE 'ri_%' OR name LIKE 'graph_%')"
                )
            ).scalars()
            for trigger_name in trigger_names:
                connection.execute(text(f'DROP TRIGGER IF EXISTS "{trigger_name}"'))
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
