from __future__ import annotations

import re

from fastapi import HTTPException

from berrybrain_api.graph_ontology import EDGE_RULES, NODE_RULES

CANONICAL_NODE_TYPES = set(NODE_RULES)

NODE_TYPE_ALIASES = {
    "web_source": "source",
}

CANONICAL_EDGE_TYPES = set(EDGE_RULES)

EDGE_TYPE_ALIASES = {
    "backlink": "references",
    "explicit_link": "references",
    "semantic": "related",
    "semantic_relation": "related",
    "semantic_similarity": "related",
    "shared_concept": "related",
    "shared_context": "related",
    "duplicate": "same_as",
    "duplicates": "same_as",
    "contrast": "contrasts_with",
    "example": "example_of",
    "application": "applies_to",
    "prerequisite": "prerequisite_for",
    "source_supports": "supports",
    "source_contradicts": "contradicts",
    "source_expands": "contextualizes",
    "insight_evidence": "derived_from",
    "insight_suggested": "derived_from",
    "attachment_related": "attached_to",
    "review_related": "derived_from",
    "topic_note": "mentions",
    "concept_note": "mentions",
}

SYMMETRIC_EDGE_TYPES = {
    edge_type for edge_type, rule in EDGE_RULES.items() if rule.symmetric
}

VALID_STATUSES = {
    "suggested",
    "confirmed",
    "accepted",
    "applied",
    "reviewed",
    "converted_to_note",
    "ignored",
    "archived",
    "stale",
    "error",
}
CONCEPTUAL_NODE_TYPES = {"concept", "entity", "topic", "context"}


def normalize_graph_label(value: str) -> str:
    normalized = re.sub(r"[-_]+", " ", value.strip().lower())
    return re.sub(r"\s+", " ", normalized)


def canonical_node_type(value: str) -> str:
    normalized = NODE_TYPE_ALIASES.get(value.strip().lower(), value.strip().lower())
    if normalized not in CANONICAL_NODE_TYPES:
        raise HTTPException(
            status_code=422, detail=f"Unsupported graph node type: {value}"
        )
    return normalized


def stored_node_types(canonical_types: set[str]) -> set[str]:
    return canonical_types | {
        alias
        for alias, canonical in NODE_TYPE_ALIASES.items()
        if canonical in canonical_types
    }


def canonical_edge_type(value: str) -> str:
    normalized = EDGE_TYPE_ALIASES.get(value.strip().lower(), value.strip().lower())
    if normalized not in CANONICAL_EDGE_TYPES:
        raise HTTPException(
            status_code=422, detail=f"Unsupported graph edge type: {value}"
        )
    return normalized
