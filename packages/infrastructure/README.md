# Infrastructure Boundary Contract

Concrete adapters for filesystems, persistence, background queues, vector indexes, ontology serialization, backups, and AI provider gateways.

## Active Adapters in BerryBrain v1.5

- **Canonical Vault Storage**: Advisory-locked Markdown filesystem persistence (`BERRYBRAIN_VAULT_LOCK_DIR`), physical vault namespace directories, watcher/scan reconciliation, and sandboxed attachment extractors (`pypdf`, `tesseract-ocr`, `faster-whisper` with `no_new_privs`).
- **SQLite Control & Graph Store**: Schema v25 migrations, FTS5 lexical index, durable job leases, append-only feedback ledger, and manifest-checksummed backup/restore archives.
- **Semantic & Ontology Gateways**: `rdflib` + `pyshacl` validation, JSON-LD/Turtle graph export, optional Qdrant/Chroma vector stores, and optional HippoRAG structural sidecar synchronization.
- **AI Provider Transport**: Mutually exclusive Local (Ollama) XOR Cloud OpenAI-compatible gateways with 1-click Auto Config capability probing, Judge v3 structured-output verification, and explicit per-stage request timeouts.
