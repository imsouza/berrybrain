# BerryBrain Operations Runbook

This runbook is the release procedure for the first-party Docker Compose stack. It covers
upgrade, rollback, backup restore, health validation, and incident recovery for a local
self-hosted instance.

## Supported topology

The default `docker compose up -d` command must start all three required services:

- `api`: owns the SQLite schema, HTTP API, backups, and health endpoint;
- `web`: serves the public site and authenticated application;
- `worker`: processes the cognitive pipeline and emits heartbeats.

`searxng` is optional and only starts with the `web-validation` profile. Persistent data
lives in the `berrybrain_data` volume and the host vault mounted from
`BERRYBRAIN_HOST_VAULT_PATH` (default `./vault`). Keep `.env` and external secret-manager
values outside backups and source control.

## Release preflight

Run these checks from the repository root before changing a running instance:

```bash
git status --short
docker compose config --quiet
docker compose ps
curl --fail --silent http://localhost:${BERRYBRAIN_API_PORT:-8000}/health
```

Do not upgrade with uncommitted deployment changes. Record the current immutable tag or
commit so rollback does not depend on memory:

```bash
git rev-parse HEAD > .berrybrain-pre-upgrade-revision
```

## Create and verify a backup

Create the pre-upgrade backup while the current `api` is healthy:

```bash
docker compose exec api python -c "from berrybrain_api.backup import create_backup; print(create_backup())"
docker compose exec api python -c "from berrybrain_api.backup import list_backups; print(list_backups())"
```

Record the returned `backup-YYYYMMDDTHHMMSSZ` identifier. A BerryBrain backup contains a
consistent SQLite snapshot, the complete vault, portable metadata, schema/version metadata,
and a checksum manifest. API keys, service tokens, and other sensitive settings are omitted;
restore those separately from the deployment secret store.

## Upgrade by checkpoint

Deploy a reviewed tag or exact commit. Avoid an unqualified `git pull` on a production
instance.

```bash
git fetch --tags origin
git checkout <reviewed-tag-or-commit>
docker compose build --pull api worker web
docker compose up -d api
docker compose up -d worker web
```

The API applies forward schema migrations before serving traffic. Do not start an older API
against a database already migrated by a newer release; use the rollback procedure below.

## Post-upgrade validation

All required services must be running and healthy:

```bash
docker compose ps api web worker
curl --fail --silent http://localhost:${BERRYBRAIN_API_PORT:-8000}/health
curl --fail --silent http://localhost:${BERRYBRAIN_WEB_PORT:-3000}/berrybrain >/dev/null
docker compose logs --since=10m api worker web
```

Then verify in the application:

1. `Monitor` shows a recent worker heartbeat and no stale active jobs.
2. Create a disposable note and wait for its cognitive stages to complete.
3. Confirm that the note, concepts, explainable connection evidence, and any grounded insight
   appear in `Knowledge Graph`.
4. Ask one graph question and confirm that the answer cites note or graph evidence.
5. Delete the disposable note and confirm the graph projection refreshes.

Release performance budgets are:

- graph projection p95 at or below 2,500 ms for 5,000 nodes and 20,000 edges;
- graph JSON payload at or below 16 MiB for that corpus;
- semantic retrieval p95 at or below 500 ms for the release benchmark corpus;
- no missing nodes or edges in either projection gate.

The automated release gate is:

```bash
cd apps/api
python -m benchmarks.maturity_release_gate
```

## Rollback

Rollback is a coordinated code, database, and vault operation. It replaces the live database
and the entire live vault with the selected backup. First create an emergency snapshot of the
failed state so post-incident evidence and new user data are not lost:

```bash
docker compose exec api python -c "from berrybrain_api.backup import create_backup; print(create_backup())"
docker compose stop web worker api
git checkout "$(cat .berrybrain-pre-upgrade-revision)"
docker compose build api worker web
docker compose run --rm api python -c "from berrybrain_api.backup import restore_backup; print(restore_backup('BACKUP_ID'))"
docker compose up -d api worker web
```

Restore validates checksums, rejects a backup from a newer unsupported schema, migrates the
staged database forward when supported, runs SQLite integrity checks, and only then swaps the
database and vault. If either swap fails, both resources are rolled back to the pre-restore
state. Never copy a SQLite file over a running API process manually.

Repeat every post-upgrade validation after rollback. Keep the emergency snapshot until the
incident review is complete.

## Disaster recovery drill

At least once per release line, test recovery against a disposable Compose project:

```bash
docker compose -p berrybrain-drill up -d api worker web
docker compose -p berrybrain-drill exec api python -c "from berrybrain_api.backup import list_backups; print(list_backups())"
docker compose -p berrybrain-drill down
```

Use a copy of the backup and a separate vault path; never point a drill at the production
volume. The drill passes only when the manifest verifies, the schema reaches the current
version, notes and settings counts match metadata, the worker heartbeat is fresh, and a graph
question returns grounded evidence.

## Incident triage

1. Stop mutation first: `docker compose stop worker`.
2. Capture `docker compose ps`, the current revision, timestamps, and the last 30 minutes of
   `api` and `worker` logs.
3. Create an emergency backup if the API and storage are readable.
4. Check `/health`, worker heartbeat age, failed/stale jobs, provider HTTP status, and the model
   invocation ledger before retrying work.
5. Prefer retrying a specific job or reprocessing a node/neighborhood over rebuilding the full
   graph.
6. Roll back only with a recorded revision and backup identifier.
7. After recovery, document user impact, data reconciliation, cause, and a regression test.

Do not paste note contents, API keys, authorization headers, or raw provider responses into
public incident reports.
