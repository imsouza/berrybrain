from pydantic import BaseModel

from fastapi import APIRouter

from berrybrain_api.database import SessionLocal
from berrybrain_api.second_brain import (
    expand_knowledge_graph,
    get_node_summary,
    infer_from_graph_with_ai,
    set_edge_status,
    set_edge_user_notes,
    set_node_status,
    set_node_user_notes,
    summarize_graph,
)
from berrybrain_api.services import build_graph, sync_knowledge_graph

router = APIRouter(prefix="/api/v1/graph", tags=["graph"])


class GraphInferRequest(BaseModel):
    question: str


class ManualNotesRequest(BaseModel):
    notes: str = ""


@router.get("")
def get_graph(max_depth: int = 2) -> dict:
    with SessionLocal() as session:
        return build_graph(session, max_depth=max_depth)


@router.get("/summary")
def get_graph_summary() -> dict:
    with SessionLocal() as session:
        return summarize_graph(session)


@router.post("/expand")
def expand_graph() -> dict:
    with SessionLocal() as session:
        return expand_knowledge_graph(session)


@router.post("/rebuild")
def rebuild_graph(dry_run: bool = True) -> dict:
    with SessionLocal() as session:
        if dry_run:
            return {"dryRun": True, "summary": summarize_graph(session)}
        result = expand_knowledge_graph(session)
        return {"dryRun": False, **result}


@router.post("/infer")
async def infer_graph(payload: GraphInferRequest) -> dict:
    with SessionLocal() as session:
        return await infer_from_graph_with_ai(session, payload.question)


@router.post("/sync")
def sync_graph() -> dict:
    with SessionLocal() as session:
        result = sync_knowledge_graph(session)
        return {"status": "synced", **result}


@router.get("/nodes/{node_id}/summary")
def graph_node_summary(node_id: int) -> dict:
    with SessionLocal() as session:
        return get_node_summary(session, node_id)


@router.post("/nodes/{node_id}/confirm")
def confirm_graph_node(node_id: int) -> dict:
    with SessionLocal() as session:
        node = set_node_status(session, node_id, "confirmed")
        return {"id": node.id, "status": node.status}


@router.post("/nodes/{node_id}/ignore")
def ignore_graph_node(node_id: int) -> dict:
    with SessionLocal() as session:
        node = set_node_status(session, node_id, "ignored")
        return {"id": node.id, "status": node.status}


@router.put("/nodes/{node_id}/notes")
def update_graph_node_notes(node_id: int, payload: ManualNotesRequest) -> dict:
    with SessionLocal() as session:
        node = set_node_user_notes(session, node_id, payload.notes)
        return {"id": node.id, "userNotes": node.user_notes}


@router.post("/connections/{edge_id}/confirm")
def confirm_graph_edge(edge_id: int) -> dict:
    with SessionLocal() as session:
        edge = set_edge_status(session, edge_id, "confirmed")
        return {"id": edge.id, "status": edge.status}


@router.put("/connections/{edge_id}/notes")
def update_graph_edge_notes(edge_id: int, payload: ManualNotesRequest) -> dict:
    with SessionLocal() as session:
        edge = set_edge_user_notes(session, edge_id, payload.notes)
        return {"id": edge.id, "userNotes": edge.user_notes}


@router.post("/connections/{edge_id}/ignore")
def ignore_graph_edge(edge_id: int) -> dict:
    with SessionLocal() as session:
        edge = set_edge_status(session, edge_id, "ignored")
        return {"id": edge.id, "status": edge.status}
