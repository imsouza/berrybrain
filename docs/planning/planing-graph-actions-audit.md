# BerryBrain Graph Actions Audit

Date: 2026-07-10

UI language rule: BerryBrain UI stays in English. User note content keeps its original language.

## Audit Table

| Button | Status | Makes sense? | Duplicated? | Current action | Problem | Correction |
|---|---|---|---|---|---|---|
| suggested | OK | yes | no | Rendered as a status badge in the node/connection detail panel. | None. It is not an action button. | Keep as badge only. |
| confirm | OK | yes, only for connections | no | `Confirm Connection` calls `POST /api/v1/graph/connections/:id/confirm`. | Old lowercase `confirm` was confusing. | Use only `Confirm Connection` for connection rows. |
| ignore | OK | yes, only for connections | no | `Ignore Connection` calls `POST /api/v1/graph/connections/:id/ignore`. | Old lowercase `ignore` was confusing. | Use only `Ignore Connection` for connection rows. |
| Create insight | OK | yes, only when item is not already an insight | no | Replaced by `Save as insight`; calls `POST /api/v1/graph/connections/:id/generate-insight`. | `Create insight` was ambiguous when the panel already showed an insight-like connection. | Keep `Save as insight`; hide for `insight_suggested` edges. |
| Confirm Node | OK | yes | no | Calls `POST /api/v1/graph/nodes/:id/confirm`; for insight nodes it becomes `Apply Insight`. | Must only appear for suggested nodes. | Already visible only when `status === "suggested"`. |
| Ignore Node | OK | yes | no | Calls `POST /api/v1/graph/nodes/:id/ignore`; for insight nodes it becomes `Ignore Insight`. | Must only appear for suggested nodes. | Already visible only when `status === "suggested"`. |
| Reprocess graph | OK | yes, but only as scoped action | no | Replaced by `Reprocess node`; calls `POST /api/v1/graph/nodes/:id/reprocess`. | Full graph reprocess is too broad for a detail panel. | Keep scoped label `Reprocess node`; full graph remains outside this panel. |
| Enrich with AI | OK | yes | no | Calls `POST /api/v1/graph/nodes/:id/enrich-ai`; saves summary/context/evidence/provider/model/prompt version. | Needs clear feedback. | Current UI shows loading and success/error message, then reloads graph. |
| Validate with web | OK | yes, only with Research Mode | no | Calls `POST /api/v1/graph/nodes/:id/validate-web`. Backend rejects when `research_mode_enabled !== "true"`. | Must not query external sources silently. | Hidden unless Research Mode is enabled; asks confirmation before running. |
| Delete Node | OK | no, not in graph detail panel | no | Backend endpoint exists, but UI action removed from Brain View. | Destructive action should not be exposed beside normal cognition actions. | Removed from graph panel. Destructive cleanup belongs in Settings/Danger Zone or a future explicit management view. |

## Current Behavior

- Node status is visual state, not an action.
- Suggested node: shows `Confirm Node`, `Ignore Node`, `Reprocess node`, `Enrich with AI`, and optionally `Validate with web`.
- Confirmed node: hides confirm/ignore; keeps `Open note`, `Reprocess node`, `Enrich with AI`, and optionally `Validate with web`.
- Insight node: uses `Apply Insight` and `Ignore Insight` instead of generic node labels.
- Suggested connection: shows `Confirm Connection`, `Ignore Connection`, and `Save as insight` when the connection is not already an insight.
- Ignored connection is removed from the visible connection list after action.
- Delete is not shown in the graph detail panel.

## Persistence And Feedback

- `Confirm Node`: persists status through graph API, registers `GRAPH_NODE_CONFIRMED`, updates panel and graph.
- `Ignore Node`: persists status through graph API, registers `GRAPH_NODE_IGNORED`, closes the panel and reloads graph.
- `Apply Insight`: applies the source insight, confirms the graph node, updates panel and graph.
- `Ignore Insight`: ignores the source insight, ignores the graph node, closes panel and reloads graph.
- `Confirm Connection`: persists status through graph API, registers `GRAPH_CONNECTION_CONFIRMED`, updates panel and graph.
- `Ignore Connection`: persists status through graph API, registers `GRAPH_CONNECTION_IGNORED`, removes row and reloads graph.
- `Save as insight`: creates or reuses a real insight, registers `GRAPH_CONNECTION_INSIGHT_CREATED`, then reloads graph.
- `Reprocess node`: creates an `ENRICH_GRAPH_NODE` job and registers `GRAPH_NODE_REPROCESS_QUEUED`.
- `Enrich with AI`: writes AI summary/context/source evidence to the node and registers `GRAPH_NODE_ENRICHED`.
- `Validate with web`: requires Research Mode, records validation evidence and registers `GRAPH_NODE_WEB_VALIDATED`.

## Done

- Removed duplicate lowercase `confirm` / `ignore` actions from the node action area.
- Kept connection actions scoped as `Confirm Connection` / `Ignore Connection`.
- Removed `Delete Node` from the Brain View action model.
- Kept `Validate with web` hidden unless Research Mode is enabled.
- Kept UI labels in English.
- Kept user note content untouched.

## Remaining Optional Improvements

- Add a `More` menu later for non-destructive secondary graph actions.
- Add a dedicated graph management screen for archive/delete operations.
- Add Playwright coverage for action visibility by item type/status.
