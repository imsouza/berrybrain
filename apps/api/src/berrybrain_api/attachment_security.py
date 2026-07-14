from __future__ import annotations

import hashlib
import io
import re
import zipfile
from pathlib import Path


MIME_CATEGORIES = {
    "image": "image",
    "audio": "audio",
    "video": "video",
    "text": "other",
}


def validate_attachment_filename(filename: str) -> str:
    raw = filename.strip()
    if (
        not raw
        or "\x00" in raw
        or "/" in raw
        or "\\" in raw
        or raw in {".", ".."}
        or Path(raw).name != raw
    ):
        raise ValueError("Attachment filename must not contain a path")
    safe = re.sub(r"[^A-Za-z0-9._ -]+", "-", raw).strip(" .")
    if not safe:
        raise ValueError("Attachment filename is invalid")
    return safe[:180]


def attachment_checksum(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def detect_mime_type(content: bytes) -> str:
    head = content[:32]
    if head.startswith(b"%PDF-"):
        return "application/pdf"
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if head.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if head.startswith((b"GIF87a", b"GIF89a")):
        return "image/gif"
    if head.startswith(b"RIFF") and content[8:12] == b"WEBP":
        return "image/webp"
    if head.startswith(b"RIFF") and content[8:12] == b"WAVE":
        return "audio/wav"
    if head.startswith(b"OggS"):
        return "audio/ogg"
    if head.startswith(b"fLaC"):
        return "audio/flac"
    if head.startswith(b"ID3") or (
        len(head) >= 2 and head[0] == 0xFF and head[1] & 0xE0 == 0xE0
    ):
        return "audio/mpeg"
    if len(content) >= 12 and content[4:8] == b"ftyp":
        brand = content[8:12]
        return "audio/mp4" if brand in {b"M4A ", b"M4B ", b"M4P "} else "video/mp4"
    if head.startswith(b"PK\x03\x04"):
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as archive:
                names = set(archive.namelist())
            if "word/document.xml" in names:
                return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        except zipfile.BadZipFile:
            return "application/octet-stream"
        return "application/zip"
    if not content:
        return "application/octet-stream"
    sample = content[:8192]
    if b"\x00" not in sample:
        for encoding in ("utf-8", "utf-16"):
            try:
                sample.decode(encoding)
                return "text/plain"
            except UnicodeDecodeError:
                continue
    return "application/octet-stream"


def attachment_category(mime_type: str) -> str:
    family = mime_type.partition("/")[0].lower()
    return MIME_CATEGORIES.get(family, "other")
