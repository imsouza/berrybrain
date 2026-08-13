"""Vault->Graph pipeline diagnostics.

Used by the vault pipeline diagnostic endpoint and the Monitor block in section 5
of fix-new-version.md. Read-only inspection across API state, worker state
and DB state. No mutation. Safe to expose behind the auth middleware.
"""

from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sqlalchemy import select

from berrybrain_api.database import SessionLocal, engine
from berrybrain_api.models import (
    GraphEdgeRecord,
    GraphNodeRecord,
    JobRecord,
    NoteRecord,
    WorkerStatus,
)

GRAPH_RELATED_JOB_TYPES = (
    "EXPAND_KNOWLEDGE_GRAPH",
    "FIND_CONNECTIONS",
    "GENERATE_INFERRED_CONNECTIONS",
    "EXPAND_CONCEPT_TO_NOTE",
    "GENERATE_GRAPH_INSIGHTS",
    "UPDATE_GRAPH_STATS",
)


@dataclass
class PipelineDiagnostic:
    api_db_path: str
    worker_status: dict[str, Any]
    notes_total: int
    vault_exists: bool
    vault_path: str
    last_note: dict[str, Any] | None
    graph_jobs: dict[str, int]
    graph_nodes: dict[str, int]
    graph_edges: dict[str, int]
    last_graph_job: dict[str, Any] | None
    diagnostics: list[dict[str, str]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "api_db_path": self.api_db_path,
            "worker": self.worker_status,
            "notes_total": self.notes_total,
            "vault": {
                "path": self.vault_path,
                "exists": self.vault_exists,
            },
            "last_note": self.last_note,
            "graph_jobs": self.graph_jobs,
            "graph_nodes": self.graph_nodes,
            "graph_edges": self.graph_edges,
            "last_graph_job": self.last_graph_job,
            "diagnostics": self.diagnostics,
        }


def _db_path_for(engine_obj) -> str:
    try:
        url = str(engine_obj.url)
    except Exception:
        return "<unknown>"
    if url.startswith("sqlite:///"):
        return url.replace("sqlite:///", "", 1)
    return url


def _check_db_writable(db_path: str) -> tuple[bool, str]:
    if not db_path or db_path == "<unknown>" or db_path.startswith("postgres"):
        return True, "non-sqlite backend"
    try:
        conn = sqlite3.connect(db_path, timeout=1)
        conn.execute("PRAGMA quick_check")
        conn.close()
        return True, "ok"
    except sqlite3.OperationalError as exc:  # pragma: no cover - env dep
        return False, f"sqlite error: {exc}"
    except OSError as exc:
        return False, f"db filesystem error: {exc}"


def diagnose_pipeline(vault_path: str | Path) -> PipelineDiagnostic:
    """Build a one-shot diagnostic snapshot of the vault->graph pipeline.

    Source: planning/fix-new-version.md §5. Every field answers a specific
    layer: API/DB parity, vault accessibility, scan result, job status,
    graph node/edge presence. `diagnostics` carries the failing-state
    messages that the web "failing-state" UI reads directly.
    """

    notes_total = 0
    last_note: dict[str, Any] | None = None
    graph_jobs: dict[str, int] = {}
    graph_nodes: dict[str, int] = {}
    graph_edges: dict[str, int] = {}
    last_graph_job: dict[str, Any] | None = None
    worker: dict[str, Any] = {}

    with SessionLocal() as session:
        notes_total = session.query(NoteRecord).count()
        last = session.execute(
            select(NoteRecord).order_by(NoteRecord.id.desc()).limit(1)
        ).scalar_one_or_none()
        if last is not None:
            last_note = {
                "id": last.id,
                "path": last.path,
                "created_at": last.created_at.isoformat()
                if getattr(last, "created_at", None)
                else None,
            }

        for jt in GRAPH_RELATED_JOB_TYPES:
            graph_jobs[jt] = (
                session.query(JobRecord).filter(JobRecord.type == jt).count()
            )

        for status in ("pending", "completed", "failed", "running"):
            graph_jobs[f"__status_{status}"] = (
                session.query(JobRecord)
                .filter(JobRecord.type.in_(GRAPH_RELATED_JOB_TYPES))
                .filter(JobRecord.status == status)
                .count()
            )

        graph_jobs["pending_total"] = graph_jobs.get("__status_pending", 0)
        graph_jobs["failed_total"] = graph_jobs.get("__status_failed", 0)

        for kind in ("note", "concept", "topic", "entity", "insight"):
            graph_nodes[kind] = (
                session.query(GraphNodeRecord)
                .filter(GraphNodeRecord.type == kind)
                .count()
            )
        graph_nodes["all"] = session.query(GraphNodeRecord).count()
        graph_nodes["active"] = (
            session.query(GraphNodeRecord)
            .filter(GraphNodeRecord.status != "ignored")
            .count()
        )

        graph_edges["all"] = session.query(GraphEdgeRecord).count()
        graph_edges["ai"] = (
            session.query(GraphEdgeRecord)
            .filter(GraphEdgeRecord.created_by == "ai")
            .count()
        )

        last_j = session.execute(
            select(JobRecord)
            .where(JobRecord.type.in_(GRAPH_RELATED_JOB_TYPES))
            .order_by(JobRecord.created_at.desc())
            .limit(1)
        ).scalar_one_or_none()
        if last_j is not None:
            last_graph_job = {
                "id": last_j.id,
                "type": last_j.type,
                "status": last_j.status,
                "error": last_j.error_message,
                "note_path": last_j.note_path,
                "created_at": last_j.created_at.isoformat()
                if getattr(last_j, "created_at", None)
                else None,
            }

        ws = session.execute(
            select(WorkerStatus).order_by(WorkerStatus.id.desc()).limit(1)
        ).scalar_one_or_none()
        if ws is not None:
            worker = {
                "status": ws.status,
                "jobs_processed": ws.jobs_processed,
                "errors": ws.errors,
                "last_heartbeat": ws.last_heartbeat.isoformat()
                if getattr(ws, "last_heartbeat", None)
                else None,
            }

    api_db_path = _db_path_for(engine)
    vault_path = str(vault_path)
    vault_exists = Path(vault_path).exists()

    diagnostics: list[dict[str, str]] = []

    if not vault_exists:
        diagnostics.append(
            {
                "code": "VAULT_MISSING",
                "severity": "error",
                "message": f"Vault path not found: {vault_path}",
            }
        )

    if not notes_total:
        diagnostics.append(
            {
                "code": "NO_NOTES_SCANNED",
                "severity": "warn",
                "message": "No notes present. Run /api/v1/vault/scan.",
            }
        )
    elif graph_nodes.get("all", 0) == 0:
        diagnostics.append(
            {
                "code": "NOTES_SCANNED_JOBS_PENDING",
                "severity": "warn",
                "message": "Notes exist but no graph nodes yet. Worker may still be processing.",
            }
        )

    if graph_jobs.get("failed_total", 0) > 0:
        diagnostics.append(
            {
                "code": "GRAPH_JOBS_FAILED",
                "severity": "error",
                "message": f"{graph_jobs['failed_total']} graph jobs failed. Check Monitor.",
            }
        )

    if graph_nodes.get("all", 0) > 0 and graph_nodes.get("active", 0) == 0:
        diagnostics.append(
            {
                "code": "GRAPH_HIDDEN_BY_FILTERS",
                "severity": "warn",
                "message": "Graph has nodes but all are 'ignored'. UI hides them by default.",
            }
        )

    if last_graph_job and last_graph_job.get("status") == "failed":
        diagnostics.append(
            {
                "code": "LAST_GRAPH_JOB_FAILED",
                "severity": "error",
                "message": f"Last graph job ({last_graph_job['type']}) failed: {last_graph_job['error']}",
            }
        )

    worker_url = os.environ.get("BERRYBRAIN_WORKER_API_URL", "<unset>")
    if worker_url == "<unset>" and not worker.get("last_heartbeat"):
        diagnostics.append(
            {
                "code": "NO_WORKER_HEARTBEAT",
                "severity": "warn",
                "message": "Worker never reported a heartbeat.",
            }
        )

    ok, msg = _check_db_writable(api_db_path)
    if not ok:
        diagnostics.append(
            {"code": "DB_NOT_WRITABLE", "severity": "error", "message": msg}
        )

    return PipelineDiagnostic(
        api_db_path=api_db_path,
        worker_status=worker,
        notes_total=notes_total,
        vault_exists=vault_exists,
        vault_path=vault_path,
        last_note=last_note,
        graph_jobs=graph_jobs,
        graph_nodes=graph_nodes,
        graph_edges=graph_edges,
        last_graph_job=last_graph_job,
        diagnostics=diagnostics,
    )
