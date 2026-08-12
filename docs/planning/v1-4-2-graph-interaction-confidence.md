# BerryBrain v1.4.2 Graph Interaction and Confidence Plan

Status: implementation and validation complete; publication paused for requested corrections.

## Voice Input

- [x] Start browser speech recognition directly from the microphone gesture.
- [x] Request microphone media without blocking recognition startup.
- [x] Render a live five-bar waveform from Web Audio frequency data.
- [x] Surface permission, device, secure-context, network, and no-speech failures in English.
- [x] Cover Home Ask and Graph Ask with browser regression tests.

## Graph Interaction

- [x] Scale node geometry within bounded limits from the rendered label.
- [x] Wrap labels to at most three lines and 58 characters with readable ellipsis.
- [x] Keep ontology geometry and context-cluster color independent.
- [x] Distinguish a drag from a click with a movement threshold and click suppression.
- [x] Keep a dragged node pinned at its dropped position.
- [x] Anchor the hover summary close to the node and include type, context, confidence,
  provenance, path, semantic state, and directed relationships.
- [x] Animate the graph camera into a clicked node before full-page navigation.
- [x] Keep 10,000-node camera interaction below the 200 ms p95 budget with deterministic
  extreme-scale layout, canvas LOD, and bitmap gesture transforms.

## Node Navigation

- [x] Replace the cramped node drawer with the full node page.
- [x] Keep the vault sidebar and global navbar on the node page.
- [x] Route **Back to graph** to the complete graph and restore graph state.
- [x] Rename the shell command to **Back to Home** and route it to the Brain home.
- [x] Keep calculated confidence read-only while node edits trigger semantic validation
  and graph recalculation.

## Ontology and Retrieval Integrity

- [x] Enforce canonical English node classes and relationship properties.
- [x] Validate relationship domain, range, direction, symmetry, reason, and evidence.
- [x] Queue Judge evaluation for newly created AI edges.
- [x] Recalculate merged node and edge confidence from consolidated evidence.
- [x] Preserve ontology triples for graph-aware RAG and HippoRAG multihop retrieval.
- [x] Exclude quarantined semantic artifacts from graph retrieval.

## Confidence Integrity

- [x] Remove fixed production confidence percentages from Flow, graph context,
  inferred connections, and deterministic Worker fallbacks.
- [x] Persist 95 percent Wilson intervals for concepts, note connections, graph nodes,
  graph edges, insights, cluster assignments, and graph inferences.
- [x] Store score, lower/upper bounds, sample size, method, factors, and timestamp.
- [x] Backfill migrated knowledge records once and keep the audit idempotent.
- [x] Return `null` plus an `unavailable` interval when no evidence signal exists.
- [x] Keep OCR/transcription engine scores distinct from knowledge confidence.

## Language and Data

- [x] Keep repository-owned UI, messages, prompts, fixtures, metadata, and docs in English.
- [x] Preserve other languages only inside user-authored notes and quoted evidence.
- [x] Remove production self-check/demo knowledge payloads.
- [x] Keep the public demo workspace empty instead of seeding fabricated notes.

## Final Release Gates

- [x] API, Worker, HippoRAG, web, and Playwright suites pass.
- [x] Repository-wide English and fabricated-data audits pass.
- [x] Production images rebuild and all services report healthy.
- [x] Ontology, confidence backfill, and clustering audits are idempotent in runtime data.
- [x] Desktop/mobile screenshots confirm graph labels, hover, waveform, zoom, and routes.
- [ ] Release commit, tag, and `main` push complete.

## Release Evidence

- API: 373 tests and 55 subtests pass.
- Worker: 45 tests pass. HippoRAG: 8 tests pass.
- Browser: 48 Playwright tests pass without retries; five repeated 10,000-node stress runs
  hold interaction p95 between 33 ms and 40 ms.
- Runtime: schema v10, clustering algorithm v5, 73 active nodes, 160 active edges,
  confidence backfill pending count zero, and second audit updates zero records.
- Operations: backup `backup-20260811T094622Z` captured schema v9 before migration; API,
  Worker, Web, and HippoRAG images rebuilt and report healthy after migration.
