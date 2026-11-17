# MuSiQue edit-stream baseline & pending-recovery protocol — frozen 01/11/2026

Frozen before running `musique_edit_stream_b4.py`, as a post-hoc comparative
analysis on the exact 99-note MuSiQue workload and 20 probes of
`musique_edit_stream.py` (`EXPERIMENTS_2026-10-23_PROTOCOL.md`, E2).

## Motivation

Comparing dependency-based invalidation only against a frozen pre-edit graph
shows that invalidation removes stale items (123 -> 0), but does not isolate
what **dependency propagation and neighborhood reconstruction** add beyond a
nontrivial **direct-provenance-only** update, nor how many of the 27
unchanged-source items reset to `pending` recover after a post-rebuild
quality-gate pass.

## Ground-truth reference state

Build an independent clean graph $G_{\text{clean}}(D')$ from scratch on the
post-update vault $D'$ (79 unchanged notes with their reference OpenIE
concepts plus 10 retracted notes with empty concepts; 10 deleted notes
absent), admitted with the same quality-gate transition. Define each derived
artifact's provenance-independent semantic identity `semantic_key`:

- Derived node (`type != "note"`): `("node", type, canonical_label)`.
- Derived edge: `("edge", type, label, endpoint_a, endpoint_b)`, sorting
  endpoints for symmetric predicates (`SYMMETRIC_EDGE_TYPES`).

An accepted derived entry returned in retrieval or present in the graph after
the 20 source updates is **stale** if either:
1. **Direct stale provenance**: its `source_note_ids` still references one of
   the 20 deleted or retracted notes; or
2. **Derivational staleness**: its `semantic_key` does not exist in the
   post-update clean reference graph $G_{\text{clean}}(D')$ (for example, a
   cross-note insight `"Connection pattern: X links 2 notes"` or a
   `shared context` / `insight citation` edge whose derivation depended on an
   altered note even after direct provenance detachment).

## Compared update strategies on the identical 99-note vault and 20 probes

1. **Frozen graph** ($G_{\text{frozen}}$): no update after the 20 source
   operations.
2. **Direct-provenance-only detach** ($G_{\text{direct-detach}}$): execute
   the 10 note deletions and 10 note retractions through direct provenance
   detachment (`remove_note_record` and `sync_note_record` +
   `upsert_generated_metadata`, which invoke `_detach_note_graph_provenance`
   to strip altered `source_note_ids` and delete items whose direct source set
   becomes empty), **without** running dependency-propagating neighborhood
   invalidation and reconstruction (`expand_knowledge_graph`).
3. **Strict direct-provenance purge** ($G_{\text{direct-purge}}$): delete
   every derived node and edge whose pre-edit `source_note_ids` contained any
   altered note ($S \cap \text{changed} \neq \emptyset$, even when shared with
   unchanged notes), plus incident edges of deleted nodes, without
   neighborhood reconstruction.
4. **BerryBrain dependency invalidation** ($G_{\text{dep}}$): full source
   update plus `expand_knowledge_graph(session)` (matching the 25/10 report).
5. **BerryBrain + post-rebuild quality-gate pass** ($G_{\text{dep+gate}}$):
   run one post-rebuild quality-gate admission worker pass over `pending`
   derived nodes and edges backed by valid active canonical sources and
   ontology checks, recording wall-clock recovery time and how many of the 27
   `pending` unchanged-source signatures recover.

## Measures

- Stale derived entries in the 20 targeted top-10 probes (both direct-source
  and total stale vs. $G_{\text{clean}}(D')$, with 10,000-resample paired
  bootstrap 95% CIs for $G_{\text{direct-detach}}$ minus $G_{\text{dep}}$,
  seed 20261101).
- Graph-wide accepted stale derived artifacts (items in $G$ absent from
  $G_{\text{clean}}(D')$).
- Retention of valid post-update semantic signatures (items in
  $G_{\text{clean}}(D')$ retained as `passed` in $G$) and false suppressions.
- Post-rebuild quality-gate pass wall time and recovery fraction of the 27
  `pending` unchanged-source items.
