from datetime import datetime, timezone

from fastapi import APIRouter
from sqlalchemy import select

from berrybrain_api.database import SessionLocal
from berrybrain_api.models import InsightRecord, NotificationRecord

router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])

NOTIFICATION_TYPES = {
    "insight_ready": "Insight ready",
    "job_failed": "Job failed",
    "graph_updated": "Graph updated",
    "note_assimilated": "Note assimilated",
    "title_generated": "Title generated",
    "provider_slow": "Provider slow",
    "provider_offline": "Provider offline",
    "connection_suggested": "Connection suggested",
    "attention_required": "Attention required",
}


def _create_notification(
    session,
    notification_type: str,
    title: str,
    description: str,
    action: str,
    action_url: str | None = None,
    related_insight_id: int | None = None,
    related_job_id: int | None = None,
) -> NotificationRecord:
    notification = NotificationRecord(
        type=notification_type,
        title=title,
        description=description,
        action=action,
        action_url=action_url,
        related_insight_id=related_insight_id,
        related_job_id=related_job_id,
    )
    session.add(notification)
    session.commit()
    session.refresh(notification)
    return notification


def _get_recent_notifications(session, limit: int = 20) -> list[dict]:
    notifications = list(
        session.execute(
            select(NotificationRecord)
            .order_by(NotificationRecord.created_at.desc())
            .limit(limit)
        ).scalars()
    )
    result = []
    for n in notifications:
        insight = (
            session.get(InsightRecord, n.related_insight_id)
            if n.related_insight_id
            else None
        )
        result.append(
            {
                "id": n.id,
                "type": n.type,
                "title": n.title,
                "description": n.description,
                "action": n.action,
                "actionUrl": n.action_url,
                "createdAt": n.created_at.isoformat() if n.created_at else None,
                "read": n.read_at is not None,
                "insightTitle": insight.title if insight else None,
            }
        )
    return result


@router.get("")
def list_notifications(limit: int = 20) -> dict:
    with SessionLocal() as session:
        notifications = _get_recent_notifications(session, limit=limit)
        return {"notifications": notifications}


@router.post("/{notification_id}/read")
def mark_notification_read(notification_id: int) -> dict:
    with SessionLocal() as session:
        notification = session.get(NotificationRecord, notification_id)
        if notification is None:
            return {"status": "not_found"}
        notification.read_at = datetime.now(timezone.utc)
        session.commit()
        session.refresh(notification)
        return {"status": "read", "notification": {"id": notification.id, "read": True}}


@router.post("/read-all")
def mark_all_notifications_read() -> dict:
    with SessionLocal() as session:
        notifications = list(
            session.execute(
                select(NotificationRecord).where(NotificationRecord.read_at.is_(None))
            ).scalars()
        )
        now = datetime.now(timezone.utc)
        for n in notifications:
            n.read_at = now
        session.commit()
        return {"status": "marked_read", "count": len(notifications)}


@router.post("/generate-insight-notification")
def generate_insight_notification(insight_id: int) -> dict:
    with SessionLocal() as session:
        insight = session.get(InsightRecord, insight_id)
        if insight is None:
            return {"status": "insight_not_found"}

        notification = _create_notification(
            session=session,
            notification_type="insight_ready",
            title="Insight pronto",
            description=insight.title,
            action="Ver insight",
            action_url="/insights",
            related_insight_id=insight_id,
        )
        return {"status": "created", "notification": {"id": notification.id}}


@router.post("/create-from-failed-job")
def create_from_failed_job(job_id: int, error_message: str | None = None) -> dict:
    with SessionLocal() as session:
        notification = _create_notification(
            session=session,
            notification_type="job_failed",
            title="Job falhou",
            description="Verifique erros no Monitor.",
            action="Ver monitor",
            action_url="/monitor",
            related_job_id=job_id,
        )
        return {"status": "created", "notification": {"id": notification.id}}
