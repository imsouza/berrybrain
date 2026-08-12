# BerryBrain v1.3.0 Maturity And Release Candidate Report

**Validation date:** August 9, 2026
**Historical status:** local release candidate approved.
**Base SHA:** `8a21e532bd6312f9b14bdcbf10a6d05e43c5327d`
**Validated SHA:** `e9109cc277d40fafbd6a624b2ed68d4a756c14cd`

This report is historical. The current release evidence is maintained in the
[v1.4.1 release plan](../planning/planning-v1-4-1.md).

## Root Causes And Fixes

| Problem | Root cause | Fix |
|---|---|---|
| New vault graph appeared incomplete | Scan and graph rebuild had different visibility timing | Pipeline diagnostics and end-to-end scan coverage |
| Renamed-note jobs could not resume | Payload relied on a stale path | Canonical ID/hash references and auditable repair |
| Ask returned HTTP 500 | Partial AI configuration and opaque errors | Required setup, capability validation, typed grounded answers, and Flow |
| Model list was empty | Provider URL and model slots lacked one normalized contract | Central model catalog and explicit slot selection |
| Settings failed on numeric identifiers | Form, API, and persistence converted identifiers differently | Typed atomic configuration v2 |
| HippoRAG lifecycle was incomplete | Index, delete, reconcile, and rebuild were not closed by vault | Authenticated lifecycle with tests |
| Graph degraded at scale | Monolithic payload and main-thread layout | Progressive endpoints, cursor pagination, summaries, worker layout, and budgets |
| Translation keys leaked into UI | Static keys were missing | Complete English catalog and visible-key regression tests |
| Healthy worker appeared offline | Monitor response omitted the consumed heartbeat field | Aligned API/frontend contract |
| HippoRAG image had vulnerable packages | Old build tooling bundled vulnerable dependencies | Updated build tooling and clean vulnerability scan |

## Queue Repair

- Before repair: 53 completed, 73 dead-letter, 16 superseded.
- After repair: 59 completed, 67 dead-letter, 16 superseded, zero active.
- Six renamed-note jobs were repaired and completed.
- Remaining historical jobs stayed quarantined with explicit reasons.

## Provider And Model Contract

- Cloud and local modes are mutually exclusive.
- Main, fast, embedding, judge, and HippoRAG roles use explicit model slots.
- Remote content requires consent.
- Judge and graph model invocations persist provider, model, prompt version, latency, and status.
- HippoRAG requests use service authentication.

## Product And UX

- Required AI setup blocks dependent work until configuration is valid.
- Settings exposes mode, endpoint, model roles, health, consent, and judge controls.
- Ask supports grounded answers and Flow persistence.
- Check Online runs through a global, auditable validation workflow.
- The graph uses semantic colors, typed shapes, focused hover, stable motion, and progressive loading.
- Node details expose source evidence, confidence, learning value, and model provenance.

## Performance Evidence

- Public and authenticated pages were tested with navigation and script budgets.
- Graph payload and layout were benchmarked at large synthetic sizes.
- Settings and graph interactions were checked for blocking work and responsive behavior.
- Cold and warm paths were measured separately.

## Semantic Graph Evidence

- Homonyms are separated by context rather than label alone.
- Cluster colors are stable and vault roots use a separate visual namespace.
- Node type is communicated by shape and border, not color alone.
- Graph generation and RAG preserve evidence and provenance.

## Backup And Data Safety

- Pre-migration backup and restore paths were verified.
- Release validation used disposable data where possible.
- Historical failed jobs were quarantined instead of silently deleted.

## Historical Quality Gates

- API, worker, sidecar, TypeScript, production build, Playwright, and performance gates passed.
- SBOM artifacts were generated for API, worker, web, and HippoRAG.
- Trivy reports recorded the release image state.
- Rollback used the database backup plus the previous image and Git tag.

## Remaining Historical Risks

- Performance depends on host storage, memory pressure, and model latency.
- Optional remote providers can change behavior outside BerryBrain's control.
- Large-vault limits require continued benchmark coverage.

## Supersession

v1.4.1 replaces this candidate's graph, ontology, confidence, node editing, English-only,
and runtime-data contracts. Do not use this report as current test evidence.
