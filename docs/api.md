# BerryBrain API — external application integration

BerryBrain is an architecture with an HTTP interface, not a web UI dependency.
An editor, content tool, study application, or automation can create Markdown
notes, observe asynchronous processing, retrieve knowledge, and query the graph
without importing the Next.js frontend or accessing SQLite directly.

The supported deployment model is **one owner-managed shared workspace**.
Service tokens are for trusted server applications. They are not tenant, user,
or vault permission boundaries. Do not distribute one in a public browser bundle,
mobile binary, repository, or URL. Keep it on your application's backend.

## Discovery and contract

| Resource | Direct API | Web reverse proxy mounted at `/berrybrain` |
| --- | --- | --- |
| Discovery | `http://localhost:8000/api/v1` | `/berrybrain/api/v1` |
| OpenAPI JSON | `http://localhost:8000/api/v1/openapi.json` | `/berrybrain/api/v1/openapi.json` |
| Interactive Swagger documentation | `http://localhost:8000/api/v1/docs` | `/berrybrain/api/v1/docs` |
| Health and DB schema compatibility | `http://localhost:8000/health` | Use the internal API health route |

OpenAPI is the machine-readable inventory of the installed routes, request
parameters, authentication alternatives, and declared response models. Core
note, search, graph-page, and Ask responses have explicit models; some internal
and administrative responses remain generic objects. This is not yet a fully
typed public SDK contract. The standard `/docs`, `/redoc`, and `/openapi.json`
also exist on the direct API origin. Discovery/documentation contain no notes
or tokens and are public. Swagger/ReDoc load UI assets from an external CDN;
raw OpenAPI and the REST API do not require that CDN.

The versioned schema uses a relative server URL to retain reverse-proxy mounts.
For a standalone client use the origin/mount plus `/api/v1`. Target the API
directly for long-running model requests when a proxy has a shorter deadline.

## Authentication and credentials

External service calls use `Authorization: Bearer TOKEN`. The existing
`BERRYBRAIN_API_TOKEN` is the bootstrap/worker credential; do not reuse or rotate
it merely to connect another application.

The owner can issue an independent credential:

1. Sign into the owner account in the BerryBrain browser application.
2. Send `POST /api/v1/security/service-tokens` with JSON
   `{"name":"writing-assistant","expires_in_days":90}` using that session's
   cookie, CSRF cookie, and matching `X-CSRF-Token` header.
3. Store the returned `token` securely. It is returned only at issuance; listings
   expose metadata, not the raw value. Allowed validity: 1–365 days.
4. Inspect credentials with `GET /api/v1/security/service-tokens` and revoke an
   individual credential with `POST /api/v1/security/service-tokens/{id}/revoke`.

Example from the developer console **of your authenticated owner page**:

```javascript
const csrf = decodeURIComponent(document.cookie.split('; ')
  .find(row => row.startsWith('bb_csrf='))?.split('=').slice(1).join('=') || '');
// Replace the mount and cookie name if your deployment customizes them.
const response = await fetch('/berrybrain/api/v1/security/service-tokens', {
  method: 'POST', credentials: 'same-origin',
  headers: {'Content-Type': 'application/json', 'X-CSRF-Token': csrf},
  body: JSON.stringify({name: 'writing-assistant', expires_in_days: 90})
});
if (!response.ok) throw new Error(`Issuance failed: ${response.status}`);
const issued = await response.json(); // issued.token: save privately; do not log/share it.
```

Token issuance preserves the existing worker credential. The separate legacy
`POST /security/service-tokens/rotate` operation rotates **all active service
credentials** into a short grace period; use it only for a coordinated rotation
of every affected client, including the worker. Normal per-application renewal
means issuing a replacement, updating that application, then revoking its old
token. The last valid active service token cannot be revoked without replacement.

Service tokens do not bypass owner-only configuration, backup/restore,
credential management, or other administrative routes. The OpenAPI security
requirements distinguish these from integration routes. Browser mutations use
both a session cookie and CSRF protection; a valid Bearer token does not require
CSRF. A token that is expired/revoked returns HTTP 401.

## Core workflow

```text
External application → authenticated API → canonical Markdown + SQLite control state
                                          ↓ queued jobs
                           worker → graph / indexes / optional HippoRAG projection
                                          ↓
External application ← status / search / evidence-grounded Ask
```

Do not write directly to the DB, graph cache, or worker queue. API mutations
perform validation, preserve note identity and provenance, and enqueue follow-up
work. Markdown remains canonical note content; identities, credentials,
configuration, policies, provenance, and jobs are authoritative operational
state, not disposable caches. Back up both the vault and database.

| Operation | Route | Integration rule |
| --- | --- | --- |
| List notes | `GET /notes?limit=50&offset=0` | Follow `nextOffset` until `null`; `total` is also returned. Limit 1–200. |
| Create | `POST /notes` | JSON `title`, `content`, optional `folder`; returns 201 and the note identity/hash. |
| Read | `GET /notes/{path}` | URL-encode path segments; keep `/` separators. |
| Update | `PUT /notes/{path}` | Send `content` and the last `base_content_hash`; stale edits return 409. |
| Processing | `GET /notes/{path}/status` | The note exists before AI jobs finish. Inspect job states and failures. |
| Search | `GET /search?q=...&limit=10` | Limit 1–100; lexical/vector/graph results include evidence signals. |
| Graph nodes | `GET /graph/nodes?cursor=0&limit=250` | Follow `nextCursor` (maximum limit 2000). |
| Graph edges | `GET /graph/edges?cursor=0&limit=500` | Follow `nextCursor` (maximum limit 5000). |
| Ask | `POST /graph/infer` | JSON `question`; inspect `status`, `answer`, `evidence`, `routes`, and `inferenceId`. |
| Jobs | `GET /jobs?limit=50` | Limit 1–200; internal handlers require claim ownership where applicable. |
| Activity | `GET /activity?limit=50` | Limit 1–200. |
| Ontology | `GET /graph/ontology` and `/graph/ontology/export` | Semantic vocabulary and export; not a replacement for runtime control state. |

Paths in this table are relative to `/api/v1`. Creation folders are `inbox`,
`study`, `permanent`, `review`, or `templates`; path moves have a separate API.
The compatibility notes list with no limit still returns the whole vault and
scans Markdown files: external clients should always request a page. Its paging
is positional, not a snapshot; concurrent inserts/moves can shift offsets.

Graph pages return a `graphVersion`. A changing version between pages signals
concurrent graph changes; discard/reload an inconsistent assembled view. A
cursor is a record ID, not a page number or stable domain identity. Prefer
`stableId`/`iri` when maintaining references across projections or renames.
Default pages include accepted artifacts; `includeProvisional=true` is for
review workbenches and still excludes rejected/quarantined artifacts. Edges
only expose endpoints visible under the same policy.

For network visualization, use `GET /graph/edges?compact=true&limit=1000`
and follow `nextCursor`. This opt-in projection omits `evidence` and
`confidenceInterval.factors` without reading those audit blobs from storage.
IDs, endpoints, relationships, reason, confidence bounds and provenance
identifiers remain unchanged. Omitted fields mean **not loaded**, not missing
evidence. The default (`compact=false`) retains the complete existing contract;
audit/inference clients must not treat the visual projection as an evidence
bundle. Nodes, ontology shapes and semantic colors are unchanged.

`GET /jobs/pipeline-progress` samples the latest 500 note-linked pipeline jobs,
excluding unrelated global maintenance before applying the limit. It supports
structured and legacy JSON note identities. It is a bounded progress view, not
the complete job ledger; use paginated `/jobs` and job detail for history.

HTTP 200 from Ask means the request completed, **not that every assertion is
true or that sufficient evidence exists**. Preserve the returned status and
citations, distinguish inference from evidence, and do not present an abstention
as an answer. Grounding checks reduce unsupported answers; they do not prove
100% factual correctness. Ask can call the configured local or cloud model and
incur that provider's costs. Web research is a separate explicit workflow, not
permission for ordinary Ask to silently use arbitrary web content.

## Job health and dashboard counts

`GET /api/v1/home/summary` reports lifetime job totals using SQL aggregates.
The `createdToday`/`completedToday` counters use UTC day boundaries.
`recentlyCompleted` contains at most eight items; it is not the source of the
lifetime `progress.completed` count. Duration estimates use up to 200 recent
successful executions per required job type and remain unavailable when there
are no valid samples. These estimates are not processing-time guarantees.

`GET /api/v1/jobs/health` treats a running job as stale when its lease expires.
The start-time threshold is used only for legacy jobs with no lease. Pending
work aged 30 minutes or more breaches the declared queue threshold; read
`slo.oldestPendingAgeSeconds` for the oldest pending age. These are operational
signals, not model-quality metrics.

In both views, active/running counts include jobs awaiting cancellation
acknowledgement. Failed counts include jobs that exhausted their attempts (`dead_letter`);
the separate `dead_letter` count is a subset, not an additional failure count.
The Home can finish current work while still showing historical failures.

Releases 1.4.9 and 1.4.10 use database schema 14. The additive index migration preserves
history; the HTTP API remains `/api/v1`. Older binaries enforce schema
compatibility, so an image-only rollback after migration is not sufficient.

## Operational history and model alerts

These endpoints use the same workspace authentication and authorization as the
rest of `/api/v1`; they do not expose host or Docker logs.

- `GET /automation-logs?compact=true&limit=50`: bounded event summaries without
  before/after note snapshots. Limit 1–100. `nextCursor` is an insertion ID; pass
  it as `before_id` for older entries. Order is descending insertion ID, not
  event timestamp. The default `compact=false` preserves full-event fields.
- `GET /automation-logs/export?limit=1000`: downloadable JSON, latest 1–1000
  compact events (default 500), with `Cache-Control: no-store`. Credentials are
  redacted and snapshots excluded, but titles, paths, and descriptions may still
  contain private metadata. Review before sharing; this is not a backup.
- `GET /jobs?status=failed&include_dead_letter=true&include_counts=true&limit=50`:
  server-side filtering includes exhausted retries. Use `nextCursor` as
  `before_id` to page older jobs; limit 1–200. Optional `counts` cover the whole
  queue, independent of the page/filter. `counts.failed` includes `dead_letter`;
  `counts.dead_letter` is a subset, so do not add it again to `counts.total`.
- `GET /monitor/stats`: job totals and completions in the last hour are global.
  `jobs.recent_sample_size` identifies the bounded 200-job sample used for type
  breakdowns; model-invocation statistics also describe a recent 200-row sample.
- `GET /monitor/model-alerts`: current configured-model warnings inferred from
  recent recorded failures, not a live provider-catalog probe. A bounded window
  of 1000 invocations is inspected; a later successful invocation clears the
  corresponding current warning. Older generic `cloud` records cannot prove
  provider identity and are ignored when predating configuration validation.

New observed model/capability rejections also create unread, per-model
notifications. A rate-limit error alone is not treated as model removal.
Notifications remain historical until marked read; current warnings and unread
history are different views. No automatic model replacement, paid availability
probe, or bulk job retry is performed.

## Python example

See [the standard-library client](../examples/berrybrain_client.py), with no
third-party runtime dependency. It rejects redirects, supplies timeouts, retains
HTTP errors/correlation IDs, and never blindly retries writes.

```bash
export BERRYBRAIN_URL='http://127.0.0.1:8000'
export BERRYBRAIN_SERVICE_TOKEN='YOUR_PRIVATE_SERVICE_TOKEN'
python examples/berrybrain_client.py
```

Running that file only lists notes. A write workflow in your application:

```python
from examples.berrybrain_client import BerryBrainClient, APIError
import os

api = BerryBrainClient(os.environ['BERRYBRAIN_URL'], os.environ['BERRYBRAIN_SERVICE_TOKEN'])
note = api.create_note('Study plan', '# Study plan\nMy source material.')
try:
    note = api.update_note(note['path'], '# Study plan\nRevised.', note['content_hash'])
except APIError as error:
    if error.status == 409:
        # Fetch current content and ask the user to merge; do not overwrite it.
        current = api.read_note(note['path'])
    else:
        raise
status = api.note_status(note['path'])
```

## Errors, limits, and deployment

- **401:** missing, expired, or revoked credentials; includes `WWW-Authenticate: Bearer`.
- **403:** owner-only operation, invalid CSRF, or disallowed origin.
- **404:** missing resource/path. Do not fabricate a replacement identity.
- **409:** version/claim conflict, invalid state, or protected last credential.
- **413:** body exceeds `BERRYBRAIN_MAX_REQUEST_BODY_BYTES` (default 25 MiB).
  The actual streamed bytes are checked too. Base64 attachment JSON expands
  binary size; per-category settings do not override this whole-request limit.
- **422:** invalid fields/bounds; validation responses omit submitted raw input.
- **429 / 503:** respect `Retry-After` when supplied; do not retry a non-idempotent
  write without checking whether it already succeeded.
- **502 / 503 on Ask:** provider/upstream failure, not proof the vault has no answer.

There is no general `Idempotency-Key` contract or webhook delivery system yet.
Use bounded polling with backoff (for example 2, 4, 8, then 15 seconds), a timeout,
and cancellation in your client. Creation can enqueue model work; after a
transport timeout reconcile state before attempting another creation.

Use HTTPS outside loopback/trusted local networks. CORS is an explicit origin
allowlist, not authentication; configure `BERRYBRAIN_CORS_ORIGINS` for approved
browser frontends. Prefer backend-to-backend integration. The API returns
`X-Correlation-ID` and `Server-Timing`, and API responses use `Cache-Control:
no-store`. Keep the DB, vault, and provider credentials off public static hosting.

Current limitations: shared-workspace authorization; no OAuth delegation or
token scopes; some generic response schemas; no compatibility-certified SDK;
no claim of multi-node/high-availability scaling for SQLite; no general
per-token usage quotas. These are explicit architecture evolution items, not
features inferred from having an HTTP endpoint. See the
[system review and checkbox plan](reviews/2026-10-03-system-api-review.md).
