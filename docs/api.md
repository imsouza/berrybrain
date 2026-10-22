# BerryBrain API — external application integration

BerryBrain is an architecture with an HTTP interface, not a web UI dependency.
An editor, content tool, study application, or automation can create Markdown
notes, observe asynchronous processing, retrieve knowledge, and query the graph
without importing the Next.js frontend or accessing SQLite directly.

The supported deployment model is **one owner-managed shared workspace**.
Service tokens are for trusted server applications. They are not tenant, user,
or vault permission boundaries. Do not distribute one in a public browser bundle,
mobile binary, repository, or URL. Keep it on your application's backend.
Profiles and their `vaultSubpath` field are currently administrative metadata:
creating a profile does **not** create an independent vault, relocate Markdown,
partition the graph, or grant access to a separate set of notes. New profile
subpaths must be relative names; traversal and absolute paths are rejected.
The canonical Markdown root is still the configured `vault_path`. Applications
can list named physical sub-vaults with `GET /api/v1/vault/namespaces`. A named
vault has a stable ID and a `vaults/<name>--ask-<id>` Markdown directory inside
that root; note documents expose `vaultId`. It is an organizational namespace,
**not** a separate access-control or graph partition. The default namespace
retains ID `default` and an empty relative path. Only the browser Ask approval
flow currently creates a named vault, together with its first note.
Applications
that require tenant or vault isolation need separate BerryBrain deployments,
credentials, and storage roots until an explicit resource-authorization model
is implemented and validated. Browser Flow history and Ask action plans are
bound to their initiating user, but ordinary workspace knowledge is shared.

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

Owner-only `POST /api/v1/backups` publishes a backup ID only after the database
snapshot, vault copy, metadata, and checksum manifest finish. A failed new
backup is not listed as a usable copy; its temporary staging directory is
removed. The SQLite snapshot has a 300-second **progress** deadline. This is
not a hard wall-clock limit when the operating system is blocked in I/O, and a
successful backup still needs restore verification before a migration/deploy.
API and worker containers must share `BERRYBRAIN_VAULT_LOCK_DIR`; the supplied
Compose file sets it to `/app/data/locks` on their common data volume. This
only coordinates builds using that setting. The currently running installation
must not be assumed to have the new lock placement until both services have
been rebuilt and restarted together.

Flow conversation-history endpoints under `/ask/sessions` require a browser
session and are scoped to the user who created each conversation. A service
token cannot create or access those private browser conversations. Migration 21
assigns older conversations only when the database has exactly one user. With
multiple users, older conversations remain stored but unassigned and inaccessible
through the API; the migration does not guess their owner.

Persisted `POST /graph/infer` answers follow the same browser owner when seeded
into Flow, given feedback, or converted to an insight by inference ID. A browser
cannot use another user's answer or an answer created with a service token.
Trusted service tokens share the installation's service-answer scope; they
cannot use browser-owned answers. Migration 24 assigns legacy answers to a
browser only when exactly one user exists. Ambiguous older answers remain
stored but inaccessible by inference ID, including to service tokens.

Flow assistant turns return a `references` array with verified resource kind,
ID, current path/title and evidence IDs. A follow-up asking to link earlier
sources may put `bbref:resolved:<kind>:<id>` markers in the answer text. These
are internal reference markers, **not URLs**: clients should turn one into a
navigation link only when the same turn's `references` contains that exact
kind and ID, and should use the current path/ID from that record. If a note is
deleted or loses eligibility, its reference is omitted on the next resolution.
Generated HTTP links in model text are not authoritative resource links.

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
| List notes | `GET /notes?limit=50&offset=0` | Follow `nextOffset` until `null`; `total` is also returned. Limit 1–200. Optional `vault_id` filters one registered namespace; each summary has `vaultId`. |
| Create | `POST /notes` | JSON `title`, `content`, optional `folder` and `vault_id`; returns 201, `vaultId`, and the note identity/hash. |
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
Omit `vault_id` or use `default` for the original root. For a named vault,
use an ID returned by `GET /vault/namespaces`; an unknown ID returns 404 and
an unavailable/symlinked namespace returns 409. The server derives the
directory from the registered ID, not from a caller-supplied filesystem path.
Ask plans may also target an existing named vault with `vault_id`. The folder
API reports registered vault boundaries as `protected` and rejects renaming or
deleting those directories (and their `vaults` ancestor); ordinary subfolders
inside a vault remain editable. Manual filesystem renames are not reconciled
into vault identities automatically.
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

### Evidence support (confidence compatibility fields)

`confidenceInterval.method=evidence-support-mean-v2` reports the mean of distinct
recorded support signals, **not probability of truth**. Its `lower`/`upper` bounds
describe uncertainty separately and are not empirically calibrated truth coverage.
The full payload adds `observations` (numeric `score` and `source`) while preserving
the `factors` list. Zero is a measured negative signal; `score=null` and
`sampleSize=0` mean no measured support, not queued work. Read semantic/job state
separately. Missing text/IDs alone do not manufacture a score.

Connection API records retain integer `confidence` percentages (0–100 or null);
their `confidenceInterval.score`, graph scores and Home `confidence` use 0–1.
In particular, connection `confidence=1` means **1%**, not 100%. Home
`confidencePercent` is nullable; `averageConfidence` excludes unmeasured artifacts
and is null when none are measured. Do not infer units from a value's magnitude.

Legacy `empirical-bernstein-bounded-signals-v1` values are interval midpoints,
often 50% regardless of input. The full payload marks `needsRecalculation=true`.
Do not interpret them as the new mean. After backup, an operator can POST
`/graph/confidence/recalculate` with scoped `node_ids` to recompute without calling
an AI provider. This preserves recorded v2 observations and recovers versioned
semantic signals only when the source fingerprint still matches. Lost raw model
signals cannot be reconstructed from the old midpoint. Responses include
`nodesUnavailable` and `edgesUnavailable`; a missing measurement stays unavailable.
The operation does not create Judge jobs or claim successful fresh evaluations.
Source-changing edits still invalidate previous observations.

Internal Judge agents must supply all five bounded rubric criteria. The backend
computes their normalized mean and applies numeric verdict gates. Each new Judge
evaluation replaces one current observation, rather than inflating the sample size
on retries. Policy-only mode is not a measured Judge score. See
[confidence methodology](confidence-model.md) for signal and calibration limits.

`GET /jobs/pipeline-progress` samples the latest 500 note-linked pipeline jobs,
excluding unrelated global maintenance before applying the limit. It supports
structured and legacy JSON note identities. It is a bounded progress view, not
the complete job ledger; use paginated `/jobs` and job detail for history.
Superseded jobs are excluded from this current-progress view, not deleted from
the ledger or reported as completed.

HTTP 200 from Ask means the request completed, **not that every assertion is
true or that sufficient evidence exists**. Preserve the returned status and
citations, distinguish inference from evidence, and do not present an abstention
as an answer. Grounding checks reduce unsupported answers; they do not prove
100% factual correctness. Ask can call the configured local or cloud model and
incur that provider's costs. Web research is a separate explicit workflow, not
permission for ordinary Ask to silently use arbitrary web content.

### Ask-assisted note draft (limited 1.5 work in progress)

`GET /api/v1/ask/action-plans/capabilities` lets an authenticated external
client inspect the current action contract. It reports the shared-workspace
model, supported and currently available actions, one-note-per-approval mode,
allowed folders, content limit, and whether an independent vault can be
created. A trusted service token can read the contract but receives an empty
`availableActions` list: it cannot propose or approve a human Ask plan.
The installed browser session receives `create_note` as available. This route
does not grant permission by itself; the write endpoints recheck session,
CSRF, plan ownership, expiry, and the approved arguments hash.

The Ask UI can turn an answer into an editable Markdown draft in the current
vault or a **new named physical vault**. The latter is still part of the shared
workspace; no per-vault ACL is implied. It does not silently write on a model
response. The browser
first calls `POST /ask/action-plans` with `title`, `folder`, `content`, and an
optional UUID `request_key`. To create a named vault and its first note in the
same approval, include `new_vault_name` (1–160 characters, no slash, backslash,
colon, or control characters).
For a subsequent note in an existing named vault, send `vault_id` from
`GET /vault/namespaces` instead; `new_vault_name` and `vault_id` are mutually
exclusive. The plan captures the registered target path and approval checks
that it still belongs to the same ID and is a real directory.
The response contains the exact preview, `argumentsHash`, a 15-minute expiry,
and a plan ID. The user then sends
`POST /ask/action-plans/{id}/approve` with `arguments_hash`, or rejects via
`POST /ask/action-plans/{id}/cancel`. `GET /ask/action-plans/{id}` retrieves its
state. Approval writes canonical Markdown once as an **unreviewed draft**; it
does not enqueue graph/embedding jobs or make the draft citable by Ask. The
returned `resultPath` links to the created note, and `vaultId` identifies the
registered namespace. A named vault's directory is derived from the immutable
plan ID, so replay cannot create another vault. After checking its claims and
links, the user explicitly calls `POST /ask/action-plans/{id}/review-draft`
with `{"reviewed":true,"content_hash":"<current SHA-256>"}` after displaying
the current `GET /notes/{path}` content and `content_hash`. Only then is the
note eligible for retrieval and normal note processing. The release is recorded
in the automation audit log with the plan ID, user ID, and content hash, but not
the note body. If the file changes
after display, the review returns HTTP 409; reload and review its current
content. The hash is checked again after database sync, so an edit during
review also returns HTTP 409 without promoting the draft. An edited draft can
be reviewed without discarding the edits. A
repeated approval or review is idempotent.
The plan binds the saved result to the note's database ID and stable ID. Its
`resultPath` resolves the **current** path after a rename or move. If the note
was deleted, `resultPath` becomes `null` and review is refused, even if another
note now occupies the old path. Migration 19 backfills older plans only when
the deterministic plan path and original content still match; it never treats
a path alone as proof of identity.
If another editor changes the file between write and database sync, the plan
becomes `partial`: its current `resultPath` is shown, the edited content is
preserved as an uncitable draft, and the user must review its current hash. A
successful review completes the plan. Unknown execution failures may resume
once after the stale-running interval; `attempts` is capped at two by migration
20, and an exhausted plan becomes `failed` with a safe `errorCode`. Because a
filesystem write may predate a database failure, clients must check the target
folder before starting a new plan after such a failure. `orphanPath` identifies
an existing, non-symlink file at the plan's exact deterministic path. If its
contents still match the approved preview, `recoveryPath` also identifies it;
the original user may call `POST /ask/action-plans/{id}/reconcile` without a
body to attach it as an uncitable draft. If the file changed, `recoveryPath` is
`null`: show the current `GET /notes/{orphanPath}` content first, then send
`{"reviewed":true,"content_hash":"<current SHA-256>"}` to `/reconcile`.
The server rechecks the hash, does not overwrite the Markdown, and leaves the
file uncitable until a separate `/review-draft` call. Missing, symlinked,
already-released, or concurrently changed files return HTTP 409. Successful
reconciliation is audited without the note body. It requires the same signed-in
user, a browser session, and CSRF.
Vault scanning keeps the exact path of an interrupted or failed approved Ask
write as a draft even if another editor changed its contents; this does not
authorize automatic reconciliation or evidence release.
`GET /ask/action-plans/reviewable?limit=20&offset=0` pages through the signed-in
user's unreviewed saved drafts, with their current paths. `limit` accepts 1–100
and defaults to 20; ordering is newest first with ID as the tie-breaker. A new browser session for
that **same user** can retrieve a completed or partial plan and submit its review using
the current note content hash. This supports recovery after session expiry;
the list does not expose draft bodies or grant access to another user's plans.
`GET /ask/action-plans/failed?limit=20&offset=0` similarly lists only that
user's approved failed `create_note` plans (title, error code, timestamp and
optional `orphanPath`; no note body). This lets a later browser session reopen
the plan ID and inspect a possible saved file. An item with no `orphanPath`
still represents a failed operation, not a saved note.
An approved plan in `executing` state can be polled and resumed after a stale
execution; expiry applies to a new approval, not to recovery of an approval
already started. A path occupied by different content is never overwritten.

Proposing, approving, and cancelling a plan require the **same authenticated
browser session and CSRF token**. Reading a saved completed or partial plan allows a new
authenticated session for its original user; reviewing it additionally requires
CSRF and the exact current content hash. A service Bearer token alone cannot approve
or review a human action. The ordinary `POST /notes` route remains the trusted
server-to-server creation API. The action-plan catalog currently contains only
`create_note` in a fixed folder, optionally with a new named physical vault;
it does not create isolated vaults, edit
existing notes, change settings, or grant agents a general write capability.
The review acknowledgement marks the note as user-reviewed, **not factually
verified**. Broader action planning, auditable per-source review history, and
security tests for the declared shared-workspace boundary remain release gates
for 1.5.0. Per-user or per-vault isolation is **not** a feature of this contract.
The note editor also opens Ask beside the current note without unmounting the
editor. Its title is only prefilled into the question; unsaved text is not sent
to the model automatically.

## Job health and dashboard counts

`GET /api/v1/home/summary` reports lifetime job totals using SQL aggregates.
`stats.jobs.byStatus` contains the actual status/count mapping, including
superseded and cancelled work. The Home charts use this snapshot, not a
fabricated time series; note assimilation is coverage, not throughput.
The `createdToday`/`completedToday` counters use UTC day boundaries.
`recentlyCompleted` contains at most eight items; it is not the source of the
lifetime `progress.completed` count. Duration estimates use up to 200 recent
successful executions per required job type and remain unavailable when there
are no valid samples. These estimates are not processing-time guarantees.

### Notifications

`GET /api/v1/notifications?limit=20` returns `notifications` and `unreadCount`.
The limit is 1–200; the count covers **all unread notifications**, not just the
page or the number of alert categories. `GET /api/v1/notifications/summary`
returns only `{ "unreadCount": 7 }` for lightweight badge polling. Both follow
the existing API authentication rules. Opening Alerts does not mark items read.
`POST /api/v1/notifications/{id}/read` marks one item read;
`POST /api/v1/notifications/read-all` marks all existing items read, without
deleting the notification history. Failed reads must not clear client badges.

### Bounded autonomous job recovery

The claim path runs a deterministic supervisor after expired-lease recovery.
Expired leases finish the associated attempt with `lease_expired` diagnostics
(or cancellation), preserving the last execution stage rather than reporting
success. Worker graph expansion/inference calls use explicit 120-second request
limits instead of the generic 10-second client default; enrichment admission
uses 60 seconds. The graph-expansion whole-job deadline is at least 330 seconds
to cover expansion, enrichment, HippoRAG synchronization and final bookkeeping.
It scans at most 50 failed/dead-letter jobs per minute, newest first with a
rotating persisted cursor. It admits at most one recovery every five minutes
and defers admission while four or more jobs are pending/running. It extends
the **same job** by one attempt, at most three times, with minimum cooldowns
of 5 minutes, 30 minutes and 2 hours after the preceding failure. Existing IDs,
attempt history and errors are preserved. No worker means no recovery scan.

Only allowlisted ingestion/enrichment/judge/maintenance jobs with recognized
transient failures are eligible. Source hashes, semantic fingerprints and the
Judge timestamp/configuration version must still match. Missing or changed
sources are superseded; unverified sources, unknown errors, permanent provider
failures and cancelled jobs are not replayed. Destructive jobs and automatic
note creation are excluded. Idempotency keys prevent duplicate recovery;
maintenance supersession additionally requires a completed newer job covering
the same scope. A partial graph update cannot replace a failed global update.
Pending/running covering maintenance defers recovery without claiming success.

Serialized jobs expose `automaticRecovery` (`count`, `scheduledAt`) when
recovered. Automation logs record `AUTO_RECOVER_JOB` and `AUTO_SUPERSEDE_JOB`.
The existing settings API accepts `automatic_job_recovery_enabled=false` to
disable this supervisor. `internal_job_recovery_state` is its checkpoint, not
an application integration interface; do not edit it. Normal manual retry
remains available in Monitor. Historical notifications remain until marked read.

This is not unlimited self-healing: credentials, removed models, exhausted
quota and repeated failures still require operator attention. Recovery may
call the configured provider and incur its normal costs; it does not switch
models/providers or bulk-replay the failed backlog. AI subagents perform their
pipeline stages; the deterministic queue supervisor owns recovery decisions.

`GET /api/v1/jobs/health` treats a running job as stale when its lease expires.
The start-time threshold is used only for legacy jobs with no lease. Pending
work aged 30 minutes or more breaches the declared queue threshold; read
`slo.oldestPendingAgeSeconds` for the oldest pending age. These are operational
signals, not model-quality metrics.

In both views, active/running counts include jobs awaiting cancellation
acknowledgement. Failed counts include jobs that exhausted their attempts (`dead_letter`);
the separate `dead_letter` count is a subset, not an additional failure count.
The Home can finish current work while still showing historical failures.

Releases 1.4.9 and 1.4.10 use database schema 14. The in-progress 1.5 tree
targets schema 24: migration 21 adds Flow ownership and an evaluation lookup
index; migration 22 backfills blank canonical graph labels and indexes node
type plus canonical label for bounded upserts; migration 23 registers the default
vault and assigns stable vault IDs to notes while preserving old paths;
migration 24 records the owner/scope of persisted graph answers. These
changes preserve rows and
the HTTP API remains `/api/v1`. Older binaries enforce schema compatibility,
so an image-only rollback after migration is not sufficient. None of these
migrations has been applied to the active installation by this worktree.

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
