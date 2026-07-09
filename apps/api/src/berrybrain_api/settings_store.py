from __future__ import annotations

from typing import Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from berrybrain_api.models import SettingRecord


def set_setting(session: Session, key: str, value: str) -> SettingRecord:
    setting = session.execute(select(SettingRecord).where(SettingRecord.key == key)).scalar_one_or_none()
    if setting is None:
        setting = SettingRecord(key=key, value=value)
        session.add(setting)
    else:
        setting.value = value

    session.commit()
    session.refresh(setting)
    return setting


def get_setting(session: Session, key: str) -> SettingRecord:
    setting = session.execute(select(SettingRecord).where(SettingRecord.key == key)).scalar_one_or_none()
    if setting is None:
        raise HTTPException(status_code=404, detail="Setting not found")
    return setting


def list_settings(session: Session) -> list[SettingRecord]:
    return list(session.execute(select(SettingRecord).order_by(SettingRecord.key.asc())).scalars())


def serialize_setting(setting: SettingRecord) -> dict[str, Any]:
    return {
        "id": setting.id,
        "key": setting.key,
        "value": setting.value,
        "updated_at": setting.updated_at.isoformat() if setting.updated_at else None,
    }
