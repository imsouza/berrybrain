"""Stage a recoverable backup while an older BerryBrain API is still running.

Run inside the active API container. This wrapper leaves the installed package
unchanged and refuses paths that differ from the container's configured paths.
The regular backup implementation supplies the vault/database locks, metadata,
portable export, and manifest; this wrapper adds staging and uses one SQLite
backup step so concurrent writes cannot repeatedly restart a multi-step copy.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sqlite3
from contextlib import closing
from pathlib import Path
from uuid import uuid4

from berrybrain_api import backup


def _snapshot_one_pass(
    source: Path, destination: Path, *, timeout_seconds: float | None = None
) -> None:
    # Keep the optional keyword for compatibility with either installed API.
    # A segmented deadline mode would restart under the active write workload.
    destination.parent.mkdir(parents=True, exist_ok=True)
    with (
        closing(
            sqlite3.connect(source.resolve().as_uri() + "?mode=ro", uri=True)
        ) as source_db,
        closing(sqlite3.connect(destination)) as dest_db,
    ):
        source_db.backup(dest_db, pages=-1)


def _assert_paths(database: Path, vault: Path, backups: Path) -> None:
    settings = backup.get_settings()
    actual = (
        Path(backup._db_path()).resolve(),
        settings.vault_path.resolve(),
        settings.backup_path.resolve(),
    )
    expected = (database.resolve(), vault.resolve(), backups.resolve())
    if actual != expected:
        raise ValueError(
            "Configured database, vault, or backup path differs from preflight"
        )
    if not database.is_file() or not vault.is_dir() or not backups.is_dir():
        raise ValueError("Expected database, vault, and backup directory must exist")


def create_preflight_backup(database: Path, vault: Path, backups: Path) -> dict:
    _assert_paths(database, vault, backups)
    staging_root = backups / f".v15-preflight-{uuid4().hex}.incomplete"
    staging_root.mkdir(mode=0o700)
    original_backup_dir = backup._backup_dir
    original_copy = backup._copy_sqlite_snapshot
    backup._backup_dir = lambda: staging_root
    backup._copy_sqlite_snapshot = _snapshot_one_pass
    try:
        result = backup.create_backup()
        backup_id = str(result["id"])
        source = staging_root / backup_id
        published = backups / backup_id
        if source != Path(result["path"]) or published.exists():
            raise RuntimeError("Unexpected backup path or existing backup ID")
        verification = backup._verify_manifest(source)
        if verification.get("status") != "verified":
            raise RuntimeError("Backup manifest was not verified")
        source.chmod(0o700)
        with closing(
            sqlite3.connect(f"file:{source / database.name}?mode=ro", uri=True)
        ) as db:
            if db.execute("PRAGMA quick_check").fetchone()[0] != "ok":
                raise RuntimeError("Snapshot SQLite quick_check failed")
            if db.execute("PRAGMA foreign_key_check").fetchone() is not None:
                raise RuntimeError("Snapshot SQLite foreign_key_check failed")
            schema = db.execute(
                "SELECT max(version) FROM schema_migrations"
            ).fetchone()[0]
            notes = db.execute("SELECT count(*) FROM notes").fetchone()[0]
        summary = {
            "id": backup_id,
            "schema": schema,
            "notes": notes,
            "verifiedFiles": verification["checkedFiles"],
        }
        os.replace(source, published)
        shutil.rmtree(staging_root, ignore_errors=True)
        return summary
    except BaseException:
        shutil.rmtree(staging_root, ignore_errors=True)
        raise
    finally:
        backup._backup_dir = original_backup_dir
        backup._copy_sqlite_snapshot = original_copy


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--vault", type=Path, required=True)
    parser.add_argument("--backups", type=Path, required=True)
    args = parser.parse_args()
    print(
        json.dumps(create_preflight_backup(args.database, args.vault, args.backups)),
        flush=True,
    )


if __name__ == "__main__":
    main()
