import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from berrybrain_api.ask_flow import (
    append_ask_turn,
    cancel_ask_session,
    close_ask_session,
    create_ask_session,
    get_ask_session_payload,
    serialize_ask_session,
    serialize_ask_turn,
)
from berrybrain_api.database import SessionLocal

router = APIRouter(prefix="/api/v1/ask", tags=["ask"])
logger = logging.getLogger(__name__)


class CreateAskSessionRequest(BaseModel):
    mode: str = "flow"
    title: str = ""
    inference_id: int | None = None


class CreateAskTurnRequest(BaseModel):
    content: str


@router.post("/sessions", status_code=201)
def create_session(payload: CreateAskSessionRequest) -> dict:
    with SessionLocal() as session:
        item = create_ask_session(
            session,
            mode=payload.mode,
            title=payload.title,
            inference_id=payload.inference_id,
        )
        return get_ask_session_payload(session, item.id)


@router.get("/sessions/{session_id}")
def get_session(session_id: str) -> dict:
    with SessionLocal() as session:
        return get_ask_session_payload(session, session_id)


@router.post("/sessions/{session_id}/turns")
async def create_turn(session_id: str, payload: CreateAskTurnRequest) -> dict:
    with SessionLocal() as session:
        try:
            user_turn, assistant_turn = await append_ask_turn(
                session, session_id, payload.content
            )
        except Exception as exc:
            if isinstance(exc, HTTPException):
                raise
            logger.exception("Flow turn failed", extra={"session_id": session_id})
            raise HTTPException(
                status_code=502,
                detail="Flow could not complete with the configured AI provider.",
            ) from exc
        return {
            "userTurn": serialize_ask_turn(user_turn),
            "assistantTurn": serialize_ask_turn(assistant_turn),
        }


@router.post("/sessions/{session_id}/cancel")
def cancel_session(session_id: str) -> dict:
    with SessionLocal() as session:
        item = cancel_ask_session(session, session_id)
        return {"session": serialize_ask_session(item)}


@router.post("/sessions/{session_id}/close")
def close_session(session_id: str) -> dict:
    with SessionLocal() as session:
        item = close_ask_session(session, session_id)
        return {"session": serialize_ask_session(item)}
