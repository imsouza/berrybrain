# BerryBrain Graph Actions Audit and Plan

## Scope

Audit and fix the actions shown in the Knowledge Graph node/connection detail panel.

UI language stays English. User notes stay in their original language.

## Audit

| Button | Status | Makes sense? | Duplicate? | Current action | Problem | Fix |
|---|---|---|---|---|---|---|
| suggested | PARCIAL | yes, as status | no | rendered as a status pill on connections and metadata on nodes | visually mixed with action buttons | keep as badge only, never button |
| confirm | PARCIAL | yes for connection | yes | calls `POST /api/v1/graph/connections/:id/confirm` | label too generic and duplicates node action pattern | rename to `Confirm Connection`; show only for suggested connections |
| ignore | PARCIAL | yes for connection | yes | calls `POST /api/v1/graph/connections/:id/ignore` | label too generic and duplicates node action pattern | rename to `Ignore Connection`; show only for suggested connections |
| Create insight | PARCIAL | yes for connection without saved insight | no | calls `POST /api/v1/graph/connections/:id/generate-insight` | appears even for `insight_suggested` edges and can be redundant | show `Save as insight` only when edge type is not `insight_suggested` |
| Confirm Node | PARCIAL | yes for suggested node | yes with connection confirm visual group | calls `POST /api/v1/graph/nodes/:id/confirm` | appears for any non-confirmed status, including ignored | show only when selected node status is `suggested` |
| Ignore Node | PARCIAL | yes for suggested node | yes with connection ignore visual group | calls `POST /api/v1/graph/nodes/:id/ignore` | appears for confirmed nodes, where `Archive` would be clearer | show only when selected node status is `suggested` |
| Reprocess graph | PARCIAL | yes, but too broad | no | calls `POST /api/v1/graph/expand` for whole graph | label implies full graph and no confirmation | replace panel action with `Reprocess node`; keep full graph outside/detail only with confirmation if needed |
| Enrich with AI | OK | yes | no | calls `POST /api/v1/graph/nodes/:id/enrich-ai` | has no disabled/loading guard | add action loading state and success/error feedback |
| Validate with web | PARCIAL | yes only when research enabled | no | calls `POST /api/v1/graph/nodes/:id/validate-web` | works without Research Mode gate, no external-source confirmation | add `research_mode_enabled`; hide/disable when off; backend blocks when off; require UI confirmation |
| Delete Node | PARCIAL | yes, dangerous | no | calls `DELETE /api/v1/graph/nodes/:id` | exposed as primary button and no confirmation | move to `Danger zone`; require confirmation; activity log |

## Required Changes

1. Add setting `research_mode_enabled`.
2. Gate `Validate with web` in frontend and backend.
3. Change insight node color in Brain View so AI insights are visually distinct.
4. Add centralized UI action model `getAvailableGraphActions`.
5. Remove duplicated generic confirm/ignore actions.
6. Add loading/success/error state per graph action.
7. Log graph actions in Activity via `AutomationLogRecord`.
8. Keep labels in English.

## Done Criteria

- `Suggested` is badge only.
- Node actions show only when relevant.
- Connection actions use `Confirm Connection` / `Ignore Connection`.
- `Save as insight` does not show for already saved insight edges.
- `Validate with web` requires Research Mode.
- `Delete Node` is in Danger zone and asks confirmation.
- Every action persists and refreshes graph/panel.
- Web typecheck passes.
- API imports pass.
