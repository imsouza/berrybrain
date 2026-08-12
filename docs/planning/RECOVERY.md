# BerryBrain recovery guide

This guide covers local recovery for the self-hosted SQLite deployment.

## Before restoring

1. Stop the Worker so no job writes while the database is replaced.
2. Keep a copy of the current `data/` and `vault/` directories.
3. Confirm that the target BerryBrain version is equal to or newer than the backup version.
4. Never edit `manifest.json`; restore rejects missing files, size changes, and SHA-256 mismatches.

## Restore from the UI or API

Use **Settings → Backups** or call `POST /api/v1/backups/{backup-id}/restore` with an authenticated administrator session. A successful response reports:

- checksum verification status;
- source and resulting schema versions;
- migrations applied;
- restored file count;
- table counts captured by the backup.

Restart API and Worker after a database restore so every process opens the restored database.

## Manual recovery

1. Stop Web, API, and Worker.
2. Verify every file listed in `manifest.json` with SHA-256 before copying it.
3. Restore the SQLite file from the backup root into `data/sqlite/`.
4. Restore the contents of `vault/` into the configured vault path.
5. Preserve `.attachments/`; attachment metadata references those relative paths.
6. Start API first and check `/health`. `schema.compatible` must be `true`.
7. Start Worker and Web, then inspect Monitor for failed or stale jobs.
8. Run a vault scan only after confirming note and attachment counts.

## Corruption or incompatible schema

- `Backup checksum mismatch`: do not force the restore. Recover the affected file from another copy.
- `Backup schema is newer`: upgrade BerryBrain; never downgrade the database by editing its version.
- Missing legacy manifest: BerryBrain can restore it as `legacy_unverified`, but retain the original backup and verify files independently.
- Partial vault recovery: Markdown and original attachments remain readable without BerryBrain; portable JSONL and GraphML exports are under `portable/`.
