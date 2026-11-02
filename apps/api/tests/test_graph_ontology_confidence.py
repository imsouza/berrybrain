import unittest
from math import log
from types import SimpleNamespace

from pydantic import ValidationError

from berrybrain_api.confidence import (
    ConfidenceSignal,
    active_node_confidence,
    estimate_confidence,
    evidence_coverage_signal,
    node_confidence_applicable,
    parse_unit_confidence,
    persist_confidence,
    persist_judge_confidence,
    serialize_confidence,
    serialize_percentage_confidence,
)
from berrybrain_api.graph_contracts import canonical_edge_type
from berrybrain_api.graph_ontology import validate_edge_types, validate_node_name
from berrybrain_api.graph_write_service import recalculate_node_confidence
from berrybrain_api.routers.graph import UpdateGraphNodeRequest


class GraphOntologyConfidenceTest(unittest.TestCase):
    def test_model_score_parser_keeps_real_zero_and_rejects_nonfinite_values(
        self,
    ) -> None:
        self.assertEqual(parse_unit_confidence(0), 0.0)
        self.assertEqual(parse_unit_confidence("0.5"), 0.5)
        self.assertEqual(parse_unit_confidence(1), 1.0)
        for value in (None, True, "invalid", -0.1, 1.1, float("nan"), float("inf")):
            with self.subTest(value=value):
                self.assertIsNone(parse_unit_confidence(value))

    def test_source_nodes_have_no_active_confidence(self) -> None:
        for node_type in (
            "note",
            "vault",
            "source",
            "web_source",
            "attachment",
            "cluster",
            "unknown",
        ):
            with self.subTest(node_type=node_type):
                node = SimpleNamespace(
                    __tablename__="graph_nodes",
                    type=node_type,
                    confidence=0.95,
                    confidence_sample_size=3,
                    confidence_method="evidence-support-mean-v2",
                )
                self.assertFalse(node_confidence_applicable(node_type))
                self.assertIsNone(active_node_confidence(node))
                self.assertEqual(serialize_confidence(node)["method"], "not_applicable")
                self.assertIsNone(serialize_confidence(node)["score"])
                recalculate_node_confidence(node)
                persist_judge_confidence(node, 1.0)
                self.assertEqual(node.confidence, 0.95)

    def test_derived_node_can_keep_a_measured_zero(self) -> None:
        node = SimpleNamespace(
            __tablename__="graph_nodes",
            type="concept",
            confidence=0.0,
            confidence_sample_size=1,
            confidence_method="evidence-support-mean-v2",
        )
        self.assertTrue(node_confidence_applicable(node.type))
        self.assertEqual(active_node_confidence(node), 0.0)
        self.assertEqual(serialize_confidence(node)["score"], 0.0)

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
        self.assertAlmostEqual(estimate.score or 0, 0.9)
        self.assertEqual(estimate.method, "evidence-support-mean-v2")
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

        self.assertAlmostEqual(estimate.score or 0, 1.0)
        self.assertLess(estimate.lower or 0, estimate.score or 0)
        self.assertEqual(estimate.upper, 1.0)

    def test_single_scored_signal_exposes_total_uncertainty(self) -> None:
        estimate = estimate_confidence([ConfidenceSignal(0.99, "judge:1")])

        self.assertEqual(estimate.sample_size, 1)
        self.assertEqual(estimate.lower, 0.0)
        self.assertEqual(estimate.upper, 1.0)
        self.assertEqual(estimate.score, 0.99)

    def test_wide_interval_does_not_erase_different_observations(self) -> None:
        for count in (1, 2, 3, 8):
            for value in (0.0, 0.1, 0.37, 0.8, 1.0):
                with self.subTest(count=count, value=value):
                    estimate = estimate_confidence(
                        [ConfidenceSignal(value, f"judge:{i}") for i in range(count)]
                    )
                    self.assertAlmostEqual(estimate.score, value)
                    self.assertEqual((estimate.lower, estimate.upper), (0.0, 1.0))

    def test_invalid_scores_are_not_clamped_or_counted(self) -> None:
        estimate = estimate_confidence(
            [
                ConfidenceSignal(value, str(i))
                for i, value in enumerate(
                    (True, False, float("nan"), float("inf"), -0.1, 1.1, "0.8", None)
                )
            ]
        )
        self.assertIsNone(estimate.score)
        self.assertEqual(estimate.sample_size, 0)

    def test_missing_text_is_not_negative_or_metadata_support(self) -> None:
        self.assertIsNone(evidence_coverage_signal(["sourceNoteId hash"], []))
        self.assertIsNone(
            evidence_coverage_signal(
                ["sourceNoteId hash"], [{"sourceNoteId": 3, "hash": "anything"}]
            )
        )
        coverage = evidence_coverage_signal(
            ["graph biology"], [{"excerpt": "graph theory", "hash": "biology"}]
        )
        self.assertEqual(coverage.score, 0.5)
        self.assertEqual(evidence_coverage_signal(["biology"], ["graph"]).score, 0)

    def test_observations_and_nominal_level_round_trip(self) -> None:
        target = SimpleNamespace()
        persist_confidence(target, estimate_confidence([(0.3, "model:x")], level=0.9))
        payload = serialize_confidence(target)
        self.assertEqual(payload["score"], 0.3)
        self.assertEqual(payload["level"], 0.9)
        self.assertEqual(payload["observations"], [{"score": 0.3, "source": "model:x"}])

    def test_judge_replaces_previous_score_instead_of_accumulating_retries(
        self,
    ) -> None:
        target = SimpleNamespace()
        persist_confidence(
            target, estimate_confidence([(0.6, "semantic:interpretation")])
        )
        persist_judge_confidence(target, 0.2)
        self.assertEqual(target.confidence, 0.4)
        persist_judge_confidence(target, 0.8)
        self.assertEqual(target.confidence, 0.7)
        self.assertEqual(target.confidence_sample_size, 2)
        persist_judge_confidence(target, 0)
        self.assertEqual(target.confidence, 0.3)
        persist_judge_confidence(target, None)
        self.assertEqual(target.confidence, 0.6)
        self.assertEqual(target.confidence_sample_size, 1)

    def test_legacy_midpoint_is_not_reused_as_an_observation(self) -> None:
        target = SimpleNamespace(confidence=0.5, confidence_factors='["model:old"]')
        persist_judge_confidence(target, 0.9)
        self.assertEqual(target.confidence, 0.9)
        self.assertEqual(target.confidence_sample_size, 1)

    def test_percentage_storage_keeps_one_percent_distinct_from_one(self) -> None:
        target = SimpleNamespace()
        persist_judge_confidence(target, 0.01, percentage=True)
        self.assertEqual(target.confidence, 1)
        self.assertEqual(serialize_percentage_confidence(target)["score"], 0.01)

    def test_malformed_stored_observation_does_not_break_judge_update(self) -> None:
        target = SimpleNamespace(
            confidence_factors='{"observations":[{"source":123,"score":0.8}]}'
        )
        persist_judge_confidence(target, 0.7)
        self.assertEqual(target.confidence, 0.7)
        self.assertEqual(target.confidence_sample_size, 1)

    def test_provenance_is_traceable_but_not_counted_as_an_observation(self) -> None:
        estimate = estimate_confidence(
            [
                ConfidenceSignal(1.0, "source-note:1"),
                ConfidenceSignal(1.0, "node-evidence:1"),
            ]
        )

        self.assertEqual(estimate.sample_size, 0)
        self.assertIsNone(estimate.score)
        self.assertEqual(
            estimate.factors,
            ("source-note:1", "node-evidence:1"),
        )

    def test_empirical_bernstein_radius_matches_the_documented_formula(self) -> None:
        estimate = estimate_confidence(
            [ConfidenceSignal(0.9, f"judge:{index}") for index in range(100)]
        )
        expected_radius = 3.0 * log(3.0 / 0.05) / 100

        self.assertEqual(estimate.sample_size, 100)
        self.assertAlmostEqual(estimate.lower or 0, 0.9 - expected_radius, places=6)
        self.assertEqual(estimate.upper, 1.0)

    def test_invalid_nominal_level_is_rejected_even_without_signals(self) -> None:
        with self.assertRaisesRegex(ValueError, "between 0 and 1"):
            estimate_confidence([], level=1.0)

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
