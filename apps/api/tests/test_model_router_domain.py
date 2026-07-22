import unittest

from berrybrain_api.modules.model_router.domain import (
    ModelCapability,
    ModelRoutingError,
    ProviderPolicy,
    select_model_route,
)


class ModelRouterDomainTest(unittest.TestCase):
    def test_local_first_route_is_explicit(self) -> None:
        decision = select_model_route(
            ModelCapability.GRAPH_INFERENCE,
            ProviderPolicy(
                preferred_provider="local",
                remote_content_consent=False,
                cloud_configured=False,
                local_configured=True,
            ),
            local_model="qwen3",
        )
        self.assertEqual(decision.provider, "local")
        self.assertEqual(decision.model, "qwen3")
        self.assertFalse(decision.remote)

    def test_cloud_route_requires_consent_and_complete_configuration(self) -> None:
        base = {
            "preferred_provider": "cloud",
            "cloud_configured": True,
            "local_configured": True,
        }
        with self.assertRaisesRegex(
            ModelRoutingError, "remote_content_consent_required"
        ):
            select_model_route(
                ModelCapability.KNOWLEDGE_INSIGHT,
                ProviderPolicy(remote_content_consent=False, **base),
                cloud_model="remote-model",
                local_model="local-model",
            )
        with self.assertRaisesRegex(ModelRoutingError, "cloud_provider_not_configured"):
            select_model_route(
                ModelCapability.KNOWLEDGE_INSIGHT,
                ProviderPolicy(
                    preferred_provider="cloud",
                    remote_content_consent=True,
                    cloud_configured=False,
                    local_configured=True,
                ),
                cloud_model="remote-model",
                local_model="local-model",
            )

    def test_unknown_or_incomplete_local_provider_fails_closed(self) -> None:
        with self.assertRaisesRegex(ModelRoutingError, "unsupported_provider"):
            select_model_route(
                ModelCapability.EMBEDDING,
                ProviderPolicy("unknown", True, True, True),
                cloud_model="remote",
                local_model="local",
            )
        with self.assertRaisesRegex(ModelRoutingError, "local_provider_not_configured"):
            select_model_route(
                ModelCapability.EMBEDDING,
                ProviderPolicy("local", False, False, False),
            )


if __name__ == "__main__":
    unittest.main()
