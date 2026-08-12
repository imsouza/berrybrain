# BerryBrain 1.0 Definition of Done

BerryBrain 1.0 is done only when a clean self-hosted install can prove the full
second-brain loop with reproducible tests.

## Release Gates

- Web, API, and Worker start with `docker compose up -d`.
- API health endpoint returns healthy.
- Web landing and `/brain` routes load without client-side exceptions.
- Worker sends heartbeat to the API.
- A fixture vault scan creates jobs.
- A changed Markdown note completes the cognitive pipeline without manual database edits.
- Generated graph edges include reason, evidence, confidence, provider/model, prompt version, and status.
- Generated insights are knowledge insights, not system diagnostics.
- Semantic search is validated against a fixture dataset.
- Backup and restore are tested from a clean instance.
- CI blocks release on backend, worker, web, container, and security failures.

## Non-Negotiables

- Markdown files remain the source of truth.
- No AI artifact is accepted without provenance.
- No hidden provider failure may become an empty successful result.
- No destructive action may run without confirmation.
- No commercial use is allowed without written permission from the owner.

