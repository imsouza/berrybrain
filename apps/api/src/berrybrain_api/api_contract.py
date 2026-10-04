"""Machine-readable integration contract shared with HTTP authentication."""

from typing import Annotated, Any

from fastapi import FastAPI, Query
from fastapi.openapi.utils import get_openapi
from fastapi.routing import APIRoute, iter_route_contexts
from pydantic import BaseModel, ConfigDict, Field

PUBLIC_OPERATIONS = frozenset(
    {
        ("GET", "/health"),
        ("GET", "/api/v1"),
        ("GET", "/openapi.json"),
        ("GET", "/api/v1/openapi.json"),
        ("GET", "/api/v1/docs"),
        ("GET", "/docs"),
        ("GET", "/docs/oauth2-redirect"),
        ("GET", "/redoc"),
        ("GET", "/api/v1/setup/status"),
        ("POST", "/api/v1/setup/admin"),
        ("POST", "/api/v1/auth/signup"),
        ("POST", "/api/v1/auth/login"),
        ("POST", "/api/v1/auth/verify-email"),
        ("POST", "/api/v1/auth/verify-2fa"),
        ("POST", "/api/v1/auth/password-reset/request"),
        ("POST", "/api/v1/auth/password-reset/confirm"),
    }
)
PageLimit = Annotated[int, Query(ge=1, le=200)]
SearchLimit = Annotated[int, Query(ge=1, le=100)]
Offset = Annotated[int, Query(ge=0)]


class NoteSummary(BaseModel):
    title: str
    path: str
    folder: str


class NotePage(BaseModel):
    notes: list[NoteSummary]
    total: int
    nextOffset: int | None


class NoteDocument(BaseModel):
    model_config = ConfigDict(extra="allow")
    title: str
    path: str
    content: str
    content_hash: str = Field(
        description="SHA-256 used as base_content_hash for updates."
    )
    links: list[str]
    frontmatter: dict[str, Any]
    id: int | None = None
    stableId: str | None = None
    sourceVersion: int | None = None


class SearchResult(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: int
    title: str
    path: str
    score: float
    source: str
    snippet: str = ""
    evidence: list[dict[str, Any]] = Field(default_factory=list)


class SearchResponse(BaseModel):
    results: list[SearchResult]


class GraphNode(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: str
    recordId: int
    stableId: str
    iri: str
    artifactVersion: int
    type: str
    label: str
    confidence: float | None


class GraphEdge(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: int
    stableId: str
    iri: str
    artifactVersion: int
    source: str
    target: str
    type: str
    confidence: float | None


class GraphNodePage(BaseModel):
    nodes: list[GraphNode]
    nextCursor: int | None
    graphVersion: int


class GraphEdgePage(BaseModel):
    edges: list[GraphEdge]
    nextCursor: int | None
    graphVersion: int


class GraphInference(BaseModel):
    model_config = ConfigDict(extra="allow")
    inferenceId: int
    status: str = Field(
        description="Inspect evidence and status; HTTP 200 alone does not mean a supported answer."
    )
    question: str
    answer: str
    evidence: list[Any]
    routes: list[str]
    relatedNodes: list[Any]
    suggestions: list[Any]
    confidence: float | None
    provider: str
    model: str
    insightId: int | None


def cookie_only_operation(path: str, method: str) -> bool:
    prefixes = (
        "/api/v1/auth/",
        "/api/v1/admin/",
        "/api/v1/security/service-tokens",
        "/api/v1/maintenance/",
        "/api/v1/backups",
        "/api/v1/settings/danger/",
    )
    return path.startswith(prefixes) or (method, path) in {
        ("POST", "/api/v1/judge/mode"),
        ("POST", "/api/v1/system/reset"),
    }


def install_openapi_contract(app: FastAPI, settings: Any) -> None:
    def openapi() -> dict[str, Any]:
        if app.openapi_schema is not None:
            return app.openapi_schema
        schema = get_openapi(
            title=app.title,
            version=app.version,
            routes=app.routes,
            description=(
                "BerryBrain architecture API v1. One owner-managed shared workspace. "
                "External server applications use a service Bearer token. Browser sessions "
                "require the CSRF cookie and X-CSRF-Token header for mutations. "
                "Note updates require base_content_hash; handle HTTP 409 before retrying. "
                "Knowledge generation is asynchronous; use note status and jobs to observe it."
            ),
        )
        schema["servers"] = [
            {"url": "/", "description": "API origin (or reverse-proxy mount)"}
        ]
        schema["components"]["securitySchemes"] = {
            "ServiceBearer": {
                "type": "http",
                "scheme": "bearer",
                "description": "Owner-issued service token; trusted server clients only.",
            },
            "BrowserSession": {
                "type": "apiKey",
                "in": "cookie",
                "name": settings.session_cookie_name,
            },
            "CSRFHeader": {
                "type": "apiKey",
                "in": "header",
                "name": "X-CSRF-Token",
                "description": "Must match the CSRF cookie bound to the session.",
            },
        }
        # Reuse real route dependencies: settings/AI/Judge administration is
        # deliberately not available to service tokens.
        owner_operations = {
            (method, route.path_format)
            for route in iter_route_contexts(app.routes)
            if isinstance(route.original_route, APIRoute)
            if any(
                getattr(dependency.call, "__name__", "")
                in {"require_admin", "_require_admin_csrf"}
                for dependency in route.dependant.dependencies
            )
            for method in route.methods
        }
        for path, item in schema["paths"].items():
            for method, operation in item.items():
                if method.upper() not in {
                    "GET",
                    "POST",
                    "PUT",
                    "PATCH",
                    "DELETE",
                    "HEAD",
                    "OPTIONS",
                }:
                    continue
                verb = method.upper()
                if (verb, path) in PUBLIC_OPERATIONS:
                    operation["security"] = []
                    continue
                browser: dict[str, list] = {"BrowserSession": []}
                if verb in {"POST", "PUT", "PATCH", "DELETE"}:
                    browser["CSRFHeader"] = []
                operation["security"] = (
                    [browser]
                    if cookie_only_operation(path, verb)
                    or (verb, path) in owner_operations
                    else [{"ServiceBearer": []}, browser]
                )
                for status, description in {
                    "401": "Authentication required or expired.",
                    "403": "Owner access, CSRF validation, or allowed origin required.",
                    "413": "Request exceeds the configured byte limit.",
                }.items():
                    operation.setdefault("responses", {}).setdefault(
                        status, {"description": description}
                    )
        app.openapi_schema = schema
        return schema

    app.openapi = openapi
