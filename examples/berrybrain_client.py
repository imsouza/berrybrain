"""Small standard-library client for trusted external BerryBrain applications.

Set BERRYBRAIN_URL to the origin/mount (without /api/v1) and
BERRYBRAIN_SERVICE_TOKEN to an owner-issued credential. Running this module
only lists notes; it does not create notes or call a model.
"""

import json
import os
import time
from typing import Any
from urllib.error import HTTPError
from urllib.parse import quote, urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener


class APIError(RuntimeError):
    def __init__(self, status: int, detail: Any, correlation_id: str = ""):
        super().__init__(
            f"BerryBrain HTTP {status}; correlation={correlation_id or 'unavailable'}"
        )
        self.status = status
        self.detail = detail
        self.correlation_id = correlation_id


class NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # Do not leak a workspace token to another origin through a redirect.
        return None


class BerryBrainClient:
    def __init__(self, base_url: str, token: str, timeout: float = 30):
        parsed = urlsplit(base_url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise ValueError("A valid HTTP(S) BerryBrain origin/mount is required")
        if parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError(
                "Do not put credentials, queries, or fragments in the base URL"
            )
        if not token.strip():
            raise ValueError("A service token is required")
        self.api_url = base_url.rstrip("/") + "/api/v1"
        self.token = token.strip()
        self.timeout = timeout
        self.opener = build_opener(NoRedirects())

    def request(
        self,
        method: str,
        endpoint: str,
        *,
        payload=None,
        params=None,
        timeout=None,
        accept: str = "application/json",
    ):
        if (
            not endpoint.startswith("/")
            or endpoint.startswith("//")
            or ".." in endpoint.split("/")
        ):
            raise ValueError("Use an API-relative endpoint, without parent traversal")
        url = self.api_url + endpoint
        if params:
            clean_params = {k: v for k, v in params.items() if v is not None}
            if clean_params:
                url += "?" + urlencode(clean_params)
        headers = {
            "Authorization": "Bearer " + self.token,
            "Accept": accept,
        }
        data = None
        if payload is not None:
            headers["Content-Type"] = "application/json"
            data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request = Request(url, data=data, headers=headers, method=method)
        try:
            with self.opener.open(request, timeout=timeout or self.timeout) as response:
                body = response.read()
                if not body:
                    return None
                raw_headers = getattr(response, "headers", None)
                content_type = (
                    raw_headers.get("Content-Type", "")
                    if hasattr(raw_headers, "get")
                    else ""
                )
                if "text/turtle" in content_type or accept == "text/turtle":
                    return body.decode("utf-8")
                return json.loads(body)
        except HTTPError as error:
            try:
                detail = json.loads(error.read()).get("detail")
            except (ValueError, AttributeError):
                detail = "Non-JSON response"
            raise APIError(
                error.code, detail, error.headers.get("X-Correlation-ID", "")
            ) from None

    def list_vaults(self):
        return self.request("GET", "/vault/namespaces")

    def list_notes(self, *, limit: int = 50, offset: int = 0, vault_id: str | None = None):
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if vault_id is not None:
            params["vault_id"] = vault_id
        return self.request("GET", "/notes", params=params)

    def read_note(self, path: str):
        return self.request("GET", "/notes/" + quote(path, safe="/"))

    def create_note(
        self,
        title: str,
        content: str,
        folder: str = "inbox",
        *,
        vault_id: str | None = None,
    ):
        payload: dict[str, Any] = {
            "title": title,
            "content": content,
            "folder": folder,
        }
        if vault_id is not None:
            payload["vault_id"] = vault_id
        return self.request("POST", "/notes", payload=payload)

    def update_note(self, path: str, content: str, base_content_hash: str):
        # Never silently retry a conflicting update: the caller must merge/review.
        return self.request(
            "PUT",
            "/notes/" + quote(path, safe="/"),
            payload={"content": content, "base_content_hash": base_content_hash},
        )

    def note_status(self, path: str):
        return self.request("GET", "/notes/" + quote(path, safe="/") + "/status")

    def wait_until_ready(
        self,
        path: str,
        *,
        timeout_seconds: float = 90.0,
        poll_intervals: tuple[float, ...] = (2.0, 4.0, 8.0, 15.0),
    ):
        deadline = time.monotonic() + timeout_seconds
        step = 0
        last_status = None
        while True:
            last_status = self.note_status(path)
            if isinstance(last_status, dict) and (
                last_status.get("graphReady") is True
                or last_status.get("status") in {"completed", "ready", "failed"}
            ):
                return last_status
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return last_status
            delay = poll_intervals[min(step, len(poll_intervals) - 1)]
            time.sleep(min(delay, remaining))
            step += 1

    def search(self, query: str, limit: int = 10):
        return self.request("GET", "/search", params={"q": query, "limit": limit})

    def ask(self, question: str):
        # This operation can use the owner's configured (possibly paid) model.
        return self.request(
            "POST", "/graph/infer", payload={"question": question}, timeout=180
        )

    def inference_feedback(
        self, inference_id: int | str, action: str, correction: str = ""
    ):
        if action not in {"upvoted", "downvoted", "corrected"}:
            raise ValueError("action must be 'upvoted', 'downvoted', or 'corrected'")
        return self.request(
            "POST",
            f"/graph/inferences/{quote(str(inference_id), safe='')}/feedback",
            payload={"action": action, "correction": correction},
        )

    def graph_nodes(
        self,
        *,
        limit: int = 250,
        cursor: str | None = None,
        include_provisional: bool = False,
    ):
        return self.request(
            "GET",
            "/graph/nodes",
            params={
                "limit": limit,
                "cursor": cursor,
                "includeProvisional": "true" if include_provisional else "false",
            },
        )

    def graph_edges(
        self,
        *,
        limit: int = 500,
        cursor: str | None = None,
        compact: bool = True,
        include_provisional: bool = False,
    ):
        return self.request(
            "GET",
            "/graph/edges",
            params={
                "limit": limit,
                "cursor": cursor,
                "compact": "true" if compact else "false",
                "includeProvisional": "true" if include_provisional else "false",
            },
        )

    def graph_delta(self, since_version: int, *, include_provisional: bool = False):
        return self.request(
            "GET",
            "/graph/delta",
            params={
                "since_version": since_version,
                "includeProvisional": "true" if include_provisional else "false",
            },
        )

    def export_ontology(
        self, *, output_format: str = "json-ld", include_provisional: bool = False
    ):
        if output_format not in {"json-ld", "turtle"}:
            raise ValueError("output_format must be 'json-ld' or 'turtle'")
        accept = "application/ld+json" if output_format == "json-ld" else "text/turtle"
        return self.request(
            "GET",
            "/graph/ontology/export",
            params={
                "format": output_format,
                "includeProvisional": "true" if include_provisional else "false",
            },
            accept=accept,
        )

    def match_skills(self, query: str = "", *, task_type: str = "ask"):
        return self.request(
            "GET",
            "/ai/skills",
            params={"query": query, "task_type": task_type},
        )


if __name__ == "__main__":
    client = BerryBrainClient(
        os.environ["BERRYBRAIN_URL"], os.environ["BERRYBRAIN_SERVICE_TOKEN"]
    )
    print(json.dumps(client.list_notes(), indent=2, ensure_ascii=False))
