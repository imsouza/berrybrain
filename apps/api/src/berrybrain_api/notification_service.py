from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from berrybrain_api.models import NotificationRecord


def create_notification(
    session: Session,
    *,
    notification_type: str,
    title: str,
    description: str,
    action: str,
    action_url: str | None = None,
    related_insight_id: int | None = None,
    related_job_id: int | None = None,
) -> NotificationRecord:
    existing = session.execute(
        select(NotificationRecord).where(
            NotificationRecord.type == notification_type,
            NotificationRecord.related_insight_id == related_insight_id,
            NotificationRecord.related_job_id == related_job_id,
            NotificationRecord.read_at.is_(None),
        )
    ).scalar_one_or_none()
    if existing is not None:
        existing.title = title
        existing.description = description
        existing.action = action
        existing.action_url = action_url
        session.flush()
        return existing

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
    session.flush()
    return notification
