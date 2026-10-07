"""Query-aware evidence excerpts with deterministic, bounded output."""

from __future__ import annotations

import math
import re
from collections import Counter

TOKEN_PATTERN = re.compile(r"[^\W_]+", flags=re.UNICODE)
BOUNDARY_PATTERN = re.compile(r"(?:\n\s*\n|(?<=[.!?])\s+)")


def normalized_tokens(value: str) -> list[str]:
    return [match.group(0).casefold() for match in TOKEN_PATTERN.finditer(value)]


def query_aware_excerpt(text: str, question: str, max_characters: int) -> str:
    """Select coherent source spans without consulting answers or relevance labels."""
    if max_characters < 1:
        raise ValueError("max_characters must be positive")
    source = text.strip()
    if len(source) <= max_characters:
        return source
    query_terms = set(normalized_tokens(question))
    if not query_terms:
        return source[:max_characters].rstrip()

    units = _source_units(source)
    frequencies = Counter(
        token for _, _, unit in units for token in set(normalized_tokens(unit))
    )

    def score(index: int) -> tuple[float, int, int]:
        unit_tokens = set(normalized_tokens(units[index][2]))
        overlap = query_terms & unit_tokens
        lexical = sum(1.0 / math.log2(2 + frequencies[token]) for token in overlap)
        phrase = 1.0 if question.casefold() in units[index][2].casefold() else 0.0
        return (lexical + phrase, len(overlap), -index)

    ranked = sorted(range(len(units)), key=score, reverse=True)
    selected: set[int] = {0}
    used = len(units[0][2])
    for index in ranked:
        for candidate in (index, index + 1, index - 1):
            if candidate < 0 or candidate >= len(units) or candidate in selected:
                continue
            length = len(units[candidate][2]) + 2
            if used + length <= max_characters:
                selected.add(candidate)
                used += length
        if used >= max_characters:
            break

    ordered = [units[index][2].strip() for index in sorted(selected)]
    result = "\n\n".join(item for item in ordered if item)
    if len(result) < max_characters:
        start = units[max(selected)][1]
        remainder = source[start:].lstrip()
        if remainder:
            separator = "\n\n" if result else ""
            available = max_characters - len(result) - len(separator)
            if available > 0:
                result += separator + remainder[:available]
    return result[:max_characters].rstrip()


def _source_units(source: str) -> list[tuple[int, int, str]]:
    units: list[tuple[int, int, str]] = []
    start = 0
    for match in BOUNDARY_PATTERN.finditer(source):
        end = match.start()
        value = source[start:end].strip()
        if value:
            units.append((start, end, value))
        start = match.end()
    tail = source[start:].strip()
    if tail:
        units.append((start, len(source), tail))
    return units or [(0, len(source), source)]
