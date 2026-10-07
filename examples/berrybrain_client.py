"""Small standard-library client for trusted external BerryBrain applications.

Set BERRYBRAIN_URL to the origin/mount (without /api/v1) and
BERRYBRAIN_SERVICE_TOKEN to an owner-issued credential. Running this module
only lists notes; it does not create notes or call a model.
"""

import json
import os
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
        self, method: str, endpoint: str, *, payload=None, params=None, timeout=None
    ):
        if (
            not endpoint.startswith("/")
            or endpoint.startswith("//")
            or ".." in endpoint.split("/")
        ):
            raise ValueError("Use an API-relative endpoint, without parent traversal")
        url = self.api_url + endpoint
        if params:
            url += "?" + urlencode(params)
        headers = {
            "Authorization": "Bearer " + self.token,
            "Accept": "application/json",
        }
        data = None
        if payload is not None:
            headers["Content-Type"] = "application/json"
            data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request = Request(url, data=data, headers=headers, method=method)
        try:
            with self.opener.open(request, timeout=timeout or self.timeout) as response:
                body = response.read()
                return json.loads(body) if body else None
        except HTTPError as error:
            try:
                detail = json.loads(error.read()).get("detail")
            except (ValueError, AttributeError):
                detail = "Non-JSON response"
            raise APIError(
                error.code, detail, error.headers.get("X-Correlation-ID", "")
            ) from None

    def list_notes(self, *, limit=50, offset=0):
        return self.request("GET", "/notes", params={"limit": limit, "offset": offset})

    def read_note(self, path: str):
        return self.request("GET", "/notes/" + quote(path, safe="/"))

    def create_note(self, title: str, content: str, folder="inbox"):
        return self.request(
            "POST",
            "/notes",
            payload={"title": title, "content": content, "folder": folder},
        )

    def update_note(self, path: str, content: str, base_content_hash: str):
        # Never silently retry a conflicting update: the caller must merge/review.
        return self.request(
            "PUT",
            "/notes/" + quote(path, safe="/"),
            payload={"content": content, "base_content_hash": base_content_hash},
        )

    def note_status(self, path: str):
        return self.request("GET", "/notes/" + quote(path, safe="/") + "/status")

    def search(self, query: str, limit=10):
        return self.request("GET", "/search", params={"q": query, "limit": limit})

    def ask(self, question: str):
        # This operation can use the owner's configured (possibly paid) model.
        return self.request(
            "POST", "/graph/infer", payload={"question": question}, timeout=180
        )


if __name__ == "__main__":
    client = BerryBrainClient(
        os.environ["BERRYBRAIN_URL"], os.environ["BERRYBRAIN_SERVICE_TOKEN"]
    )
    print(json.dumps(client.list_notes(), indent=2, ensure_ascii=False))
