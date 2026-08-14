# Feedback-Driven Learning

## Scope

BerryBrain adapts future graph extraction, retrieval, insight generation, and Judge decisions from
auditable user feedback. This release does not train or fine-tune model weights. It implements
context-scoped policy adaptation: durable decisions become bounded evidence supplied to agents and
Judges on later work that overlaps the same source-note context.

This distinction is deliberate. Policy adaptation is reversible, attributable, backup-safe, and
available with local or cloud providers. Model-weight training would require a separate dataset,
consent, evaluation, rollback, and deployment process that does not exist in v1.4.8.

## Learning Loop

1. A user performs a knowledge-affecting action.
2. The API records an append-only `LearningEventRecord`; graph decisions also update the active
   `GraphFeedbackRecord` for the affected semantic identity.
3. The event stores actor, origin, action, target, timestamp, source-note IDs, context hash, signal,
   and bounded before/after state.
4. Before each AI job, the Worker requests the current learning policy for that job's note/path.
5. The API selects only global or overlapping-context signals, keeps the newest signal for each
   actor and target, and separates negative patterns, positive patterns, corrections, and
   annotations.
6. The policy is inserted as untrusted data. Agents must still validate source evidence,
   ontology constraints, and quality gates.
7. Generated artifacts pass deterministic checks and, where configured, the Judge. A positive
   user signal cannot bypass those checks.
8. Monitor exposes event counts, recent direction, active graph feedback, policy version, and the
   explicit fact that model weights were not updated.

## Action Coverage

| User action | Durable signal | Effect on future work |
| --- | --- | --- |
| Create or materially edit a note | Created/corrected note event | New note version is processed; prior note-owned provenance is detached when required |
| Rename or move a note | Corrected note event | Stable note identity is preserved; links and affected jobs are updated |
| Delete a note | Deleted note event | Note-owned evidence is removed; shared artifacts are recalculated from remaining sources |
| Confirm, ignore, restore, correct, or delete a graph node/edge | Active graph feedback plus learning event | Same or overlapping contexts prefer the decision and suppress rejected regeneration |
| Merge or split graph nodes | Corrected/restored graph feedback | Canonical identity and future reconciliation follow the latest scoped decision |
| Add a node/edge note or evidence | Annotation event | Agents receive it as user-authored, unverified context |
| Accept, reject, dismiss, or convert an insight | Insight event | Later insight proposals use the scoped positive or negative signal |
| Upvote, downvote, or correct an Ask answer/inference | Answer/inference event | Ask, retrieval, agents, and Judges receive the scoped correction or preference |

Interface navigation, scrolling, and incidental clicks are not semantic labels. They may contribute
to operational telemetry, but they do not modify the knowledge policy. Treating every click as
learning data would introduce noise, accidental bias, and privacy risk.

## Conflict And Scope Rules

- Source-note overlap scopes feedback to related work; unrelated notes do not inherit the signal.
- A global signal is used only when it was intentionally recorded without source-note scope.
- For the same actor, target type, and target key, the newest applicable event wins.
- Explicit correction has more information than a binary vote and is exposed separately.
- Deletion, rejection, ignore, dismissal, and downvote are negative signals.
- Acceptance, confirmation, correction, restoration, and upvote are positive signals.
- Annotation is context, not ground truth.
- The active graph feedback record prevents a deleted or rejected artifact from returning solely
  because an agent reran against the same evidence.

## Agent And Judge Roles

Agents propose extraction, enrichment, connections, clusters, insights, gaps, and grounded answers.
They do not directly admit knowledge. Deterministic validators enforce type, naming, provenance,
state, and ontology rules. The Judge evaluates grounding, relevance, contradiction, and risk with
the active provider configuration. Committee mode uses distinct compatible models when available;
failed members remain auditable and do not vote.

Feedback is one input to this process, not a substitute for evidence. A correction that conflicts
with source material can be retained as user context while the generated artifact remains
provisional or rejected.

## Observability And Recovery

The Monitor endpoint and interface expose:

- `mode=feedback-guided-adaptation` and `policy_version=feedback-policy.v1`;
- total and last-24-hour event counts;
- positive, negative, and neutral event counts;
- active graph feedback count and counts by target type;
- latest event timestamp;
- `model_weights_updated=false`.

Learning events and graph feedback are included in backup and restore. They are not provider prompt
instructions and are serialized as bounded untrusted data to reduce prompt-injection risk.

## Validation

Automated tests cover context overlap, unrelated-context exclusion, latest-decision precedence,
correction/annotation propagation, inference provenance, graph mutation feedback, note lifecycle,
backup portability, Monitor telemetry, and Worker prompt injection. Human longitudinal validation
is still required to claim that adaptation improves outcomes over time.
