from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from statistics import variance
from typing import Any

TOKEN_RE = re.compile(r"[\w-]{3,}", flags=re.UNICODE)
CONFIDENCE_METHOD = "evidence-support-mean-v2"
# Canonical documents and namespaces are sources, not AI-derived hypotheses.
# An allowlist also keeps legacy or unknown graph types from exposing stale scores.
DERIVED_NODE_CONFIDENCE_TYPES = frozenset(
    {"concept", "entity", "topic", "context", "insight", "gap", "study_path"}
)
PROVENANCE_SIGNAL_PREFIXES = (
    "connection-evidence:",
    "edge-evidence:",
    "insight-evidence:",
    "node-evidence:",
    "related-note:",
    "source-attachment:",
    "source-note:",
)


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
    observations: tuple[ConfidenceSignal, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def parse_unit_confidence(value: object) -> float | None:
    """Reject missing, nonfinite, boolean and out-of-contract model scores."""
    if value is None or isinstance(value, bool):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return parsed if math.isfinite(parsed) and 0.0 <= parsed <= 1.0 else None


def serialize_estimate(estimate: ConfidenceEstimate) -> dict[str, Any]:
    return {
        "score": estimate.score,
        "lower": estimate.lower,
        "upper": estimate.upper,
        "level": estimate.level,
        "sampleSize": estimate.sample_size,
        "method": estimate.method,
        "factors": list(estimate.factors),
        "observations": [asdict(signal) for signal in estimate.observations],
        "interpretation": "evidence_support_not_probability",
    }


def estimate_confidence(
    signals: Iterable[ConfidenceSignal | tuple[float, str]],
    *,
    level: float = 0.95,
) -> ConfidenceEstimate:
    """Average distinct support signals, separately from descriptive uncertainty.

    Provenance identifiers establish traceability but are not correctness outcomes, so
    they never increase support by themselves. Heterogeneous signals are not proven
    independent or calibrated: neither the mean nor its interval is truth probability.
    """
    if not 0 < level < 1:
        raise ValueError("Confidence level must be between 0 and 1")
    observations: list[ConfidenceSignal] = []
    factors: list[str] = []
    seen_sources: set[str] = set()
    for item in signals:
        signal = item if isinstance(item, ConfidenceSignal) else ConfidenceSignal(*item)
        if (
            not isinstance(signal.source, str)
            or not signal.source.strip()
            or signal.source in seen_sources
            or isinstance(signal.score, bool)
            or not isinstance(signal.score, int | float)
            or not math.isfinite(signal.score)
            or not 0 <= signal.score <= 1
        ):
            continue
        seen_sources.add(signal.source)
        factors.append(signal.source)
        if signal.source.startswith(PROVENANCE_SIGNAL_PREFIXES):
            continue
        observations.append(ConfidenceSignal(float(signal.score), signal.source))

    if not observations:
        return ConfidenceEstimate(
            None, None, None, 0, "unavailable", tuple(factors), level
        )

    sample_size = len(observations)
    observed_mean = sum(item.score for item in observations) / sample_size
    if sample_size == 1:
        lower, upper = 0.0, 1.0
    else:
        delta = 1.0 - level
        empirical_variance = variance(item.score for item in observations)
        log_term = math.log(3.0 / delta)
        radius = (
            math.sqrt(2.0 * empirical_variance * log_term / sample_size)
            + 3.0 * log_term / sample_size
        )
        lower = max(0.0, observed_mean - radius)
        upper = min(1.0, observed_mean + radius)
    return ConfidenceEstimate(
        round(observed_mean, 6),
        round(lower, 6),
        round(upper, 6),
        sample_size,
        CONFIDENCE_METHOD,
        tuple(factors),
        level,
        tuple(observations),
    )


def estimate_connection_confidence(
    *,
    reason: str,
    evidence: Iterable[Any],
    model_score: int | float | None = None,
    model_source: str = "connection-model",
) -> ConfidenceEstimate:
    """Calculate descriptive support from evidence and model signals."""
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
    if model_score is not None and not isinstance(model_score, bool):
        try:
            normalized_score = float(model_score)
        except (TypeError, ValueError):
            normalized_score = math.nan
        if math.isfinite(normalized_score) and 0 <= normalized_score <= 100:
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
    target.confidence_factors = _stored_estimate(estimate)
    target.confidence_updated_at = datetime.now(UTC)


def persist_percentage_confidence(target: Any, estimate: ConfidenceEstimate) -> None:
    """Persist an estimate for legacy records whose score column is an integer percent."""
    target.confidence = round((estimate.score or 0.0) * 100)
    target.confidence_lower = estimate.lower
    target.confidence_upper = estimate.upper
    target.confidence_sample_size = estimate.sample_size
    target.confidence_method = estimate.method
    target.confidence_factors = _stored_estimate(estimate)
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
        for token in TOKEN_RE.findall(_evidence_text(item))
    }
    if not evidence_tokens:
        return None
    coverage = len(claim_tokens & evidence_tokens) / len(claim_tokens)
    return ConfidenceSignal(coverage, "evidence-claim-token-coverage")


def _evidence_text(item: Any) -> str:
    # IDs, hashes, paths and JSON keys establish provenance, not textual support.
    if isinstance(item, dict):
        return " ".join(
            _evidence_text(item[key])
            for key in ("excerpt", "text", "quote", "content")
            if key in item
        )
    if isinstance(item, list):
        return " ".join(_evidence_text(value) for value in item)
    return item if isinstance(item, str) else ""


def _stored_estimate(estimate: ConfidenceEstimate) -> str:
    return json.dumps(
        {
            "version": 2,
            "factors": list(estimate.factors),
            "observations": [asdict(signal) for signal in estimate.observations],
            "level": estimate.level,
        },
        ensure_ascii=False,
    )


def _stored_details(target: Any) -> dict[str, Any]:
    try:
        parsed = json.loads(getattr(target, "confidence_factors", "[]") or "[]")
    except (TypeError, json.JSONDecodeError):
        return {}
    if isinstance(parsed, list):
        return {"factors": parsed}
    if not isinstance(parsed, dict):
        return {}
    return {
        **parsed,
        "factors": parsed.get("factors")
        if isinstance(parsed.get("factors"), list)
        else [],
        "observations": parsed.get("observations")
        if isinstance(parsed.get("observations"), list)
        else [],
    }


def stored_confidence_signals(target: Any) -> list[ConfidenceSignal]:
    """Read actual observations, never reinterpret a legacy interval midpoint."""
    details = _stored_details(target)
    signals = [
        ConfidenceSignal(1.0, source)
        for source in details.get("factors", [])
        if isinstance(source, str) and source.startswith(PROVENANCE_SIGNAL_PREFIXES)
    ]
    for item in details.get("observations", []):
        if (
            isinstance(item, dict)
            and "score" in item
            and isinstance(item.get("source"), str)
        ):
            signals.append(ConfidenceSignal(item["score"], item["source"]))
    return signals


def persist_judge_confidence(
    target: Any, score: float | None, *, percentage: bool = False
) -> None:
    """Replace the current judge observation; retries are not new evidence.

    None means no measured verdict (e.g. policy-only mode or evaluator error),
    not a negative score. A genuine zero verdict remains a scored observation.
    """
    if _is_graph_node(target) and not node_confidence_applicable(target.type):
        return
    signals = [
        signal
        for signal in stored_confidence_signals(target)
        if not signal.source.startswith("judge:")
    ]
    if score is not None:
        signals.append(ConfidenceSignal(score, "judge:quality-score"))
    persist = persist_percentage_confidence if percentage else persist_confidence
    persist(target, estimate_confidence(signals))


def serialize_confidence(target: Any, *, compact: bool = False) -> dict[str, Any]:
    if _is_graph_node(target) and not node_confidence_applicable(target.type):
        return {
            "score": None,
            "lower": None,
            "upper": None,
            "sampleSize": 0,
            "method": "not_applicable",
            "applicability": "not_applicable",
            "needsRecalculation": False,
            **(
                {}
                if compact
                else {
                    "factors": [],
                    "observations": [],
                    "interpretation": "not_applicable",
                }
            ),
            "computedAt": None,
        }
    sample_size = int(getattr(target, "confidence_sample_size", 0) or 0)
    score = getattr(target, "confidence", None) if sample_size else None
    details = {} if compact else _stored_details(target)
    return {
        "score": score,
        "lower": getattr(target, "confidence_lower", None),
        "upper": getattr(target, "confidence_upper", None),
        **({"level": details.get("level", 0.95)} if not compact else {}),
        "sampleSize": sample_size,
        "method": getattr(target, "confidence_method", "unavailable") or "unavailable",
        "needsRecalculation": getattr(target, "confidence_method", "")
        == "empirical-bernstein-bounded-signals-v1",
        **(
            {}
            if compact
            else {
                "factors": details.get("factors", []),
                "observations": details.get("observations", []),
                "interpretation": "evidence_support_not_probability",
            }
        ),
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


def node_confidence_applicable(node_type: str) -> bool:
    return str(node_type or "").strip().lower() in DERIVED_NODE_CONFIDENCE_TYPES


def active_node_confidence(node: Any) -> float | None:
    if not node_confidence_applicable(getattr(node, "type", "")):
        return None
    return node.confidence if getattr(node, "confidence_sample_size", 0) else None


def _is_graph_node(target: Any) -> bool:
    return getattr(target, "__tablename__", None) == "graph_nodes"


def _json_list(raw: str) -> list[Any]:
    try:
        parsed = json.loads(raw or "[]")
    except (TypeError, json.JSONDecodeError):
        return []
    return parsed if isinstance(parsed, list) else []
