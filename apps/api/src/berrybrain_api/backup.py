import hashlib
import json
import os
import shutil
import sqlite3
import tempfile
from contextlib import closing
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path
from uuid import uuid4
from xml.etree import ElementTree
from zipfile import ZipFile

from fastapi import HTTPException
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session
from sqlalchemy.pool import NullPool

from berrybrain_api import __version__
from berrybrain_api.config import get_settings
from berrybrain_api.database import (
    Base,
    SessionLocal,
    ensure_sqlite_columns,
)
from berrybrain_api.database import (
    engine as database_engine,
)
from berrybrain_api.filesystem import serialized_vault, vault_lock
from berrybrain_api.models import (
    AttachmentExtractionRecord,
    NoteAttachmentRecord,
    SettingRecord,
)
from berrybrain_api.runtime_guard import database_lease, exclusive_database_access
from berrybrain_api.schema_migrations import (
    CURRENT_SCHEMA_VERSION,
    apply_schema_migrations,
    get_schema_version,
)


def _resolve_backup_path(backup_id: str) -> Path:
    # ponytail: backups live directly under backup_dir; reject traversal/separators.
    if (
        not backup_id
        or "/" in backup_id
        or "\\" in backup_id
        or not backup_id.startswith("backup-")
    ):
        raise HTTPException(status_code=400, detail="Invalid backup id")
    root = _backup_dir().resolve()
    dest = (root / backup_id).resolve()
    if dest != root and not str(dest).startswith(str(root) + os.sep):
        raise HTTPException(status_code=400, detail="Invalid backup id")
    return dest


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


def _copy_sqlite_snapshot(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with (
        closing(sqlite3.connect(source)) as source_db,
        closing(sqlite3.connect(destination)) as dest_db,
    ):
        source_db.backup(dest_db)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _create_manifest(root: Path) -> dict[str, object]:
    files = []
    for path in sorted(root.glob("**/*")):
        if not path.is_file() or path.name == "manifest.json" or path.is_symlink():
            continue
        files.append(
            {
                "path": path.relative_to(root).as_posix(),
                "sizeBytes": path.stat().st_size,
                "sha256": _sha256_file(path),
            }
        )
    return {
        "format": "berrybrain-backup-manifest.v1",
        "createdAt": datetime.now(UTC).isoformat(),
        "files": files,
    }


def _verify_manifest(root: Path) -> dict[str, object]:
    path = root / "manifest.json"
    if not path.exists():
        return {
            "status": "legacy_unverified",
            "checkedFiles": 0,
            "warning": "This backup predates checksum manifests.",
        }
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Backup manifest is invalid: {exc}") from exc
    files = manifest.get("files", [])
    if not isinstance(files, list):
        raise ValueError("Backup manifest file list is invalid")
    checked = 0
    for item in files:
        if not isinstance(item, dict):
            raise ValueError("Backup manifest entry is invalid")
        relative = Path(str(item.get("path", "")))
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("Backup manifest contains an unsafe path")
        candidate = (root / relative).resolve()
        if root.resolve() not in candidate.parents or not candidate.is_file():
            raise ValueError(f"Backup file is missing: {relative.as_posix()}")
        expected_size = int(item.get("sizeBytes", -1))
        expected_checksum = str(item.get("sha256", ""))
        if candidate.stat().st_size != expected_size:
            raise ValueError(f"Backup file size mismatch: {relative.as_posix()}")
        if _sha256_file(candidate) != expected_checksum:
            raise ValueError(f"Backup checksum mismatch: {relative.as_posix()}")
        checked += 1
    return {"status": "verified", "checkedFiles": checked}


def _read_backup_metadata(root: Path) -> dict[str, object]:
    path = root / "metadata.json"
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Backup metadata is invalid: {exc}") from exc
    return value if isinstance(value, dict) else {}


def _is_sensitive_setting(key: str) -> bool:
    normalized = key.lower()
    return any(
        marker in normalized
        for marker in ("api_key", "password", "secret", "token", "credential")
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


@serialized_vault
def create_backup() -> dict[str, object]:
    ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    _id = f"backup-{ts}-{uuid4().hex[:8]}"
    dest = _backup_dir() / _id
    dest.mkdir(parents=True)

    db = Path(_db_path())
    if db.exists():
        with database_lease(db):
            _copy_sqlite_snapshot(db, dest / db.name)

    vault = get_settings().vault_path
    if vault.exists():
        shutil.copytree(
            vault,
            dest / "vault",
            dirs_exist_ok=True,
            ignore=shutil.ignore_patterns(".berrybrain-restore", ".berrybrain-write-*"),
        )

    snapshot_engine = (
        create_engine(f"sqlite:///{dest / db.name}", poolclass=NullPool)
        if (dest / db.name).exists()
        else None
    )
    with (
        Session(snapshot_engine)
        if snapshot_engine is not None
        else SessionLocal() as session
    ):
        meta = {
            "id": _id,
            "createdAt": datetime.now(UTC).isoformat(),
            "berryBrainVersion": __version__,
            "schemaVersion": get_schema_version(session.get_bind()),
            "tables": {},
            "note_count": 0,
            "job_count": 0,
            "settings": {},
            "omittedSensitiveSettings": [],
            "embeddingModels": [],
        }
        for table in (
            "notes",
            "jobs",
            "connections",
            "insights",
            "concepts",
            "chunks",
            "embeddings",
            "graph_nodes",
            "graph_edges",
            "service_tokens",
            "note_attachments",
            "attachment_extractions",
        ):
            row = session.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
            meta["tables"][table] = row
        meta["note_count"] = int(meta["tables"].get("notes", 0) or 0)
        meta["job_count"] = int(meta["tables"].get("jobs", 0) or 0)
        for setting in session.execute(select(SettingRecord)).scalars():
            if _is_sensitive_setting(setting.key):
                meta["omittedSensitiveSettings"].append(setting.key)
            else:
                meta["settings"][setting.key] = setting.value
        if "embeddings" in meta["tables"]:
            meta["embeddingModels"] = [
                {"provider": row[0] or "", "model": row[1] or ""}
                for row in session.execute(
                    text(
                        "SELECT DISTINCT provider, model FROM embeddings "
                        "WHERE model != '' ORDER BY provider, model"
                    )
                )
            ]
        (dest / "metadata.json").write_text(
            json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        _write_portable_metadata_directory(dest / "portable", session)
    manifest = _create_manifest(dest)
    (dest / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    return {
        "id": _id,
        "path": str(dest),
        "metadata": meta,
    }


def restore_backup(backup_id: str) -> dict[str, object]:
    src = _resolve_backup_path(backup_id)
    if not src.is_dir():
        raise FileNotFoundError(f"Backup {backup_id} not found")

    verification = _verify_manifest(src)
    metadata = _read_backup_metadata(src)
    backup_schema = int(metadata.get("schemaVersion", 0) or 0)
    if backup_schema > CURRENT_SCHEMA_VERSION:
        raise ValueError(
            "Backup schema is newer than this BerryBrain build "
            f"({backup_schema} > {CURRENT_SCHEMA_VERSION})"
        )

    db = Path(_db_path())
    src_db = src / db.name
    restore_id = uuid4().hex
    staged_db: Path | None = None
    staged_vault: Path | None = None
    migration = {
        "fromVersion": backup_schema,
        "toVersion": backup_schema,
        "applied": [],
    }
    if src_db.exists():
        db.parent.mkdir(parents=True, exist_ok=True)
        staged_db = db.with_name(f".{db.name}.restore-{restore_id}")
        shutil.copy2(src_db, staged_db)
        try:
            restore_engine = create_engine(
                f"sqlite:///{staged_db}", connect_args={"check_same_thread": False}
            )
            try:
                actual_schema = get_schema_version(restore_engine)
                if actual_schema != backup_schema:
                    raise ValueError(
                        "Backup schema metadata does not match its database "
                        f"({backup_schema} != {actual_schema})"
                    )
                Base.metadata.create_all(bind=restore_engine)
                ensure_sqlite_columns(restore_engine)
                migration = apply_schema_migrations(restore_engine)
                with restore_engine.connect() as connection:
                    integrity = connection.execute(
                        text("PRAGMA integrity_check")
                    ).scalar()
                if str(integrity).lower() != "ok":
                    raise ValueError(
                        f"Restored database failed integrity check: {integrity}"
                    )
            finally:
                restore_engine.dispose()
        except Exception:
            _remove_restore_path(staged_db)
            raise

    vault = get_settings().vault_path
    src_vault = src / "vault"
    restored_files = 0
    if src_vault.is_dir():
        vault.parent.mkdir(parents=True, exist_ok=True)
        staged_vault = vault.parent / f".{vault.name}.restore-{restore_id}"
        try:
            shutil.copytree(src_vault, staged_vault)
        except Exception:
            _remove_restore_path(staged_db)
            _remove_restore_path(staged_vault)
            raise
        restored_files = sum(1 for item in src_vault.glob("**/*") if item.is_file())

    try:
        _commit_prepared_restore(
            database_path=db,
            staged_database=staged_db,
            vault_path=vault,
            staged_vault=staged_vault,
            restore_id=restore_id,
        )
    finally:
        _remove_restore_path(staged_db)
        _remove_restore_path(staged_vault)

    return {
        "id": backup_id,
        "status": "restored",
        "verification": verification,
        "schemaVersion": backup_schema,
        "migration": migration,
        "restoredFiles": restored_files,
        "tables": metadata.get("tables", {}),
    }


def _commit_prepared_restore(
    *,
    database_path: Path,
    staged_database: Path | None,
    vault_path: Path,
    staged_vault: Path | None,
    restore_id: str,
) -> None:
    database_path.parent.mkdir(parents=True, exist_ok=True)
    with exclusive_database_access(database_path), vault_lock(vault_path):
        from berrybrain_api.runtime_guard import restore_marker

        if restore_marker(database_path).exists():
            raise RuntimeError(
                "An interrupted restore requires recovery; no changes made."
            )
        _commit_restore_contents(
            database_path=database_path,
            staged_database=staged_database,
            vault_path=vault_path,
            staged_vault=staged_vault,
            restore_id=restore_id,
        )


def _commit_restore_contents(
    *,
    database_path: Path,
    staged_database: Path | None,
    vault_path: Path,
    staged_vault: Path | None,
    restore_id: str,
) -> None:
    rollback_database = database_path.with_name(
        f".{database_path.name}.rollback-{restore_id}"
    )
    vault_path.mkdir(parents=True, exist_ok=True)
    workspace_root = vault_path / ".berrybrain-restore"
    if workspace_root.is_symlink():
        raise ValueError("Restore workspace cannot be a symlink")
    workspace_root.mkdir(exist_ok=True)
    workspace = Path(tempfile.mkdtemp(prefix="restore-", dir=workspace_root))
    rollback_vault = workspace / "previous"
    incoming_vault = workspace / "incoming"
    rollback_vault.mkdir()
    old_entries: list[str] = []
    installed_entries: list[str] = []
    database_replaced = False
    from berrybrain_api.filesystem import atomic_write_text
    from berrybrain_api.runtime_guard import restore_marker

    marker = restore_marker(database_path)
    _dispose_database_engines()
    try:
        if staged_database is not None and database_path.exists():
            _copy_sqlite_snapshot(database_path, rollback_database)
        if staged_vault is not None:
            shutil.copytree(
                staged_vault,
                incoming_vault,
                ignore=shutil.ignore_patterns(".berrybrain-restore"),
            )
        atomic_write_text(
            marker,
            json.dumps(
                {
                    "phase": "prepared",
                    "database": str(database_path),
                    "rollbackDatabase": str(rollback_database),
                    "workspace": str(workspace),
                    "vault": str(vault_path),
                    "oldEntries": [
                        entry.name
                        for entry in vault_path.iterdir()
                        if entry != workspace_root
                    ],
                    "incomingEntries": [
                        entry.name for entry in incoming_vault.iterdir()
                    ]
                    if incoming_vault.exists()
                    else [],
                }
            ),
        )
        if staged_vault is not None:
            for entry in list(vault_path.iterdir()):
                if entry == workspace_root:
                    continue
                os.replace(entry, rollback_vault / entry.name)
                old_entries.append(entry.name)
            for entry in list(incoming_vault.iterdir()):
                os.replace(entry, vault_path / entry.name)
                installed_entries.append(entry.name)
        if staged_database is not None:
            # SQLite backup replaces contents transactionally without swapping an
            # inode still known to idle pools in another API process, or leaving
            # an unrelated WAL beside a replaced file.
            _copy_sqlite_snapshot(staged_database, database_path)
            database_replaced = True
    except Exception:
        try:
            if database_replaced:
                if rollback_database.exists():
                    _copy_sqlite_snapshot(rollback_database, database_path)
                else:
                    database_path.unlink(missing_ok=True)
            for name in reversed(installed_entries):
                _remove_restore_path(vault_path / name)
            for name in reversed(old_entries):
                os.replace(rollback_vault / name, vault_path / name)
        except Exception as rollback_error:
            # Keep the only recovery copies; never delete them after failed rollback.
            raise RuntimeError(
                f"Restore rollback incomplete; recovery copies retained at {workspace} and {rollback_database}"
            ) from rollback_error
        else:
            _remove_restore_path(rollback_database)
            _remove_restore_path(workspace)
            marker.unlink(missing_ok=True)
        raise
    else:
        atomic_write_text(
            marker,
            json.dumps(
                {
                    "phase": "committed",
                    "database": str(database_path),
                    "rollbackDatabase": str(rollback_database),
                    "workspace": str(workspace),
                    "vault": str(vault_path),
                }
            ),
        )
        _remove_restore_path(rollback_database)
        _remove_restore_path(workspace)
        marker.unlink(missing_ok=True)
    finally:
        _dispose_database_engines()


def _dispose_database_engines() -> None:
    engines = [database_engine, SessionLocal.kw.get("bind")]
    disposed: set[int] = set()
    for bound_engine in engines:
        if bound_engine is None or id(bound_engine) in disposed:
            continue
        bound_engine.dispose()
        disposed.add(id(bound_engine))


def _remove_restore_path(path: Path | None) -> None:
    if path is None or (not path.exists() and not path.is_symlink()):
        return
    if path.is_symlink():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()


def delete_backup(backup_id: str) -> dict[str, object]:
    dest = _resolve_backup_path(backup_id)
    if not dest.is_dir():
        raise FileNotFoundError(f"Backup {backup_id} not found")
    shutil.rmtree(dest)
    return {"status": "deleted", "id": backup_id}


def export_full() -> BytesIO:
    # Export one retained snapshot, not a live DB file followed by a different backup.
    backup = create_backup()
    snapshot_root = Path(str(backup["path"]))
    buf = BytesIO()
    with ZipFile(buf, "w") as zf:
        db = snapshot_root / Path(_db_path()).name
        if db.exists():
            zf.write(db, db.name)

        vault = snapshot_root / "vault"
        if vault.exists():
            for file_path in vault.glob("**/*"):
                if not file_path.is_file() or file_path.is_symlink():
                    continue
                rel = file_path.relative_to(vault)
                zf.write(file_path, f"vault/{rel}")

        snapshot_engine = create_engine(f"sqlite:///{db}", poolclass=NullPool)
        with Session(snapshot_engine) as session:
            attachments = list(session.execute(select(NoteAttachmentRecord)).scalars())
            extractions = {
                item.attachment_id: item
                for item in session.execute(
                    select(AttachmentExtractionRecord)
                ).scalars()
            }
            manifest = [
                _serialize_attachment_export(item, extractions.get(item.id))
                for item in attachments
            ]
            portable = _portable_metadata_payloads(session)
        zf.writestr(
            "metadata/attachments.json",
            json.dumps(manifest, ensure_ascii=False, indent=2),
        )
        for relative_path, content in portable.items():
            zf.writestr(f"portable/{relative_path}", content)

        zf.writestr(
            "backup_id.json",
            json.dumps({"id": backup["id"], "created_at": backup["metadata"]}),
        )

    buf.seek(0)
    return buf


def _serialize_attachment_export(
    attachment: NoteAttachmentRecord,
    extraction: AttachmentExtractionRecord | None,
) -> dict[str, object]:
    return {
        "id": attachment.id,
        "noteId": attachment.note_id,
        "notePath": attachment.note_path,
        "filename": attachment.filename,
        "storedPath": attachment.stored_path,
        "mimeType": attachment.mime_type,
        "declaredMimeType": attachment.declared_mime_type,
        "checksum": attachment.checksum,
        "validationStatus": attachment.validation_status,
        "category": attachment.category,
        "sizeBytes": attachment.size_bytes,
        "createdAt": attachment.created_at.isoformat()
        if attachment.created_at
        else None,
        "extraction": {
            "status": extraction.status,
            "language": extraction.language,
            "provider": extraction.provider,
            "model": extraction.model,
            "confidence": extraction.confidence,
            "stage": extraction.stage,
            "progress": extraction.progress,
            "extractor": extraction.extractor,
            "locationMetadata": _json_object(extraction.location_metadata),
            "updatedAt": extraction.updated_at.isoformat()
            if extraction.updated_at
            else None,
        }
        if extraction
        else None,
    }


def _json_object(raw: str) -> dict[str, object]:
    try:
        value = json.loads(raw or "{}")
    except (json.JSONDecodeError, TypeError):
        return {}
    return value if isinstance(value, dict) else {}


PORTABLE_TABLES = (
    "insights",
    "concepts",
    "jobs",
    "connections",
    "graph_nodes",
    "graph_edges",
    "graph_feedback",
    "learning_events",
    "attachment_extractions",
    "model_invocations",
)


def _portable_metadata_payloads(session) -> dict[str, str]:
    payloads: dict[str, str] = {}
    for table_name in PORTABLE_TABLES:
        rows = session.execute(
            text(f"SELECT * FROM {table_name} ORDER BY id")
        ).mappings()
        payloads[f"{table_name}.jsonl"] = "\n".join(
            json.dumps(dict(row), ensure_ascii=False, default=_json_default)
            for row in rows
        )
    settings_rows = session.execute(
        text("SELECT key, value, updated_at FROM settings ORDER BY key")
    ).mappings()
    safe_settings = [
        dict(row) for row in settings_rows if not _is_sensitive_setting(str(row["key"]))
    ]
    payloads["settings.json"] = json.dumps(
        safe_settings, ensure_ascii=False, indent=2, default=_json_default
    )
    payloads["knowledge-graph.graphml"] = _graphml(session)
    return payloads


def _write_portable_metadata_directory(path: Path, session) -> None:
    path.mkdir(parents=True, exist_ok=True)
    for relative_path, content in _portable_metadata_payloads(session).items():
        (path / relative_path).write_text(content, encoding="utf-8")


def _json_default(value):
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, bytes):
        return {"binaryBytes": len(value)}
    return str(value)


def _graphml(session) -> str:
    namespace = "http://graphml.graphdrawing.org/xmlns"
    root = ElementTree.Element("graphml", xmlns=namespace)
    graph = ElementTree.SubElement(
        root, "graph", id="berrybrain", edgedefault="directed"
    )
    for row in session.execute(
        text(
            "SELECT id, type, label, title, status, confidence, provider, model "
            "FROM graph_nodes ORDER BY id"
        )
    ).mappings():
        node = ElementTree.SubElement(graph, "node", id=f"n{row['id']}")
        for key, value in row.items():
            ElementTree.SubElement(node, "data", key=str(key)).text = str(value or "")
    for row in session.execute(
        text(
            "SELECT id, source_node_id, target_node_id, type, label, reason, "
            "evidence, confidence, provider, model, status "
            "FROM graph_edges ORDER BY id"
        )
    ).mappings():
        edge = ElementTree.SubElement(
            graph,
            "edge",
            id=f"e{row['id']}",
            source=f"n{row['source_node_id']}",
            target=f"n{row['target_node_id']}",
        )
        for key, value in row.items():
            if key in {"id", "source_node_id", "target_node_id"}:
                continue
            ElementTree.SubElement(edge, "data", key=str(key)).text = str(value or "")
    return ElementTree.tostring(root, encoding="unicode", xml_declaration=True)
