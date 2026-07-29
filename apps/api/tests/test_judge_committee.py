from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

API_SRC = Path(__file__).resolve().parents[2] / "apps" / "api" / "src"
WORKER_SRC = Path(__file__).resolve().parents[2] / "apps" / "worker" / "src"
for p in (str(API_SRC), str(WORKER_SRC)):
    if p not in sys.path:
        sys.path.insert(0, p)

os.environ.setdefault("BERRYBRAIN_SESSION_SECRET", "test-secret-non-default")
os.environ.setdefault("BERRYBRAIN_API_DB", ":memory:")

from berrybrain_api.judge_committee import (  # noqa: E402
    JudgeMode,
    aggregate_score,
    disagreement,
    generator_model_blocked_in_committee,
    is_high_impact,
    persist_committee_run,
    should_use_committee,
    tally_verdicts,
)
from berrybrain_api.routers.judge import _scorecard_agreement  # noqa: E402


class TestJudgeCommitteeLogic(unittest.TestCase):
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

    def test_aggregate_score(self):
        self.assertAlmostEqual(aggregate_score([0.5, 0.7, 0.9]), 0.7, places=2)
        self.assertEqual(aggregate_score([]), 0.0)

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
