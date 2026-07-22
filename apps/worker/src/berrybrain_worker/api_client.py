from __future__ import annotations

import asyncio

import httpx

_claim_tokens: dict[int, str] = {}


class JobCancellationRequested(Exception):
    pass


async def assert_api_ready(client: httpx.AsyncClient, api_url: str) -> None:
    last_error = None
    for attempt in range(30):
        try:
            response = await client.get(f"{api_url}/health")
            response.raise_for_status()
            print(f"API ready: {api_url}")
            return
        except httpx.HTTPError as exc:
            last_error = exc
            await asyncio.sleep(min(2 + attempt // 5, 8))
    raise RuntimeError(f"API not ready at {api_url}: {last_error}")


async def claim_next_job(client: httpx.AsyncClient, api_url: str) -> dict | None:
    response = await client.post(f"{api_url}/api/v1/jobs/claim")
    response.raise_for_status()
    payload = response.json()
    job = payload.get("job")
    if job:
        token = str(job.get("claim_token") or "")
        if token:
            _claim_tokens[int(job["id"])] = token
    return job


def _claim_headers(job_id: int) -> dict[str, str]:
    token = _claim_tokens.get(job_id, "")
    return {"X-BerryBrain-Claim-Token": token} if token else {}


async def renew_job_lease(client: httpx.AsyncClient, api_url: str, job_id: int) -> None:
    response = await client.post(
        f"{api_url}/api/v1/jobs/{job_id}/renew-lease",
        headers=_claim_headers(job_id),
    )
    response.raise_for_status()


async def renew_lease_until_done(
    client: httpx.AsyncClient, api_url: str, job_id: int
) -> None:
    try:
        while True:
            await asyncio.sleep(60)
            await renew_job_lease(client, api_url, job_id)
    except asyncio.CancelledError:
        return
    except Exception as exc:
        print(f"could not renew lease for job {job_id}: {exc}")


async def fetch_note(client: httpx.AsyncClient, api_url: str, note_path: str) -> dict:
    encoded = "/".join(part for part in note_path.split("/"))
    response = await client.get(f"{api_url}/api/v1/notes/{encoded}")
    response.raise_for_status()
    return response.json()


async def upsert_metadata(
    client: httpx.AsyncClient,
    api_url: str,
    note_path: str,
    generation_type: str,
    content: dict,
    content_hash: str,
    model_used: str,
) -> None:
    encoded = "/".join(part for part in note_path.split("/"))
    response = await client.put(
        f"{api_url}/api/v1/metadata/{generation_type}?note_path={encoded}",
        json={
            "content": content,
            "content_hash": content_hash,
            "model_used": model_used,
        },
    )
    response.raise_for_status()


async def complete_job(client: httpx.AsyncClient, api_url: str, job_id: int) -> None:
    response = await client.post(
        f"{api_url}/api/v1/jobs/{job_id}/complete",
        headers=_claim_headers(job_id),
    )
    if response.status_code == 409:
        try:
            detail = str(response.json().get("detail", ""))
        except ValueError:
            detail = ""
        if "cancellation" in detail.lower():
            raise JobCancellationRequested(detail)
    response.raise_for_status()
    _claim_tokens.pop(job_id, None)


async def is_job_cancellation_requested(
    client: httpx.AsyncClient, api_url: str, job_id: int
) -> bool:
    response = await client.get(f"{api_url}/api/v1/jobs/{job_id}/cancellation")
    response.raise_for_status()
    return bool(response.json().get("cancelRequested", False))


async def acknowledge_job_cancellation(
    client: httpx.AsyncClient, api_url: str, job_id: int
) -> None:
    response = await client.post(
        f"{api_url}/api/v1/jobs/{job_id}/cancelled",
        headers=_claim_headers(job_id),
    )
    response.raise_for_status()
    _claim_tokens.pop(job_id, None)


async def fail_job(
    client: httpx.AsyncClient,
    api_url: str,
    job_id: int,
    error_message: str,
) -> None:
    response = await client.post(
        f"{api_url}/api/v1/jobs/{job_id}/fail",
        json={"error_message": error_message},
        headers=_claim_headers(job_id),
    )
    response.raise_for_status()
    _claim_tokens.pop(job_id, None)


async def send_heartbeat(
    client: httpx.AsyncClient,
    api_url: str,
    jobs_processed: int,
    errors: int,
    ollama_healthy: bool = False,
) -> None:
    try:
        await client.post(
            f"{api_url}/api/v1/worker/heartbeat",
            json={
                "jobs_processed": jobs_processed,
                "errors": errors,
                "ollama_healthy": ollama_healthy,
            },
        )
    except Exception:
        pass
