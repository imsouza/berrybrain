import unittest

from berrybrain_worker.content_fallbacks import (
    chunk_note_for_embedding,
    fallback_classification,
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


if __name__ == "__main__":
    unittest.main()
