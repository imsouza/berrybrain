# Application Boundary Contract

BerryBrain application orchestration and use-case coordination.

## Boundary Rule

This layer coordinates domain invariants and storage/provider ports without coupling business workflows to browser presentation components, FastAPI transport wiring, or raw SQLite/Ollama driver details (checked by `scripts/lint/architecture-fitness.js`).

## Active Workflows in BerryBrain v1.5

- **Canonical Note & Vault Lifecycle**: Create, optimistic-concurrency update (`base_content_hash`), rename/move preserving `stableId`, vault-namespace assignment, and dependency-propagating provenance repair on edits or deletions.
- **Autopilot Pipeline & Bounded Recovery**: Asynchronous stage orchestration (`PARSE_NOTE` through `EXPAND_KNOWLEDGE_GRAPH`, `GENERATE_GRAPH_INSIGHTS`, and `VALIDATE_GRAPH_NODE_WITH_WEB`) with leases, idempotency keys, and bounded supervisor cooldowns.
- **Two-Tier Retrieval & Grounded Ask**: Hybrid FTS5 + dense RRF lookup, expanded-pool Cross-Encoder reranking + admitted graph traversal, persistent Flow turns, context-routed selection across the 1,576 Markdown Agent Skills, and supervised human-approved Ask Action Plans (`create_note`, `create_vault_and_note`, `enrich_note`).
- **Feedback Policy Resolution**: Scoped policy lookup before Worker extraction, Judge rubric v3 evaluation, and retrieval ranking.
