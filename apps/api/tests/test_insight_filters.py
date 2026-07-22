import unittest
from unittest.mock import MagicMock, patch

from berrybrain_api.routers.insights import (
    SyncInsightsRequest,
    _as_float,
    _as_int,
    _as_list,
    _has_knowledge_evidence,
    _is_system_diagnostic_item,
    _is_valid_generated_insight,
    sync_insights_from_ai,
)


class InsightFilterTest(unittest.TestCase):
    def test_payload_helpers_fail_closed_and_clamp_confidence(self) -> None:
        self.assertEqual(_as_list("not-a-list"), [])
        self.assertEqual(_as_list(["note.md"]), ["note.md"])
        self.assertEqual(_as_float("invalid", 0.6), 0.6)
        self.assertEqual(_as_float(2), 0.95)
        self.assertEqual(_as_float(-1), 0.0)
        self.assertEqual(_as_int("invalid", 4), 4)
        self.assertEqual(_as_int("7"), 7)

    def test_knowledge_evidence_accepts_structured_graph_sources(self) -> None:
        self.assertTrue(
            _has_knowledge_evidence(
                [{"source": "knowledge_graph", "nodeId": "concept:docker"}]
            )
        )
        self.assertTrue(_has_knowledge_evidence(["notes/docker.md: namespaces"]))
        self.assertFalse(
            _has_knowledge_evidence(
                [{"source": "semantic_data", "text": "pendingJobs: 8"}]
            )
        )

    def test_system_diagnostic_is_not_knowledge_insight(self) -> None:
        self.assertTrue(
            _is_system_diagnostic_item(
                "system_diagnostic",
                "Pipeline Bottleneck in Note Titling Prevents Graph Connectivity",
                "jobsByType.GENERATE_NOTE_TITLE backlog",
                "",
                "",
                "",
                ["semantic_data", "graphSummary"],
            )
        )

    def test_knowledge_insight_requires_note_or_graph_evidence(self) -> None:
        valid, reason = _is_valid_generated_insight(
            "Docker and shell form a local operations foundation",
            "Docker and Linux shell scripting appear together as a foundation for local automation and deployment workflows.",
            "This helps decide what to study next and how the notes reinforce each other.",
            "Create a bridge note about Docker plus shell automation.",
            "Connects two note nodes and clarifies their shared automation context.",
            [
                "inbox/docker.md: Docker containers isolate applications.",
                "connection Docker ↔ Linux Shell: shared automation context.",
            ],
            0.82,
        )

        self.assertTrue(valid, reason)

    def test_technical_terms_are_rejected_even_with_confidence(self) -> None:
        valid, reason = _is_valid_generated_insight(
            "Pipeline Bottleneck in Note Titling Prevents Graph Connectivity",
            "The GENERATE_NOTE_TITLE queue has a backlog and causes graph fragmentation.",
            "It matters because jobsByType shows pending jobs.",
            "Open Monitor and clear the queue.",
            "Updates graphSummary after the pipeline recovers.",
            ["semantic_data", "graphSummary"],
            0.92,
        )

        self.assertFalse(valid)
        self.assertEqual(reason, "technical_or_system_diagnostic")

    @patch("berrybrain_api.routers.insights.expand_knowledge_graph")
    @patch("berrybrain_api.routers.insights.create_insight")
    @patch("berrybrain_api.routers.insights.SessionLocal")
    def test_sync_creates_only_grounded_knowledge_and_expands_graph(
        self,
        session_local: MagicMock,
        create_insight: MagicMock,
        expand_graph: MagicMock,
    ) -> None:
        session = session_local.return_value.__enter__.return_value
        payload = SyncInsightsRequest(
            payload={
                "insights": [
                    {
                        "type": "knowledge_gap",
                        "title": (
                            "Connection between Docker and Linux shell automation boundaries"
                        ),
                        "description": (
                            "The Docker and shell notes both describe repeatable local "
                            "operations, but neither explains where container orchestration "
                            "should replace shell automation."
                        ),
                        "why_it_matters": (
                            "The missing boundary can lead to fragile operational choices."
                        ),
                        "suggested_action": (
                            "Write a comparison note with concrete decision criteria."
                        ),
                        "graph_impact": (
                            "Connects Docker, Linux shell, automation, and orchestration."
                        ),
                        "evidence": [
                            "notes/docker.md: containers package repeatable services.",
                            "notes/shell.md: scripts automate local operations.",
                        ],
                        "related_notes": [10, 11],
                        "confidence": 0.5,
                        "priority": 5,
                        "provider": "nvidia-nim",
                        "model": "qwen",
                        "promptVersion": "insight-generate.v3",
                    }
                ]
            }
        )

        result = sync_insights_from_ai(payload)

        self.assertEqual(result["insights_created"], 1)
        self.assertEqual(result["skipped"], [])
        create_insight.assert_called_once()
        args, kwargs = create_insight.call_args
        self.assertIs(args[0], session)
        self.assertEqual(args[1], "new_connection")
        self.assertAlmostEqual(kwargs["confidence"], 0.61)
        self.assertEqual(args[5], 5)
        self.assertEqual(kwargs["provider"], "nvidia-nim")
        expand_graph.assert_called_once_with(session)

    @patch("berrybrain_api.routers.insights.expand_knowledge_graph")
    @patch("berrybrain_api.routers.insights.create_insight")
    @patch("berrybrain_api.routers.insights.SessionLocal")
    def test_sync_rejects_diagnostics_malformed_and_unsupported_evidence(
        self,
        session_local: MagicMock,
        create_insight: MagicMock,
        expand_graph: MagicMock,
    ) -> None:
        session_local.return_value.__enter__.return_value = MagicMock()
        payload = SyncInsightsRequest(
            payload={
                "insights": [
                    "invalid",
                    {
                        "type": "pipeline_bottleneck",
                        "title": "Pipeline Bottleneck in Note Titling",
                        "description": "jobsByType.GENERATE_NOTE_TITLE has a backlog.",
                    },
                    {
                        "type": "hypothesis",
                        "title": "A technically plausible but unsupported relationship",
                        "description": (
                            "This statement is deliberately long enough to pass the basic "
                            "length requirement but has no note or graph evidence."
                        ),
                        "why_it_matters": "It could influence a future study decision.",
                        "suggested_action": "Collect evidence from two relevant notes.",
                        "graph_impact": "No graph change should occur without evidence.",
                        "evidence": ["semantic_data", "provider status"],
                        "confidence": 0.9,
                    },
                ]
            }
        )

        result = sync_insights_from_ai(payload)

        self.assertEqual(result["insights_created"], 0)
        self.assertEqual(
            [item["reason"] for item in result["skipped"]],
            ["system_diagnostic", "system_diagnostic"],
        )
        create_insight.assert_not_called()
        expand_graph.assert_not_called()

    @patch("berrybrain_api.routers.insights.expand_knowledge_graph")
    @patch("berrybrain_api.routers.insights.create_insight")
    @patch("berrybrain_api.routers.insights.SessionLocal")
    def test_sync_supports_single_insight_payload_and_normalizes_unknown_type(
        self,
        session_local: MagicMock,
        create_insight: MagicMock,
        expand_graph: MagicMock,
    ) -> None:
        session = session_local.return_value.__enter__.return_value
        result = sync_insights_from_ai(
            SyncInsightsRequest(
                payload={
                    "type": "invented_type",
                    "title": "Missing tradeoff between two container deployment models",
                    "description": (
                        "The current container notes describe two deployment models but do "
                        "not compare their operational costs or failure boundaries."
                    ),
                    "why_it_matters": "A comparison is needed before choosing a model.",
                    "suggested_action": "Create a decision note using both sources.",
                    "graph_impact": "Adds an evidence-backed gap between deployment nodes.",
                    "evidence": [
                        {"path": "notes/docker-compose.md", "text": "single host"},
                        {"path": "notes/kubernetes.md", "text": "cluster scheduling"},
                    ],
                    "confidence": "invalid",
                    "priority": "invalid",
                }
            )
        )

        self.assertEqual(result["insights_created"], 1)
        args, kwargs = create_insight.call_args
        self.assertEqual(args[1], "knowledge_gap")
        self.assertEqual(args[5], 5)
        self.assertEqual(kwargs["confidence"], 0.7)
        expand_graph.assert_called_once_with(session)


if __name__ == "__main__":
    unittest.main()
