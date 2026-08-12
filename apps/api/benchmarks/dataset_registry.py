from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class DatasetStatus:
    identifier: str
    installed: bool
    valid: bool
    reason: str
    path: str
    checksum: str


def file_checksum(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_manifest(path: Path) -> dict[str, Any]:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    required = {"schemaVersion", "id", "source", "license", "version", "files"}
    missing = sorted(required - manifest.keys())
    if missing:
        raise ValueError(f"dataset manifest is missing: {', '.join(missing)}")
    if manifest["schemaVersion"] != "berrybrain-dataset.v1":
        raise ValueError("unsupported dataset manifest schema")
    if not isinstance(manifest["files"], list) or not manifest["files"]:
        raise ValueError("dataset manifest must declare at least one file")
    return manifest


def verify_dataset(manifest_path: Path, data_root: Path) -> list[DatasetStatus]:
    manifest = load_manifest(manifest_path)
    statuses: list[DatasetStatus] = []
    for item in manifest["files"]:
        relative_path = str(item.get("path") or "")
        expected = str(item.get("sha256") or "")
        path = data_root / relative_path
        if not path.is_file():
            statuses.append(
                DatasetStatus(
                    identifier=str(manifest["id"]),
                    installed=False,
                    valid=False,
                    reason="file is not installed",
                    path=relative_path,
                    checksum="",
                )
            )
            continue
        actual = file_checksum(path)
        valid = bool(expected) and actual == expected
        statuses.append(
            DatasetStatus(
                identifier=str(manifest["id"]),
                installed=True,
                valid=valid,
                reason="checksum verified" if valid else "checksum mismatch or missing",
                path=relative_path,
                checksum=actual,
            )
        )
    return statuses
