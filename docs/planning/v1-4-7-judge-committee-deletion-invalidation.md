# v1.4.7 Judge Committee and Deletion Invalidation

**Status:** Implemented and validated locally
**Scope:** provider-aware Judge defaults, editable committee roles, model independence, contextual deletion feedback, dependent insight invalidation, scoped clustering, and visible processing state.

## 1. Problem Statement

The automatic Judge defaulted to one model even when the active provider exposed several usable models. Committee support existed, but required manual configuration and did not assign distinct evaluation responsibilities. Separately, deleting a graph node removed its incident edges but left dependent insight records active and scheduled broad maintenance without describing progress to the user.

The observed `Skip` failure demonstrated both issues. Navigation boilerplate was extracted as a concept, connected unrelated source notes, and produced an insight. Deleting only the visible concept did not invalidate every semantic consequence.

## 2. Research Basis

The implementation follows these evidence-backed principles:

| Principle | BerryBrain application |
| --- | --- |
| RAG evaluation is multidimensional | Separate faithfulness, relevance, contradiction, source-quality, and ontology roles. |
| Structured criteria improve Judge consistency | Every role receives an explicit focus while still returning the complete artifact rubric. |
| A generator should not evaluate its own output | The generator model is excluded from eligible committee slots. |
| Diverse panels reduce single-model bias | Provider defaults select distinct available non-generator chat models. |
| LLM verdicts are not ground truth | Committee output remains secondary to human calibration and can resolve to review. |

Primary references:

- Es et al., *Ragas: Automated Evaluation of Retrieval Augmented Generation*, arXiv:2309.15217.
- Ru et al., *RAGChecker: A Fine-grained Framework for Diagnosing Retrieval-Augmented Generation*, arXiv:2408.08067.
- Liu et al., *G-Eval: NLG Evaluation using GPT-4 with Better Human Alignment*, arXiv:2303.16634.
- Kim et al., *Prometheus 2*, arXiv:2405.01535.
- Verga et al., *Replacing Judges with Juries*, arXiv:2404.18796.

## 3. Implemented Judge Contract

- Default committee size: `3`; editable range: `2` to `5`.
- Default roles: `faithfulness`, `relevance`, and `contradiction`.
- Optional roles for larger committees: `source_quality` and `ontology_consistency`.
- Provider assignment requires both a live catalog entry and a successful structured-response
  compatibility probe against the active endpoint.
- Embedding, reranking, moderation, guard, speech, and image models are excluded by capability-oriented name filtering.
- The configured generator model is excluded.
- Fewer than two eligible models keeps `single_model` mode instead of claiming committee consensus.
- A custom valid committee is preserved when the provider configuration remains compatible.
- Mode, count, model, role, and focus are editable in Settings.
- Automatic `JUDGE_ARTIFACT` jobs use the committee for nodes, edges, and insights when committee mode is active.

## 4. Implemented Deletion Contract

1. Capture incident edges, source notes, neighbors, and cluster scope before deletion.
2. Find incident insight nodes and same-context insights that explicitly mention the deleted label.
3. Expire dependent insight records and delete their graph projections in the same transaction.
4. Record contextual negative feedback so the same artifact is quarantined if regenerated in the same source context.
5. Remove semantic profiles and cluster assignments owned by deleted nodes.
6. Queue insight regeneration, clustering, graph statistics, and HippoRAG synchronization.
7. Recalculate only the incident cluster scope when a bounded scope exists.
8. Show a persistent graph status banner until all returned jobs complete or fail.
9. Reload graph data after completion so deleted artifacts cannot remain in the client projection.

This is policy learning from user decisions, not model-weight fine-tuning. Feedback changes future artifact admission for the same semantic identity and evidence scope.

## 5. Validation Matrix

| Check | Result |
| --- | --- |
| Provider defaults create three distinct roles | Passed |
| Generator model excluded | Passed |
| Invalid model categories excluded | Passed |
| Automatic background evaluation invokes configured committee | Passed |
| Deleted artifact regeneration is quarantined | Passed |
| Incident insight record expires | Passed |
| Insight graph projection is removed | Passed |
| Semantic profile and cluster assignment removed | Passed |
| Scoped reclustering preserves unrelated cluster | Passed |
| Stale graph connection excluded from hybrid search | Passed |
| Focused API regression suite | 40 passed |
| Full API suite | 436 passed in 226.307 seconds |
| Worker suite | 53 passed in 12.926 seconds |
| Web lint, TypeScript, and production build | Passed |
| Node deletion browser E2E | Passed in 33.3 seconds |
| Real deleted `Skip` node after fresh database session | Zero rows; feedback remains active |
| Real dependent insight | Insight 65 expired |
| Real bounded repair | Four jobs completed on first attempt |
| Real Judge committee evaluation | Three judges; evaluation 419 completed |
| Failed historical Judge jobs after valid defaults | Jobs 1303-1306 retried and completed |

## 6. Remaining Release Gates

- [x] Implement provider-aware committee defaults.
- [x] Make Judge mode, count, model, role, and focus editable.
- [x] Exclude the generator from committee eligibility.
- [x] Add contextual deletion suppression.
- [x] Invalidate dependent insights synchronously.
- [x] Add scoped cluster recomputation.
- [x] Add visible mutation progress in the graph.
- [x] Remove stale graph relationships from hybrid search.
- [x] Re-run the complete suite after the stale-search correction.
- [x] Rebuild the runtime containers and apply schema migration 11.
- [x] Validate the live `Skip` corpus and persisted Judge configuration.
- [ ] Publish v1.4.7 after all release checks pass.
