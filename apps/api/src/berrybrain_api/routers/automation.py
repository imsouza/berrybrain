import json
from typing import Annotated

from fastapi import APIRouter, Query
from fastapi.responses import Response
from pydantic import BaseModel

from berrybrain_api.automation_logs import (
    create_automation_log,
    list_automation_logs,
    serialize_automation_log,
)
from berrybrain_api.database import SessionLocal

router = APIRouter(prefix="/api/v1/automation-logs", tags=["automation"])


class CreateAutomationLogRequest(BaseModel):
    action_type: str
    target_type: str = "system"
    target_id: str = "worker"
    description: str = ""
    before_state: dict | None = None
    after_state: dict | None = None
    reversible: bool = False


@router.get("")
def list_logs(
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    before_id: Annotated[int | None, Query(ge=1)] = None,
    compact: bool = False,
) -> dict:
    with SessionLocal() as session:
        logs = list_automation_logs(
            session, limit=limit + 1, before_id=before_id, compact=compact
        )
        more = len(logs) > limit
        page = logs[:limit]
        return {
            "logs": [serialize_automation_log(log, compact=compact) for log in page],
            "nextCursor": page[-1].id if more else None,
        }


@router.get("/export")
def export_logs(limit: Annotated[int, Query(ge=1, le=1000)] = 500) -> Response:
    """Bounded authenticated export. Never includes before/after note snapshots."""
    with SessionLocal() as session:
        logs = list_automation_logs(session, limit=limit, compact=True)
        payload = {
            "scope": "recent automation logs",
            "limit": limit,
            "containsPrivateMetadata": True,
            "logs": [serialize_automation_log(log, compact=True) for log in logs],
        }
    return Response(
        json.dumps(payload, ensure_ascii=False),
        media_type="application/json",
        headers={
            "Content-Disposition": 'attachment; filename="berrybrain-logs.json"',
            "Cache-Control": "no-store",
        },
    )


@router.post("", status_code=201)
def create_log(payload: CreateAutomationLogRequest) -> dict:
    with SessionLocal() as session:
        log = create_automation_log(
            session,
            action_type=payload.action_type,
            target_type=payload.target_type,
            target_id=payload.target_id,
            description=payload.description,
            before_state=payload.before_state or {},
            after_state=payload.after_state or {},
            reversible=payload.reversible,
        )
        return {"log": serialize_automation_log(log)}
