import unittest

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
from berrybrain_api.models import GraphNodeRecord, NodeEnrichmentVersionRecord
from berrybrain_api.semantic_enrichment import (
    SEMANTIC_PROMPT_VERSION,
    SemanticAnalysis,
    SemanticConfidence,
    persist_semantic_analysis,
    queue_node_enrichment,
    semantic_analysis_payload,
    source_fingerprint,
)


class SemanticEnrichmentTest(unittest.TestCase):
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
        self.node = GraphNodeRecord(
            type="concept",
            label="Docker",
            summary="Container runtime used by deployment notes.",
            source_note_ids="[1]",
        )
        self.session.add(self.node)
        self.session.commit()

    def tearDown(self) -> None:
        self.session.close()
        self.engine.dispose()

    def test_queue_is_idempotent_for_same_evidence_and_configuration(self) -> None:
        first, first_created = queue_node_enrichment(self.session, self.node)
        second, second_created = queue_node_enrichment(self.session, self.node)

        self.assertTrue(first_created)
        self.assertFalse(second_created)
        self.assertEqual(first.id, second.id)
        self.assertEqual(self.node.semantic_state, "pending")
        self.assertEqual(self.node.color_id, "pending")

    def test_reprocessing_preserves_last_valid_context_color(self) -> None:
        self.node.color_id = "semantic-existing-context"
        self.session.commit()

        queue_node_enrichment(self.session, self.node, force=True)

        self.assertEqual(self.node.semantic_state, "pending")
        self.assertEqual(self.node.color_id, "semantic-existing-context")

    def test_analysis_is_versioned_and_exposes_specific_contract(self) -> None:
        fingerprint = source_fingerprint(self.session, self.node)
        analysis = SemanticAnalysis(
            meaning_in_context="Docker packages the services described in deployment notes.",
            use_in_notes="The notes use Docker for reproducible API and Worker execution.",
            why_it_matters_here="It connects local development with release deployment.",
            supported_findings=["API and Worker are deployed as containers."],
            inferences=["The same images can support repeatable releases."],
            uncertainties=["Production orchestration is not described."],
            evidence=[{"source": "deployment.md", "excerpt": "docker compose up"}],
            connection_assessments=[],
            confidence=SemanticConfidence(
                concept_detection=0.98,
                semantic_interpretation=0.9,
                evidence_coverage=0.75,
            ),
            provider="local",
            model="main",
            source_fingerprint=fingerprint,
        )

        profile = persist_semantic_analysis(self.session, self.node, analysis)
        payload = semantic_analysis_payload(self.session, self.node.id)

        self.assertEqual(profile.prompt_version, SEMANTIC_PROMPT_VERSION)
        self.assertEqual(payload["state"], "completed")
        self.assertEqual(payload["historyCount"], 1)
        self.assertIn("Docker packages", payload["analysis"]["meaning_in_context"])
        self.assertEqual(
            self.session.query(NodeEnrichmentVersionRecord).count(),
            1,
        )
