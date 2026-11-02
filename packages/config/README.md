# Config Boundary Contract

Shared configuration conventions and environment contracts across BerryBrain services (`web`, `api`, `worker`, `hipporag`).

## Key Runtime Settings

- **Workspace & Storage**: `BERRYBRAIN_VAULT_PATH`, `BERRYBRAIN_DATABASE_URL`, `BERRYBRAIN_VAULT_LOCK_DIR` (shared across `api` and `worker` containers for safe concurrent writes and backups).
- **Security & Network**: `BERRYBRAIN_SESSION_SECRET`, `BERRYBRAIN_API_TOKEN` (internal worker bootstrap credential—issue separate expiring service tokens via `/api/v1/security/service-tokens` for external apps), `BERRYBRAIN_CORS_ORIGINS`, and `BERRYBRAIN_MAX_REQUEST_BODY_BYTES`.
- **Reverse-Proxy Mounts**: `NEXT_PUBLIC_BASE_PATH` / `/berrybrain` mount support with relative OpenAPI server resolution (`../..`).

Never commit `.env` files, provider API keys, or service tokens to version control.
