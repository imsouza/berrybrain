# Upgrade and rollback

## Upgrade

1. Create a BerryBrain backup and retain the reported manifest verification data.
2. Stop Worker, Web, and API.
3. Pull the target source revision or immutable image tag.
4. Review `CHANGELOG.md` and `KNOWN_LIMITATIONS.md`.
5. Build images with `docker compose build --pull`.
6. Start API first. `/health` must report `schema.compatible: true` and the expected target version.
7. Start Worker and Web with `docker compose up -d`.
8. Confirm Worker heartbeat, queue recovery, note counts, graph counts, and a known semantic query.

Schema migrations are additive. Jobs/embeddings are normalized during bootstrap, and compatible restored schemas migrate automatically.

## Rollback before a schema change

Stop the stack and start the previous immutable images. Do not change the vault. Confirm `/health`, then start Worker.

## Rollback after a schema change

1. Stop all services.
2. Restore the pre-upgrade backup using the target version's restore path or the manual recovery guide.
3. Start the previous API image and verify schema compatibility.
4. Start Worker and Web.

Do not edit `schema_migrations` manually. BerryBrain blocks a database newer than the running build to prevent destructive downgrade behavior.

## Emergency rollback

Markdown and original attachments remain readable directly from the vault. Portable JSONL and GraphML under the backup's `portable/` directory can be inspected without BerryBrain. See `docs/planning/RECOVERY.md`.
