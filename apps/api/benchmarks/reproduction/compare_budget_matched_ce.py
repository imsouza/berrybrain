"""Compare clean four-route CE with label-free, query-budget-matched Hybrid CE."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from comparative_retrieval_benchmark import paired_comparisons
from same_corpus_rag_benchmark import sha256_file
from semantic_rerank_benchmark import candidate_pool


FOUR_ROUTES = ("bm25", "dense", "hybrid", "openie_graphrag")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--four-route", type=Path, required=True)
    parser.add_argument("--matched-hybrid", type=Path, required=True)
    parser.add_argument("--source-ten", type=Path, required=True)
    parser.add_argument("--matched-source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    four = json.loads(args.four_route.read_text())
    matched = json.loads(args.matched_hybrid.read_text())
    ten = json.loads(args.source_ten.read_text())
    matched_source = json.loads(args.matched_source.read_text())
    assert four["status"] == matched["status"] == "completed"
    assert four["classification"] == matched["classification"] == "post-hoc exploratory clean-source rerun"
    assert four["acceptance"]["claimAuthorized"] is matched["acceptance"]["claimAuthorized"] is False
    assert four["split"] == matched["split"] == "confirmatory"
    assert four["protocol"]["baseReportSha256"] == sha256_file(args.source_ten)
    assert matched["protocol"]["baseReportSha256"] == sha256_file(args.matched_source)
    for key in ("corpusSha256", "queriesSha256", "splitManifestSha256", "model", "revision", "maxLength", "rankingDepth", "inferenceBackend", "intraOpThreads", "onnxModelSha256"):
        assert four["protocol"][key] == matched["protocol"][key], key
    assert four["execution"] == matched["execution"]
    assert four["protocol"]["sourceMethods"] == list(FOUR_ROUTES)
    assert matched["protocol"]["sourceMethods"] == ["hybrid"]
    assert matched_source["protocol"]["hybridBudgetSourceSha256"] == sha256_file(args.source_ten)

    four_rows = four["observations"]["semantic_rerank"]
    matched_rows = matched["observations"]["semantic_rerank"]
    query_ids = {row["queryId"] for row in four_rows}
    assert len(four_rows) == len(matched_rows) == len(query_ids) == 600
    assert query_ids == {row["queryId"] for row in matched_rows}
    source_rankings = ten["retrieval"]["rankings"]
    matched_rankings = matched_source["retrieval"]["rankings"]
    budgets = {}
    for query_id in query_ids:
        four_count = len(candidate_pool(source_rankings, query_id, FOUR_ROUTES))
        matched_count = len(matched_rankings["hybrid"][query_id])
        if four_count != matched_count:
            raise ValueError(f"Candidate budget differs for {query_id}")
        budgets[query_id] = four_count
    comparisons = paired_comparisons(
        {"four_route_ce": four_rows, "budget_matched_hybrid_ce": matched_rows},
        candidate_method="four_route_ce",
        seed=20261025,
        resamples=10000,
    )["budget_matched_hybrid_ce"]
    result = {
        "status": "completed",
        "classification": "post-hoc exploratory candidate-budget-matched control on previously observed MuSiQue split",
        "claimAuthorized": False,
        "questionCount": len(query_ids),
        "sha256": {
            "fourRouteReport": sha256_file(args.four_route),
            "matchedHybridReport": sha256_file(args.matched_hybrid),
            "sourceTen": sha256_file(args.source_ten),
            "matchedSource": sha256_file(args.matched_source),
        },
        "candidateBudget": {
            "matchingRule": "Hybrid source depth equals the deduplicated four-route union size for each query, without relevance labels",
            "equalForEveryQuery": True,
            "minimum": min(budgets.values()),
            "maximum": max(budgets.values()),
            "mean": sum(budgets.values()) / len(budgets),
        },
        "summaries": {
            "four_route_ce": four["summaries"]["semantic_rerank"],
            "budget_matched_hybrid_ce": matched["summaries"]["semantic_rerank"],
        },
        "fourRouteMinusMatchedHybridPairedBootstrap": comparisons,
        "limitations": [
            "This control was specified after the clean four-route and Hybrid40 results had been inspected.",
            "Equal candidate counts do not make the candidate identities equal; route and ranking composition still differ.",
            "Timing was measured in separate runs with different host load and cannot support a matched speed claim.",
            "Exact historical source-ranking replication failed; this is a clean-source post-hoc reanalysis.",
            "External AI-provider latency is excluded.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "status": "completed",
        "candidateBudget": result["candidateBudget"],
        "summaries": result["summaries"],
        "fourRouteMinusMatchedHybridPairedBootstrap": comparisons,
    }))


if __name__ == "__main__":
    main()
