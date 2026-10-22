import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import HTTPException
from pydantic import ValidationError

from berrybrain_api.routers import judge


class JudgePromptTest(unittest.TestCase):
    def test_submission_rejects_invalid_scores_and_verdicts(self):
        payload = dict(
            artifact_type="node",
            artifact_id=1,
            verdict="passed",
            score=0.8,
            rubric="{}",
            reasoning="fixture",
            evidence_used="[]",
            provider="fixture",
            model="judge",
            prompt_version="test",
        )
        for score in (True, "0.8", float("nan"), -1, 80):
            with self.subTest(score=score), self.assertRaises(ValidationError):
                judge.ArtifactEvaluationCreate(**{**payload, "score": score})
        with self.assertRaises(ValidationError):
            judge.ArtifactEvaluationCreate(**{**payload, "verdict": "unknown"})

    def test_internal_judge_total_is_derived_from_rubric_not_self_report(self):
        rubric = dict(
            accuracy=9, relevance=8, semantic_coherence=8, evidence_quality=9, clarity=8
        )
        verdict, score, _ = judge._parse_judge_result(
            {"rubric": rubric, "verdict": "passed", "score": 0.5}
        )
        self.assertEqual(verdict, "passed")
        self.assertAlmostEqual(score, 0.84)
        rubric["accuracy"] = 5
        verdict, _, _ = judge._parse_judge_result(
            {"rubric": rubric, "verdict": "passed"}
        )
        self.assertEqual(verdict, "rejected")
        rubric["accuracy"] = 6
        verdict, _, _ = judge._parse_judge_result(
            {"rubric": rubric, "verdict": "passed"}
        )
        self.assertEqual(verdict, "review")

    def test_incomplete_or_invalid_rubric_is_not_defaulted_to_zero(self):
        for value in (None, True, "8", float("nan"), -1, 11):
            rubric = dict(
                accuracy=value,
                relevance=8,
                semantic_coherence=8,
                evidence_quality=8,
                clarity=8,
            )
            with self.subTest(value=value), self.assertRaises(ValueError):
                judge._parse_judge_result({"rubric": rubric, "verdict": "passed"})
        with self.assertRaises(ValueError):
            judge._parse_judge_result({"rubric": {}, "verdict": "passed", "score": 1})

    def test_judge_score_requires_a_real_bounded_measurement(self) -> None:
        for invalid in (None, True, False, "0.8", -1, 80, float("nan"), float("inf")):
            with self.subTest(value=invalid), self.assertRaises(ValueError):
                judge._validated_judge_score(invalid)
        self.assertEqual(judge._validated_judge_score(0), 0.0)
        self.assertEqual(judge._validated_judge_score(0.73), 0.73)

    def test_submitted_evaluation_updates_support_from_actual_judge_score(self):
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        from berrybrain_api.models import Base, GraphNodeRecord

        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        factory = sessionmaker(bind=engine)
        with factory() as session:
            node = GraphNodeRecord(type="concept", label="Graphs", confidence=0.5)
            session.add(node)
            session.commit()
            node_id = node.id
        with patch.object(judge, "SessionLocal", factory):
            for score in (0.8, 0.2, 0.0):
                judge.submit_evaluation(
                    judge.ArtifactEvaluationCreate(
                        artifact_type="node",
                        artifact_id=node_id,
                        verdict="review",
                        score=score,
                        rubric="{}",
                        reasoning="fixture",
                        evidence_used="[]",
                        provider="fixture",
                        model="judge",
                        prompt_version="test",
                    )
                )
                with factory() as session:
                    node = session.get(GraphNodeRecord, node_id)
                    self.assertEqual(node.confidence, score)
                    self.assertEqual(node.confidence_sample_size, 1)
                    self.assertEqual(node.confidence_method, "evidence-support-mean-v2")
        engine.dispose()

    def test_routes_canonical_provider_id_through_its_mode(self) -> None:
        routed = judge._with_judge_route(
            {
                "provider": "cloud",
                "judge_provider": "nvidia-nim",
                "judge_model": "judge-model",
                "fallback_provider": "opencode-zen",
                "fallback_model": "main-backup-not-a-judge",
                "fallback_api_key": "fake-key",
            }
        )

        self.assertEqual(routed["provider"], "cloud")
        self.assertEqual(routed["cloud_model"], "judge-model")
        self.assertFalse(any(key.startswith("fallback_") for key in routed))

    def test_rejects_mixed_judge_mode(self) -> None:
        with self.assertRaisesRegex(ValueError, "cannot mix"):
            judge._with_judge_route(
                {
                    "provider": "cloud",
                    "judge_provider": "ollama",
                    "judge_model": "local-judge",
                }
            )

    def test_loads_the_versioned_prompt_from_project_root(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            prompt_dir = Path(root) / "prompts"
            prompt_dir.mkdir()
            (prompt_dir / judge.JUDGE_PROMPT_VERSION).write_text(
                "Evaluate the artifact.", encoding="utf-8"
            )
            with patch.object(judge, "PROJECT_ROOT", Path(root)):
                self.assertEqual(judge._load_judge_prompt(), "Evaluate the artifact.")

    def test_missing_prompt_is_a_retryable_service_failure(self) -> None:
        with (
            tempfile.TemporaryDirectory() as root,
            patch.object(judge, "PROJECT_ROOT", Path(root)),
            self.assertRaises(HTTPException) as error,
        ):
            judge._load_judge_prompt()

        self.assertEqual(error.exception.status_code, 503)


if __name__ == "__main__":
    unittest.main()
