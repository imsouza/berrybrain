import unittest
from unittest.mock import AsyncMock, patch

from fastapi import BackgroundTasks
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from berrybrain_api.database import Base
from berrybrain_api.models import (
    GraphEdgeRecord,
    GraphNodeRecord,
    SemanticClusterRecord,
)
from berrybrain_api.routers.ask import get_suggestions


class AskSuggestionsTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.engine = create_engine(
            "sqlite:///:memory:", connect_args={"check_same_thread": False}
        )
        Base.metadata.create_all(bind=self.engine)
        self.factory = sessionmaker(bind=self.engine)

    def tearDown(self) -> None:
        self.engine.dispose()

    async def test_empty_graph_returns_no_suggestions(self) -> None:
        with patch("berrybrain_api.routers.ask.SessionLocal", self.factory):
            result = await get_suggestions(BackgroundTasks(), limit=10)

        self.assertEqual(result["questions"], [])
        self.assertEqual(result["topics"], [])
        self.assertEqual(result["graph"], {"nodes": 0, "edges": 0})

    async def test_single_graph_node_still_provides_a_full_grounded_queue(self) -> None:
        with self.factory() as session:
            session.add(
                GraphNodeRecord(
                    type="note",
                    label="Forecasting notes",
                    status="confirmed",
                    semantic_status="active",
                )
            )
            session.commit()

        with patch("berrybrain_api.routers.ask.SessionLocal", self.factory):
            result = await get_suggestions(BackgroundTasks(), limit=16)

        self.assertGreaterEqual(len(result["questions"]), 5)
        self.assertTrue(
            all("Forecasting notes" in item["prompt"] for item in result["questions"])
        )
        self.assertTrue(all(item["nodeIds"] for item in result["questions"]))

    async def test_suggestions_are_derived_from_live_graph_artifacts(self) -> None:
        with self.factory() as session:
            cluster = SemanticClusterRecord(
                stable_key="distributed-systems",
                label="Distributed systems",
                status="active",
            )
            session.add(cluster)
            session.flush()
            note = GraphNodeRecord(
                type="note",
                label="Observability notes",
                status="confirmed",
                semantic_status="active",
                cluster_id=cluster.id,
                quality_gate_status="passed",
            )
            concept = GraphNodeRecord(
                type="concept",
                label="Time series",
                status="confirmed",
                semantic_status="active",
                cluster_id=cluster.id,
                quality_gate_status="passed",
            )
            gap = GraphNodeRecord(
                type="gap",
                label="Missing retention policy",
                status="suggested",
                semantic_status="active",
                created_by="ai",
                quality_gate_status="passed",
            )
            session.add_all([note, concept, gap])
            session.flush()
            session.add(
                GraphEdgeRecord(
                    source_node_id=note.id,
                    target_node_id=concept.id,
                    type="about",
                    status="confirmed",
                    quality_gate_status="passed",
                )
            )
            session.commit()
            concept_id = concept.id
            gap_id = gap.id

        generate = AsyncMock(
            return_value={
                "questions": [
                    {
                        "prompt": "What evidence connects Time series to Observability notes?",
                        "topic": "Time series",
                        "node_ids": [concept_id],
                        "intent": "graph_structure",
                    },
                    {
                        "prompt": "Which evidence could resolve Missing retention policy?",
                        "topic": "Missing retention policy",
                        "node_ids": [gap_id],
                        "intent": "gap",
                    },
                    {
                        "prompt": "What invented node should I inspect?",
                        "topic": "Invented",
                        "node_ids": [999999],
                        "intent": "graph_content",
                    },
                ],
                "topics": ["Distributed systems", "Time series", "Invented"],
            }
        )
        with (
            patch("berrybrain_api.routers.ask.SessionLocal", self.factory),
            patch("berrybrain_api.routers.ask.get_ai_config", return_value={}),
            patch("berrybrain_api.routers.ask.generate_graph_answer", generate),
        ):
            background_tasks = BackgroundTasks()
            initial = await get_suggestions(background_tasks, limit=10)
            await background_tasks()
            result = await get_suggestions(BackgroundTasks(), limit=10)

        prompts = " ".join(item["prompt"] for item in result["questions"])
        self.assertEqual(initial["generation"], "graph_context")
        self.assertIn("Missing retention policy", prompts)
        self.assertIn("Time series", prompts)
        self.assertNotIn("invented node", prompts)
        self.assertIn("Distributed systems", result["topics"])
        self.assertNotIn("Invented", result["topics"])
        self.assertEqual(result["graph"]["nodes"], 3)
        self.assertEqual(result["graph"]["edges"], 1)
        self.assertIn("ai_gap", {item["source"] for item in result["questions"]})
        self.assertEqual(result["generation"], "cached_ai")
        generate.assert_awaited_once()

    async def test_provider_failure_recovers_with_live_graph_questions(self) -> None:
        with self.factory() as session:
            first = GraphNodeRecord(
                type="concept",
                label="Event sourcing",
                status="confirmed",
                semantic_status="active",
                quality_gate_status="passed",
            )
            second = GraphNodeRecord(
                type="entity",
                label="Order service",
                status="confirmed",
                semantic_status="active",
                quality_gate_status="passed",
            )
            session.add_all([first, second])
            session.flush()
            session.add(
                GraphEdgeRecord(
                    source_node_id=first.id,
                    target_node_id=second.id,
                    type="implemented_by",
                    status="confirmed",
                    quality_gate_status="passed",
                )
            )
            session.commit()

        with (
            patch("berrybrain_api.routers.ask.SessionLocal", self.factory),
            patch("berrybrain_api.routers.ask.get_ai_config", return_value={}),
            patch(
                "berrybrain_api.routers.ask.generate_graph_answer",
                AsyncMock(side_effect=RuntimeError("provider unavailable")),
            ),
        ):
            background_tasks = BackgroundTasks()
            result = await get_suggestions(background_tasks, limit=16)
            await background_tasks()

        self.assertEqual(result["generation"], "graph_context")
        self.assertGreaterEqual(len(result["questions"]), 5)
        self.assertTrue(
            all(item["source"] == "graph_context" for item in result["questions"])
        )
        prompts = " ".join(item["prompt"] for item in result["questions"])
        self.assertIn("Event sourcing", prompts)
        self.assertIn("Order service", prompts)
        self.assertIn("implemented by", prompts)


if __name__ == "__main__":
    unittest.main()
