from __future__ import annotations

import re
from pathlib import Path


def normalize_slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def fallback_terms(note: dict, limit: int = 8) -> list[str]:
    title = str(note.get("title") or Path(str(note.get("path", ""))).stem).replace(
        "-", " "
    )
    content = str(note.get("content") or "")
    candidates: list[str] = []
    candidates.extend(re.findall(r"^#{1,3}\s+(.+)$", content, flags=re.MULTILINE))
    candidates.extend(re.findall(r"\b[A-Z][A-Za-z0-9_+.-]{2,}\b", content))
    candidates.extend(
        [part.strip() for part in re.split(r"[:/\\-|]", title) if part.strip()]
    )
    candidates.append(title.strip())
    seen: set[str] = set()
    terms: list[str] = []
    for item in candidates:
        clean = " ".join(str(item).strip().split())
        key = clean.lower()
        if len(clean) < 3 or len(clean) > 80 or key in seen:
            continue
        seen.add(key)
        terms.append(clean)
        if len(terms) >= limit:
            break
    return terms


def fallback_classification(note: dict) -> dict:
    terms = fallback_terms(note)
    return {
        "note_type": "study",
        "topics": terms[:5],
        "tags": [normalize_slug(term) for term in terms[:5]],
        "concepts": terms,
        "source": "deterministic_fallback",
    }


def fallback_assimilation(note: dict) -> dict:
    content = str(note.get("content") or "")
    terms = fallback_terms(note)
    summary = " ".join(content.replace("#", " ").split())[:360]
    return {
        "summary": summary or f"Note about {note.get('title') or note.get('path')}.",
        "concepts": terms,
        "gaps": [],
        "questions": [],
        "source": "deterministic_fallback",
    }


def fallback_concepts(note: dict) -> dict:
    terms = fallback_terms(note)
    return {
        "concepts": [
            {
                "name": term,
                "description": "",
                "confidence": 0.35,
                "source": "deterministic_fallback",
            }
            for term in terms
        ],
        "source": "deterministic_fallback",
    }


def fallback_entities(note: dict) -> dict:
    terms = fallback_terms(note)
    return {
        "entities": [
            {
                "name": term,
                "type": "term",
                "confidence": 0.3,
                "source": "deterministic_fallback",
            }
            for term in terms
        ],
        "source": "deterministic_fallback",
    }


def fallback_topics(note: dict) -> dict:
    terms = fallback_terms(note, limit=5)
    return {
        "topics": [
            {
                "name": term,
                "confidence": 0.3,
                "source": "deterministic_fallback",
            }
            for term in terms
        ],
        "source": "deterministic_fallback",
    }


def fallback_context(note: dict) -> dict:
    title = note.get("title") or Path(str(note.get("path", ""))).stem
    return {
        "contexts": [
            {
                "name": str(title).replace("-", " "),
                "description": "Context inferred locally because the AI did not return valid JSON.",
                "confidence": 0.25,
                "source": "deterministic_fallback",
            }
        ],
        "source": "deterministic_fallback",
    }


def chunk_note_for_embedding(content: str, max_chars: int = 2400) -> list[dict]:
    lines = (content or "").splitlines()
    chunks: list[dict] = []
    heading_stack: list[str] = []
    current_lines: list[str] = []
    current_heading = ""
    start_line = 1

    def flush(end_line: int) -> None:
        nonlocal current_lines, start_line, current_heading
        text = "\n".join(current_lines).strip()
        if not text:
            current_lines = []
            start_line = end_line + 1
            return
        chunks.append(
            {
                "chunk_index": len(chunks),
                "text": text,
                "heading_path": current_heading,
                "start_line": start_line,
                "end_line": max(start_line, end_line),
                "token_count": len(re.findall(r"\b\w+\b", text)),
            }
        )
        current_lines = []
        start_line = end_line + 1

    for index, line in enumerate(lines, start=1):
        heading = re.match(r"^(#{1,6})\s+(.+)$", line)
        if heading:
            level = len(heading.group(1))
            title = heading.group(2).strip()
            heading_stack = heading_stack[: level - 1] + [title]
        if current_lines and len("\n".join(current_lines + [line])) > max_chars:
            flush(index - 1)
        if not current_lines:
            start_line = index
            current_heading = " / ".join(heading_stack)
        current_lines.append(line)

    flush(len(lines))
    return chunks or (
        [
            {
                "chunk_index": 0,
                "text": (content or "").strip(),
                "heading_path": "",
                "start_line": 1,
                "end_line": max(1, len(lines)),
                "token_count": len(re.findall(r"\b\w+\b", content or "")),
            }
        ]
        if (content or "").strip()
        else []
    )
