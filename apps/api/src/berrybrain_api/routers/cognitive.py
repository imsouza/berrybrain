from pydantic import BaseModel

from fastapi import APIRouter

from berrybrain_api.cognitive_layer import (
    answer_cognitive_query,
    cognitive_config,
    cognitive_status,
    index_knowledge_base,
    orchestrate_retrieval,
    semantic_data_state,
)
from berrybrain_api.database import SessionLocal
from berrybrain_api.maturity_service import cognitive_maturity_report

router = APIRouter(prefix="/api/v1/cognitive", tags=["cognitive"])


class CognitiveQueryRequest(BaseModel):
    question: str


@router.get("/status")
def get_cognitive_status() -> dict:
    with SessionLocal() as session:
        return cognitive_status(session)


@router.get("/config")
def get_cognitive_config() -> dict:
    with SessionLocal() as session:
        return cognitive_config(session)


@router.post("/index")
def index_cognitive_knowledge_base() -> dict:
    with SessionLocal() as session:
        return index_knowledge_base(session)


@router.post("/retrieve")
def retrieve_cognitive_context(payload: CognitiveQueryRequest) -> dict:
    with SessionLocal() as session:
        return orchestrate_retrieval(session, payload.question)


@router.get("/semantic-data")
def get_semantic_data_state() -> dict:
    with SessionLocal() as session:
        return semantic_data_state(session)


@router.get("/maturity")
def get_cognitive_maturity() -> dict:
    with SessionLocal() as session:
        return cognitive_maturity_report(session)


@router.post("/query")
async def query_cognitive_layer(payload: CognitiveQueryRequest) -> dict:
    with SessionLocal() as session:
        return await answer_cognitive_query(session, payload.question)
