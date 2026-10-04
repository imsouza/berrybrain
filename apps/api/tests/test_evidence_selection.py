from __future__ import annotations

import pytest

from berrybrain_api.evidence_selection import query_aware_excerpt


def test_short_source_is_preserved() -> None:
    assert query_aware_excerpt("Short source.", "What source?", 100) == "Short source."


def test_relevant_late_span_is_selected_with_lead_context() -> None:
    source = (
        "Ada Lovelace was an English mathematician. "
        + "Background material. " * 30
        + "Her work concerned Charles Babbage's Analytical Engine."
    )
    excerpt = query_aware_excerpt(
        source, "Whose Analytical Engine concerned her work?", 180
    )
    assert excerpt.startswith("Ada Lovelace")
    assert "Analytical Engine" in excerpt
    assert len(excerpt) <= 180


def test_empty_question_falls_back_to_prefix() -> None:
    source = "alpha " * 100
    assert query_aware_excerpt(source, "", 20) == source.strip()[:20].rstrip()


def test_invalid_limit_fails_closed() -> None:
    with pytest.raises(ValueError, match="positive"):
        query_aware_excerpt("source", "question", 0)
