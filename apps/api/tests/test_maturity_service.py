import unittest
from datetime import UTC, datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import berrybrain_api.models  # noqa: F401
from berrybrain_api.database import Base
from berrybrain_api.maturity_service import (
    cognitive_maturity_report,
    insight_outcome_metrics,
)
from berrybrain_api.models import (
    GraphEdgeRecord,
    GraphInferenceRecord,
    GraphNodeRecord,
    InsightRecord,
)


class MaturityServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.session = sessionmaker(bind=self.engine)()
        self.now = datetime(2026, 7, 21, tzinfo=UTC)

    def tearDown(self) -> None:
        self.session.close()
        self.engine.dispose()

    def test_empty_vault_is_not_declared_mature(self) -> None:
        report = cognitive_maturity_report(self.session, now=self.now)

        self.assertFalse(report["eligibleFor100Percent"])
        self.assertFalse(report["insightOutcomes"]["meetsTarget"])
        self.assertTrue(report["blockers"])

    def test_complete_provenance_and_longitudinal_outcomes_pass(self) -> None:
        source = GraphNodeRecord(
            type="note",
            label="Source",
            source="note",
            source_id=1,
            source_note_ids="[1]",
            source_evidence='["source.md"]',
            status="confirmed",
        )
        concept = GraphNodeRecord(
            type="concept",
            label="Evidence",
            source="concept_extraction",
            source_id=1,
            source_note_ids="[1]",
            source_evidence='["Source: Evidence"]',
            provider="deterministic",
            model="fixture.v1",
            prompt_version="fixture.v1",
            status="confirmed",
        )
        archived_history = GraphNodeRecord(
            type="concept",
            label="Former concept",
            status="stale",
        )
        self.session.add_all([source, concept, archived_history])
        self.session.flush()
        self.session.add(
            GraphEdgeRecord(
                source_node_id=source.id,
                target_node_id=concept.id,
                type="mentions",
                reason="The source note explicitly discusses Evidence.",
                evidence='["Source", "Evidence"]',
                source_note_ids="[1]",
                confidence=1.0,
                created_by="system",
                provider="deterministic",
                model="fixture.v1",
                prompt_version="fixture.v1",
                status="confirmed",
            )
        )
        self.session.add(
            GraphInferenceRecord(
                question="What is supported?",
                answer="Evidence is supported by Source.",
                status="answered",
                confidence=0.9,
                routes='["knowledge_graph"]',
                evidence='["Source", "Evidence"]',
                related_nodes="[]",
                suggestions="[]",
                provider="fixture",
                model="fixture.v1",
                prompt_version="fixture.v1",
            )
        )
        for index in range(20):
            created_at = self.now - timedelta(days=30 - index)
            applied = index < 14
            self.session.add(
                InsightRecord(
                    type="new_connection",
                    title=f"Grounded insight {index}",
                    description="A specific relationship supported by two sources.",
                    related_notes="[1]",
                    why_it_matters="This changes how the source knowledge is studied.",
                    evidence='["Source", "Evidence"]',
                    suggested_action="Review and connect the cited source material.",
                    graph_impact="Adds one evidence-backed relationship.",
                    confidence=0.9,
                    status="applied" if applied else "ignored",
                    provider="fixture",
                    model="fixture.v1",
                    prompt_version="fixture.v1",
                    applied_at=self.now if applied else None,
                    ignored_at=self.now if not applied else None,
                    feedback_score=1 if applied else -1,
                    created_at=created_at,
                )
            )
        self.session.commit()

        report = cognitive_maturity_report(self.session, now=self.now)

        self.assertTrue(report["structuralReady"])
        self.assertTrue(report["eligibleFor100Percent"])
        self.assertEqual(report["insightOutcomes"]["usefulnessRate"], 0.7)
        self.assertEqual(report["metrics"]["unresolvedArtifactCount"], 0)
        self.assertEqual(report["metrics"]["archivedStaleArtifactCount"], 1)
        self.assertEqual(report["blockers"], [])

    def test_outcome_gate_requires_real_sample_and_time(self) -> None:
        self.session.add(
            InsightRecord(
                type="knowledge_gap",
                title="Recent gap",
                description="A recent reviewed gap.",
                related_notes="[1]",
                evidence='["A", "B"]',
                status="applied",
                provider="fixture",
                model="fixture",
                prompt_version="fixture",
                feedback_score=1,
                applied_at=self.now,
                created_at=self.now - timedelta(days=2),
            )
        )
        self.session.commit()

        metrics = insight_outcome_metrics(self.session, now=self.now)

        self.assertFalse(metrics["meetsTarget"])
        self.assertEqual(metrics["reviewed"], 1)
        self.assertEqual(metrics["observationDays"], 2)
        self.assertEqual(len(metrics["blockers"]), 2)


if __name__ == "__main__":
    unittest.main()
