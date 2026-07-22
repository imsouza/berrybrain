from __future__ import annotations

import base64
import hashlib
from typing import Any

from cryptography.fernet import Fernet, InvalidToken
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from berrybrain_api.models import SettingRecord


SECRET_SETTING_KEYS = {"ai_api_key", "graph_ai_api_key"}
ENCRYPTED_PREFIX = "enc:v1:"


def _secret_cipher() -> Fernet:
    from berrybrain_api.config import get_settings

    secret = get_settings().session_secret.encode("utf-8")
    key = base64.urlsafe_b64encode(
        hashlib.sha256(b"berrybrain.settings.v1\0" + secret).digest()
    )
    return Fernet(key)


def encode_setting_value(key: str, value: str) -> str:
    if (
        key not in SECRET_SETTING_KEYS
        or not value
        or value.startswith(ENCRYPTED_PREFIX)
    ):
        return value
    token = _secret_cipher().encrypt(value.encode("utf-8")).decode("ascii")
    return f"{ENCRYPTED_PREFIX}{token}"


def decode_setting_value(key: str, value: str | None) -> str:
    raw = value or ""
    if key not in SECRET_SETTING_KEYS or not raw.startswith(ENCRYPTED_PREFIX):
        return raw
    try:
        return (
            _secret_cipher()
            .decrypt(raw.removeprefix(ENCRYPTED_PREFIX).encode("ascii"))
            .decode("utf-8")
        )
    except (InvalidToken, UnicodeError, ValueError):
        return ""


def settings_values(settings: list[SettingRecord]) -> dict[str, str]:
    return {row.key: decode_setting_value(row.key, row.value) for row in settings}


def migrate_secret_settings(session: Session) -> int:
    rows = list(
        session.execute(
            select(SettingRecord).where(SettingRecord.key.in_(SECRET_SETTING_KEYS))
        ).scalars()
    )
    migrated = 0
    for row in rows:
        if row.value and not row.value.startswith(ENCRYPTED_PREFIX):
            row.value = encode_setting_value(row.key, row.value)
            migrated += 1
    if migrated:
        session.commit()
    return migrated


def set_setting(session: Session, key: str, value: str) -> SettingRecord:
    stored_value = encode_setting_value(key, value)
    setting = session.execute(
        select(SettingRecord).where(SettingRecord.key == key)
    ).scalar_one_or_none()
    if setting is None:
        setting = SettingRecord(key=key, value=stored_value)
        session.add(setting)
    else:
        setting.value = stored_value

    session.commit()
    session.refresh(setting)
    return setting


def get_setting(session: Session, key: str) -> SettingRecord:
    setting = session.execute(
        select(SettingRecord).where(SettingRecord.key == key)
    ).scalar_one_or_none()
    if setting is None:
        raise HTTPException(status_code=404, detail="Setting not found")
    return setting


def list_settings(session: Session) -> list[SettingRecord]:
    return list(
        session.execute(
            select(SettingRecord).order_by(SettingRecord.key.asc())
        ).scalars()
    )


def serialize_setting(setting: SettingRecord) -> dict[str, Any]:
    return {
        "id": setting.id,
        "key": setting.key,
        "value": decode_setting_value(setting.key, setting.value),
        "updated_at": setting.updated_at.isoformat() if setting.updated_at else None,
    }
