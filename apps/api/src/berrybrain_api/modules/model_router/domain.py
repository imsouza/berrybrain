from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ModelCapability(StrEnum):
    GRAPH_INFERENCE = "graph_inference"
    KNOWLEDGE_INSIGHT = "knowledge_insight"
    NODE_ENRICHMENT = "node_enrichment"
    EMBEDDING = "embedding"


@dataclass(frozen=True, slots=True)
class ProviderPolicy:
    preferred_provider: str
    remote_content_consent: bool
    cloud_configured: bool
    local_configured: bool


@dataclass(frozen=True, slots=True)
class RoutingDecision:
    capability: ModelCapability
    provider: str
    model: str
    reason: str
    remote: bool


class ModelRoutingError(ValueError):
    pass


def select_model_route(
    capability: ModelCapability,
    policy: ProviderPolicy,
    *,
    cloud_model: str = "",
    local_model: str = "",
) -> RoutingDecision:
    preferred = (policy.preferred_provider or "local").strip().lower()
    if preferred == "cloud":
        if not policy.remote_content_consent:
            raise ModelRoutingError("remote_content_consent_required")
        if not policy.cloud_configured or not cloud_model.strip():
            raise ModelRoutingError("cloud_provider_not_configured")
        return RoutingDecision(
            capability=capability,
            provider="cloud",
            model=cloud_model.strip(),
            reason="explicit_cloud_preference",
            remote=True,
        )
    if preferred not in {"local", "ollama"}:
        raise ModelRoutingError("unsupported_provider")
    if not policy.local_configured or not local_model.strip():
        raise ModelRoutingError("local_provider_not_configured")
    return RoutingDecision(
        capability=capability,
        provider="local",
        model=local_model.strip(),
        reason="local_first_policy",
        remote=False,
    )
