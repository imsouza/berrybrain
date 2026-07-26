from fastapi import APIRouter

from berrybrain_api.config import get_settings
from berrybrain_api.database import SessionLocal
from berrybrain_api.vault_graph_pipeline import diagnose_pipeline
from berrybrain_api.vault_graph_service import (
    scan_and_refresh_graph,
    scan_response_with_graph,
)

router = APIRouter(prefix="/api/v1/vault", tags=["vault"])
LEGACY_SCAN_STATUS = "scan+graph refreshed"
SCAN_AND_REBUILD_STATUS = "scan+rebuild completed"


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
