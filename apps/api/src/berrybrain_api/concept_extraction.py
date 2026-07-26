from __future__ import annotations

import json
import re
from typing import Any

from berrybrain_api.models import (
    GeneratedMetadataRecord,
    NoteRecord,
)

# Constants from second_brain
PROMPT_VERSION = "graph-expand.deterministic.v1"
STOPWORDS = {
    "a",
    "as",
    "de",
    "do",
    "da",
    "das",
    "dos",
    "e",
    "em",
    "o",
    "os",
    "para",
    "por",
    "que",
    "um",
    "uma",
    "com",
    "sobre",
    "qual",
    "quais",
    "relacao",
    "relação",
    "tem",
    "ver",
}

CONTENT_CONCEPT_PATTERNS = {
    "frontend": "Frontend development",
    "backend": "Backend development",
    "full stack": "Full Stack development",
    "ux/ui": "UX/UI design",
    "ux ui": "UX/UI design",
    "desenvolvimento web": "Web development",
    "design de interfaces": "Interface design",
    "design gráfico": "Graphic design",
    "ciência da computação": "Computer Science",
    "html": "HTML",
    "css": "CSS",
    "javascript": "JavaScript",
    "typescript": "TypeScript",
    "react": "React",
    "next.js": "Next.js",
    "node.js": "Node.js",
    "tailwind": "Tailwind CSS",
    "docker": "Docker",
    "postgresql": "PostgreSQL",
    "hulk": "Hulk",
    "bruce banner": "Bruce Banner",
    "radiação": "Radiation",
    "raiva": "Emotional control",
    "emoções": "Emotional control",
    "equilíbrio": "Balance",
    "conflitos internos": "Internal conflict",
    "força": "Strength",
    "superação": "Overcoming adversity",
    "rio de janeiro": "Rio de Janeiro",
    "desafios sociais": "Social challenges",
    "desafios urbanos": "Urban challenges",
    "desenvolvimento": "Development",
    "transformação": "Transformation",
}


def _parse_json_object(value: str) -> dict[str, Any]:
    try:
        parsed = json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def normalize_concept_name(value: str) -> str:
    cleaned = re.sub(r"[-_]+", " ", value.strip().lower())
    cleaned = re.sub(r"\s+", " ", cleaned)
    cleaned = re.sub(r"^[#/\\-]+|[#/\\-]+$", "", cleaned)
    if len(cleaned) < 3 or cleaned in STOPWORDS:
        return ""
    return cleaned[:120]


def _extract_note_concepts(
    note: NoteRecord, metadata: list[GeneratedMetadataRecord]
) -> list[tuple[str, str, str]]:
    concepts: list[tuple[str, str, str]] = []
    seen: set[str] = set()
    note_title_key = normalize_concept_name(note.title)
    for record in metadata:
        content = _parse_json_object(record.content)
        values: list[Any] = []
        if record.generation_type == "concepts":
            values = _extract_values(content, ["concepts", "items", "keywords"])
        elif record.generation_type == "summary":
            values = _extract_values(content, ["concepts", "keywords"])
        elif record.generation_type == "classification":
            values = _extract_values(content, ["concepts"])
        if not values and record.generation_type in {"concepts", "summary"}:
            values = _extract_terms_from_metadata_text(content)
        for value in values:
            if isinstance(value, dict):
                name = str(
                    value.get("name")
                    or value.get("title")
                    or value.get("label")
                    or value.get("text")
                    or ""
                )
            else:
                name = str(value)
            normalized = normalize_concept_name(name)
            if not normalized or normalized == note_title_key or normalized in seen:
                continue
            if _is_valid_concept_name(name):
                seen.add(normalized)
                concepts.append(
                    (name, f"{note.title}: {name}", record.model_used or "")
                )
    for name in _extract_content_concepts(note):
        normalized = normalize_concept_name(name)
        if not normalized or normalized == note_title_key or normalized in seen:
            continue
        if _is_valid_concept_name(name):
            seen.add(normalized)
            concepts.append((name, f"{note.title}: {name}", "content-analysis"))
    return concepts


def _is_valid_concept_name(name: str) -> bool:
    clean = " ".join(str(name or "").strip().split())
    if len(clean) < 2 or len(clean) > 80:
        return False
    if len(clean.split()) > 8:
        return False
    lowered = clean.lower()
    if normalize_concept_name(clean) in {
        "assim",
        "apesar",
        "baixe",
        "contatos",
        "durante",
        "foto",
        "home",
        "study",
        "studies",
        "note",
        "notes",
        "draft",
        "rascunho",
        "inbox",
        "janeiro",
        "meus",
        "processo",
        "projetos",
        "resumo",
        "rio",
        "servicos",
        "serviços",
        "tanto",
    }:
        return False
    if "/" in lowered or "\\" in lowered:
        return False
    if lowered.endswith(".md"):
        return False
    blocked_prefixes = (
        "falta ",
        "faltam ",
        "nao ha ",
        "não há ",
        "sem ",
        "lacuna",
        "missing ",
        "no ",
    )
    return not lowered.startswith(blocked_prefixes)


def _is_valid_topic_name(name: str, note_title_key: str = "") -> bool:
    if not _is_valid_concept_name(name):
        return False
    normalized = normalize_concept_name(name)
    if normalized == note_title_key:
        return False
    if normalized.replace(" ", "-") == note_title_key.replace(" ", "-"):
        return False
    generic = {
        "study",
        "studies",
        "note",
        "notes",
        "permanent",
        "permanente",
        "permanentes",
        "inbox",
        "draft",
        "rascunho",
    }
    if normalized in generic:
        return False
    return not ("/" in str(name) or "\\" in str(name))


def _concepts_from_title(title: str) -> list[tuple[str, str, str]]:
    parts = [p for p in re.split(r"[:|/\\-]", title) if p.strip()]
    concepts = [(title, f"Note title: {title}", "")]
    concepts.extend((part, f"Note title: {title}", "") for part in parts)
    return concepts


def _extract_content_concepts(note: NoteRecord) -> list[str]:
    text = _clean_note_text_for_concepts(note.content or "")
    if not text.strip():
        return []
    lowered = text.lower()
    candidates: list[str] = []
    for needle, concept in CONTENT_CONCEPT_PATTERNS.items():
        if needle in lowered:
            candidates.append(concept)

    # Capture explicit proper names that often act as entities/concepts.
    for match in re.finditer(
        r"\b([A-ZÀ-Ý][\wÀ-ÿ]+(?:[ \t]+[A-ZÀ-Ý][\wÀ-ÿ]+){0,3})\b", text
    ):
        name = " ".join(match.group(1).split())
        normalized = normalize_concept_name(name)
        if _is_valid_concept_name(name) and normalized not in {"home", "resumo"}:
            candidates.append(name)

    return _unique_concept_names(candidates)[:18]


def _extract_terms_from_metadata_text(content: Any) -> list[str]:
    text = _flatten_metadata_text(content)
    if not text:
        return []
    candidates: list[str] = []
    for line in re.split(r"[\n;]+", text):
        clean = re.sub(r"^[*\-\d.\s]+", "", line).strip()
        if _is_valid_concept_name(clean):
            candidates.append(clean)
    for phrase in re.findall(r'"([^"]{3,80})"', text):
        if _is_valid_concept_name(phrase):
            candidates.append(phrase)
    return _unique_concept_names(candidates)[:12]


def _flatten_metadata_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "\n".join(_flatten_metadata_text(item) for item in value)
    if isinstance(value, dict):
        return "\n".join(_flatten_metadata_text(item) for item in value.values())
    return ""


def _unique_concept_names(values: list[str]) -> list[str]:
    seen: set[str] = set()
    preliminary: list[str] = []
    for value in values:
        clean = " ".join(str(value or "").strip().split())
        normalized = normalize_concept_name(clean)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        preliminary.append(clean)
    normalized_all = {normalize_concept_name(value): value for value in preliminary}
    result: list[str] = []
    for value in preliminary:
        normalized = normalize_concept_name(value)
        is_partial = (
            len(normalized.split()) == 1
            and not value.isupper()
            and any(
                normalized != other and normalized in other.split()
                for other in normalized_all
            )
        )
        if not is_partial:
            result.append(value)
    return result


def _clean_note_text_for_concepts(text: str) -> str:
    cleaned = re.sub(r"!\[[^\]]*\]\([^)]+\)", " ", text)
    cleaned = re.sub(r"\[[^\]]+\]\([^)]+\)", " ", cleaned)
    cleaned = re.sub(r"`[^`]*`", " ", cleaned)
    cleaned = re.sub(r"https?://\S+", " ", cleaned)
    return cleaned


def _extract_values(content: Any, keys: list[str]) -> list[Any]:
    if isinstance(content, list):
        return content
    if not isinstance(content, dict):
        return []
    values: list[Any] = []
    for key in keys:
        item = content.get(key)
        if isinstance(item, list):
            values.extend(item)
        elif item:
            values.append(item)
    return values
