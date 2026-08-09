import unittest
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from berrybrain_api.ai_configuration import (
    AIConfiguration,
    HippoRagSlot,
    JudgeSlot,
    ModelSlot,
    save_configuration,
)
from berrybrain_api.database import Base
from berrybrain_api.graph_research import (
    create_research_run,
    execute_research_run,
    safe_evidence_url,
)
from berrybrain_api.models import (
    GraphNodeRecord,
    GraphResearchResultRecord,
    JobRecord,
)


class GraphResearchTest(unittest.TestCase):
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

    def test_global_run_plans_gaps_and_persists_untrusted_evidence(self) -> None:
        node = GraphNodeRecord(
            type="concept",
            label="Distributed tracing",
            confidence=0.4,
            semantic_state="needs_review",
            validation_status="unvalidated",
        )
        self.session.add(node)
        self.session.commit()
        run = create_research_run(self.session, graph_version=3)

        with patch(
            "berrybrain_api.graph_research.searxng_search",
            return_value=[
                {
                    "title": "Tracing guide",
                    "url": "https://example.org/tracing",
                    "content": "A trace links spans across distributed services.",
                },
                {
                    "title": "Blocked local source",
                    "url": "http://127.0.0.1/private",
                    "content": "private",
                },
            ],
        ):
            completed = execute_research_run(
                self.session, run.id, "http://searxng:8080"
            )

        result = self.session.query(GraphResearchResultRecord).one()
        self.session.refresh(node)
        self.assertEqual(completed.status, "completed")
        self.assertEqual(result.status, "suggested")
        self.assertEqual(result.source_url, "https://example.org/tracing")
        self.assertEqual(node.semantic_state, "pending")
        self.assertEqual(
            self.session.query(JobRecord)
            .filter(JobRecord.type == "ENRICH_GRAPH_NODE")
            .count(),
            1,
        )

    def test_ssrf_sensitive_result_urls_are_rejected(self) -> None:
        self.assertFalse(safe_evidence_url("file:///etc/passwd"))
        self.assertFalse(safe_evidence_url("http://localhost/admin"))
        self.assertFalse(safe_evidence_url("http://10.0.0.2/internal"))
        self.assertTrue(safe_evidence_url("https://example.com/reference"))
