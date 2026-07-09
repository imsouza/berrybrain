import json
import shutil
import time
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

from sqlalchemy import text

from berrybrain_api.config import get_settings
from berrybrain_api.database import SessionLocal


def _backup_dir() -> Path:
    p = get_settings().backup_path
    p.mkdir(parents=True, exist_ok=True)
    return p


def _db_path() -> str:
    url = get_settings().database_url
    return (
        url.removeprefix("sqlite:///").split("?")[0]
        if url.startswith("sqlite:///")
        else url
    )


def list_backups() -> list[dict[str, object]]:
    backups: list[dict[str, object]] = []
    for entry in sorted(_backup_dir().iterdir(), reverse=True):
        if entry.is_dir() and entry.name.startswith("backup-"):
            backups.append(
                {
                    "id": entry.name,
                    "created_at": entry.name.removeprefix("backup-"),
                    "size_mb": round(
                        sum(f.stat().st_size for f in entry.glob("**/*") if f.is_file())
                        / (1024 * 1024),
                        1,
                    ),
                }
            )
    return backups[:50]


def create_backup() -> dict[str, object]:
    ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    _id = f"backup-{ts}"
    dest = _backup_dir() / _id
    dest.mkdir(parents=True)

    db = Path(_db_path())
    if db.exists():
        shutil.copy2(db, dest / db.name)

    vault = get_settings().vault_path
    if vault.exists():
        shutil.copytree(vault, dest / "vault", dirs_exist_ok=True)

    with SessionLocal() as session:
        meta = {
            "id": _id,
            "tables": {},
            "note_count": 0,
            "job_count": 0,
        }
        for table in ("notes", "jobs", "connections", "insights"):
            row = session.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
            meta["tables"][table] = row
        (dest / "metadata.json").write_text(json.dumps(meta))

    return {
        "id": _id,
        "path": str(dest),
        "metadata": meta,
    }


def restore_backup(backup_id: str) -> dict[str, object]:
    src = _backup_dir() / backup_id
    if not src.is_dir():
        raise FileNotFoundError(f"Backup {backup_id} not found")

    db = Path(_db_path())
    src_db = src / db.name
    if src_db.exists():
        shutil.copy2(src_db, db)

    vault = get_settings().vault_path
    src_vault = src / "vault"
    if src_vault.is_dir():
        for item in src_vault.iterdir():
            dest = vault / item.name
            if item.is_dir():
                shutil.copytree(item, dest, dirs_exist_ok=True)
            else:
                shutil.copy2(item, dest)

    return {"id": backup_id, "status": "restored"}


def delete_backup(backup_id: str) -> dict[str, object]:
    dest = _backup_dir() / backup_id
    if not dest.is_dir():
        raise FileNotFoundError(f"Backup {backup_id} not found")
    shutil.rmtree(dest)
    return {"status": "deleted", "id": backup_id}


def export_full() -> BytesIO:
    buf = BytesIO()
    with ZipFile(buf, "w") as zf:
        db = Path(_db_path())
        if db.exists():
            zf.write(db, db.name)

        vault = get_settings().vault_path
        for f in vault.glob("**/*.md"):
            rel = f.relative_to(vault)
            zf.write(f, f"vault/{rel}")

        t0 = time.time()
        backup = create_backup()
        zf.writestr(
            "backup_id.json",
            json.dumps({"id": backup["id"], "created_at": backup["metadata"]}),
        )

    buf.seek(0)
    return buf
