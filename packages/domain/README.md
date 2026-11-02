# Domain Boundary Contract

Pure BerryBrain domain invariants and business rules.

## Boundary Rule

This layer defines framework-independent entities, value objects, and semantic invariants. It must never depend on HTTP routers, React components, SQLite sessions, filesystem drivers, Ollama/OpenAI transport clients, or outer delivery layers (enforced automatically by `scripts/lint/architecture-fitness.js`).

## Core Domain Concepts (Active in Runtime Services)

- **Canonical Sources**: `Note`, `Vault` (named physical organizational namespaces inside the shared workspace), and `NoteAttachment`.
- **Governed Graph Artifacts**: `GraphNode`, `GraphEdge`, `Concept`, `Connection`, and `Insight`—validated against SKOS, PROV-O, OWL, and SHACL domain/range rules (`graph_contracts.py` and `ontology/*.ttl`).
- **Evidence Support & Quarantine**: Read-only `evidence-support-mean-v2` observations and descriptive bounded-signal intervals on derived artifacts (`null` on canonical notes/vaults), plus semantic quarantine for unverified or rejected candidates.
- **Reversible Human Feedback**: Source-scoped, append-oriented policy signals (`graph_feedback`, `learning_events`) with `model_weights_updated=false`.
- **Supervised Execution**: `Job`, `AskActionPlan`, and `AutomationLog`.

In the polyglot runtime (`Python FastAPI/Worker` + `TypeScript Next.js`), active Python domain contracts live in `apps/api/src/berrybrain_api/` (`graph_contracts.py`, `confidence.py`, `artifact_state.py`), while this directory anchors the monorepo architectural fitness boundary.
