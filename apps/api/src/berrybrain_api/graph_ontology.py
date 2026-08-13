from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable
from dataclasses import dataclass


@dataclass(frozen=True)
class NodeRule:
    ontology_class: str
    description: str


@dataclass(frozen=True)
class EdgeRule:
    ontology_property: str
    source_types: frozenset[str]
    target_types: frozenset[str]
    symmetric: bool = False


NODE_RULES = {
    "vault": NodeRule("schema:DataCatalog", "Visual root for a vault namespace."),
    "note": NodeRule("schema:CreativeWork", "Authored document stored in the vault."),
    "concept": NodeRule("skos:Concept", "Reusable abstract idea or technique."),
    "entity": NodeRule(
        "schema:Thing",
        "Identifiable person, organization, product, place, project, or standard.",
    ),
    "topic": NodeRule(
        "skos:ConceptScheme", "Broad subject grouping notes and concepts."
    ),
    "source": NodeRule("prov:Entity", "External provenance resource."),
    "attachment": NodeRule("schema:MediaObject", "File attached to a note."),
    "insight": NodeRule("prov:Entity", "Evidence-grounded derived claim."),
    "context": NodeRule(
        "bb:Context", "Situational, temporal, domain, or project scope."
    ),
    "gap": NodeRule(
        "bb:KnowledgeGap", "Explicit unanswered question or missing knowledge."
    ),
    "study_path": NodeRule("bb:StudyPath", "Ordered learning path."),
    "cluster": NodeRule(
        "skos:Collection", "Computed visual collection; not source knowledge."
    ),
}

_KNOWLEDGE = frozenset({"concept", "entity", "topic", "context"})
_EVIDENCE = frozenset({"note", "source", "attachment"})
_DERIVED = frozenset({"insight", "gap", "study_path"})

EDGE_RULES = {
    "mentions": EdgeRule("schema:mentions", frozenset({"note"}), _KNOWLEDGE),
    "about": EdgeRule("schema:about", frozenset({"note"}) | _DERIVED, _KNOWLEDGE),
    "references": EdgeRule("dcterms:references", frozenset({"note"}), _EVIDENCE),
    "derived_from": EdgeRule(
        "prov:wasDerivedFrom",
        _DERIVED | frozenset({"attachment"}),
        _EVIDENCE | _KNOWLEDGE,
    ),
    "supports": EdgeRule(
        "bb:supports",
        _EVIDENCE | frozenset({"insight"}),
        _DERIVED | _KNOWLEDGE | frozenset({"note"}),
    ),
    "contradicts": EdgeRule(
        "bb:contradicts",
        _EVIDENCE | frozenset({"insight"}),
        _DERIVED | _KNOWLEDGE | frozenset({"note"}),
    ),
    "broader": EdgeRule(
        "skos:broader", frozenset({"concept", "topic"}), frozenset({"concept", "topic"})
    ),
    "narrower": EdgeRule(
        "skos:narrower",
        frozenset({"concept", "topic"}),
        frozenset({"concept", "topic"}),
    ),
    "instance_of": EdgeRule("rdf:type", frozenset({"entity"}), frozenset({"concept"})),
    "part_of": EdgeRule("dcterms:isPartOf", _KNOWLEDGE, _KNOWLEDGE),
    "prerequisite_for": EdgeRule(
        "bb:prerequisiteFor",
        frozenset({"concept", "topic", "note"}),
        frozenset({"concept", "topic", "note"}),
    ),
    "example_of": EdgeRule(
        "bb:exampleOf",
        frozenset({"concept", "entity", "note"}),
        frozenset({"concept", "topic", "note"}),
    ),
    "applies_to": EdgeRule(
        "bb:appliesTo", frozenset({"concept", "insight"}), _KNOWLEDGE
    ),
    "same_as": EdgeRule(
        "owl:sameAs", frozenset({"entity"}), frozenset({"entity"}), True
    ),
    "contrasts_with": EdgeRule(
        "skos:related",
        frozenset({"concept", "insight", "note"}),
        frozenset({"concept", "insight", "note"}),
        True,
    ),
    "attached_to": EdgeRule(
        "schema:associatedMedia", frozenset({"attachment"}), frozenset({"note"})
    ),
    "contextualizes": EdgeRule(
        "bb:contextualizes",
        frozenset({"source", "context", "note"}),
        _KNOWLEDGE | _DERIVED | frozenset({"note"}),
    ),
    "related": EdgeRule(
        "skos:related",
        _KNOWLEDGE | frozenset({"note"}),
        _KNOWLEDGE | frozenset({"note"}),
        True,
    ),
}

GENERIC_LABELS = {
    "title",
    "url",
    "url source",
    "source",
    "markdown",
    "markdown content",
    "content",
    "heading",
    "headings",
    "metadata",
    "note",
    "notes",
    "unknown",
    "item",
}
SENTENCE_PREFIXES = {
    "i",
    "we",
}


def canonical_label(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", str(value or ""))
    normalized = re.sub(r"[\s_-]+", " ", normalized).strip()
    return normalized


def validate_node_name(node_type: str, label: str) -> list[str]:
    clean = canonical_label(label)
    normalized = clean.casefold()
    words = clean.split()
    issues: list[str] = []
    if node_type not in NODE_RULES:
        return [f"Unsupported node type: {node_type}"]
    minimum_length = 1 if node_type == "note" else 2
    if len(clean) < minimum_length or len(clean) > 120:
        issues.append(f"Name must contain between {minimum_length} and 120 characters.")
    if normalized in GENERIC_LABELS:
        issues.append("Name is a metadata key or generic placeholder, not knowledge.")
    if node_type in {"concept", "entity", "topic", "context"}:
        if re.search(r"[/\\]", clean) or normalized.endswith(".md"):
            issues.append("Name must not be a file path.")
        if len(words) > 7 or clean.endswith((".", "!", "?")):
            issues.append(
                "Semantic node names must be concise noun phrases, not sentences."
            )
        if words and words[0].casefold() in SENTENCE_PREFIXES and len(words) > 2:
            issues.append("Personal statements cannot be semantic node names.")
    if node_type == "entity" and clean.islower() and len(words) > 1:
        issues.append("Entity names must preserve an identifiable proper name.")
    return issues


def validate_edge_types(
    edge_type: str, source_type: str, target_type: str
) -> list[str]:
    rule = EDGE_RULES.get(edge_type)
    if rule is None:
        return [f"Unsupported edge type: {edge_type}"]
    issues: list[str] = []
    if source_type not in rule.source_types:
        issues.append(f"{edge_type} cannot start at {source_type}.")
    if target_type not in rule.target_types:
        issues.append(f"{edge_type} cannot target {target_type}.")
    return issues


def ontology_class(node_type: str) -> str:
    rule = NODE_RULES.get(node_type)
    return rule.ontology_class if rule else "bb:Unknown"


def ontology_property(edge_type: str) -> str:
    rule = EDGE_RULES.get(edge_type)
    return rule.ontology_property if rule else "bb:unknownRelation"


def first_issue(groups: Iterable[list[str]]) -> str:
    return next((issue for group in groups for issue in group), "")
