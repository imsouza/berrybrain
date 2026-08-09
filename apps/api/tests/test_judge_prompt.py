import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import HTTPException

from berrybrain_api.routers import judge


class JudgePromptTest(unittest.TestCase):
    def test_routes_canonical_provider_id_through_its_mode(self) -> None:
        routed = judge._with_judge_route(
            {
                "provider": "cloud",
                "judge_provider": "nvidia-nim",
                "judge_model": "judge-model",
            }
        )

        self.assertEqual(routed["provider"], "cloud")
        self.assertEqual(routed["cloud_model"], "judge-model")

    def test_rejects_mixed_judge_mode(self) -> None:
        with self.assertRaisesRegex(ValueError, "cannot mix"):
            judge._with_judge_route(
                {
                    "provider": "cloud",
                    "judge_provider": "ollama",
                    "judge_model": "local-judge",
                }
            )

    def test_loads_the_versioned_prompt_from_project_root(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            prompt_dir = Path(root) / "prompts"
            prompt_dir.mkdir()
            (prompt_dir / "artifact-judge.v1.md").write_text(
                "Evaluate the artifact.", encoding="utf-8"
            )
            with patch.object(judge, "PROJECT_ROOT", Path(root)):
                self.assertEqual(judge._load_judge_prompt(), "Evaluate the artifact.")

    def test_missing_prompt_is_a_retryable_service_failure(self) -> None:
        with (
            tempfile.TemporaryDirectory() as root,
            patch.object(judge, "PROJECT_ROOT", Path(root)),
            self.assertRaises(HTTPException) as error,
        ):
            judge._load_judge_prompt()

        self.assertEqual(error.exception.status_code, 503)


if __name__ == "__main__":
    unittest.main()
