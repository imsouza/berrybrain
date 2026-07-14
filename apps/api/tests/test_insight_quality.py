import unittest
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import berrybrain_api.models  # noqa: F401
from berrybrain_api.database import Base
from berrybrain_api.models import InsightRecord
from berrybrain_api.services import create_insight, get_active_insights


class InsightQualityTest(unittest.TestCase):
    def setUp(self) -> None:
        engine = create_engine("sqlite://")
        Base.metadata.create_all(engine)
        self.session = sessionmaker(bind=engine)()

    def tearDown(self) -> None:
        self.session.close()

    def create_strong(self, title: str, evidence: list[str]):
        return create_insight(
            self.session,
            "knowledge_gap",
            title,
            "The current notes explain telemetry signals but omit how sampling changes trace interpretation.",
            related_notes=[1, 2],
            priority=6,
            why_it_matters="Without this distinction, latency conclusions may be misleading.",
            evidence=evidence,
            suggested_action="Add a permanent note explaining trace sampling tradeoffs.",
            graph_impact="Connects observability, tracing, and statistical sampling.",
            confidence=0.86,
            provider="nvidia-nim",
            model="qwen",
            prompt_version="insight.v2",
        )

    def test_same_evidence_deduplicates_reformulated_insight(self) -> None:
        first = self.create_strong(
            "Trace sampling is a missing observability concept",
            ["note-a: trace sampling", "note-b: latency traces"],
        )
        second = self.create_strong(
            "Observability notes omit sampling effects on traces",
            ["note-b: latency traces", "note-a: trace sampling"],
        )
        self.assertEqual(first.id, second.id)
        self.assertEqual(self.session.query(type(first)).count(), 1)
        self.assertGreaterEqual(second.quality_score, 0.8)
        self.assertIsNotNone(second.last_recalculated_at)

    def test_vague_insights_are_penalized(self) -> None:
        vague = create_insight(
            self.session,
            "knowledge_gap",
            "Knowledge gap",
            "Vague.",
            related_notes=[3],
            priority=6,
            evidence=["thin evidence"],
            why_it_matters="This may matter, but current support is weak.",
            suggested_action="Collect another source before acting.",
            graph_impact="No graph change until evidence improves.",
            confidence=0.9,
        )
        strong = self.create_strong(
            "Sampling assumptions change trace-based latency conclusions",
            ["trace source", "sampling source"],
        )
        self.assertLess(vague.quality_score, strong.quality_score)
        self.assertLess(vague.priority, strong.priority)
        self.assertLess(vague.confidence, 0.9)

    def test_knowledge_insight_without_cognitive_evidence_is_rejected(self) -> None:
        with self.assertRaises(HTTPException):
            create_insight(
                self.session,
                "knowledge_gap",
                "Generic unsupported insight",
                "No evidence is supplied.",
            )

    def test_feedback_ranks_insights_and_expiration_removes_stale_items(self) -> None:
        preferred = self.create_strong(
            "Preferred insight about trace sampling",
            ["preferred-a", "preferred-b"],
        )
        other = self.create_strong(
            "Other insight about metric aggregation",
            ["other-a", "other-b"],
        )
        preferred.feedback_score = 2
        other.expires_at = datetime.now(UTC) - timedelta(seconds=1)
        self.session.commit()

        active = get_active_insights(self.session)

        self.assertEqual(active[0].id, preferred.id)
        self.session.refresh(other)
        self.assertEqual(other.status, "expired")

    def test_legacy_migration_archives_unsupported_and_upgrades_grounded(self) -> None:
        unsupported = InsightRecord(
            type="hypothesis",
            title="Generic legacy hypothesis",
            description="A legacy claim without source support.",
            status="suggested",
        )
        grounded = InsightRecord(
            type="hypothesis",
            title="Container isolation depends on Linux kernel primitives",
            description=(
                "The Docker and Linux notes both describe namespaces and process "
                "isolation as the basis of containers."
            ),
            related_notes="[1,2]",
            why_it_matters="It connects operational Docker usage to its kernel foundations.",
            evidence='["Docker: namespaces isolate containers", "Linux: namespaces isolate processes"]',
            suggested_action="Create a permanent note about namespace-based isolation.",
            graph_impact="Connects Docker, Linux, namespaces, and process isolation.",
            confidence=0.82,
            status="suggested",
            provider="deterministic",
            model="legacy-knowledge.v1",
        )
        self.session.add_all([unsupported, grounded])
        self.session.commit()

        active = get_active_insights(self.session)
        self.session.refresh(unsupported)
        self.session.refresh(grounded)

        self.assertEqual([item.id for item in active], [grounded.id])
        self.assertEqual(unsupported.status, "archived")
        self.assertIsNotNone(unsupported.dismissed_at)
        self.assertTrue(grounded.fingerprint)
        self.assertGreater(grounded.quality_score, 0.7)
        self.assertIsNotNone(grounded.expires_at)


if __name__ == "__main__":
    unittest.main()
