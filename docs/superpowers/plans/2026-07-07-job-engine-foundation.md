# Job Engine Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first reliable BerryBrain job queue so note changes create processable `PARSE_NOTE` jobs.

**Architecture:** Keep Markdown as source of truth and SQLite as automation state. Add a focused `jobs.py` application service around `JobRecord`, expose small API endpoints for workers, and keep the worker as an API client with no direct database access.

**Tech Stack:** FastAPI, SQLAlchemy, SQLite, Python `unittest`, Docker Compose.

---

## File Structure

- `apps/api/src/berrybrain_api/jobs.py`: job queue service functions, status transitions, serialization.
- `apps/api/src/berrybrain_api/main.py`: HTTP endpoints and note CRUD enqueue hooks.
- `apps/api/src/berrybrain_api/models.py`: reuse existing `JobRecord`.
- `apps/api/tests/test_jobs.py`: unit tests for queue behavior.
- `apps/worker/src/berrybrain_worker/main.py`: claim one pending job and complete `PARSE_NOTE`.

## Task 1: Job Service

**Files:**
- Create: `apps/api/src/berrybrain_api/jobs.py`
- Test: `apps/api/tests/test_jobs.py`

- [ ] **Step 1: Write failing tests**

```python
def test_create_and_claim_job_transitions_to_running():
    job = create_job(session, "PARSE_NOTE", {"note_path": "inbox/a.md"})
    claimed = claim_next_job(session)
    self.assertEqual(claimed.id, job.id)
    self.assertEqual(claimed.status, "running")
    self.assertEqual(claimed.attempts, 1)

def test_complete_and_fail_job_set_terminal_statuses():
    completed = complete_job(session, job.id)
    failed = fail_job(session, other.id, "boom")
```

- [ ] **Step 2: Verify RED**

Run: `rtk docker compose exec api sh -lc 'PYTHONPATH=/app/apps/api/src python -m unittest /app/apps/api/tests/test_jobs.py'`

Expected: fail because `berrybrain_api.jobs` does not exist.

- [ ] **Step 3: Implement minimal service**

```python
def create_job(session, job_type, payload):
    record = JobRecord(type=job_type, payload=compact_json(payload))
    session.add(record)
    session.commit()
    session.refresh(record)
    return record
```

- [ ] **Step 4: Verify GREEN**

Run: same unittest command. Expected: OK.

## Task 2: Enqueue Note Jobs From CRUD

**Files:**
- Modify: `apps/api/src/berrybrain_api/main.py`
- Modify: `apps/api/src/berrybrain_api/jobs.py`
- Test: `apps/api/tests/test_jobs.py`

- [ ] **Step 1: Add failing test**

```python
def test_enqueue_note_changed_job_uses_parse_note_payload():
    jobs = enqueue_note_changed_jobs(session, "inbox/a.md", "NOTE_UPDATED", "abc")
    self.assertEqual(jobs[0].type, "PARSE_NOTE")
    self.assertIn('"event_type":"NOTE_UPDATED"', jobs[0].payload)
```

- [ ] **Step 2: Verify RED**

Run: job unittest command. Expected: fail because `enqueue_note_changed_jobs` does not exist.

- [ ] **Step 3: Implement enqueue helper and call it after note create/update/delete**

```python
enqueue_note_changed_jobs(session, note_path, "NOTE_UPDATED", note["content_hash"])
```

- [ ] **Step 4: Verify GREEN**

Run: job unittest command. Expected: OK.

## Task 3: Worker API Endpoints

**Files:**
- Modify: `apps/api/src/berrybrain_api/main.py`

- [ ] **Step 1: Add endpoints**

```python
GET /api/v1/jobs
POST /api/v1/jobs/claim
POST /api/v1/jobs/{job_id}/complete
POST /api/v1/jobs/{job_id}/fail
```

- [ ] **Step 2: Smoke test endpoints**

Run:

```bash
rtk proxy curl -sS http://127.0.0.1:8000/api/v1/jobs
```

Expected: JSON object with `jobs`.

## Task 4: Worker Claim Loop Minimum

**Files:**
- Modify: `apps/worker/src/berrybrain_worker/main.py`

- [ ] **Step 1: Implement one-job run**

```python
job = await claim_next_job(client, settings.api_url)
if job and job["type"] == "PARSE_NOTE":
    await complete_job(client, settings.api_url, job["id"])
```

- [ ] **Step 2: Verify worker command**

Run:

```bash
rtk docker compose run --rm worker
```

Expected: worker connects to API and reports either no pending jobs or completed one `PARSE_NOTE` job.

## Self-Review

- Spec coverage: covers Etapa 6 base and prepares Etapa 7. Does not implement Ollama, embeddings, flashcards, review, insight or graph.
- Placeholder scan: no TODO/TBD placeholders.
- Type consistency: `JobRecord`, `PARSE_NOTE`, `pending`, `running`, `completed`, `failed` match current model.
