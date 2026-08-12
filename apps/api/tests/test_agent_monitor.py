import unittest
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import patch

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker

from berrybrain_api.agent_monitor import ensure_agent_monitoring
from berrybrain_api.database import Base
from berrybrain_api.jobs import (
    ENRICH_GRAPH_NODE,
    GENERATE_GRAPH_INSIGHTS,
    UPDATE_GRAPH_CLUSTERS,
)
from berrybrain_api.models import GraphNodeRecord, JobRecord


class AgentMonitorTest(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine(
            "sqlite:///:memory:", connect_args={"check_same_thread": False}
        )
        Base.metadata.create_all(bind=self.engine)
        self.factory = sessionmaker(bind=self.engine)

    def tearDown(self) -> None:
        self.engine.dispose()

    def test_monitor_is_idle_without_graph_evidence(self) -> None:
        with self.factory() as session:
            result = ensure_agent_monitoring(session)
        self.assertEqual(result, {"status": "idle", "jobs": []})

    def test_monitor_schedules_due_work_once(self) -> None:
        with self.factory() as session:
            session.add(
                GraphNodeRecord(
                    type="concept",
                    label="Temporal database",
                    status="confirmed",
                    semantic_status="active",
                    semantic_state="pending",
                    created_by="ai",
                )
            )
            session.commit()

            configuration = SimpleNamespace(
                validated_at=datetime.now(UTC),
                configuration_fingerprint="test-configuration",
            )
            with patch(
                "berrybrain_api.agent_monitor.load_configuration",
                return_value=configuration,
            ):
                first = ensure_agent_monitoring(session)
                first_count = session.scalar(select(func.count(JobRecord.id)))
                second = ensure_agent_monitoring(session)
                second_count = session.scalar(select(func.count(JobRecord.id)))

                enrich_job = session.execute(
                    select(JobRecord).where(JobRecord.type == ENRICH_GRAPH_NODE)
                ).scalar_one()
                enrich_job.status = "dead_letter"
                enrich_job.completed_at = datetime.now(UTC)
                session.commit()
                third = ensure_agent_monitoring(session)
                third_count = session.scalar(select(func.count(JobRecord.id)))

            jobs = list(session.execute(select(JobRecord)).scalars())
            job_types = {job.type for job in jobs}
            enrich_job = next(job for job in jobs if job.type == ENRICH_GRAPH_NODE)

        self.assertEqual(first["ai"], "active")
        self.assertEqual(second["ai"], "active")
        self.assertEqual(first_count, second_count)
        self.assertEqual(third["ai"], "active")
        self.assertEqual(second_count, third_count)
        self.assertTrue(
            {
                ENRICH_GRAPH_NODE,
                GENERATE_GRAPH_INSIGHTS,
                "JUDGE_ARTIFACT",
                UPDATE_GRAPH_CLUSTERS,
            }.issubset(job_types)
        )
        self.assertIn("source_fingerprint", enrich_job.payload)


if __name__ == "__main__":
    unittest.main()
