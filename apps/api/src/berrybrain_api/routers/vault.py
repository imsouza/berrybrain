from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import select

from berrybrain_api.config import get_settings
from berrybrain_api.database import SessionLocal
from berrybrain_api.models import VaultRecord
from berrybrain_api.vault_graph_pipeline import diagnose_pipeline
from berrybrain_api.vault_graph_service import (
    scan_and_refresh_graph,
    scan_response_with_graph,
)

router = APIRouter(prefix="/api/v1/vault", tags=["vault"])
LEGACY_SCAN_STATUS = "scan+graph refreshed"
SCAN_AND_REBUILD_STATUS = "scan+rebuild completed"


class VaultNamespace(BaseModel):
    id: str
    name: str
    path: str
    kind: Literal["shared_physical_namespace"]


class VaultNamespaceList(BaseModel):
    workspaceModel: Literal["shared"]
    vaults: list[VaultNamespace]


@router.get("/namespaces", response_model=VaultNamespaceList)
def list_vault_namespaces() -> dict:
    """Physical namespaces, not separate users or access-control domains."""
    with SessionLocal() as session:
        vaults = session.scalars(select(VaultRecord).order_by(VaultRecord.created_at)).all()
        result = [
            {
                "id": item.id,
                "name": item.name,
                "path": item.path,
                "kind": "shared_physical_namespace",
            }
            for item in vaults
        ]
    if not any(item["id"] == "default" for item in result):
        result.insert(
            0,
            {"id": "default", "name": "Default", "path": "", "kind": "shared_physical_namespace"},
        )
    return {"workspaceModel": "shared", "vaults": result}


@router.post("/scan")
def scan_vault() -> dict:
    settings = get_settings()
    with SessionLocal() as session:
        result = scan_and_refresh_graph(
            session, settings.vault_path, status=LEGACY_SCAN_STATUS
        )
        return scan_response_with_graph(result)


@router.post("/scan-and-rebuild")
def scan_and_rebuild_graph() -> dict:
    settings = get_settings()
    with SessionLocal() as session:
        return scan_and_refresh_graph(
            session, settings.vault_path, status=SCAN_AND_REBUILD_STATUS
        )


@router.get("/debug/vault-graph-pipeline")
def debug_vault_graph_pipeline() -> dict:
    settings = get_settings()
    diag = diagnose_pipeline(settings.vault_path)
    return diag.to_dict()
