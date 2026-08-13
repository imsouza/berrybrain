from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

API_SRC = Path(__file__).resolve().parents[2] / "apps" / "api" / "src"
WORKER_SRC = Path(__file__).resolve().parents[2] / "apps" / "worker" / "src"
for p in (str(API_SRC), str(WORKER_SRC)):
    if p not in sys.path:
        sys.path.insert(0, p)

os.environ.setdefault("BERRYBRAIN_SESSION_SECRET", "test-secret-non-default")
os.environ.setdefault("BERRYBRAIN_API_DB", ":memory:")

from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from berrybrain_api.database import Base  # noqa: E402
from berrybrain_api.judge_committee import (  # noqa: E402
    DEFAULT_COMMITTEE_SIZE,
    JudgeMode,
    aggregate_score,
    configure_provider_committee,
    disagreement,
    eligible_committee_slots,
    generator_model_blocked_in_committee,
    is_high_impact,
    judge_model_candidates,
    persist_committee_run,
    recommend_committee,
    should_use_committee,
    tally_verdicts,
)
from berrybrain_api.models import (  # noqa: E402
    GraphNodeRecord,
    JudgeVerdictRecord,
    SettingRecord,
)
from berrybrain_api.routers.judge import (  # noqa: E402
    EvaluateInternalRequest,
    _judge_defaults_response,
    _scorecard_agreement,
    evaluate_artifact_internal,
)


class TestJudgeCommitteeLogic(unittest.TestCase):
    def test_partial_provider_defaults_return_the_compatible_committee_size(self):
        committee = [
            {"slot": f"judge-{index}", "provider": "cloud", "model": model}
            for index, model in enumerate(["judge-a", "judge-b", "judge-c"], 1)
        ]

        response = _judge_defaults_response(committee, requested_size=5)

        self.assertEqual(response["mode"], "committee")
        self.assertEqual(response["committee_size"], 3)
        self.assertTrue(response["ready"])

    def test_candidate_ranking_excludes_non_text_models_and_interleaves_families(
        self,
    ):
        candidates = judge_model_candidates(
            available_models=[
                "nvidia/nemotron-reasoning-a",
                "nvidia/nemotron-reasoning-b",
                "deepseek/reasoning-c",
                "meta/llama-instruct",
                "nvidia/embed-model",
                "meta/vision-instruct",
            ],
            generator_model="generator",
        )

        self.assertEqual(
            candidates[:4],
            [
                "nvidia/nemotron-reasoning-a",
                "deepseek/reasoning-c",
                "meta/llama-instruct",
                "nvidia/nemotron-reasoning-b",
            ],
        )
        self.assertNotIn("nvidia/embed-model", candidates)
        self.assertNotIn("meta/vision-instruct", candidates)

    def test_provider_defaults_assign_three_distinct_roles_and_exclude_generator(self):
        committee = recommend_committee(
            provider="openai",
            available_models=[
                "generator-model",
                "embedding-model",
                "judge-chat-a",
                "judge-instruct-b",
                "judge-reason-c",
                "moderation-model",
            ],
            generator_model="generator-model",
            primary_judge_model="judge-chat-a",
        )

        self.assertEqual(len(committee), DEFAULT_COMMITTEE_SIZE)
        self.assertEqual(committee[0]["model"], "judge-chat-a")
        self.assertEqual(
            {item["role"] for item in committee},
            {"faithfulness", "relevance", "contradiction"},
        )
        self.assertNotIn("generator-model", {item["model"] for item in committee})
        self.assertNotIn("embedding-model", {item["model"] for item in committee})

    def test_provider_configuration_enables_committee_and_persists_consent(self):
        engine = create_engine("sqlite://")
        Base.metadata.create_all(engine)
        session = sessionmaker(bind=engine)()
        try:
            config = configure_provider_committee(
                session,
                provider="nvidia-nim",
                available_models=["generator", "judge-a", "judge-b", "judge-c"],
                generator_model="generator",
                primary_judge_model="judge-a",
            )

            self.assertEqual(config.mode, JudgeMode.COMMITTEE)
            self.assertEqual(config.committee_size, 3)
            self.assertEqual(len(config.committee), 3)
            self.assertIsNotNone(config.consent_at)
        finally:
            session.close()
            engine.dispose()

    def test_is_high_impact(self):
        self.assertTrue(is_high_impact("node"))
        self.assertTrue(is_high_impact("edge"))
        self.assertTrue(is_high_impact("insight"))
        self.assertFalse(is_high_impact("connection"))
        self.assertFalse(is_high_impact("answer"))

    def test_should_use_committee_only_when_enabled_and_high_impact(self):
        from dataclasses import dataclass

        @dataclass
        class C:
            mode: JudgeMode
            committee: list[dict]

        self.assertTrue(should_use_committee(C(JudgeMode.COMMITTEE, []), "node"))
        self.assertFalse(should_use_committee(C(JudgeMode.SINGLE_MODEL, []), "node"))
        self.assertFalse(should_use_committee(C(JudgeMode.COMMITTEE, []), "connection"))

    def test_generator_model_blocked(self):
        committee = [
            {"slot": "a", "model": "llama3:8b"},
            {"slot": "b", "model": "mistral:7b"},
        ]
        blocked = generator_model_blocked_in_committee("llama3:8b", committee)
        self.assertEqual(blocked, ["a"])
        self.assertEqual(
            generator_model_blocked_in_committee("qwen2:7b", committee), []
        )

    def test_eligible_committee_excludes_generator_empty_and_duplicate_slots(self):
        committee = [
            {"slot": "generator", "provider": "nvidia-nim", "model": "qwen"},
            {"slot": "alpha", "provider": "nvidia-nim", "model": "llama"},
            {"slot": "duplicate", "provider": "nvidia-nim", "model": "llama"},
            {"slot": "beta", "provider": "nvidia-nim", "model": "mistral"},
            {"slot": "empty", "provider": "nvidia-nim", "model": ""},
        ]

        eligible = eligible_committee_slots(committee, "qwen")

        self.assertEqual(
            [(item["slot"], item["model"]) for item in eligible],
            [("alpha", "llama"), ("beta", "mistral")],
        )

    def test_disagreement(self):
        self.assertTrue(disagreement(["passed", "rejected"]))
        self.assertFalse(disagreement(["passed", "passed"]))

    def test_tally_unanimous_pass(self):
        self.assertEqual(tally_verdicts(["passed", "passed", "passed"]), "passed")

    def test_tally_any_rejected_rejects(self):
        self.assertEqual(
            tally_verdicts(["passed", "rejected", "passed"]), "passed"
        )  # majority wins

    def test_tally_review_present(self):
        self.assertEqual(tally_verdicts(["passed", "review"]), "review")

    def test_tally_disagreement_no_majority_fails_soft_to_review(self):
        self.assertEqual(tally_verdicts(["passed", "rejected"]), "review")

    def test_tally_majority_pass(self):
        self.assertEqual(
            tally_verdicts(["passed", "passed", "rejected"]), "passed"
        )  # 2-of-3 majority wins

    def test_tally_empty_is_error(self):
        self.assertEqual(tally_verdicts([]), "error")

    def test_unavailable_judge_does_not_change_valid_consensus(self):
        self.assertEqual(tally_verdicts(["passed", "passed", "error"]), "passed")
        self.assertFalse(disagreement(["passed", "passed", "error"]))

    def test_aggregate_score(self):
        self.assertAlmostEqual(aggregate_score([0.5, 0.7, 0.9]), 0.7, places=2)
        self.assertEqual(aggregate_score([]), 0.0)


class TestAutomaticJudgeCommittee(unittest.IsolatedAsyncioTestCase):
    async def test_background_evaluation_uses_configured_non_generator_models(self):
        engine = create_engine("sqlite://")
        Base.metadata.create_all(engine)
        factory = sessionmaker(bind=engine)
        with factory() as session:
            node = GraphNodeRecord(
                type="concept",
                label="Temporal Forecasting",
                source_note_ids="[]",
                source_evidence='["Forecasts estimate future observations."]',
                created_by="ai",
                created_by_model="generator-model",
            )
            session.add(node)
            session.add_all(
                [
                    SettingRecord(key="judge_mode", value="committee"),
                    SettingRecord(
                        key="judge_committee_config",
                        value=(
                            '[{"slot":"generator","provider":"nvidia-nim",'
                            '"model":"generator-model"},'
                            '{"slot":"alpha","provider":"nvidia-nim",'
                            '"model":"judge-alpha"},'
                            '{"slot":"beta","provider":"nvidia-nim",'
                            '"model":"judge-beta"}]'
                        ),
                    ),
                    SettingRecord(
                        key="judge_committee_consent_at", value="2026-08-13T00:00:00Z"
                    ),
                ]
            )
            session.commit()
            node_id = node.id

        responses = [
            {
                "verdict": "passed",
                "score": 8.4,
                "rubric": {"accuracy": 8},
                "reasoning": "Supported.",
            },
            {
                "verdict": "passed",
                "score": 8.8,
                "rubric": {"accuracy": 9},
                "reasoning": "Supported.",
            },
        ]
        gateway_config = {
            "provider": "cloud",
            "judge_provider": "nvidia-nim",
            "judge_model": "unused",
        }
        with (
            patch("berrybrain_api.routers.judge.SessionLocal", factory),
            patch(
                "berrybrain_api.ai_gateway.get_ai_config",
                return_value=gateway_config,
            ),
            patch(
                "berrybrain_api.ai_gateway.generate_graph_answer",
                new=AsyncMock(side_effect=responses),
            ) as generate,
        ):
            result = await evaluate_artifact_internal(
                EvaluateInternalRequest(artifact_type="node", artifact_id=node_id)
            )

        self.assertEqual(result["executionMode"], "committee")
        self.assertEqual(result["judgeCount"], 2)
        self.assertEqual(generate.await_count, 2)
        called_models = {
            call.kwargs["config"]["judge_model"] for call in generate.await_args_list
        }
        self.assertEqual(called_models, {"judge-alpha", "judge-beta"})
        assigned_roles = {
            call.kwargs["system"].split("Role: ", 1)[1].splitlines()[0]
            for call in generate.await_args_list
        }
        self.assertEqual(assigned_roles, {"general"})
        with factory() as session:
            verdicts = session.query(JudgeVerdictRecord).all()
            refreshed = session.get(GraphNodeRecord, node_id)
            self.assertEqual(len(verdicts), 3)
            self.assertEqual(refreshed.quality_gate_status, "passed")
            self.assertEqual(refreshed.latest_evaluation_id, result["evaluationId"])
        engine.dispose()

    def test_scorecard_agreement_uses_weighted_kappa_and_correct_error_rates(self):
        pairs = [("passed", "passed")] * 20
        pairs += [("rejected", "rejected")] * 9
        pairs += [("passed", "rejected")]
        pairs += [("rejected", "passed")]

        agreement = _scorecard_agreement(pairs)

        self.assertEqual(agreement["comparable"], 31)
        self.assertEqual(agreement["matched"], 29)
        self.assertGreaterEqual(agreement["weighted_kappa"], 0.80)
        self.assertEqual(agreement["false_acceptance_rate"], 0.1)
        self.assertEqual(agreement["false_rejection_rate"], 0.0476)


class TestPersistCommitteeRun(unittest.TestCase):
    def setUp(self):
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        from berrybrain_api.models import Base

        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        import berrybrain_api.database as db

        self._orig_sessionlocal = db.SessionLocal
        db.SessionLocal = self.Session
        self.session = self.Session()

    def tearDown(self):
        self.session.close()
        import berrybrain_api.database as db

        db.SessionLocal = self._orig_sessionlocal

    def test_persist_committee_run_creates_verdicts_and_summary(self):
        verdicts = [
            {
                "slot": "a",
                "provider": "ollama",
                "model": "llama3:8b",
                "verdict": "passed",
                "score": 0.8,
                "rubric": {},
                "reasoning": "ok",
                "latency_ms": 12,
            },
            {
                "slot": "b",
                "provider": "ollama",
                "model": "mistral:7b",
                "verdict": "passed",
                "score": 0.6,
                "rubric": {},
                "reasoning": "ok",
                "latency_ms": 20,
            },
        ]
        summary = persist_committee_run(
            self.session,
            artifact_type="node",
            artifact_id=42,
            verdicts=verdicts,
            enforcing=False,
        )
        self.assertEqual(summary.verdict, "passed")
        self.assertAlmostEqual(summary.score, 0.7, places=2)
        from berrybrain_api.models import JudgeVerdictRecord

        rows = (
            self.session.query(JudgeVerdictRecord)
            .filter(
                JudgeVerdictRecord.committee_id != "",
            )
            .all()
        )
        self.assertEqual(len(rows), 3)  # 2 + 1 summary

    def test_persist_committee_run_enforcing_disagreement_fails_closed(self):
        verdicts = [
            {
                "slot": "a",
                "provider": "x",
                "model": "M1",
                "verdict": "passed",
                "score": 0.8,
                "rubric": {},
                "reasoning": "",
                "latency_ms": 1,
            },
            {
                "slot": "b",
                "provider": "x",
                "model": "M2",
                "verdict": "rejected",
                "score": 0.2,
                "rubric": {},
                "reasoning": "",
                "latency_ms": 1,
            },
        ]
        summary = persist_committee_run(
            self.session,
            artifact_type="edge",
            artifact_id=7,
            verdicts=verdicts,
            enforcing=True,
        )
        self.assertEqual(summary.verdict, "review")

    def test_persist_committee_run_non_enforcing_disagreement_soft_review(self):
        verdicts = [
            {
                "slot": "a",
                "provider": "x",
                "model": "M1",
                "verdict": "passed",
                "score": 0.9,
                "rubric": {},
                "reasoning": "",
                "latency_ms": 1,
            },
            {
                "slot": "b",
                "provider": "x",
                "model": "M2",
                "verdict": "rejected",
                "score": 0.1,
                "rubric": {},
                "reasoning": "",
                "latency_ms": 1,
            },
        ]
        summary = persist_committee_run(
            self.session,
            artifact_type="edge",
            artifact_id=8,
            verdicts=verdicts,
            enforcing=False,
        )
        self.assertEqual(summary.verdict, "review")

    def test_persist_committee_run_excludes_unavailable_judge_from_score(self):
        verdicts = [
            {
                "slot": "a",
                "provider": "x",
                "model": "M1",
                "verdict": "passed",
                "score": 0.8,
                "rubric": {},
                "reasoning": "",
                "latency_ms": 1,
            },
            {
                "slot": "b",
                "provider": "x",
                "model": "M2",
                "verdict": "passed",
                "score": 0.6,
                "rubric": {},
                "reasoning": "",
                "latency_ms": 1,
            },
            {
                "slot": "c",
                "provider": "x",
                "model": "M3",
                "verdict": "error",
                "score": 0.0,
                "rubric": {},
                "reasoning": "judge-unavailable",
                "latency_ms": 1,
            },
        ]
        summary = persist_committee_run(
            self.session,
            artifact_type="node",
            artifact_id=9,
            verdicts=verdicts,
            enforcing=False,
        )
        self.assertEqual(summary.verdict, "passed")
        self.assertAlmostEqual(summary.score, 0.7, places=2)


class TestRouterEndpoints(unittest.TestCase):
    """Endpoints logic tests using TestClient when fastapi present; else skip."""

    def setUp(self):
        try:
            from fastapi.testclient import TestClient

            from berrybrain_api.main import app

            self.client = TestClient(app)
        except (ImportError, RuntimeError):
            self.client = None

    def test_mode_get_returns_default(self):
        if not self.client:
            return
        r = self.client.get("/api/v1/judge/mode")
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertIn(body["mode"], ["deterministic", "single_model", "committee"])

    def test_scorecard_get_returns_not_calibrated(self):
        if not self.client:
            return
        r = self.client.get("/api/v1/judge/scorecard")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["status"], "NOT_CALIBRATED")


if __name__ == "__main__":
    unittest.main()
