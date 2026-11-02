# Shared Boundary Contract

Cross-cutting primitive types, pure formatting helpers, and zero-dependency utilities that remain independent of higher-level business, persistence, or presentation layers (enforced by `scripts/lint/architecture-fitness.js`).

For external applications integrating with BerryBrain over HTTP without importing internal workspace modules, use the zero-dependency reference adapters in `examples/berrybrain_client.py` and `examples/berrybrain_client.mjs` alongside `/api/v1/openapi.json`.
