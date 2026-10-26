import asyncio
import json
import unittest
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import berrybrain_api.cognitive_layer  # noqa: F401
from berrybrain_api.agent_monitor import ensure_agent_monitoring
from berrybrain_api.agent_skills import (
    load_agent_skills,
    resolve_skills_dir,
    select_skills_for_context,
)
from berrybrain_api.cognitive_query import (
    _query_tokens,
    answer_cognitive_query,
)
from berrybrain_api.database import Base
from berrybrain_api.models import (
    GraphNodeRecord,
    GraphResearchRunRecord,
    SettingRecord,
)


class AgentSkillsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine(
            "sqlite:///:memory:", connect_args={"check_same_thread": False}
        )
        Base.metadata.create_all(bind=self.engine)
        self.session = sessionmaker(bind=self.engine)()

    def tearDown(self) -> None:
        self.session.close()
        self.engine.dispose()

    def test_skills_library_loads_all_markdown_files_from_project_folder(self) -> None:
        skills_dir = resolve_skills_dir()
        self.assertTrue(skills_dir.is_dir())
        skills = load_agent_skills()
        self.assertGreaterEqual(len(skills), 1500)
        skill_ids = {skill.id for skill in skills}
        expected = {
            "scientific-article",
            "literature-review",
            "tcc-dissertation-monograph",
            "technical-documentation-rfc",
            "study-guide-active-recall",
            "research-synthesis-multihop",
            "critical-epistemic-audit",
            "executive-briefing-report",
            "software-architecture-code",
            "mathematical-formal-proof",
            "experimental-methodology-lab",
            "pedagogical-lesson-plan",
            "project-roadmap-planning",
            "comparative-matrix-benchmark",
            "knowledge-enrichment-24h",
        }
        self.assertTrue(expected.issubset(skill_ids))
        for skill in skills:
            self.assertTrue(skill.file_name.endswith(".md"))
            self.assertIn("bbref:", skill.instructions)

    def test_select_skills_for_context_triggers_automatically_from_user_prompt(
        self,
    ) -> None:
        article_matches = select_skills_for_context(
            "Crie um artigo científico completo no padrão IMRaD sobre Feira de Ciências"
        )
        self.assertTrue(article_matches)
        self.assertEqual(article_matches[0].id, "scientific-article")
        self.assertEqual(article_matches[0].recommended_max_tokens, 4096)

        review_matches = select_skills_for_context(
            "Elabore uma revisão sistemática de literatura e estado da arte sobre grafos"
        )
        self.assertTrue(review_matches)
        self.assertEqual(review_matches[0].id, "literature-review")

        tcc_matches = select_skills_for_context(
            "Escreva um capítulo de TCC e monografia sobre arquitetura cognitiva"
        )
        self.assertTrue(tcc_matches)
        self.assertEqual(tcc_matches[0].id, "tcc-dissertation-monograph")

        rfc_matches = select_skills_for_context(
            "Gere uma documentação técnica e especificação RFC da arquitetura"
        )
        self.assertTrue(rfc_matches)
        self.assertEqual(rfc_matches[0].id, "technical-documentation-rfc")

    def test_query_tokens_strips_output_format_words_to_preserve_vault_subject(
        self,
    ) -> None:
        tokens = _query_tokens(
            "Crie um artigo científico estruturado sobre fotossíntese e clorofila"
        )
        self.assertIn("fotossintese", tokens)
        self.assertIn("clorofila", tokens)
        self.assertNotIn("artigo", tokens)
        self.assertNotIn("cientifico", tokens)
        self.assertNotIn("estruturado", tokens)

    def test_answer_cognitive_query_activates_scientific_article_skill(self) -> None:
        node = GraphNodeRecord(
            type="concept",
            label="Fotossíntese Experimental",
            summary="A clorofila absorve luz solar para converter CO2 e água em glicose.",
            status="confirmed",
            semantic_status="active",
        )
        self.session.add(node)
        self.session.commit()

        captured: dict[str, object] = {}

        async def fake_generate(config, prompt, system, *, timeout=60, max_tokens=1024):
            captured["system"] = system
            captured["prompt"] = prompt
            captured["max_tokens"] = max_tokens
            parsed_prompt = json.loads(prompt)
            ev_id = parsed_prompt["evidence"][0]["evidenceId"]
            return {
                "status": "answered",
                "evidence": [{"evidenceId": ev_id}],
                "answer": f"# Estudo Experimental da Fotossíntese\n\n## Resumo\nBaseado em [Fotossíntese Experimental](bbref:{ev_id}).",
                "relatedNodes": [],
                "suggestions": [],
                "confidence": 0.92,
            }

        fake_orchestrated = {
            "routes": ["knowledge_graph"],
            "semanticState": {},
            "relatedNodes": [],
            "retrievers": ["graph"],
            "embedding_type": "lexical",
            "evidence": [
                {
                    "evidenceId": "ev-foto-1",
                    "source": "knowledge_graph",
                    "title": node.label,
                    "text": node.summary,
                    "score": 0.95,
                    "metadata": {
                        "nodeId": node.id,
                    },
                }
            ],
        }

        with (
            patch(
                "berrybrain_api.cognitive_layer.orchestrate_retrieval",
                return_value=fake_orchestrated,
            ),
            patch(
                "berrybrain_api.cognitive_layer.get_ai_config",
                return_value={
                    "provider": "cloud",
                    "cloud_model": "models/gemini-2.5-flash",
                },
            ),
            patch(
                "berrybrain_api.cognitive_layer.generate_graph_answer",
                side_effect=fake_generate,
            ),
        ):
            result = asyncio.run(
                answer_cognitive_query(
                    self.session,
                    "Crie um artigo científico sobre fotossíntese",
                )
            )

        self.assertEqual(result["status"], "answered")
        self.assertTrue(result.get("activeSkills"))
        self.assertEqual(result["activeSkills"][0]["id"], "scientific-article")
        self.assertEqual(captured["max_tokens"], 4096)
        self.assertIn("Scientific Article & Academic Paper", str(captured["system"]))

    def test_24h_agent_monitor_schedules_web_research_when_enabled(self) -> None:
        self.session.add_all(
            [
                SettingRecord(key="research_mode_enabled", value="true"),
                SettingRecord(key="remote_content_consent", value="true"),
                GraphNodeRecord(
                    type="concept",
                    label="Quantum Decoherence",
                    status="confirmed",
                    semantic_status="active",
                    semantic_state="completed",
                    validation_status="unvalidated",
                    created_by="ai",
                ),
            ]
        )
        self.session.commit()

        configuration = SimpleNamespace(
            validated_at=datetime.now(UTC),
            configuration_fingerprint="test-fp",
        )
        with patch(
            "berrybrain_api.agent_monitor.load_configuration",
            return_value=configuration,
        ):
            res = ensure_agent_monitoring(self.session)

        job_types = {item["type"] for item in res["jobs"]}
        self.assertIn("RESEARCH_GRAPH", job_types)
        self.assertEqual(self.session.query(GraphResearchRunRecord).count(), 1)


if __name__ == "__main__":
    unittest.main()
