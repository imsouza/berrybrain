import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from starlette.requests import Request

from berrybrain_api.ai_configuration import (
    AIConfiguration,
    HippoRagSlot,
    JudgeSlot,
    ModelSlot,
    save_configuration,
)
from berrybrain_api.ask_flow import (
    append_ask_turn,
    cancel_ask_session,
    close_ask_session,
    create_ask_session,
    create_insight_from_flow_session,
    get_ask_session_payload,
)
from berrybrain_api.ask_references import (
    append_verified_reference_links,
    capture_ask_references,
    resolve_ask_references,
)
from berrybrain_api.cognitive_query import retrieve_graph
from berrybrain_api.database import Base
from berrybrain_api.models import (
    AskTurnRecord,
    GraphInferenceRecord,
    GraphNodeRecord,
    InsightRecord,
    NoteAttachmentRecord,
    NoteRecord,
)
from berrybrain_api.routers.graph import GraphInferRequest, infer_graph


class AskFlowTest(unittest.IsolatedAsyncioTestCase):
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

    async def test_turns_are_persisted_and_restored_in_sequence(self) -> None:
        flow = create_ask_session(self.session)
        answer = AsyncMock(
            return_value={
                "answer": "Docker isolates the API and Worker processes.",
                "evidence": [{"nodeId": 7}],
                "provider": "local",
                "model": "main",
            }
        )
        with patch("berrybrain_api.ask_flow.answer_cognitive_query", answer):
            await append_ask_turn(self.session, flow.id, "How is Docker used?")

        payload = get_ask_session_payload(self.session, flow.id)
        self.assertEqual(
            [turn["role"] for turn in payload["turns"]], ["user", "assistant"]
        )
        self.assertEqual(payload["turns"][1]["evidenceIds"], ["7"])
        self.assertTrue(payload["session"]["active"])

    async def test_fallback_provenance_survives_flow_reload(self) -> None:
        flow = create_ask_session(self.session)
        answer = AsyncMock(
            return_value={
                "answer": "Resposta fundamentada.",
                "evidence": [{"nodeId": 7}],
                "provider": "opencode-zen",
                "model": "alternate",
                "fallbackUsed": True,
                "fallbackReason": "model_unavailable",
            }
        )
        with patch("berrybrain_api.ask_flow.answer_cognitive_query", answer):
            await append_ask_turn(self.session, flow.id, "Pergunta")

        restored = get_ask_session_payload(self.session, flow.id)["turns"][1]
        self.assertEqual(restored["provider"], "opencode-zen")
        self.assertEqual(restored["model"], "alternate")
        self.assertTrue(restored["fallbackUsed"])
        self.assertEqual(restored["fallbackReason"], "model_unavailable")

    async def test_verified_references_keep_resource_types_and_follow_rename(
        self,
    ) -> None:
        note = NoteRecord(
            title="Ciência de dados",
            slug="ciencia-de-dados",
            path="Feira/Ciencia de dados.md",
            content="Dados e experimentos",
            content_hash="version-one",
        )
        node = GraphNodeRecord(
            type="concept",
            label="Grafos",
            title="Grafos",
            status="confirmed",
            quality_gate_status="passed",
            semantic_status="active",
        )
        self.session.add_all([note, node])
        self.session.commit()
        flow = create_ask_session(self.session)
        answer = AsyncMock(
            return_value={
                "answer": "Use a nota e o conceito.",
                "evidence": [
                    {
                        "evidenceId": "ev-note",
                        "metadata": {"noteId": note.id},
                        "citationStatus": "source_verified",
                    },
                    {
                        "evidenceId": "ev-node",
                        "metadata": {"nodeId": node.id},
                        "citationStatus": "source_verified",
                    },
                ],
            }
        )
        with patch("berrybrain_api.ask_flow.answer_cognitive_query", answer):
            await append_ask_turn(self.session, flow.id, "Quais fontes?")
        refs = get_ask_session_payload(self.session, flow.id)["turns"][1]["references"]
        self.assertEqual({ref["kind"] for ref in refs}, {"note", "graph_node"})
        first_answer = get_ask_session_payload(self.session, flow.id)["turns"][1][
            "content"
        ]
        self.assertIn(f"bbref:resolved:note:{note.id}", first_answer)
        self.assertIn(f"bbref:resolved:graph_node:{node.id}", first_answer)
        note_ref = next(ref for ref in refs if ref["kind"] == "note")
        self.assertEqual(note_ref["path"], note.path)
        self.assertEqual(note_ref["evidenceIds"], ["ev-note"])

        with patch(
            "berrybrain_api.ask_flow.answer_cognitive_query", new_callable=AsyncMock
        ) as model:
            await append_ask_turn(
                self.session, flow.id, "Consegue linkar as notas para mim?"
            )
            model.assert_not_awaited()
        linked = get_ask_session_payload(self.session, flow.id)["turns"][3]
        self.assertEqual(
            {ref["kind"] for ref in linked["references"]}, {"note", "graph_node"}
        )
        self.assertIn(
            f"[Ciência de dados](bbref:resolved:note:{note.id})", linked["content"]
        )
        self.assertIn(
            f"[Grafos](bbref:resolved:graph_node:{node.id})", linked["content"]
        )

        # An unrelated answer without citations must not erase verified links.
        with patch(
            "berrybrain_api.ask_flow.answer_cognitive_query",
            AsyncMock(return_value={"answer": "Resposta sem fontes.", "evidence": []}),
        ):
            await append_ask_turn(self.session, flow.id, "Outra pergunta")
        with patch(
            "berrybrain_api.ask_flow.answer_cognitive_query", new_callable=AsyncMock
        ) as model:
            await append_ask_turn(self.session, flow.id, "Consegue linkar as notas?")
            model.assert_not_awaited()
        later = get_ask_session_payload(self.session, flow.id)["turns"][-1]
        self.assertIn(f"bbref:resolved:note:{note.id}", later["content"])
        self.assertEqual(
            {ref["kind"] for ref in later["references"]}, {"note", "graph_node"}
        )

        note.path = "Feira/Nota renomeada.md"
        note.content_hash = "version-two"
        self.session.commit()
        renamed = get_ask_session_payload(self.session, flow.id)["turns"][1][
            "references"
        ]
        renamed_note = next(ref for ref in renamed if ref["kind"] == "note")
        self.assertEqual(renamed_note["path"], note.path)
        self.assertFalse(renamed_note["current"])

        self.session.delete(note)
        self.session.commit()
        surviving = get_ask_session_payload(self.session, flow.id)["turns"][1][
            "references"
        ]
        self.assertEqual([ref["kind"] for ref in surviving], ["graph_node"])
        with patch(
            "berrybrain_api.ask_flow.answer_cognitive_query", new_callable=AsyncMock
        ) as model:
            await append_ask_turn(self.session, flow.id, "Consegue linkar as notas?")
            model.assert_not_awaited()
        final = get_ask_session_payload(self.session, flow.id)["turns"][-1]
        self.assertEqual([ref["kind"] for ref in final["references"]], ["graph_node"])
        self.assertNotIn(f"bbref:resolved:note:{note.id}", final["content"])

    def test_unverified_evidence_cannot_become_a_navigation_link(self) -> None:
        note = NoteRecord(
            title="Private source",
            slug="private-source",
            path="private/source.md",
            content_hash="version-one",
        )
        self.session.add(note)
        self.session.commit()
        forged = [{"evidenceId": "forged", "metadata": {"noteId": note.id}}]
        self.assertEqual(capture_ask_references(self.session, forged), [])
        self.assertEqual(append_verified_reference_links("Answer", []), "Answer")

    def test_verified_reference_links_are_not_duplicated(self) -> None:
        refs = [
            {
                "kind": "note",
                "id": 53,
                "title": "Fichamento [RAG]",
                "evidenceIds": ["ev-53"],
            },
            {
                "kind": "graph_node",
                "id": 6,
                "title": "Grafos",
                "evidenceIds": ["ev-6"],
            },
        ]
        answer = "Use [Fichamento](bbref:ev-53) e Grafos."
        linked = append_verified_reference_links(answer, refs)
        self.assertEqual(linked.count("bbref:ev-53"), 1)
        self.assertNotIn("bbref:resolved:note:53", linked)
        self.assertIn("[Grafos](bbref:resolved:graph_node:6)", linked)
        self.assertEqual(append_verified_reference_links(linked, refs), linked)
        self.assertEqual(append_verified_reference_links("", refs), "")

    def test_verified_reference_title_is_markdown_escaped(self) -> None:
        linked = append_verified_reference_links(
            "Veja a fonte.",
            [{"kind": "note", "id": 1, "title": "Um [título]"}],
        )
        self.assertIn("[Um \\[título\\]](bbref:resolved:note:1)", linked)

    def test_graph_reference_offers_only_live_source_notes(self) -> None:
        live = NoteRecord(title="Origem", slug="origem", path="A/origem.md")
        draft = NoteRecord(
            title="Rascunho",
            slug="rascunho",
            path="A/rascunho.md",
            evidence_status="draft",
        )
        self.session.add_all([live, draft])
        self.session.flush()
        node = GraphNodeRecord(
            type="concept",
            label="Conceito",
            status="confirmed",
            quality_gate_status="passed",
            semantic_status="active",
            source_note_ids=json.dumps([live.id, draft.id, 999999, live.id]),
        )
        self.session.add(node)
        self.session.commit()
        evidence = [
            {
                "evidenceId": "ev-node",
                "metadata": {"nodeId": node.id},
                "citationStatus": "source_verified",
            }
        ]
        stored = capture_ask_references(self.session, evidence)
        resolved = resolve_ask_references(self.session, stored)
        self.assertEqual(
            resolved[0]["sourceNotes"],
            [
                {
                    "id": live.id,
                    "title": live.title,
                    "path": live.path,
                    "vaultId": "default",
                }
            ],
        )
        live.path = "B/renomeada.md"
        self.session.commit()
        self.assertEqual(
            resolve_ask_references(self.session, stored)[0]["sourceNotes"][0]["path"],
            live.path,
        )
        self.session.delete(live)
        self.session.commit()
        self.assertEqual(
            resolve_ask_references(self.session, stored)[0]["sourceNotes"], []
        )
        node.source_note_ids = "invalid JSON"
        self.session.commit()
        self.assertEqual(
            resolve_ask_references(self.session, stored)[0]["sourceNotes"], []
        )

    async def test_direct_ask_persists_verified_navigation_links(self) -> None:
        note = NoteRecord(
            title="Feira de ciências",
            slug="feira-de-ciencias",
            path="Feira/base.md",
            content_hash="v1",
        )
        self.session.add(note)
        self.session.commit()
        response = {
            "status": "answered",
            "answer": "Use esta nota para o artigo.",
            "evidence": [
                {
                    "evidenceId": "ev-feira",
                    "metadata": {"noteId": note.id},
                    "citationStatus": "source_verified",
                }
            ],
        }
        request = Request(
            {
                "type": "http",
                "method": "POST",
                "path": "/api/graph/infer",
                "headers": [],
            }
        )
        with (
            patch(
                "berrybrain_api.routers.graph.answer_cognitive_query",
                AsyncMock(return_value=response),
            ),
            patch(
                "berrybrain_api.routers.graph.request_inference_owner_id",
                return_value=None,
            ),
        ):
            result = await infer_graph(
                GraphInferRequest(question="Qual nota?"), request, self.session
            )
        marker = f"bbref:resolved:note:{note.id}"
        self.assertIn(marker, result["answer"])
        self.assertEqual(result["references"][0]["path"], note.path)
        saved = self.session.get(GraphInferenceRecord, result["inferenceId"])
        self.assertIsNotNone(saved)
        self.assertIn(marker, saved.answer)

    async def test_verified_attachment_opens_its_current_owner_note(self) -> None:
        note = NoteRecord(
            title="Feira",
            slug="feira",
            path="Feira/base.md",
            content="Um anexo",
            content_hash="version-one",
        )
        self.session.add(note)
        self.session.flush()
        attachment = NoteAttachmentRecord(
            note_id=note.id,
            note_path=note.path,
            filename="dados.pdf",
            stored_path="attachments/dados.pdf",
            checksum="a" * 64,
            validation_status="validated",
        )
        self.session.add(attachment)
        self.session.commit()
        evidence = {
            "evidenceId": "ev-pdf",
            "metadata": {"attachmentId": attachment.id, "noteId": note.id},
            "citationStatus": "source_verified",
        }
        flow = create_ask_session(self.session)
        with patch(
            "berrybrain_api.ask_flow.answer_cognitive_query",
            AsyncMock(return_value={"answer": "Veja o anexo.", "evidence": [evidence]}),
        ):
            await append_ask_turn(self.session, flow.id, "Quais dados?")
        refs = get_ask_session_payload(self.session, flow.id)["turns"][1]["references"]
        attached = next(ref for ref in refs if ref["kind"] == "attachment")
        self.assertEqual(attached["title"], "dados.pdf")
        self.assertEqual(attached["path"], note.path)

        note.path = "Feira/renomeada.md"
        self.session.commit()
        renamed = get_ask_session_payload(self.session, flow.id)["turns"][1][
            "references"
        ]
        self.assertEqual(
            next(ref for ref in renamed if ref["kind"] == "attachment")["path"],
            note.path,
        )
        mismatched = {
            **evidence,
            "metadata": {"attachmentId": attachment.id, "noteId": note.id + 100},
        }
        self.assertFalse(
            any(
                ref["kind"] == "attachment"
                for ref in capture_ask_references(self.session, [mismatched])
            )
        )

    def test_legacy_note_confidence_does_not_change_retrieval(self) -> None:
        node = GraphNodeRecord(
            type="note",
            label="Feira de ciências e grafos",
            status="confirmed",
            semantic_status="active",
            confidence=0.1,
            confidence_lower=0.01,
            confidence_sample_size=2,
        )
        self.session.add(node)
        self.session.commit()
        first, _ = retrieve_graph(self.session, "feira ciencias grafos")
        self.assertTrue(first)
        self.assertIsNone(first[0].metadata["confidence"])
        node.confidence = 0.99
        node.confidence_lower = 0.99
        self.session.commit()
        second, _ = retrieve_graph(self.session, "feira ciencias grafos")
        self.assertEqual(first[0].score, second[0].score)

    async def test_sessions_are_isolated_and_can_be_closed(self) -> None:
        first = create_ask_session(self.session, title="First")
        second = create_ask_session(self.session, title="Second")
        answer = AsyncMock(return_value={"answer": "Grounded answer.", "evidence": []})
        with patch("berrybrain_api.ask_flow.answer_cognitive_query", answer):
            await append_ask_turn(self.session, first.id, "Only in first")
        close_ask_session(self.session, first.id)

        first_payload = get_ask_session_payload(self.session, first.id)
        second_payload = get_ask_session_payload(self.session, second.id)
        self.assertFalse(first_payload["session"]["active"])
        self.assertEqual(len(first_payload["turns"]), 2)
        self.assertEqual(second_payload["turns"], [])

    async def test_session_can_continue_from_a_graph_inference(self) -> None:
        inference = GraphInferenceRecord(
            access_scope="service",
            question="What does the graph show?",
            answer="The graph links Docker to the API.",
            status="ok",
            evidence='[{"nodeId": 7}]',
            provider="ollama",
            model="main",
        )
        self.session.add(inference)
        self.session.commit()

        flow = create_ask_session(self.session, inference_id=inference.id)
        payload = get_ask_session_payload(self.session, flow.id)

        self.assertEqual(
            [turn["content"] for turn in payload["turns"]],
            [inference.question, inference.answer],
        )
        self.assertEqual(payload["turns"][1]["evidenceIds"], ["7"])

    async def test_flow_answer_can_be_saved_as_insight(self) -> None:
        flow = create_ask_session(self.session)
        answer = AsyncMock(
            return_value={
                "status": "answered",
                "answer": "Docker and the API connect through local automation.",
                "evidence": [{"nodeId": 7}],
                "provider": "local",
                "model": "main",
            }
        )
        with patch("berrybrain_api.ask_flow.answer_cognitive_query", answer):
            await append_ask_turn(
                self.session, flow.id, "How does Docker connect to the API?"
            )

        result = create_insight_from_flow_session(self.session, flow.id)

        self.assertEqual(result["status"], "created")
        self.assertIsNotNone(result["insight"]["id"])
        self.assertIsNotNone(self.session.get(InsightRecord, result["insight"]["id"]))
        inference = (
            self.session.query(GraphInferenceRecord)
            .filter_by(insight_id=result["insight"]["id"])
            .one()
        )
        # The saved turn only retains evidence IDs, not measured support signals.
        # IDs alone must not manufacture a confidence score.
        self.assertEqual(inference.confidence_sample_size, 0)
        self.assertEqual(
            inference.confidence_method,
            "unavailable",
        )

    async def test_cancelled_turn_does_not_persist_provider_answer(self) -> None:
        flow = create_ask_session(self.session)

        async def cancel_during_provider_call(*_args, **_kwargs):
            cancel_ask_session(self.session, flow.id)
            return {"answer": "This answer must be discarded.", "evidence": []}

        with (
            patch(
                "berrybrain_api.ask_flow.answer_cognitive_query",
                side_effect=cancel_during_provider_call,
            ),
            self.assertRaisesRegex(HTTPException, "cancelled"),
        ):
            await append_ask_turn(self.session, flow.id, "Cancel this turn")

        payload = get_ask_session_payload(self.session, flow.id)
        self.assertEqual(len(payload["turns"]), 1)
        self.assertEqual(payload["turns"][0]["status"], "cancelled")

    async def test_closed_session_does_not_persist_provider_answer(self) -> None:
        flow = create_ask_session(self.session)

        async def close_during_provider_call(*_args, **_kwargs):
            close_ask_session(self.session, flow.id)
            return {"answer": "This answer must be discarded.", "evidence": []}

        with (
            patch(
                "berrybrain_api.ask_flow.answer_cognitive_query",
                side_effect=close_during_provider_call,
            ),
            self.assertRaisesRegex(HTTPException, "cancelled"),
        ):
            await append_ask_turn(self.session, flow.id, "Close this session")

        payload = get_ask_session_payload(self.session, flow.id)
        self.assertFalse(payload["session"]["active"])
        self.assertEqual(len(payload["turns"]), 1)
        self.assertEqual(payload["turns"][0]["status"], "cancelled")

    async def test_failed_turn_does_not_persist_late_provider_answer(self) -> None:
        flow = create_ask_session(self.session)

        async def fail_during_provider_call(*_args, **_kwargs):
            turn = self.session.query(AskTurnRecord).filter_by(session_id=flow.id).one()
            turn.status = "failed"
            self.session.commit()
            return {"answer": "This answer must be discarded.", "evidence": []}

        with (
            patch(
                "berrybrain_api.ask_flow.answer_cognitive_query",
                side_effect=fail_during_provider_call,
            ),
            self.assertRaisesRegex(HTTPException, "no longer processing"),
        ):
            await append_ask_turn(self.session, flow.id, "Interrupted request")

        payload = get_ask_session_payload(self.session, flow.id)
        self.assertEqual(len(payload["turns"]), 1)
        self.assertEqual(payload["turns"][0]["status"], "failed")

    async def test_provider_error_does_not_override_cancelled_turn(self) -> None:
        flow = create_ask_session(self.session)

        async def cancel_then_fail(*_args, **_kwargs):
            cancel_ask_session(self.session, flow.id)
            raise RuntimeError("Provider failed after cancellation")

        with (
            patch(
                "berrybrain_api.ask_flow.answer_cognitive_query",
                side_effect=cancel_then_fail,
            ),
            self.assertRaisesRegex(RuntimeError, "after cancellation"),
        ):
            await append_ask_turn(self.session, flow.id, "Cancel before failure")

        payload = get_ask_session_payload(self.session, flow.id)
        self.assertEqual(len(payload["turns"]), 1)
        self.assertEqual(payload["turns"][0]["status"], "cancelled")

    async def test_cancel_between_provider_return_and_final_write_discards_answer(
        self,
    ) -> None:
        from berrybrain_api import ask_flow

        flow = create_ask_session(self.session)
        finish = ask_flow._finish_processing_turn

        def cancel_before_final_write(session, turn_id, status):
            cancel_ask_session(self.session, flow.id)
            return finish(session, turn_id, status)

        with (
            patch(
                "berrybrain_api.ask_flow.answer_cognitive_query",
                AsyncMock(return_value={"answer": "Late answer", "evidence": []}),
            ),
            patch(
                "berrybrain_api.ask_flow._finish_processing_turn",
                side_effect=cancel_before_final_write,
            ),
            self.assertRaisesRegex(HTTPException, "cancelled") as error,
        ):
            await append_ask_turn(self.session, flow.id, "Race with cancel")

        self.assertEqual(error.exception.status_code, 409)
        payload = get_ask_session_payload(self.session, flow.id)
        self.assertEqual(len(payload["turns"]), 1)
        self.assertEqual(payload["turns"][0]["status"], "cancelled")

    async def test_cancel_between_provider_failure_and_final_write_stays_cancelled(
        self,
    ) -> None:
        from berrybrain_api import ask_flow

        flow = create_ask_session(self.session)
        finish = ask_flow._finish_processing_turn

        def cancel_before_final_write(session, turn_id, status):
            cancel_ask_session(self.session, flow.id)
            return finish(session, turn_id, status)

        with (
            patch(
                "berrybrain_api.ask_flow.answer_cognitive_query",
                AsyncMock(return_value={"status": "waiting_provider"}),
            ),
            patch(
                "berrybrain_api.ask_flow._finish_processing_turn",
                side_effect=cancel_before_final_write,
            ),
            self.assertRaisesRegex(HTTPException, "cancelled") as error,
        ):
            await append_ask_turn(self.session, flow.id, "Race with provider error")

        self.assertEqual(error.exception.status_code, 409)
        payload = get_ask_session_payload(self.session, flow.id)
        self.assertEqual(len(payload["turns"]), 1)
        self.assertEqual(payload["turns"][0]["status"], "cancelled")

    async def test_other_question_is_rejected_while_turn_is_processing(self) -> None:
        flow = create_ask_session(self.session)
        self.session.add(
            AskTurnRecord(
                session_id=flow.id,
                sequence=1,
                role="user",
                content="First question",
                status="processing",
            )
        )
        self.session.commit()

        with self.assertRaisesRegex(HTTPException, "already processing") as error:
            await append_ask_turn(self.session, flow.id, "Different question")

        self.assertEqual(error.exception.status_code, 409)
        self.assertEqual(
            len(get_ask_session_payload(self.session, flow.id)["turns"]), 1
        )

    async def test_unique_processing_turn_collision_returns_conflict(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            engine = create_engine(f"sqlite:///{Path(directory) / 'flow.db'}")
            Base.metadata.create_all(engine)
            first = sessionmaker(bind=engine)()
            contender = sessionmaker(bind=engine)()
            try:
                save_configuration(
                    first,
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
                flow = create_ask_session(first)
                commit_first = first.commit

                def commit_after_competitor() -> None:
                    contender.add(
                        AskTurnRecord(
                            session_id=flow.id,
                            sequence=1,
                            role="user",
                            content="Competing question",
                            status="processing",
                        )
                    )
                    contender.commit()
                    commit_first()

                with (
                    patch.object(first, "commit", side_effect=commit_after_competitor),
                    self.assertRaises(HTTPException) as error,
                ):
                    await append_ask_turn(first, flow.id, "My question")

                self.assertEqual(error.exception.status_code, 409)
                self.assertEqual(
                    [
                        turn["content"]
                        for turn in get_ask_session_payload(first, flow.id)["turns"]
                    ],
                    ["Competing question"],
                )
            finally:
                first.close()
                contender.close()
                engine.dispose()

    async def test_provider_failure_does_not_persist_assistant_answer(self) -> None:
        flow = create_ask_session(self.session)
        answer = AsyncMock(
            return_value={
                "status": "waiting_provider",
                "answer": "",
                "evidence": [{"nodeId": 7}],
            }
        )

        with (
            patch("berrybrain_api.ask_flow.answer_cognitive_query", answer),
            self.assertRaises(HTTPException) as raised,
        ):
            await append_ask_turn(self.session, flow.id, "Retry this question")

        self.assertEqual(raised.exception.status_code, 503)
        self.assertEqual(raised.exception.detail["code"], "provider_unavailable")
        payload = get_ask_session_payload(self.session, flow.id)
        self.assertEqual(len(payload["turns"]), 1)
        self.assertEqual(payload["turns"][0]["status"], "failed")
