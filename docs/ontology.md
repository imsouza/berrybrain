# Graph Ontology And Visual Semantics

## Classification

BerryBrain v1.4.8 implements an ontology application profile, not a universal domain ontology. It
defines stable classes, predicates, identity rules, validation shapes, lifecycle state, provenance,
and serializations needed by the product's graph and RAG pipeline. The profile is published as
Turtle and JSON-LD and validated with SHACL constraints.

## Why The Ontology Exists

The ontology prevents graph elements from being decorative strings. It gives extraction, storage,
visualization, retrieval, and the Judge the same contract for:

- what a node represents;
- which relationships are legal and directed;
- how aliases map to canonical classes and predicates;
- which evidence and note version support an assertion;
- whether an artifact is provisional, accepted, ignored, quarantined, archived, or deleted;
- how confidence support is represented without calling it a calibrated probability;
- how graph paths can be used by grounded multi-hop retrieval.

## Node Classes

| Class | Meaning | Visual shape |
| --- | --- | --- |
| `Note` | Canonical vault document and provenance root | Circle |
| `Concept` | Abstract idea expressed by one or more sources | Diamond |
| `Entity` | Identifiable person, organization, place, product, event, or work | Hexagon |
| `Topic` | Broader thematic grouping used for navigation and retrieval | Triangle |
| `Insight` | Evidence-backed proposed synthesis requiring acceptance state | Rectangle |
| `ResearchGap` | Explicit unresolved question or missing evidence | Octagon |

A candidate name must be normalized, grammatical, informative, and supported by source evidence.
Navigation fragments, stop phrases, isolated verbs, low-information tokens, diagnostics, and
unsupported abbreviations are rejected or quarantined. Entity candidates also require entity-like
semantics; concepts require reusable abstract meaning; topics require broader grouping scope.

## Predicates

Canonical edge types follow ontology/UML-style verb phrases and define source class, target class,
direction, inverse where applicable, symmetry, and admissible evidence. Examples include
`mentions`, `defines`, `hasTopic`, `supports`, `contradicts`, `derivedFrom`, `relatedTo`, and
`identifies`. Alias labels are normalized before persistence.

An edge is active only when both endpoints are active, evidence is current, the quality gate allows
it, and no applicable user feedback suppresses it. Removing a node invalidates incident edges and
dependent insights, then schedules scoped cluster, retrieval, statistics, and insight maintenance.

## Visual Contract

- Shape encodes class and never cluster.
- Fill color encodes semantic context cluster and never confidence.
- Every node in one current cluster shares a deterministic, contrast-safe cluster color.
- A vault-note parent uses BerryBrain primary red `#CC4168` regardless of cluster.
- Insights use a dedicated highlight treatment while retaining rectangular shape.
- Text color is calculated from fill luminance to keep WCAG-readable contrast.
- Edge line style and arrow direction encode predicate role and state.
- Confidence is displayed numerically as a calculated support interval, not as color.

These channels are independent. Two concepts in different contexts keep the same diamond shape but
different colors. A note and concept in the same context keep different shapes but may share a
cluster color, except for the mandatory note-parent red override.

## Identity, Provenance, And State

Each canonical artifact has stable identity, source-note IDs, source attachment IDs where relevant,
source evidence, current source version, quality-gate status, lifecycle status, and confidence
signals. Writes are idempotent. Reprocessing reconciles the same semantic identity instead of
creating duplicates. Superseded or deleted evidence cannot remain retrievable through an active
edge.

## RAG Use

Graph retrieval uses canonical type and predicate, direction, aliases, source provenance, current
state, feedback suppression, and the lower confidence bound. It combines lexical and dense seeds,
expands only valid paths, reranks evidence, and supplies citations to Ask. The internal 44-query
regression fixture shows graph-hybrid retrieval recovering all designed multi-hop paths while the
standard hybrid configuration recovers none; this is a controlled regression result, not proof of
superiority on external corpora.

## Machine-Readable Contract

The ontology service exposes the application profile as JSON-LD and Turtle. Source definitions live
under `apps/api/src/berrybrain_api/ontology/`; SHACL shapes validate class and predicate constraints.
API contract tests verify serialization, stable IRIs, aliases, domain/range rules, and invalid graph
rejection.
