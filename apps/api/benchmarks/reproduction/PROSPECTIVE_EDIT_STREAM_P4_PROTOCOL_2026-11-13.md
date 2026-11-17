# Prospective MuSiQue edit-stream confirmation (P4) — preregistered protocol frozen 13/11/2026

Frozen and SHA-256 hashed **before** selecting, building, or inspecting the
second independent edit stream.

## Motivation and preregistered confirmatory status

In `EDIT_STREAM_N4_PROTOCOL_2026-11-08.md`, auditing the 8 residual broken
top-10 derivations from the 01/11/2026 comparative edit stream (`Stream 1`,
`musique_edit_stream_b4.py`) revealed that `_prune_stale_graph_insights` in
`berrybrain_api/graph_expansion.py` passed all surviving concepts
`set(concept_to_note_ids)` rather than filtering by
`MIN_INSIGHT_SUPPORT_NOTES = 2`. Applying `reproduction-src/insight_min_support_n4.patch`
eliminated all 8 residual broken top-10 derivations (`0/129`) and reached
`100.0%` retention (`2,229/2,229`) of $G_{\text{clean}}(D')$ after one
quality-gate pass, but that rerun was explicitly classified as **post-hoc**
because the bug was discovered on the same 99-note `Stream 1` workload.

To test prospectively whether the fixed lifecycle code generalizes without
modification to an unseen workload, this protocol defines a **second, strictly
disjoint MuSiQue edit stream (`Stream 2`)** under a salted SHA-256 seed
(`"p4-prospective-edit-stream-2026-11-13:"`).

## Fixed inputs and frozen implementation

- Questions (`2,417` total in `artifact/inputs/musique.json`, SHA-256
  `cb935bfdbef3de6dc5bfeb23f49bfaa03fb627da05c1ee02427959712881fb5b`).
- Corpus (`11,656` documents in `artifact/inputs/musique_corpus.json`, SHA-256
  `debe3ee5ebde2ba6af2fa6f24e2b98a82ba65c4ff6d76dbcd7ee557b398fd4db`).
- Published OpenIE entity extraction (`external-corpus/openie_results_ner_gpt-4o-mini.json`,
  SHA-256 `b57a1f5677b1ba96c3f63d2d3072318ffedefba5ab5f2dc3148422b0cf317707`),
  truncated to at most 6 distinct normalized entities per passage plus the
  passage title (`entities_for_doc`), identical to `Stream 1`.
- Fixed BerryBrain service implementation:
  `/mnt/HDD_1/Antigravity/berrybrain-insight-support/apps/api/src/berrybrain_api/graph_expansion.py`
  (SHA-256 `1c38afecca76af2079c653cb9e1bacb043f0a32baf0cb5d618463c75cce371ee`,
  incorporating `reproduction-src/insight_min_support_n4.patch` with zero
  further code changes).

## Disjoint workload construction (`Stream 2`)

Let `stream2_digest(x) = sha256(("p4-prospective-edit-stream-2026-11-13:" + x).encode("utf-8")).hexdigest()`.

1. **Stream 1 exclusion sets:** Compute `Stream 1`'s 20 question IDs
   (`S1_QUESTION_IDS`) and 99 selected passage keys (`S1_SELECTED_KEYS`, the 49
   supporting passages plus 50 distractors of `musique_edit_stream.py`).
2. **Disjoint question and supporting-passage selection:** Iterate over all
   questions in `musique.json` ordered deterministically by
   `(stream2_digest(q["id"]), q["id"])`. Skip any question whose `id` is in
   `S1_QUESTION_IDS` or whose supporting passages (`is_supporting == True`)
   intersect `S1_SELECTED_KEYS`. Select the first `N_QUESTIONS = 20` qualifying
   questions (`S2_QUESTION_IDS`), and let `S2_SUPPORT_KEYS` be the union of
   their supporting passage keys.
3. **Disjoint distractor selection:** From all corpus keys excluding
   `S1_SELECTED_KEYS | S2_SUPPORT_KEYS`, select the first `N_DISTRACTORS = 50`
   keys ordered by `stream2_digest(key)` (`S2_DISTRACTOR_KEYS`).
4. **Disjointness assertions (enforced before building the vault):**
   - `S1_QUESTION_IDS.isdisjoint(S2_QUESTION_IDS)`
   - `S1_SELECTED_KEYS.isdisjoint(S2_SUPPORT_KEYS | set(S2_DISTRACTOR_KEYS))`
   - `len(S2_QUESTION_IDS) == 20`, `len(S2_DISTRACTOR_KEYS) == 50`, and
     `len(S2_SUPPORT_KEYS) >= 20`.
5. **Operations and targeted probes:** Order `S2_SUPPORT_KEYS` by
   `stream2_digest(key)`. The first `N_DELETE = 10` passages are deleted via
   `remove_note_record`; the next `N_EDIT = 10` passages are replaced with the
   retraction text `"# Corrected source\n\nThe earlier passage has been retracted.\n"`
   and empty concept metadata via `sync_note_record` and
   `upsert_generated_metadata`. For each of the 20 changed notes, the targeted
   probe query is selected prior to observing any graph output as the first
   extracted concept with `>= 2` whitespace-delimited tokens (or `concepts[0]`
   if none exists).

## Evaluated views and preregistered confirmatory hypotheses

Evaluate the five views defined in `EDIT_STREAM_B4_PROTOCOL_2026-11-01.md`
against the ground-truth post-update graph $G_{\text{clean}}(D'')$ built from
scratch on the surviving `len(S2_SELECTED_KEYS) - 10` post-edit notes, using
10,000 paired bootstrap resamples (`SEED = 20261113`):

1. `frozen` (pre-edit graph $G(D_2)$ without invalidation)
2. `directProvenanceDetach` (detach changed `source_note_ids` without dependency propagation)
3. `directProvenancePurge` (delete every derived node/edge citing any changed source)
4. `dependencyInvalidation` (`expand_knowledge_graph` with `MIN_INSIGHT_SUPPORT_NOTES = 2`)
5. `dependencyPlusQualityGate` (`dependencyInvalidation` followed by one `admit_valid_derived_items` pass)

### Primary confirmatory criteria

- **H1-P4 (Zero broken derivations):** `dependencyInvalidation` and
  `dependencyPlusQualityGate` achieve `0` broken derivations in top-10 probe
  retrieval (`probeBrokenDerivationStaleCount == 0`) and `0` broken derivations
  across the entire accepted graph (`graphBrokenDerivationCount == 0`), and the
  paired bootstrap 95% CI for `directProvenanceDetach` minus
  `dependencyInvalidation` broken top-10 derivations per probe excludes zero
  above zero.
- **H2-P4 (Complete post-gate retention):** `dependencyPlusQualityGate` retains
  `100.0%` of $G_{\text{clean}}(D'')$ (`cleanReferenceNormRetentionRate == 1.0`,
  `cleanReferenceNormFalseSuppression == 0`), strictly exceeding
  `directProvenancePurge`.

If either H1-P4 or H2-P4 fails on `Stream 2`, report the exact residual broken
derivations or retention loss in `Table 4`, §5.2, and Limitations without
altering `graph_expansion.py`.
