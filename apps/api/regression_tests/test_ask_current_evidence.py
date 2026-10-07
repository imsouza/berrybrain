"""Isolated Ask regressions: temporary vault/DB, mocked provider, no benchmarks."""

import atexit
import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

_sandbox = tempfile.TemporaryDirectory(prefix="berrybrain-ask-regression-")
atexit.register(_sandbox.cleanup)
os.environ.update(
    {
        "BERRYBRAIN_PROJECT_ROOT": _sandbox.name,
        "BERRYBRAIN_DATABASE_URL": "sqlite:///:memory:",
        "BERRYBRAIN_VAULT_PATH": _sandbox.name,
        "BERRYBRAIN_VAULT_WATCHER_ENABLED": "false",
        "BERRYBRAIN_ENABLE_DEFAULT_OWNER": "false",
    }
)

from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from berrybrain_api import cognitive_layer, cognitive_query  # noqa: E402
from berrybrain_api.ai_gateway import _cloud_json  # noqa: E402
from berrybrain_api.cloud_compat import cloud_chat_options  # noqa: E402
from berrybrain_api.database import Base  # noqa: E402
from berrybrain_api.models import AskSessionRecord, NoteRecord  # noqa: E402
from berrybrain_api.vault import parse_markdown_note  # noqa: E402


class AskCurrentEvidenceTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.session = Session(self.engine)
        self.addCleanup(self.engine.dispose)
        self.addCleanup(self.session.close)
        self.root = Path(_sandbox.name)
        self.note_file = self.root / "current.md"
        content = "# Aprendizado\nGamificação usa desafios e feedback.\n"
        self.note_file.write_text(content, encoding="utf8")
        note = NoteRecord(
            title="Aprendizado",
            slug="current",
            path="current.md",
            content=content,
            content_hash=parse_markdown_note(content).content_hash,
        )
        self.session.add(note)
        self.session.commit()
        self.current = {
            "source": "knowledge_base",
            "title": note.title,
            "text": content,
            "score": 1.0,
            "metadata": {"noteId": note.id},
        }
        self.stale = {
            "source": "hipporag",
            "title": "Removed note",
            "text": "Old claim",
            "score": 1.0,
            "metadata": {"docId": "inbox/removed.md"},
        }
        self.retrieval = {
            "routes": ["knowledge_base", "hipporag"],
            "evidence": [self.stale, self.current],
            "relatedNodes": [],
            "semanticState": {},
        }
        self.generate = AsyncMock(side_effect=self.answer)
        for target, kwargs in [
            (
                "berrybrain_api.config.get_settings",
                {
                    "return_value": SimpleNamespace(
                        vault_path=self.root,
                        flow_recent_turns=6,
                        flow_context_token_budget=1024,
                    )
                },
            ),
            (
                "berrybrain_api.cognitive_query.build_learning_guidance",
                {"return_value": {}},
            ),
        ]:
            patcher = patch(target, **kwargs)
            patcher.start()
            self.addCleanup(patcher.stop)
        for name, value in [
            ("orchestrate_retrieval", lambda *_: self.retrieval),
            ("get_ai_config", lambda *_: {"provider": "cloud"}),
            ("generate_graph_answer", self.generate),
        ]:
            patcher = patch.object(cognitive_layer, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    async def answer(self, config, prompt, system, **kwargs):
        supplied = json.loads(prompt)["evidence"]
        self.assertEqual(len(supplied), 1)
        self.assertEqual(
            supplied[0]["metadata"]["noteId"], self.current["metadata"]["noteId"]
        )
        return {
            "status": "answered",
            "answer": "Gamificação usa desafios e feedback.",
            "evidence": [{"evidenceId": supplied[0]["evidenceId"]}],
            "confidence": 0.5,
        }

    async def test_stale_optional_result_does_not_veto_current_note(self):
        result = await cognitive_query.answer_cognitive_query(
            self.session, "Como funciona gamificação?"
        )
        self.assertEqual(result["status"], "answered")
        self.assertEqual(len(result["evidence"]), 1)
        self.assertEqual(result["evidence"][0]["citationStatus"], "source_verified")

    async def test_only_unverifiable_results_still_abstain(self):
        self.retrieval["evidence"] = [self.stale]
        result = await cognitive_query.answer_cognitive_query(self.session, "Pergunta")
        self.assertEqual(result["status"], "insufficient_evidence")
        self.generate.assert_not_awaited()

    async def test_source_edited_during_generation_still_abstains(self):
        async def edited(*args, **kwargs):
            result = await self.answer(*args, **kwargs)
            self.note_file.write_text("Changed during generation", encoding="utf8")
            return result

        self.generate.side_effect = edited
        result = await cognitive_query.answer_cognitive_query(self.session, "Pergunta")
        self.assertEqual(result["status"], "insufficient_evidence")
        self.assertIn("changed", result["reason"])

    async def test_invented_citation_still_abstains(self):
        self.generate.side_effect = None
        self.generate.return_value = {"answer": "Claim", "evidence": ["invented-id"]}
        result = await cognitive_query.answer_cognitive_query(self.session, "Pergunta")
        self.assertEqual(result["status"], "insufficient_evidence")
        self.assertIn("citations", result["reason"])

    async def test_timeout_does_not_expose_discarded_evidence(self):
        self.generate.side_effect = TimeoutError()
        result = await cognitive_query.answer_cognitive_query(self.session, "Pergunta")
        self.assertEqual(result["status"], "waiting_provider")
        self.assertEqual(result["evidence"], [self.current])

    async def test_graph_ask_searches_the_user_question_without_internal_instructions(
        self,
    ):
        from berrybrain_api.routers.graph import GraphInferRequest, infer_graph

        question = "crie um guia de estudo sobre computação"
        with patch.object(
            cognitive_layer, "orchestrate_retrieval", return_value=self.retrieval
        ) as retrieve:
            result = await infer_graph(
                GraphInferRequest(question=question), self.session
            )
        retrieve.assert_called_once_with(self.session, question)
        self.assertEqual(result["status"], "answered")
        self.assertEqual(self.generate.await_args.kwargs["max_tokens"], 3072)
        prompt = json.loads(self.generate.await_args.args[1])
        self.assertEqual(prompt["question"], question)

    async def test_flow_keeps_history_out_of_retrieval_query(self):
        from berrybrain_api import ask_flow

        item = AskSessionRecord(
            id="flow-test",
            mode="flow",
            title="Test",
            active=True,
            configuration_fingerprint="test-config",
        )
        self.session.add(item)
        self.session.commit()
        question = "crie um guia de estudo sobre computação"
        with (
            patch.object(
                ask_flow,
                "load_configuration",
                return_value=SimpleNamespace(configuration_fingerprint="test-config"),
            ),
            patch.object(
                cognitive_layer, "orchestrate_retrieval", return_value=self.retrieval
            ) as retrieve,
        ):
            await ask_flow.append_ask_turn(self.session, item.id, question)
        retrieve.assert_called_once_with(self.session, question)
        prompt = json.loads(self.generate.await_args.args[1])
        self.assertIn(question, prompt["conversationContext"])

    async def test_citation_format_is_regenerated_once_without_fabricating_sources(
        self,
    ):
        async def retry(*args, **kwargs):
            if self.generate.await_count == 1:
                return {"answer": "Draft without usable citations", "evidence": []}
            self.assertIn("citationValidationFeedback", json.loads(args[1]))
            return await self.answer(*args, **kwargs)

        self.generate.side_effect = retry
        result = await cognitive_query.answer_cognitive_query(self.session, "Pergunta")
        self.assertEqual(result["status"], "answered")
        self.assertEqual(self.generate.await_count, 2)

    def test_short_followup_uses_previous_user_topic_not_assistant_instructions(self):
        history = "user: crie um guia de computação\nassistant: Graph nodes and internal instructions\nuser: explique isso melhor"
        query = cognitive_query._retrieval_question("explique isso melhor", history)
        self.assertIn("computação", query)
        self.assertNotIn("Graph nodes", query)

    def test_broad_topic_uses_accented_folder_and_diversifies_note_content(self):
        for i in range(4):
            content = f"# Algoritmo {i}\n\nExplicação técnica exclusiva {i}."
            self.session.add(
                NoteRecord(
                    title=f"Algoritmo {i}",
                    slug=f"alg-{i}",
                    path=f"Computacao/alg-{i}.md",
                    content=content,
                    content_hash=parse_markdown_note(content).content_hash,
                )
            )
        self.session.add(
            NoteRecord(
                title="Guia de estudo de biologia",
                slug="mapa-bio",
                path="Biologia/mapa.md",
                content="Guia de estudo. " * 100,
                content_hash="unused",
            )
        )
        self.session.commit()
        rows = cognitive_query._retrieve_lexical_kb(
            self.session, "crie um guia de estudo sobre computação", limit=4
        )
        self.assertEqual(len({r.metadata["noteId"] for r in rows}), 4)
        self.assertTrue(all(r.metadata["path"].startswith("Computacao/") for r in rows))
        self.assertTrue(all("Explicação técnica" in r.text for r in rows))


class NimJsonCompatibilityTests(unittest.TestCase):
    def test_options_are_scoped_to_nim_nemotron_3(self):
        self.assertEqual(
            cloud_chat_options(
                "https://integrate.api.nvidia.com/v1",
                "nvidia/nemotron-3-super-120b-a12b",
            ),
            {"chat_template_kwargs": {"enable_thinking": False}},
        )
        self.assertEqual(
            cloud_chat_options(
                "https://example.com/v1", "nvidia/nemotron-3-super-120b-a12b"
            ),
            {},
        )
        self.assertEqual(
            cloud_chat_options(
                "https://integrate.api.nvidia.com/v1", "meta/llama-3.1-8b-instruct"
            ),
            {},
        )

    def test_runtime_sends_final_answer_options(self):
        response = MagicMock()
        response.__enter__.return_value.read.return_value = json.dumps(
            {"choices": [{"message": {"content": '{"probe":true}'}}]}
        ).encode()
        with patch("urllib.request.urlopen", return_value=response) as request:
            result = _cloud_json(
                {
                    "cloud_api_url": "https://integrate.api.nvidia.com/v1",
                    "cloud_api_key": "test-placeholder",
                    "cloud_model": "nvidia/nemotron-3.5-lightning-30b-a3b",
                },
                "JSON probe",
                "JSON only",
                12,
                32,
            )
        body = json.loads(request.call_args.args[0].data)
        self.assertEqual(body["chat_template_kwargs"], {"enable_thinking": False})
        self.assertEqual(result, {"probe": True})


if __name__ == "__main__":
    unittest.main()
