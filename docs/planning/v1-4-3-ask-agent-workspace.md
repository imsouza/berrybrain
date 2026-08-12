# BerryBrain v1.4.3 Ask and Agent Workspace Plan

Status: implementation and local validation complete; publication paused.

## Architecture Decisions

- Ask has a dedicated workspace. Home and Graph route to it with optional query state.
- Flow is the optional persistent, evidence-grounded multi-turn memory layer.
- Graph gap research is an explicit external-evidence operation; results stay untrusted until confirmed.
- Suggestions render immediately from live graph artifacts. AI refreshes them asynchronously and
  only validated node IDs and labels enter the versioned cache. No graph evidence means no suggestions.
- Enrichment, gap discovery, Judge evaluation, clustering, and insights are internal agent work.
- Insights stay auditable records but appear primarily as graph nodes with accept/reject actions.
- Review Today and its active API, worker, UI, and test surfaces are removed.
- Confidence stays calculated from evidence signals and Wilson intervals; users cannot edit it.

## Implementation Checklist

- [x] Add graph-derived Ask suggestions API.
- [x] Keep the suggestion queue populated during provider failure with non-mocked graph semantics.
- [x] Run AI suggestion generation in background and refresh the client from the graph-version cache.
- [x] Add dedicated Ask workspace with voice, answers, Flow history, suggestions, and topic cloud.
- [x] Add Home and Graph Ask workspace entry points and return paths.
- [x] Add non-note node deletion and automatic graph recalculation.
- [x] Add graph insight accept/reject actions.
- [x] Add heartbeat-driven agent monitoring with idempotent scheduling.
- [x] Add evidence fingerprints, stale-job suppression, and provider-failure cooldown to enrichment.
- [x] Remove manual enrichment controls and disable switches.
- [x] Remove Review Today UI, routes, worker handler, jobs, and tests.
- [x] Remove the separate Insights page and Home insight cards.
- [x] Connect persistent English notifications to real insight and terminal-job events.
- [x] Update README, architecture docs, landing Docs, and changelog.
- [x] Add API tests for suggestions, agent monitoring, deletion, and confidence regression.
- [x] Pass web TypeScript validation, focused API tests, and the worker suite.
- [x] Pass the complete API and browser suites after final integration.
- [x] Rebuild and verify the local Docker stack.
- [ ] Commit, tag, or push. Publication remains paused by user request.

## Validation Evidence

- API: 373 tests and 55 subtests passed.
- Worker: 47 tests passed.
- Web: TypeScript passed, production images built, and 47 Playwright tests passed.
- Runtime: API, Worker, Web, and HippoRAG are healthy; enrichment cooldown prevented new jobs
  during an active provider rate limit.
