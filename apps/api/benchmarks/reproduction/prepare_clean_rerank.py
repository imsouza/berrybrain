"""Audit historical-vs-clean source rankings and make a depth-10 clean report.

The source rerun already computed depth 40. This script changes no scores:
it slices those exact rankings to ten documents for the four-route reranker.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--clean", type=Path, required=True)
    parser.add_argument("--historical", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--audit", type=Path, required=True)
    args = parser.parse_args()

    clean = json.loads(args.clean.read_text())
    historical = json.loads(args.historical.read_text())
    assert clean["status"] == historical["status"] == "completed"
    assert clean["protocol"]["rankingDepth"] == 40
    assert historical["protocol"]["rankingDepth"] == 10
    for key in ("corpus", "queries", "openie"):
        assert clean["inputs"][key]["sha256"] == historical["inputs"][key]["sha256"]
    assert clean["protocol"]["embeddingModelSha256"] == historical["protocol"]["embeddingModelSha256"]
    assert clean["git"]["dirty"] is False

    ranking_audit = {}
    for method, previous in historical["retrieval"]["rankings"].items():
        current = clean["retrieval"]["rankings"][method]
        assert set(previous) == set(current)
        ranking_audit[method] = {
            "sameOrderedTop10Questions": sum(previous[q] == current[q][:10] for q in previous),
            "sameTop10SetQuestions": sum(set(previous[q]) == set(current[q][:10]) for q in previous),
            "missingHistoricalTop10Items": sum(len(set(previous[q]) - set(current[q][:10])) for q in previous),
            "questionCount": len(previous),
        }
        clean["retrieval"]["rankings"][method] = {q: ranking[:10] for q, ranking in current.items()}

    clean["protocol"]["rankingDepth"] = 10
    clean["limitations"].append(
        "This depth-10 report is an exact slice of the clean depth-40 rerun; source rankings differed from the historical report and are not an exact replication."
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(clean, indent=2, sort_keys=True) + "\n")
    audit = {
        "classification": "post-hoc reproducibility diagnostic",
        "cleanReportSha256": sha256(args.clean),
        "historicalReportSha256": sha256(args.historical),
        "rankingAudit": ranking_audit,
        "interpretation": "Exact historical ranking replication failed. New matched-model comparisons must use only the clean rerun's own source rankings and be reported as exploratory.",
    }
    args.audit.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": "completed", "rankingAudit": ranking_audit}))


if __name__ == "__main__":
    main()
