import unittest
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from berrybrain_api.ai_configuration import (
    AIConfiguration,
    HippoRagSlot,
    JudgeSlot,
    ModelSlot,
    save_configuration,
)
from berrybrain_api.ask_flow import (
    append_ask_turn,
    cancel_ask_session,
    close_ask_session,
    create_ask_session,
    create_insight_from_flow_session,
    get_ask_session_payload,
)
from berrybrain_api.database import Base
from berrybrain_api.models import GraphInferenceRecord, InsightRecord


class AskFlowTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.engine = create_engine(
            "sqlite:///:memory:", connect_args={"check_same_thread": False}
        )
        Base.metadata.create_all(bind=self.engine)
        self.session = sessionmaker(bind=self.engine)()
        save_configuration(
            self.session,
            AIConfiguration(
                mode="local",
                main=ModelSlot(provider_id="ollama", model_id="main"),
                embedding=ModelSlot(provider_id="ollama", model_id="embed"),
                judge=JudgeSlot(provider_id="ollama", model_id="judge"),
                hipporag=HippoRagSlot(provider_id="ollama", model_id="rag"),
                endpoint_url="http://ollama:11434",
            ),
            validated=True,
        )

    def tearDown(self) -> None:
        self.session.close()
        self.engine.dispose()

    async def test_turns_are_persisted_and_restored_in_sequence(self) -> None:
        flow = create_ask_session(self.session)
        answer = AsyncMock(
            return_value={
                "answer": "Docker isolates the API and Worker processes.",
                "evidence": [{"nodeId": 7}],
                "provider": "local",
                "model": "main",
            }
        )
        with patch("berrybrain_api.ask_flow.answer_cognitive_query", answer):
            await append_ask_turn(self.session, flow.id, "How is Docker used?")

        payload = get_ask_session_payload(self.session, flow.id)
        self.assertEqual(
            [turn["role"] for turn in payload["turns"]], ["user", "assistant"]
        )
        self.assertEqual(payload["turns"][1]["evidenceIds"], ["7"])
        self.assertTrue(payload["session"]["active"])

    async def test_sessions_are_isolated_and_can_be_closed(self) -> None:
        first = create_ask_session(self.session, title="First")
        second = create_ask_session(self.session, title="Second")
        answer = AsyncMock(return_value={"answer": "Grounded answer.", "evidence": []})
        with patch("berrybrain_api.ask_flow.answer_cognitive_query", answer):
            await append_ask_turn(self.session, first.id, "Only in first")
        close_ask_session(self.session, first.id)

        first_payload = get_ask_session_payload(self.session, first.id)
        second_payload = get_ask_session_payload(self.session, second.id)
        self.assertFalse(first_payload["session"]["active"])
        self.assertEqual(len(first_payload["turns"]), 2)
        self.assertEqual(second_payload["turns"], [])

    async def test_session_can_continue_from_a_graph_inference(self) -> None:
        inference = GraphInferenceRecord(
            question="What does the graph show?",
            answer="The graph links Docker to the API.",
            status="ok",
            evidence='[{"nodeId": 7}]',
            provider="ollama",
            model="main",
        )
        self.session.add(inference)
        self.session.commit()

        flow = create_ask_session(self.session, inference_id=inference.id)
        payload = get_ask_session_payload(self.session, flow.id)

        self.assertEqual(
            [turn["content"] for turn in payload["turns"]],
            [inference.question, inference.answer],
        )
        self.assertEqual(payload["turns"][1]["evidenceIds"], ["7"])

    async def test_flow_answer_can_be_saved_as_insight(self) -> None:
        flow = create_ask_session(self.session)
        answer = AsyncMock(
            return_value={
                "status": "answered",
                "answer": "Docker and the API connect through local automation.",
                "evidence": [{"nodeId": 7}],
                "provider": "local",
                "model": "main",
            }
        )
        with patch("berrybrain_api.ask_flow.answer_cognitive_query", answer):
            await append_ask_turn(
                self.session, flow.id, "How does Docker connect to the API?"
            )

        result = create_insight_from_flow_session(self.session, flow.id)

        self.assertEqual(result["status"], "created")
        self.assertIsNotNone(result["insight"]["id"])
        self.assertIsNotNone(self.session.get(InsightRecord, result["insight"]["id"]))
        inference = (
            self.session.query(GraphInferenceRecord)
            .filter_by(insight_id=result["insight"]["id"])
            .one()
        )
        self.assertGreater(inference.confidence_sample_size, 0)
        self.assertEqual(inference.confidence_method, "jeffreys-wilson-evidence-v2")

    async def test_cancelled_turn_does_not_persist_provider_answer(self) -> None:
        flow = create_ask_session(self.session)

        async def cancel_during_provider_call(*_args, **_kwargs):
            cancel_ask_session(self.session, flow.id)
            return {"answer": "This answer must be discarded.", "evidence": []}

        with (
            patch(
                "berrybrain_api.ask_flow.answer_cognitive_query",
                side_effect=cancel_during_provider_call,
            ),
            self.assertRaisesRegex(HTTPException, "cancelled"),
        ):
            await append_ask_turn(self.session, flow.id, "Cancel this turn")

        payload = get_ask_session_payload(self.session, flow.id)
        self.assertEqual(len(payload["turns"]), 1)
        self.assertEqual(payload["turns"][0]["status"], "cancelled")

    async def test_provider_failure_does_not_persist_assistant_answer(self) -> None:
        flow = create_ask_session(self.session)
        answer = AsyncMock(
            return_value={
                "status": "waiting_provider",
                "answer": "",
                "evidence": [{"nodeId": 7}],
            }
        )

        with (
            patch("berrybrain_api.ask_flow.answer_cognitive_query", answer),
            self.assertRaises(HTTPException) as raised,
        ):
            await append_ask_turn(self.session, flow.id, "Retry this question")

        self.assertEqual(raised.exception.status_code, 503)
        self.assertEqual(raised.exception.detail["code"], "provider_unavailable")
        payload = get_ask_session_payload(self.session, flow.id)
        self.assertEqual(len(payload["turns"]), 1)
        self.assertEqual(payload["turns"][0]["status"], "failed")
