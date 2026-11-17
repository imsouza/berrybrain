# MuSiQue edit-stream minimum-support correction — protocol frozen 08/11/2026

Post-hoc implementation correction and exact rerun on the 99-note MuSiQue
workload, 20 source operations (10 deletions, 10 retractions), and 20 targeted
entity probes of `EDIT_STREAM_B4_PROTOCOL_2026-11-01.md`
(`musique_edit_stream_b4.py`, SHA-256
`2bc9cf8e7fae39e627271bffda461a6d37322479a2fcb944094a5beb83c2e4a7`).

## Motivation and post-hoc status

In the 01/11/2026 comparative run (`musique-edit-stream-b4-report.json`),
dependency-propagating rebuild reduced broken top-ten derivations from 37/146
(1.85 per probe) under direct-provenance detachment to 8/132 (0.40 per probe),
while strict direct-provenance purge achieved 0/103 broken derivations at the
cost of destroying 22.9% (511/2,229) of valid post-edit knowledge. Auditing the
8 residual entries identified a single implementation omission in
`berrybrain_api/graph_expansion.py`: `_prune_stale_graph_insights` received all
surviving concepts `set(concept_to_note_ids)`, including concepts whose active
supporting note count had fallen from `>= 2` to `1` after a deletion or
retraction, leaving six multi-note `InsightRecord` nodes (`"Connection pattern:
... links N notes"`) unpruned.

Because this fix was motivated by inspecting the 01/11/2026 edit-stream audit,
it is explicitly classified as a **post-hoc bug fix** in the manuscript's
status table (`Table 4`).

## Minimal code change

In `apps/api/src/berrybrain_api/graph_expansion.py` (patch saved at
`reproduction-src/insight_min_support_n4.patch`, unit regression tests at
`reproduction-src/test_insight_minimum_support.py`):

- Define `MIN_INSIGHT_SUPPORT_NOTES = 2` (matching `_upsert_graph_insights`,
  which only creates cross-note pattern insights when `len(note_ids) >= 2`).
- Filter the active concept set passed to `_prune_stale_graph_insights` to
  `{normalized for normalized, note_ids in concept_to_note_ids.items() if len(note_ids) >= MIN_INSIGHT_SUPPORT_NOTES}`.

No change is made to `musique_edit_stream_b4.py`, the 99-note vault (49
supporting passages from 20 hash-selected MuSiQue questions plus 50
distractors), the 20 operations, the 20 targeted probes, the clean post-edit
reference graph $G_{\text{clean}}(D')$, or the paired bootstrap parameters
(10,000 resamples, seed `20261101`).

## Verification criteria

1. Unit tests (`test_insight_minimum_support.py`, `test_maturation_regressions.py`,
   `test_graph_invalidation.py`) pass.
2. Frozen, direct-provenance detach, and strict direct-provenance purge
   baselines match `musique-edit-stream-b4-report.json` identically.
3. Report whether `dependencyInvalidation` and `dependencyPlusQualityGate`
   reach 0 broken top-10 derivations while retaining 100.0% of
   $G_{\text{clean}}(D')$ after one quality-gate pass.
