from __future__ import annotations

import csv
import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
from datetime import UTC, datetime
from io import StringIO
from pathlib import Path
from xml.etree import ElementTree

from sqlalchemy import select
from sqlalchemy.orm import Session

from berrybrain_api.automation_logs import create_automation_log
from berrybrain_api.generated_metadata import upsert_generated_metadata
from berrybrain_api.graph_write_service import GraphWriteService
from berrybrain_api.extractor_sandbox import sandboxed_subprocess_kwargs
from berrybrain_api.models import (
    AttachmentExtractionRecord,
    GraphNodeRecord,
    NoteAttachmentRecord,
    NoteRecord,
)
from berrybrain_api.second_brain import (
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

ALLOWED_ATTACHMENT_EXTRACTORS = {
    "auto",
    "attachment-text.v1",
    "tesseract",
    "faster-whisper",
    "whisper-cli",
}


def validate_attachment_extractor(value: str | None) -> str:
    extractor = (value or "auto").strip().lower()
    if extractor not in ALLOWED_ATTACHMENT_EXTRACTORS:
        raise ValueError(f"Unsupported attachment extractor: {extractor}")
    return extractor


def process_attachment(
    session: Session,
    vault_path: str | Path,
    attachment_id: int,
    *,
    extractor: str = "auto",
    ocr_executable: str = "tesseract",
    ocr_language: str = "eng",
    transcription_executable: str = "whisper",
    transcription_model: str = "base",
    timeout_seconds: int = 300,
) -> dict[str, object]:
    extractor = validate_attachment_extractor(extractor)
    attachment = session.get(NoteAttachmentRecord, attachment_id)
    if attachment is None:
        raise ValueError("Attachment not found")
    note = session.get(NoteRecord, attachment.note_id)
    if note is None:
        raise ValueError("Attachment note not found")

    extraction = _get_or_create_extraction(session, attachment.id)
    extraction.status = "processing"
    extraction.stage = "validating"
    extraction.progress = 5
    extraction.extractor = extractor
    extraction.error = ""
    extraction.updated_at = datetime.now(UTC)
    session.commit()

    vault_root = Path(vault_path).resolve()
    file_path = (vault_root / attachment.stored_path).resolve()
    if vault_root not in file_path.parents:
        _finish_extraction(
            session,
            extraction,
            status="failed",
            error="Attachment path escapes the vault",
        )
        raise ValueError("Invalid attachment path")
    if not file_path.exists():
        _finish_extraction(
            session,
            extraction,
            status="failed",
            error="Attachment file not found",
        )
        raise ValueError("Attachment file not found")

    extraction.stage = "extracting"
    extraction.progress = 25
    session.commit()
    (
        text,
        status,
        error,
        location_metadata,
        confidence,
        used_extractor,
        provider,
        model,
    ) = _extract_text(
        file_path,
        attachment,
        extractor=extractor,
        ocr_executable=ocr_executable,
        ocr_language=ocr_language,
        transcription_executable=transcription_executable,
        transcription_model=transcription_model,
        timeout_seconds=max(10, timeout_seconds),
    )
    if status != "completed":
        confidence = 0.0
    summary = _summarize_text(text, attachment.filename) if text else ""
    _finish_extraction(
        session,
        extraction,
        status=status,
        text=text,
        summary=summary,
        confidence=confidence,
        error=error,
        location_metadata=location_metadata,
        extractor=used_extractor,
        provider=provider,
        model=model,
    )

    node = _upsert_attachment_node(session, attachment, note, extraction)
    if status == "completed" and text:
        upsert_generated_metadata(
            session,
            note.id,
            f"attachment_text_{attachment.id}",
            {
                "attachmentId": attachment.id,
                "attachmentHash": f"{attachment.stored_path}:{attachment.size_bytes}",
                "filename": attachment.filename,
                "summary": summary,
                "extractedText": text[:12000],
            },
            content_hash=note.content_hash,
            model_used=extraction.model,
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
            "extractor": extraction.extractor,
            "provider": extraction.provider,
            "model": extraction.model,
            "confidence": extraction.confidence,
        },
        reversible=False,
    )
    return serialize_extraction(extraction)


def serialize_extraction(
    record: AttachmentExtractionRecord | None,
) -> dict[str, object]:
    if record is None:
        return {
            "status": "pending",
            "summary": "",
            "confidence": 0.0,
            "provider": "deterministic",
            "model": "attachment-text.v1",
            "error": "",
            "stage": "pending",
            "progress": 0,
            "extractor": "attachment-text.v1",
            "locationMetadata": {},
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
        "stage": record.stage,
        "progress": record.progress,
        "extractor": record.extractor,
        "locationMetadata": _load_location_metadata(record.location_metadata),
        "updatedAt": record.updated_at.isoformat() if record.updated_at else None,
    }


def _load_location_metadata(raw: str) -> dict[str, object]:
    try:
        value = json.loads(raw or "{}")
    except (json.JSONDecodeError, TypeError):
        return {}
    return value if isinstance(value, dict) else {}


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
    location_metadata: dict[str, object] | None = None,
    extractor: str = "attachment-text.v1",
    provider: str = "deterministic",
    model: str = "attachment-text.v1",
) -> None:
    extraction.status = status
    extraction.extracted_text = text
    extraction.summary = summary
    extraction.confidence = confidence
    extraction.error = error
    extraction.stage = "completed" if status == "completed" else status
    extraction.progress = (
        100 if status in {"completed", "failed", "unsupported", "encrypted"} else 25
    )
    extraction.extractor = extractor
    extraction.location_metadata = json.dumps(
        location_metadata or {}, ensure_ascii=False
    )
    extraction.provider = provider
    extraction.model = model
    extraction.updated_at = datetime.now(UTC)
    session.commit()


def _extract_text(
    path: Path,
    attachment: NoteAttachmentRecord,
    *,
    extractor: str,
    ocr_executable: str,
    ocr_language: str,
    transcription_executable: str,
    transcription_model: str,
    timeout_seconds: int,
) -> tuple[str, str, str, dict[str, object], float, str, str, str]:
    suffix = path.suffix.lower()
    mime = (attachment.mime_type or "").lower()
    if attachment.category == "image":
        if extractor not in {"auto", "tesseract"}:
            return _unsupported_extractor(extractor, attachment.category)
        return _extract_image_ocr(path, ocr_executable, ocr_language, timeout_seconds)
    if attachment.category in {"audio", "video"}:
        if extractor not in {"auto", "faster-whisper", "whisper-cli"}:
            return _unsupported_extractor(extractor, attachment.category)
        selected_executable = transcription_executable
        if extractor == "faster-whisper":
            selected_executable = "faster-whisper"
        elif extractor == "whisper-cli":
            selected_executable = "whisper"
        return _transcribe_media(
            path,
            selected_executable,
            transcription_model,
            timeout_seconds,
        )
    if extractor not in {"auto", "attachment-text.v1"}:
        return _unsupported_extractor(extractor, attachment.category)
    if suffix == ".pdf" or mime == "application/pdf":
        return (
            *_extract_pdf_text(path),
            0.8,
            "attachment-text.v1",
            "deterministic",
            "pypdf",
        )
    if suffix == ".docx":
        return (
            *_extract_docx_text(path),
            0.8,
            "attachment-text.v1",
            "deterministic",
            "docx-xml.v1",
        )
    if suffix in TEXT_SUFFIXES or mime.startswith("text/"):
        return (
            _read_text_file(path),
            "completed",
            "",
            {},
            1.0,
            "attachment-text.v1",
            "deterministic",
            "text-decoder.v1",
        )
    return (
        "",
        "unsupported",
        "No extractor is configured for this attachment type.",
        {},
        0.0,
        "attachment-text.v1",
        "deterministic",
        "attachment-text.v1",
    )


def _unsupported_extractor(
    extractor: str, category: str
) -> tuple[str, str, str, dict[str, object], float, str, str, str]:
    return (
        "",
        "unsupported",
        f'Extractor "{extractor}" cannot process {category} attachments.',
        {},
        0.0,
        extractor,
        "local",
        extractor,
    )


def _resolve_local_executable(configured: str, expected: str) -> str | None:
    if Path(configured).name != expected:
        return None
    return shutil.which(configured)


def _extract_image_ocr(
    path: Path, executable: str, language: str, timeout_seconds: int
) -> tuple[str, str, str, dict[str, object], float, str, str, str]:
    resolved = _resolve_local_executable(executable, "tesseract")
    model = f"tesseract-{language or 'eng'}"
    if resolved is None:
        return (
            "",
            "waiting_ocr",
            "Local Tesseract OCR is not installed or configured.",
            {},
            0.0,
            "tesseract",
            "local",
            model,
        )
    try:
        with tempfile.TemporaryDirectory(prefix="berrybrain-ocr-") as work_dir:
            result = subprocess.run(
                [resolved, str(path), "stdout", "-l", language or "eng", "tsv"],
                **sandboxed_subprocess_kwargs(
                    resolved,
                    work_dir,
                    timeout_seconds,
                ),
            )
    except subprocess.TimeoutExpired:
        return (
            "",
            "failed",
            "OCR timed out.",
            {},
            0.0,
            "tesseract",
            "local",
            model,
        )
    if result.returncode != 0:
        error = (result.stderr or "Tesseract OCR failed.").strip()[:500]
        return "", "failed", error, {}, 0.0, "tesseract", "local", model

    words: list[dict[str, object]] = []
    lines: dict[tuple[str, str, str, str], list[str]] = {}
    confidences: list[float] = []
    for row in csv.DictReader(StringIO(result.stdout), delimiter="\t"):
        word = (row.get("text") or "").strip()
        try:
            confidence = float(row.get("conf") or -1)
        except ValueError:
            confidence = -1
        if not word or confidence < 0:
            continue
        line_key = tuple(
            row.get(name, "0")
            for name in ("page_num", "block_num", "par_num", "line_num")
        )
        lines.setdefault(line_key, []).append(word)
        confidences.append(confidence)
        if len(words) < 2000:
            words.append(
                {
                    "text": word,
                    "confidence": round(confidence / 100, 4),
                    "page": int(row.get("page_num") or 1),
                    "box": {
                        key: int(row.get(key) or 0)
                        for key in ("left", "top", "width", "height")
                    },
                }
            )
    text = "\n".join(" ".join(items) for items in lines.values()).strip()
    confidence = sum(confidences) / (100 * len(confidences)) if confidences else 0.0
    if not text:
        return (
            "",
            "failed",
            "OCR found no readable text.",
            {},
            0.0,
            "tesseract",
            "local",
            model,
        )
    return (
        text[:120000],
        "completed",
        "",
        {"kind": "ocr_words", "language": language or "eng", "words": words},
        round(confidence, 4),
        "tesseract",
        "local",
        model,
    )


def _transcribe_media(
    path: Path, executable: str, model: str, timeout_seconds: int
) -> tuple[str, str, str, dict[str, object], float, str, str, str]:
    if executable.strip().lower() == "faster-whisper":
        return _transcribe_faster_whisper(path, model, timeout_seconds)

    resolved = _resolve_local_executable(executable, "whisper")
    if resolved is None:
        return (
            "",
            "waiting_transcription",
            "Local Whisper transcription is not installed or configured.",
            {},
            0.0,
            "whisper-cli",
            "local",
            model,
        )
    with tempfile.TemporaryDirectory(prefix="berrybrain-transcription-") as output_dir:
        try:
            result = subprocess.run(
                [
                    resolved,
                    str(path),
                    "--model",
                    model,
                    "--output_format",
                    "json",
                    "--output_dir",
                    output_dir,
                ],
                **sandboxed_subprocess_kwargs(
                    resolved,
                    output_dir,
                    timeout_seconds,
                ),
            )
        except subprocess.TimeoutExpired:
            return (
                "",
                "failed",
                "Transcription timed out.",
                {},
                0.0,
                "whisper-cli",
                "local",
                model,
            )
        if result.returncode != 0:
            error = (result.stderr or "Whisper transcription failed.").strip()[:500]
            return "", "failed", error, {}, 0.0, "whisper-cli", "local", model
        output_path = Path(output_dir) / f"{path.stem}.json"
        try:
            payload = json.loads(output_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            return (
                "",
                "failed",
                f"Invalid transcription output: {exc}",
                {},
                0.0,
                "whisper-cli",
                "local",
                model,
            )

    segments = [
        {
            "start": float(item.get("start", 0.0)),
            "end": float(item.get("end", 0.0)),
            "text": str(item.get("text", "")).strip(),
        }
        for item in payload.get("segments", [])
        if isinstance(item, dict) and str(item.get("text", "")).strip()
    ]
    text = " ".join(str(item["text"]) for item in segments).strip()
    if not text:
        return (
            "",
            "failed",
            "Transcription produced no text.",
            {},
            0.0,
            "whisper-cli",
            "local",
            model,
        )
    return (
        text[:120000],
        "completed",
        "",
        {
            "kind": "media_timestamps",
            "language": str(payload.get("language", "")),
            "segments": segments[:2000],
        },
        0.8,
        "whisper-cli",
        "local",
        model,
    )


def _transcribe_faster_whisper(
    path: Path, model: str, timeout_seconds: int
) -> tuple[str, str, str, dict[str, object], float, str, str, str]:
    executable = str(Path(sys.executable).resolve())
    with tempfile.TemporaryDirectory(prefix="berrybrain-transcription-") as work_dir:
        try:
            result = subprocess.run(
                [
                    executable,
                    "-m",
                    "berrybrain_api.faster_whisper_extractor",
                    "--input",
                    str(path),
                    "--model",
                    model,
                ],
                **sandboxed_subprocess_kwargs(
                    executable,
                    work_dir,
                    timeout_seconds,
                ),
            )
        except subprocess.TimeoutExpired:
            return (
                "",
                "failed",
                "Transcription timed out.",
                {},
                0.0,
                "faster-whisper",
                "local",
                model,
            )
    if result.returncode != 0:
        error = (result.stderr or "Faster Whisper transcription failed.").strip()[:500]
        return "", "failed", error, {}, 0.0, "faster-whisper", "local", model
    try:
        payload = json.loads(result.stdout)
    except (json.JSONDecodeError, TypeError) as exc:
        return (
            "",
            "failed",
            f"Invalid transcription output: {exc}",
            {},
            0.0,
            "faster-whisper",
            "local",
            model,
        )
    segments = [
        {
            "start": float(item.get("start", 0.0)),
            "end": float(item.get("end", 0.0)),
            "text": str(item.get("text", "")).strip(),
            "confidence": float(item.get("confidence", 0.0)),
        }
        for item in payload.get("segments", [])
        if isinstance(item, dict) and str(item.get("text", "")).strip()
    ]
    text = " ".join(str(item["text"]) for item in segments).strip()
    if not text:
        return (
            "",
            "failed",
            "Transcription produced no text.",
            {},
            0.0,
            "faster-whisper",
            "local",
            model,
        )
    return (
        text[:120000],
        "completed",
        "",
        {
            "kind": "media_timestamps",
            "language": str(payload.get("language", "")),
            "languageProbability": float(payload.get("language_probability", 0.0)),
            "segments": segments[:2000],
        },
        max(0.0, min(1.0, float(payload.get("confidence", 0.0)))),
        "faster-whisper",
        "local",
        model,
    )


def _extract_pdf_text(path: Path) -> tuple[str, str, str, dict[str, object]]:
    try:
        from pypdf import PdfReader  # type: ignore
    except Exception:
        return (
            "",
            "waiting_pdf_extractor",
            "PDF extraction requires the optional pypdf package.",
            {},
        )
    try:
        reader = PdfReader(str(path))
        if reader.is_encrypted:
            return "", "encrypted", "Encrypted PDF files are not supported.", {}
        pages = []
        chunks = []
        offset = 0
        for page_number, page in enumerate(reader.pages, start=1):
            page_text = (page.extract_text() or "").strip()
            chunk = f"[Page {page_number}]\n{page_text}"
            chunks.append(chunk)
            pages.append(
                {
                    "page": page_number,
                    "startChar": offset,
                    "endChar": offset + len(chunk),
                }
            )
            offset += len(chunk) + 2
        text = "\n\n".join(chunks).strip()
    except Exception as exc:
        return "", "failed", f"PDF extraction failed: {exc}", {}
    if not text:
        return "", "waiting_ocr", "PDF has no extractable text; OCR is required.", {}
    return text[:120000], "completed", "", {"kind": "pdf_pages", "pages": pages}


def _extract_docx_text(path: Path) -> tuple[str, str, str, dict[str, object]]:
    try:
        with zipfile.ZipFile(path) as archive:
            xml = archive.read("word/document.xml")
    except Exception as exc:
        return "", "failed", f"DOCX extraction failed: {exc}", {}
    try:
        root = ElementTree.fromstring(xml)
        texts = [node.text or "" for node in root.iter() if node.tag.endswith("}t")]
    except Exception as exc:
        return "", "failed", f"DOCX text parsing failed: {exc}", {}
    text = "\n".join(item.strip() for item in texts if item.strip())
    return (
        text[:120000],
        "completed",
        "" if text else "DOCX contains no extractable text.",
        {},
    )


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
    evidence = [attachment.filename, note.title, extraction.status]
    summary = (
        extraction.summary or f"{attachment.filename} is attached to {note.title}."
    )
    ai_context = (
        f'This attachment supports the note "{note.title}". Extraction status is '
        f"{extraction.status}. Use it as source evidence once text, OCR, or transcription is available."
    )
    existing = GraphWriteService(session, autocommit=False).upsert_node(
        node_type="attachment",
        label=attachment.filename,
        title=attachment.filename,
        summary=summary,
        ai_summary=summary,
        ai_context=ai_context,
        source="attachment",
        source_id=attachment.id,
        source_note_ids=[note.id],
        source_attachment_ids=[attachment.id],
        source_evidence=evidence,
        confidence=extraction.confidence or 0.5,
        created_by="system",
        model=extraction.model,
        provider=extraction.provider,
        prompt_version="attachment-processing.v1",
        status="confirmed" if extraction.status == "completed" else "suggested",
        source_quality="extracted" if extraction.status == "completed" else "pending",
        learning_value="attachment",
        graph_metadata={
            "path": attachment.stored_path,
            "mimeType": attachment.mime_type,
            "category": attachment.category,
            "sizeBytes": attachment.size_bytes,
            "extractionStatus": extraction.status,
        },
    )
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
        provider=extraction.provider,
        model=extraction.model,
        prompt_version="attachment-processing.v1",
        confidence=existing.confidence,
    )
    if edge:
        edge.ai_notes = (
            "Attachment connection created from persisted note attachment metadata."
        )
    session.commit()
    return existing
