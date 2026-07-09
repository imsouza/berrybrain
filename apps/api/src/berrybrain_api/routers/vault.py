from fastapi import APIRouter

from berrybrain_api.config import get_settings
from berrybrain_api.database import SessionLocal
from berrybrain_api.vault_scan import scan_vault as do_scan

router = APIRouter(prefix="/api/v1/vault", tags=["vault"])


@router.post("/scan")
def scan_vault() -> dict:
    settings = get_settings()
    with SessionLocal() as session:
        return do_scan(session, settings.vault_path)
