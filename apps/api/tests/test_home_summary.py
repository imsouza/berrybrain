import unittest
from datetime import timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from berrybrain_api.database import Base
from berrybrain_api.jobs import utc_now
from berrybrain_api.models import (
    AutomationLogRecord,
    ConceptRecord,
    ConnectionRecord,
    EmbeddingRecord,
    GeneratedMetadataRecord,
    InsightRecord,
    JobRecord,
    NoteRecord,
    SettingRecord,
    WorkerStatus,
)


class HomeSummaryTest(unittest.TestCase):
    def setUp(self) -> None:
        engine = create_engine(
            "sqlite:///:memory:", connect_args={"check_same_thread": False}
        )
        Base.metadata.create_all(bind=engine)
        self.session = sessionmaker(bind=engine)()

    def tearDown(self) -> None:
        self.session.close()

    def test_build_home_summary_exposes_progress_and_knowledge_sections(self) -> None:
        now = utc_now()
        note_a = NoteRecord(
            title="Observabilidade",
            slug="observabilidade",
            path="estudos/observabilidade.md",
            content="Notas sobre logs, métricas e traces.",
            content_hash="a",
            status="synced",
            created_at=now,
            updated_at=now,
            last_processed_at=now - timedelta(minutes=3),
        )
        note_b = NoteRecord(
            title="Edge Computing",
            slug="edge-computing",
            path="estudos/edge-computing.md",
            content_hash="b",
            status="new",
            created_at=now,
            updated_at=now,
        )
        self.session.add_all([note_a, note_b])
        self.session.flush()

        self.session.add_all(
            [
                JobRecord(type="PARSE_NOTE", status="completed", completed_at=now),
                JobRecord(
                    type="GENERATE_EMBEDDING",
                    status="running",
                    payload='{"note_path":"estudos/observabilidade.md"}',
                    started_at=now - timedelta(seconds=34),
                ),
                JobRecord(type="FIND_CONNECTIONS", status="pending"),
                JobRecord(type="GENERATE_INSIGHTS", status="failed", error_message="timeout"),
                WorkerStatus(
                    status="running",
                    last_heartbeat=now,
                    jobs_processed=9,
                    errors=1,
                    ollama_healthy=False,
                ),
                SettingRecord(key="ai_provider", value="cloud"),
                SettingRecord(key="ai_model", value="nvidia/nemotron"),
                ConceptRecord(
                    name="observabilidade",
                    normalized_name="observabilidade",
                    description="Monitoramento de sistemas.",
                ),
                ConnectionRecord(
                    source_note_id=note_a.id,
                    target_note_id=note_b.id,
                    connection_type="semantic",
                    confidence=82,
                    reason="Ambas tratam de sistemas distribuídos.",
                    created_by="ai",
                ),
                InsightRecord(
                    type="knowledge_gap",
                    title="Lacuna detectada",
                    description="Falta uma nota central.",
                    related_notes='["estudos/observabilidade.md"]',
                    priority=2,
                ),
                GeneratedMetadataRecord(
                    note_id=note_a.id,
                    generation_type="summary",
                    content='{"summary":"Resumo"}',
                    content_hash="a",
                    model_used="nvidia/nemotron",
                ),
                EmbeddingRecord(
                    note_id=note_a.id,
                    content_hash="a",
                    vector="[0.1, 0.2]",
                    model="bge-m3",
                ),
                AutomationLogRecord(
                    action_type="ENQUEUE_JOB",
                    target_type="note",
                    target_id=note_a.path,
                    description="Criou job EXPAND_KNOWLEDGE_GRAPH para NOTE_CREATED",
                    created_at=now,
                ),
            ]
        )
        self.session.commit()

        from berrybrain_api.home_summary import build_home_summary

        summary = build_home_summary(self.session)

        self.assertEqual(summary["status"]["worker"], "running")
        self.assertEqual(summary["status"]["cloudProvider"], "nvidia-nim")
        self.assertEqual(summary["status"]["cloudModel"], "nvidia/nemotron")
        self.assertEqual(summary["progress"]["mode"], "determinate")
        self.assertEqual(summary["progress"]["percent"], 25)
        self.assertEqual(summary["stats"]["notes"]["total"], 2)
        self.assertEqual(summary["stats"]["notes"]["unassimilated"], 1)
        self.assertEqual(summary["stats"]["connections"]["total"], 1)
        self.assertEqual(summary["stats"]["concepts"]["total"], 1)
        self.assertIn("study", summary["stats"])
        self.assertNotIn("flashcards", summary["stats"])
        self.assertNotIn("reviews", summary["stats"])
        self.assertEqual(summary["graphSummary"]["nodes"], 2)
        self.assertEqual(summary["graphSummary"]["edges"], 1)
        self.assertEqual(summary["graphSummary"]["orphans"], 0)
        self.assertEqual(len(summary["activeJobs"]), 1)
        self.assertEqual(len(summary["recentInsights"]), 1)
        self.assertEqual(len(summary["detectedConcepts"]), 1)
        self.assertEqual(len(summary["recentConnections"]), 1)
        self.assertTrue(summary["recentlyCompleted"])
        self.assertTrue(summary["needsAttention"])


if __name__ == "__main__":
    unittest.main()
