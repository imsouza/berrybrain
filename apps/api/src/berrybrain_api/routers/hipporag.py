from __future__ import annotations

import json
import logging
import os

import httpx
from fastapi import APIRouter
from sqlalchemy import select

from berrybrain_api.database import SessionLocal
from berrybrain_api.models import GraphEdgeRecord, GraphNodeRecord, NoteRecord

router = APIRouter(prefix="/api/v1/hipporag", tags=["hipporag"])
logger = logging.getLogger(__name__)

HIPPORAG_URL = os.getenv("HIPPORAG_URL", "http://localhost:8000")
HIPPORAG_SERVICE_TOKEN = os.getenv("HIPPORAG_SERVICE_TOKEN", "")


def _headers() -> dict[str, str]:
    if not HIPPORAG_SERVICE_TOKEN:
        return {}
    return {"Authorization": f"Bearer {HIPPORAG_SERVICE_TOKEN}"}


def _sync_failure(path: str) -> dict[str, str]:
    return {"path": path, "code": "sidecar_request_failed"}


def _ids(raw: str) -> set[int]:
    try:
        values = json.loads(raw or "[]")
    except (TypeError, json.JSONDecodeError):
        return set()
    return {
        int(value)
        for value in values
        if isinstance(value, int | str) and str(value).isdigit()
    }


@router.get("/status")
async def hipporag_status():
    try:
        async with httpx.AsyncClient() as client:
            res = await client.get(f"{HIPPORAG_URL}/health", timeout=3.0)
            res.raise_for_status()
            return {"status": "online", "details": res.json()}
    except Exception:
        return {"status": "offline"}


@router.post("/reconcile")
async def hipporag_reconcile():
    try:
        async with httpx.AsyncClient() as client:
            res = await client.post(
                f"{HIPPORAG_URL}/reconcile", headers=_headers(), timeout=10.0
            )
            res.raise_for_status()
            return res.json()
    except Exception:
        return {"status": "error", "message": "HippoRAG reconcile failed."}


@router.post("/rebuild")
async def hipporag_rebuild():
    try:
        async with httpx.AsyncClient() as client:
            res = await client.post(
                f"{HIPPORAG_URL}/rebuild", headers=_headers(), timeout=10.0
            )
            res.raise_for_status()
            return res.json()
    except Exception:
        return {"status": "error", "message": "HippoRAG rebuild failed."}


@router.post("/sync-graph")
async def hipporag_sync_graph() -> dict:
    with SessionLocal() as session:
        notes = list(session.execute(select(NoteRecord)).scalars())
        nodes = list(
            session.execute(
                select(GraphNodeRecord).where(
                    GraphNodeRecord.status != "ignored",
                    GraphNodeRecord.semantic_status == "active",
                )
            ).scalars()
        )
        edges = list(
            session.execute(
                select(GraphEdgeRecord).where(
                    GraphEdgeRecord.status != "ignored",
                    GraphEdgeRecord.semantic_status == "active",
                )
            ).scalars()
        )

    note_ids = {note.id for note in notes}
    node_by_id = {node.id: node for node in nodes}
    note_id_by_node = {
        node.id: int(node.source_id)
        for node in nodes
        if node.type == "note" and node.source_id in note_ids
    }
    triples_by_note: dict[int, set[tuple[str, str, str]]] = {
        note.id: {(note.title, "rdf:type", "schema:CreativeWork")} for note in notes
    }
    for node in nodes:
        associated_notes = _ids(node.source_note_ids)
        if node.id in note_id_by_node:
            associated_notes.add(note_id_by_node[node.id])
        for note_id in associated_notes & note_ids:
            triples_by_note[note_id].add(
                (node.label, "rdf:type", node.ontology_class or f"bb:{node.type}")
            )
    for edge in edges:
        source = node_by_id.get(edge.source_node_id)
        target = node_by_id.get(edge.target_node_id)
        if source is None or target is None:
            continue
        associated_notes = _ids(edge.source_note_ids)
        associated_notes.update(_ids(source.source_note_ids))
        associated_notes.update(_ids(target.source_note_ids))
        if source.id in note_id_by_node:
            associated_notes.add(note_id_by_node[source.id])
        if target.id in note_id_by_node:
            associated_notes.add(note_id_by_node[target.id])
        triple = (
            source.label,
            edge.ontology_property or f"bb:{edge.type}",
            target.label,
        )
        for note_id in associated_notes & note_ids:
            triples_by_note[note_id].add(triple)

    indexed = 0
    triple_count = 0
    errors: list[dict[str, str]] = []
    async with httpx.AsyncClient() as client:
        for note in notes:
            triples = [
                {"subject": subject, "predicate": predicate, "object": object_}
                for subject, predicate, object_ in sorted(triples_by_note[note.id])
            ]
            try:
                response = await client.post(
                    f"{HIPPORAG_URL}/index",
                    headers=_headers(),
                    json={
                        "vault_id": "default",
                        "doc_id": note.path,
                        "content": note.content,
                        "triples": triples,
                    },
                    timeout=30.0,
                )
                response.raise_for_status()
                indexed += 1
                triple_count += int(response.json().get("triples", 0))
            except Exception:
                logger.warning(
                    "HippoRAG graph sync failed for note %s",
                    note.id,
                    exc_info=True,
                )
                errors.append(_sync_failure(note.path))
    return {
        "status": "completed" if not errors else "partial",
        "documents": indexed,
        "triples": triple_count,
        "errors": errors,
    }
