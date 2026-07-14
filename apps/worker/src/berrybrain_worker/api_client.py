from __future__ import annotations

import asyncio

import httpx


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
    return payload.get("job")


async def renew_job_lease(client: httpx.AsyncClient, api_url: str, job_id: int) -> None:
    response = await client.post(f"{api_url}/api/v1/jobs/{job_id}/renew-lease")
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
    response = await client.post(f"{api_url}/api/v1/jobs/{job_id}/complete")
    response.raise_for_status()


async def fail_job(
    client: httpx.AsyncClient,
    api_url: str,
    job_id: int,
    error_message: str,
) -> None:
    response = await client.post(
        f"{api_url}/api/v1/jobs/{job_id}/fail",
        json={"error_message": error_message},
    )
    response.raise_for_status()


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
