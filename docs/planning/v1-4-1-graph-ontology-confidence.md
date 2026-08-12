# BerryBrain v1.4.1 Graph, Ontology, and Confidence Plan

Status: complete; release evidence consolidated in the v1.4.2 plan.

## Canonical Ontology

- [x] Define canonical English node types and aliases at ingestion boundaries.
- [x] Define canonical directed relationship types with domain and range rules.
- [x] Map concepts, entities, topics, notes, sources, evidence, gaps, flows, and insights to distinct roles.
- [x] Validate node names for semantic specificity, type compatibility, and source context.
- [x] Quarantine invalid nodes and edges instead of publishing them.
- [x] Audit and normalize existing graph records idempotently.

## Relationship Semantics

- [x] Use explicit ontology and UML-style relationship names.
- [x] Reject meaningless, unsupported, duplicate, and invalid-direction edges.
- [x] Preserve provenance and evidence on accepted edges.
- [x] Include relationship semantics in search, Ask, and graph-aware RAG.
- [x] Synchronize the canonical graph contract with HippoRAG.

## Confidence

- [x] Remove user-editable confidence controls.
- [x] Calculate node, edge, insight, and answer confidence from evidence signals.
- [x] Use Wilson score intervals with a 95 percent confidence level.
- [x] Store method, sample size, lower bound, upper bound, and provenance.
- [x] Recalculate affected graph confidence after accepted edits.
- [x] Avoid fixed confidence values in production execution paths.

## Contextual Clustering

- [x] Cluster by semantic vectors and graph structure, not node type alone.
- [x] Keep ontology type independent from cluster assignment.
- [x] Assign stable cluster colors and reserve red for vault note roots.
- [x] Publish only English semantic labels from the current enrichment contract.
- [x] Use factual canonical-type fallbacks when current semantic labels are unavailable.
- [x] Keep clustering deterministic and idempotent.

## Graph Rendering and Navigation

- [x] Prevent duplicate canvas and DOM labels.
- [x] Preserve readable full labels and stable layout dimensions.
- [x] Render distinct type shapes, contextual colors, directed edges, and an accurate legend.
- [x] Animate node zoom before navigating to the full node page.
- [x] Preserve global navigation and vault sidebar on node pages.
- [x] Show evidence, provenance, semantic validation, relationships, and read-only confidence.

## Retrieval and Insights

- [x] Support flow-sourced insights.
- [x] Run eligible automatic insight generation every 24 hours.
- [x] Remove structural-key repetition from evidence output.
- [x] Answer graph-structure questions using inferred intent and live graph data.
- [x] Add voice input to every Ask entry point.

## Language and Data Integrity

- [x] Use English for all repository-owned UI, API messages, prompts, metadata, docs, and generated output.
- [x] Preserve original language only for user-authored vault content and quoted evidence.
- [x] Remove Portuguese aliases and legacy compatibility strings from source.
- [x] Remove hardcoded demo, seed, and mock records from production paths.
- [x] Default unknown source language to `und` rather than assuming a locale.

## Final Release Gates

- [x] Repository-wide English lexical audit passes.
- [x] API, worker, HippoRAG, web, and browser test suites pass.
- [x] Production images rebuild and all health checks pass.
- [x] Runtime ontology and clustering audits pass twice without further changes.
- [ ] Release commit, tag, and push are complete.
