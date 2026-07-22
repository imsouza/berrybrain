from __future__ import annotations

import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from berrybrain_api.models import AutomationLogRecord
from berrybrain_api.redaction import redact_text, redact_value


def create_automation_log(
    session: Session,
    action_type: str,
    target_type: str,
    target_id: str,
    description: str,
    before_state: dict[str, Any],
    after_state: dict[str, Any],
    reversible: bool,
    autocommit: bool = True,
) -> AutomationLogRecord:
    log = AutomationLogRecord(
        action_type=action_type,
        target_type=target_type,
        target_id=target_id,
        description=redact_text(description),
        before_state=compact_json(redact_value(before_state)),
        after_state=compact_json(redact_value(after_state)),
        reversible=1 if reversible else 0,
    )
    session.add(log)
    if autocommit:
        session.commit()
        session.refresh(log)
    else:
        session.flush()
    return log


def list_automation_logs(
    session: Session, limit: int = 50
) -> list[AutomationLogRecord]:
    return list(
        session.execute(
            select(AutomationLogRecord)
            .order_by(
                AutomationLogRecord.created_at.desc(), AutomationLogRecord.id.desc()
            )
            .limit(limit)
        ).scalars()
    )


def serialize_automation_log(log: AutomationLogRecord) -> dict[str, Any]:
    return {
        "id": log.id,
        "action_type": log.action_type,
        "target_type": log.target_type,
        "target_id": log.target_id,
        "description": log.description,
        "before_state": parse_json(log.before_state),
        "after_state": parse_json(log.after_state),
        "reversible": bool(log.reversible),
        "reverted_at": log.reverted_at.isoformat() if log.reverted_at else None,
        "reverted_by_log_id": log.reverted_by_log_id,
        "created_at": log.created_at.isoformat() if log.created_at else None,
    }


def compact_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def parse_json(value: str) -> Any:
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return {}
