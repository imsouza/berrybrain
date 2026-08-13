import unittest

from pydantic import ValidationError

from berrybrain_api.confidence import ConfidenceSignal, estimate_confidence
from berrybrain_api.graph_contracts import canonical_edge_type
from berrybrain_api.graph_ontology import validate_edge_types, validate_node_name
from berrybrain_api.routers.graph import UpdateGraphNodeRequest


class GraphOntologyConfidenceTest(unittest.TestCase):
    def test_confidence_is_unavailable_without_evidence(self) -> None:
        estimate = estimate_confidence([])
        self.assertIsNone(estimate.score)
        self.assertEqual(estimate.sample_size, 0)
        self.assertEqual(estimate.method, "unavailable")

    def test_confidence_interval_comes_from_distinct_evidence(self) -> None:
        estimate = estimate_confidence(
            [
                ConfidenceSignal(1.0, "note:1"),
                ConfidenceSignal(0.8, "judge:1"),
                ConfidenceSignal(0.2, "judge:1"),
            ]
        )
        self.assertEqual(estimate.sample_size, 2)
        self.assertAlmostEqual(estimate.score or 0, 0.766667)
        self.assertEqual(estimate.method, "jeffreys-wilson-evidence-v2")
        self.assertLess(estimate.lower or 0, estimate.score or 0)
        self.assertGreater(estimate.upper or 0, estimate.score or 0)

    def test_positive_evidence_does_not_claim_absolute_certainty(self) -> None:
        estimate = estimate_confidence(
            [
                ConfidenceSignal(1.0, "note:1"),
                ConfidenceSignal(1.0, "model:1"),
                ConfidenceSignal(1.0, "evidence:1"),
            ]
        )

        self.assertAlmostEqual(estimate.score or 0, 0.875)
        self.assertLess(estimate.lower or 0, estimate.score or 0)
        self.assertEqual(estimate.upper, 1.0)

    def test_name_validator_rejects_metadata_and_sentences(self) -> None:
        self.assertTrue(validate_node_name("concept", "markdown content"))
        self.assertTrue(validate_node_name("concept", "I am Jordan Lee"))
        self.assertEqual(validate_node_name("concept", "time series"), [])
        self.assertEqual(validate_node_name("entity", "OpenAI"), [])

    def test_edge_contract_enforces_direction_and_domain(self) -> None:
        self.assertEqual(validate_edge_types("mentions", "note", "concept"), [])
        self.assertTrue(validate_edge_types("mentions", "concept", "note"))
        self.assertEqual(canonical_edge_type("backlink"), "references")
        self.assertEqual(canonical_edge_type("prerequisite"), "prerequisite_for")

    def test_node_edit_contract_rejects_confidence(self) -> None:
        with self.assertRaises(ValidationError):
            UpdateGraphNodeRequest(label="Time series", confidence=0.99)


if __name__ == "__main__":
    unittest.main()
