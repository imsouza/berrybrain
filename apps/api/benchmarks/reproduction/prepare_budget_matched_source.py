"""Create label-free Hybrid pools with each query's four-route candidate count."""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

from same_corpus_rag_benchmark import sha256_file
from semantic_rerank_benchmark import candidate_pool


FOUR_ROUTES = ("bm25", "dense", "hybrid", "openie_graphrag")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-ten", type=Path, required=True)
    parser.add_argument("--source-forty", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    ten = json.loads(args.source_ten.read_text())
    forty = json.loads(args.source_forty.read_text())
    assert ten["git"] == forty["git"]
    assert ten["inputs"] == forty["inputs"]
    assert ten["protocol"]["embeddingModelSha256"] == forty["protocol"]["embeddingModelSha256"]
    source = ten["retrieval"]["rankings"]
    control = forty["retrieval"]["rankings"]
    assert set(source["hybrid"]) == set(control["hybrid"])
    budgets = {}
    for query_id in source["hybrid"]:
        budget = len(candidate_pool(source, query_id, FOUR_ROUTES))
        if budget < 10 or budget > len(control["hybrid"][query_id]):
            raise ValueError(f"Invalid budget for {query_id}: {budget}")
        control["hybrid"][query_id] = control["hybrid"][query_id][:budget]
        budgets[query_id] = budget
    forty["protocol"]["hybridBudgetPolicy"] = (
        "first N(q) clean Hybrid-RRF documents, N(q)=deduplicated clean four-route top-ten union size"
    )
    forty["protocol"]["hybridBudgetSourceSha256"] = sha256_file(args.source_ten)
    forty["protocol"]["hybridBudgetMean"] = statistics.fmean(budgets.values())
    forty["protocol"]["hybridBudgetMin"] = min(budgets.values())
    forty["protocol"]["hybridBudgetMax"] = max(budgets.values())
    forty["limitations"].append(
        "Hybrid source rankings have query-specific depth equal to the four-route deduplicated union size; source relevance labels did not select N(q)."
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(forty, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "status": "completed",
        "queryCount": len(budgets),
        "meanBudget": forty["protocol"]["hybridBudgetMean"],
        "minBudget": min(budgets.values()),
        "maxBudget": max(budgets.values()),
    }))


if __name__ == "__main__":
    main()
