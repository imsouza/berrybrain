import unittest
from unittest.mock import patch

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from berrybrain_api.database import Base
from berrybrain_api.graph_inference_service import (
    create_insight_from_persisted_inference,
    persist_graph_inference,
)
from berrybrain_api.models import GraphInferenceRecord, InsightRecord, JobRecord


class GraphInferenceTransactionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.session = sessionmaker(bind=self.engine)()

    def tearDown(self) -> None:
        self.session.close()
        self.engine.dispose()

    def test_failed_outbox_write_rolls_back_insight_and_link(self) -> None:
        inference = persist_graph_inference(
            self.session,
            "How are deployment and automation connected?",
            {
                "status": "answered",
                "answer": "Deployment uses automation to make releases repeatable.",
                "evidence": ["Deployment note", "Automation note"],
                "routes": ["knowledge_graph"],
                "confidence": 0.82,
                "provider": "deterministic",
                "model": "transaction-fixture",
            },
        )

        with patch(
            "berrybrain_api.graph_inference_service.create_job",
            side_effect=RuntimeError("queue unavailable"),
        ):
            with self.assertRaisesRegex(RuntimeError, "queue unavailable"):
                create_insight_from_persisted_inference(self.session, inference.id)
        self.session.rollback()

        persisted = self.session.get(GraphInferenceRecord, inference.id)
        self.assertIsNotNone(persisted)
        self.assertIsNone(persisted.insight_id)
        self.assertIsNone(
            self.session.execute(select(InsightRecord)).scalar_one_or_none()
        )

    def test_projection_runs_only_through_durable_outbox_job(self) -> None:
        inference = persist_graph_inference(
            self.session,
            "How are containers and shell automation connected?",
            {
                "status": "answered",
                "answer": "Shell automation makes container operations repeatable.",
                "evidence": ["Containers note", "Shell automation note"],
                "routes": ["knowledge_graph"],
                "confidence": 0.81,
                "provider": "deterministic",
                "model": "projection-fixture",
            },
        )

        result = create_insight_from_persisted_inference(self.session, inference.id)

        self.assertEqual(result["status"], "created")
        self.assertEqual(result["graphUpdate"], "queued")
        self.assertIsNotNone(self.session.get(InsightRecord, result["insight"]["id"]))
        queued = self.session.execute(select(JobRecord)).scalars().all()
        self.assertEqual(len(queued), 1)
        self.assertEqual(queued[0].status, "pending")


if __name__ == "__main__":
    unittest.main()
