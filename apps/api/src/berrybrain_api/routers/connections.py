from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import select

from berrybrain_api.database import SessionLocal
from berrybrain_api.generated_metadata import resolve_note_id
from berrybrain_api.home_summary import list_recent_connections
from berrybrain_api.models import ConnectionRecord, NoteRecord
from berrybrain_api.services import (
    create_connection,
    get_connections_for_note,
    serialize_connection,
    set_connection_status,
)

router = APIRouter(prefix="/api/v1/connections", tags=["connections"])


class SyncConnectionsRequest(BaseModel):
    note_path: str
    connections: list[dict]


@router.post("/sync")
def sync_connections_from_ai(payload: SyncConnectionsRequest) -> dict:
    with SessionLocal() as session:
        note_id = resolve_note_id(session, payload.note_path)
        created = 0
        for conn in payload.connections:
            target_path = conn.get("target", "")
            if not target_path:
                continue
            target_note = session.execute(
                select(NoteRecord).where(NoteRecord.path == target_path)
            ).scalar_one_or_none()
            if target_note is None:
                continue
            conn_type = conn.get("type", "semantic")
            if conn_type not in {
                "backlink",
                "semantic",
                "semantic_similarity",
                "shared_concept",
                "prerequisite",
                "related",
                "duplicate",
                "contrast",
                "example",
                "application",
            }:
                conn_type = "semantic"
            confidence = int(conn.get("confidence", 0.5) * 100)
            reason = conn.get("reason", "")
            existing = session.execute(
                select(ConnectionRecord).where(
                    ConnectionRecord.source_note_id == note_id,
                    ConnectionRecord.target_note_id == target_note.id,
                    ConnectionRecord.connection_type == conn_type,
                )
            ).scalar_one_or_none()
            if existing is None:
                create_connection(
                    session,
                    note_id,
                    target_note.id,
                    conn_type,
                    confidence,
                    reason,
                    "ai",
                    evidence=conn.get("evidence", [])
                    if isinstance(conn.get("evidence", []), list)
                    else [],
                    provider=conn.get("provider", ""),
                    model=conn.get("model", ""),
                    prompt_version=conn.get("prompt_version", "connection-reason.v1"),
                    status=conn.get("status", "suggested"),
                )
                created += 1
        return {"status": "synced", "connections_created": created}


@router.get("")
def list_recent_connections_endpoint(limit: int = 20) -> dict:
    with SessionLocal() as session:
        return {"connections": list_recent_connections(session, limit=min(limit, 100))}


@router.get("/id/{connection_id}")
def get_connection(connection_id: int) -> dict:
    with SessionLocal() as session:
        connection = session.get(ConnectionRecord, connection_id)
        if connection is None:
            raise HTTPException(status_code=404, detail="Connection not found")
        return {"connection": serialize_connection(session, connection)}


@router.post("/id/{connection_id}/confirm")
def confirm_connection(connection_id: int) -> dict:
    with SessionLocal() as session:
        connection = set_connection_status(session, connection_id, "confirmed")
        return {"connection": serialize_connection(session, connection)}


@router.post("/id/{connection_id}/ignore")
def ignore_connection(connection_id: int) -> dict:
    with SessionLocal() as session:
        connection = set_connection_status(session, connection_id, "ignored")
        return {"connection": serialize_connection(session, connection)}


@router.get("/{note_path:path}")
def list_connections(note_path: str) -> dict:
    with SessionLocal() as session:
        note_id = resolve_note_id(session, note_path)
        conns = get_connections_for_note(session, note_id)
        return {"connections": [serialize_connection(session, c) for c in conns]}
