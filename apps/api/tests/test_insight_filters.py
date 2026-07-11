import unittest

from berrybrain_api.routers.insights import (
    _is_system_diagnostic_item,
    _is_valid_generated_insight,
)


class InsightFilterTest(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
