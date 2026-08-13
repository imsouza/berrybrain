# v1.4.5 Graph Quality and Workspace Layout

Status: validated release candidate; publication authorized.

## Scope

- [x] Center Graph Ask independently from asymmetric left and right controls.
- [x] Normalize layout, filter, and knowledge control geometry.
- [x] Remove capitalization-only concept promotion.
- [x] Require structured AI evidence for concepts, topics, entities, and contexts.
- [x] Require cross-note corroboration for deterministic text concepts.
- [x] Preserve generated artifact provenance so the Judge evaluates AI nodes.
- [x] Quarantine Judge-rejected graph artifacts from graph reads.
- [x] Prune unsupported generated nodes during graph expansion.
- [x] Remove duplicate Home infographics and graph summaries.
- [x] Keep actionable Home operations in equal-size columns.
- [x] Render attention content only when an actionable condition exists.
- [x] Return to Graph immediately after node deletion.
- [x] Recalculate graph statistics, clusters, and retrieval after node deletion.
- [x] Replace raw evidence means with calibrated point estimates and confidence intervals.
- [x] Treat missing or stale Judge and enrichment artifacts as superseded work.
- [x] Preserve semantic node IDs across idempotent graph expansions.
- [x] Keep distinct semantic values from the same metadata record as distinct nodes.
- [x] Generate graph insights after every note-change pipeline and on the monitoring cadence.
- [x] Resolve AI-provided note paths and titles to durable note IDs before creating insights.
- [x] Publication explicitly authorized for v1.4.5.

## Semantic Admission Rules

| Candidate source | Admission requirement | Post-admission control |
| --- | --- | --- |
| AI concept metadata | Structured concept plus non-empty source evidence | Judge artifact evaluation |
| Deterministic note text | Candidate occurs in at least two independent notes | Corpus-derived confidence |
| AI topic metadata | Structured topic plus scope or description | Judge artifact evaluation |
| AI entity metadata | Structured entity plus description or evidence | Judge artifact evaluation |
| AI context metadata | Explicit context generation with a valid domain | Judge artifact evaluation |
| Classification tags, paths, languages, note types | Never promoted as semantic nodes | Retained only as metadata |
| Capitalized words | Never sufficient by themselves | No visible node |

## Measured Vault Result

Measurement date: 2026-08-13. Source: current local three-note vault after a complete graph expansion.

| Metric | Before quality gate | After quality gate |
| --- | ---: | ---: |
| Active concepts | 50+ mixed candidates | 23 evidence-backed concepts |
| Active topics | 9 | 3 |
| Active entities | 8 | 3 |
| Active contexts | 7 | 2 |
| Capitalization noise examples | `August`, `December`, `Once`, `Eagerly` | 0 active |
| Classification noise examples | `reference`, `und`, `physics-simulation` | 0 active |

The measured result is vault-specific evidence, not a universal precision estimate. Formal extraction precision and recall still require a labeled benchmark corpus.

## Confidence Calibration

The former implementation persisted the raw evidence mean. Fully positive evidence therefore rendered every node as `100%`, even when the sample was small. The current `jeffreys-wilson-evidence-v2` method reports:

- Point estimate: Jeffreys-smoothed evidence mean, `(sum(scores) + 0.5) / (n + 1)`.
- Interval: 95% Wilson score interval over the observed evidence mean.
- Sample size: the number of independently keyed evidence signals.
- Provenance: the signal keys and method are persisted with the artifact.

Real-vault measurement on 2026-08-13 after the migration and stable expansion:

| Node type | Nodes | Point estimate min | Mean | Max | Interval envelope | Evidence samples |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| Concept | 23 | 0.813 | 0.813 | 0.813 | 0.370-0.995 | 3 |
| Context | 2 | 0.833 | 0.833 | 0.833 | 0.342-1.000 | 2 |
| Entity | 36 | 0.833 | 0.835 | 0.900 | 0.342-1.000 | 2-4 |
| Insight | 8 | 0.698 | 0.848 | 0.900 | 0.264-1.000 | 3-4 |
| Note | 3 | 0.875 | 0.875 | 0.875 | 0.439-1.000 | 3 |
| Topic | 18 | 0.833 | 0.850 | 0.875 | 0.342-1.000 | 2-3 |

An interval upper bound may equal `1.000`; this is not displayed as a 100% point estimate. No measured active node had a 100% point estimate.

## Dead-Letter Recovery

Root causes found:

1. Graph expansion deleted and recreated suggested typed nodes, so queued enrichment jobs targeted missing IDs and received HTTP 404.
2. Multiple values in one metadata record shared one `source_id`; the upsert repeatedly overwrote one semantic node.
3. No-op upserts changed artifact versions, making queued Judge work stale.
4. Missing and stale artifacts were treated as retryable failures instead of obsolete work.

Corrections:

- Reconcile generated semantic nodes against current source metadata and delete only obsolete nodes.
- Match semantic nodes by canonical type and label; reserve source identity matching for note, attachment, and insight nodes.
- Preserve `updated_at` for no-op upserts and no-op enrichment.
- Include artifact versions in Judge requests.
- Complete worker jobs when a deleted graph node returns 404.
- Mark missing or version-stale Judge and enrichment jobs as `superseded`.

Measured target job state on 2026-08-13:

| Job type | Completed | Pending/running | Superseded historical work | Dead letter |
| --- | ---: | ---: | ---: | ---: |
| `ENRICH_GRAPH_NODE` | 12 | 4 | 242 | 0 |
| `JUDGE_ARTIFACT` | 134 | 6 | 451 | 0 |

Two consecutive real-vault expansions after the fix changed zero existing node versions.

## Automatic Insights

Insights are generated through two non-manual paths:

1. Every note create or edit queues `GENERATE_GRAPH_INSIGHTS` after extraction, graph expansion, inferred connections, and concept expansion.
2. Agent monitoring queues a periodic run. The configurable `insights_auto_interval_hours` value defaults to 24 hours and is bounded to 1-168 hours.

The Insights API also invokes the monitor check, but the feature does not depend on opening that page. Valid suggested insights are materialized as rectangular graph nodes and linked to resolved source notes. The real-vault verification job `790` completed in one attempt; the measured graph contained 8 suggested insight nodes after the worker processed the current backlog.

## Verification Gates

- [x] Focused semantic, graph lifecycle, stable-ID, deletion, and insight tests pass.
- [x] Web ESLint passes with zero warnings.
- [x] API and Web production images build.
- [x] Real vault expansion completes and removes known noise.
- [x] Full API regression suite passes: 413 tests.
- [x] Graph Playwright suite passes: 11 Chromium scenarios.
- [x] Node deletion returns to Graph and is covered by browser and API tests.
- [x] Target `ENRICH_GRAPH_NODE` and `JUDGE_ARTIFACT` dead-letter count is zero.
- [x] Real-vault confidence point estimates are calibrated below 100%.
- [x] Repeated real-vault graph expansion changes zero existing node versions.
