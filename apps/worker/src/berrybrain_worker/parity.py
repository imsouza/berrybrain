"""API/worker environment parity check.

Used by worker `main()` at startup (planning/fix-new-version.md §10).
Compares the worker's view of API_URL against the API's reported vault
path and DB path. If they diverge, prints a loud warning so a stale
worker never silently drains the wrong queue.
"""

from __future__ import annotations

from typing import Any

import httpx


async def check_api_parity(client: httpx.AsyncClient, api_url: str) -> dict[str, Any]:
    """Hit /api/v1/status and /api/v1/debug/vault-graph-pipeline, return
    a dict the worker can log. Returns `{"ok": False, ...}` on any error;
    the worker logs and continues — parity is informative, not blocking,
    by design (we cannot let a missing debug endpoint crash the worker
    on older deployments)."""

    out: dict[str, Any] = {"ok": True, "warnings": []}
    try:
        r = await client.get(f"{api_url}/api/v1/status", timeout=5)
        r.raise_for_status()
        out["status"] = r.json()
    except httpx.HTTPError as exc:
        out["ok"] = False
        out["warnings"].append(f"status unreachable: {exc}")
        return out

    try:
        r = await client.get(f"{api_url}/api/v1/debug/vault-graph-pipeline", timeout=5)
        r.raise_for_status()
        out["pipeline"] = r.json()
    except httpx.HTTPError as exc:
        out["warnings"].append(
            f"debug/pipeline endpoint missing: {exc}. "
            "Upgrade berrybrain_api to expose /api/v1/debug/vault-graph-pipeline."
        )

    diag_codes = {d["code"] for d in out.get("pipeline", {}).get("diagnostics", [])}
    if "DB_NOT_WRITABLE" in diag_codes:
        out["ok"] = False
    if "VAULT_MISSING" in diag_codes:
        out["ok"] = False
    return out
