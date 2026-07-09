from pathlib import Path
from dataclasses import dataclass
import hashlib
import re
import unicodedata

from fastapi import HTTPException


SAFE_FOLDERS = {
    "inbox",
    "estudos",
    "permanentes",
    "revisao",
    "templates",
}


@dataclass(frozen=True)
class MarkdownMetadata:
    body: str
    content_hash: str
    frontmatter: dict[str, str | list[str]]
    links: list[str]


def slugify_title(title: str) -> str:
    ascii_title = (
        unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode("ascii")
    )
    normalized = ascii_title.strip().lower()
    normalized = re.sub(r"[^a-z0-9\-_ ]+", "", normalized)
    normalized = re.sub(r"\s+", "-", normalized)
    return normalized.strip("-") or "nota"


def unique_note_path(vault_path: Path, folder: str, slug: str) -> Path:
    candidate = resolve_note_path(vault_path, f"{folder}/{slug}.md")
    if not candidate.exists():
        return candidate

    suffix = 2
    while True:
        candidate = resolve_note_path(vault_path, f"{folder}/{slug}-{suffix}.md")
        if not candidate.exists():
            return candidate
        suffix += 1


def content_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def extract_internal_links(content: str) -> list[str]:
    links: list[str] = []
    seen: set[str] = set()
    for match in re.finditer(r"\[\[([^\]]+)\]\]", content):
        target = match.group(1).split("|", 1)[0].split("#", 1)[0].strip()
        if target and target not in seen:
            seen.add(target)
            links.append(target)
    return links


def parse_markdown_note(content: str) -> MarkdownMetadata:
    frontmatter: dict[str, str | list[str]] = {}
    body = content

    if content.startswith("---\n"):
        closing = content.find("\n---", 4)
        if closing != -1:
            raw_frontmatter = content[4:closing]
            body = content[closing + 4 :].lstrip("\n")
            frontmatter = parse_frontmatter(raw_frontmatter)

    return MarkdownMetadata(
        body=body,
        content_hash=content_hash(content),
        frontmatter=frontmatter,
        links=extract_internal_links(body),
    )


def parse_frontmatter(raw_frontmatter: str) -> dict[str, str | list[str]]:
    parsed: dict[str, str | list[str]] = {}
    current_list_key: str | None = None

    for raw_line in raw_frontmatter.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if current_list_key and stripped.startswith("- "):
            value = stripped[2:].strip()
            current = parsed.setdefault(current_list_key, [])
            if isinstance(current, list):
                current.append(value)
            continue

        current_list_key = None
        if ":" not in line:
            continue

        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            continue

        if not value:
            parsed[key] = []
            current_list_key = key
            continue

        if value.startswith("[") and value.endswith("]"):
            parsed[key] = [
                item.strip() for item in value[1:-1].split(",") if item.strip()
            ]
        else:
            parsed[key] = value.strip("\"'")

    return parsed


def ensure_vault(vault_path: Path) -> None:
    vault_path.mkdir(parents=True, exist_ok=True)
    for folder in SAFE_FOLDERS:
        (vault_path / folder).mkdir(parents=True, exist_ok=True)


def resolve_note_path(vault_path: Path, note_path: str) -> Path:
    ensure_vault(vault_path)
    root = vault_path.resolve()
    candidate = (root / note_path).resolve()

    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid note path") from exc

    if candidate.suffix != ".md":
        raise HTTPException(status_code=400, detail="Only Markdown notes are supported")

    return candidate


def list_markdown_notes(vault_path: Path) -> list[dict[str, str]]:
    ensure_vault(vault_path)

    if not vault_path.exists():
        return []

    notes: list[dict[str, str]] = []
    for path in sorted(vault_path.rglob("*.md")):
        relative_path = path.relative_to(vault_path).as_posix()
        notes.append(
            {
                "title": path.stem,
                "path": relative_path,
                "folder": path.parent.relative_to(vault_path).as_posix(),
            }
        )
    return notes


def read_note(vault_path: Path, note_path: str) -> dict[str, object]:
    path = resolve_note_path(vault_path, note_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Note not found")

    content = path.read_text(encoding="utf-8")
    metadata = parse_markdown_note(content)
    return {
        "title": path.stem,
        "path": path.relative_to(vault_path.resolve()).as_posix(),
        "content": content,
        "content_hash": metadata.content_hash,
        "links": metadata.links,
        "frontmatter": metadata.frontmatter,
    }


def create_note(
    vault_path: Path, title: str, folder: str, content: str
) -> dict[str, object]:
    if folder not in SAFE_FOLDERS:
        raise HTTPException(status_code=400, detail="Invalid folder")

    clean_title = title.strip() or "Rascunho"
    slug = slugify_title(clean_title)
    path = unique_note_path(vault_path, folder, slug)

    path.parent.mkdir(parents=True, exist_ok=True)
    text = content.strip()

    path.write_text(text, encoding="utf-8")
    return read_note(vault_path, path.relative_to(vault_path.resolve()).as_posix())


def update_note(vault_path: Path, note_path: str, content: str) -> dict[str, object]:
    path = resolve_note_path(vault_path, note_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Note not found")

    path.write_text(content, encoding="utf-8")
    return read_note(vault_path, note_path)


def delete_note(vault_path: Path, note_path: str) -> dict[str, str]:
    path = resolve_note_path(vault_path, note_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Note not found")

    path.unlink()
    return {"status": "deleted", "path": note_path}


def rename_note(vault_path: Path, note_path: str, new_title: str) -> dict[str, object]:
    old_path = resolve_note_path(vault_path, note_path)
    if not old_path.exists():
        raise HTTPException(status_code=404, detail="Note not found")

    slug = slugify_title(new_title)
    folder = old_path.parent.name
    new_path = resolve_note_path(vault_path, f"{folder}/{slug}.md")
    if new_path.exists() and new_path != old_path:
        new_path = unique_note_path(vault_path, folder, slug)

    old_path.rename(new_path)
    return read_note(vault_path, new_path.relative_to(vault_path.resolve()).as_posix())
