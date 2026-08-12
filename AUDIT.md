# BerryBrain Maturity Audit

**Date:** July 14, 2026
**Scope:** local-first product, API, worker, web, cognitive layer, security, data,
installation, and release.
**Historical result:** 307/307 v1.0 planning criteria completed.
**Current source of truth:** [v1.4.2 release plan](docs/planning/v1-4-2-graph-interaction-confidence.md).

## Executive Conclusion

BerryBrain implements the core of an evidence-backed second brain:

- Markdown notes remain the primary source.
- The worker runs a durable cognitive pipeline.
- Chunks and embeddings support semantic retrieval.
- Nodes and edges represent notes, concepts, topics, entities, gaps, sources, and insights.
- Connections and insights preserve reason, evidence, calculated confidence, and provenance.
- Graph search combines note data, semantic memory, ontology, and graph structure.
- Operational failures remain separate from learner-facing knowledge insights.
- Graph mutations are persistent, reversible where supported, and audited.
- Attachments can become cognitive sources through controlled extraction, OCR, and transcription.
- Authentication protects one local owner account without a default password.

## Reproduced Historical Evidence

| Area | Evidence | Result |
|---|---|---|
| API | Unit and integration suite | 156 passed |
| Worker | Integration, fallbacks, prompts, resilience | 34 passed |
| Web | Playwright with disposable API and database | 13/13 passed |
| Web build | Production `next build` | Passed |
| Types | TypeScript `--noEmit` | Passed |
| Diff | `git diff --check` | Passed |
| Installation | Isolated Compose project | Web, API, and worker healthy |
| Pipeline | Disposable note in clean installation | Completed in 82 seconds |
| Search | Disposable note query | 19 milliseconds |
| Data | Disposable database, volume, and vault | Production data unchanged |

## Clean-Install Findings

### Internal Worker Host

The worker used `http://api:8000`, but `api` was absent from the allowed-host list.
The middleware returned HTTP 400 and jobs could not run. The Compose contract now includes
the internal host and regression coverage verifies worker/API parity.

### Compose Environment File

An isolated project originally reused assumptions from the primary environment. Startup
validation now checks required paths, provider mode, credentials, service tokens, and
runtime directories before application work begins.

## Subsystem Assessment

| Subsystem | Assessment |
|---|---|
| Vault | Real Markdown source with guarded paths and atomic mutations |
| API | Typed contracts, schema migrations, maintenance, and audit surfaces |
| Worker | Durable queue processing with retries, leases, cancellation, and recovery |
| Cognitive layer | Evidence-backed extraction, retrieval, graph inference, and review |
| Graph | Canonical ontology, typed edges, semantic quarantine, and calculated confidence |
| Web | Authenticated workspace, accessible controls, responsive graph, and full node pages |
| Operations | Backups, restore checks, health probes, diagnostics, and release gates |

## Security

- Owner authentication uses hardened password hashing and secure session controls.
- Sensitive mutations require CSRF protection.
- Provider secrets are never returned to the browser.
- Remote processing requires explicit consent.
- Online validation rejects unsafe and private network targets.
- Prompt injection defenses treat notes, attachments, graph labels, and retrieved passages as data.
- Audit events cover account, configuration, and sensitive graph operations.

## Cognitive Integrity

- Generated claims require persisted source evidence.
- Missing evidence produces an explicit insufficient-evidence state.
- Confidence uses evidence signals and a persisted 95% interval.
- User edits trigger semantic validation and graph recalculation.
- Unsupported ontology names and relationships are quarantined.
- HippoRAG receives canonical triples and supports multihop retrieval.
- System-generated prose is English; user-authored evidence remains verbatim.
- Runtime code contains no seeded demo or fabricated knowledge payloads.

## Final Opinion

The historical v1.0 release gates were satisfied. Later releases supersede the historical
counts above; use the active release plan, README, changelog, and current CI results for the
latest certification.
