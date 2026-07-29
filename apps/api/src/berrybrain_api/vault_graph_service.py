from __future__ import annotations

from pathlib import Path
from typing import Any, TypedDict

from sqlalchemy.orm import Session

from berrybrain_api.second_brain import expand_knowledge_graph
from berrybrain_api.vault_scan import scan_vault


class VaultGraphRefreshResult(TypedDict):
    scan: dict[str, Any]
    graph: dict[str, Any]
    status: str


def scan_and_refresh_graph(
    session: Session, vault_path: Path, *, status: str
) -> VaultGraphRefreshResult:
    scan = scan_vault(session, vault_path)
    graph = expand_knowledge_graph(session)
    return {
        "scan": scan,
        "graph": graph,
        "status": status,
    }


def scan_response_with_graph(result: VaultGraphRefreshResult) -> dict[str, Any]:
    return {
        **result["scan"],
        "graph": result["graph"],
        "status": result["status"],
    }
