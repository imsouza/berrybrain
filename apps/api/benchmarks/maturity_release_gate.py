from __future__ import annotations

import json
from dataclasses import asdict, dataclass

from benchmarks.cognitive_maturity_benchmark import (
    run_benchmark as run_cognitive_benchmark,
)
from benchmarks.insight_usefulness_benchmark import (
    run_benchmark as run_insight_benchmark,
)
from benchmarks.graph_performance_benchmark import (
    run_benchmark as run_graph_performance_benchmark,
)
from benchmarks.semantic_search_benchmark import (
    run_benchmark as run_semantic_benchmark,
)


@dataclass(frozen=True)
class MaturityReleaseGate:
    passed: bool
    semantic: dict[str, object]
    insights: dict[str, object]
    cognition: dict[str, object]
    graph_performance: dict[str, object]
    failed_gates: tuple[str, ...]


def run_release_gate() -> MaturityReleaseGate:
    semantic = run_semantic_benchmark()
    insights = run_insight_benchmark()
    cognition = run_cognitive_benchmark()
    graph_performance = run_graph_performance_benchmark()
    failed: list[str] = []

    semantic_gates = {
        "semantic.recall_at_10": semantic.recall_at_10 >= 0.85,
        "semantic.mrr": semantic.mean_reciprocal_rank >= 0.75,
        "semantic.ndcg_at_10": semantic.ndcg_at_10 >= 0.85,
        "semantic.negative_rejection": semantic.negative_rejection_rate == 1.0,
        "semantic.relationship_recall": semantic.relationship_recall_at_10 == 1.0,
        "semantic.latency_p95": semantic.latency_p95_ms <= 500,
        "semantic.indexing_coverage": semantic.indexing_coverage >= 0.995,
        "semantic.fresh_evidence": semantic.stale_evidence_count == 0,
    }
    failed.extend(name for name, passed in semantic_gates.items() if not passed)
    if not insights.meets_target:
        failed.append("insights.expert_labeled_usefulness")
    if not cognition.meets_targets:
        failed.append("cognition.graph_integrity_and_provenance")
    if not graph_performance.meets_targets:
        failed.append("graph.performance_budget")

    return MaturityReleaseGate(
        passed=not failed,
        semantic=asdict(semantic),
        insights=asdict(insights),
        cognition=asdict(cognition),
        graph_performance=asdict(graph_performance),
        failed_gates=tuple(failed),
    )


def main() -> int:
    result = run_release_gate()
    print(json.dumps(asdict(result), indent=2, sort_keys=True))
    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
