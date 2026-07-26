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

SETTING_JUDGE_MODE = "judge_mode"
SETTING_JUDGE_COMMITTEE_CONFIG = "judge_committee_config"
SETTING_JUDGE_CONSENT = "judge_committee_consent_at"

DEFAULT_COMMITTEE_CONFIG: list[dict[str, str]] = [
    {"slot": "alpha", "provider": "", "model": ""},
    {"slot": "beta", "provider": "", "model": ""},
    {"slot": "gamma", "provider": "", "model": ""},
]


@dataclass
class JudgeConfig:
    mode: JudgeMode = JudgeMode.SINGLE_MODEL
    committee: list[dict[str, str]] = field(
        default_factory=lambda: list(DEFAULT_COMMITTEE_CONFIG)
    )
    consent_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode.value,
            "committee": list(self.committee),
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

    mode = JudgeMode(mode_row.value) if mode_row else JudgeMode.SINGLE_MODEL
    committee = (
        json.loads(cfg_row.value)
        if cfg_row and cfg_row.value
        else list(DEFAULT_COMMITTEE_CONFIG)
    )
    consent = consent_row.value if consent_row else None
    return JudgeConfig(mode=mode, committee=committee, consent_at=consent)


def save_judge_config(session: Session, cfg: JudgeConfig) -> None:
    for key, value in (
        (SETTING_JUDGE_MODE, cfg.mode.value),
        (SETTING_JUDGE_COMMITTEE_CONFIG, json.dumps(cfg.committee)),
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


def tally_verdicts(verdicts: list[str]) -> str:
    if not verdicts:
        return "error"
    counts: dict[str, int] = {}
    for v in verdicts:
        counts[v] = counts.get(v, 0) + 1
    # Unanimous verdicts
    if counts.get("passed", 0) == len(verdicts):
        return "passed"
    if counts.get("rejected", 0) == len(verdicts):
        return "rejected"
    # Any review present
    if counts.get("review", 0) > 0:
        return "review"
    # Majority check (tie -> review)
    majority = max(counts.values())
    winners = [v for v, c in counts.items() if c == majority]
    if len(winners) == 1 and majority * 2 > len(verdicts):
        return winners[0]
    return "review"  # disagreement fails-closed-soft


def disagreement(verdicts: list[str]) -> bool:
    return len({v for v in verdicts}) > 1


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
    score = aggregate_score([float(v.get("score", 0.0)) for v in verdicts])

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
        prompt_version="artifact-judge.v1.md",
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
