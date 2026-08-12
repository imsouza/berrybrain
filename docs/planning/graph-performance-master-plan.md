# BerryBrain Graph Performance Master Plan

## Status

This historical master plan is complete and has been consolidated into the active
[v1.4.1 release plan](planning-v1-4-1.md). The active plan is the source of truth for
implementation evidence, release checks, migration results, and final test counts.

## Product Invariants

- [x] Exactly one AI mode is active: cloud or local.
- [x] Required AI configuration is validated before AI-dependent work is queued.
- [x] Generated enrichment is evidence-backed and runs through bounded jobs.
- [x] Online validation is explicit, auditable, and protected against unsafe URLs.
- [x] Graph color represents semantic context.
- [x] Graph shape and border represent ontology type.
- [x] Vault roots use a separate visual namespace and BerryBrain red.
- [x] Confidence is calculated from evidence signals and is read-only in the UI.
- [x] Performance budgets are release gates, not advisory targets.
- [x] System UI, errors, labels, summaries, and generated answers are English-only.
- [x] User-authored source content and verbatim evidence excerpts remain unchanged.
- [x] Runtime code contains no seeded demo, mock, sample, or fabricated knowledge data.

## Completed Workstreams

### Queue Reliability

- [x] Durable job state machine with leases, attempts, cancellation, recovery, and logs.
- [x] Versioned payload validation for every supported job type.
- [x] Judge jobs use persisted evidence and model provenance.
- [x] Maintenance can inspect and repair stale legacy jobs without deleting history.
- [x] Home and Monitor derive counts from the same durable job records.

### Required Configuration

- [x] Cloud and local modes are mutually exclusive.
- [x] Model roles are validated before activation.
- [x] The required setup surface blocks AI work when configuration is incomplete.
- [x] Settings exposes explicit provider, model, consent, and health state.
- [x] Judge settings are scrollable and readable at constrained viewport heights.

### Semantic Enrichment

- [x] Nodes persist contextual meaning, note usage, learning value, evidence, and uncertainty.
- [x] Semantic profiles are versioned and become stale when their prompt contract changes.
- [x] Enrichment preserves quoted user evidence while generating all system prose in English.
- [x] Failed or stale enrichment is retryable and never replaced by fabricated fallback claims.

### Ask And Flow

- [x] Ask can query note content and the graph structure itself.
- [x] Graph questions resolve node labels, ontology types, edges, clusters, and evidence.
- [x] Flow turns persist context without hardcoded intent phrases.
- [x] A grounded Flow answer can be saved as an insight.
- [x] Voice input is available on the home Ask bar and graph Ask surface.

### Graph Performance

- [x] Full graph projection avoids ORM materialization for large payloads.
- [x] Compact graph serialization omits empty optional fields.
- [x] The 5,000-node and 20,000-edge benchmark remains within the release budget.
- [x] Graph rendering uses stable dimensions and bounded simulation behavior.
- [x] Labels do not duplicate, overlap by implementation error, or collapse into initials.
- [x] Canvas tests verify nonblank rendering and active pixel changes.

### Ontology And Edges

- [x] Node types map to canonical English ontology classes.
- [x] Edge types map to canonical English ontology properties.
- [x] Edge direction and endpoint type constraints are validated before persistence.
- [x] Unsupported names, metadata keys, sentences, and personal statements are quarantined.
- [x] RAG serializes typed relationships and cites graph evidence.
- [x] HippoRAG receives canonical triples and supports multihop retrieval.

### Semantic Colors

- [x] Context clustering combines semantic profiles, node text, and graph relationships.
- [x] Cluster count and maximum size are derived from the current graph population.
- [x] Oversized clusters are split deterministically.
- [x] Assignment confidence uses calculated evidence intervals.
- [x] Algorithm upgrades bypass old hysteresis while user-pinned assignments remain stable.
- [x] Reapplying an unchanged preview is idempotent.
- [x] Published cluster labels use the current English semantic profile contract.
- [x] Nodes without a current profile use an honest English type/group label until reprocessed.

### Node Experience

- [x] Hover displays a concise evidence-backed summary.
- [x] Click performs a zoom transition before opening a full node page.
- [x] Vault sidebar and top navigation remain mounted on node pages.
- [x] The full page exposes node data, ontology, confidence interval, evidence, and connections.
- [x] Editing is an explicit action and confidence is never user-editable.
- [x] Save validates semantic context and triggers graph recalculation.
- [x] The user can return to the previous graph view.

### Vault Experience

- [x] New Note always creates and opens the note editor.
- [x] Untitled notes use the English `Untitled note` convention.
- [x] Sidebar notes and folders support drag-and-drop reordering.
- [x] Sidebar rename, move, and delete actions operate on real vault data.
- [x] Demo routes do not seed fake notes, jobs, insights, metrics, or model status.

## Release Gates

- [x] API unit and integration suites pass.
- [x] Worker suites pass with API integration paths enabled.
- [x] HippoRAG direct sidecar tests pass.
- [x] Frontend typecheck, lint, and production build pass.
- [x] Ontology audit is idempotent on the production database.
- [x] Semantic clustering is idempotent on the production database.
- [ ] Final authenticated Playwright suite passes against the rebuilt Compose stack.
- [ ] Desktop and mobile screenshots confirm graph, node page, Settings, and voice controls.
- [ ] README, landing documentation, release metadata, commit, tag, and push are complete.

## References

- [Active v1.4.1 plan](planning-v1-4-1.md)
- [Design system](../DESIGN.md)
- [Design fix plan](design-fix-plan.md)
- [Architecture](../ARCHITECTURE.md)
- [Operations](../../OPERATIONS.md)
