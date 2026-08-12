from __future__ import annotations

import argparse
import json
import statistics
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

CAPABILITIES = (
    "capture-and-extraction",
    "durable-semantic-memory",
    "retrieval-and-grounded-inference",
    "knowledge-graph-and-ontology",
    "insights-and-continuous-agents",
    "transparency-confidence-and-user-control",
    "performance-efficiency-and-scalability",
    "reliability-and-recoverability",
    "security-privacy-and-safety",
    "interaction-quality-and-accessibility",
    "maintainability-architecture-and-governance",
)


@dataclass(frozen=True)
class CapabilityAssessment:
    capability: str
    level: int
    evidence_count: int
    current_evidence_count: int
    rationale: str


@dataclass(frozen=True)
class MaturityAssessment:
    schema_version: str
    assessed_at: str
    minimum_level: int
    median_level: float
    readiness: str
    mandatory_gates_passed: bool
    capabilities: tuple[CapabilityAssessment, ...]
    rejected_evidence: tuple[dict[str, str], ...]


def _parse_timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def assess_maturity(
    evidence: list[dict[str, Any]],
    *,
    repository_root: Path,
    mandatory_gates_passed: bool,
    now: datetime | None = None,
) -> MaturityAssessment:
    now = now or datetime.now(UTC)
    accepted: dict[str, list[dict[str, Any]]] = {name: [] for name in CAPABILITIES}
    rejected: list[dict[str, str]] = []
    for item in evidence:
        capability = str(item.get("capability") or "")
        level = int(item.get("level") or 0)
        artifact = str(item.get("artifact") or "")
        classification = str(item.get("classification") or "")
        reason = ""
        if capability not in accepted:
            reason = "unknown capability"
        elif level not in range(1, 6):
            reason = "level must be between 1 and 5"
        elif not artifact or not (repository_root / artifact).is_file():
            reason = "artifact is missing"
        elif classification not in {
            "implementation",
            "ci-regression",
            "representative",
            "independent-comparison",
            "field-study",
        }:
            reason = "unsupported evidence classification"
        elif level >= 4 and classification not in {
            "independent-comparison",
            "field-study",
        }:
            reason = "Levels 4-5 require independent or field evidence"
        elif level == 5 and classification != "field-study":
            reason = "Level 5 requires field-study evidence"
        else:
            expires_at = str(item.get("expiresAt") or "")
            if expires_at and _parse_timestamp(expires_at) < now:
                reason = "evidence is stale"
        if reason:
            rejected.append(
                {"capability": capability, "artifact": artifact, "reason": reason}
            )
        else:
            accepted[capability].append(item)

    assessments: list[CapabilityAssessment] = []
    for capability in CAPABILITIES:
        candidates = accepted[capability]
        level = max((int(item["level"]) for item in candidates), default=0)
        assessments.append(
            CapabilityAssessment(
                capability=capability,
                level=level,
                evidence_count=sum(
                    1 for item in evidence if item.get("capability") == capability
                ),
                current_evidence_count=len(candidates),
                rationale=(
                    f"Highest current evidence level is {level}."
                    if candidates
                    else "No current verifiable evidence."
                ),
            )
        )
    levels = [item.level for item in assessments]
    minimum = min(levels)
    median = statistics.median(levels)
    if not mandatory_gates_passed:
        readiness = "blocked"
    elif minimum >= 4:
        readiness = "independently-validated"
    elif minimum >= 3:
        readiness = "representative-evidence"
    elif minimum >= 2:
        readiness = "engineering-evidence"
    else:
        readiness = "incomplete-evidence"
    return MaturityAssessment(
        schema_version="berrybrain-maturity.v3",
        assessed_at=now.isoformat(),
        minimum_level=minimum,
        median_level=median,
        readiness=readiness,
        mandatory_gates_passed=mandatory_gates_passed,
        capabilities=tuple(assessments),
        rejected_evidence=tuple(rejected),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate evidence-based Maturity V3.")
    parser.add_argument("--evidence", required=True)
    parser.add_argument("--repository-root", default=".")
    parser.add_argument("--mandatory-gates-passed", action="store_true")
    parser.add_argument("--output", default="reports/maturity-v3.json")
    args = parser.parse_args()
    evidence = json.loads(Path(args.evidence).read_text(encoding="utf-8"))
    if not isinstance(evidence, list):
        raise ValueError("evidence input must be a JSON array")
    assessment = assess_maturity(
        evidence,
        repository_root=Path(args.repository_root),
        mandatory_gates_passed=args.mandatory_gates_passed,
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(asdict(assessment), indent=2, sort_keys=True) + "\n")
    print(json.dumps(asdict(assessment), indent=2, sort_keys=True))
    return 0 if assessment.readiness != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
