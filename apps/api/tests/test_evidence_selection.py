from __future__ import annotations

import unittest

from berrybrain_api.evidence_selection import query_aware_excerpt


class EvidenceSelectionTests(unittest.TestCase):
    def test_short_source_is_preserved(self) -> None:
        self.assertEqual(
            query_aware_excerpt("Short source.", "What source?", 100), "Short source."
        )

    def test_relevant_late_span_is_selected_with_lead_context(self) -> None:
        source = (
            "Ada Lovelace was an English mathematician. "
            + "Background material. " * 30
            + "Her work concerned Charles Babbage's Analytical Engine."
        )
        excerpt = query_aware_excerpt(
            source, "Whose Analytical Engine concerned her work?", 180
        )
        self.assertTrue(excerpt.startswith("Ada Lovelace"))
        self.assertIn("Analytical Engine", excerpt)
        self.assertLessEqual(len(excerpt), 180)

    def test_empty_question_falls_back_to_prefix(self) -> None:
        source = "alpha " * 100
        self.assertEqual(
            query_aware_excerpt(source, "", 20), source.strip()[:20].rstrip()
        )

    def test_invalid_limit_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "positive"):
            query_aware_excerpt("source", "question", 0)


if __name__ == "__main__":
    unittest.main()
