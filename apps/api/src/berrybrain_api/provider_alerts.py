"""Model-availability notifications from observed, persisted provider failures.

No inference probes, automatic provider changes, or guessed catalogue removals.
"""

import re
from datetime import UTC

from sqlalchemy import select
from sqlalchemy.orm import Session

from berrybrain_api.ai_configuration import load_configuration
from berrybrain_api.models import ModelInvocationRecord

UNAVAILABLE_MODEL = re.compile(
    r"model[_ -]not[_ -]found|unknown model|invalid model|"
    r"model.{0,120}(?:not found|does not exist|no longer|retired|deprecated|unavailable|not available|not supported)|"
    r"(?:404|410).{0,120}model|does not provide chat",
    re.IGNORECASE,
)


def model_availability_alerts(session: Session) -> list[dict]:
    configuration = load_configuration(session)
    if configuration is None:
        return []
    alerts = []
    seen = set()
    # Bound the read by insertion order. Historical ledgers store 'cloud' rather
    # than a vendor ID, so do not attribute events predating validated settings.
    recent = session.execute(
        select(
            ModelInvocationRecord.model,
            ModelInvocationRecord.provider,
            ModelInvocationRecord.status,
            ModelInvocationRecord.error_class,
            ModelInvocationRecord.error_message,
            ModelInvocationRecord.started_at,
            ModelInvocationRecord.completed_at,
        )
        .order_by(ModelInvocationRecord.id.desc())
        .limit(1000)
    ).all()
    for role in ("main", "embedding", "judge", "hipporag"):
        slot = getattr(configuration, role)
        if not getattr(slot, "enabled", True) or not slot.model_id:
            continue
        key = (slot.provider_id, slot.model_id)
        if key in seen:
            continue
        seen.add(key)
        # Narrow terminal history; no prompts, answers or raw provider errors
        # are returned in notifications. A later successful call clears it.
        latest = next(
            (
                item
                for item in recent
                if item.model == slot.model_id
                and item.status in {"completed", "failed"}
                and item.provider in {slot.provider_id, configuration.mode}
            ),
            None,
        )
        if latest is None or latest.status != "failed":
            continue
        if configuration.validated_at and latest.started_at.replace(
            tzinfo=UTC
        ) < configuration.validated_at.astimezone(UTC):
            continue
        if not UNAVAILABLE_MODEL.search(
            f"{latest.error_class or ''} {latest.error_message or ''}"
        ):
            continue
        alerts.append(
            {
                "kind": "model_unavailable",
                "provider": slot.provider_id,
                "model": slot.model_id,
                "role": role,
                "action": "settings",
                "title": f"Model unavailable: {slot.model_id}",
                "description": f"The provider rejected the configured {role} model. It may have been removed or access changed. Review AI setup; no model was changed automatically.",
                "observedAt": (latest.completed_at or latest.started_at).isoformat(),
            }
        )
    return alerts
