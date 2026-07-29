from __future__ import annotations

import re

from fastapi import HTTPException

CANONICAL_NODE_TYPES = {
    "note",
    "concept",
    "entity",
    "topic",
    "source",
    "attachment",
    "insight",
    "context",
    "gap",
    "review_question",
    "study_path",
    "cluster",
}

NODE_TYPE_ALIASES = {
    "nota": "note",
    "conceito": "concept",
    "entidade": "entity",
    "topico": "topic",
    "tópico": "topic",
    "fonte": "source",
    "web_source": "source",
    "anexo": "attachment",
    "contexto": "context",
    "lacuna": "gap",
}

CANONICAL_EDGE_TYPES = {
    "explicit_link",
    "semantic_relation",
    "prerequisite",
    "example_of",
    "contrasts_with",
    "duplicates",
    "applies_to",
    "derived_from",
    "mentions",
    "supports",
    "contradicts",
}

EDGE_TYPE_ALIASES = {
    "backlink": "explicit_link",
    "semantic": "semantic_relation",
    "semantic_similarity": "semantic_relation",
    "shared_concept": "semantic_relation",
    "shared_context": "semantic_relation",
    "related": "semantic_relation",
    "duplicate": "duplicates",
    "contrast": "contrasts_with",
    "example": "example_of",
    "application": "applies_to",
    "source_supports": "supports",
    "source_contradicts": "contradicts",
    "source_expands": "derived_from",
    "insight_evidence": "derived_from",
    "insight_suggested": "derived_from",
    "attachment_related": "derived_from",
    "review_related": "derived_from",
    "topic_note": "mentions",
    "concept_note": "mentions",
}

SYMMETRIC_EDGE_TYPES = {
    "semantic_relation",
    "contrasts_with",
    "duplicates",
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
