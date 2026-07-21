from __future__ import annotations

from dataclasses import dataclass
from typing import Any

GROUNDED_STATUSES = frozenset({"answered", "success", "sufficient_evidence"})
SAVABLE_STATUSES = GROUNDED_STATUSES | {"insufficient_evidence"}


@dataclass(frozen=True)
class InferenceSnapshot:
    id: int
    question: str
    answer: str
    status: str
    confidence: float
    routes: tuple[str, ...]
    evidence: tuple[Any, ...]
    related_nodes: tuple[Any, ...]
    provider: str
    model: str
    prompt_version: str


@dataclass(frozen=True)
class InsightDraft:
    type: str
    title: str
    description: str
    priority: int
    why_it_matters: str
    evidence: tuple[Any, ...]
    suggested_action: str
    graph_impact: str
    confidence: float
    grounded: bool


class InferenceNotSavableError(ValueError):
    pass


class MissingGroundedEvidenceError(ValueError):
    pass


def build_insight_draft(inference: InferenceSnapshot) -> InsightDraft:
    if inference.status not in SAVABLE_STATUSES:
        raise InferenceNotSavableError(inference.status)

    grounded = inference.status in GROUNDED_STATUSES
    if grounded:
        if not inference.evidence:
            raise MissingGroundedEvidenceError(inference.status)
        return InsightDraft(
            type="new_connection",
            title=f"Inference: {inference.question}"[:255],
            description=inference.answer,
            priority=6,
            why_it_matters=(
                "This conclusion connects knowledge already present in the vault and "
                "can guide navigation, consolidation, or further study."
            ),
            evidence=inference.evidence,
            suggested_action=(
                "Review the cited evidence, then confirm a graph connection or create "
                "a permanent note if the relationship is useful."
            ),
            graph_impact=(
                "Adds an insight node linked to the notes and graph evidence that "
                "support this inference."
            ),
            confidence=inference.confidence,
            grounded=True,
        )

    checked = ", ".join(inference.routes) or "the configured retrieval routes"
    evidence = inference.evidence or (
        f"BerryBrain checked {checked} and found no sufficient supporting evidence.",
    )
    return InsightDraft(
        type="knowledge_gap",
        title=f"Knowledge gap: {inference.question}"[:255],
        description=(
            "BerryBrain could not establish this relationship from the current vault. "
            "This is a missing-evidence signal, not a generated conclusion."
        ),
        priority=5,
        why_it_matters=(
            "The unanswered question identifies where the current knowledge base is "
            "too sparse or disconnected to support a reliable conclusion."
        ),
        evidence=evidence,
        suggested_action=(
            "Add or process source notes that address this question, then run the "
            "graph inference again."
        ),
        graph_impact=(
            "Adds a knowledge-gap node without inventing a relationship between "
            "existing nodes."
        ),
        confidence=0.0,
        grounded=False,
    )
