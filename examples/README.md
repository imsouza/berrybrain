# BerryBrain Reference Clients (`examples/`)

Zero-dependency reference clients for integrating trusted server-side applications, CLIs, editor back-ends, and AI agent pipelines with a self-hosted **BerryBrain REST API v1** instance:

- [`berrybrain_client.py`](./berrybrain_client.py) — Python 3.11+ standard-library client (`urllib.request`, no third-party dependencies).
- [`berrybrain_client.mjs`](./berrybrain_client.mjs) — Node.js 20+ / TypeScript-friendly ESM client (native `fetch`, no npm dependencies).

For complete architectural integration patterns—including running BerryBrain as a headless cognitive sidecar, extending the 1,576 Markdown Agent Skills, or adopting BerryBrain's 5 core invariants in your own stack—see [`docs/integrating-berrybrain-architecture.md`](../docs/integrating-berrybrain-architecture.md) and [`docs/api.md`](../docs/api.md).

## Security & Workspace Rules

1. **Issue a dedicated expiring service token** as the signed-in local owner (`POST /api/v1/security/service-tokens`); never reuse the internal worker token (`BERRYBRAIN_API_TOKEN`) and never bundle a service token inside a public browser frontend.
2. **Single shared owner workspace**: service tokens authenticate trusted backend callers into the owner's workspace; they do not provide multi-tenant per-user or per-vault ACL isolation.
3. **No redirects, no blind conflict retries**: both clients block HTTP redirects so `Authorization: Bearer` tokens cannot leak across origins, preserve `X-Correlation-ID` on failures, and surface `HTTP 409` on `update_note` / `updateNote` when `base_content_hash` is stale so callers reload instead of silently overwriting edits.

## Quick Verification (Read-Only)

Running either module directly only lists notes (`GET /api/v1/notes`)—it never writes files or invokes a language model:

```bash
export BERRYBRAIN_URL="http://127.0.0.1:8000"
export BERRYBRAIN_SERVICE_TOKEN="YOUR_PRIVATE_SERVICE_TOKEN"

# Python 3.11+
python3 examples/berrybrain_client.py

# Node.js 20+
node examples/berrybrain_client.mjs
```

## End-to-End Python Example

```python
import os
from examples.berrybrain_client import APIError, BerryBrainClient

api = BerryBrainClient(
    os.environ["BERRYBRAIN_URL"],
    os.environ["BERRYBRAIN_SERVICE_TOKEN"],
)

# 1. Inspect physical vault namespaces and matched Agent Skills
vaults = api.list_vaults()
skills = api.match_skills("Write a systematic literature review on GraphRAG")

# 2. Create a canonical Markdown note and wait for bounded Autopilot assimilation
note = api.create_note(
    "Distributed Consensus Notes",
    "# Consensus\nRaft separates leader election from log replication.",
    folder="inbox",
)
status = api.wait_until_ready(note["path"], timeout_seconds=60)

# 3. Safe optimistic update with base_content_hash
try:
    note = api.update_note(
        note["path"],
        note["content"] + "\n\nPaxos and Raft both require majority quorums.",
        note["content_hash"],
    )
except APIError as err:
    if err.status == 409:
        latest = api.read_note(note["path"])
        raise RuntimeError(f"Concurrent edit detected at {latest['content_hash']}") from err
    raise

# 4. Hybrid + Graph search and grounded GraphRAG inference
hits = api.search("leader election log replication", limit=5)
answer = api.ask("How does Raft organize consensus according to my notes?")
print(answer["status"], answer["answer"])
```

## End-to-End Node.js / TypeScript Example

```javascript
import { BerryBrainClient, BerryBrainApiError } from "./examples/berrybrain_client.mjs";

const api = new BerryBrainClient(
  process.env.BERRYBRAIN_URL,
  process.env.BERRYBRAIN_SERVICE_TOKEN,
);

const note = await api.createNote(
  "Architecture ADR",
  "# ADR-01\nCanonical Markdown stays separate from rebuildable graph projections.",
);

await api.waitUntilReady(note.path, { timeoutMs: 60_000 });

const inference = await api.ask("Why keep canonical Markdown separate from graph projections?");
console.log({
  status: inference.status,
  answer: inference.answer,
  evidenceCount: inference.evidence?.length ?? 0,
  supportMean: inference.confidence?.score ?? null,
});

// Export governed knowledge graph as W3C JSON-LD or Turtle
const jsonLd = await api.exportOntology({ format: "json-ld" });
```
