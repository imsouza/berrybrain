# Migration To 1.4.8

## Scope

Version 1.4.8 upgrades graph identity, artifact state, ontology metadata, feedback learning, Settings,
provider health, and observability. The migration is automatic at API startup and is designed for
existing local vaults and SQLite databases.

## Before Upgrade

1. Stop API and Worker processes so no job can write during backup.
2. Back up the SQLite database, Markdown vault, attachments, job inbox, and sidecar data.
3. Verify the backup manifest and checksums.
4. Record the current release tag, provider mode, active provider/model assignments, and vault path.
5. Keep the original backup immutable until post-upgrade verification passes.

## Schema Changes

- Schema version advances to v12.
- Canonical graph artifacts gain stable UUID/IRI identity and version-aware state.
- Parent and source relationships gain foreign keys, indexes, uniqueness, and lifecycle constraints.
- Existing verified orphan records are archived instead of silently retained as active knowledge.
- Graph feedback and learning events are durable backup-owned tables.
- SQLite foreign-key enforcement is enabled on every connection.

The migration does not rewrite Markdown note content. Note IDs and graph note identity remain stable
across rename and move. Material edits create a new source version and repair only affected
provenance; deletion removes note-owned evidence and recalculates shared artifacts.

## Provider And Judge Changes

- Cloud and Local remain mutually exclusive execution modes.
- Active-provider health replaces the legacy Ollama-specific health response.
- Legacy heartbeat input remains temporarily accepted for rolling compatibility.
- Judge committee defaults are resolved from the live active-provider catalog and structured JSON
  compatibility probes. No fixed provider model ID is assumed.
- Stale model invocations are reconciled at monitoring time.

Review Settings after upgrade. A cloud configuration must not contain an active Ollama route, and a
local configuration must not call a cloud generation endpoint.

## Learning Behavior

User actions affecting knowledge now create scoped learning records. Existing graph feedback is
preserved and migrated into the active policy where applicable. This changes future admission and
generation policy but does not train provider model weights. See `docs/learning-and-feedback.md`.

## Post-Upgrade Verification

1. Start API, then Worker, then Web.
2. Confirm `/health`, authentication, CSRF, Worker heartbeat, and active-provider health.
3. Run the vault scan and wait for the finite pipeline ETA to clear.
4. Verify note nodes appear immediately and derived nodes arrive through the queue.
5. Confirm ignored, deleted, quarantined, and stale artifacts are absent from default Graph and Ask.
6. Open ontology JSON-LD/Turtle export and run the graph validation endpoint.
7. Confirm Monitor shows `feedback-guided-adaptation`, `feedback-policy.v1`, and
   `model_weights_updated=false`.
8. Test backup and restore in an isolated directory before deleting the pre-upgrade backup.

## Rollback

Application downgrade against a migrated live database is not supported. Stop services, preserve
the failed-upgrade database for diagnosis, restore the complete pre-upgrade backup, and redeploy the
previous tagged release. Do not copy only the SQLite file when vault or sidecar state changed after
upgrade.
