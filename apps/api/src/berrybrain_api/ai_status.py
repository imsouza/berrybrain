"""Read-only status shared by Home and Settings; never runs a provider probe."""

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from berrybrain_api.ai_configuration import (
    configuration_gate,
    load_configuration,
    provider_endpoint,
)


def saved_test_status(session: Session, values: dict[str, str]) -> tuple[str, str]:
    url = (values.get("ai_api_url") or values.get("ai_custom_url") or "").rstrip("/")
    model = values.get("ai_model", "")
    revision = values.get("ai_key_revision", "")
    legacy_matches = (
        values.get("ai_last_test_url", "").rstrip("/") == url
        and values.get("ai_last_test_key_revision", "") == revision
        and values.get("ai_last_test_model", "") == model
        and values.get("ai_last_test_method") == "chat_completions"
    )
    status = (
        values.get("ai_last_test_status", "untested") if legacy_matches else "untested"
    )
    tested_at = values.get("ai_last_test_at", "") if legacy_matches else ""
    configuration = load_configuration(session)
    if (
        configuration is not None
        and configuration.mode == "cloud"
        and values.get("ai_provider") == "cloud"
        and configuration.main.model_id == model
        and provider_endpoint(configuration, configuration.main.provider_id).rstrip("/")
        == url
        and configuration_gate(session)["valid"]
        and configuration.validated_at is not None
    ):
        validated_at = configuration.validated_at
        validated_at = (
            validated_at.replace(tzinfo=UTC)
            if validated_at.tzinfo is None
            else validated_at.astimezone(UTC)
        )
        # Do not conceal a subsequent failed explicit connection test.
        try:
            legacy_at = datetime.fromisoformat(tested_at.replace("Z", "+00:00"))
            legacy_at = (
                legacy_at.replace(tzinfo=UTC) if legacy_at.tzinfo is None else legacy_at
            )
        except ValueError:
            legacy_at = None
        if legacy_at is None or legacy_at < validated_at:
            return "connected", validated_at.isoformat()
    return status, tested_at
