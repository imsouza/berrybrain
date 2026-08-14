from __future__ import annotations

import json
import secrets
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from sqlalchemy.orm import Session

from berrybrain_api.models import (
    ArtifactEvaluationRecord,
    JudgeVerdictRecord,
    SettingRecord,
)


class JudgeMode(StrEnum):
    DETERMINISTIC = "deterministic"
    SINGLE_MODEL = "single_model"
    COMMITTEE = "committee"


HIGH_IMPACT_ARTIFACT_TYPES = ("node", "edge", "insight")

MIN_COMMITTEE_SIZE = 2
MAX_COMMITTEE_SIZE = 5
DEFAULT_COMMITTEE_SIZE = 3

DEFAULT_JUDGE_ROLES: tuple[dict[str, str], ...] = (
    {
        "role": "faithfulness",
        "focus": (
            "Verify that every material claim is entailed by the cited source evidence "
            "and that citations identify the supporting source."
        ),
    },
    {
        "role": "relevance",
        "focus": (
            "Verify semantic relevance, usefulness, ontology fit, and whether the "
            "artifact belongs in this knowledge context."
        ),
    },
    {
        "role": "contradiction",
        "focus": (
            "Detect contradictions, unsupported inference, ambiguous cross-domain links, "
            "and relationships created from incidental shared words."
        ),
    },
    {
        "role": "source_quality",
        "focus": (
            "Assess source quality, evidence coverage, provenance completeness, and "
            "whether the evidence is sufficient for the claimed confidence."
        ),
    },
    {
        "role": "ontology_consistency",
        "focus": (
            "Verify node class, relationship direction, ontology property, naming, and "
            "consistency with neighboring graph artifacts."
        ),
    },
)

SETTING_JUDGE_MODE = "judge_mode"
SETTING_JUDGE_COMMITTEE_CONFIG = "judge_committee_config"
SETTING_JUDGE_CONSENT = "judge_committee_consent_at"
SETTING_JUDGE_COMMITTEE_SIZE = "judge_committee_size"

DEFAULT_COMMITTEE_CONFIG: list[dict[str, str]] = [
    {
        "slot": f"judge-{index + 1}",
        "provider": "",
        "model": "",
        **role,
    }
    for index, role in enumerate(DEFAULT_JUDGE_ROLES[:DEFAULT_COMMITTEE_SIZE])
]


@dataclass
class JudgeConfig:
    mode: JudgeMode = JudgeMode.SINGLE_MODEL
    committee: list[dict[str, str]] = field(
        default_factory=lambda: list(DEFAULT_COMMITTEE_CONFIG)
    )
    committee_size: int = DEFAULT_COMMITTEE_SIZE
    consent_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode.value,
            "committee": list(self.committee),
            "committee_size": self.committee_size,
            "consent_at": self.consent_at,
        }


def load_judge_config(session: Session) -> JudgeConfig:
    mode_row = (
        session.query(SettingRecord)
        .filter(SettingRecord.key == SETTING_JUDGE_MODE)
        .first()
    )
    cfg_row = (
        session.query(SettingRecord)
        .filter(SettingRecord.key == SETTING_JUDGE_COMMITTEE_CONFIG)
        .first()
    )
    consent_row = (
        session.query(SettingRecord)
        .filter(SettingRecord.key == SETTING_JUDGE_CONSENT)
        .first()
    )
    size_row = (
        session.query(SettingRecord)
        .filter(SettingRecord.key == SETTING_JUDGE_COMMITTEE_SIZE)
        .first()
    )

    mode = JudgeMode(mode_row.value) if mode_row else JudgeMode.SINGLE_MODEL
    committee = (
        json.loads(cfg_row.value)
        if cfg_row and cfg_row.value
        else list(DEFAULT_COMMITTEE_CONFIG)
    )
    consent = consent_row.value if consent_row else None
    try:
        committee_size = max(
            MIN_COMMITTEE_SIZE,
            min(MAX_COMMITTEE_SIZE, int(size_row.value)),
        )
    except (AttributeError, TypeError, ValueError):
        committee_size = DEFAULT_COMMITTEE_SIZE
    return JudgeConfig(
        mode=mode,
        committee=committee,
        committee_size=committee_size,
        consent_at=consent,
    )


def save_judge_config(session: Session, cfg: JudgeConfig) -> None:
    for key, value in (
        (SETTING_JUDGE_MODE, cfg.mode.value),
        (SETTING_JUDGE_COMMITTEE_CONFIG, json.dumps(cfg.committee)),
        (SETTING_JUDGE_COMMITTEE_SIZE, str(cfg.committee_size)),
        (SETTING_JUDGE_CONSENT, cfg.consent_at or ""),
    ):
        row = session.query(SettingRecord).filter(SettingRecord.key == key).first()
        if row:
            row.value = value
            row.updated_at = datetime.now(UTC).replace(tzinfo=None)
        else:
            session.add(SettingRecord(key=key, value=value))
    session.commit()


def is_high_impact(artifact_type: str) -> bool:
    return artifact_type in HIGH_IMPACT_ARTIFACT_TYPES


def should_use_committee(cfg: JudgeConfig, artifact_type: str) -> bool:
    return cfg.mode == JudgeMode.COMMITTEE and is_high_impact(artifact_type)


def generator_model_blocked_in_committee(
    generator_model: str, committee: list[dict[str, str]]
) -> list[str]:
    gen = (generator_model or "").strip().lower()
    if not gen:
        return []
    return [
        j["slot"]
        for j in committee
        if (j.get("model", "") or "").strip().lower() == gen
    ]


def eligible_committee_slots(
    committee: list[dict[str, str]], generator_model: str = ""
) -> list[dict[str, str]]:
    generator = (generator_model or "").strip().casefold()
    seen: set[tuple[str, str]] = set()
    eligible: list[dict[str, str]] = []
    for item in committee:
        provider = str(item.get("provider") or "").strip()
        model = str(item.get("model") or "").strip()
        slot = str(item.get("slot") or "").strip()
        identity = (provider.casefold(), model.casefold())
        if not provider or not model or not slot or identity in seen:
            continue
        if generator and model.casefold() == generator:
            continue
        seen.add(identity)
        eligible.append(
            {
                "slot": slot,
                "provider": provider,
                "model": model,
                "role": str(item.get("role") or "general").strip()[:80],
                "focus": str(item.get("focus") or "").strip()[:1000],
            }
        )
    return eligible


def recommend_committee(
    *,
    provider: str,
    available_models: list[str],
    generator_model: str = "",
    primary_judge_model: str = "",
    committee_size: int = DEFAULT_COMMITTEE_SIZE,
) -> list[dict[str, str]]:
    """Assign distinct, available chat models to evidence-oriented Judge roles."""
    size = max(MIN_COMMITTEE_SIZE, min(MAX_COMMITTEE_SIZE, committee_size))
    ordered = judge_model_candidates(
        available_models=available_models,
        generator_model=generator_model,
        primary_judge_model=primary_judge_model,
    )

    return [
        {
            "slot": f"judge-{index + 1}",
            "provider": provider.strip(),
            "model": model,
            **DEFAULT_JUDGE_ROLES[index],
        }
        for index, model in enumerate(ordered[:size])
    ]


def judge_model_candidates(
    *,
    available_models: list[str],
    generator_model: str = "",
    primary_judge_model: str = "",
    preferred_models: list[str] | None = None,
) -> list[str]:
    """Rank text-generation candidates and interleave model families."""
    generator = generator_model.strip().casefold()
    excluded_fragments = (
        "code",
        "embed",
        "rerank",
        "moderation",
        "guard",
        "safety",
        "reward",
        "vision",
        "-vl",
        "vl-",
        "omni",
        "parse",
        "ocr",
        "whisper",
        "transcri",
        "speech",
        "audio",
        "tts",
        "image",
    )
    normalized: dict[str, str] = {}
    for raw_model in available_models:
        model = str(raw_model or "").strip()
        key = model.casefold()
        if (
            not model
            or key == generator
            or any(fragment in key for fragment in excluded_fragments)
        ):
            continue
        normalized.setdefault(key, model)

    preferred = primary_judge_model.strip()
    priority_markers = (
        "judge",
        "nemotron",
        "reasoning",
        "reason",
        "deepseek",
        "llama",
        "mistral",
        "qwen",
        "gemma",
        "instruct",
        "chat",
    )
    preferred_order = [*(preferred_models or []), preferred]
    ordered: list[str] = []
    for item in preferred_order:
        key = item.strip().casefold()
        if key in normalized:
            ordered.append(normalized.pop(key))

    ranked = sorted(
        normalized.values(),
        key=lambda model: (
            min(
                (
                    index
                    for index, marker in enumerate(priority_markers)
                    if marker in model.casefold()
                ),
                default=len(priority_markers),
            ),
            model.casefold(),
        ),
    )
    by_family: dict[str, list[str]] = {}
    for model in ranked:
        family = model.split("/", 1)[0].casefold()
        by_family.setdefault(family, []).append(model)
    while by_family:
        for family in list(by_family):
            ordered.append(by_family[family].pop(0))
            if not by_family[family]:
                del by_family[family]

    return ordered


def configure_provider_committee(
    session: Session,
    *,
    provider: str,
    available_models: list[str],
    generator_model: str,
    primary_judge_model: str,
) -> JudgeConfig:
    """Keep a valid custom committee or create provider-aware defaults."""
    cfg = load_judge_config(session)
    available = {str(model).strip().casefold() for model in available_models}
    current = eligible_committee_slots(cfg.committee, generator_model)
    current_is_usable = (
        len(current) >= cfg.committee_size
        and all(item["provider"] == provider for item in current)
        and all(item["model"].casefold() in available for item in current)
    )
    if current_is_usable:
        cfg.committee = current[: cfg.committee_size]
    else:
        cfg.committee_size = DEFAULT_COMMITTEE_SIZE
        cfg.committee = recommend_committee(
            provider=provider,
            available_models=available_models,
            generator_model=generator_model,
            primary_judge_model=primary_judge_model,
            committee_size=cfg.committee_size,
        )

    if len(cfg.committee) >= MIN_COMMITTEE_SIZE:
        cfg.committee_size = len(cfg.committee)
        cfg.mode = JudgeMode.COMMITTEE
        if not cfg.consent_at:
            cfg.consent_at = datetime.now(UTC).isoformat()
    else:
        cfg.mode = JudgeMode.SINGLE_MODEL
    save_judge_config(session, cfg)
    return cfg


def tally_verdicts(verdicts: list[str]) -> str:
    resolved = [
        verdict for verdict in verdicts if verdict in {"passed", "review", "rejected"}
    ]
    if not resolved:
        return "error"
    counts: dict[str, int] = {}
    for v in resolved:
        counts[v] = counts.get(v, 0) + 1
    # Unanimous verdicts
    if counts.get("passed", 0) == len(resolved):
        return "passed"
    if counts.get("rejected", 0) == len(resolved):
        return "rejected"
    # Any review present
    if counts.get("review", 0) > 0:
        return "review"
    # Majority check (tie -> review)
    majority = max(counts.values())
    winners = [v for v, c in counts.items() if c == majority]
    if len(winners) == 1 and majority * 2 > len(resolved):
        return winners[0]
    return "review"  # disagreement fails-closed-soft


def disagreement(verdicts: list[str]) -> bool:
    return len({v for v in verdicts if v in {"passed", "review", "rejected"}}) > 1


def aggregate_score(scores: list[float]) -> float:
    if not scores:
        return 0.0
    return round(sum(scores) / len(scores), 4)


def new_committee_id() -> str:
    return secrets.token_hex(16)


def persist_committee_run(
    session: Session,
    *,
    artifact_type: str,
    artifact_id: int,
    verdicts: list[dict[str, Any]],
    enforcing: bool,
) -> ArtifactEvaluationRecord:
    committee_id = new_committee_id()
    verdict_strings = [v.get("verdict", "error") for v in verdicts]
    summary = tally_verdicts(verdict_strings)
    if enforcing and disagreement(verdict_strings):
        summary = "review"
    score = aggregate_score(
        [
            float(v.get("score", 0.0))
            for v in verdicts
            if v.get("verdict") in {"passed", "review", "rejected"}
        ]
    )

    for v in verdicts:
        session.add(
            JudgeVerdictRecord(
                committee_id=committee_id,
                artifact_type=artifact_type,
                artifact_id=artifact_id,
                judge_slot=v.get("slot", ""),
                provider=v.get("provider", ""),
                model=v.get("model", ""),
                verdict=v.get("verdict", "error"),
                score=float(v.get("score", 0.0)),
                rubric=json.dumps(v.get("rubric", {})),
                reasoning=v.get("reasoning", ""),
                latency_ms=int(v.get("latency_ms", 0)),
                is_summary=0,
            )
        )

    summary_record = ArtifactEvaluationRecord(
        artifact_type=artifact_type,
        artifact_id=artifact_id,
        verdict=summary,
        score=score,
        rubric=json.dumps({"committee_id": committee_id, "enforcing": enforcing}),
        reasoning="committee run",
        evidence_used="[]",
        provider="committee",
        model="committee",
        prompt_version="artifact-judge.v2.md",
    )
    session.add(summary_record)
    session.commit()
    session.refresh(summary_record)

    session.add(
        JudgeVerdictRecord(
            committee_id=committee_id,
            artifact_type=artifact_type,
            artifact_id=artifact_id,
            judge_slot="summary",
            provider="committee",
            model="committee",
            verdict=summary,
            score=score,
            rubric=summary_record.rubric,
            reasoning=summary_record.reasoning,
            latency_ms=0,
            is_summary=1,
        )
    )
    session.commit()
    return summary_record
