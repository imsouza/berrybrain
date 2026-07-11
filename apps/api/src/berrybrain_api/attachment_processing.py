from __future__ import annotations

import json
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from xml.etree import ElementTree

from sqlalchemy import select
from sqlalchemy.orm import Session

from berrybrain_api.automation_logs import create_automation_log
from berrybrain_api.generated_metadata import upsert_generated_metadata
from berrybrain_api.models import (
    AttachmentExtractionRecord,
    GraphNodeRecord,
    NoteAttachmentRecord,
    NoteRecord,
)
from berrybrain_api.second_brain import (
    _dump_json,
    _upsert_graph_edge,
    _upsert_note_node,
)

TEXT_SUFFIXES = {
    ".txt",
    ".md",
    ".markdown",
    ".csv",
    ".json",
    ".yaml",
    ".yml",
    ".log",
    ".xml",
    ".html",
    ".css",
    ".js",
    ".ts",
    ".py",
    ".sh",
}


def process_attachment(
    session: Session, vault_path: str | Path, attachment_id: int
) -> dict[str, object]:
    attachment = session.get(NoteAttachmentRecord, attachment_id)
    if attachment is None:
        raise ValueError("Attachment not found")
    note = session.get(NoteRecord, attachment.note_id)
    if note is None:
        raise ValueError("Attachment note not found")

    extraction = _get_or_create_extraction(session, attachment.id)
    extraction.status = "processing"
    extraction.error = ""
    extraction.updated_at = datetime.now(UTC)
    session.commit()

    file_path = (Path(vault_path) / attachment.stored_path).resolve()
    if not file_path.exists():
        _finish_extraction(
            session,
            extraction,
            status="failed",
            error="Attachment file not found",
        )
        raise ValueError("Attachment file not found")

    text, status, error = _extract_text(file_path, attachment)
    summary = _summarize_text(text, attachment.filename) if text else ""
    confidence = 0.8 if status == "completed" else 0.0
    _finish_extraction(
        session,
        extraction,
        status=status,
        text=text,
        summary=summary,
        confidence=confidence,
        error=error,
    )

    node = _upsert_attachment_node(session, attachment, note, extraction)
    if status == "completed" and text:
        upsert_generated_metadata(
            session,
            note.id,
            f"attachment_text_{attachment.id}",
            {
                "attachmentId": attachment.id,
                "filename": attachment.filename,
                "summary": summary,
                "extractedText": text[:12000],
            },
            content_hash=f"{attachment.stored_path}:{attachment.size_bytes}",
            model_used="attachment-text.v1",
        )

    create_automation_log(
        session,
        action_type="PROCESS_ATTACHMENT",
        target_type="attachment",
        target_id=str(attachment.id),
        description=f"Attachment processed: {attachment.filename}",
        before_state={},
        after_state={
            "status": status,
            "note_path": note.path,
            "graph_node_id": node.id if node else None,
        },
        reversible=False,
    )
    return serialize_extraction(extraction)


def serialize_extraction(record: AttachmentExtractionRecord | None) -> dict[str, object]:
    if record is None:
        return {
            "status": "pending",
            "summary": "",
            "confidence": 0.0,
            "provider": "deterministic",
            "model": "attachment-text.v1",
            "error": "",
            "updatedAt": None,
        }
    return {
        "id": record.id,
        "attachmentId": record.attachment_id,
        "status": record.status,
        "summary": record.summary,
        "confidence": record.confidence,
        "provider": record.provider,
        "model": record.model,
        "error": record.error,
        "updatedAt": record.updated_at.isoformat() if record.updated_at else None,
    }


def _get_or_create_extraction(
    session: Session, attachment_id: int
) -> AttachmentExtractionRecord:
    record = session.execute(
        select(AttachmentExtractionRecord).where(
            AttachmentExtractionRecord.attachment_id == attachment_id
        )
    ).scalar_one_or_none()
    if record is not None:
        return record
    record = AttachmentExtractionRecord(attachment_id=attachment_id, status="pending")
    session.add(record)
    session.flush()
    return record


def _finish_extraction(
    session: Session,
    extraction: AttachmentExtractionRecord,
    status: str,
    text: str = "",
    summary: str = "",
    confidence: float = 0.0,
    error: str = "",
) -> None:
    extraction.status = status
    extraction.extracted_text = text
    extraction.summary = summary
    extraction.confidence = confidence
    extraction.error = error
    extraction.provider = "deterministic"
    extraction.model = "attachment-text.v1"
    extraction.updated_at = datetime.now(UTC)
    session.commit()


def _extract_text(path: Path, attachment: NoteAttachmentRecord) -> tuple[str, str, str]:
    suffix = path.suffix.lower()
    mime = (attachment.mime_type or "").lower()
    if attachment.category == "image":
        return "", "waiting_ocr", "OCR/vision extraction is not configured yet."
    if attachment.category in {"audio", "video"}:
        return "", "waiting_transcription", "Audio/video transcription is not configured yet."
    if suffix == ".pdf" or mime == "application/pdf":
        return _extract_pdf_text(path)
    if suffix == ".docx":
        return _extract_docx_text(path)
    if suffix in TEXT_SUFFIXES or mime.startswith("text/"):
        return _read_text_file(path), "completed", ""
    return "", "unsupported", "No extractor is configured for this attachment type."


def _extract_pdf_text(path: Path) -> tuple[str, str, str]:
    try:
        from pypdf import PdfReader  # type: ignore
    except Exception:
        return "", "waiting_pdf_extractor", "PDF extraction requires the optional pypdf package."
    try:
        reader = PdfReader(str(path))
        text = "\n\n".join(page.extract_text() or "" for page in reader.pages).strip()
    except Exception as exc:
        return "", "failed", f"PDF extraction failed: {exc}"
    if not text:
        return "", "waiting_ocr", "PDF has no extractable text; OCR is required."
    return text[:120000], "completed", ""


def _extract_docx_text(path: Path) -> tuple[str, str, str]:
    try:
        with zipfile.ZipFile(path) as archive:
            xml = archive.read("word/document.xml")
    except Exception as exc:
        return "", "failed", f"DOCX extraction failed: {exc}"
    try:
        root = ElementTree.fromstring(xml)
        texts = [node.text or "" for node in root.iter() if node.tag.endswith("}t")]
    except Exception as exc:
        return "", "failed", f"DOCX text parsing failed: {exc}"
    text = "\n".join(item.strip() for item in texts if item.strip())
    return text[:120000], "completed", "" if text else "DOCX contains no extractable text."


def _read_text_file(path: Path) -> str:
    raw = path.read_bytes()
    for encoding in ("utf-8", "utf-16", "latin-1"):
        try:
            return raw.decode(encoding).strip()[:120000]
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace").strip()[:120000]


def _summarize_text(text: str, filename: str) -> str:
    compact = " ".join(text.split())
    if len(compact) <= 280:
        return compact
    return f"{filename}: {compact[:277]}..."


def _upsert_attachment_node(
    session: Session,
    attachment: NoteAttachmentRecord,
    note: NoteRecord,
    extraction: AttachmentExtractionRecord,
) -> GraphNodeRecord:
    existing = session.execute(
        select(GraphNodeRecord).where(
            GraphNodeRecord.type == "attachment",
            GraphNodeRecord.source == "attachment",
            GraphNodeRecord.source_id == attachment.id,
        )
    ).scalar_one_or_none()
    evidence = [attachment.filename, note.title, extraction.status]
    summary = extraction.summary or f"{attachment.filename} is attached to {note.title}."
    ai_context = (
        f'This attachment supports the note "{note.title}". Extraction status is '
        f'{extraction.status}. Use it as source evidence once text, OCR, or transcription is available.'
    )
    if existing is None:
        existing = GraphNodeRecord(
            type="attachment",
            label=attachment.filename,
            title=attachment.filename,
            source="attachment",
            source_id=attachment.id,
        )
        session.add(existing)
        session.flush()
    existing.summary = summary
    existing.ai_summary = summary
    existing.ai_context = ai_context
    existing.source_note_ids = _dump_json([note.id])
    existing.source_attachment_ids = _dump_json([attachment.id])
    existing.source_evidence = _dump_json(evidence)
    existing.confidence = extraction.confidence or 0.5
    existing.created_by = "system"
    existing.created_by_model = "attachment-text.v1"
    existing.provider = "deterministic"
    existing.model = "attachment-text.v1"
    existing.prompt_version = "attachment-processing.v1"
    existing.status = "confirmed" if extraction.status == "completed" else "suggested"
    existing.source_quality = "extracted" if extraction.status == "completed" else "pending"
    existing.learning_value = "attachment"
    existing.graph_metadata = json.dumps(
        {
            "path": attachment.stored_path,
            "mimeType": attachment.mime_type,
            "category": attachment.category,
            "sizeBytes": attachment.size_bytes,
            "extractionStatus": extraction.status,
        },
        ensure_ascii=False,
    )
    existing.updated_at = datetime.now(UTC)
    note_node = _upsert_note_node(session, note)
    edge = _upsert_graph_edge(
        session,
        existing.id,
        note_node.id,
        edge_type="attachment_related",
        label="attachment related",
        reason=f'The attachment "{attachment.filename}" belongs to the note "{note.title}".',
        evidence=evidence,
        source_note_ids=[note.id],
        created_by="system",
        status="confirmed",
        provider="deterministic",
        model="attachment-text.v1",
        prompt_version="attachment-processing.v1",
        confidence=existing.confidence,
    )
    if edge:
        edge.ai_notes = (
            "Attachment connection created from persisted note attachment metadata."
        )
    session.commit()
    return existing
