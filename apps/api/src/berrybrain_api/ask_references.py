"""Resolve cited Ask evidence to current, typed BerryBrain resources.

The model supplies evidence IDs only. Resource IDs, titles and navigation targets
are taken from verified retrieval metadata and then checked against live records.
No URL supplied by the model or by a note is trusted as a navigation target.
"""

from __future__ import annotations

import json
import re
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from berrybrain_api.artifact_state import accepted_node_clause
from berrybrain_api.models import GraphNodeRecord, NoteAttachmentRecord, NoteRecord


def _record_id(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    try:
        parsed = int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError, OverflowError):
        return None
    return parsed if parsed > 0 and str(value).strip() == str(parsed) else None


def capture_ask_references(session: Session, evidence: object) -> list[dict[str, Any]]:
    """Capture only identities that came from validated, cited evidence."""
    if not isinstance(evidence, list):
        return []
    captured: dict[tuple[str, int], dict[str, Any]] = {}
    for item in evidence[:40]:
        if not isinstance(item, dict):
            continue
        if item.get("citationStatus") != "source_verified":
            continue
        metadata = item.get("metadata")
        if not isinstance(metadata, dict):
            metadata = item
        evidence_id = str(item.get("evidenceId") or item.get("id") or "")[:160]
        for kind, field in (
            ("attachment", "attachmentId"),
            ("note", "noteId"),
            ("graph_node", "nodeId"),
        ):
            identity = _record_id(metadata.get(field))
            if identity is None:
                continue
            if kind == "attachment":
                record = session.get(NoteAttachmentRecord, identity)
                if record is None or record.validation_status != "validated":
                    continue
                claimed_note_id = _record_id(metadata.get("noteId"))
                if claimed_note_id is not None and record.note_id != claimed_note_id:
                    continue
                owner = session.get(NoteRecord, record.note_id)
                if owner is None or owner.evidence_status == "draft":
                    continue
                stable_id = f"{owner.stable_id}:{record.checksum}:{record.stored_path}"
                version = record.checksum
            elif kind == "note":
                record = session.get(NoteRecord, identity)
                if record is None or record.evidence_status == "draft":
                    continue
                stable_id = record.stable_id
                version = record.content_hash
            else:
                record = session.scalar(
                    select(GraphNodeRecord).where(
                        GraphNodeRecord.id == identity, accepted_node_clause()
                    )
                )
                if record is None:
                    continue
                stable_id = record.stable_id
                version = str(record.artifact_version)
            key = (kind, identity)
            if key not in captured:
                captured[key] = {
                    "kind": kind,
                    "id": identity,
                    "stableId": stable_id,
                    "sourceVersion": version,
                    "evidenceIds": [],
                }
            if evidence_id and evidence_id not in captured[key]["evidenceIds"]:
                captured[key]["evidenceIds"].append(evidence_id)
    return list(captured.values())


def resolve_ask_references(session: Session, stored: object) -> list[dict[str, Any]]:
    """Revalidate IDs and stable identity before exposing a current route."""
    if not isinstance(stored, list):
        return []
    result: list[dict[str, Any]] = []
    for item in stored[:40]:
        if not isinstance(item, dict):
            continue
        kind = item.get("kind")
        identity = _record_id(item.get("id"))
        stable_id = item.get("stableId")
        if identity is None or not isinstance(stable_id, str) or not stable_id:
            continue
        if kind == "attachment":
            attachment = session.get(NoteAttachmentRecord, identity)
            if attachment is None or attachment.validation_status != "validated":
                continue
            note = session.get(NoteRecord, attachment.note_id)
            if note is None or note.evidence_status == "draft":
                continue
            current_stable_id = (
                f"{note.stable_id}:{attachment.checksum}:{attachment.stored_path}"
            )
            if current_stable_id != stable_id:
                continue
            result.append(
                {
                    "kind": "attachment",
                    "id": attachment.id,
                    "stableId": current_stable_id,
                    "title": attachment.filename,
                    "path": note.path,
                    "noteId": note.id,
                    "noteTitle": note.title,
                    "vaultId": note.vault_id,
                    "sourceVersion": item.get("sourceVersion"),
                    "current": item.get("sourceVersion") == attachment.checksum,
                    "evidenceIds": _evidence_ids(item),
                }
            )
        elif kind == "note":
            note = session.get(NoteRecord, identity)
            if (
                note is None
                or note.evidence_status == "draft"
                or note.stable_id != stable_id
            ):
                continue
            result.append(
                {
                    "kind": "note",
                    "id": note.id,
                    "stableId": note.stable_id,
                    "title": note.title,
                    "path": note.path,
                    "vaultId": note.vault_id,
                    "sourceVersion": item.get("sourceVersion"),
                    "current": item.get("sourceVersion") == note.content_hash,
                    "evidenceIds": _evidence_ids(item),
                }
            )
        elif kind == "graph_node":
            node = session.scalar(
                select(GraphNodeRecord).where(
                    GraphNodeRecord.id == identity, accepted_node_clause()
                )
            )
            if node is None or node.stable_id != stable_id:
                continue
            result.append(
                {
                    "kind": "graph_node",
                    "id": node.id,
                    "stableId": node.stable_id,
                    "title": node.title or node.label,
                    "nodeType": node.type,
                    "vaultId": node.vault_id,
                    "sourceNotes": _graph_source_notes(session, node),
                    "sourceVersion": item.get("sourceVersion"),
                    "current": item.get("sourceVersion") == str(node.artifact_version),
                    "evidenceIds": _evidence_ids(item),
                }
            )
    return result


def _graph_source_notes(
    session: Session, node: GraphNodeRecord
) -> list[dict[str, Any]]:
    """Expose only current, non-draft notes explicitly recorded as node sources."""
    try:
        raw = json.loads(node.source_note_ids or "[]")
    except (TypeError, ValueError):
        return []
    if not isinstance(raw, list):
        return []
    note_ids = list(
        dict.fromkeys(filter(None, (_record_id(item) for item in raw[:20])))
    )[:8]
    if not note_ids:
        return []
    notes = {
        note.id: note
        for note in session.scalars(
            select(NoteRecord).where(
                NoteRecord.id.in_(note_ids), NoteRecord.evidence_status != "draft"
            )
        )
    }
    return [
        {
            "id": notes[note_id].id,
            "title": notes[note_id].title,
            "path": notes[note_id].path,
            "vaultId": notes[note_id].vault_id,
        }
        for note_id in note_ids
        if note_id in notes
    ]


def _evidence_ids(item: dict[str, Any]) -> list[str]:
    raw = item.get("evidenceIds")
    if not isinstance(raw, list):
        return []
    return [value[:160] for value in raw[:20] if isinstance(value, str) and value]


def append_verified_reference_links(
    answer: str, references: list[dict[str, Any]]
) -> str:
    """Add navigable sources when the model omitted their verified links.

    References must already have been resolved against live records. The model's
    text and claimed URLs are never used to construct the navigation target.
    """
    if not answer.strip():
        return answer
    missing: list[str] = []
    for reference in references[:40]:
        kind = reference.get("kind")
        identity = _record_id(reference.get("id"))
        if kind not in {"note", "graph_node", "attachment"} or identity is None:
            continue
        markers = [f"resolved:{kind}:{identity}", *_evidence_ids(reference)]
        if any(f"](bbref:{marker})" in answer for marker in markers):
            continue
        title = " ".join(str(reference.get("title") or "Reference").split())
        label = re.sub(r"([\\\[\]])", r"\\\1", title)
        missing.append(f"[{label}](bbref:resolved:{kind}:{identity})")
    if not missing:
        return answer
    return answer.rstrip() + "\n\nFontes verificadas: " + " · ".join(missing)
