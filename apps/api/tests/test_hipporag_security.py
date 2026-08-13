import unittest
from unittest.mock import patch

from berrybrain_api.config import Settings
from berrybrain_api.routers import hipporag
from berrybrain_api.routers.ai_configuration import _probe_judge_models


class HippoRagSecurityTest(unittest.TestCase):
    @patch("berrybrain_api.ai_gateway._cloud_json")
    def test_judge_probe_keeps_only_structured_compatible_models(self, generate):
        def response(configuration, *_args):
            if configuration["cloud_model"] == "stale-model":
                raise ValueError("unsupported")
            return {"probe": True}

        generate.side_effect = response

        models = _probe_judge_models(
            "nvidia-nim",
            "https://provider.example/v1",
            "secret",
            ["stale-model", "working-model"],
            required=1,
        )

        self.assertEqual(models, ["working-model"])

    def test_prefixed_runtime_configuration_reaches_the_sidecar(self) -> None:
        with patch.dict(
            "os.environ",
            {
                "BERRYBRAIN_HIPPORAG_URL": "http://hipporag:8000",
                "BERRYBRAIN_HIPPORAG_SERVICE_TOKEN": "service-token",
            },
        ):
            settings = Settings(_env_file=None)

        self.assertEqual(settings.hipporag_url, "http://hipporag:8000")
        self.assertEqual(settings.hipporag_service_token, "service-token")

    def test_sync_does_not_return_exception_details(self) -> None:
        result = hipporag._sync_failure("Research/private-note.md")

        self.assertEqual(
            result,
            {
                "path": "Research/private-note.md",
                "code": "sidecar_request_failed",
            },
        )


if __name__ == "__main__":
    unittest.main()
