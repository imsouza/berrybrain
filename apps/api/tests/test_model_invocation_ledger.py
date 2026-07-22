import asyncio
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from berrybrain_api.ai_gateway import GraphAIUnavailable, generate_graph_answer
from berrybrain_api.database import Base
from berrybrain_api.models import ModelInvocationRecord
from berrybrain_api.model_invocation_service import (
    ModelInvocationHandle,
    _safe_error_message,
    finish_model_invocation,
    start_model_invocation,
)


class ModelInvocationLedgerTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        path = Path(self.tmp.name) / "ledger.db"
        self.engine = create_engine(
            f"sqlite:///{path}", connect_args={"check_same_thread": False}
        )
        Base.metadata.create_all(self.engine)
        self.session = sessionmaker(bind=self.engine)()
        self.config = {
            "provider": "local",
            "ollama_base_url": "http://ollama.test",
            "ollama_model": "qwen",
        }

    def tearDown(self) -> None:
        self.session.close()
        self.engine.dispose()
        self.tmp.cleanup()

    async def test_success_records_provenance_without_prompt_content(self) -> None:
        secret_prompt = "private note content that must never be persisted"
        with patch(
            "berrybrain_api.ai_gateway._ollama_json",
            return_value={"answer": "grounded"},
        ):
            result = await generate_graph_answer(
                self.config,
                secret_prompt,
                "system evidence policy",
                session=self.session,
                prompt_version="ledger-test.v1",
                correlation_id="test:success",
            )

        self.assertEqual(result, {"answer": "grounded"})
        record = self.session.execute(select(ModelInvocationRecord)).scalar_one()
        self.assertEqual(record.status, "completed")
        self.assertEqual(record.capability, "graph_inference")
        self.assertEqual(record.provider, "local")
        self.assertEqual(record.model, "qwen")
        self.assertEqual(record.prompt_version, "ledger-test.v1")
        self.assertGreater(record.input_units, 0)
        self.assertGreater(record.output_units, 0)
        self.assertNotIn(secret_prompt, repr(record.__dict__))

    async def test_failure_is_sanitized_and_persisted(self) -> None:
        leaked_key = "nvapi-super-secret-value"
        with patch(
            "berrybrain_api.ai_gateway._ollama_json",
            side_effect=GraphAIUnavailable(f"provider rejected {leaked_key}"),
        ):
            with self.assertRaises(GraphAIUnavailable):
                await generate_graph_answer(
                    self.config,
                    "question",
                    "system",
                    session=self.session,
                    prompt_version="ledger-failure.v1",
                )

        record = self.session.execute(select(ModelInvocationRecord)).scalar_one()
        self.assertEqual(record.status, "failed")
        self.assertEqual(record.error_class, "GraphAIUnavailable")
        self.assertNotIn(leaked_key, record.error_message)
        self.assertIn("[REDACTED]", record.error_message)

    async def test_routing_failure_is_recorded(self) -> None:
        with self.assertRaisesRegex(GraphAIUnavailable, "explicit consent"):
            await generate_graph_answer(
                {
                    "provider": "cloud",
                    "cloud_api_url": "https://provider.test/v1",
                    "cloud_api_key": "nvapi-not-persisted",
                    "cloud_model": "reasoner",
                    "remote_content_consent": "false",
                },
                "private evidence",
                "system",
                session=self.session,
            )

        record = self.session.execute(select(ModelInvocationRecord)).scalar_one()
        self.assertEqual(record.status, "failed")
        self.assertEqual(record.provider, "cloud")
        self.assertTrue(record.remote)

    async def test_cancellation_is_recorded(self) -> None:
        started = asyncio.Event()

        async def blocked_call(*_args):
            started.set()
            await asyncio.Event().wait()

        with patch("berrybrain_api.ai_gateway._to_thread", side_effect=blocked_call):
            task = asyncio.create_task(
                generate_graph_answer(
                    self.config,
                    "question",
                    "system",
                    session=self.session,
                    prompt_version="cancel-test.v1",
                )
            )
            await started.wait()
            task.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await task

        record = self.session.execute(select(ModelInvocationRecord)).scalar_one()
        self.assertEqual(record.status, "cancelled")

    async def test_retry_count_is_persisted(self) -> None:
        with (
            patch(
                "berrybrain_api.ai_gateway._ollama_json",
                side_effect=[TimeoutError("slow"), {"answer": "recovered"}],
            ),
            patch("berrybrain_api.ai_gateway.time.sleep"),
        ):
            await generate_graph_answer(
                self.config,
                "question",
                "system",
                session=self.session,
                prompt_version="retry-ledger.v1",
            )

        record = self.session.execute(select(ModelInvocationRecord)).scalar_one()
        self.assertEqual(record.status, "completed")
        self.assertEqual(record.attempt_count, 2)

    def test_ledger_failure_never_breaks_cognitive_work(self) -> None:
        with patch(
            "berrybrain_api.model_invocation_service._ledger_session",
            side_effect=RuntimeError("database unavailable"),
        ):
            handle = start_model_invocation(
                self.session,
                capability="graph_inference",
                provider="local",
                model="qwen",
                prompt_version="failure-test.v1",
                remote=False,
                input_units=10,
            )
            self.assertIsNone(handle)
            finish_model_invocation(
                ModelInvocationHandle(999, self.engine),
                status="failed",
                latency_ms=1,
            )

    def test_missing_record_and_error_categories_are_safe(self) -> None:
        finish_model_invocation(
            ModelInvocationHandle(999, self.engine),
            status="failed",
            latency_ms=1,
        )
        self.assertIn("invalid structured", _safe_error_message(ValueError("raw")))
        http_error = urllib.error.HTTPError(
            "https://provider.test", 503, "Unavailable", None, None
        )
        self.assertEqual(
            _safe_error_message(http_error), "The provider returned HTTP 503."
        )
        self.assertEqual(
            _safe_error_message(RuntimeError("private note text")),
            "The model invocation failed. See the error class and provider logs.",
        )


if __name__ == "__main__":
    unittest.main()
