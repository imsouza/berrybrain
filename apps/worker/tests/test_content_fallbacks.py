import unittest

from berrybrain_worker.content_fallbacks import (
    chunk_note_for_embedding,
    fallback_classification,
    fallback_concepts,
)


class ContentFallbacksTest(unittest.TestCase):
    def test_chunking_preserves_heading_and_line_evidence(self) -> None:
        content = "# Docker\nContainers and images.\n## Shell\nAutomation scripts."

        chunks = chunk_note_for_embedding(content, max_chars=32)

        self.assertGreaterEqual(len(chunks), 2)
        self.assertEqual(chunks[0]["start_line"], 1)
        self.assertEqual(chunks[0]["heading_path"], "Docker")
        self.assertEqual(chunks[-1]["heading_path"], "Docker / Shell")

    def test_classification_uses_real_note_terms(self) -> None:
        result = fallback_classification(
            {
                "title": "Docker Operations",
                "path": "notes/docker.md",
                "content": "# Container Runtime\nDocker and Linux automation.",
            }
        )

        self.assertIn("Container Runtime", result["concepts"])
        self.assertEqual(result["source"], "deterministic_fallback")

    def test_fallback_confidence_uses_source_occurrences_and_wilson_interval(
        self,
    ) -> None:
        result = fallback_concepts(
            {
                "title": "Telemetry",
                "path": "notes/telemetry.md",
                "content": "# Telemetry\nTelemetry links traces. Telemetry supports alerts.",
            }
        )
        concept = next(
            item for item in result["concepts"] if item["name"] == "Telemetry"
        )

        self.assertEqual(concept["confidenceInterval"]["sampleSize"], 4)
        self.assertEqual(
            concept["confidenceInterval"]["method"],
            "wilson-source-occurrence-v1",
        )
        self.assertEqual(concept["confidence"], concept["confidenceInterval"]["lower"])


if __name__ == "__main__":
    unittest.main()
