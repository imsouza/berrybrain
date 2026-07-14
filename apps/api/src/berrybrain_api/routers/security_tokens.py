from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select

from berrybrain_api.config import get_settings
from berrybrain_api.database import SessionLocal
from berrybrain_api.models import ServiceTokenRecord
from berrybrain_api.security import (
    assert_csrf,
    audit_event,
    normalize_email,
    require_session_user,
    revoke_service_token,
    rotate_service_token,
)

router = APIRouter(prefix="/api/v1/security/service-tokens", tags=["security"])


class RotateServiceTokenRequest(BaseModel):
    name: str = Field(default="worker", min_length=1, max_length=120)
    grace_seconds: int = Field(default=900, ge=60, le=3600)


@router.get("")
def list_service_tokens(request: Request) -> dict:
    with SessionLocal() as session:
        _require_owner(session, request, require_csrf=False)
        records = list(
            session.execute(
                select(ServiceTokenRecord).order_by(
                    ServiceTokenRecord.created_at.desc()
                )
            ).scalars()
        )
        return {"tokens": [_serialize_token(item) for item in records]}


@router.post("/rotate", status_code=201)
def rotate_token(payload: RotateServiceTokenRequest, request: Request) -> dict:
    settings = get_settings()
    with SessionLocal() as session:
        owner = _require_owner(session, request, require_csrf=True)
        raw_token, record = rotate_service_token(
            session,
            settings,
            name=payload.name,
            grace_seconds=payload.grace_seconds,
        )
        audit_event(
            session,
            request,
            "SERVICE_TOKEN_ROTATED",
            owner,
            "service_token",
            str(record.id),
            {"name": record.name, "graceSeconds": payload.grace_seconds},
        )
        return {
            "token": raw_token,
            "record": _serialize_token(record),
            "warning": "This token is shown once. Update the Worker before the grace period expires.",
        }


@router.post("/{token_id}/revoke")
def revoke_token(token_id: int, request: Request) -> dict:
    with SessionLocal() as session:
        owner = _require_owner(session, request, require_csrf=True)
        record = session.get(ServiceTokenRecord, token_id)
        if record is None:
            raise HTTPException(status_code=404, detail="Service token not found")
        active_count = len(
            list(
                session.execute(
                    select(ServiceTokenRecord).where(
                        ServiceTokenRecord.status == "active",
                        ServiceTokenRecord.revoked_at.is_(None),
                    )
                ).scalars()
            )
        )
        if record.status == "active" and active_count <= 1:
            raise HTTPException(
                status_code=409,
                detail="Rotate the active token before revoking it.",
            )
        record = revoke_service_token(session, token_id)
        audit_event(
            session,
            request,
            "SERVICE_TOKEN_REVOKED",
            owner,
            "service_token",
            str(record.id),
            {"name": record.name},
        )
        return {"token": _serialize_token(record)}


def _require_owner(session, request: Request, *, require_csrf: bool):
    settings = get_settings()
    user, session_record = require_session_user(session, settings, request)
    if normalize_email(user.email) != normalize_email(settings.admin_email):
        raise HTTPException(status_code=403, detail="Owner access required")
    if require_csrf:
        assert_csrf(settings, request, session_record)
    return user


def _serialize_token(record: ServiceTokenRecord) -> dict[str, object]:
    expires_at = record.expires_at
    if expires_at and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    effective_status = record.status
    if expires_at and expires_at < datetime.now(UTC) and record.status == "grace":
        effective_status = "expired"
    return {
        "id": record.id,
        "name": record.name,
        "status": effective_status,
        "expiresAt": expires_at.isoformat() if expires_at else None,
        "lastUsedAt": record.last_used_at.isoformat() if record.last_used_at else None,
        "createdAt": record.created_at.isoformat() if record.created_at else None,
    }
