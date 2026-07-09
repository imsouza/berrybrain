from fastapi import APIRouter
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
def list_logs(limit: int = 50) -> dict:
    with SessionLocal() as session:
        logs = list_automation_logs(session, limit=min(limit, 100))
        return {"logs": [serialize_automation_log(log) for log in logs]}


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
