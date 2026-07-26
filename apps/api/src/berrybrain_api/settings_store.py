from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
from typing import Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from berrybrain_api.config import get_settings
from berrybrain_api.models import SettingRecord

ENCRYPTED_SETTING_KEYS = {"ai_api_key", "graph_ai_api_key"}
_ENCRYPTION_PREFIX = "bbenc:v1:"
SECRET_SETTING_KEYS = ENCRYPTED_SETTING_KEYS
ENCRYPTED_PREFIX = _ENCRYPTION_PREFIX


def _secret_key() -> bytes:
    secret = get_settings().session_secret or os.getenv("BERRYBRAIN_SESSION_SECRET", "")
    if not secret:
        secret = "berrybrain-local-settings-secret"
    return hashlib.sha256(secret.encode("utf-8")).digest()


def _b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _unb64(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def _keystream(key: bytes, nonce: bytes, length: int) -> bytes:
    blocks: list[bytes] = []
    counter = 0
    while sum(len(block) for block in blocks) < length:
        blocks.append(
            hmac.new(key, nonce + counter.to_bytes(4, "big"), hashlib.sha256).digest()
        )
        counter += 1
    return b"".join(blocks)[:length]


def encode_setting_value(key: str, value: str) -> str:
    if (
        key not in ENCRYPTED_SETTING_KEYS
        or value == ""
        or value.startswith(_ENCRYPTION_PREFIX)
    ):
        return value
    raw = value.encode("utf-8")
    nonce = secrets.token_bytes(16)
    secret_key = _secret_key()
    stream = _keystream(secret_key, nonce, len(raw))
    cipher = bytes(left ^ right for left, right in zip(raw, stream, strict=True))
    mac = hmac.new(secret_key, nonce + cipher, hashlib.sha256).digest()
    return f"{_ENCRYPTION_PREFIX}{_b64(nonce)}:{_b64(cipher)}:{_b64(mac)}"


def decode_setting_value(key: str, value: str) -> str:
    if key not in ENCRYPTED_SETTING_KEYS or not value.startswith(_ENCRYPTION_PREFIX):
        return value
    try:
        nonce_raw, cipher_raw, mac_raw = value[len(_ENCRYPTION_PREFIX) :].split(":", 2)
        nonce = _unb64(nonce_raw)
        cipher = _unb64(cipher_raw)
        mac = _unb64(mac_raw)
    except ValueError:
        return ""
    secret_key = _secret_key()
    expected = hmac.new(secret_key, nonce + cipher, hashlib.sha256).digest()
    if not hmac.compare_digest(mac, expected):
        return ""
    stream = _keystream(secret_key, nonce, len(cipher))
    raw = bytes(left ^ right for left, right in zip(cipher, stream, strict=True))
    return raw.decode("utf-8")


def settings_values(settings: list[SettingRecord]) -> dict[str, str]:
    return {row.key: decode_setting_value(row.key, row.value) for row in settings}


def migrate_secret_settings(session: Session) -> int:
    rows = list(
        session.execute(
            select(SettingRecord).where(SettingRecord.key.in_(ENCRYPTED_SETTING_KEYS))
        ).scalars()
    )
    migrated = 0
    for row in rows:
        if row.value and not row.value.startswith(_ENCRYPTION_PREFIX):
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
