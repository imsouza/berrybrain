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

    def test_legacy_note_score_does_not_order_research(self) -> None:
        notes = [
            GraphNodeRecord(
                type="note",
                label=f"Saved note {index}",
                confidence=score,
                confidence_sample_size=2,
                semantic_state="needs_review",
            )
            for index, score in enumerate((0.1, 0.9), start=1)
        ]
        concept = GraphNodeRecord(
            type="concept",
            label="Derived concept",
            confidence=0.5,
            confidence_sample_size=2,
            semantic_state="needs_review",
        )
        self.session.add_all([*notes, concept])
        self.session.commit()

        def planned_queries() -> list[str]:
            seen: list[str] = []

            def search(query, *_args, **_kwargs):
                seen.append(query)
                return []

            run = create_research_run(self.session)
            with patch(
                "berrybrain_api.graph_research.searxng_search", side_effect=search
            ):
                execute_research_run(self.session, run.id, "http://searxng:8080")
            return seen

        first = planned_queries()
        notes[0].confidence = 0.95
        notes[1].confidence = 0.01
        self.session.commit()
        second = planned_queries()
        self.assertEqual(first, second)
        self.assertEqual(first, ["Derived concept", "Saved note 1", "Saved note 2"])
