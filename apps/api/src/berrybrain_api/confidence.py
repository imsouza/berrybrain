from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from statistics import NormalDist
from typing import Any

TOKEN_RE = re.compile(r"[\w-]{3,}", flags=re.UNICODE)


@dataclass(frozen=True)
class ConfidenceSignal:
    score: float
    source: str


@dataclass(frozen=True)
class ConfidenceEstimate:
    score: float | None
    lower: float | None
    upper: float | None
    sample_size: int
    method: str
    factors: tuple[str, ...]
    level: float = 0.95

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def serialize_estimate(estimate: ConfidenceEstimate) -> dict[str, Any]:
    return {
        "score": estimate.score,
        "lower": estimate.lower,
        "upper": estimate.upper,
        "level": estimate.level,
        "sampleSize": estimate.sample_size,
        "method": estimate.method,
        "factors": list(estimate.factors),
    }


def estimate_confidence(
    signals: Iterable[ConfidenceSignal | tuple[float, str]],
    *,
    level: float = 0.95,
) -> ConfidenceEstimate:
    """Estimate a Jeffreys-smoothed mean and Wilson interval from independent signals."""
    observations: list[ConfidenceSignal] = []
    seen_sources: set[str] = set()
    for item in signals:
        signal = item if isinstance(item, ConfidenceSignal) else ConfidenceSignal(*item)
        if signal.source in seen_sources or not math.isfinite(signal.score):
            continue
        seen_sources.add(signal.source)
        observations.append(
            ConfidenceSignal(max(0.0, min(1.0, float(signal.score))), signal.source)
        )

    if not observations:
        return ConfidenceEstimate(None, None, None, 0, "unavailable", ())

    sample_size = len(observations)
    observed_mean = sum(item.score for item in observations) / sample_size
    z = NormalDist().inv_cdf(0.5 + level / 2)
    denominator = 1 + (z * z / sample_size)
    center = (observed_mean + (z * z / (2 * sample_size))) / denominator
    margin = (
        z
        * math.sqrt(
            (observed_mean * (1 - observed_mean) / sample_size)
            + (z * z / (4 * sample_size * sample_size))
        )
        / denominator
    )
    posterior_mean = (
        sum(item.score for item in observations) + 0.5
    ) / (sample_size + 1)
    return ConfidenceEstimate(
        round(posterior_mean, 6),
        round(max(0.0, center - margin), 6),
        round(min(1.0, center + margin), 6),
        sample_size,
        "jeffreys-wilson-evidence-v2",
        tuple(item.source for item in observations),
        level,
    )


def estimate_connection_confidence(
    *,
    reason: str,
    evidence: Iterable[Any],
    model_score: int | float | None = None,
    model_source: str = "connection-model",
) -> ConfidenceEstimate:
    """Calculate connection confidence from independent evidence and model signals."""
    evidence_items = [item for item in evidence if str(item).strip()]
    signals = [
        ConfidenceSignal(
            1.0,
            "connection-evidence:"
            + hashlib.sha256(
                json.dumps(item, sort_keys=True, ensure_ascii=False).encode()
            ).hexdigest()[:16],
        )
        for item in evidence_items
    ]
    coverage = evidence_coverage_signal([reason], evidence_items)
    if coverage is not None:
        signals.append(coverage)
    if model_score is not None:
        try:
            normalized_score = float(model_score)
        except (TypeError, ValueError):
            normalized_score = math.nan
        if math.isfinite(normalized_score):
            normalized_score = (
                normalized_score / 100 if normalized_score > 1 else normalized_score
            )
            signals.append(ConfidenceSignal(normalized_score, f"model:{model_source}"))
    return estimate_confidence(signals)


def persist_confidence(target: Any, estimate: ConfidenceEstimate) -> None:
    target.confidence = estimate.score if estimate.score is not None else 0.0
    target.confidence_lower = estimate.lower
    target.confidence_upper = estimate.upper
    target.confidence_sample_size = estimate.sample_size
    target.confidence_method = estimate.method
    target.confidence_factors = json.dumps(list(estimate.factors), ensure_ascii=False)
    target.confidence_updated_at = datetime.now(UTC)


def persist_percentage_confidence(target: Any, estimate: ConfidenceEstimate) -> None:
    """Persist an estimate for legacy records whose score column is an integer percent."""
    target.confidence = round((estimate.score or 0.0) * 100)
    target.confidence_lower = estimate.lower
    target.confidence_upper = estimate.upper
    target.confidence_sample_size = estimate.sample_size
    target.confidence_method = estimate.method
    target.confidence_factors = json.dumps(list(estimate.factors), ensure_ascii=False)
    target.confidence_updated_at = datetime.now(UTC)


def evidence_coverage_signal(
    claims: Iterable[str], evidence: Iterable[Any]
) -> ConfidenceSignal | None:
    claim_tokens = {
        token.casefold()
        for claim in claims
        for token in TOKEN_RE.findall(str(claim or ""))
    }
    if not claim_tokens:
        return None
    evidence_tokens = {
        token.casefold()
        for item in evidence
        for token in TOKEN_RE.findall(
            json.dumps(item, ensure_ascii=False)
            if isinstance(item, dict | list)
            else str(item or "")
        )
    }
    coverage = len(claim_tokens & evidence_tokens) / len(claim_tokens)
    return ConfidenceSignal(coverage, "evidence-claim-token-coverage")


def serialize_confidence(target: Any) -> dict[str, Any]:
    sample_size = int(getattr(target, "confidence_sample_size", 0) or 0)
    score = getattr(target, "confidence", None) if sample_size else None
    return {
        "score": score,
        "lower": getattr(target, "confidence_lower", None),
        "upper": getattr(target, "confidence_upper", None),
        "level": 0.95,
        "sampleSize": sample_size,
        "method": getattr(target, "confidence_method", "unavailable") or "unavailable",
        "factors": _json_list(getattr(target, "confidence_factors", "[]")),
        "computedAt": (
            target.confidence_updated_at.isoformat()
            if getattr(target, "confidence_updated_at", None)
            else None
        ),
    }


def serialize_percentage_confidence(target: Any) -> dict[str, Any]:
    payload = serialize_confidence(target)
    score = payload.get("score")
    payload["score"] = (float(score) / 100) if isinstance(score, int | float) else None
    return payload


def _json_list(raw: str) -> list[Any]:
    try:
        parsed = json.loads(raw or "[]")
    except (TypeError, json.JSONDecodeError):
        return []
    return parsed if isinstance(parsed, list) else []
