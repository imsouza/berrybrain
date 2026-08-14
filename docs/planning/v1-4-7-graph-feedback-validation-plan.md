# BerryBrain v1.4.7 Graph Feedback and Validation Plan

**Date:** 2026-08-13
**Status:** Implemented and validated locally
**Scope:** graph readability, extraction quality, relationship relevance, persistent user feedback, automatic Judge routing, regression validation, and release documentation.

## 1. Verified Problems

### 1.1 Node label contrast

The canvas selects white text from the node type before considering the actual semantic-cluster fill. A light cluster color can therefore receive white text even when the palette supplies a dark accessible text color.

### 1.2 False concept and relationship

The observed `skip` connection is reproducible from real vault data:

| Note | Imported line | Extraction result |
|---|---|---|
| The Raven By Edgar Allan Poe | `Skip to main content` | single-word concept `skip` |
| Crimson Weather Mod For Crimson Desert | `Skip to content` | single-word concept `skip` |

The deterministic extractor accepted a capitalized single word from web-navigation boilerplate. Corpus corroboration then incorrectly strengthened the candidate because the same boilerplate appeared in two unrelated documents. The graph expansion joined both notes and generated a cross-note insight. The current Judge evaluated the persisted artifact but did not receive enough document-role context to identify the navigation fragment.

### 1.3 User actions do not currently produce adaptive memory

Graph edits, ignores, confirmations, and deletions are recorded in automation logs, but those logs are audit history only. Deletion removes the artifact and its edges, allowing a later expansion to recreate the same candidate. Ignoring hides an artifact but does not provide a reusable rejection rule. Editing changes the current artifact but does not map the previous identity to the correction for future runs.

### 1.4 Automatic Judge does not currently use the committee

The automatic `JUDGE_ARTIFACT` route uses one configured `judge_model`. Committee mode exists, supports multiple model slots, rejects generator self-review, and persists individual verdicts, but is only used by a separate endpoint. The background pipeline does not invoke it.

## 2. Target Behavior

1. Node text color is selected from the actual rendered fill and must maximize WCAG contrast. Palette text is retained only when it is at least as readable as the validated foreground candidates.
2. Imported navigation and other non-content boilerplate cannot become concepts, topics, entities, contexts, or relationship evidence.
3. Deterministic single-token concepts require stronger evidence than simple repetition across documents.
4. Generated links require content-bearing evidence and cannot be justified only by identical low-information fragments.
5. User confirmation, rejection, deletion, restoration, and correction create durable graph feedback records.
6. Negative feedback suppresses the same generated artifact in the same evidence context on future expansion runs.
7. A user correction maps the previous candidate identity to the corrected identity for matching future context.
8. Positive feedback remains auditable and can contribute an independent human evidence signal to recalculated confidence.
9. Automatic Judge jobs use committee mode when it is explicitly enabled, consented, valid for the artifact type, and contains at least two eligible models distinct from the generator.
10. Single-model mode remains supported and is reported explicitly; the system never claims committee consensus when only one model ran.

## 3. Architecture

### 3.1 Persistent feedback ledger

Add `graph_feedback` with:

- artifact kind and stable candidate key;
- context fingerprint and source-note scope;
- action (`confirmed`, `ignored`, `deleted`, `corrected`, or `restored`);
- original and replacement payloads;
- active state and timestamps.

The ledger is append-oriented for auditability. A policy resolver selects the latest active decision for an artifact key and matching context. Context-scoped feedback avoids globally banning a valid term because it was irrelevant in one document set.

### 3.2 Mutation integration

`GraphWriteService` remains the single mutation boundary:

- confirm: record positive feedback and recalculate confidence with an independent human signal;
- ignore: record negative feedback and hide/quarantine generated artifacts;
- delete: record negative feedback before physical removal;
- edit: record a correction from the previous semantic identity to the accepted identity;
- restore: deactivate the matching negative decision.

Generated node and edge upserts consult the feedback policy. A matching negative decision results in an ignored, quarantined artifact rather than a visible regenerated artifact. Corrected candidates resolve to the accepted replacement when the context matches.

### 3.3 Extraction gates

The extraction pipeline will:

- remove Markdown links, code, URLs, and detected navigation/boilerplate lines before candidate discovery;
- reject single-word title-case matches found only at line or sentence starts;
- require a single-token deterministic candidate to be supported by a heading/title or repeated content-bearing usage;
- preserve AI candidates only when their cited evidence appears in source content and passes the same content-role checks;
- quarantine rejected generated candidates with an explicit machine-readable reason.

### 3.4 Relationship gates

Cross-note `related` edges must be supported by a retained concept with valid source evidence in every linked note. Co-occurrence within one note remains a suggestion, not proof of synonymy or causality. Ontology domain/range validation remains mandatory. Suppressed endpoints or edge identities cannot produce visible edges or RAG traversal paths.

### 3.5 Judge routing

The automatic Judge route will select one execution mode per artifact:

- `single_model`: one configured Judge model;
- `committee`: all valid configured slots except the generator model, with at least two eligible models;
- `deterministic`: no LLM claim; deterministic quality gates only.

Committee results persist every model verdict plus the aggregate. Invalid committee configuration fails clearly and does not silently downgrade to one model.

## 4. Validation Method

### 4.1 Unit tests

- WCAG contrast selection for light, dark, malformed, and semantic palette colors.
- Boilerplate removal and single-token candidate rules.
- Feedback key stability and context matching.
- Confirm, ignore, delete, edit, restore, and regenerated-candidate behavior.
- Edge suppression and confidence recalculation.
- Judge single-model, deterministic, committee, generator-exclusion, and insufficient-committee paths.

### 4.2 Integration tests

- Two unrelated notes sharing `Skip to ...` produce no `skip` concept, cross-note edge, or insight.
- A deleted generated node remains absent after graph expansion.
- An edited generated node is not duplicated under its rejected former identity.
- Ignored relationships are excluded from graph reads and retrieval synchronization.
- Committee jobs persist multiple verdict rows and one aggregate evaluation.

### 4.3 UI tests

- Light nodes render dark readable labels; dark nodes render the highest-contrast label.
- Graph deletion returns to the graph and refreshed data does not recreate the node.
- Node status and feedback state remain consistent after reload.

### 4.4 Runtime audit

- Rebuild API, Worker, and Web images.
- Run API formatting/lint, focused tests, full API suite, web lint/type/build, Playwright graph tests, and Compose smoke checks.
- Run a real-data graph expansion and verify the observed `skip` false positive is removed or quarantined.
- Inspect dead-letter jobs and provider invocation provenance after the run.

## 5. Documentation and Release

- Update README architecture, graph quality, adaptive feedback, and Judge-mode descriptions.
- Update product docs and technical architecture with limitations: this is online policy adaptation, not model-weight training.
- Add schema and operational notes for feedback backup/restore.
- Add measured validation results after tests complete.
- Update versions and changelog to `1.4.7` only after acceptance criteria pass.
- Publish through a release branch and PR; merge only after all required checks pass; tag and publish `v1.4.7` from the merged `main` commit.

## 6. Acceptance Criteria

- [x] Every visible node label meets the best available WCAG contrast against its actual fill.
- [x] The reproduced `skip` fixture creates no concept, relationship, or insight.
- [x] Negative feedback survives deletion and blocks same-context regeneration.
- [x] Corrections are retained and prevent the former candidate from being duplicated.
- [x] Confirmations provide a traceable human confidence signal.
- [x] Automatic Judge routing reflects configured single-model, deterministic, or committee behavior.
- [x] Committee mode uses at least two eligible non-generator models and persists per-model provenance.
- [x] Feedback is included in portable metadata exports and schema migration coverage.
- [x] Graph/RAG reads exclude ignored or quarantined artifacts.
- [x] Focused and full validation suites pass.
- [x] README, Docs, changelog, and versions match verified behavior.
- [ ] PR checks pass before `v1.4.7` is merged and released.
Runtime follow-up completed on 2026-08-13:

- [x] Preserve valid cluster colors while semantic enrichment is pending or stale.
- [x] Distinguish a missing cluster scope from an explicit empty scope in the worker.
- [x] Expand scoped recalculation to every active member of an affected cluster.
- [x] Reuse cluster identity and color by prior membership overlap.
- [x] Apply validated edge confidence as a real similarity signal.
- [x] Split assignments below the semantic cohesion floor.
- [x] Count current node memberships instead of historical assignment rows.
- [x] Suppress deleted concepts before deterministic relation generation.
- [x] Quarantine indirect note relationships that cite a deleted concept.
- [x] Replace, rather than accumulate, evidence for recalculated shared-concept edges.

Real runtime audit after repair: 88 active nodes, 0 pending colors, 0 references to inactive
clusters, 18 active non-empty clusters, 18 distinct active colors, and 0 active relationships based
on the deleted `skip` concept.
