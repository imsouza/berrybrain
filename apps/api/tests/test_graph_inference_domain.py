import ast
import unittest
from pathlib import Path

from berrybrain_api.modules.graph_inference.domain import (
    InferenceNotSavableError,
    InferenceSnapshot,
    MissingGroundedEvidenceError,
    build_insight_draft,
)


def snapshot(**changes) -> InferenceSnapshot:
    values = {
        "id": 1,
        "question": "How are Docker and shell connected?",
        "answer": "Shell scripts automate Docker workflows.",
        "status": "answered",
        "confidence": 0.82,
        "routes": ("knowledge_base", "knowledge_graph"),
        "evidence": ("Docker note", "Shell note"),
        "related_nodes": ("note_1", "note_2"),
        "provider": "nvidia-nim",
        "model": "test-model",
        "prompt_version": "graph-inference.v2",
    }
    values.update(changes)
    return InferenceSnapshot(**values)


class GraphInferenceDomainTest(unittest.TestCase):
    def test_grounded_answer_builds_connection_insight(self) -> None:
        draft = build_insight_draft(snapshot())

        self.assertEqual(draft.type, "new_connection")
        self.assertTrue(draft.grounded)
        self.assertEqual(draft.confidence, 0.82)
        self.assertEqual(len(draft.evidence), 2)

    def test_insufficient_answer_builds_gap_without_inventing_evidence(self) -> None:
        draft = build_insight_draft(
            snapshot(
                status="insufficient_evidence",
                answer="There is not enough evidence.",
                confidence=0.0,
                evidence=(),
            )
        )

        self.assertEqual(draft.type, "knowledge_gap")
        self.assertFalse(draft.grounded)
        self.assertIn("found no sufficient", str(draft.evidence[0]))

    def test_provider_failure_is_not_knowledge(self) -> None:
        with self.assertRaises(InferenceNotSavableError):
            build_insight_draft(snapshot(status="waiting_provider"))

    def test_grounded_answer_requires_evidence(self) -> None:
        with self.assertRaises(MissingGroundedEvidenceError):
            build_insight_draft(snapshot(evidence=()))


class GraphInferenceArchitectureTest(unittest.TestCase):
    def test_domain_has_no_framework_or_persistence_imports(self) -> None:
        path = (
            Path(__file__).parents[1]
            / "src/berrybrain_api/modules/graph_inference/domain.py"
        )
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)

        banned = ("fastapi", "sqlalchemy", "berrybrain_api.database", "routers")
        self.assertFalse(
            [name for name in imported if name.startswith(banned)],
            f"Domain imports infrastructure: {sorted(imported)}",
        )

    def test_application_service_does_not_open_database_sessions(self) -> None:
        path = (
            Path(__file__).parents[1] / "src/berrybrain_api/graph_inference_service.py"
        )
        source = path.read_text(encoding="utf-8")
        self.assertNotIn("SessionLocal", source)


if __name__ == "__main__":
    unittest.main()
