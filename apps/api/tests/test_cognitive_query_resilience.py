from __future__ import annotations

import unittest
from unittest.mock import AsyncMock, patch

from berrybrain_api.cognitive_layer import (
    _bounded_query_evidence,
    answer_cognitive_query,
)


def _retrieval() -> dict:
    return {
        "routes": ["knowledge_base", "knowledge_graph"],
        "evidence": [
            {
                "source": "knowledge_base",
                "title": "Docker Essentials",
                "text": "Docker and shell automation are connected. " * 100,
                "score": 0.9,
                "metadata": {"notePath": "docker.md"},
            }
        ],
        "relatedNodes": [{"id": 1, "label": "Docker Essentials"}],
        "semanticState": {},
    }


class CognitiveQueryResilienceTests(unittest.IsolatedAsyncioTestCase):
    @patch(
        "berrybrain_api.cognitive_layer.get_ai_config",
        return_value={"provider": "cloud"},
    )
    @patch(
        "berrybrain_api.cognitive_layer.orchestrate_retrieval",
        side_effect=lambda *_: _retrieval(),
    )
    @patch(
        "berrybrain_api.cognitive_layer.generate_graph_answer",
        new_callable=AsyncMock,
        side_effect=TimeoutError("provider timed out"),
    )
    async def test_provider_timeout_returns_grounded_fallback(
        self,
        generate: AsyncMock,
        _orchestrate,
        _config,
    ) -> None:
        result = await answer_cognitive_query(
            object(), "How do Docker and shell connect?"
        )

        self.assertEqual(result["status"], "waiting_provider")
        self.assertIn("80 seconds", result["reason"])
        self.assertTrue(result["evidence"])
        self.assertEqual(generate.await_args.kwargs["timeout"], 80)
        self.assertEqual(generate.await_args.kwargs["max_tokens"], 1024)

    @patch(
        "berrybrain_api.cognitive_layer.get_ai_config",
        return_value={"provider": "cloud"},
    )
    @patch(
        "berrybrain_api.cognitive_layer.orchestrate_retrieval",
        side_effect=lambda *_: _retrieval(),
    )
    @patch(
        "berrybrain_api.cognitive_layer.generate_graph_answer",
        new_callable=AsyncMock,
        return_value={
            "status": "answered",
            "answer": "Docker uses shell commands to automate container workflows.",
            "evidence": ["Docker Essentials"],
            "confidence": "high",
        },
    )
    async def test_invalid_model_confidence_cannot_crash_endpoint(
        self,
        _generate: AsyncMock,
        _orchestrate,
        _config,
    ) -> None:
        result = await answer_cognitive_query(
            object(), "How do Docker and shell connect?"
        )

        self.assertEqual(result["status"], "answered")
        self.assertEqual(result["confidence"], 0.5)

    def test_prompt_evidence_has_per_item_and_total_limits(self) -> None:
        evidence = [
            {"title": f"Note {index}", "text": "x" * 2000} for index in range(20)
        ]

        bounded = _bounded_query_evidence(evidence)

        self.assertLessEqual(len(bounded), 12)
        self.assertTrue(all(len(item["text"]) <= 1200 for item in bounded))
        self.assertLessEqual(sum(len(item["text"]) for item in bounded), 9000)


if __name__ == "__main__":
    unittest.main()
