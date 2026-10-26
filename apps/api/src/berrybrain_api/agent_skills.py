"""Context-triggered Agent Skills loader and selector for BerryBrain.

Loads Markdown skill definitions (`.md`) recursively from the project's `/skills`
directory and automatically activates the most relevant skill(s) based on the
user's request or background cognitive task, while preserving BerryBrain's strict
vault-first and 24h web-validated evidence grounding principles.
"""

from __future__ import annotations

import os
import re
import unicodedata
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class AgentSkill:
    id: str
    name: str
    category: str
    description: str
    triggers: tuple[str, ...]
    keywords: tuple[str, ...]
    task_types: tuple[str, ...]
    recommended_max_tokens: int
    file_name: str
    relative_path: str
    priority_tier: int
    instructions: str
    normalized_triggers: tuple[str, ...] = ()
    normalized_phrase_keywords: tuple[str, ...] = ()
    normalized_token_keywords: frozenset[str] = frozenset()

    def to_summary(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "triggers": list(self.triggers),
            "keywords": list(self.keywords),
            "taskTypes": list(self.task_types),
            "recommendedMaxTokens": self.recommended_max_tokens,
            "fileName": self.file_name,
            "relativePath": self.relative_path,
        }


def _normalize_text(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value or "")
    stripped = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", stripped.lower()).strip()


def _tokenize_normalized(value: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]{2,}", _normalize_text(value)))


def resolve_skills_dir() -> Path:
    env_dir = os.environ.get("BERRYBRAIN_SKILLS_DIR", "").strip()
    if env_dir:
        candidate = Path(env_dir)
        if candidate.is_dir():
            return candidate

    here = Path(__file__).resolve()
    candidates = [
        here.parents[4]
        / "skills",  # repo root: apps/api/src/berrybrain_api -> repo/skills
        here.parents[2] / "skills",  # /app/src/berrybrain_api -> /app/skills
        Path("/app/skills"),
        Path.cwd() / "skills",
    ]
    for candidate in candidates:
        if candidate.is_dir():
            return candidate
    return candidates[0]


def _parse_frontmatter(raw_text: str) -> tuple[dict[str, Any], str]:
    text = raw_text.lstrip("\ufeff")
    if not text.startswith("---\n"):
        return {}, text.strip()
    end_idx = text.find("\n---\n", 4)
    if end_idx == -1:
        return {}, text.strip()

    header_block = text[4:end_idx]
    body = text[end_idx + 5 :].strip()
    meta: dict[str, Any] = {}
    current_list_key: str | None = None

    for raw_line in header_block.splitlines():
        line = raw_line.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.lstrip().startswith("- ") and current_list_key:
            item = line.lstrip()[2:].strip().strip("'\"")
            if item:
                meta.setdefault(current_list_key, []).append(item)
            continue
        if ":" in line:
            key, val = line.split(":", 1)
            key = key.strip()
            val = val.strip()
            if not val:
                current_list_key = key
                meta[key] = []
            else:
                current_list_key = None
                cleaned = val.strip("'\"")
                if cleaned.isdigit():
                    meta[key] = int(cleaned)
                else:
                    meta[key] = cleaned
    return meta, body


CORE_SKILL_IDS = frozenset(
    {
        "scientific-article",
        "literature-review",
        "tcc-dissertation-monograph",
        "technical-documentation-rfc",
        "study-guide-active-recall",
        "research-synthesis-multihop",
        "critical-epistemic-audit",
        "executive-briefing-report",
        "software-architecture-code",
        "mathematical-formal-proof",
        "experimental-methodology-lab",
        "pedagogical-lesson-plan",
        "project-roadmap-planning",
        "comparative-matrix-benchmark",
        "knowledge-enrichment-24h",
    }
)


@lru_cache(maxsize=1)
def load_agent_skills() -> tuple[AgentSkill, ...]:
    skills_dir = resolve_skills_dir()
    if not skills_dir.is_dir():
        return ()

    loaded: list[AgentSkill] = []
    seen_ids: set[str] = set()
    for path in sorted(skills_dir.rglob("*.md")):
        if path.name.lower() in {"readme.md", "index.md", "catalog.md"}:
            continue
        try:
            raw = path.read_text(encoding="utf-8")
        except OSError:
            continue
        meta, body = _parse_frontmatter(raw)
        if not body:
            continue
        skill_id = str(meta.get("id") or path.stem).strip()
        if skill_id in seen_ids:
            continue
        seen_ids.add(skill_id)
        name = str(meta.get("name") or skill_id.replace("-", " ").title()).strip()
        category = str(meta.get("category") or "general").strip()
        description = str(meta.get("description") or "").strip()
        triggers = tuple(
            str(item).strip()
            for item in (meta.get("triggers") or [])
            if str(item).strip()
        )
        keywords = tuple(
            str(item).strip()
            for item in (meta.get("keywords") or [])
            if str(item).strip()
        )
        task_types = tuple(
            str(item).strip()
            for item in (meta.get("task_types") or ["ask"])
            if str(item).strip()
        )
        max_tokens = int(meta.get("recommended_max_tokens") or 3072)
        priority_tier = int(
            meta.get("priority_tier") or (1 if skill_id in CORE_SKILL_IDS else 2)
        )
        norm_triggers = tuple(
            t for t in (_normalize_text(item) for item in triggers) if t
        )
        phrase_kws: list[str] = []
        token_kws: set[str] = set()
        for kw in keywords:
            nkw = _normalize_text(kw)
            if not nkw:
                continue
            if " " in nkw:
                phrase_kws.append(nkw)
            else:
                token_kws.add(nkw)
        rel_path = path.relative_to(skills_dir).as_posix()
        loaded.append(
            AgentSkill(
                id=skill_id,
                name=name,
                category=category,
                description=description,
                triggers=triggers,
                keywords=keywords,
                task_types=task_types,
                recommended_max_tokens=max_tokens,
                file_name=path.name,
                relative_path=rel_path,
                priority_tier=priority_tier,
                instructions=body,
                normalized_triggers=norm_triggers,
                normalized_phrase_keywords=tuple(phrase_kws),
                normalized_token_keywords=frozenset(token_kws),
            )
        )
    return tuple(loaded)


def list_agent_skills() -> list[dict[str, Any]]:
    return [skill.to_summary() for skill in load_agent_skills()]


def select_skills_for_context(
    query: str,
    *,
    task_type: str = "ask",
    max_skills: int = 2,
) -> list[AgentSkill]:
    """Automatically select and rank agent skills that match the user's request context."""
    skills = load_agent_skills()
    if not skills:
        return []

    normalized_query = _normalize_text(query)
    query_tokens = _tokenize_normalized(query)
    scored: list[tuple[int, int, str, AgentSkill]] = []

    for skill in skills:
        score = 0
        if (
            task_type in {"enrich_node", "research_graph", "validate_web"}
            and skill.id == "knowledge-enrichment-24h"
        ):
            score += 50

        trigger_hits = 0
        for norm_trigger in skill.normalized_triggers:
            if norm_trigger in normalized_query:
                trigger_hits += 1
                score += 14 + min(len(norm_trigger.split()), 4) * 3

        matched_keywords = len(skill.normalized_token_keywords & query_tokens)
        for norm_kw in skill.normalized_phrase_keywords:
            if norm_kw in normalized_query:
                matched_keywords += 2

        if matched_keywords > 0:
            score += matched_keywords * 3

        if trigger_hits > 0 and skill.priority_tier == 1:
            score += 6

        if score >= 6:
            scored.append((-score, skill.priority_tier, skill.id, skill))

    scored.sort(key=lambda item: (item[0], item[1], item[2]))
    return [item[3] for item in scored[: max(1, max_skills)]]


def format_active_skills_prompt(skills: list[AgentSkill]) -> str:
    if not skills:
        return ""
    blocks = [
        "ACTIVE CONTEXTUAL BERRYBRAIN SKILLS (automatically triggered by user intent):",
        "Follow the structural, methodological, and formatting rules of the active skill(s) below,",
        "while strictly grounding every factual claim in the provided Vault Notes, Graph Evidence, and 24h Web-Validated Sources using [title](bbref:<evidenceId>) citations.",
    ]
    for skill in skills:
        blocks.append(
            f"\n--- BEGIN SKILL: {skill.name} ({skill.file_name}) ---\n"
            f"{skill.instructions}\n"
            f"--- END SKILL: {skill.name} ---"
        )
    return "\n".join(blocks)
