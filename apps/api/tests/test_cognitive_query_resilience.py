from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from berrybrain_api.cognitive_layer import (
    _bounded_query_evidence,
    answer_cognitive_query,
)
from berrybrain_api.cognitive_query import RetrievalEvidence, _rrf
from berrybrain_api.config import Settings
from berrybrain_api.database import Base
from berrybrain_api.models import NoteRecord
from berrybrain_api.vault import create_note


def _retrieval() -> dict:
    return {
        "routes": ["knowledge_base", "knowledge_graph"],
        "evidence": [
            {
                "source": "knowledge_base",
                "title": "Docker Essentials",
                "text": "Docker and shell automation are connected. " * 100,
                "score": 0.9,
                "metadata": {"notePath": "inbox/docker.md", "noteId": 1},
            }
        ],
        "relatedNodes": [{"id": 1, "label": "Docker Essentials"}],
        "semanticState": {},
    }


class CognitiveQueryResilienceTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        settings = Settings(_env_file=None, vault_path=Path(temporary.name) / "vault")
        configuration = patch(
            "berrybrain_api.config.get_settings", return_value=settings
        )
        configuration.start()
        self.addCleanup(configuration.stop)
        note = create_note(
            settings.vault_path, "Docker", "inbox", _retrieval()["evidence"][0]["text"]
        )
        engine = create_engine("sqlite:///:memory:")
        self.addCleanup(engine.dispose)
        Base.metadata.create_all(engine)
        self.session = Session(engine)
        self.addCleanup(self.session.close)
        self.session.add(
            NoteRecord(
                title="Docker Essentials",
                slug="docker",
                path=note["path"],
                content=note["content"],
                content_hash=note["content_hash"],
            )
        )
        self.session.commit()

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
            self.session, "How do Docker and shell connect?"
        )

        self.assertEqual(result["status"], "waiting_provider")
        self.assertEqual(result["answer"], "")
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
        _generate.return_value["evidence"] = [
            {
                "evidenceId": _bounded_query_evidence(
                    _retrieval()["evidence"],
                    question="How do Docker and shell connect?",
                )[0]["evidenceId"]
            }
        ]
        result = await answer_cognitive_query(
            self.session, "How do Docker and shell connect?"
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

    def test_rrf_merges_the_same_chunk_across_retrieval_routes(self) -> None:
        vector = RetrievalEvidence(
            source="knowledge_base",
            title="Docker Essentials",
            text="Vector result.",
            score=0.8,
            metadata={
                "noteId": 7,
                "chunk": 2,
                "retrieval": "qdrant_vector",
            },
        )
        lexical = RetrievalEvidence(
            source="knowledge_base",
            title="Docker Essentials",
            text="Lexical result.",
            score=0.9,
            metadata={
                "noteId": 7,
                "chunk": 2,
                "retrieval": "lexical_plus_metadata",
            },
        )

        fused = _rrf([vector], [lexical])

        self.assertEqual(len(fused), 1)
        self.assertEqual(fused[0].text, "Lexical result.")
        self.assertEqual(
            fused[0].metadata["retrievalRoutes"],
            ["qdrant_vector", "lexical_plus_metadata"],
        )
        self.assertEqual(fused[0].metadata["evidenceKey"], "note:7:chunk:2")
        self.assertAlmostEqual(fused[0].score, 2 / 61, places=6)

    def test_prompt_evidence_round_robins_across_sources(self) -> None:
        evidence = [
            {
                "title": "Note A first",
                "text": "alpha first",
                "metadata": {"noteId": 1, "chunk": 0},
            },
            {
                "title": "Note A second",
                "text": "alpha second",
                "metadata": {"noteId": 1, "chunk": 1},
            },
            {
                "title": "Note B first",
                "text": "beta first",
                "metadata": {"noteId": 2, "chunk": 0},
            },
        ]

        bounded = _bounded_query_evidence(evidence, question="alpha beta")

        self.assertEqual(
            [item["title"] for item in bounded],
            ["Note A first", "Note B first", "Note A second"],
        )
        self.assertEqual(len({item["evidenceId"] for item in bounded}), 3)
        self.assertEqual([item["queryTokenOverlap"] for item in bounded], [1, 1, 1])

    def test_prompt_evidence_rejects_invalid_limits(self) -> None:
        with self.assertRaisesRegex(ValueError, "Evidence limits must be positive"):
            _bounded_query_evidence([], limit=0)


if __name__ == "__main__":
    unittest.main()
