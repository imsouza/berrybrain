from fastapi import APIRouter

from berrybrain_api.backup import (
    create_backup,
    delete_backup,
    export_full,
    list_backups,
    restore_backup,
)

router = APIRouter(prefix="/api/v1/backups", tags=["backups"])


@router.get("")
def get_backups() -> dict:
    return {"backups": list_backups()}


@router.post("", status_code=201)
def create_backup_endpoint() -> dict:
    return {"backup": create_backup()}


@router.delete("/{backup_id}")
def delete_backup_endpoint(backup_id: str) -> dict:
    return delete_backup(backup_id)


@router.post("/{backup_id}/restore")
def restore_backup_endpoint(backup_id: str) -> dict:
    restore_backup(backup_id)
    return {"status": "restored"}


@router.get("/export")
def export_backup():
    return export_full()
